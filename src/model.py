"""
Win Probability Model for MadnessEV

This module is the brain of the system. It takes team stats from
Barttorvik and computes win probabilities for any matchup.

V1: Log5 method — simple, fast, well-calibrated
V2: Efficiency-based model — uses AdjO, AdjD, AdjT for more detail

The output of this module feeds directly into the EV calculator.
Two inputs go in (Barthag A, Barthag B), one number comes out (win probability).
"""

import pandas as pd
from src.barttorvik_scraper import get_team_stats
from src.utils import (
    american_to_implied_prob,
    american_to_decimal,
    calculate_vig,
    remove_vig,
    calculate_ev,
    kelly_fraction,
    kelly_stake,
)



def log5(barthag_a: float, barthag_b: float) -> float:
    """
    Log5 formula — estimates win probability for Team A against Team B.

    Created by Bill James (baseball statistician). Works for any
    head-to-head sport where each team has a known strength rating.

    Formula:
        P(A beats B) = (A × (1 - B)) / (A × (1 - B) + B × (1 - A))

    Args:
        barthag_a: Team A's Barthag rating (0 to 1)
        barthag_b: Team B's Barthag rating (0 to 1)

    Returns:
        Probability that Team A beats Team B (0 to 1)

    Example:
        Michigan (0.9819) vs Connecticut (0.9561)
        log5(0.9819, 0.9561) → 0.714 (Michigan wins 71.4%)
    """

    numerator = barthag_a * (1 - barthag_b)
    denominator = (barthag_a * (1 - barthag_b)) + (barthag_b * (1 - barthag_a))

    # Safety check — denominator should never be zero but just in case
    if denominator == 0:
        return 0.5

    return numerator / denominator


def predict_matchup(team_a: str, team_b: str) -> dict:
    """
    Predicts win probability for a matchup between two teams.

    Fetches Barthag for both teams, runs Log5, and returns
    a clean dictionary with all the relevant numbers.

    Args:
        team_a: Name of Team A e.g. "Michigan"
        team_b: Name of Team B e.g. "Connecticut"

    Returns a dict with:
        - team_a, team_b: team names
        - barthag_a, barthag_b: raw Barthag ratings
        - prob_a, prob_b: model win probabilities (sum to 1.0)
    """

    print(f"\nPredicting: {team_a} vs {team_b}")

    # Step 1 — Fetch stats for both teams
    stats_a = get_team_stats(team_a)
    stats_b = get_team_stats(team_b)

    # Step 2 — Bail out if either team wasn't found
    if stats_a is None:
        print(f"Could not find stats for {team_a}. Cannot predict.")
        return None

    if stats_b is None:
        print(f"Could not find stats for {team_b}. Cannot predict.")
        return None

    # Step 3 — Extract Barthag for each team
    barthag_a = float(stats_a["barthag"])
    barthag_b = float(stats_b["barthag"])

    # Step 4 — Run Log5
    prob_a = log5(barthag_a, barthag_b)
    prob_b = 1 - prob_a  # Probabilities must sum to 1

    # Step 5 — Package and return results
    return {
        "team_a":     stats_a["team"],
        "team_b":     stats_b["team"],
        "barthag_a":  round(barthag_a, 4),
        "barthag_b":  round(barthag_b, 4),
        "prob_a":     round(prob_a, 4),
        "prob_b":     round(prob_b, 4),
    }


from scipy import stats as scipy_stats

# League average constants for 2026 D-I basketball
LEAGUE_AVG_EFFICIENCY = 105.0   # points per 100 possessions, average team
LEAGUE_AVG_POSSESSIONS = 68.0   # possessions per 40 min game, average pace
MARGIN_STD_DEV = 11.0           # historical std dev of college basketball margins


