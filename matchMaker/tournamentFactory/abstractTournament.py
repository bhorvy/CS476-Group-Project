from abc import ABC, abstractmethod
from ..models import Tournament

class AbstractTournament(ABC):
    def __init__(self, tid):
        self.object = Tournament.objects.get(id=tid)
        self.name = self.object.name
        self.description = self.object.description
        self.layout = self.object.layout
    
    @abstractmethod
    def findUserInBracket(self, uid):
        pass

    @abstractmethod
    def IsMatchComplete(self, roundId, matchId):
        pass

    @abstractmethod
    def handleWinner(self, roundId, matchId, winnerId):
        pass

    @abstractmethod
    def determineWinner(self, roundId, matchId):
        pass

    @abstractmethod
    def deleteTournament(self):
        pass

    @abstractmethod
    def updateScore(self, roundId, matchId, score):
        pass
