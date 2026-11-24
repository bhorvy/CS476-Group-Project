# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: tournamentCreate.py
# Purpose: Code for creating new tournament

import random
from ..models import Tournament

class TournamentCreate:
    def __init__(self, name, description, players, gameName, format):
        self.name = name
        self.description = description
        self.players = players
        self.format = format
        self.layout = self.generateBracket(players)
        self.gameName = gameName
    def generateBracket(self, players):
        # 1v1 brackets single elim correlate with length of bits cleanly (i.e. 16 players has 4 rounds),
        # Many of the lines of code are based on this fact.
        numPlayers = len(players)
        # Find the next power of 2 greater than or equal to numPlayers.
        # If numPlayers is 17, 15 bye slots will have to be filled as 32 is the next power.
        # At least 2 slots so there is always a match, even with one player.
        # When creating a tournament with one member, we crashed
        nextPowerOf2 = max(2, 1 << (numPlayers - 1).bit_length())
        # Create a list of players with 0 for byes
        bracketPlayers = players + [0] * (nextPowerOf2 - numPlayers)
        # Shuffle the players to randomize the bracket
        random.shuffle(bracketPlayers)
        # Create the initial bracket structure
        match self.format:
            case "SINGLE_ELIM":
                return self.createSingleElimBracket(bracketPlayers)
            case "DOUBLE_ELIM":
                return self.createDoubleElimBracket(bracketPlayers)
            case "POOLS":
                return self.createPools(bracketPlayers)

    def createSingleElimBracket(self, players):
        bracket = []
        currentRound = []
        for i in range(0, len(players), 2):
            match = {
                "players": [
                    {"player_id": players[i], "score": 0},
                    {"player_id": players[i + 1], "score": 0}
                ],
                "winner_id": 0
            }
            currentRound.append(match)
        bracket.append(currentRound)
        
        # Generate subsequent rounds with empty matches
        while len(currentRound) > 1:
            nextRound = []
            for _ in range(len(currentRound) // 2):
                match = {
                    "players": [
                        {"player_id": 0, "score": 0},
                        {"player_id": 0, "score": 0}
                    ],
                    "winner_id": 0
                }
                nextRound.append(match)
            bracket.append(nextRound)
            currentRound = nextRound
            
        return {"bracket": bracket}

    def createDoubleElimBracket(self, players):
        upper_bracket = []
        lower_bracket = []

        #Upper bracket formation (similar to single elim)
        currentRound = []
        for i in range(0, len(players), 2):
            match = {
                "players": [
                    {"player_id": players[i], "score": 0},
                    {"player_id": players[i + 1], "score": 0}
                ],
                "winner_id": 0
            }
            currentRound.append(match)
        upper_bracket.append(currentRound)

        while len(currentRound) > 1:
            nextRound = []
            for _ in range(len(currentRound) // 2):
                match = {
                    "players": [
                        {"player_id": 0, "score": 0},
                        {"player_id": 0, "score": 0}
                    ],
                    "winner_id": 0
                }
                nextRound.append(match)
            upper_bracket.append(nextRound)
            currentRound = nextRound

        #Lower bracket function
        currentRound = upper_bracket[0]
        print(currentRound)
        while len(currentRound) > 1:
            nextRound = []
            #Lower bracket requires 2 times looping the same round size for major and minor rounds
            for _ in range(2):
                nextRound = []
                for _ in range(len(currentRound) // 2):
                    match = {
                        "players": [
                            {"player_id": 0, "score": 0},
                            {"player_id": 0, "score": 0}
                        ],
                        "winner_id": 0
                    }
                    nextRound.append(match)
                lower_bracket.append(nextRound)
            currentRound = nextRound
        return {"bracket" : {
            "upper_bracket" : upper_bracket,
            "lower_bracket" : lower_bracket
        }}

    def createPools(self, players):
        bracket = []
        pools = []
        bracketSlots = (len(players) // 2 + 1) if len(players) % 2 == 1 else (len(players) // 2)
        for i in range(0, len(players), 4):
            pools.append(self.createPoolMatches(players[i:i + 4]))

        # Create the initial bracket structure
        while bracketSlots > 1:
            currentRound = []
            for _ in range(bracketSlots // 2):
                match = {
                    "players": [
                        {"player_id": 0, "score": 0},
                        {"player_id": 0, "score": 0}
                    ],
                    "winner_id": 0
                }
                currentRound.append(match)
            bracket.append(currentRound)
            bracketSlots = len(currentRound)
        
        return {
            "pools": pools,
            "bracket": bracket
            }

    def createPoolMatches(self, players):
        #Pools are fixed to 4 players, so the matches can be hardcoded.
        return [
            { "players": [{"player_id": players[0], "score": 0}, {"player_id": players[1], "score": 0}], "winner_id": 0 },
            { "players": [{"player_id": players[2], "score": 0}, {"player_id": players[3], "score": 0}], "winner_id": 0 },
            { "players": [{"player_id": players[0], "score": 0}, {"player_id": players[2], "score": 0}], "winner_id": 0 },
            { "players": [{"player_id": players[1], "score": 0}, {"player_id": players[3], "score": 0}], "winner_id": 0 },
            { "players": [{"player_id": players[0], "score": 0}, {"player_id": players[3], "score": 0}], "winner_id": 0 },
            { "players": [{"player_id": players[1], "score": 0}, {"player_id": players[2], "score": 0}], "winner_id": 0 },
            { "players": [{"player_id": players[0], "wins": 0, "losses":0}, {"player_id": players[1], "wins": 0, "losses":0},
                          { "player_id": players[2], "wins": 0, "losses":0}, {"player_id": players[3], "wins": 0, "losses":0}]}
        ]


    def createTournament(self):
        # Create a new Tournament instance and save it to the database
        tournament = Tournament(name=self.name, description=self.description, layout=self.layout, game_title=self.gameName)
        tournament.save()
        return tournament