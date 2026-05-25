"""
Configuration settings for MadnessEV

This module loads environment variables and defines constants used throughout
the application. Centralizing configuration here means:
1. Change settings in ONE place
2. Sensitive data (API keys) stays separate from code
3. Constants have meaningful names instead of magic numbers
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# The .env file should be in the project root directory
load_dotenv()

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Get the project root directory (parent of the config folder)
# Path(__file__) gets this file's path, .parent goes up one level
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories - using Path makes this work on Windows, Mac, and Linux
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
HISTORICAL_DATA_DIR = DATA_DIR / "historical"

# Database path
DATABASE_PATH = DATA_DIR / "madness.db"

# =============================================================================
# API CONFIGURATION
# =============================================================================

# The Odds API settings
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"

# Sport key for NCAA Men's Basketball
# This is how The Odds API identifies different sports/leagues
SPORT_KEY = "basketball_ncaab"

# Regions - "us" gives us American bookmakers (DraftKings, FanDuel, etc.)
# Other options: "us,uk,eu,au" for more bookmakers
REGIONS = "us"

# Markets we want to pull:
# - h2h: Moneyline (who wins the game)
# - spreads: Point spreads (team wins by X points)
# - totals: Over/under total points
MARKETS = "h2h,spreads,totals"

# Odds format - American odds are what US sportsbooks use (-150, +200, etc.)
# Alternatives: "decimal" (2.5, 3.0) or "fractional" (3/2, 2/1)
ODDS_FORMAT = "american"

# =============================================================================
# TOURNAMENT CONFIGURATION - 2026 NCAA TOURNAMENT
# =============================================================================

TOURNAMENT_YEAR = 2026

# Tournament rounds and dates (update as tournament progresses)
# This helps us label games and track progress
TOURNAMENT_ROUNDS = {
    "First Four": {"start": "2026-03-17", "end": "2026-03-18"},
    "First Round": {"start": "2026-03-19", "end": "2026-03-20"},
    "Second Round": {"start": "2026-03-21", "end": "2026-03-22"},
    "Sweet 16": {"start": "2026-03-26", "end": "2026-03-27"},
    "Elite Eight": {"start": "2026-03-28", "end": "2026-03-29"},
    "Final Four": {"start": "2026-04-04", "end": "2026-04-04"},
    "Championship": {"start": "2026-04-06", "end": "2026-04-06"},
}

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# For the Log5 model - these are defaults, can be tuned
DEFAULT_MODEL_VERSION = "log5_v1"

# For Kelly Criterion bet sizing
# Full Kelly is mathematically optimal but very aggressive
# Most bettors use fractional Kelly to reduce variance
KELLY_FRACTION = 0.25  # Use 1/4 Kelly (25% of the full Kelly suggestion)

# Minimum EV threshold to consider a bet "interesting"
# EV of 0.05 means you expect to make $5 profit per $100 wagered
MIN_EV_THRESHOLD = 0.05

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

# How long to wait before pulling fresh data (in seconds)
# During active games, you might want shorter intervals
CACHE_DURATION_SECONDS = 7200  # 2 hours

# Whether to use cached data in development (saves API calls)
USE_CACHE = True


def validate_config():
    """
    Check that required configuration is present.
    Call this at application startup to fail fast if something is missing.
    """
    errors = []
    
    if not ODDS_API_KEY:
        errors.append(
            "ODDS_API_KEY not found. "
            "Create a .env file with your API key. "
            "Get a free key at https://the-odds-api.com"
        )
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))
    
    return True


# Quick test when this file is run directly
if __name__ == "__main__":
    print("Configuration loaded successfully!")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"API Key configured: {'Yes' if ODDS_API_KEY else 'No - SET YOUR API KEY!'}")
    print(f"Sport: {SPORT_KEY}")
    print(f"Tournament year: {TOURNAMENT_YEAR}")
