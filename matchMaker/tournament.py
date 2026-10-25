from .models import Tournament

class TournamentInstance:
    def __init__(self, tid):
        self.object = Tournament.objects.get(id=tid)
        self.name = self.object.name
        self.description = self.object.description
        self.layout = self.object.layout

    def getBracket(self):
        return self.layout["bracket"]