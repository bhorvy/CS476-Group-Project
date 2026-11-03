from django.urls import path
from . import views

urlpatterns = [
    path('', views.matchMaker, name='matchMaker'),
    path('signUpPage/', views.signUpPage, name='signUpPage'),
    path('loginPage/',  views.loginPage, name='loginPage'),
    path('tournament/<int:tid>/', views.tournamentPage, name='tournamentPage'),
    path('manage-tournament/<int:tid>/', views.manageTournament, name='manageTournament'),
    path('homePage/', views.homePage, name='homePage'),
    path('profilePage/', views.profilePage, name='profilePage'),
    path('gameAccount/', views.gameAccount, name='gameAccount'),
    path('create-tournament/', views.tournamentCreatePage, name='createTournament'),
<<<<<<< HEAD
    path('score-popup/', views.scorePopup, name='scorePopup'),
=======
    path('score-popup', views.scorePopup, name='scorePopup'),
    path('loginUserType/', views.loginUserType, name='loginUserType'),
    path('registerUserType/', views.registerUserType, name='registerUserType'),
    path('registerAdmin', views.registerAdmin, name= 'registerAdmin'),
>>>>>>> 7f449ae846507e4db0d64f5df8a584fafc45490d
    path('logout/', views.logoutHandler, name='logoutHandler')
]