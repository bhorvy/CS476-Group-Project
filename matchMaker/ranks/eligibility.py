# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: eligibility.py
# Purpose: Code for checking tournament rank eligibility constraints

from ..models import GameAccount
from .helpers import rank_label_for_value


def member_rank_eligibility_error(member, tournament):
    # Check if member's rank qualifies for tournament min/max ranks
    minimum = tournament.min_rank
    maximum = tournament.max_rank
    if not minimum and not maximum:
        return None
    
    if (minimum is None) or (maximum is None):
        return "This tournament has invalid rank limits. Ask an admin to update them."

    # Get the member's rank for this game
    account = GameAccount.objects.filter(
        member=member,
        game_title=tournament.game_title,
    ).exclude(rank_value=None).order_by("-last_synced").first()
    if account is None:
        return (f"{member.user.username} must link and sync a " f"{tournament.game_title} rank before registering.")

    if int(minimum) is not None and account.rank_value < int(minimum):
        minimum_label = rank_label_for_value(tournament.game_title, int(minimum))
        return (f"{member.user.username} is below the minimum rank " f"({minimum_label}).")
    if int(maximum) is not None and account.rank_value > int(maximum):
        maximum_label = rank_label_for_value(tournament.game_title, int(maximum))
        return (f"{member.user.username} is above the maximum rank " f"({maximum_label}).")
    return None


def rank_eligibility_errors(members, tournament):
    # Check all members and collect any eligibility errors
    errors = []
    for member in members:
        error = member_rank_eligibility_error(member, tournament)
        if error:
            errors.append(error)
    return errors
