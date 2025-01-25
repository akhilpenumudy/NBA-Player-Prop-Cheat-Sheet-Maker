# Mapping of team names to abbreviations
team_name_to_abbr = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Brooklyn Nets": "BKN",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTH",
    "Washington Wizards": "WAS",
    "San Antonio Spurs": "SAS",
}


def team_name_to_abbreviation(team_name):
    """
    Converts a full NBA team name to its corresponding abbreviation.

    Parameters:
        team_name (str): The full name of the NBA team.

    Returns:
        str: The abbreviation of the NBA team, or None if not found.
    """
    return team_name_to_abbr.get(team_name, None)
