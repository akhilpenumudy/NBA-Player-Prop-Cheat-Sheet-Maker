import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from teamNames import team_name_to_abbreviation
import json
import http.client
import requests
from parlayMaker import generate_nba_parlays_merged

API_KEY = "enter your API key"

st.set_page_config(
    page_title="NBA Cheat Sheets",
    page_icon="📋",
)


st.write("## Player Prop Cheat Sheets 🏀")
if "selected_matchup" not in st.session_state:
    st.session_state.selected_matchup = 0


@st.cache_data
def call_endpoint_with_players_and_teams(url, max_level=3):
    """
    Fetches data from the PrizePicks API and includes player names and their team names.

    Parameters:
        url (str): The API endpoint to call.
        max_level (int): The level of JSON normalization to apply.

    Returns:
        pd.DataFrame: A DataFrame containing the main data with player names and team names.
    """
    # Fetch the API response
    resp = requests.get(url).json()

    # Normalize the main data
    data = pd.json_normalize(resp["data"], max_level=max_level)

    # Normalize the included data
    included = pd.json_normalize(resp["included"], max_level=max_level)

    # Filter for player data in the included section
    players = included[included["type"] == "new_player"][
        ["id", "attributes.name", "attributes.team", "attributes.team_name"]
    ].rename(
        columns={
            "id": "player_id",
            "attributes.name": "player_name",
            "attributes.team": "team_abbreviation",
            "attributes.team_name": "team_name",
        }
    )

    # Merge the player names and team names into the main data
    data = pd.merge(
        data,
        players,
        how="left",
        left_on=["relationships.new_player.data.id"],
        right_on=["player_id"],
    )

    return data


# API URL for NBA projections
url = "https://partner-api.prizepicks.com/projections?league_id=7&per_page=1000"

# Call the function and fetch data with player names and team names
df = call_endpoint_with_players_and_teams(url)
# Select the desired columns from the DataFrame
o_df = df[
    [
        "player_name",
        "team_abbreviation",
        "attributes.stat_type",
        "attributes.line_score",
    ]
].copy()
o_df = o_df[~o_df["attributes.stat_type"].str.contains(r"\(Combo\)", na=False)]
o_df = o_df[~o_df["attributes.stat_type"].str.contains("Fantasy Score", na=False)]
o_df = o_df.rename(
    columns={
        "player_name": "Player",
        "team_abbreviation": "Team",
        "attributes.stat_type": "Stat",
        "attributes.line_score": "Line",
    }
)
# gets the main o_df ready

all_games_playing = pd.read_csv("januarySchedule.csv")
df = o_df

# in the all games_playing dataframe the first collumn in the "Date". Find all of the games that are playing today. the format of the date in the collumn is: Wed Jan 1 2025
today = pd.to_datetime("today").strftime("%a %b %d %Y")
today_games = all_games_playing[all_games_playing["Date"] == today]
# gets the teams playing today in abbreviation form
teamsToday = today_games[["Visitor/Neutral", "Home/Neutral"]].copy()
teamsToday["Visitor/Neutral"] = teamsToday["Visitor/Neutral"].apply(
    lambda x: team_name_to_abbreviation(x)
)
teamsToday["Home/Neutral"] = teamsToday["Home/Neutral"].apply(
    lambda x: team_name_to_abbreviation(x)
)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.write("Todays games - ", today)
    st.dataframe(teamsToday, hide_index=True, use_container_width=True)

allmatchups = []
matchup_names = []  # Store matchup names for dropdown

for index, row in teamsToday.iterrows():
    visitor = row["Visitor/Neutral"]
    home = row["Home/Neutral"]
    matchup_key = f"{visitor}_vs_{home}"
    matchup_names.append(f"{visitor} vs {home}")  # Add readable matchup name

    # Filter the df DataFrame for players from the visitor and home teams
    visitor_data = df[df["Team"] == visitor]
    home_data = df[df["Team"] == home]

    # Combine the data for the matchup
    matchup_df = pd.concat([visitor_data, home_data], ignore_index=True)

    # Dynamically create a DataFrame variable for the matchup
    globals()[matchup_key] = matchup_df
    allmatchups.append(matchup_df)  # Store the dataframe in the list

