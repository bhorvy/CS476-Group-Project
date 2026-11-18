from django.db import transaction
from .models import Member,ScoreChange
from .tournamentFactory.singleElim import SingleElimination 
from .observers.bracketUpdateSubject import notify_tournament_updated

class BanError(Exception):
    pass

def ban_member(memeber,reason):
    if member.is_power_user:
        raise BanError("power user cannot be banned")
    if member.is_banned:
        raise BanError("user is already banned")
    member.is_banned = True
    member.ban_reason = reason
    memeber.save(updae_fields=["is_banned","ban_reason"])

def overwrite_match_scores(tournment_id,round_id,match_id,score1,sore2,admin_user,reason):
    tournament = SingleElimination(tournament_id)
    layout = tournament.layout
    try:
        players=layout["bracket"][round_id][match_id]["players"]
    except (IndexError,KeyError):
        raise ValueError("that match does not exist")
    if len(players) != 2:
        raise ValueError("match does not have two player")
    
    old_scores = [p.get("score",0) for p in players]
    players[0]["score"] = score1
    players[0]["score"] = score2
    
    with transaction.atomic():
        tournament.object.layout = layout
        tournament.object.save(update_fields=["layout"])
        ScoreChanges.objects.create(
            tournament = tournament.object,
            round_number = round_id,
            match_number = match_id,
            changed_by = admin_user,
            old_scores = old_scores,
            new_scores = [score1,score2],
            reason = reason,
        )
    
    player_ids = [p["player_id"] for p in players if p["player_id"] !=0]
    members = memeber.objects.filter(id__in=player_ids)
    notify_tournament_updated(tournament.object,members, "your match score was changed by the admin")
    return tournament.object