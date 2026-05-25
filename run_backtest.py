from src.backtest import run_backtest

print("\n" + "="*60)
print("MODEL COMPARISON — V1 vs V2 vs V3")
print("="*60)

summaries = {}

for version in ["v1", "v2", "v3"]:
    print(f"\nRunning {version.upper()}...")
    df, summary = run_backtest(model_version=version)
    summaries[version] = summary
    df.to_csv(f"data/processed/backtest_{version}.csv", index=False)

print("\n\n" + "="*60)
print("COMPARISON SUMMARY")
print("="*60)
print(f"\n{'Metric':<22} {'V1 (Log5)':>14} {'V2 (Efficiency)':>16} {'V3 (Blend)':>12}")
print("-" * 66)

rows = [
    ("Games Bet",      "games_bet",      lambda v: f"{v:>14d}"),
    ("Games Skipped",  "games_skipped",  lambda v: f"{v:>14d}"),
    ("Win Rate",       "win_rate",       lambda v: f"{v:>13.1f}%"),
    ("Total Wagered",  "total_wagered",  lambda v: f"  ${v:>10,.2f}"),
    ("Net Profit",     "net_profit",     lambda v: f"  ${v:>+10,.2f}"),
    ("ROI",            "roi_pct",        lambda v: f"{v:>13.2f}%"),
    ("Final Bankroll", "final_bankroll", lambda v: f"  ${v:>10,.2f}"),
]

for label, key, fmt in rows:
    row = f"{label:<22}"
    for v in ["v1", "v2", "v3"]:
        row += fmt(summaries[v][key])
    print(row)

print("\nAll three backtest results saved to data/processed/")
print("\n--- KEY INSIGHT ---")
for v in ["v1", "v2", "v3"]:
    s = summaries[v]
    print(f"{v.upper()}: {s['wins']}W-{s['losses']}L  "
          f"Win rate: {s['win_rate']}%  "
          f"ROI: {s['roi_pct']:+.2f}%  "
          f"Profit: ${s['net_profit']:+,.2f}")