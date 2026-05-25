"""
Backtest Engine for MadnessEV

Runs the full EV analysis across all 63 tournament games and
computes hypothetical P&L based on a fixed starting bankroll.

Strategy:
  - For each game, run analyze_game() to get model vs market probabilities
  - If EV > 0 for either team, record a hypothetical bet
  - Use quarter-Kelly staking on a $1000 starting bankroll
  - Check actual winner and resolve each bet
  - Track cumulative P&L across the tournament

Output:
  - Full game-by-game results DataFrame
  - Summary statistics (ROI, win rate, calibration)
"""

import pandas as pd
from src.data_compiler import compile_odds
from src.model import analyze_game

# Starting bankroll for Kelly staking
STARTING_BANKROLL = 1000.0

# Minimum EV threshold to place a bet
# 0.0 means bet any positive EV
# 0.05 means only bet if EV > 5% of stake
MIN_EV_THRESHOLD = 0.0


def run_backtest(model_version: str = "v1") -> tuple:
    """
    Runs the full tournament backtest.

    Returns:
        results_df: DataFrame with one row per game, all analysis included
        summary:    Dict with overall P&L statistics
    """

    # --- Load all games ---
    games_df = compile_odds()
    if games_df is None:
        print("No games data found. Cannot run backtest.")
        return None, None

    print(f"\nRunning backtest on {len(games_df)} games...")
    print("=" * 60)

    results = []
    bankroll = STARTING_BANKROLL
    cumulative_pnl = 0.0

    for _, game in games_df.iterrows():
        team_a = game["team_a"]
        team_b = game["team_b"]
        odds_a = int(game["odds_a"])
        odds_b = int(game["odds_b"])
        winner = game["winner"]
        round_name = game["round"]
        data_quality = game["data_quality"]

        # --- Run the model ---
        analysis = analyze_game(
            team_a=team_a,
            team_b=team_b,
            odds_a=odds_a,
            odds_b=odds_b,
            bankroll=bankroll,
            model_version=model_version
        )

        # --- Skip if model couldn't analyze (missing Barthag) ---
        if analysis is None:
            results.append({
                "round":        round_name,
                "team_a":       team_a,
                "team_b":       team_b,
                "winner":       winner,
                "skipped":      True,
                "skip_reason":  "Missing team stats",
                "data_quality": data_quality,
            })
            continue

        # --- Determine bet ---
        bet_team  = None
        bet_odds  = None
        bet_stake = 0.0
        bet_ev    = 0.0

        if analysis["ev_a"] > MIN_EV_THRESHOLD and analysis["ev_a"] >= analysis["ev_b"]:
            bet_team  = analysis["team_a"]
            bet_odds  = odds_a
            bet_stake = analysis["kelly_stake_a"]
            bet_ev    = analysis["ev_a"]

        elif analysis["ev_b"] > MIN_EV_THRESHOLD:
            bet_team  = analysis["team_b"]
            bet_odds  = odds_b
            bet_stake = analysis["kelly_stake_b"]
            bet_ev    = analysis["ev_b"]

        # --- Resolve bet ---
        bet_result = None
        profit     = 0.0

        if bet_team is not None and bet_stake > 0:
            if winner is None or pd.isna(winner):
                bet_result = "pending"
            elif bet_team.lower() == str(winner).lower():
                # Win — calculate profit from decimal odds
                from src.utils import american_to_decimal
                decimal = american_to_decimal(bet_odds)
                profit = bet_stake * (decimal - 1)
                bet_result = "win"
            else:
                profit = -bet_stake
                bet_result = "loss"

            cumulative_pnl += profit
            bankroll = STARTING_BANKROLL + cumulative_pnl

        # --- Record result ---
        results.append({
            "round":            round_name,
            "team_a":           analysis["team_a"],
            "team_b":           analysis["team_b"],
            "winner":           winner,
            "model_prob_a":     analysis["model_prob_a"],
            "model_prob_b":     analysis["model_prob_b"],
            "market_prob_a":    analysis["market_prob_a"],
            "market_prob_b":    analysis["market_prob_b"],
            "edge_a":           analysis["edge_a"],
            "edge_b":           analysis["edge_b"],
            "ev_a":             analysis["ev_a"],
            "ev_b":             analysis["ev_b"],
            "bet_team":         bet_team,
            "bet_stake":        round(bet_stake, 2),
            "bet_odds":         bet_odds,
            "bet_result":       bet_result,
            "profit":           round(profit, 2),
            "cumulative_pnl":   round(cumulative_pnl, 2),
            "bankroll":         round(bankroll, 2),
            "data_quality":     data_quality,
            "skipped":          False,
        })

    results_df = pd.DataFrame(results)

    # --- Compute summary ---
    summary = compute_summary(results_df)

    return results_df, summary


def compute_summary(df: pd.DataFrame) -> dict:
    """
    Computes overall backtest statistics from results DataFrame.
    """
    bets = df[(df["skipped"] == False) & (df["bet_team"].notna())]
    no_bets = df[(df["skipped"] == False) & (df["bet_team"].isna())]
    skipped = df[df["skipped"] == True]

    wins   = bets[bets["bet_result"] == "win"]
    losses = bets[bets["bet_result"] == "loss"]

    total_wagered = bets["bet_stake"].sum()
    net_profit    = bets["profit"].sum()
    roi           = (net_profit / total_wagered * 100) if total_wagered > 0 else 0

    return {
        "total_games":    len(df),
        "games_bet":      len(bets),
        "games_no_bet":   len(no_bets),
        "games_skipped":  len(skipped),
        "wins":           len(wins),
        "losses":         len(losses),
        "win_rate":       round(len(wins) / len(bets) * 100, 1) if len(bets) > 0 else 0,
        "total_wagered":  round(total_wagered, 2),
        "net_profit":     round(net_profit, 2),
        "roi_pct":        round(roi, 2),
        "final_bankroll": round(STARTING_BANKROLL + net_profit, 2),
    }


