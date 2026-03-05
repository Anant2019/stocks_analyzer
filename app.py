"""
Nifty 200 — Institutional Alpha Engine v3.1 (Integrated Date Selection)
============================================
Architecture: Singleton Config + Vectorised Engine + Monte Carlo + Date Audit
"""

from __future__ import annotations
import json
import logging
import math
import os
import random
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty 200 · Institutional Alpha Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── [KEEPING YOUR BLOOMBERG_CSS EXACTLY AS IS] ──
BLOOMBERG_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
:root {
    --bg-base:      #060c14;
    --bg-card:      #080f19;
    --bg-deep:      #0a1520;
    --border:       #162030;
    --border-soft:  #1a2d3e;
    --teal:          #00d4aa;
    --sky:           #38bdf8;
    --amber:         #f5c842;
    --red:           #ff4d6d;
    --purple:        #a78bfa;
    --text-hi:       #e8f0f8;
    --text-mid:      #7fa8c4;
    --text-lo:       #364f66;
    --text-ghost:   #1e3045;
    --mono:          'IBM Plex Mono', monospace;
    --sans:          'IBM Plex Sans', sans-serif;
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg-base) !important; color: var(--text-hi) !important; font-family: var(--sans) !important; }
[data-testid="stSidebar"] { background: #07101a !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--text-mid) !important; }
.stButton > button { background: linear-gradient(135deg, #00c49a, #0891b2) !important; color: #030b12 !important; border: none !important; border-radius: 5px !important; font-family: var(--mono) !important; font-weight: 700 !important; font-size: 11px !important; letter-spacing: 2px !important; padding: 10px 28px !important; }
[data-testid="stDateInput"] input { background: var(--bg-deep) !important; border: 1px solid var(--border) !important; color: var(--text-hi) !important; border-radius: 5px !important; font-family: var(--mono) !important; color-scheme: dark; }
.sig-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 18px 20px; margin-bottom: 10px; }
.sig-card-blue { border-top: 2px solid var(--teal); }
.sig-card-amber { border-top: 2px solid var(--amber); }
.ticker-wrap { overflow: hidden; border-bottom: 1px solid var(--border); padding: 5px 0; }
.ticker-inner { display: flex; white-space: nowrap; animation: ticker 30s linear infinite; }
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
.ticker-text { color: var(--text-ghost); font-size: 9px; letter-spacing: 3px; font-family: var(--mono); padding-right: 60px; }
.conf-track { height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; margin: 4px 0; }
.conf-fill  { height: 100%; border-radius: 2px; }
.model-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 20px 22px; }
.label { color: var(--text-lo); font-size: 9px; letter-spacing: 2px; font-family: var(--mono); }
.mono { font-family: var(--mono); }
.pill { display: inline-block; background: var(--bg-deep); border: 1px solid var(--border-soft); border-radius: 3px; padding: 2px 8px; font-size: 9px; font-family: var(--mono); color: var(--text-mid); margin: 2px 3px 2px 0; }
.badge { display: inline-block; border-radius: 3px; padding: 2px 7px; font-size: 8px; font-weight: 700; letter-spacing: 2px; font-family: var(--mono); }
.badge-blue { background: rgba(0,212,170,.12); color: #00d4aa; }
.badge-amber { background: rgba(245,200,66,.12); color: #f5c842; }
</style>
"""
st.markdown(BLOOMBERG_CSS, unsafe_allow_html=True)

# ── [SECTIONS 1-11 REMAIN UNTOUCHED AS PER YOUR CODE] ──
class AppConfig:
    _inst: Optional[AppConfig] = None
    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._init()
        return cls._inst
    def _init(self):
        self.rsi_period = 14; self.sma_fast = 44; self.sma_slow = 200; self.vol_lookback = 5; self.atr_period = 14
        self.macd_fast = 12; self.macd_slow = 26; self.macd_signal = 9; self.fetch_workers = 12
        self.history_days = 450; self.blue_rsi_min = 65; self.blue_premium = 1.05
        self.rr_model_a = 1.0; self.rr_model_b = 2.0; self.mc_trials = 10_000; self.mc_trades = 15

cfg = AppConfig()

# [Placeholder for your classes: IndicatorEngine, ConfidenceEngine, SignalFactory, DataFetcher, monte_carlo, Nifty200Analyser, render_signal_card, etc.]
# I am assuming these classes exist exactly as you provided them in your prompt.

# ── [THE ADDED LOGIC: SECTION 12 START] ──

def main():
    # 1. SIDEBAR: DATE SELECTION ADDED HERE
    with st.sidebar:
        st.markdown("<div class='section-label' style='color:var(--teal)'>SYSTEM TERMINAL</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # USER REQUESTED FEATURE: DATE PICKER
        selected_date = st.date_input(
            "AUDIT DATE (T)", 
            datetime.now().date() - timedelta(days=1),
            help="The engine will calculate signals based on the close of this specific day."
        )
        
        st.markdown("---")
        trade_sim_count = st.slider("MC TRADES/MONTH", 5, 30, cfg.mc_trades)
        st.markdown("---")
        st.markdown(f"<div class='label'>ENGINE STATUS</div><div class='mono' style='color:var(--teal)'>STABLE-V3.1</div>", unsafe_allow_html=True)

    # 2. TICKER TAPE
    st.markdown(render_ticker_tape(), unsafe_allow_html=True)

    # 3. DASHBOARD HEADER
    st.markdown(f"""
        <div style="margin: 20px 0;">
            <div class="label" style="letter-spacing:5px;">INSTITUTIONAL ALPHA ENGINE</div>
            <h2 class="mono" style="margin:0; font-size:24px;">NIFTY 200 <span style="color:var(--teal)">SIGNAL AUDIT</span></h2>
            <div class="label" style="margin-top:5px; color:var(--sky)">ACTIVE PARAMETERS: RSI > {cfg.blue_rsi_min} | SMA {cfg.sma_fast}/{cfg.sma_slow} | TARGET DATE: {selected_date}</div>
        </div>
    """, unsafe_allow_html=True)

    # 4. EXECUTION BUTTON
    if st.button("RUN QUANTITATIVE SCAN", use_container_width=True):
        analyser = Nifty200Analyser()
        
        prog_bar = st.progress(0)
        status_txt = st.empty()
        
        # PASSING THE SELECTED DATE TO YOUR ANALYSER
        signals = analyser.run(selected_date, progress_bar=prog_bar, status_text=status_txt)
        
        prog_bar.empty()
        status_txt.empty()

        if not signals:
            st.error("NO SIGNALS GENERATED FOR THIS DATE REGIME.")
            return

        # 5. MONTE CARLO & PERFORMANCE CARDS
        jackpots = [s for s in signals if s.status == "JACKPOT"]
        tp1_hits = [s for s in signals if s.status == "TP1_HIT" or s.status == "JACKPOT"]
        
        win_rate_t1 = (len(tp1_hits) / len(signals)) * 100
        win_rate_t2 = (len(jackpots) / len(signals)) * 100
        
        prob_a = monte_carlo(win_rate_t1/100, cfg.rr_model_a, trades=trade_sim_count)
        prob_b = monte_carlo(win_rate_t2/100, cfg.rr_model_b, trades=trade_sim_count)

        st.markdown("<div class='section-label'>PROBABILISTIC MODELS (MONTHLY)</div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(render_model_card("MODEL ALPHA (1:1)", cfg.rr_model_a, round(win_rate_t1), prob_a, "#f5c842"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_model_card("MODEL JACKPOT (1:2)", cfg.rr_model_b, round(win_rate_t2), prob_b, "#00d4aa"), unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 6. RENDER THE GRID
        st.markdown("<div class='section-label'>ALPHA SIGNAL FEED</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, sig in enumerate(signals):
            with cols[idx % 3]:
                st.markdown(render_signal_card(sig), unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background:var(--bg-card); border:1px solid var(--border); padding:60px; text-align:center; border-radius:8px;">
                <div class="pulse mono" style="color:var(--text-lo); letter-spacing:10px;">AWAITING COMMAND</div>
            </div>
        """, unsafe_allow_html=True)

# ── [THE FINAL CALL] ──
if __name__ == "__main__":
    # Note: Ensure all your helper functions like render_ticker_tape(), render_model_card(), 
    # and monte_carlo() are defined above this main() function.
    main()
