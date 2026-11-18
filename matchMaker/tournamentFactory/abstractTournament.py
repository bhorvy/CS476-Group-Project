from abc import ABC, abstractmethod
from ..models import Tournament

class AbstractTournament(ABC):
    def __init__(self, tid):
        self.object = Tournament.objects.get(id=tid)
        self.name = self.object.name
        self.description = self.object.description
        self.layout = self.object.layout or {"bracket": []}
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

    def deleteTournament(self):
        self.object.delete()

    @abstractmethod
    def updateScore(self, roundId, matchId, score, isUpperBracket):
        pass