def efficiency_model(team_a: str, team_b: str) -> dict:
    """
    V2 Win Probability Model — Efficiency Based.

    Simulates the actual game by combining each team's offense
    against the opponent's defense explicitly:

        A's expected scoring = (A_AdjO × B_AdjD) / league_average
        B's expected scoring = (B_AdjO × A_AdjD) / league_average

    Then converts expected margin to win probability using a
    normal distribution with historical std dev of 11 points.

    Args:
        team_a: Team A name e.g. "Michigan"
        team_b: Team B name e.g. "UConn"

    Returns dict with prob_a, prob_b, expected_margin, and inputs.
    Returns None if either team's stats are unavailable.
    """

    # --- Step 1: Get efficiency stats for both teams ---
    stats_a = get_team_stats(team_a)
    stats_b = get_team_stats(team_b)

    if stats_a is None:
        print(f"Could not find stats for {team_a}. Cannot run V2 model.")
        return None
    if stats_b is None:
        print(f"Could not find stats for {team_b}. Cannot run V2 model.")
        return None

    # Check we have AdjO and AdjD — not just Barthag fallback
    if stats_a["adj_o"] is None or stats_a["adj_d"] is None:
        print(f"No efficiency data for {team_a}. Falling back to Log5.")
        return None
    if stats_b["adj_o"] is None or stats_b["adj_d"] is None:
        print(f"No efficiency data for {team_b}. Falling back to Log5.")
        return None

    adj_o_a = float(stats_a["adj_o"])
    adj_d_a = float(stats_a["adj_d"])
    adj_o_b = float(stats_b["adj_o"])
    adj_d_b = float(stats_b["adj_d"])

    # --- Step 2: Expected points per 100 possessions ---
    # A's offense against B's defense, normalised by league average
    # If A scores 130 against average (105) and B allows 89 against average (105):
    # A's expected rate = 130 × (89/105) = 116.8
    a_pts_per_100 = adj_o_a * (adj_d_b / LEAGUE_AVG_EFFICIENCY)
    b_pts_per_100 = adj_o_b * (adj_d_a / LEAGUE_AVG_EFFICIENCY)

    # --- Step 3: Scale to actual game possessions ---
    # Using league average tempo since CBBD doesn't provide AdjT
    a_expected_pts = a_pts_per_100 * (LEAGUE_AVG_POSSESSIONS / 100)
    b_expected_pts = b_pts_per_100 * (LEAGUE_AVG_POSSESSIONS / 100)

    expected_margin = a_expected_pts - b_expected_pts

    # --- Step 4: Convert margin to win probability ---
    # norm.cdf measures what fraction of the bell curve is above zero
    # i.e. probability that actual margin > 0 (Team A wins)
    prob_a = scipy_stats.norm.cdf(expected_margin / MARGIN_STD_DEV)
    prob_b = 1 - prob_a

    return {
        "team_a":          stats_a["team"],
        "team_b":          stats_b["team"],
        "adj_o_a":         round(adj_o_a, 2),
        "adj_d_a":         round(adj_d_a, 2),
        "adj_o_b":         round(adj_o_b, 2),
        "adj_d_b":         round(adj_d_b, 2),
        "a_pts_per_100":   round(a_pts_per_100, 2),
        "b_pts_per_100":   round(b_pts_per_100, 2),
        "expected_margin": round(expected_margin, 2),
        "prob_a":          round(prob_a, 4),
        "prob_b":          round(prob_b, 4),
    }


def blend_models(team_a: str, team_b: str,
                 weight_v1: float = 0.5,
                 weight_v2: float = 0.5) -> dict:
    """
    V3 Model — Weighted blend of Log5 (V1) and Efficiency (V2).

    Combines both models into a single probability. When they agree,
    confidence is high. When they disagree by 5+ percentage points,
    flags the game for extra scrutiny — the models are picking up
    different signals worth investigating before betting.

    Args:
        team_a:    Team A name
        team_b:    Team B name
        weight_v1: Weight given to Log5 output (default 0.5)
        weight_v2: Weight given to efficiency model output (default 0.5)
                   weight_v1 + weight_v2 must equal 1.0

    Returns dict with blended probabilities and model disagreement flag.
    Returns None if either underlying model fails.
    """

    v1 = predict_matchup(team_a, team_b)
    v2 = efficiency_model(team_a, team_b)

    # If V2 fails (missing AdjO/AdjD), fall back to V1 only
    if v1 is None:
        return None

    if v2 is None:
        print(f"V2 unavailable for {team_a} vs {team_b}. Using V1 only.")
        return {
            "team_a":        v1["team_a"],
            "team_b":        v1["team_b"],
            "prob_a":        v1["prob_a"],
            "prob_b":        v1["prob_b"],
            "v1_prob_a":     v1["prob_a"],
            "v2_prob_a":     None,
            "model_used":    "v1_only",
            "disagreement":  0.0,
            "flag":          False,
            "flag_reason":   "",
        }

    # Blend probabilities
    blended_a = round(weight_v1 * v1["prob_a"] + weight_v2 * v2["prob_a"], 4)
    blended_b = round(1 - blended_a, 4)

    # Measure disagreement between models
    disagreement = abs(v1["prob_a"] - v2["prob_a"]) * 100

    # Flag if models disagree by 5+ percentage points
    flag = disagreement >= 5.0
    flag_reason = (
        f"Models disagree by {disagreement:.1f}pp — "
        f"V1 says {v1['prob_a']*100:.1f}%, "
        f"V2 says {v2['prob_a']*100:.1f}%. "
        f"Investigate before betting."
    ) if flag else ""

    return {
        "team_a":        v1["team_a"],
        "team_b":        v1["team_b"],
        "prob_a":        blended_a,
        "prob_b":        blended_b,
        "v1_prob_a":     v1["prob_a"],
        "v2_prob_a":     v2["prob_a"],
        "barthag_a":     v1["barthag_a"],
        "barthag_b":     v1["barthag_b"],
        "expected_margin": v2["expected_margin"],
        "model_used":    "v3_blend",
        "disagreement":  round(disagreement, 2),
        "flag":          flag,
        "flag_reason":   flag_reason,
    }