# Calculate number of rows needed (4 buttons per row)
num_rows = (len(matchup_names) + 3) // 4

# Create containers - one for buttons and one for the table
button_container = st.container()
table_container = st.container()

# Use the button container for the grid of buttons
with button_container:
    # Iterate through rows
    for row in range(num_rows):
        # Create 4 columns for each row
        cols = st.columns(4)

        # Create buttons for this row
        for col_idx in range(4):
            matchup_idx = row * 4 + col_idx

            # Check if we still have matchups to display
            if matchup_idx < len(matchup_names):
                with cols[col_idx]:
                    if st.button(matchup_names[matchup_idx], key=f"btn_{matchup_idx}"):
                        st.session_state.selected_matchup = matchup_idx

conn = http.client.HTTPSConnection("tank01-fantasy-stats.p.rapidapi.com")

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "tank01-fantasy-stats.p.rapidapi.com",
}

conn.request("GET", "/getNBAPlayerList", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))  # put this in a data frame called playerList

# Convert the JSON data to a dictionary
player_data = json.loads(data.decode("utf-8"))
# Convert the 'body' dictionary to a pandas DataFrame
playerList = pd.DataFrame(player_data["body"])


# make me a function that takes in a player name and returns the player id
def get_player_id(player_name):
    # Filter the DataFrame to find the player
    player_row = playerList[playerList["longName"] == player_name]

    if not player_row.empty:
        # Return the player ID
        return player_row.iloc[0]["playerID"]
    else:
        return None


# Function to fetch the last N games for a player
def get_last_n_games(player_id, season=2024, n=15):
    conn = http.client.HTTPSConnection("tank01-fantasy-stats.p.rapidapi.com")
    headers = {
        "x-rapidapi-key": API_KEY,  # Replace with your API key
        "x-rapidapi-host": "tank01-fantasy-stats.p.rapidapi.com",
    }
    # Make the API request
    conn.request(
        "GET",
        f"/getNBAGamesForPlayer?playerID={player_id}&season={season}&fantasyPoints=true&pts=1&reb=1.25&stl=3&blk=3&ast=1.5&TOV=-1&mins=0&doubleDouble=0&tripleDouble=0&quadDouble=0",
        headers=headers,
    )
    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data.decode("utf-8"))

    # Return the games data
    if json_data.get("statusCode") == 200:
        games_data = json_data.get("body", {})
        # Sort games by date (assuming gameID contains date) and return the last N games
        sorted_games = sorted(games_data.items(), key=lambda x: x[0], reverse=True)[:n]
        return dict(sorted_games)
    else:
        print(
            f"Error fetching games for player ID {player_id}: {json_data.get('message', 'Unknown error')}"
        )
        return {}


