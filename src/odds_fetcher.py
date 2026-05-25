"""
Odds Fetcher Module for MadnessEV
This module is responsible for fetching the latest odds data from The Odds API.
"""


from urllib import response

import requests
import json
import os 
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file

# API Configuration
API_KEY = os.getenv("ODDS_API_KEY")  # Get API key from environment variable
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "basketball_ncaab"  # NCAA Basketball
REGIONS = "us"  # Regions to pull odds from (us, uk, eu, au)
MARKETS = "h2h"  # Types of odds to pull (h2h, spreads, totals)
ODDS_FORMAT = "american"  # Format of odds (american, decimal, fractional)


def fetch_odds():
    """

    Fetches live odds from The Odds API for NCAA Basketball games.
    Returns a list of games with their odds and related information.

    """

    # Build the URl 
    url = f"{BASE_URL}/sports/{SPORT}/odds"

    params = {
    "apiKey": API_KEY,
    "regions": REGIONS,
    "markets": MARKETS,
    "oddsFormat": ODDS_FORMAT,

    }

    # Make the API request
    print(f"Fetching odds data from The Odds API for {SPORT}...")
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        games = response.json()
        print(f"Successfully fetched odds for {len(games)} games.")

        # Show remaining API requests for the month (free tier = 500/moonth)
        remaining_requests = response.headers.get("x-requests-remaining")
        print(f"Remaining API requests for the month: {remaining_requests}")

        return games
    else:
        print(f"Failed to fetch odds data. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def save_odds(games, filename="odds_data.json"):
    """
    Save odds data to a JSON file.
    
    This lets us:
    1. Keep the data after closing Python
    2. Avoid wasting API calls during development
    3. Track how odds change over time
    """
    # Create the data/raw folder if it doesn't exist
    raw_folder = Path("data/raw")
    raw_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"odds_{timestamp}.json"
    
    # Full path to file
    filepath = raw_folder / filename
    
    # Save to file
    with open(filepath, "w") as f:
        json.dump(games, f, indent=2)
    
    print(f"Saved {len(games)} games to {filepath}")
    return filepath


def load_odds(filename):
    """
    Load odds data from a saved JSON file.
    
    This lets us work with saved data without using API calls.
    """
    filepath = Path("data/raw") / filename
    
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return None
    
    with open(filepath, "r") as f:
        games = json.load(f)
    
    print(f"Loaded {len(games)} games from {filepath}")
    return games