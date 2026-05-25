"""
Data Compiler for MadnessEV

Loads and merges all odds data sources into one clean DataFrame
ready for the backtest pipeline.

Two sources:
1. data/historical/2026_tournament_odds.csv — full tournament, 63 games
   Mix of real sourced and approximated odds (source column tells you which)
2. data/raw/odds_data.json — 6 Sweet 16/Elite Eight games
   Real multi-bookmaker odds from The Odds API

Strategy:
  For games that exist in BOTH sources, prefer the JSON data
  (multi-bookmaker real data beats single-bookmaker sourced data)
  For all other games, use the CSV.
"""

import json
import pandas as pd
from pathlib import Path
from src.team_names import normalize_team_name

# File paths
ODDS_JSON_PATH   = Path("data/raw/odds_data.json")
ODDS_CSV_PATH    = Path("data/historical/2026_tournament_odds.csv")


# ============================================================
# STEP 1 — Load and parse the CSV
# ============================================================

def load_csv_odds() -> pd.DataFrame:
    """
    Loads the tournament odds CSV and normalizes team names.

    Returns a clean DataFrame with columns:
        team_a, team_b, seed_a, seed_b,
        odds_a, odds_b, round, winner,
        source, data_quality
    """
    if not ODDS_CSV_PATH.exists():
        print(f"CSV not found at {ODDS_CSV_PATH}")
        return None

    df = pd.read_csv(ODDS_CSV_PATH)

    # Normalize team names to CBBD standard
    df["team_a"] = df["team_a"].apply(normalize_team_name)
    df["team_b"] = df["team_b"].apply(normalize_team_name)
    df["winner"] = df["winner"].apply(normalize_team_name)

    # Add data quality flag — makes it easy to filter later
    # "real" = sourced from actual bookmaker, "approximated" = seed-based estimate
    df["data_quality"] = df["source"].apply(
        lambda s: "real" if "real" in str(s) else "approximated"
    )

    print(f"Loaded {len(df)} games from CSV.")
    print(f"  Real sourced: {len(df[df['data_quality'] == 'real'])}")
    print(f"  Approximated: {len(df[df['data_quality'] == 'approximated'])}")

    return df


# ============================================================
# STEP 2 — Load and parse the JSON (multi-bookmaker data)
# ============================================================

def extract_best_odds(game: dict) -> dict:
    """
    Extracts the best available moneyline odds for each team
    across all bookmakers in a single game's JSON entry.

    'Best' means:
      - For the favorite (negative odds): least negative = least you risk
      - For the underdog (positive odds): most positive = most you win

    Args:
        game: One game entry from odds_data.json

    Returns a dict with:
        team_a, team_b, odds_a, odds_b,
        best_book_a, best_book_b, num_bookmakers
    """
    home_team = normalize_team_name(game["home_team"])
    away_team = normalize_team_name(game["away_team"])

    best_odds = {}  # { team_name: best_odds_so_far }
    best_book = {}  # { team_name: bookmaker_name }
    bookmaker_count = 0

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market["key"] != "h2h":
                continue

            bookmaker_count += 1

            for outcome in market.get("outcomes", []):
                team = normalize_team_name(outcome["name"])
                price = outcome["price"]

                if team not in best_odds:
                    best_odds[team] = price
                    best_book[team] = bookmaker["title"]
                else:
                    current = best_odds[team]
                    # Better odds = higher number always
                    # -150 is better than -200 for favorites
                    # +200 is better than +150 for underdogs
                    if price > current:
                        best_odds[team] = price
                        best_book[team] = bookmaker["title"]

    # Find which team is home and which is away
    teams = list(best_odds.keys())
    if len(teams) < 2:
        return None

    # Use home/away order from the JSON
    team_a = home_team
    team_b = away_team

    if team_a not in best_odds or team_b not in best_odds:
        # Try to match by partial name
        for t in teams:
            if home_team.lower() in t.lower() or t.lower() in home_team.lower():
                team_a = t
            if away_team.lower() in t.lower() or t.lower() in away_team.lower():
                team_b = t

    if team_a not in best_odds or team_b not in best_odds:
        print(f"Could not match teams for: {game['home_team']} vs {game['away_team']}")
        return None

    return {
        "team_a":          team_a,
        "team_b":          team_b,
        "odds_a":          best_odds[team_a],
        "odds_b":          best_odds[team_b],
        "best_book_a":     best_book[team_a],
        "best_book_b":     best_book[team_b],
        "num_bookmakers":  bookmaker_count,
        "commence_time":   game.get("commence_time"),
    }


