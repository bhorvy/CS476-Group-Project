

# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: abstractTournament.py
# Purpose: Code for regular tournament

from abc import ABC, abstractmethod
from ..models import Tournament

class AbstractTournament(ABC):
    def __init__(self, tid):
        self.object = Tournament.objects.get(id=tid)
        self.name = self.object.name
        self.description = self.object.description
        self.layout = self.object.layout or {"bracket": []}
        self.status = self.object.status
        if "bracket" not in self.layout:
            self.layout = {"bracket": []}
    
    @abstractmethod
    def findUserInBracket(self, uid):
        pass

    @abstractmethod
    def IsMatchComplete(self, roundId, matchId):
        pass

    @abstractmethod
    def handleWinner(self, roundId, matchId, winnerId, isUpperBracket = False):
        pass

    @abstractmethod
    def determineWinner(self, roundId, matchId):
        pass

    @abstractmethod
    def updateScore(self, roundId, matchId, score, isUpperBracket):
        pass

    def deleteTournament(self):
        self.object.delete()
        
    def updateStatus(self, status):
        self.status = status
        self.object.save()
