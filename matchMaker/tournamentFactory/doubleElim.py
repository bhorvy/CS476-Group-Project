from ..models import Tournament
from .abstractTournament import AbstractTournament
import math
import pdb

class DoubleElimination(AbstractTournament):

    def getBracket(self):
        return self.layout.get("bracket", [])

    #findUserInBracket is used to find the first instance of a user in a tournament bracket
    #   starting from the latest point in the bracket. This is used solely to determine which
    #   match a user can edit, given older matches should not be edited. Returns null if no 
    #   instance of that user is found.
    def findUserInBracket(self, uid):
        if not self.layout.get("bracket"):
            return None
        #Search the lower bracket first. The furthest one has to be is the lower bracket first. If not there, then
        #   search the upper bracket afterwards.
        #Lower bracket search
        for i in range(len(self.layout["bracket"]["lower_bracket"]) - 1, -1, -1):
            for j in range(0, len(self.layout["bracket"]["lower_bracket"][i])):
                for k in range(0, len(self.layout["bracket"]["lower_bracket"][i][j]["players"])):
                    if self.layout["bracket"]["lower_bracket"][i][j]["players"][k]["player_id"] == uid:
                        return {"round_id": i, "match_id": j, "is_upper_bracket": False}
        #Upper bracket search
        for i in range(len(self.layout["bracket"]["upper_bracket"]) - 1, -1, -1):
            for j in range(0, len(self.layout["bracket"]["upper_bracket"][i])):
                for k in range(0, len(self.layout["bracket"]["upper_bracket"][i][j]["players"])):
                    if self.layout["bracket"]["upper_bracket"][i][j]["players"][k]["player_id"] == uid:
                        return {"round_id": i, "match_id": j, "is_upper_bracket": True}

        return None

    #Function to determine if a match has is a completed match. Determined by the simple logic that
    #   if a winner_id is 0 (null), a winner is not decided. Therefore match is not complete.
    def IsMatchComplete(self, roundId, matchId, IsUpperBracket):
        return (self.object.layout["bracket"]["upper_bracket"][roundId][matchId]["winner_id"] > 0 if IsUpperBracket 
                else self.object.layout["bracket"]["lower_bracket"][roundId][matchId]["winner_id"])

    def handleWinner(self, roundId, matchId, winnerId, isUpperBracket):
        data = self.layout
        bracketName = "upper_bracket" if isUpperBracket else "lower_bracket"
        #Check if it is the finals. If so, only handle the winner's id.
        if (roundId + 1) == len(data["bracket"][bracketName]):
            data["bracket"][bracketName][roundId][matchId]["winner_id"] = winnerId
            if(isUpperBracket):
                loserSlotIndex = 1 if data["bracket"]["upper_bracket"][roundId][matchId]["players"][0]["player_id"] == winnerId else 0
                loserId = data["bracket"]["upper_bracket"][roundId][matchId]["players"][loserSlotIndex]["player_id"]
                (data["bracket"]["lower_bracket"][(roundId * 2) - 1][matchId]["players"][0]["player_id"]) = loserId
            self.object.layout = data
            self.object.save()
            return
        
        if (isUpperBracket):
            nextRoundMatchIndex = math.ceil((matchId + 1) / 2) - 1
            playerSlotIndex = (matchId % 2)
            # Update the layout with the winner of the match in the next round's specific player slot
            data["bracket"]["upper_bracket"][roundId + 1][nextRoundMatchIndex]["players"][playerSlotIndex]["player_id"] = winnerId

            #Put loser in the lower bracket.
            nextRoundLen = len(data["bracket"]["lower_bracket"][roundId])
            #Initial lower bracket seeding is different from the rest of the lower bracket.
            #First round slotting is based on match position.
            loserSlotIndex = 1 if data["bracket"]["upper_bracket"][roundId][matchId]["players"][0]["player_id"] == winnerId else 0
            loserId = data["bracket"]["upper_bracket"][roundId][matchId]["players"][loserSlotIndex]["player_id"]
            if (roundId == 0):
                (data["bracket"]["lower_bracket"][roundId][nextRoundMatchIndex]["players"][playerSlotIndex]["player_id"]) = loserId
            else:
                if (roundId % 2 == 1):
                    #If round is odd, move the loser to the opposite side of the lower bracket.
                    (data["bracket"]["lower_bracket"][(roundId * 2) - 1][(matchId + (nextRoundLen // 2)) 
                                                                            % nextRoundLen]["players"][0]["player_id"]) = loserId
                else:
                    #If round is even, move the loser to the same side of the lower bracket.
                    (data["bracket"]["lower_bracket"][(roundId * 2) - 1][matchId]["players"][0]["player_id"]) = loserId

        else:
            #First round to second round layout is the same size so it does not follow typical elimination standards.
            #Therefore, keep the same matchId for the players coming down from upper bracket.
            if (roundId % 2 == 0):
                data["bracket"]["lower_bracket"][roundId + 1][matchId]["players"][1]["player_id"] = winnerId
            else:
                #Loser bracket progression behaves similarly to single elimination
                nextRoundMatchIndex = math.ceil((matchId + 1) / 2) - 1
                playerSlotIndex = (matchId % 2)
                data["bracket"]["lower_bracket"][roundId + 1][nextRoundMatchIndex]["players"][playerSlotIndex]["player_id"] = winnerId
                    
        #Update the winner_id field of the completed match to denote it is completed.
        data["bracket"][bracketName][roundId][matchId]["winner_id"] = winnerId
        
        # Save the updated layout back to the database
        self.object.layout = data
        self.object.save()

    #If a winner is to be called, compare the scores and move the bracket accordingly. Equal scores
    #   can not be accepted as no winner can be determined.
    def determineWinner(self, roundId, matchId, isUpperBracket):
        bracketName = "upper_bracket" if isUpperBracket else "lower_bracket"
        player1Score = self.layout["bracket"][bracketName][roundId][matchId]["players"][0]["score"]
        player2Score = self.layout["bracket"][bracketName][roundId][matchId]["players"][1]["score"]
        if player1Score > player2Score:
            self.handleWinner(roundId, matchId, 
                              self.layout["bracket"][bracketName][roundId][matchId]["players"][0]["player_id"], isUpperBracket)
            return True
        elif player2Score > player1Score:
            self.handleWinner(roundId, matchId, 
                              self.layout["bracket"][bracketName][roundId][matchId]["players"][1]["player_id"], isUpperBracket)
            return True
        return False

    # update the score after finding the round and match ID from the tournament, send in the playerId to update and the 
    # the new score.
    def updateScore(self, roundId, matchId, newScore, isUpperBracket):
        bracketName = "upper_bracket" if isUpperBracket else "lower_bracket"
        #get match from the JSON
        match = self.layout["bracket"][bracketName][roundId][matchId]
        # Update the scores based on array position of both the layout JSON and the array of new scores.
        for i in range(len(match["players"])):
            match["players"][i]["score"] = newScore[i]

        self.object.layout = self.layout
        self.object.save()
        return



