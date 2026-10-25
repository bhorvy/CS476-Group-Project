from django.db import models
from django.conf import settings

# Create your models here.
class Member(models.Model):
  user = models.OneToOneField(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='member',
  )
  firstname = models.CharField(max_length=255)
  lastname = models.CharField(max_length=255)
  class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"
  gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
  DOB = models.DateField()
  #image field can come once I learn how to implement it. 

  def __str__(self):
    return f"{self.firstname} {self.lastname}"

#subject to change just getting something down
class Tournament(models.Model):
  name = models.CharField(max_length=100);
  description = models.CharField(max_length=255);

class Match(models.Model):
  player1 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='player1')
  player2 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='player2') 
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE) 
  winner = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='winner')

#model for teams, ie who are the members and who is the captain
class Team(models.Model):
  name = models.CharField(max_length=100, unique=True)
  tag = models.CharField(max_length=100, blank=True)
  leader = models.ForeignKey(Member, on_delete=models.Protect, related_name='led_teams')
  members = models.ManyToManyField(Member, related_name='teams', blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  def __str__(self):
    return self.name
#class GameAccount(models.Model):

#class TournamentRegistration(models.Model):


