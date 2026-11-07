from django.urls import path
from . import views

urlpatterns = [
    path('', views.matchMaker, name='matchMaker'),
    path('signUpPage/', views.signUpPage, name='signUpPage'),
    path('loginPage/',  views.loginPage, name='loginPage'),
    path('tournament/', views.TournamentList, name='tournamentList'),
    path('team/', views.teamPage, name='teamPage'),
    path('team/<int:team_id>/join/', views.joinTeam, name='joinTeam'),
    path('tournament/<int:tid>/register/', views.registerForTournament, name='registerTournament'),
    path('tournament/<int:tid>/', views.tournamentPage, name='tournamentPage'),
    path('manage-tournament/<int:tid>/', views.manageTournament, name='manageTournament'),
    path('homePage/', views.homePage, name='homePage'),
    path('profilePage/', views.profilePage, name='profilePage'),
    path('gameAccount/', views.gameAccount, name='gameAccount'),
    path('create-tournament/', views.tournamentCreatePage, name='createTournament'),
    path('score-popup', views.scorePopup, name='scorePopup'),
    path('logout/', views.logoutHandler, name='logoutHandler')
]