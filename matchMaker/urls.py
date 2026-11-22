# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: urls.py
# Purpose: Code for all url paths

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
    path('profilePage/edit/', views.editProfile, name='editProfile'),
    path('gameAccount/', views.gameAccount, name='gameAccount'),
    path('create-tournament/', views.tournamentCreatePage, name='createTournament'),
    path('score-popup', views.scorePopup, name='scorePopup'),
    path('logout/', views.logoutHandler, name='logoutHandler'),
    path("notifications/", views.tournamentNotifications, name="tournamentNotifications"),
    path('admin-tools/member/<int:member_id>/ban/', views.adminBanMember, name='adminBanMember'),
    path('admin-tools/member/<int:member_id>/unban/', views.adminUnbanMember, name='adminUnbanMember'),
    path('admin-tools/members/', views.adminMemberList, name='adminMemberList'),
]