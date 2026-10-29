from django.urls import path
from . import views

urlpatterns = [
    path('', views.matchMaker, name='matchMaker'),
    path('signUpPage/', views.signUpPage, name='signUpPage'),
    path('loginPage/',  views.loginPage, name='loginPage'),
    path('tournament/<int:tid>/', views.tournamentPage, name='tournamentPage'),
    path('homePage/', views.homePage, name='homePage'),
    path('profilePage/', views.profilePage, name='profilePage'),
    path('gameAccount/', views.gameAccount, name='gameAccount'),
    path('create-tournament/', views.tournamentCreatePage, name='createTournament')
]