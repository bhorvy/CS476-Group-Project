from django.urls import path
from . import views

urlpatterns = [
    path('matchMaker/', views.matchMaker, name='matchMaker'),
    path('matchMaker/signUpPage/', views.signUpPage, name='signUpPage'),
    path('matchMaker/loginPage/', views.loginPage, name='loginPage'),
]