# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: middleware.py
# Purpose: Code for that runs on every request the user make 
#if the user is banned by the admin the user wil be logged out

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

class BannedUserMiddleware:
    #function called every time the server starts
    def __init__(self,get_response): 
        self.get_response=get_response
    #function called every time when a new request is made
    def __call__(self,request):
        if request.user.is_authenticated:
            member=getattr(request.user,"member",None)
            if member and member.is_banned:
                logout(request)
                message.error(request,f"your account was banned.reason:{memeber.ban_reason}")
                return redirect("loginPage")
        return self.get_response(request)
