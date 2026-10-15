from django.urls import path
from . import views

urlpatterns = [
    path('matchMaker/', views.matchMaker, name='matchMaker'),
]