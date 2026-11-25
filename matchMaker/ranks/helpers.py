# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: helpers.py
# Purpose: Code for rank definitions and lookup functions across games

DEADLOCK_RANKS = (
    "Obscurus",
    "Initiate",
    "Seeker",
    "Acolyte",
    "Sentinel",
    "Mystic",
    "Ritualist",
    "Emissary",
    "Oracle",
    "Phantom",
    "Ascendant",
    "Eternus",
)

# values are tier * 10 + subrank
DEADLOCK_CHOICES = [("0", DEADLOCK_RANKS[0])]
for rank in range(1, len(DEADLOCK_RANKS)):
    for subrank in range(1, 7):
        DEADLOCK_CHOICES.append((str(rank * 10 + subrank), f"{DEADLOCK_RANKS[rank]} {subrank}"))

VALORANT_CHOICES = [("0", "Unrated")]
valorant_tiers = [
    ("Iron", 3),
    ("Bronze", 6),
    ("Silver", 9),
    ("Gold", 12),
    ("Platinum", 15),
    ("Diamond", 18),
    ("Ascendant", 21),
    ("Immortal", 24),
]
for tier_name, first_value in valorant_tiers:
    for subrank in range(1, 4):
        VALORANT_CHOICES.append((str(first_value + subrank - 1), f"{tier_name} {subrank}"))
VALORANT_CHOICES.append(("27", "Radiant"))

VALORANT_REGIONS = ("na", "eu", "ap", "kr", "latam", "br")
LEAGUE_REGIONS = ("na1", "br1", "la1", "la2","kr", "jp1", "eun1", "euw1","tr1" "ru", "oc1", "ph2","sg2", "th2", "tw2", "vn2")

# base value is the IV division of each tier, and the other divisions add an offset
LEAGUE_DIVISION_VALUES = {
    "IV": 0,
    "III": 1,
    "II": 2,
    "I": 3,
}

LEAGUE_TIER_BASES = (
    ("IRON", "Iron", 1),
    ("BRONZE", "Bronze", 5),
    ("SILVER", "Silver", 9),
    ("GOLD", "Gold", 13),
    ("PLATINUM", "Platinum", 17),
    ("EMERALD", "Emerald", 21),
    ("DIAMOND", "Diamond", 25),
)
LEAGUE_CHOICES = [("0", "Unrated")]
for _, tier_name, base_value in LEAGUE_TIER_BASES:
    for division, division_offset in LEAGUE_DIVISION_VALUES.items():
        LEAGUE_CHOICES.append((str(base_value + division_offset), f"{tier_name} {division}"))
LEAGUE_CHOICES.append(("29", "Master"))
LEAGUE_CHOICES.append(("30", "Grandmaster"))
LEAGUE_CHOICES.append(("31", "Challenger"))

LEAGUE_UPPER_TIER_VALUES = {
    "MASTER": 29,
    "GRANDMASTER": 30,
    "CHALLENGER": 31,
}

# the same number can mean different ranks in different games, so each game keeps its own list
RANK_CHOICES = {
    "Deadlock": tuple(DEADLOCK_CHOICES),
    "Valorant": tuple(VALORANT_CHOICES),
    "League of Legends": tuple(LEAGUE_CHOICES),
}
SUPPORTED_RANKED_GAMES = ("Deadlock", "Valorant", "League of Legends")
GAME_TITLE_CHOICES = (
    ("Deadlock", "Deadlock"),
    ("Valorant", "Valorant"),
    ("League of Legends", "League of Legends"),
    ("OTHER", "Other"),
)

# help text for the game account form
GAME_ACCOUNT_HELP = {
    "Deadlock": {
        "label": "Steam ID",
        "help": "Enter your numeric steam account ID.",
        "account_name_help": "Enter your display name for the your account.",
        "tag_help": "",
    },
    "Valorant": {
        "label": "Region",
        "help": "Use na, eu, ap, kr, latam, or br.",
        "account_name_help": "Enter your Riot game name.",
        "tag_help": "Enter your tag, for example NA1.",
    },
    "League of Legends": {
        "label": "Platform region",
        "help": "Use your region: na1, br1, la1, la2, kr, jp1, eun1, euw1, tr1, ru, oc1, ph2, sg2, th2, tw2, or vn2.",
        "account_name_help": "Enter your Riot game name.",
        "tag_help": "Enter your tag, for example NA1.",
    },
    "OTHER": {
        "label": "",
        "help": "",
        "account_name_help": "Enter the username for this game account.",
        "tag_help": "",
    },
}


# get the ranks and subranks for a given game
def rank_choices_for_game(game_title):
    for supported_game, choices in RANK_CHOICES.items():
        if game_title == supported_game:
            return choices
    return ()

def rank_label_for_value(game_title, rank_value):
    for value, label in rank_choices_for_game(game_title):
        if value == str(rank_value):
            return label
    return None

# regional routing group that Riot's API expects for each platform region
RIOT_PLATFORM_ROUTING = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "kr": "asia", "jp1": "asia", "eun1": "europe", "euw1": "europe",
    "tr1": "europe", "ru": "europe", "oc1": "sea", "ph2": "sea",
    "sg2": "sea", "th2": "sea", "tw2": "sea", "vn2": "sea",
}

def league_rank_value(tier, division):
    for tier_code, _, base_value in LEAGUE_TIER_BASES:
        if tier == tier_code:
            return base_value + LEAGUE_DIVISION_VALUES[division]

    raise ValueError("Invalid League tier.")