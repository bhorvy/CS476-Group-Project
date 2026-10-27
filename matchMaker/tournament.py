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
        # This is a mock function to simulate the progression of a tournament bracket.
        # Mostly used for testing purposes. Will likely get deleted later on in the project.
        for roundId in range(len(self.layout["bracket"])-1):
            for matchId in range(len(self.layout["bracket"][roundId])):
                player1 = self.layout["bracket"][roundId][matchId][0]
                player2 = self.layout["bracket"][roundId][matchId][1]
                #Handles null player slots (byes). If both players exist, randomly select.
                if player1 == 0:
                    winnerId = player2
                elif player2 == 0:
                    winnerId = player1
                elif player1 and player2:
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

    def deleteTournament(self):
        self.object.delete()

class TournamentCreate:
    def __init__(self, name, description, players, gameName):
        self.name = name
        self.description = description
        self.players = players
        self.layout = self.generateBracket(players)
        self.gameName = gameName


    def generateBracket(self, players):
        # 1v1 brackets single elim correlate with length of bits cleanly (i.e. 16 players has 4 rounds),
        # Many of the lines of code are based on this fact.

        numPlayers = len(players)
        #Find the next power of 2 greater than or equal to numPlayers.
        #If numPlayers is 17, 15 bye slots will have to be filled as 32 is the next power.
        nextPowerOf2 = 1 << (numPlayers - 1).bit_length()
        # Create a list of players with 0 for byes
        bracketPlayers = players + [0] * (nextPowerOf2 - numPlayers)
        # Shuffle the players to randomize the bracket
        random.shuffle(bracketPlayers)
        # Create the initial bracket structure
        bracket = []
        currentRound = []
        for i in range(0, len(bracketPlayers), 2):
            currentRound.append([bracketPlayers[i], bracketPlayers[i + 1]])
        bracket.append(currentRound)
        # Generate subsequent rounds with empty matches
        while len(currentRound) > 1:
            nextRound = [[0, 0] for _ in range(len(currentRound) // 2)]
            bracket.append(nextRound)
            currentRound = nextRound
        return {"bracket": bracket}

    def createTournament(self):
        # Create a new Tournament instance and save it to the database
        tournament = Tournament(name=self.name, description=self.description, layout=self.layout, game_title=self.gameName)
        tournament.save()
        return tournament