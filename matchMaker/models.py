from django.db import models
from django.conf import settings

# Create your models here.
class Member(models.Model):
  user = models.OneToOneField(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE
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