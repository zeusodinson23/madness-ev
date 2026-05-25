# MadnessEV 🏀

**March Madness Expected Value Dashboard**

A Python application that analyzes NCAA Tournament betting odds to identify positive expected value (+EV) betting opportunities.

## What It Does

- 📊 Pulls live betting odds from multiple sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- 📈 Computes implied probabilities from betting lines
- 🎯 Compares market odds against your model's win probabilities
- 💰 Identifies mispriced bets (positive expected value)
- 📉 Tracks line movement and hypothetical P&L

## Quick Start

### 1. Install Dependencies

```bash
cd madness-ev
pip install -r requirements.txt
```

### 2. Get Your API Key

1. Go to [The Odds API](https://the-odds-api.com) and sign up (free)
2. Copy your API key from the dashboard
3. Create a `.env` file in the project root:

```
ODDS_API_KEY=your_actual_api_key_here
```

### 3. Fetch Odds

```bash
# Use cached data (for development)
python src/odds_fetcher.py

# Force fresh API call
python src/odds_fetcher.py --force
```

### 4. Process and Analyze

```bash
python src/odds_processor.py
```

## Project Structure

```
madness-ev/
├── config/                # Configuration and settings
│   └── settings.py        # API keys, constants, paths
├── data/
│   ├── raw/               # Raw API responses (JSON)
│   ├── processed/         # Clean CSVs
│   └── historical/        # Reference data
├── src/                   # Core Python modules
│   ├── odds_fetcher.py    # Pull odds from API
│   ├── odds_processor.py  # Convert to probabilities
│   ├── utils.py           # Odds conversion, EV calc
│   └── model.py           # Win probability models (coming soon)
├── pages/                 # Streamlit dashboard pages
├── notebooks/             # Jupyter notebooks
└── scripts/               # CLI utilities
```

## Key Concepts

### American Odds → Probability

```python
# Favorite: -150 means bet $150 to win $100
# Underdog: +200 means bet $100 to win $200

from src.utils import american_to_implied_prob

american_to_implied_prob(-150)  # → 0.60 (60%)
american_to_implied_prob(+200)  # → 0.33 (33%)
```

### Expected Value

```python
from src.utils import calculate_ev, american_to_decimal

# You think Team X has 40% chance, market offers +200
model_prob = 0.40
decimal_odds = american_to_decimal(+200)  # 3.0

ev = calculate_ev(model_prob, decimal_odds)  # → +$20 per $100 bet
```

### The Vig (Bookmaker's Edge)

When you add implied probabilities for both sides, they sum to >100%:
- Team A: -110 → 52.4%
- Team B: -110 → 52.4%
- Total: 104.8% (the extra 4.8% is the vig)

We remove this to get "true" probabilities for fair comparison.

## Tournament Status

**2026 NCAA Men's Basketball Tournament**
- ✅ First Four: March 17-18
- ✅ First Round: March 19-20
- 🔴 **Round of 32: March 21-22** ← Current
- ⬜ Sweet 16: March 26-27
- ⬜ Elite Eight: March 28-29
- ⬜ Final Four: April 4
- ⬜ Championship: April 6

## Coming Soon

- [ ] Barttorvik scraper for team analytics
- [ ] Log5 win probability model
- [ ] Streamlit dashboard
- [ ] Line movement tracking
- [ ] P&L tracker
- [ ] Historical backtesting

## Tech Stack

- **Python 3.11+**
- **pandas** - Data manipulation
- **requests** - API calls
- **Streamlit** - Dashboard (coming soon)
- **Plotly** - Visualization (coming soon)
- **SQLite** - Data storage (coming soon)

## API Budget

Free tier: 500 requests/month

**Budget strategy:**
- Cached responses in `data/raw/` prevent redundant calls
- Set `USE_CACHE=True` in settings during development
- Each odds fetch = 1 request
- Tournament needs ~180 calls (12/day × 15 game days)

## License

MIT
