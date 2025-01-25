import pandas as pd
import itertools
import numpy as np


def generate_nba_parlays_merged(merged_df, min_hitrate=0.6, max_parlays=100, legs=2):
    """
    Generates NBA parlays from a single merged DataFrame with improved efficiency.

    Args:
      merged_df: A pandas DataFrame containing all prop bets.
      min_hitrate: Minimum average hit rate to consider (default: 0.6)
      max_parlays: Maximum number of parlays to return (default: 100)
      legs: Number of legs in parlay (2 or 3, default: 2)
    """
    # Vectorized hit rate calculations
    merged_df["Hit Rate 5"] = merged_df["Last 5 games"].str.split("/").str[0].astype(
        float
    ) / merged_df["Last 5 games"].str.split("/").str[1].astype(float)
    merged_df["Hit Rate 10"] = merged_df["Last 10 games"].str.split("/").str[0].astype(
        float
    ) / merged_df["Last 10 games"].str.split("/").str[1].astype(float)
    merged_df["Hit Rate 15"] = merged_df["Last 15 games"].str.split("/").str[0].astype(
        float
    ) / merged_df["Last 15 games"].str.split("/").str[1].astype(float)

    # Calculate average hit rate for both over and under scenarios
    merged_df["Over_Hit_Rate"] = (
        merged_df["Hit Rate 5"] + merged_df["Hit Rate 10"] + merged_df["Hit Rate 15"]
    ) / 3
    merged_df["Under_Hit_Rate"] = 1 - merged_df["Over_Hit_Rate"]

    # Create separate dataframes for over and under opportunities with stricter filtering
    over_props = merged_df[merged_df["Over_Hit_Rate"] >= min_hitrate].copy()
    under_props = merged_df[merged_df["Under_Hit_Rate"] >= min_hitrate].copy()

    over_props["Direction"] = "Over"
    over_props["Avg_Hit_Rate"] = over_props["Over_Hit_Rate"]
    under_props["Direction"] = "Under"
    under_props["Avg_Hit_Rate"] = under_props["Under_Hit_Rate"]

    # Combine promising props and ensure team diversity
    promising_props = pd.concat([over_props, under_props])

    # Sort by hit rate and get top props while ensuring team diversity
    top_props = promising_props.sort_values("Avg_Hit_Rate", ascending=False)

    # Ensure we don't have more than 3 props from the same team
    team_counts = {}
    filtered_props = []
    for idx, row in top_props.iterrows():
        team = row["Team"]
        if team not in team_counts:
            team_counts[team] = 0
        if team_counts[team] < 3:
            filtered_props.append(idx)
            team_counts[team] += 1

    # Convert filtered props to DataFrame
    promising_props = promising_props.loc[filtered_props]

    # Convert to numpy array for faster operations
    props_array = promising_props.index.values
    parlay_list = []

    # Generate parlays based on specified number of legs
    for leg_combo in itertools.combinations(props_array, legs):
        leg_props = [promising_props.loc[leg] for leg in leg_combo]

        # Check if all props are from the same team
        teams = set(leg["Team"] for leg in leg_props)
        if len(teams) < 2:  # Skip if all props are from the same team
            continue

        # Calculate parlay probability
        parlay_prob = 1
        for leg in leg_props:
            parlay_prob *= leg["Avg_Hit_Rate"]

        if parlay_prob >= min_hitrate:
            parlay_data = {}
            for i, leg in enumerate(leg_props, 1):
                parlay_data.update(
                    {
                        f"Leg {i} Player": [leg["Player"]],
                        f"Leg {i} Team": [leg["Team"]],
                        f"Leg {i} Stat": [leg["Stat"]],
                        f"Leg {i} Line": [leg["Line"]],
                        f"Leg {i} Direction": [leg["Direction"]],
                    }
                )
            parlay_data["Parlay Probability"] = [parlay_prob]

            parlay_df = pd.DataFrame(parlay_data)
            parlay_list.append(parlay_df)

        if len(parlay_list) >= max_parlays:
            break

    # Sort by probability and return top parlays
    if parlay_list:
        combined_parlays = pd.concat(parlay_list, ignore_index=True)
        return [combined_parlays.nlargest(max_parlays, "Parlay Probability")]
    return []


# df = pd.read_csv("Test.csv")
# parlays = generate_nba_parlays_merged(df, min_hitrate=0.6, max_parlays=100, legs=2)
# Eparlays[0].to_csv("parlays.csv", index=False)
