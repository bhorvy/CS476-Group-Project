from typing import List
from .observer import Subject, Observer
from ..models import TournamentNotification
from django.db import transaction

##TODO: Implement observer code to be utilized despite django's stateless restrictions.
class TournamentUpdateSubject(Subject):
    def __init__(self):
        super().__init__()

        self.observers: List[Observer] = []

    def attach(self, observer: Observer):
        self.observers.append(observer)

    def detach(self, observer: Observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify(self, tournament, message):
        for observer in self.observers:
            observer.update(tournament, message)

class BracketUpdateNotify(Observer):
    def __init__(self, members):
           self.members = members;

    def update(self, tournamnet, message):
        for member in self.members:
            TournamentNotification.objects.create(
                member=member,
                tournament=tournamnet,
                message=message,
            )

# i don't think we need this anymore. 
tournamentNotifier = TournamentUpdateSubject()


#function to create a message for each user in a particular tournament 
def notify_tournament_updated(tournament, members, message):

    subject = TournamentUpdateSubject()
    subject.attach(BracketUpdateNotify(members))

    subject.notify(tournament, message)