def load_json_odds() -> pd.DataFrame:
    """
    Loads the Odds API JSON and extracts best available odds
    for each game across all bookmakers.

    Returns a clean DataFrame.
    """
    if not ODDS_JSON_PATH.exists():
        print(f"JSON not found at {ODDS_JSON_PATH}")
        return None

    with open(ODDS_JSON_PATH, "r") as f:
        games = json.load(f)

    rows = []
    for game in games:
        result = extract_best_odds(game)
        if result:
            rows.append(result)

    df = pd.DataFrame(rows)
    df["source"]       = "OddsAPI_real"
    df["data_quality"] = "real"

    print(f"Loaded {len(df)} games from Odds API JSON.")
    return df


# ============================================================
# STEP 3 — Merge both sources
# ============================================================

def compile_odds() -> pd.DataFrame:
    """
    Master function — loads both sources and merges them.

    Priority: JSON data (multi-bookmaker) beats CSV data
    for any game that appears in both.

    Returns one clean DataFrame with all tournament games,
    sorted by round order.
    """

    csv_df  = load_csv_odds()
    json_df = load_json_odds()

    if csv_df is None:
        print("No CSV data found. Cannot compile.")
        return None

    # Round order for sorting
    round_order = {
        "First Four":   1,
        "First Round":  2,
        "Second Round": 3,
        "Sweet 16":     4,
        "Elite Eight":  5,
        "Final Four":   6,
        "Championship": 7,
    }

    # If no JSON data, return CSV only
    if json_df is None or len(json_df) == 0:
        csv_df["round_num"] = csv_df["round"].map(round_order)
        return csv_df.sort_values("round_num").drop(columns="round_num")

    # Build a set of team pairs from JSON so we know which games to override
    json_pairs = set()
    for _, row in json_df.iterrows():
        pair = frozenset([row["team_a"], row["team_b"]])
        json_pairs.add(pair)

    # Filter CSV to exclude games already covered by JSON
    def not_in_json(row):
        pair = frozenset([row["team_a"], row["team_b"]])
        return pair not in json_pairs

    csv_only = csv_df[csv_df.apply(not_in_json, axis=1)].copy()

    print(f"CSV games not in JSON: {len(csv_only)}")
    print(f"JSON games (preferred): {len(json_df)}")

    # Merge — JSON rows on top, then CSV-only rows
    # Align columns first
    shared_cols = ["team_a", "team_b", "odds_a", "odds_b",
                   "source", "data_quality"]

    # Add round info to JSON rows from CSV where possible
    json_df["round"]  = None
    json_df["winner"] = None
    json_df["seed_a"] = None
    json_df["seed_b"] = None

    for idx, jrow in json_df.iterrows():
        pair = frozenset([jrow["team_a"], jrow["team_b"]])
        match = csv_df[csv_df.apply(
            lambda r: frozenset([r["team_a"], r["team_b"]]) == pair, axis=1
        )]
        if not match.empty:
            json_df.at[idx, "round"]  = match.iloc[0]["round"]
            json_df.at[idx, "winner"] = match.iloc[0]["winner"]
            json_df.at[idx, "seed_a"] = match.iloc[0]["seed_a"]
            json_df.at[idx, "seed_b"] = match.iloc[0]["seed_b"]

    # Combine
    all_cols = ["team_a", "team_b", "seed_a", "seed_b",
                "odds_a", "odds_b", "round", "winner",
                "source", "data_quality"]

    combined = pd.concat([
        json_df[all_cols],
        csv_only[all_cols]
    ], ignore_index=True)

# Remove NIT games — these have no round because they're not in the tournament CSV
    combined = combined[combined["round"].notna()].copy()

    combined["round_num"] = combined["round"].map(round_order)
    combined = combined.sort_values("round_num").drop(columns="round_num")
    combined = combined.reset_index(drop=True)

    print(f"\nFinal compiled dataset: {len(combined)} games")
    print(combined.groupby(["round", "data_quality"]).size().to_string())

    return combined



