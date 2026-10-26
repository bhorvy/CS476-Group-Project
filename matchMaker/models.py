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
  name = models.CharField(max_length=100)
  description = models.CharField(max_length=255)
  layout = models.JSONField()
#  layout note: The JSON currently is {"bracket": (3D array)}
#  3D array structure: [round][match][player]
#  player ids are stored in the array
#  Example layout: {"bracket": [[[1, 2], [3, 4], [5, 6], [7, 8]], [[0, 0], [0, 0]], [[0, 0]]]}
#       (0s denote null playerids)

#class Match(models.Model):
#  player1 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='player1')
#  player2 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='player2') 
#  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE) 
#  winner = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='winner')
