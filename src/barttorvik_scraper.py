"""
Team Stats Fetcher for MadnessEV

Fetches team efficiency stats from College Basketball Data API (CBBD).
Calculates Barthag from adjusted offensive and defensive efficiency ratings.

Data source: collegebasketballdata.com (free API key required)
API key stored in .env as CBBD_API_KEY

Fallback chain:
1. In-memory cache (same session)
2. Live CBBD API fetch
3. Disk cache (any age)
4. Hardcoded fallback (key tournament teams only)
"""

import cbbd
import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from src.team_names import normalize_team_name



load_dotenv()

# --- Cache configuration ---
CACHE_PATH = Path("data/raw/team_stats_cache.csv")
CACHE_MAX_AGE_HOURS = 24

# In-memory cache — stores DataFrame for entire Python session
_memory_cache = None


def calculate_barthag(adj_o: float, adj_d: float) -> float:
    """
    Calculates Barthag from adjusted offensive and defensive efficiency.

    Formula: AdjO^11 / (AdjO^11 + AdjD^11)

    Community-reverse-engineered approximation of Barttorvik's formula.
    Average difference from published Barthag values: ~0.009
    Accuracy is highest for elite teams where it matters most.

    Args:
        adj_o: Adjusted offensive efficiency (points per 100 possessions)
        adj_d: Adjusted defensive efficiency (points allowed per 100 possessions)

    Returns:
        Barthag value between 0 and 1
    """
    o_power = adj_o ** 11
    d_power = adj_d ** 11
    return o_power / (o_power + d_power)


def get_fallback_data() -> dict:
    """
    FALLBACK ONLY — hardcoded Barthag ratings for key 2026 tournament teams.

    ⚠️  IMPORTANT: Only used if CBBD API fails AND no disk cache exists.
    ⚠️  Values pulled from Barttorvik end-of-season CSV, May 2026.
    ⚠️  Only Barthag available here — adj_o and adj_d will be None.

    If you're seeing these values in output, check your CBBD_API_KEY.
    """
    return {
        # --- FINAL FOUR ---
        "Connecticut":      0.9561,
        "Illinois":         0.9682,
        "Arizona":          0.9772,
        "Michigan":         0.9819,

        # --- ELITE EIGHT ---
        "Duke":             0.9768,
        "Auburn":           0.8697,
        "Houston":          0.9714,
        "Iowa State":       0.9631,

        # --- SWEET 16 ---
        "Purdue":           0.9610,
        "Tennessee":        0.9447,
        "Texas Tech":       0.9349,
        "Baylor":           0.8477,
        "Florida":          0.9719,
        "Gonzaga":          0.9357,
        "Alabama":          0.9423,
        "Kentucky":         0.8888,

        # --- OTHER KEY TEAMS ---
        "St. John's":       0.9507,
        "North Carolina":   0.8951,
        "Marquette":        0.7617,
        "Creighton":        0.7302,
    }




def fetch_team_stats() -> pd.DataFrame:
    """
    Fetches all team efficiency stats from CBBD API.

    Called once per session maximum — results cached in memory and on disk.
    On success: saves full DataFrame with barthag, adj_o, adj_d for all teams.
    On failure: falls through to disk cache then hardcoded fallback.

    Returns DataFrame with columns: team, barthag, adj_o, adj_d, adj_t
    Returns None if all layers fail.
    """
    global _memory_cache

    # --- Layer 1: In-memory cache ---
    if _memory_cache is not None:
        print("Loading team stats from memory.")
        return _memory_cache

    # --- Layer 2: Fresh disk cache ---
    if CACHE_PATH.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(
            CACHE_PATH.stat().st_mtime
        )
        if cache_age < timedelta(hours=CACHE_MAX_AGE_HOURS):
            print(f"Loading team stats from disk cache "
                  f"(age: {int(cache_age.total_seconds() / 3600)}h old).")
            _memory_cache = pd.read_csv(CACHE_PATH)
            return _memory_cache
        else:
            print(f"Disk cache stale "
                  f"({int(cache_age.total_seconds() / 3600)}h old). Re-fetching...")

    # --- Layer 3: Live CBBD API ---
    print("Fetching team stats from CBBD API...")

    try:
        api_key = os.getenv("CBBD_API_KEY")

        if not api_key:
            print("⚠️  CBBD_API_KEY not found in .env. Check your .env file.")
            return _load_cache_fallback()

        configuration = cbbd.Configuration(access_token=api_key)

        with cbbd.ApiClient(configuration) as api_client:
            ratings_api = cbbd.RatingsApi(api_client)
            results = ratings_api.get_adjusted_efficiency(season=2026)

        # Build DataFrame from API response
        rows = []
        for team in results:
            adj_o = team.offensive_rating
            adj_d = team.defensive_rating
            barthag = calculate_barthag(adj_o, adj_d)
            rows.append({
                "team":    team.team,
                "barthag": round(barthag, 4),
                "adj_o":   adj_o,
                "adj_d":   adj_d,
                "adj_t":   None,
            })

        df = pd.DataFrame(rows)

        # Save to disk and memory
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(CACHE_PATH, index=False)
        _memory_cache = df
        print(f"✅ Fetched {len(df)} teams from CBBD. Saved to cache.")
        return df

    except Exception as e:
        print(f"⚠️  CBBD API error: {e}")
        return _load_cache_fallback()
    


def _load_cache_fallback() -> pd.DataFrame:
    """
    Loads disk cache if it exists — any age is acceptable as last resort.
    """
    global _memory_cache
    if CACHE_PATH.exists():
        print("⚠️  Using disk cache as fallback.")
        _memory_cache = pd.read_csv(CACHE_PATH)
        return _memory_cache
    print("No disk cache found.")
    return None


def get_team_stats(team_name: str) -> dict:
    """
    Main function for the pipeline to call.

    Resolves name aliases, fetches full dataset, finds the team,
    falls back to hardcoded data if needed.

    Args:
        team_name: Team name e.g. "Michigan", "UConn", "Iowa St."

    Returns dict with: team, barthag, adj_o, adj_d, adj_t
    Returns None if team not found anywhere.
    """

    # Resolve alias — "UConn" → "Connecticut", "Iowa St." → "Iowa State"
    resolved_name = normalize_team_name(team_name)

    # --- Attempt 1: Live data via CBBD ---
    df = fetch_team_stats()

    if df is not None:
        match = df[df["team"].str.lower() == resolved_name.lower()]

        if not match.empty:
            row = match.iloc[0]
            return {
                "team":    row["team"],
                "barthag": float(row["barthag"]),
                "adj_o":   row["adj_o"],
                "adj_d":   row["adj_d"],
                "adj_t":   row["adj_t"],
            }
        else:
            print(f"'{resolved_name}' not found in live data. Trying fallback...")

    # --- Attempt 2: Hardcoded fallback ---
    # ⚠️ If you're hitting this, check your CBBD_API_KEY
    fallback = get_fallback_data()

    if resolved_name in fallback:
        print(f"⚠️  Using hardcoded fallback for {resolved_name}.")
        return {
            "team":    resolved_name,
            "barthag": fallback[resolved_name],
            "adj_o":   None,
            "adj_d":   None,
            "adj_t":   None,
        }

    print(f"Could not find stats for '{team_name}' anywhere.")
    return None


