# MadnessEV

**A sports betting analytics dashboard for the 2026 NCAA Men's Basketball Tournament.**

MadnessEV pulls team efficiency ratings, builds win probability models, and compares them against real bookmaker odds to find positive expected value betting opportunities. The full 2026 tournament (67 games) is backtested with three models and tracked through a Streamlit dashboard with live model switching, Kelly criterion sizing, and cumulative P&L visualisation.

**[Live Demo](https://madness-ev.streamlit.app)** &nbsp;

---

## What It Does

Bookmakers price every game with a built-in profit margin. When a model consistently estimates a team's win probability higher than what the market implies, that gap is a positive expected value betting opportunity. MadnessEV quantifies this gap across every game of the 2026 tournament and simulates what would have happened if you had bet every identified edge.

The dashboard lets you switch between three models, adjust Kelly fraction and starting bankroll, filter by round, and see how every decision plays out across the P&L curve.

---

## Key Findings

Running all three models on the corrected 67-game dataset with Quarter Kelly staking on a $1,000 bankroll:

| Model | Bets | Win Rate | Net Profit | ROI on Wagered |
|---|---|---|---|---|
| V1 — Log5 | 44 | 50.0% | +$403.13 | +27.2% |
| V2 — Efficiency | 49 | 67.3% | +$423.94 | +17.2% |
| V3 — Blend | 47 | 57.4% | +$408.49 | +22.7% |

The most counterintuitive result: V2 wins 67.3% of bets but earns a lower ROI than V1 which wins only 50.0%. Win rate is a misleading metric in betting. V1 identifies fewer but larger market inefficiencies, generating more return per dollar risked. This mirrors a core principle in quantitative finance — number of winning positions tells you nothing without knowing the return on each.

V1 and V2 produce nearly identical probabilities on most games (average difference under 2 percentage points) because Barthag is derived from the same AdjO and AdjD data that V2 uses directly. Their convergence confirms internal consistency rather than redundancy.

---

## Models

**V1 — Log5.** Takes each team's Barthag (probability of beating an average D-I team) and applies the Log5 formula invented by Bill James. Simple, well-calibrated, best ROI of the three.

**V2 — Efficiency Model.** Directly matches each team's adjusted offensive efficiency against the opponent's adjusted defensive efficiency, estimates expected scoring margin, and converts to win probability using a normal distribution with historical standard deviation of 11 points.

**V3 — Blend.** Weighted average of V1 and V2 (50/50). Flags any game where the two models disagree by 5+ percentage points as requiring extra scrutiny.

---

## Data Sources

- **Team efficiency:** College Basketball Data API (collegebasketballdata.com) — AdjO and AdjD for all 365 D-I teams, 2026 season
- **Barthag:** Calculated from AdjO and AdjD using the community approximation formula (average deviation from published values: ~0.009)
- **Odds:** The Odds API live snapshot (March 28), DraftKings opening lines via OutKick, FOX Sports and ESPN, VegasInsider for the Championship
- **Tournament results:** Cross-verified against On3.com complete tournament tracker, NCAA.com, CBS Sports, and FOX Sports for all 67 games

All 67 games use real published bookmaker odds. No approximations. Every game result was verified against On3.com's complete post-tournament record.

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/zeusodinson23/madness-ev.git
cd madness-ev
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up API keys**

Create a `.env` file in the project root:
```
ODDS_API_KEY=your_odds_api_key
CBBD_API_KEY=your_cbbd_api_key
```

Both keys are free. Get The Odds API key at [the-odds-api.com](https://the-odds-api.com) and CBBD key at [collegebasketballdata.com](https://collegebasketballdata.com/key).

The team stats cache (`data/raw/team_stats_cache.csv`) is included in the repo so the app runs immediately without needing to call CBBD — the tournament is over and the data is static.

**5. Run the dashboard**
```bash
streamlit run app.py
```

---

## Project Structure

```
madness-ev/
├── app.py                          # Streamlit dashboard (4 pages)
├── run_backtest.py                 # Model comparison runner
├── requirements.txt
│
├── src/
│   ├── barttorvik_scraper.py       # CBBD API fetcher with 3-layer caching
│   ├── model.py                    # V1 Log5, V2 Efficiency, V3 Blend models
│   ├── backtest.py                 # Full backtest engine
│   ├── data_compiler.py            # Loads and merges odds data sources
│   ├── utils.py                    # EV, Kelly, vig removal, odds conversion
│   ├── odds_fetcher.py             # The Odds API integration
│   └── team_names.py               # Name normalisation and aliases
│
├── data/
│   ├── raw/
│   │   ├── odds_data.json          # Live odds snapshot (March 28, 2026)
│   │   └── team_stats_cache.csv    # CBBD efficiency ratings, all 365 teams
│   ├── historical/
│   │   └── 2026_tournament_odds.csv # All 67 games, verified results and odds
│   └── processed/
│       ├── backtest_v1.csv
│       ├── backtest_v2.csv
│       └── backtest_v3.csv
│
├── config/
│   └── settings.py
│
└── .streamlit/
    └── config.toml                 # Light theme config
```

---

## Tech Stack

Python 3.11, pandas, numpy, scipy, Streamlit, Plotly, CBBD API, The Odds API

---

## Limitations

- 67 games is insufficient for statistically robust conclusions about model edge
- First Round odds are opening lines from Selection Sunday, not closing lines
- V2 uses league-average tempo (68 possessions) since CBBD does not provide adjusted tempo
- Single season — multi-year backtesting needed to confirm genuine edge
- Arkansas vs Hawaii (First Round) is skipped because Hawaii is not in the CBBD database

---

## License

MIT
