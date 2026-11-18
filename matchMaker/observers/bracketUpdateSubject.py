# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: bracketUpdateSubject.py
# Purpose: Implement observer code

from .observer import Subject, Observer
from ..models import TournamentNotification, Tournament, Member
from typing import Iterable
class TournamentUpdateSubject(Subject):
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, tournament : Tournament, message: str) -> None:
        for observer in self._observers:
            observer.update(tournament, message)

class BracketUpdateNotify(Observer):
    def __init__(self, members : Iterable[Member]):
           self.members = members;

    def update(self, tournamnet : Tournament, message : str) -> None:
        for member in self.members:
            TournamentNotification.objects.create(
                member=member,
                tournament=tournamnet,
                message=message,
            )


#function to create a message for each user in a particular tournament 
def notify_tournament_updated(tournament, members, message):

    subject = TournamentUpdateSubject()
    subject.attach(BracketUpdateNotify(members))

    subject.notify(tournament, message)