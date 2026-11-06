from typing import List
from .observer import Subject, Observer

##TODO: Implement observer code to be utilized despite django's stateless restrictions.
class TournamentUpdateSubject(Subject):
    def __init__(self):
        super().__init__()

        self.observers: List[Observer]

    def attach(self, observer: Observer):
        self.observers.append(observer)

    def detach(self, observer: Observer, tid: int):
        if tid in self.observers:
            self.observers.remove(observer)

    def notify(self, tid: int):
        for observer in self.observers:
            observer.update(tid, self)

class BracketUpdateNotify(Observer):
    def update(self):
        print("I did an action")

tournamentNotifier = TournamentUpdateSubject()