# Function to calculate hit rate for each prop
@st.cache_data
def calculate_hitrate(matchup_df, season=2025):
    # Add new columns for hit rates
    matchup_df["hitrate_last5"] = None
    matchup_df["hitrate_last10"] = None
    matchup_df["hitrate_last15"] = None

    # Group the DataFrame by player to avoid redundant API calls
    grouped_players = matchup_df.groupby("Player")

    for player_name, group in grouped_players:
        # Get player ID
        player_id = get_player_id(player_name)
        if not player_id:
            print(f"Player ID not found for {player_name}")
            continue

        # Fetch last 15 games (we'll use subsets for 5 and 10 games)
        games_data = get_last_n_games(player_id, season, n=15)
        if not games_data:
            print(f"No games found for {player_name}")
            continue

        # Extract subsets for last 5 and 10 games
        games_last5 = dict(list(games_data.items())[:5])
        games_last10 = dict(list(games_data.items())[:10])
        games_last15 = games_data  # Already has last 15 games

        # Calculate hit rates for each prop in the group
        for index, row in group.iterrows():
            stat = row["Stat"]
            line = row["Line"]

            def calculate_hit_count(games_data):
                hit_count = 0
                for game_id, game_stats in games_data.items():
                    if stat == "Pts+Asts":
                        player_stat = float(game_stats.get("pts", 0)) + float(
                            game_stats.get("ast", 0)
                        )
                    elif stat == "Rebs+Asts":
                        player_stat = float(game_stats.get("reb", 0)) + float(
                            game_stats.get("ast", 0)
                        )
                    elif stat == "Points":
                        player_stat = float(game_stats.get("pts", 0))
                    elif stat == "Rebounds":
                        player_stat = float(game_stats.get("reb", 0))
                    elif stat == "Assists":
                        player_stat = float(game_stats.get("ast", 0))
                    elif stat == "Steals":
                        player_stat = float(game_stats.get("stl", 0))
                    elif stat == "Blocks":
                        player_stat = float(game_stats.get("blk", 0))
                    elif stat == "Blks+Stls":
                        player_stat = float(game_stats.get("blk", 0)) + float(
                            game_stats.get("stl", 0)
                        )
                    elif stat == "Pts+Rebs":
                        player_stat = float(game_stats.get("pts", 0)) + float(
                            game_stats.get("reb", 0)
                        )
                    elif stat == "Pts+Rebs+Asts":
                        player_stat = (
                            float(game_stats.get("pts", 0))
                            + float(game_stats.get("reb", 0))
                            + float(game_stats.get("ast", 0))
                        )
                    elif stat == "3-PT Made":
                        player_stat = float(game_stats.get("tptfgm", 0))
                    elif stat == "Blocked Shots":
                        player_stat = float(game_stats.get("blk", 0))
                    elif stat == "Turnovers":
                        player_stat = float(
                            game_stats.get("TOV", 0)
                        )  # Corrected key for turnovers
                    elif stat == "FG Attempted":
                        player_stat = float(game_stats.get("fga", 0))
                    elif stat == "FG Made":
                        player_stat = float(game_stats.get("fgm", 0))
                    elif stat == "Defensive Rebounds":
                        player_stat = float(game_stats.get("DefReb", 0))
                    elif stat == "Offensive Rebounds":
                        player_stat = float(game_stats.get("OffReb", 0))
                    elif stat == "3-PT Attempted":
                        player_stat = float(game_stats.get("tptfga", 0))
                    else:
                        print(f"Unsupported stat: {stat}")
                        continue

                    if player_stat >= line:
                        hit_count += 1
                return hit_count

            # Calculate hit rates for last 5, 10, and 15 games
            hitrate_last5 = calculate_hit_count(games_last5)
            hitrate_last10 = calculate_hit_count(games_last10)
            hitrate_last15 = calculate_hit_count(games_last15)

            # Update hit rates in the DataFrame
            matchup_df.at[index, "hitrate_last5"] = f"{hitrate_last5}/5"
            matchup_df.at[index, "hitrate_last10"] = f"{hitrate_last10}/10"
            matchup_df.at[index, "hitrate_last15"] = f"{hitrate_last15}/15"

    return matchup_df


# if the last 5 games is 4/5 or 5/5 then make the background green. if it is 3/5 then make the background yellow. if it is 2/5 or less then make the background red
# if the last 10 games is 8/10 or 9/10 or 10/10 then make the background green. if it is 7/10 then make the background yellow. if it is 6/10 or less then make the background red
# if the last 15 games is 12/15 or 13/15 or 14/15 or 15/15 then make the background green. if it is 11/15 then make the background yellow. if it is 10/15 or less then make the background red
def highlight_hitrate(row):
    styles = [""] * len(row)

    last_5 = row["Last 5 games"]
    last_10 = row["Last 10 games"]
    last_15 = row["Last 15 games"]

    if last_5 == "4/5" or last_5 == "5/5":
        styles[row.index.get_loc("Last 5 games")] = (
            "background-color: rgba(0, 255, 0, 0.3)"
        )
    elif last_5 == "3/5":
        styles[row.index.get_loc("Last 5 games")] = (
            "background-color: rgba(255, 255, 0, 0.3)"
        )
    elif last_5 in ["2/5", "1/5", "0/5"]:
        styles[row.index.get_loc("Last 5 games")] = (
            "background-color: rgba(255, 0, 0, 0.3)"
        )

    if last_10 in ["8/10", "9/10", "10/10"]:
        styles[row.index.get_loc("Last 10 games")] = (
            "background-color: rgba(0, 255, 0, 0.3)"
        )
    elif last_10 == "7/10":
        styles[row.index.get_loc("Last 10 games")] = (
            "background-color: rgba(255, 255, 0, 0.3)"
        )
    elif last_10 in ["6/10", "5/10", "4/10", "3/10", "2/10", "1/10", "0/10"]:
        styles[row.index.get_loc("Last 10 games")] = (
            "background-color: rgba(255, 0, 0, 0.3)"
        )

    if last_15 in ["12/15", "13/15", "14/15", "15/15"]:
        styles[row.index.get_loc("Last 15 games")] = (
            "background-color: rgba(0, 255, 0, 0.3)"
        )
    elif last_15 == "11/15":
        styles[row.index.get_loc("Last 15 games")] = (
            "background-color: rgba(255, 255, 0, 0.3)"
        )
    elif last_15 in [
        "10/15",
        "9/15",
        "8/15",
        "7/15",
        "6/15",
        "5/15",
        "4/15",
        "3/15",
        "2/15",
        "1/15",
        "0/15",
    ]:
        styles[row.index.get_loc("Last 15 games")] = (
            "background-color: rgba(255, 0, 0, 0.3)"
        )

    return styles


