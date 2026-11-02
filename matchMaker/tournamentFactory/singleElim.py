from ..models import Tournament
from .abstractTournament import AbstractTournament
import math

class SingleElimination(AbstractTournament):

    def getBracket(self):
        return self.layout["bracket"]

    #findUserInBracket is used to find the first instance of a user in a tournament bracket
    #   starting from the latest point in the bracket. This is used solely to determine which
    #   match a user can edit, given older matches should not be edited. Returns null if no 
    #   instance of that user is found.
    def findUserInBracket(self, uid):
        #Highest round and decrements
        for i in range(len(self.layout["bracket"]) - 1, -1, -1):
            for j in range(0, len(self.layout["bracket"][i])):
                for k in range(0, len(self.layout["bracket"][i][j]["players"])):
                    if self.layout["bracket"][i][j]["players"][k]["player_id"] == uid:
                        return {"round_id": i, "match_id": j}

        return None

    #Function to determine if a match has is a completed match. Determined by the simple logic that
    #   if a winner_id is 0 (null), a winner is not decided. Therefore match is not complete.
    def IsMatchComplete(self, roundId, matchId):
        return self.object.layout["bracket"][roundId][matchId]["winner_id"] > 0

    def handleWinner(self, roundId, matchId, winnerId):
        data = self.layout
        #Check if it is the finals. If so, only handle the winner's id.
        #TODO: Make a tournament winner field in either the layout or Tournament model,
        #   and assign it as well when final match is complete.
        if (roundId + 1) == len(data["bracket"]):
            data["bracket"][roundId][matchId]["winner_id"] = winnerId
            self.object.layout = data
            self.object.save()
            return
        nextRoundMatchIndex = math.ceil(matchId / 2) - 1
        playerSlotIndex = 0 if matchId % 2 == 1 else 1
        # Update the layout with the winner of the match in the next round's specific player slot
        data["bracket"][roundId + 1][nextRoundMatchIndex]["players"][playerSlotIndex]["player_id"] = winnerId

        #Update the winner_id field of the completed match to denote it is completed.
        data["bracket"][roundId][matchId]["winner_id"] = winnerId
        
        # Save the updated layout back to the database
        self.object.layout = data
        self.object.save()

    #If a winner is to be called, compare the scores and move the bracket accordingly. Equal scores
    #   can not be accepted as no winner can be determined.
    def determineWinner(self, roundId, matchId):
            player1Score = self.layout["bracket"][roundId][matchId]["players"][0]["score"]
            player2Score = self.layout["bracket"][roundId][matchId]["players"][1]["score"]
            if player1Score > player2Score:
                self.handleWinner(roundId, matchId, self.layout["bracket"][roundId][matchId]["players"][0]["player_id"])
                return True
            elif player2Score > player1Score:
                self.handleWinner(roundId, matchId, self.layout["bracket"][roundId][matchId]["players"][1]["player_id"])
                return True
            return False

    def deleteTournament(self):
        self.object.delete()

    # update the score after finding the round and match ID from the tournament, send in the playerId to update and the 
    # the new score.
    def updateScore(self, roundId, matchId, newScore):
        #get match from the JSON
        match = self.layout["bracket"][roundId][matchId] 
        # Update the scores based on array position of both the layout JSON and the array of new scores.
        for i in range(len(match["players"])):
            match["players"][i]["score"] = newScore[i]
        #for player in match["players"]:
        #    if player["player_id"] == playerId:
        #        player["score"] = newScore

        self.object.layout = self.layout
        self.object.save()
        return



