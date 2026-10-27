from django.db import models
from django.conf import settings

class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

#model for members, the users of the system
class Member(models.Model):
  user = models.OneToOneField(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='member',
  )
  firstname = models.CharField(max_length=255)
  lastname = models.CharField(max_length=255)
  gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
  DOB = models.DateField()
  #profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

  def __str__(self):
    return f"{self.firstname} {self.lastname} ({self.user.username})"

#model for teams, ie who are the members and who is the captain
class Team(models.Model):
  name = models.CharField(max_length=100, unique=True)
  tag = models.CharField(max_length=100, blank=True)
  leader = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='led_teams')
  members = models.ManyToManyField(Member, related_name='teams', blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  def __str__(self):
    return self.name
  
  class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"
  gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
  DOB = models.DateField()
  #profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

  def __str__(self):
    return f"{self.firstname} {self.lastname} ({self.user.username})"

#model for tournaments, arguabably MOST IMPORTANT MODEL, so please change if you feel the need
class Tournament(models.Model):
  class TournmanentFormat(models.TextChoices):
    SOLO = "SOLO", "1v1 SOLO"
    TEAM = "TEAM", "Team"
    OTHER = "OTHER", "Other"
  class Status(models.TextChoices):
    UPCOMING = "UPCOMING", "Upcoming"
    ONGOING = "ONGOING", "Ongoing"
    COMPLETED = "COMPLETED", "Completed"
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True)
  layout = models.JSONField()
#  layout note: The JSON currently is {"bracket": (3D array)}
#  3D array structure: [round][match][player]
#  player ids are stored in the array
#  Example layout: {"bracket": [[[1, 2], [3, 4], [5, 6], [7, 8]], [[0, 0], [0, 0]], [[0, 0]]]}
#       (0s denote null playerids)
  game_title = models.CharField(max_length=100)
  format = models.CharField(max_length=10, choices=TournmanentFormat.choices, default=TournmanentFormat.SOLO)
  status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)
  is_public = models.BooleanField(default=True)
  max_participants = models.IntegerField(default=16)
  min_rank = models.IntegerField(blank=True, null=True, default=0)
  max_rank = models.IntegerField(blank=True, null=True, default=9999)
  start_date = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  def __str__(self):
    return f"{self.name} - ({self.game_title})"

#model for registration status in tournaments for both teams and individuals
class TournamentRegistration(models.Model):
  class RegistrationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Admin Approval"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
    INVITED = "INVITED", "Invited (Closed Bracket)"

#model for game accounts, ie the accounts that members have for games
class GameAccount(models.Model):
  member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='game_accounts')
  game_title = models.CharField(max_length=100)
  game_username = models.CharField(max_length=100)
  external_player_id = models.CharField(max_length=100, blank=True)
  rank_or_elo = models.IntegerField(blank=True, null=True)
  last_synced = models.DateTimeField(auto_now=True)
  def __str__(self):
    return f"{self.member.user.username} - {self.game_title} ({self.game_username})"

  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='registrations')
  member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='tournament_registrations')
  team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='tournament_registrations')
  status = models.CharField(max_length=20, choices=TournamentRegistration.RegistrationStatus.choices, default=TournamentRegistration.RegistrationStatus.PENDING)
  rejection_reason = models.CharField(max_length=255, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  def __str__(self):
    participant = self.member.user.username if self.member else self.team.name
    return f"{participant} -> {self.tournament.name} [{self.status}]"

#model for matches
class Match(models.Model):
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
  round_number = models.PositiveIntegerField(default=1)
  match_number = models.PositiveIntegerField(default=1)
  player1 = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_as_p1')
  player2 = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_as_p2')
  team1 = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_as_t1')
  team2 = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_as_t2')
  score1 = models.IntegerField(default=0)
  score2 = models.IntegerField(default=0)
  submitted_by = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_matches')
  is_disputed = models.BooleanField(default=False)
  is_completed = models.BooleanField(default=False)
  winner_member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='solo_matches_won')
  winner_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_matches_won')
  def __str__(self):
    c1 = self.player1.user.username if self.player1 else (self.team1.name if self.team1 else "TBD")
    c2 = self.player2.user.username if self.player2 else (self.team2.name if self.team2 else "TBD")
    return f"{self.tournament.name} (R{self.round_number} M{self.match_number}) : {c1} vs {c2}"
