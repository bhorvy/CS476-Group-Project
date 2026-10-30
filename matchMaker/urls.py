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
    path('create-tournament/', views.tournamentCreatePage, name='createTournament'),
    path('score-popup/', views.scorePopup, name='scorePopup'),
    path('loginUserType/', views.loginUserType, name='loginUserType'),
    path('registerUserType/', views.registerUserType, name='registerUserType'),
    path('registerAdmin', views.registerAdmin, name= 'registerAdmin'),
    path('logout/', views.logoutHandler, name='logoutHandler')
]