def print_summary(results_df: pd.DataFrame, summary: dict):
    """
    Prints a clean formatted summary of backtest results.
    """
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS — 2026 NCAA Tournament")
    print("=" * 60)

    print(f"\n{'Games analyzed:':<25} {summary['total_games']}")
    print(f"{'Games bet:':<25} {summary['games_bet']}")
    print(f"{'Games skipped:':<25} {summary['games_skipped']} (missing team data)")
    print(f"{'Games no bet (-EV):':<25} {summary['games_no_bet']}")

    print(f"\n{'Win/Loss record:':<25} {summary['wins']}W - {summary['losses']}L")
    print(f"{'Win rate:':<25} {summary['win_rate']}%")

    print(f"\n{'Starting bankroll:':<25} ${STARTING_BANKROLL:,.2f}")
    print(f"{'Total wagered:':<25} ${summary['total_wagered']:,.2f}")
    print(f"{'Net profit/loss:':<25} ${summary['net_profit']:+,.2f}")
    print(f"{'ROI:':<25} {summary['roi_pct']:+.2f}%")
    print(f"{'Final bankroll:':<25} ${summary['final_bankroll']:,.2f}")

    print("\n--- BETS BY ROUND ---")
    bets = results_df[
        (results_df["skipped"] == False) &
        (results_df["bet_team"].notna())
    ]

    if len(bets) > 0:
        round_order = ["First Four", "First Round", "Second Round",
                       "Sweet 16", "Elite Eight", "Final Four", "Championship"]
        for r in round_order:
            round_bets = bets[bets["round"] == r]
            if len(round_bets) == 0:
                continue
            round_wins   = len(round_bets[round_bets["bet_result"] == "win"])
            round_profit = round_bets["profit"].sum()
            print(f"  {r:<15} {len(round_bets):>3} bets  "
                  f"{round_wins}W-{len(round_bets)-round_wins}L  "
                  f"P&L: ${round_profit:+,.2f}")

    print("\n--- TOP +EV BETS ---")
    top_bets = bets.nlargest(5, "ev_a")[
        ["team_a", "team_b", "round", "ev_a", "bet_team", "bet_result", "profit"]
    ]
    print(top_bets.to_string(index=False))
    
    print("\n--- PERFORMANCE BY DATA QUALITY ---")
    for quality in ["real", "approximated"]:
        q_bets = bets[bets["data_quality"] == quality]
        if len(q_bets) == 0:
            continue
        q_wins = len(q_bets[q_bets["bet_result"] == "win"])
        q_wagered = q_bets["bet_stake"].sum()
        q_profit = q_bets["profit"].sum()
        q_roi = (q_profit / q_wagered * 100) if q_wagered > 0 else 0
        print(f"  {quality:<15} "
              f"{len(q_bets):>3} bets  "
              f"{q_wins}W-{len(q_bets)-q_wins}L  "
              f"wagered: ${q_wagered:,.2f}  "
              f"P&L: ${q_profit:+,.2f}  "
              f"ROI: {q_roi:+.1f}%")

    print("\n--- CALIBRATION CHECK ---")
    print("(Model probability buckets vs actual win rate)")
    no_skip = results_df[results_df["skipped"] == False].copy()

    # Build one row per team per game for calibration
    cal_rows = []
    for _, row in no_skip.iterrows():
        cal_rows.append({
            "model_prob": row["model_prob_a"],
            "won": 1 if row["winner"] == row["team_a"] else 0
        })
        cal_rows.append({
            "model_prob": row["model_prob_b"],
            "won": 1 if row["winner"] == row["team_b"] else 0
        })

    cal_df = pd.DataFrame(cal_rows)
    cal_df["bucket"] = pd.cut(
        cal_df["model_prob"],
        bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        labels=["0-10%", "10-20%", "20-30%", "30-40%", "40-50%",
                "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
    )

    cal_summary = cal_df.groupby("bucket", observed=True).agg(
        predictions=("model_prob", "count"),
        actual_wins=("won", "sum"),
        avg_model_prob=("model_prob", "mean")
    ).reset_index()

    cal_summary["actual_win_rate"] = (
        cal_summary["actual_wins"] / cal_summary["predictions"] * 100
    ).round(1)
    cal_summary["avg_model_prob_pct"] = (
        cal_summary["avg_model_prob"] * 100
    ).round(1)
    cal_summary["gap"] = (
        cal_summary["actual_win_rate"] - cal_summary["avg_model_prob_pct"]
    ).round(1)

    print(f"\n  {'Bucket':<10} {'Predictions':>12} {'Model%':>8} "
          f"{'Actual%':>9} {'Gap':>7}")
    print("  " + "-" * 52)
    for _, row in cal_summary.iterrows():
        if row["predictions"] == 0:
            continue
        print(f"  {str(row['bucket']):<10} "
              f"{int(row['predictions']):>12} "
              f"{row['avg_model_prob_pct']:>7.1f}% "
              f"{row['actual_win_rate']:>8.1f}% "
              f"{row['gap']:>+7.1f}%")


