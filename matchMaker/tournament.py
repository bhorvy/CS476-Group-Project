from .models import Tournament
import math
import random
import json
import pdb

class TournamentInstance:
    def __init__(self, tid):
        self.object = Tournament.objects.get(id=tid)
        self.name = self.object.name
        self.description = self.object.description
        self.layout = self.object.layout

    def getBracket(self):
        return self.layout["bracket"]

    def mockBracketProgression(self):
        # This is a mock function to simulate the progression of the tournament
        # In a real scenario, you would have logic to determine the winners of each match
        
        for roundId in range(len(self.layout["bracket"])-1):
            for matchId in range(len(self.layout["bracket"][roundId])):
                player1 = self.layout["bracket"][roundId][matchId][0]
                player2 = self.layout["bracket"][roundId][matchId][1]
                if player1 and player2:
                    winnerId = random.choice([player1, player2])
                    self.handleWinner(roundId, matchId + 1, winnerId)

    def handleWinner(self, roundId, matchId, winnerId):
        data = self.layout
        nextRoundBracket = math.ceil(matchId / 2)
        # Update the layout with the winner of the match
        if matchId % 2 == 1:
            data["bracket"][roundId + 1][nextRoundBracket - 1][0] = winnerId
        else:
            data["bracket"][roundId + 1][nextRoundBracket - 1][1] = winnerId
        # Save the updated layout back to the database
        self.object.layout = data
        self.object.save()