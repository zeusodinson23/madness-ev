"""
MadnessEV — March Madness Expected Value Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import base64
from pathlib import Path

st.set_page_config(
    page_title="MadnessEV",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
:root {
    --bg:#F4F6FA; --bg-card:#FFFFFF; --border:#DDE3EF;
    --mm-blue:#1A6DCC; --mm-blue-dark:#1255A3; --mm-blue-pale:#E8F0FB;
    --text:#0D1020; --text-mid:#3A4460; --text-dim:#7A8AAA;
}
html,body,[class*="css"],.main,.block-container,
[data-testid="stAppViewContainer"],[data-testid="stMain"] {
    background-color:var(--bg) !important;
    color:var(--text) !important;
    font-family:'Syne',sans-serif !important;
}
header[data-testid="stHeader"] {
    background-color:var(--bg-card) !important;
    border-bottom:1px solid var(--border) !important;
}
.block-container { padding-top:2rem !important; max-width:1400px !important; }
[data-testid="stSidebar"] {
    background-color:var(--bg-card) !important;
    border-right:2px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color:var(--text) !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color:var(--text-dim) !important; }
[data-testid="stSidebar"] hr { border-color:var(--border) !important; }
[data-testid="stSidebar"] label { color:var(--text-mid) !important; font-size:0.88rem; }
[data-testid="stMetric"] {
    background:var(--bg-card) !important;
    border:1px solid var(--border) !important;
    border-top:3px solid var(--mm-blue) !important;
    border-radius:8px !important;
    padding:14px 16px !important;
    box-shadow:0 1px 4px rgba(0,0,0,0.06) !important;
    min-width:0 !important;
}
[data-testid="stMetricValue"] {
    font-family:'JetBrains Mono',monospace !important;
    font-size:1.25rem !important;
    color:var(--mm-blue) !important;
    white-space:nowrap !important;
    overflow:hidden !important;
    text-overflow:ellipsis !important;
    display:block !important;
}
[data-testid="stMetricLabel"] {
    color:var(--text-dim) !important;
    font-size:0.6rem !important;
    text-transform:uppercase !important;
    letter-spacing:0.1em !important;
}
h1 { font-size:2.2rem !important; font-weight:800 !important; color:var(--text) !important; letter-spacing:-0.02em !important; }
h2 { font-size:0.68rem !important; font-weight:700 !important; color:var(--text-dim) !important; letter-spacing:0.15em !important; text-transform:uppercase !important; margin-top:1.8rem !important; }
p,li { color:var(--text-mid) !important; }
strong { color:var(--text) !important; }
hr { border-color:var(--border) !important; margin:1.2rem 0 !important; }
.mm-table { width:100%; border-collapse:collapse; font-family:'JetBrains Mono',monospace; font-size:0.77rem; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,0.04); }
.mm-table th { background-color:#E8F0FB; color:#1255A3; font-weight:700; text-align:center; padding:10px 12px; letter-spacing:0.04em; border-bottom:2px solid #DDE3EF; }
.mm-table td { text-align:center; padding:8px 12px; border-bottom:1px solid #EEF1F8; color:#3A4460; background:#FFFFFF; }
.mm-table tr:last-child td { border-bottom:none; }
.mm-table tr:hover td { background-color:#F8FAFF; }
[data-baseweb="select"] > div { background-color:var(--bg-card) !important; border-color:var(--border) !important; color:var(--text) !important; }
[data-baseweb="tag"] { background-color:var(--mm-blue-pale) !important; border:1px solid var(--mm-blue) !important; }
[data-baseweb="tag"] span { color:var(--mm-blue-dark) !important; }
[data-testid="stNumberInput"] input { font-family:'JetBrains Mono',monospace !important; background:var(--bg-card) !important; border-color:var(--border) !important; color:var(--text) !important; }
label { color:var(--text-dim) !important; font-size:0.75rem !important; text-transform:uppercase !important; letter-spacing:0.08em !important; }
[data-testid="stCheckbox"] { margin-top:28px !important; }
[data-testid="stCheckbox"] label { color:var(--text-mid) !important; font-size:0.82rem !important; text-transform:none !important; letter-spacing:0 !important; }
[data-testid="stCodeBlock"] pre { background:var(--bg) !important; border:1px solid var(--border) !important; border-left:3px solid var(--mm-blue) !important; color:var(--text) !important; }
.title-accent { width:44px; height:3px; background:var(--mm-blue); margin:2px 0 22px 0; border-radius:2px; }
[data-testid="stSpinner"] > div { border-top-color:var(--mm-blue) !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_logo_b64():
    for name in ["logo_transparent.png", "logo.png"]:
        p = Path(name)
        if p.exists():
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

def df_to_html(df):
    rows_html = "".join(
        f"<tr>{''.join(f'<td>{v}</td>' for v in row)}</tr>"
        for _, row in df.iterrows()
    )
    headers = "".join(f"<th>{col}</th>" for col in df.columns)
    return f'<table class="mm-table"><thead><tr>{headers}</tr></thead><tbody>{rows_html}</tbody></table>'


# ── Load data — cached per model version ───────────────────────────────────────
@st.cache_data
def load_data(model_version: str = "v1"):
    from src.backtest import run_backtest
    return run_backtest(model_version=model_version)

with st.spinner("Loading model..."):
    results_df, _ = load_data(st.session_state.get("p_model", "v1"))


# ── Recalculate P&L ────────────────────────────────────────────────────────────
def recalculate_pnl(df, kelly_mult, starting_bankroll):
    from src.utils import american_to_decimal, kelly_fraction as kf_fn

    bets = df[
        (df["skipped"] == False) & (df["bet_team"].notna())
    ].copy().reset_index(drop=True)

    if len(bets) == 0:
        return pd.DataFrame(), {
            "games_bet":0,"wins":0,"losses":0,"win_rate":0.0,
            "total_wagered":0.0,"net_profit":0.0,"roi_on_wagered":0.0,
            "roi_on_bankroll":0.0,
            "final_bankroll":float(starting_bankroll),
            "starting_bankroll":float(starting_bankroll),
        }

    bankroll = float(starting_bankroll)
    cum_pnl  = 0.0
    rows     = []

    for _, row in bets.iterrows():
        mp  = row["model_prob_a"] if row["bet_team"] == row["team_a"] else row["model_prob_b"]
        dec = american_to_decimal(int(row["bet_odds"]))
        fk  = kf_fn(mp, dec)
        stk = max(0.0, bankroll * fk * kelly_mult)

        if   row["bet_result"] == "win":  profit = stk * (dec - 1)
        elif row["bet_result"] == "loss": profit = -stk
        else:                             profit = 0.0

        cum_pnl += profit
        bankroll = float(starting_bankroll) + cum_pnl

        r = row.copy()
        r["bet_stake"]      = round(stk, 2)
        r["profit"]         = round(profit, 2)
        r["cumulative_pnl"] = round(cum_pnl, 2)
        r["bankroll"]       = round(bankroll, 2)
        rows.append(r)

    rd      = pd.DataFrame(rows)
    wagered = rd["bet_stake"].sum()
    net     = rd["profit"].sum()
    wins    = len(rd[rd["bet_result"] == "win"])
    n       = len(rd)

    return rd, {
        "games_bet":         n,
        "wins":              wins,
        "losses":            n - wins,
        "win_rate":          round(wins/n*100, 1) if n else 0,
        "total_wagered":     round(wagered, 2),
        "net_profit":        round(net, 2),
        "roi_on_wagered":    round(net/wagered*100, 2) if wagered else 0,
        "roi_on_bankroll":   round(net/float(starting_bankroll)*100, 2),
        "final_bankroll":    round(float(starting_bankroll)+net, 2),
        "starting_bankroll": float(starting_bankroll),
    }


# ── Session state ──────────────────────────────────────────────────────────────
PERSISTENCE = {
    "p_rounds":   [],
    "p_quality":  [],
    "p_kelly":    "1/4 Kelly",
    "p_bankroll": 1000.0,
    "p_ev_only":  False,
    "p_model":    "v1",
}
for k, v in PERSISTENCE.items():
    if k not in st.session_state:
        st.session_state[k] = v

KELLY_MAP    = {"1/4 Kelly": 0.25, "1/2 Kelly": 0.5, "Full Kelly": 1.0}
KELLY_OPT    = list(KELLY_MAP.keys())
ROUND_OPT    = ["First Four","First Round","Second Round",
                "Sweet 16","Elite Eight","Final Four","Championship"]
MODEL_OPT    = ["v1", "v2", "v3"]
MODEL_LABELS = {"v1": "V1 — Log5", "v2": "V2 — Efficiency", "v3": "V3 — Blend"}

PLOT_BASE = dict(
    paper_bgcolor="#F4F6FA", plot_bgcolor="#FFFFFF",
    font=dict(family="JetBrains Mono", color="#7A8AAA", size=11),
    margin=dict(l=10, r=10, t=24, b=40),
)
AX = dict(gridcolor="#EEF1F8", color="#AAB4CC", zeroline=False, showline=False)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_b64 = get_logo_b64()
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="width:100%;max-width:200px;margin-bottom:8px;">',
            unsafe_allow_html=True
        )
    st.markdown(
        "<span style='color:#AAB4CC;font-size:0.68rem;"
        "letter-spacing:0.15em;text-transform:uppercase'>"
        "2026 NCAA Tournament</span>", unsafe_allow_html=True
    )
    st.markdown("---")
    page = st.radio("nav",
        ["EV Scanner","P&L Tracker","Calibration","Methodology"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    active_model = MODEL_LABELS.get(st.session_state.get("p_model", "v1"), "Log5 V1")
    st.markdown(
        f"<span style='color:#AAB4CC;font-size:0.68rem;line-height:2'>"
        f"Model: {active_model}<br>Team data: CBBD API<br>"
        f"Odds: DraftKings + Odds API</span>",
        unsafe_allow_html=True
    )


# ── Helpers ────────────────────────────────────────────────────────────────────
def apply_filters(base_df):
    df = base_df.copy()  # include all games, skipped and non-skipped
    if st.session_state["p_rounds"]:
        df = df[df["round"].isin(st.session_state["p_rounds"])]
    if st.session_state["p_quality"]:
        df = df[df["data_quality"].isin(st.session_state["p_quality"])]
    if st.session_state["p_ev_only"]:
        df = df[df["bet_team"].notna()]
    return df

def restore_widget(w_key, p_key):
    if w_key not in st.session_state:
        st.session_state[w_key] = st.session_state[p_key]

def save_widget(w_key, p_key):
    st.session_state[p_key] = st.session_state[w_key]


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EV SCANNER
# ══════════════════════════════════════════════════════════════════════════════
if page == "EV Scanner":
    st.markdown("# EV Scanner")
    st.markdown('<div class="title-accent"></div>', unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    f1, f2, f3, f4, f5, f6 = st.columns([2.0, 1.6, 1.3, 1.2, 1.2, 0.7])

    with f1:
        restore_widget("w_rounds", "p_rounds")
        st.multiselect("Round", options=ROUND_OPT,
                       placeholder="All rounds", key="w_rounds")
        save_widget("w_rounds", "p_rounds")

    with f2:
        restore_widget("w_quality", "p_quality")
        st.multiselect("Data Quality", options=["real","approximated"],
                       placeholder="All quality", key="w_quality")
        save_widget("w_quality", "p_quality")

    with f3:
        restore_widget("w_model", "p_model")
        st.selectbox("Model", options=MODEL_OPT,
                     format_func=lambda x: MODEL_LABELS[x], key="w_model")
        save_widget("w_model", "p_model")

    with f4:
        restore_widget("w_kelly", "p_kelly")
        st.selectbox("Kelly Fraction", options=KELLY_OPT, key="w_kelly")
        save_widget("w_kelly", "p_kelly")

    with f5:
        restore_widget("w_bankroll", "p_bankroll")
        st.number_input("Starting Bankroll ($)",
                        min_value=100.0, max_value=10_000_000.0,
                        step=100.0, format="%.0f", key="w_bankroll")
        save_widget("w_bankroll", "p_bankroll")

    with f6:
        restore_widget("w_ev_only", "p_ev_only")
        st.checkbox("+EV only", key="w_ev_only")
        save_widget("w_ev_only", "p_ev_only")

    kelly_mult = KELLY_MAP[st.session_state["p_kelly"]]
    bankroll   = st.session_state["p_bankroll"]

    # Reload data with selected model — cached so only reruns when model changes
    results_df, _ = load_data(st.session_state["p_model"])

    df = apply_filters(results_df)
    recalc_bets, rs = recalculate_pnl(df, kelly_mult, bankroll)

    # ── Stats ─────────────────────────────────────────────────────────────────
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("Games Shown",       len(df))
    s2.metric("Bets Placed",        rs["games_bet"])
    s3.metric("Win Rate",           f"{rs['win_rate']}%")
    s4.metric("Net Profit",         f"${rs['net_profit']:+,.2f}")
    s5.metric("ROI On Wagered",     f"{rs['roi_on_wagered']:+.1f}%")
    s6.metric("Return On Bankroll", f"{rs['roi_on_bankroll']:+.1f}%")

    st.markdown("")

    # ── Table ─────────────────────────────────────────────────────────────────
    from src.utils import american_to_decimal, kelly_fraction as kf_fn

    rows = []
    for i, (_, r) in enumerate(df.iterrows(), start=1):
        has_bet = pd.notna(r["bet_team"]) and r["bet_stake"] > 0
        if has_bet:
            mp  = r["model_prob_a"] if r["bet_team"] == r["team_a"] else r["model_prob_b"]
            dec = american_to_decimal(int(r["bet_odds"]))
            stk = round(bankroll * kf_fn(mp, dec) * kelly_mult, 2)
            match = recalc_bets[
                (recalc_bets["team_a"] == r["team_a"]) &
                (recalc_bets["team_b"] == r["team_b"])
            ] if len(recalc_bets) > 0 else pd.DataFrame()
            pnl_str = f"${match.iloc[0]['profit']:+.2f}" if not match.empty else ""
            res_str = r["bet_result"].upper() if pd.notna(r.get("bet_result")) else "PENDING"
            bet_str = f"BET {r['bet_team']}"
            stk_str = f"${stk:.2f}"
        else:
            pnl_str = res_str = stk_str = ""
            bet_str = "SKIPPED" if r.get("skipped") == True else "No Bet"

        # Helper — returns formatted value or "N/A" if NaN/None
        def fmt_pct(val):
            if pd.isna(val):
                return "N/A"
            try:
                return f"{float(val)*100:.1f}%"
            except (TypeError, ValueError):
                return "N/A"

        def fmt_ev(val):
            if pd.isna(val):
                return "N/A"
            try:
                return f"${float(val):+.2f}"
            except (TypeError, ValueError):
                return "N/A"

        rows.append({
            "#":         i,
            "Round":     r["round"],
            "Matchup":   f"{r['team_a']} vs {r['team_b']}",
            "Model A%":  fmt_pct(r["model_prob_a"]),
            "Model B%":  fmt_pct(r["model_prob_b"]),
            "Market A%": fmt_pct(r["market_prob_a"]),
            "Market B%": fmt_pct(r["market_prob_b"]),
            "Edge":      fmt_ev(r["edge_a"]).replace("$","") if fmt_ev(r["edge_a"]) != "N/A" else "N/A",
            "Ev A":      fmt_ev(r["ev_a"]),
            "Ev B":      fmt_ev(r["ev_b"]),
            "Bet":       bet_str,
            "Stake":     stk_str,
            "Result":    res_str,
            "P&L":       pnl_str,
            "Quality":   r["data_quality"],
        })

    st.markdown(df_to_html(pd.DataFrame(rows)), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — P&L TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "P&L Tracker":
    st.markdown("# P&L Tracker")
    st.markdown('<div class="title-accent"></div>', unsafe_allow_html=True)

    kelly_mult = KELLY_MAP[st.session_state["p_kelly"]]
    bankroll   = st.session_state["p_bankroll"]

    # Use same model and filters as EV Scanner
    results_df, _ = load_data(st.session_state["p_model"])
    df_filtered = apply_filters(results_df)
    bets_recalc, ds = recalculate_pnl(df_filtered, kelly_mult, bankroll)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Starting",          f"${ds['starting_bankroll']:,.2f}")
    m2.metric("Final Bankroll",    f"${ds['final_bankroll']:,.2f}")
    m3.metric("Net Profit",        f"${ds['net_profit']:+,.2f}")
    m4.metric("Win Rate",          f"{ds['win_rate']}%")
    m5.metric("ROI On Wagered",    f"{ds['roi_on_wagered']:+.1f}%")
    m6.metric("Return/Bankroll",   f"{ds['roi_on_bankroll']:+.1f}%")

    st.markdown("")

    if len(bets_recalc) == 0:
        st.info("No bets match the current filters. Adjust filters on the EV Scanner page.")
    else:
        bets_df = bets_recalc.copy().reset_index(drop=True)
        bets_df["bet_num"] = range(1, len(bets_df) + 1)
        bets_df["label"]   = bets_df.apply(
            lambda r: f"{r['team_a']} vs {r['team_b']} ({r['round']})", axis=1
        )

        fig = go.Figure()
        fig.add_hline(y=0, line_dash="dot", line_color="#DDE3EF", line_width=1.5)

        x_vals   = bets_df["bet_num"].tolist()
        y_vals   = bets_df["cumulative_pnl"].tolist()
        res_list = bets_df["bet_result"].tolist()

        prev_y = 0
        for i in range(len(x_vals)):
            color = "#00884A" if res_list[i] == "win" else "#CC2244"
            fig.add_trace(go.Scatter(
                x=[x_vals[i]-1, x_vals[i]], y=[prev_y, y_vals[i]],
                mode="lines", line=dict(color=color, width=2.5),
                showlegend=False, hoverinfo="skip"
            ))
            prev_y = y_vals[i]

        for res, color, lbl in [("win","#00884A","Win"),("loss","#CC2244","Loss")]:
            mask = bets_df["bet_result"] == res
            if mask.any():
                fig.add_trace(go.Scatter(
                    x=bets_df.loc[mask,"bet_num"],
                    y=bets_df.loc[mask,"cumulative_pnl"],
                    mode="markers",
                    marker=dict(color=color, size=6,
                                line=dict(color="#F4F6FA", width=1.5)),
                    name=lbl, text=bets_df.loc[mask,"label"],
                    hovertemplate=f"<b>%{{text}}</b><br>P&L: $%{{y:+.2f}}<extra>{lbl.upper()}</extra>"
                ))

        fig.update_layout(
            **PLOT_BASE, height=380,
            xaxis=dict(title="Bet Number", **AX),
            yaxis=dict(title="Cumulative P&L ($)", tickprefix="$", **AX),
            legend=dict(bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="#DDE3EF", borderwidth=1),
            hovermode="closest"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("## By Round")
        round_order = ["First Four","First Round","Second Round",
                       "Sweet 16","Elite Eight","Final Four","Championship"]
        rr = []
        for r in round_order:
            rb = bets_df[bets_df["round"] == r]
            if not len(rb): continue
            w = len(rb[rb["bet_result"] == "win"])
            wag = rb["bet_stake"].sum(); pnl = rb["profit"].sum()
            rr.append({"Round":r,"Bets":len(rb),"W":w,"L":len(rb)-w,
                       "Win%":f"{w/len(rb)*100:.0f}%",
                       "Wagered":f"${wag:,.2f}",
                       "P&L":f"${pnl:+,.2f}",
                       "ROI":f"{pnl/wag*100:+.1f}%" if wag else "0%"})
        st.markdown(df_to_html(pd.DataFrame(rr)), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("## Real vs Approximated Odds")
        qr = []
        for q in ["real","approximated"]:
            qb = bets_df[bets_df["data_quality"] == q]
            if not len(qb): continue
            w = len(qb[qb["bet_result"] == "win"])
            wag = qb["bet_stake"].sum(); pnl = qb["profit"].sum()
            qr.append({"Quality":q.capitalize(),"Bets":len(qb),"W":w,"L":len(qb)-w,
                       "Win%":f"{w/len(qb)*100:.0f}%",
                       "Wagered":f"${wag:,.2f}",
                       "P&L":f"${pnl:+,.2f}",
                       "ROI":f"{pnl/wag*100:+.1f}%" if wag else "0%"})
        st.markdown(df_to_html(pd.DataFrame(qr)), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Calibration":
    st.markdown("# Model Calibration")
    st.markdown('<div class="title-accent"></div>', unsafe_allow_html=True)
    st.markdown("""
    A perfectly calibrated model lies exactly on the diagonal.
    When it predicts 70%, that team wins 70% of the time.
    Points **above** the line = model underestimates.
    Points **below** the line = model overestimates.
    Dot size reflects number of predictions in that bucket.
    """)

    # Use selected model for calibration too
    results_df, _ = load_data(st.session_state["p_model"])
    no_skip = results_df[results_df["skipped"] == False].copy()

    cr = []
    for _, row in no_skip.iterrows():
        cr.append({"model_prob":row["model_prob_a"],
                   "won":1 if row["winner"]==row["team_a"] else 0})
        cr.append({"model_prob":row["model_prob_b"],
                   "won":1 if row["winner"]==row["team_b"] else 0})

    cal_df = pd.DataFrame(cr)
    cal_df["bucket"] = pd.cut(cal_df["model_prob"],
        bins=[0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0],
        labels=[.05,.15,.25,.35,.45,.55,.65,.75,.85,.95])
    cs = cal_df.groupby("bucket", observed=True).agg(
        count=("model_prob","count"),
        actual=("won","mean"),
        avg_p=("model_prob","mean")
    ).reset_index()
    cs["bucket"] = cs["bucket"].astype(float)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",
        line=dict(color="#DDE3EF",dash="dash",width=1.5),name="Perfect Calibration"))
    fig.add_trace(go.Scatter(
        x=cs["avg_p"],y=cs["actual"],mode="markers+lines",
        marker=dict(color="#1A6DCC",size=cs["count"]*2,sizemode="area",
                    line=dict(color="#F4F6FA",width=1.5),opacity=0.85),
        line=dict(color="rgba(26,109,204,0.35)",width=1.5),
        name=f"Model ({MODEL_LABELS.get(st.session_state['p_model'], 'V1')})",
        hovertemplate="Model: %{x:.0%}<br>Actual: %{y:.0%}<extra></extra>"
    ))
    fig.update_layout(
        **PLOT_BASE, height=450,
        xaxis=dict(title="Model Predicted Probability",
                   tickformat=".0%",range=[-.02,1.02],**AX),
        yaxis=dict(title="Actual Win Rate",
                   tickformat=".0%",range=[-.02,1.02],**AX),
        legend=dict(bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#DDE3EF",borderwidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("## Bucket Detail")
    tbl = []
    for _, row in cs.iterrows():
        tbl.append({
            "Bucket":f"{row['bucket']*100:.0f}%",
            "Predictions":int(row["count"]),
            "Model Avg":f"{row['avg_p']*100:.1f}%",
            "Actual":f"{row['actual']*100:.1f}%",
            "Gap":f"{(row['actual']-row['bucket'])*100:+.1f}%",
        })
    st.markdown(df_to_html(pd.DataFrame(tbl)), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Methodology":
    st.markdown("# Methodology")
    st.markdown('<div class="title-accent"></div>', unsafe_allow_html=True)

    # ── Custom methodology styles ──────────────────────────────────────────────
    st.markdown("""
    <style>
    .meth-section {
        margin: 2rem 0 0.5rem 0;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #1A6DCC;
    }
    .meth-h2 {
        font-size: 1.3rem;
        font-weight: 800;
        color: #0D1020;
        margin: 0.2rem 0 0.8rem 0;
        letter-spacing: -0.01em;
    }
    .meth-body {
        font-size: 0.92rem;
        color: #3A4460;
        line-height: 1.8;
        margin-bottom: 1rem;
    }
    .meth-formula {
        background: #F4F6FA;
        border-left: 3px solid #1A6DCC;
        border-radius: 0 6px 6px 0;
        padding: 14px 20px;
        margin: 1rem 0;
        font-size: 1.05rem;
        color: #0D1020;
        font-family: 'Syne', sans-serif;
    }
    .meth-formula .formula-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #7A8AAA;
        margin-bottom: 6px;
    }
    .meth-divider {
        border: none;
        border-top: 1px solid #DDE3EF;
        margin: 2.5rem 0;
    }
    .meth-callout {
        background: #E8F0FB;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 1rem 0;
        font-size: 0.88rem;
        color: #1255A3;
        line-height: 1.7;
    }
    .meth-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.84rem;
        margin: 1rem 0;
    }
    .meth-table th {
        background: #E8F0FB;
        color: #1255A3;
        font-weight: 700;
        text-align: left;
        padding: 10px 14px;
        border-bottom: 2px solid #DDE3EF;
    }
    .meth-table td {
        padding: 9px 14px;
        border-bottom: 1px solid #EEF1F8;
        color: #3A4460;
        vertical-align: top;
    }
    .meth-table tr:last-child td { border-bottom: none; }
    .meth-table tr:hover td { background: #F8FAFF; }
    sup { font-size: 0.65em; vertical-align: super; }
    sub { font-size: 0.65em; vertical-align: sub; }
    </style>
    """, unsafe_allow_html=True)

    # ── OVERVIEW ───────────────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Overview</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">What MadnessEV Does</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="meth-body">
    MadnessEV is a sports betting analytics tool built for the 2026 NCAA Men's Basketball Tournament.
    The core question it answers is deceptively simple: when a bookmaker prices a team at 35% implied
    win probability, is that actually accurate? If our model says that team wins 50% of the time,
    there is a meaningful gap between what the market believes and what the data suggests. That gap
    is where profitable bets live.
    </p>
    <p class="meth-body">
    The project pulls team efficiency ratings from a public basketball analytics API, computes win
    probabilities for every tournament matchup using three separate models, compares those probabilities
    against real bookmaker odds, and identifies bets where the model believes the market has mispriced
    a team. A full retroactive P&L simulation runs across all 67 games of the 2026 tournament to test
    whether the models actually had an edge.
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    # ── DATA ───────────────────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Data Sources</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">Where the Numbers Come From</p>', unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    <strong>Team Efficiency (CBBD API).</strong> Team strength data comes from the College Basketball
    Data API at collegebasketballdata.com. This provides Adjusted Offensive Efficiency (AdjO) and
    Adjusted Defensive Efficiency (AdjD) for all 365 Division I teams for the 2026 season.
    These are not raw stats. They are adjusted for opponent quality and pace, meaning a team that
    scores 85 points against elite defenses every game is rated higher than one that scores 85 against
    weak defenses. Michigan led the country with an AdjO of 130.7 and an AdjD of 88.7, making them
    the most complete team in the dataset.
    </p>
    <p class="meth-body">
    <strong>Barthag.</strong> Barthag is a single number between 0 and 1 representing a team's
    probability of beating an average Division I team on a neutral court. We calculate it from AdjO
    and AdjD using the community reverse-engineered approximation of Barttorvik's formula:
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">Barthag Formula</div>
        Barthag = AdjO<sup>11</sup> / (AdjO<sup>11</sup> + AdjD<sup>11</sup>)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    The exponent of 11 amplifies small differences in efficiency into meaningful probability gaps.
    Michigan's Barthag works out to 0.986, meaning the model expects them to beat an average team
    98.6% of the time. A mid-major team might sit at 0.55. The gap between those two numbers is
    what drives the win probability calculations. Our calculated Barthag values deviate from
    Barttorvik's published figures by an average of 0.009, which is well within acceptable range
    for a model of this type.
    </p>
    <p class="meth-body">
    <strong>Betting Odds.</strong> Odds were sourced from multiple places depending on when each
    game occurred relative to our data collection window. The Odds API captured a live snapshot on
    March 28, covering the Sweet 16 and Elite Eight. DraftKings opening lines from Selection Sunday
    were sourced from OutKick and ESPN articles for all 55 earlier games. VegasInsider provided
    Championship odds. Eight games where no published odds could be found use seed-based approximations
    and are clearly labeled in the dashboard as approximated data.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <table class="meth-table">
        <thead><tr><th>Source</th><th>Games</th><th>Rounds</th><th>Quality</th></tr></thead>
        <tbody>
            <tr><td>The Odds API (March 28 live snapshot)</td><td>6</td><td>Sweet 16 and Elite Eight games</td><td>Real</td></tr>
            <tr><td>DraftKings opening lines via OutKick and ESPN</td><td>55</td><td>First Four through Second Round</td><td>Real</td></tr>
            <tr><td>VegasInsider</td><td>1</td><td>Championship</td><td>Real</td></tr>
            <tr><td>Seed-based approximation</td><td>5</td><td>Various Second Round and Final Four</td><td>Approximated</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    # ── MODELS ─────────────────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">The Models</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">Three Ways to Estimate Win Probability</p>', unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    Once we have each team's Barthag and efficiency ratings, the question becomes: given that Team A
    is rated at 0.986 and Team B at 0.957, what is the actual probability that A beats B in this
    specific game? Three models answer that question in different ways.
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:1rem;font-weight:700;color:#0D1020;margin:1.2rem 0 0.4rem 0;">V1 — Log5 (Barthag-based)</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="meth-body">
    Log5 was invented by baseball statistician Bill James and works beautifully for head-to-head
    sports. The formula takes each team's overall win rate against an average opponent and isolates
    the probability of one beating the other. The intuition is that it filters out the two
    uninformative scenarios (both teams win, both teams lose) and keeps only the signal. If Team A
    beats an average team 97% of the time and Team B beats an average team 86% of the time, Log5
    tells you what happens when they face each other directly.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">Log5 Formula (V1)</div>
        P(A beats B) = (A &times; (1 &minus; B)) / (A &times; (1 &minus; B) + B &times; (1 &minus; A))
        <br><small style="color:#7A8AAA;font-size:0.78rem;">where A and B are each team's Barthag rating</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    For the 2026 Championship, Michigan (Barthag 0.986) against UConn (Barthag 0.957) gives a
    Log5 win probability of 76.3% for Michigan. The market priced Michigan at only 62.1% after
    vig removal. That 14.2 percentage point gap was our edge signal on the championship game.
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:1rem;font-weight:700;color:#0D1020;margin:1.4rem 0 0.4rem 0;">V2 — Efficiency Model (AdjO and AdjD)</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="meth-body">
    Rather than using Barthag as a pre-cooked single number, V2 goes one level deeper and simulates
    the actual game by directly matching each team's offense against the opponent's defense. This
    can capture matchup dynamics that Barthag misses. A team with an elite offense and average
    defense might have the same Barthag as a team with elite defense and average offense, but they
    would perform very differently against certain opponents.
    </p>
    <p class="meth-body">
    The model estimates how many points each team would score per 100 possessions in this specific
    matchup, scales that to a realistic game (approximately 68 possessions), and converts the
    expected scoring margin to a win probability. The conversion uses the fact that college basketball
    game margins follow a roughly normal distribution with a standard deviation of about 11 points.
    So a team expected to win by 5 points wins roughly 67% of the time, and a team expected to win
    by 11 points wins roughly 84% of the time.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">V2 Efficiency Model</div>
        A<sub>pts</sub> = AdjO<sub>A</sub> &times; (AdjD<sub>B</sub> / league avg)<br>
        B<sub>pts</sub> = AdjO<sub>B</sub> &times; (AdjD<sub>A</sub> / league avg)<br>
        Expected margin = (A<sub>pts</sub> &minus; B<sub>pts</sub>) &times; (possessions / 100)<br>
        P(A wins) = normal CDF(expected margin / 11)
        <br><small style="color:#7A8AAA;font-size:0.78rem;">league avg efficiency = 105, possessions = 68 (constant, CBBD does not provide tempo)</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:1rem;font-weight:700;color:#0D1020;margin:1.4rem 0 0.4rem 0;">V3 — Blend (50% V1 + 50% V2)</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="meth-body">
    The blend averages the output of both models. In principle, combining models that make different
    types of errors produces more stable predictions than either model alone. V3 also flags any game
    where V1 and V2 disagree by 5 or more percentage points, treating those as cases where the
    models are picking up different signals and warranting extra scrutiny before betting.
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    # ── BETTING FRAMEWORK ──────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Betting Framework</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">From Win Probability to Bet Sizing</p>', unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    <strong>Converting bookmaker odds to implied probability.</strong> American odds come in two
    formats. Negative odds (like -180) show how much you need to bet to win $100. Positive odds
    (like +155) show how much you win on a $100 bet. Both encode an implied probability of that
    team winning, but bookmakers inflate those probabilities so they sum to more than 100%. That
    excess is their profit margin, called the vig or juice.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">Implied Probability</div>
        Negative odds: P = |odds| / (|odds| + 100)&nbsp;&nbsp;&nbsp;
        e.g. -180 &rarr; 180/280 = 64.3%<br>
        Positive odds: P = 100 / (odds + 100)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        e.g. +155 &rarr; 100/255 = 39.2%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    <strong>Removing the vig.</strong> In the Championship game example, Michigan at -180 implies
    64.3% and UConn at +155 implies 39.2%. Those sum to 103.5%, meaning the bookmaker built in a
    3.5% margin. We divide each by the total to get the fair probabilities the market truly implies:
    Michigan 62.1%, UConn 37.9%, summing to exactly 100%.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">Vig Removal</div>
        Fair probability = Raw implied / (Raw<sub>A</sub> + Raw<sub>B</sub>)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    <strong>Expected Value.</strong> EV answers the question: if I made this exact bet 1,000 times,
    how much would I expect to win or lose per $100 wagered? A positive EV means the bet is
    profitable in the long run given our model's probability. A negative EV means we expect to lose
    money even if we win the occasional game.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">Expected Value (per $100)</div>
        EV = (p &times; profit if win) &minus; ((1 &minus; p) &times; $100)<br>
        <small style="color:#7A8AAA;font-size:0.78rem;">where p is our model's win probability and profit if win = (decimal odds &minus; 1) &times; $100</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    For the Championship: model says Michigan wins 76.3%, decimal odds are 1.556 (profit of $55.60
    per $100 wagered). EV = (0.763 x $55.60) minus (0.237 x $100) = $42.42 minus $23.70 = +$18.72.
    Every $100 bet on Michigan in this scenario was worth $18.72 in expected value, making it a
    strong positive EV opportunity.
    </p>
    <p class="meth-body">
    <strong>Kelly Criterion and Bet Sizing.</strong> Once a positive EV bet is identified, the next
    question is how much to bet. The Kelly Criterion is a formula that calculates the mathematically
    optimal fraction of your bankroll to wager, maximising long-run growth rate.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-formula">
        <div class="formula-label">Kelly Criterion</div>
        Full Kelly = (b &times; p &minus; q) / b<br>
        <small style="color:#7A8AAA;font-size:0.78rem;">
            b = decimal odds minus 1 (net profit per $1 wagered)&nbsp;&nbsp;
            p = model win probability&nbsp;&nbsp;
            q = 1 minus p (loss probability)
        </small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    Full Kelly is mathematically optimal but extremely aggressive in practice. For the Championship,
    it recommended betting 33.6% of the entire bankroll on a single game. In real betting, this
    level of exposure creates too much volatility. Three variants are available in the dashboard:
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <table class="meth-table">
        <thead><tr><th>Variant</th><th>Calculation</th><th>Bankroll Bet (Championship)</th><th>Character</th></tr></thead>
        <tbody>
            <tr><td>Full Kelly</td><td>Full Kelly fraction</td><td>33.6% ($336 on $1,000)</td><td>Maximises growth but very volatile</td></tr>
            <tr><td>Half Kelly</td><td>Full Kelly x 0.5</td><td>16.8% ($168 on $1,000)</td><td>Good balance of growth and safety</td></tr>
            <tr><td>Quarter Kelly</td><td>Full Kelly x 0.25</td><td>8.4% ($84 on $1,000)</td><td>Conservative default used in this backtest</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    # ── KEY FINDINGS ───────────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Key Findings</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">What the Backtest Revealed</p>', unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    <strong>Win rate is a misleading metric in betting.</strong> V2 achieved a 67.3% win rate across
    49 bets while V1 won only 50.0% of 44 bets. Most people would call V2 the better model. But V1
    produced a higher ROI of 27.2% against V2's 17.2%. The reason: V2 bets more frequently on heavy
    favourites who win often but pay out very little. V1 finds fewer but larger edges at better
    prices, generating more return per dollar risked. This mirrors a well-known principle in
    quantitative finance: number of winning trades is irrelevant without knowing the return on each.
    </p>
    <p class="meth-body">
    <strong>Model convergence confirms the data.</strong> V1 uses only Barthag while V2 directly
    models AdjO and AdjD. Despite different mathematical paths, they produce nearly identical
    probabilities on most games (average difference under 2 percentage points). This makes sense:
    Barthag is itself derived from AdjO and AdjD, so both models are working from the same
    underlying information. The convergence is reassuring rather than redundant because it confirms
    the data is internally consistent.
    </p>
    <p class="meth-body">
    <strong>Real odds versus approximated odds.</strong> Games where we had genuine bookmaker odds
    showed significantly different EV profiles than games with seed-based approximations. The
    approximated odds games produced poor ROI because the estimates were not calibrated to real
    market pricing. Any serious evaluation of model performance should filter to real-odds games only.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="meth-callout">
        Backtest results with Quarter Kelly staking on a $1,000 starting bankroll:<br>
        V1 (Log5): 22W-22L &nbsp;|&nbsp; 50.0% win rate &nbsp;|&nbsp; +$403.13 profit &nbsp;|&nbsp; 27.2% ROI on wagered<br>
        V2 (Efficiency): 33W-16L &nbsp;|&nbsp; 67.3% win rate &nbsp;|&nbsp; +$423.94 profit &nbsp;|&nbsp; 17.2% ROI on wagered<br>
        V3 (Blend): 27W-20L &nbsp;|&nbsp; 57.4% win rate &nbsp;|&nbsp; +$408.49 profit &nbsp;|&nbsp; 22.7% ROI on wagered
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    # ── LIMITATIONS ────────────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Limitations</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">What This Does Not Prove</p>', unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    67 games is not enough to draw statistically robust conclusions about model edge. In sports
    betting, even a skilled bettor expects high variance over a single tournament. A model can show
    positive returns over 67 games through luck alone. Confirming genuine edge requires thousands
    of bets across multiple seasons.
    </p>
    <p class="meth-body">
    The odds data has important limitations. First Round games use DraftKings opening lines from
    Selection Sunday, not the closing lines just before tip-off. Closing lines reflect the most
    efficient market pricing after sharp money has moved the line. Opening lines are softer and
    easier to beat, which may inflate the apparent edge in early rounds.
    </p>
    <p class="meth-body">
    The V2 model uses a constant league-average tempo of 68 possessions rather than team-specific
    adjusted tempo. This simplification means two fast-paced teams are modelled the same way as two
    slow teams, even though real game pace would differ significantly. CBBD does not currently
    provide adjusted tempo data through their efficiency endpoint.
    </p>
    <p class="meth-body">
    Eight games in the dataset use seed-based approximated odds rather than published bookmaker
    lines. These should be excluded from any serious evaluation of model performance.
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    st.markdown('<hr class="meth-divider">', unsafe_allow_html=True)

    # ── FUTURE IMPROVEMENTS ────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Future Improvements</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">What the Next Version Would Do Differently</p>', unsafe_allow_html=True)

    st.markdown("""
    <p class="meth-body">
    Building MadnessEV surfaced a clear set of gaps between what the current version does and what
    a genuinely robust sports betting analytics system would look like. These are not hypothetical
    additions but direct lessons from building and testing this one.
    </p>
    <p class="meth-body">
    <strong>Closing lines instead of opening lines.</strong> The single highest-impact improvement
    would be using closing lines rather than opening lines for odds data. Closing lines, recorded
    minutes before tip-off, represent the market at its most efficient after professional bettors
    have had time to move prices. Opening lines are softer and easier to beat, which means the
    current backtest likely overstates the true edge. A fair evaluation of model performance requires
    closing line value analysis, where you compare your model's probability against the line at the
    moment you would actually place the bet.
    </p>
    <p class="meth-body">
    <strong>Adjusted tempo in the V2 model.</strong> V2 currently assumes every game is played at
    league-average pace (68 possessions). In reality, pace varies significantly by team and matchup.
    A game between two slow teams like Virginia and Iowa State plays out very differently from a
    fast-paced game between Gonzaga and Florida. Adding team-specific adjusted tempo would make the
    expected scoring margin calculation meaningfully more accurate, particularly for games involving
    extreme pace outliers. The cbbdata R package has this data; a Python wrapper or a secondary
    scrape from Sports Reference would bring it into this pipeline.
    </p>
    <p class="meth-body">
    <strong>Multi-season backtesting.</strong> 67 games is a single data point in the distribution
    of possible tournament outcomes. A proper validation of model edge requires running the same
    pipeline across five to ten years of tournament data, giving thousands of games to work with.
    Barttorvik and CBBD both have historical data going back to 2008. The pipeline architecture
    already supports this; it would require sourcing historical opening or closing odds, which are
    available through services like The Odds API's historical endpoint or Pinnacle's public data.
    </p>
    <p class="meth-body">
    <strong>Calibrated model weighting for V3.</strong> The current V3 blend weights V1 and V2
    equally at 50/50 with no empirical basis for that split. A better approach would be to run both
    models across historical seasons and weight them by their relative calibration scores, giving
    more weight to whichever model has historically been closer to actual outcomes. This transforms
    V3 from a naive average into a genuinely optimised ensemble.
    </p>
    <p class="meth-body">
    <strong>Live line movement tracking.</strong> The original project design included a line movement
    tracker that would show how odds shifted in the hours before tip-off. Sharp line movement,
    where odds move quickly in one direction without obvious news, is one of the strongest signals
    in sports betting and often indicates professional money. The database schema and polling logic
    were planned but not built for this retrospective version. This would be the most visually
    compelling addition to a live-season version of the tool.
    </p>
    <p class="meth-body">
    <strong>Sport-agnostic architecture for IPL cricket.</strong> The underlying pipeline (efficiency
    ratings, vig removal, EV calculation, Kelly sizing, P&L tracking) is sport-agnostic. The only
    components tied to college basketball are the CBBD API integration and the tournament bracket
    structure. A second sport module for IPL cricket, using Cricsheet ball-by-ball data for team
    strength ratings and a similar efficiency-based model, would demonstrate that the framework
    generalises beyond a single domain. This was always the intended next phase of the project.
    </p>
    """, unsafe_allow_html=True)

    # ── TECH STACK ─────────────────────────────────────────────────────────────
    st.markdown('<p class="meth-section">Technical Stack</p>', unsafe_allow_html=True)
    st.markdown('<p class="meth-h2">How It Was Built</p>', unsafe_allow_html=True)

    st.markdown("""
    <table class="meth-table">
        <thead><tr><th>Component</th><th>Technology</th><th>Purpose</th></tr></thead>
        <tbody>
            <tr><td>Language</td><td>Python 3.11</td><td>Core pipeline and modelling</td></tr>
            <tr><td>Team efficiency data</td><td>CBBD API (collegebasketballdata.com)</td><td>AdjO, AdjD for 365 teams with 3-layer caching</td></tr>
            <tr><td>Odds data</td><td>The Odds API + DraftKings opening lines</td><td>Real bookmaker moneyline prices</td></tr>
            <tr><td>Analytics</td><td>pandas, numpy, scipy</td><td>Data processing, normal distribution for V2</td></tr>
            <tr><td>Dashboard</td><td>Streamlit</td><td>Interactive web interface</td></tr>
            <tr><td>Charts</td><td>Plotly</td><td>P&L and calibration visualisations</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)