from django.urls import path
from . import views

urlpatterns = [
    path('', views.matchMaker, name='matchMaker'),
    path('signUpPage/', views.signUpPage, name='signUpPage'),
    path('loginPage/',  views.loginPage, name='loginPage'),
]