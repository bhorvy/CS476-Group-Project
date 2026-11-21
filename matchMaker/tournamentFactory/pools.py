from ..models import Tournament
from .abstractTournament import AbstractTournament
import math
import pdb

class Pools(AbstractTournament):

    def getBracket(self):
        return self.layout.get("bracket", [])

    def getPools(self):
        return self.layout.get("pools", [])

    #findUserInBracket is used to find the first instance of a user in a tournament bracket
    #   starting from the latest point in the bracket. This is used solely to determine which
    #   match a user can edit, given older matches should not be edited. Returns null if no 
    #   instance of that user is found.
    def findUserInBracket(self, uid):      
        #Search bracket first, then pools after.
        for i in range(len(self.layout["bracket"]) - 1, -1, -1):
            for j in range(0, len(self.layout["bracket"][i])):
                for k in range(0, len(self.layout["bracket"][i][j]["players"])):
                    if self.layout["bracket"][i][j]["players"][k]["player_id"] == uid:
                        return {"round_id": i, "match_id": j, "is_bracket": True}
        for i in range(len(self.layout["pools"])):
            for j in range(6):
                for k in range(0, len(self.layout["pools"][i][j]["players"])):
                    if self.layout["pools"][i][j]["players"][k]["player_id"] == uid:
                        if self.layout["pools"][i][j]["winner_id"] == 0:
                        #If the last 2 matches are played, then the player need not edit matches in the pool.
                            if ((j == 5 or j == 4) and self.layout["pools"][i][j]["winner_id"] > 0):
                                return None
                            return {"pool_id": i, "match_id": j, "is_bracket": False}
        return None

    #Function to determine if a match has is a completed match. Determined by the simple logic that
    #   if a winner_id is 0 (null), a winner is not decided. Therefore match is not complete.
    def IsMatchComplete(self, roundId, matchId, isBracket):
        return (self.object.layout["bracket"][roundId][matchId]["winner_id"] > 0 if isBracket 
                else self.object.layout["pools"][roundId][matchId]["winner_id"] > 0)

    def handleWinner(self, roundId, matchId, winnerId, isBracket):
        data = self.layout
        bracketName = "bracket" if isBracket else "pools"
        #Check if it is the finals. If so, only handle the winner's id.
        if(isBracket):
            if (roundId + 1) == len(data[bracketName]):
                data[bracketName][roundId][matchId]["winner_id"] = winnerId
                self.object.layout = data
                self.object.save()
                return
            nextRoundMatchIndex = math.floor(matchId / 2)
            playerSlotIndex = 0 if matchId % 2 == 0 else 1
            # Update the layout with the winner of the match in the next round's specific player slot
            data[bracketName][roundId + 1][nextRoundMatchIndex]["players"][playerSlotIndex]["player_id"] = winnerId
    
            #Update the winner_id field of the completed match to denote it is completed.
            data[bracketName][roundId][matchId]["winner_id"] = winnerId

        else:
            loserId = (data[bracketName][roundId][matchId]["players"][0]["player_id"] if 
                       data[bracketName][roundId][matchId]["players"][1]["player_id"] == winnerId else
                       data[bracketName][roundId][matchId]["players"][1]["player_id"])

            #Search for the proper winner and loser ids and update their W/L
            for i in range(len(data[bracketName][roundId][6]["players"])):
                if data[bracketName][roundId][6]["players"][i]["player_id"] == winnerId:
                    data[bracketName][roundId][6]["players"][i]["wins"]+=1 
                if data[bracketName][roundId][6]["players"][i]["player_id"] == loserId:
                    data[bracketName][roundId][6]["players"][i]["losses"]+=1 

            #Sort the current win/loss record to easily determine standings
            scores = data[bracketName][roundId][6]["players"]
            scores.sort(key=lambda x: x["wins"], reverse=True)

            #Update the winner_id field of the completed match to denote it is completed.
            data[bracketName][roundId][matchId]["winner_id"] = winnerId

            #If the pool is complete, move the top 2 participants to bracket stage.
            #First position and second position are on separate sides of the bracket to prevent replaying each other.
            if(self.isPoolFinished(roundId)):
                data["bracket"][0][roundId]["players"][0]["player_id"] = scores[0]["player_id"]
                data["bracket"][0][(roundId + (len(data["bracket"][0]) // 2)) % len(data["bracket"][0])]["players"][1]["player_id"] = scores[1]["player_id"]
                
        
        # Save the updated layout back to the database
        self.object.layout = data
        self.object.save()

    #If a winner is to be called, compare the scores and move the bracket accordingly. Equal scores
    #   can not be accepted as no winner can be determined.
    def determineWinner(self, roundId, matchId, isBracket):
        bracketName = "bracket" if isBracket else "pools"
        player1Score = self.layout[bracketName][roundId][matchId]["players"][0]["score"]
        player2Score = self.layout[bracketName][roundId][matchId]["players"][1]["score"]
        if player1Score > player2Score:
            self.handleWinner(roundId, matchId, 
                              self.layout[bracketName][roundId][matchId]["players"][0]["player_id"], isBracket)
            return True
        elif player2Score > player1Score:
            self.handleWinner(roundId, matchId, 
                              self.layout[bracketName][roundId][matchId]["players"][1]["player_id"], isBracket)
            return True
        return False

    # update the score after finding the round and match ID from the tournament, send in the playerId to update and the 
    # the new score.
    #Bracket: ["bracket"][roundId][matchId]
    #Pools: ["pools"][poolId][matchId (except last pos, which is W/L)]
    def updateScore(self, roundId, matchId, newScore, isBracket):
        bracketName = "bracket" if isBracket else "pools"
        #get match from the JSON
        match = self.layout[bracketName][roundId][matchId]
        # Update the scores based on array position of both the layout JSON and the array of new scores.
        for i in range(len(match["players"])):
            match["players"][i]["score"] = newScore[i]

        self.object.layout = self.layout
        self.object.save()
        return

    def isPoolFinished(self, poolId):
        #If any of the matches are not marked with a winner, the overall pool is not finished.
        complete = True
        for i in range(0, 6):
            if self.layout["pools"][poolId][i]["winner_id"] == 0:
                complete = False
        return complete