def analyze_game(team_a: str, team_b: str,
                 odds_a: int, odds_b: int,
                 bankroll: float = 1000,
                 model_version: str = "v1") -> dict:
    """
    Full analysis of a single game — the core of the EV pipeline.

    Combines model win probability with market implied probability
    to determine if a bet has positive expected value.

    Args:
        team_a:        Name of Team A e.g. "Michigan"
        team_b:        Name of Team B e.g. "UConn"
        odds_a:        American moneyline odds for Team A e.g. -180
        odds_b:        American moneyline odds for Team B e.g. +150
        bankroll:      Hypothetical bankroll for Kelly sizing (default $1000)
        model_version: Which model to use — "v1", "v2", or "v3"
    """

    # --- Step 1: Get model probabilities ---
    model_flag = False
    model_flag_reason = ""

    if model_version == "v1":
        matchup = predict_matchup(team_a, team_b)

    elif model_version == "v2":
        matchup = efficiency_model(team_a, team_b)
        if matchup is None:
            print(f"V2 failed for {team_a} vs {team_b}, falling back to V1.")
            matchup = predict_matchup(team_a, team_b)

    elif model_version == "v3":
        matchup = blend_models(team_a, team_b)
        if matchup is not None:
            model_flag = matchup["flag"]
            model_flag_reason = matchup["flag_reason"]

    else:
        print(f"Unknown model version: {model_version}. Using V1.")
        matchup = predict_matchup(team_a, team_b)

    if matchup is None:
        print(f"Could not analyze {team_a} vs {team_b}.")
        return None

    model_prob_a = matchup["prob_a"]
    model_prob_b = matchup["prob_b"]

    # --- Step 2: Convert market odds to implied probabilities ---
    raw_implied_a = american_to_implied_prob(odds_a)
    raw_implied_b = american_to_implied_prob(odds_b)

    # --- Step 3: Remove the vig to get fair market probabilities ---
    vig = calculate_vig(raw_implied_a, raw_implied_b)
    fair_prob_a, fair_prob_b = remove_vig(raw_implied_a, raw_implied_b)

    # --- Step 4: Convert odds to decimal for EV calculation ---
    decimal_a = american_to_decimal(odds_a)
    decimal_b = american_to_decimal(odds_b)

    # --- Step 5: Calculate EV for betting each team ---
    ev_a = calculate_ev(model_prob_a, decimal_a)
    ev_b = calculate_ev(model_prob_b, decimal_b)

    # --- Step 6: Calculate Kelly stakes ---
    stake_a = kelly_stake(bankroll, model_prob_a, decimal_a)
    stake_b = kelly_stake(bankroll, model_prob_b, decimal_b)

    # --- Step 7: Determine recommendation ---
    edge_a = model_prob_a - fair_prob_a
    edge_b = model_prob_b - fair_prob_b

    if ev_a > 0 and ev_a >= ev_b:
        recommendation = f"BET {matchup['team_a']} (+EV: ${ev_a:.2f} per $100)"
    elif ev_b > 0:
        recommendation = f"BET {matchup['team_b']} (+EV: ${ev_b:.2f} per $100)"
    else:
        recommendation = "NO BET — both sides are -EV"

    return {
        # Teams
        "team_a":              matchup["team_a"],
        "team_b":              matchup["team_b"],

        # Ratings
        "barthag_a":           matchup.get("barthag_a"),
        "barthag_b":           matchup.get("barthag_b"),

        # Model probabilities
        "model_prob_a":        round(model_prob_a, 4),
        "model_prob_b":        round(model_prob_b, 4),

        # Market odds and probabilities
        "odds_a":              odds_a,
        "odds_b":              odds_b,
        "market_prob_a":       round(fair_prob_a, 4),
        "market_prob_b":       round(fair_prob_b, 4),
        "vig":                 round(vig, 4),

        # Edge
        "edge_a":              round(edge_a, 4),
        "edge_b":              round(edge_b, 4),

        # EV per $100
        "ev_a":                round(ev_a, 2),
        "ev_b":                round(ev_b, 2),

        # Kelly stakes
        "kelly_stake_a":       round(stake_a, 2),
        "kelly_stake_b":       round(stake_b, 2),

        # Recommendation
        "recommendation":      recommendation,

        # Model metadata
        "model_version":       model_version,
        "model_flag":          model_flag,
        "model_flag_reason":   model_flag_reason,
    }