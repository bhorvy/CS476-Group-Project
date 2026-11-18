# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: models.py
# Purpose: Code for setting the rules for banning the member 

from .models import Member

class BanError(Exception):
    pass

#check who can be baned, who cannot be and raise an error 
def ban_member(member,reason):
    if member.is_power_user:
        raise BanError("power user cannot be banned")
    if member.is_banned:
        raise BanError("user is already banned")
    member.is_banned = True
    member.ban_reason = reason
    member.save(update_fields=["is_banned","ban_reason"])
