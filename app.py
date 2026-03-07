"""
NSE 200 Swing Trade Screener — Streamlit version
"""

import time
import random
from datetime import datetime
from dataclasses import dataclass
from typing import List

import streamlit as st
import pandas as pd

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Swing Screener",
    page_icon="📈",
    layout="wide",
)

# ─────────────────────────────────────────────
# DATA: NSE 200 Stocks (sample subset)
# ─────────────────────────────────────────────
NSE_200_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK",
    "LT", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "POWERGRID",
    "NTPC", "TECHM", "HCLTECH", "BAJAJFINSV", "ONGC",
    "TATAMOTORS", "ADANIPORTS", "DIVISLAB", "DRREDDY", "CIPLA",
    "JSWSTEEL", "TATASTEEL", "HINDALCO", "COALINDIA", "IOC",
    "BPCL", "GRASIM", "EICHERMOT", "HEROMOTOCO", "BRITANNIA",
    "SHREECEM", "INDUSINDBK", "M&M", "BAJAJ-AUTO", "SIEMENS",
    "PIDILITIND", "DABUR", "GODREJCP", "MARICO", "COLPAL",
]

# ─────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────
@dataclass
class ScreenerResult:
    symbol: str
    signal: str
    rsi: float
    macd: str
    above_ema: bool
    volume_surge: bool
    score: int


# ─────────────────────────────────────────────
# DEMO DATA GENERATOR
# ─────────────────────────────────────────────
def generate_demo_data() -> List[ScreenerResult]:
    results = []
    candidates = random.sample(NSE_200_STOCKS, k=random.randint(8, 18))
    for sym in candidates:
        rsi = round(random.uniform(45, 70), 1)
        macd = random.choice(["Bullish", "Neutral"])
        above_ema = random.random() > 0.3
        volume_surge = random.random() > 0.4
        score = int(
            (rsi / 100) * 40
            + (20 if macd == "Bullish" else 0)
            + (20 if above_ema else 0)
            + (20 if volume_surge else 0)
        )
        signal = "BUY" if score >= 60 else "WATCH"
        results.append(ScreenerResult(sym, signal, rsi, macd, above_ema, volume_surge, score))
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def results_to_df(results: List[ScreenerResult]) -> pd.DataFrame:
    return pd.DataFrame([{
        "Symbol":     r.symbol,
        "Signal":     r.signal,
        "RSI":        r.rsi,
        "MACD":       r.macd,
        "Above EMA":  "✔" if r.above_ema else "✘",
        "Vol Surge":  "✔" if r.volume_surge else "✘",
        "Score":      r.score,
    } for r in results])


# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark background */
    .stApp { background-color: #0f1117; }

    /* Header strip */
    .header-strip {
        background: #1a1d27;
        border-bottom: 1px solid #2a2d3a;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .header-title { color: #e2e8f0; font-size: 1.3rem; font-weight: 700; font-family: monospace; }
    .header-sub   { color: #64748b; font-size: 0.85rem; font-family: monospace; }

    /* Strategy panel */
    .strategy-box {
        background: #1a1d27;
        border: 1px solid #2a2d3a;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
        font-family: monospace;
    }
    .strategy-box h4 { color: #e2e8f0; margin: 0 0 8px 0; }
    .strategy-box li { color: #94a3b8; font-size: 0.88rem; margin: 4px 0; }
    .strategy-box .warn { color: #f59e0b; font-size: 0.8rem; margin-top: 10px; }

    /* Signal badges */
    .badge-buy   { background:#052e16; color:#22c55e; padding:2px 10px; border-radius:99px;
                   font-weight:700; font-size:0.8rem; font-family:monospace; }
    .badge-watch { background:#451a03; color:#f59e0b; padding:2px 10px; border-radius:99px;
                   font-weight:700; font-size:0.8rem; font-family:monospace; }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 48px 20px;
        color: #64748b;
        font-family: monospace;
    }
    .empty-state .icon { font-size: 3rem; margin-bottom: 12px; }
    .empty-state h3    { color: #e2e8f0; font-size: 1.1rem; margin: 0; }
    .empty-state p     { font-size: 0.85rem; margin: 6px 0 0 0; }

    /* Scan time */
    .scan-time { color: #64748b; font-size: 0.78rem; font-family: monospace; text-align: right; }

    /* Hide default streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "has_scanned" not in st.session_state:
    st.session_state.has_scanned = False
if "last_scan_time" not in st.session_state:
    st.session_state.last_scan_time = None


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
match_count = len(st.session_state.results)
st.markdown(f"""
<div class="header-strip">
    <span class="header-title">📈 NSE Swing Screener</span>
    <span class="header-sub">
        {len(NSE_200_STOCKS)} stocks · {match_count} matches
    </span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TOOLBAR
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 5])

with col1:
    scan_clicked = st.button("▶  Scan Now", type="primary", use_container_width=True)

with col2:
    show_strategy = st.toggle("ℹ Strategy", value=False)

with col3:
    if st.session_state.last_scan_time:
        st.markdown(
            f'<p class="scan-time">Last scan: {st.session_state.last_scan_time} · Demo data</p>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# SCAN LOGIC (with animated progress)
# ─────────────────────────────────────────────
if scan_clicked:
    progress_bar = st.progress(0, text="Scanning NSE 200 stocks…")
    for i in range(0, 101, 5):
        time.sleep(0.06)
        progress_bar.progress(i, text=f"Scanning NSE 200 stocks… {i}%")
    progress_bar.empty()

    st.session_state.results = generate_demo_data()
    st.session_state.has_scanned = True
    st.session_state.last_scan_time = datetime.now().strftime("%H:%M:%S")
    st.rerun()


# ─────────────────────────────────────────────
# STRATEGY PANEL
# ─────────────────────────────────────────────
if show_strategy:
    st.markdown("""
    <div class="strategy-box">
        <h4>Strategy: Swing Buy Signal</h4>
        <ul>
            <li>RSI between 40–70 (momentum, not overbought)</li>
            <li>MACD bullish crossover or positive histogram</li>
            <li>Price above 20-day EMA (uptrend filter)</li>
            <li>Volume 1.5× 20-day average (institutional interest)</li>
        </ul>
        <p class="warn">⚠ Demo data only · Connect live API for real signals</p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RESULTS TABLE  or  EMPTY STATE
# ─────────────────────────────────────────────
if st.session_state.has_scanned and st.session_state.results:
    df = results_to_df(st.session_state.results)

    # Colour-code Signal column via styler
    def style_signal(val):
        if val == "BUY":
            return "color: #22c55e; font-weight: 700;"
        elif val == "WATCH":
            return "color: #f59e0b; font-weight: 700;"
        return ""

    def style_score(val):
        if val >= 70:
            return "color: #22c55e;"
        elif val >= 50:
            return "color: #f59e0b;"
        return "color: #94a3b8;"

    styled = (
        df.style
        .applymap(style_signal, subset=["Signal"])
        .applymap(style_score,  subset=["Score"])
        .set_properties(**{
            "background-color": "#1a1d27",
            "color": "#e2e8f0",
            "font-family": "monospace",
            "font-size": "0.88rem",
        })
        .set_table_styles([{
            "selector": "th",
            "props": [
                ("background-color", "#2a2d3a"),
                ("color", "#94a3b8"),
                ("font-family", "monospace"),
                ("font-size", "0.85rem"),
                ("text-align", "center"),
            ]
        }])
        .hide(axis="index")
    )

    st.dataframe(styled, use_container_width=True, height=420)

elif not st.session_state.has_scanned:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">▶</div>
        <h3>Ready to Scan</h3>
        <p>Analyze NSE 200 stocks for swing buy signals</p>
        <p style="margin-top:10px; font-size:0.78rem; color:#475569;">
            Currently showing demo data · Connect live API for real-time screening
        </p>
    </div>
    """, unsafe_allow_html=True)