# actually calculating the hitrate
allmatchups[st.session_state.selected_matchup] = calculate_hitrate(
    allmatchups[st.session_state.selected_matchup]
)


# renames the columns
for i in allmatchups:
    i.rename(
        columns={
            "hitrate_last5": "Last 5 games",
            "hitrate_last10": "Last 10 games",
            "hitrate_last15": "Last 15 games",
        },
        inplace=True,
    )

# Filter out Dunks and Free Throws Made
filtered_df = allmatchups[st.session_state.selected_matchup][
    ~allmatchups[st.session_state.selected_matchup]["Stat"].isin(
        ["Dunks", "Free Throws Made"]
    )
]


with table_container:
    if "selected_matchup" in st.session_state:
        st.markdown("---")
        # check length of filtered_df
        if len(filtered_df) == 0:
            st.info(
                "No active player props available for this game. The game might be in progress or has already happened."
            )
        else:
            st.dataframe(
                filtered_df.style.apply(highlight_hitrate, axis=1),
                hide_index=True,
                use_container_width=True,
            )
            st.markdown(
                "<p style='font-size: 12px; display: inline;'>📌 Betting data scraped from <span style=color:#d742f5;> Prize Picks</span></p>",
                unsafe_allow_html=True,
            )

            # Add a header for the parlays section
            st.markdown("---")
            st.markdown("#### 🎯 Recommended *Same Game Parlays*")
            parlays = generate_nba_parlays_merged(
                filtered_df,
                min_hitrate=0.65,
                max_parlays=5,
                legs=2,
            )

            if parlays and len(parlays[0]) > 0:
                # Create columns for displaying parlays side by side
                num_parlays = len(parlays[0])
                cols = st.columns(min(num_parlays, 2))  # Max 3 parlays per row

                # Iterate through each parlay
                for idx, parlay in parlays[0].iterrows():
                    col_idx = idx % 2  # Determine which column to use
                    with cols[col_idx]:
                        # Create a container for each parlay
                        with st.container():
                            st.markdown(
                                f"**🎲 Parlay #{idx + 1}** ({round(parlay['Parlay Probability']*100, 2)}%)"
                            )

                            # Display each leg of the parlay
                            for leg in range(1, 3):  # For 2-leg parlays
                                # Display each leg of the parlay
                                direction_color = (
                                    "green"
                                    if parlay[f"Leg {leg} Direction"] == "Over"
                                    else "red"
                                )
                                st.markdown(
                                    f"""
                                    - {parlay[f'Leg {leg} Player']} 
                                    <span style='color: {direction_color}'>{parlay[f'Leg {leg} Direction']}</span> {parlay[f'Leg {leg} Line']} {parlay[f'Leg {leg} Stat']} 
                                    \n
                                    """,
                                    unsafe_allow_html=True,
                                )
                            st.markdown("---")
            else:
                st.warning("No high-confidence parlays found for this game.")
