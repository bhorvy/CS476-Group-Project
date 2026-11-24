# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: lookup.py
# Purpose: Code for looking up game ranks via various APIs

import os
import requests
from .helpers import LEAGUE_UPPER_TIER_VALUES, RIOT_PLATFORM_ROUTING, league_rank_value, rank_label_for_value

#https://docs.python.org/3/tutorial/errors.html
class RankLookupError(Exception):
    pass

def deadlock_rank(external_player_id):

    url = f"https://api.deadlock-api.com/v1/players/{external_player_id}/rank"
    headers = {}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RankLookupError(f"Deadlock API returned HTTP {response.status_code}.")
    data = response.json();

    value = (data.get("badge"))
    
    display = rank_label_for_value("Deadlock", value)
    if display is None:
        raise RankLookupError("Deadlock API returned an unsupported rank.")
    return (display, value)


def valorant_rank(game_name, tag_line, region):
    api_key = os.environ.get("HENRIKDEV_API_KEY")
    if not api_key:
        raise RankLookupError("Valorant rank syncing is not configured.")
    game_name = game_name.strip()
    tag_line = tag_line.strip()
    region = region.strip()
    if region not in {"na", "eu", "ap", "kr", "latam", "br"}:
        raise RankLookupError("Enter a Valorant region: na, eu, ap, kr, latam, or br.")
    url = ("https://api.henrikdev.xyz/valorant/v1/mmr/"f"{region}/{game_name}/{tag_line}")
   
    headers = {"Authorization": api_key}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RankLookupError(f"Valorant API returned HTTP {response.status_code}.")
    data = response.json()["data"]

    tier = data.get("currenttier")
    display = data.get("currenttierpatched")
   
    return (display, tier)


def league_of_legends_rank(game_name, tag_line, platform):
    api_key = os.environ.get("RIOT_API_KEY")
    if not api_key:
        raise RankLookupError("League of Legends rank syncing is not configured.")
    game_name = game_name.strip()
    tag_line = tag_line.strip()
    platform = platform.strip()
    routing = RIOT_PLATFORM_ROUTING.get(platform)
    if routing is None:
        raise RankLookupError("Enter a valid League platform region (for example, na1 or euw1).")
  
    headers = {"X-Riot-Token": api_key}
    account_url = (f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}")
    response = requests.get(account_url, headers=headers)
    if response.status_code != 200:
        raise RankLookupError(f"Riot API returned HTTP {response.status_code}.")
    account_data = response.json();
    puuid = account_data.get("puuid")
    
    url = (f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RankLookupError(f"League API returned HTTP {response.status_code}.")
    entries = response.json()
    solo = None
    for entry in entries:
        if entry.get("queueType") == "RANKED_SOLO_5x5":
            solo = entry
    if not solo:
        return ("Unrated", 0)

    tier = solo["tier"]
    
    value = LEAGUE_UPPER_TIER_VALUES.get(tier) or league_rank_value(tier, solo["rank"])

    display = rank_label_for_value("League of Legends", value)
    return (display, value)


def fetch_game_rank(game_title, username, external_player_id, game_tag):
    game = game_title.strip().casefold()
    if game == "deadlock":
        return deadlock_rank(external_player_id)
    if game == "valorant":
        return valorant_rank(username.strip(), game_tag.strip(), external_player_id)
    if game == "league of legends":
        return league_of_legends_rank(username.strip(), game_tag.strip(), external_player_id)