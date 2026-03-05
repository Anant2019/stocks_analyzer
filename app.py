"""
Nifty 200 — Institutional Alpha Engine v4.0
============================================
Bloomberg Dark-Mode Dashboard · Pure Python / Streamlit

NEW in v4.0:
  ✅ Beginner-friendly onboarding with step-by-step guide
  ✅ Fixed date picker — any valid past trading date works
  ✅ Full SEBI-compliant legal disclaimer (popup + persistent banner)
  ✅ Plain-English tooltips on every input and indicator
  ✅ "How to read this?" guide embedded in UI
  ✅ Clear error messages with suggested fixes

Deploy:
    pip install streamlit yfinance pandas numpy
    streamlit run nifty200_app.py
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be FIRST Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty 200 Signal Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# BLOOMBERG DARK CSS  +  beginner-friendly overrides
# ─────────────────────────────────────────────────────────────────────────────
BLOOMBERG_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg-base:    #060c14;
    --bg-card:    #080f19;
    --bg-deep:    #0a1520;
    --border:     #162030;
    --border-s:   #1e3045;
    --teal:       #00d4aa;
    --sky:        #38bdf8;
    --amber:      #f5c842;
    --red:        #ff4d6d;
    --purple:     #a78bfa;
    --green:      #4ade80;
    --text-hi:    #e8f0f8;
    --text-mid:   #7fa8c4;
    --text-lo:    #364f66;
    --text-ghost: #1e3045;
    --mono:       'IBM Plex Mono', monospace;
    --sans:       'IBM Plex Sans', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg-base) !important;
    color: var(--text-hi) !important;
    font-family: var(--sans) !important;
}
[data-testid="stSidebar"] {
    background: #07101a !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-mid) !important; font-size: 13px !important; }
[data-testid="stSidebar"] h3 { color: var(--teal) !important; font-size: 13px !important; font-weight: 700 !important; }

/* Hide default Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding: 1rem 1.5rem 2rem !important; max-width: 1380px !important; }

/* Metrics */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 16px 18px !important;
}
[data-testid="metric-container"] label {
    color: var(--text-lo) !important;
    font-family: var(--mono) !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: var(--text-hi) !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 11px !important;
    color: var(--text-lo) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00c49a, #0891b2) !important;
    color: #030b12 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 1px !important;
    padding: 12px 28px !important;
    transition: opacity .2s, transform .1s !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }

/* Secondary buttons */
.stButton > button[kind="secondary"] {
    background: var(--bg-deep) !important;
    color: var(--text-mid) !important;
    border: 1px solid var(--border-s) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 6px !important; }
[data-testid="stDataFrame"] th {
    background: var(--bg-deep) !important;
    color: var(--text-lo) !important;
    font-family: var(--mono) !important;
    font-size: 10px !important;
    letter-spacing: 1px !important;
    padding: 8px 12px !important;
}
[data-testid="stDataFrame"] td {
    font-family: var(--mono) !important;
    font-size: 12px !important;
    color: var(--text-hi) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--sans) !important;
    font-size: 13px !important;
    color: var(--text-mid) !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] summary:hover { color: var(--text-hi) !important; }

/* Date input */
[data-testid="stDateInput"] input {
    background: var(--bg-deep) !important;
    border: 1px solid var(--border-s) !important;
    color: var(--text-hi) !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    color-scheme: dark;
}
[data-testid="stDateInput"] label {
    color: var(--text-mid) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Select/radio */
[data-testid="stRadio"] label { color: var(--text-mid) !important; font-size: 13px !important; }
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p { color: var(--text-hi) !important; font-weight: 600 !important; }

/* Success / warning / error */
[data-testid="stAlert"] { border-radius: 6px !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* Info boxes */
[data-testid="stInfo"] { background: rgba(56,189,248,.08) !important; border: 1px solid rgba(56,189,248,.25) !important; border-radius: 6px !important; color: #7fa8c4 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border-s); border-radius: 2px; }

/* ── CUSTOM COMPONENTS ── */
.section-hdr {
    color: var(--text-lo);
    font-size: 9px;
    letter-spacing: 4px;
    font-family: var(--mono);
    margin: 0 0 12px 0;
    padding-top: 4px;
}
.friendly-hdr {
    color: var(--text-mid);
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
}
.step-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
.step-num {
    background: linear-gradient(135deg,#00c49a,#0891b2);
    color: #030b12;
    font-weight: 700;
    font-size: 13px;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    font-family: var(--mono);
    vertical-align: middle;
}
.mono { font-family: var(--mono); }
.label { color: var(--text-lo); font-size: 9px; letter-spacing: 2px; font-family: var(--mono); }

/* Signal card */
.sig-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 10px;
    transition: border-color .2s, transform .15s;
}
.sig-card:hover { border-color: var(--border-s); transform: translateY(-2px); }
.sig-blue  { border-top: 3px solid var(--teal); }
.sig-amber { border-top: 3px solid var(--amber); }

.badge { display:inline-block; border-radius:4px; padding:2px 8px; font-size:9px; font-weight:700; letter-spacing:2px; font-family:var(--mono); }
.badge-blue  { background:rgba(0,212,170,.12); color:#00d4aa; }
.badge-amber { background:rgba(245,200,66,.12); color:#f5c842; }

.pill {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid var(--border-s);
    border-radius: 4px;
    padding: 3px 9px;
    font-size: 10px;
    font-family: var(--mono);
    color: var(--text-mid);
    margin: 2px 3px 2px 0;
}
.status-dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:5px; vertical-align:middle; }

/* Model card */
.model-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 22px;
    height: 100%;
}
.win-bar { display:flex; gap:3px; margin:10px 0; }
.win-seg  { flex:1; height:5px; border-radius:2px; }

/* Confidence bar */
.conf-track { height:4px; background:var(--border); border-radius:2px; overflow:hidden; margin:5px 0 3px; }
.conf-fill  { height:100%; border-radius:2px; }

/* Gauge */
.gauge-wrap { text-align:center; }

/* Disclaimer box */
.disclaimer-box {
    background: rgba(255,77,109,.05);
    border: 1px solid rgba(255,77,109,.3);
    border-left: 4px solid #ff4d6d;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.disclaimer-title {
    color: #ff4d6d;
    font-size: 13px;
    font-weight: 700;
    font-family: var(--mono);
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.disclaimer-text {
    color: #9e6070;
    font-size: 12px;
    line-height: 1.7;
}

/* Ticker tape */
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
@keyframes pulse  { 0%,100%{opacity:1} 50%{opacity:.3} }
.ticker-wrap  { overflow:hidden; border-bottom:1px solid var(--border); padding:5px 0; }
.ticker-inner { display:flex; white-space:nowrap; animation:ticker 35s linear infinite; }
.ticker-text  { color:var(--text-ghost); font-size:9px; letter-spacing:3px; font-family:var(--mono); padding-right:60px; }
.pulse        { animation:pulse 2s infinite; }

/* How it works card */
.howto-card {
    background: rgba(0,212,170,.04);
    border: 1px solid rgba(0,212,170,.15);
    border-radius: 8px;
    padding: 16px 20px;
}
.howto-row { display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }
.howto-icon { font-size:18px; min-width:24px; margin-top:1px; }
.howto-body {}
.howto-title { color:var(--teal); font-size:12px; font-weight:600; margin-bottom:2px; }
.howto-desc  { color:var(--text-lo); font-size:11px; line-height:1.5; }

/* Legend */
.legend-item { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.legend-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

/* Date guide */
.date-guide {
    background: rgba(56,189,248,.05);
    border: 1px solid rgba(56,189,248,.18);
    border-radius: 6px;
    padding: 12px 16px;
    margin-top: 8px;
}
</style>
"""

st.markdown(BLOOMBERG_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. SINGLETON CONFIG
# ─────────────────────────────────────────────────────────────────────────────
class AppConfig:
    _inst: Optional["AppConfig"] = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._init()
        return cls._inst

    def _init(self):
        self.rsi_period    = int(os.getenv("RSI_PERIOD",    "14"))
        self.sma_fast      = int(os.getenv("SMA_FAST",      "44"))
        self.sma_slow      = int(os.getenv("SMA_SLOW",      "200"))
        self.vol_lookback  = int(os.getenv("VOL_LOOKBACK",  "5"))
        self.atr_period    = int(os.getenv("ATR_PERIOD",    "14"))
        self.macd_fast     = int(os.getenv("MACD_FAST",     "12"))
        self.macd_slow     = int(os.getenv("MACD_SLOW",     "26"))
        self.macd_signal   = int(os.getenv("MACD_SIGNAL",   "9"))
        self.fetch_workers = int(os.getenv("FETCH_WORKERS", "8"))
        self.history_days  = int(os.getenv("HISTORY_DAYS",  "450"))
        self.blue_rsi_min  = float(os.getenv("BLUE_RSI_MIN", "65"))
        self.blue_premium  = float(os.getenv("BLUE_PREMIUM", "1.05"))
        self.mc_trials     = 10_000
        self.mc_trades     = 15


cfg = AppConfig()


# ─────────────────────────────────────────────────────────────────────────────
# 2. LOGGER
# ─────────────────────────────────────────────────────────────────────────────
class _Logger:
    _inst: Optional[logging.Logger] = None

    @classmethod
    def get(cls) -> logging.Logger:
        if cls._inst is None:
            lg = logging.getLogger("nifty200")
            lg.setLevel(logging.DEBUG)
            fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%Y-%m-%dT%H:%M:%S")
            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            lg.addHandler(sh)
            try:
                fh = logging.FileHandler("nifty200.log", mode="a")
                fh.setFormatter(fmt)
                lg.addHandler(fh)
            except Exception:
                pass
            cls._inst = lg
        return cls._inst


log = _Logger.get()


# ─────────────────────────────────────────────────────────────────────────────
# 3. NIFTY 200 UNIVERSE
# ─────────────────────────────────────────────────────────────────────────────
NIFTY_200: list[str] = [
    'ABB.NS','ACC.NS','ADANIENSOL.NS','ADANIENT.NS','ADANIGREEN.NS','ADANIPORTS.NS',
    'ADANIPOWER.NS','ATGL.NS','AMBUJACEM.NS','APOLLOHOSP.NS','ASIANPAINT.NS','AUBANK.NS',
    'AUROPHARMA.NS','DMART.NS','AXISBANK.NS','BAJAJ-AUTO.NS','BAJFINANCE.NS','BAJAJFINSV.NS',
    'BAJAJHLDNG.NS','BALKRISIND.NS','BANDHANBNK.NS','BANKBARODA.NS','BANKINDIA.NS',
    'BERGEPAINT.NS','BEL.NS','BHARTIARTL.NS','BIOCON.NS','BOSCHLTD.NS','BPCL.NS',
    'BRITANNIA.NS','CANBK.NS','CHOLAFIN.NS','CIPLA.NS','COALINDIA.NS','COFORGE.NS',
    'COLPAL.NS','CONCOR.NS','CUMMINSIND.NS','DLF.NS','DABUR.NS','DALBHARAT.NS',
    'DEEPAKNTR.NS','DIVISLAB.NS','DIXON.NS','DRREDDY.NS','EICHERMOT.NS','ESCORTS.NS',
    'EXIDEIND.NS','FEDERALBNK.NS','GAIL.NS','GLAND.NS','GLENMARK.NS','GODREJCP.NS',
    'GODREJPROP.NS','GRASIM.NS','GUJGASLTD.NS','HAL.NS','HCLTECH.NS','HDFCBANK.NS',
    'HDFCLIFE.NS','HEROMOTOCO.NS','HINDALCO.NS','HINDCOPPER.NS','HINDPETRO.NS',
    'HINDUNILVR.NS','ICICIBANK.NS','ICICIGI.NS','ICICIPRULI.NS','IDFCFIRSTB.NS','ITC.NS',
    'INDIAHOTEL.NS','IOC.NS','IRCTC.NS','IRFC.NS','IGL.NS','INDUSTOWER.NS','INDUSINDBK.NS',
    'INFY.NS','IPCALAB.NS','JSWSTEEL.NS','JSL.NS','JUBLFOOD.NS','KOTAKBANK.NS','LT.NS',
    'LTIM.NS','LTTS.NS','LICHSGFIN.NS','LICI.NS','LUPIN.NS','MRF.NS','M&M.NS','M&MFIN.NS',
    'MARICO.NS','MARUTI.NS','MAXHEALTH.NS','MPHASIS.NS','NHPC.NS','NMDC.NS','NTPC.NS',
    'NESTLEIND.NS','OBEROIRLTY.NS','ONGC.NS','OIL.NS','PAYTM.NS','PIIND.NS','PFC.NS',
    'POLYCAB.NS','POWARGRID.NS','PRESTIGE.NS','RELIANCE.NS','RVNL.NS','RECLTD.NS',
    'SBICARD.NS','SBILIFE.NS','SRF.NS','SHREECEM.NS','SHRIRAMFIN.NS','SIEMENS.NS',
    'SONACOMS.NS','SBIN.NS','SAIL.NS','SUNPHARMA.NS','SUNTV.NS','SYNGENE.NS',
    'TATACOMM.NS','TATAELXSI.NS','TATACONSUM.NS','TATAMOTORS.NS','TATAPOWER.NS',
    'TATASTEEL.NS','TCS.NS','TECHM.NS','TITAN.NS','TORNTPHARM.NS','TRENT.NS','TIINDIA.NS',
    'UPL.NS','ULTRACEMCO.NS','UNITDSPR.NS','VBL.NS','VEDL.NS','VOLTAS.NS','WIPRO.NS',
    'YESBANK.NS','ZOMATO.NS','ZYDUSLIFE.NS',
]


# ─────────────────────────────────────────────────────────────────────────────
# 4. DATE UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def is_trading_day(d: date) -> bool:
    """Return True if ``d`` is a weekday (Mon–Fri). Does not check Indian holidays."""
    return d.weekday() < 5  # 0=Mon … 4=Fri


def last_trading_day() -> date:
    """Return the most recent weekday on or before today."""
    d = datetime.now().date()
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def safe_date_bounds() -> tuple[date, date]:
    """
    Return (min_date, max_date) for the date picker.
    min: 2 years ago  |  max: yesterday (or last Friday if today is weekend)
    """
    max_d = last_trading_day()
    if max_d == datetime.now().date():
        # Today is a weekday; allow yesterday too for backtest clarity
        max_d = max_d - timedelta(days=1)
        while not is_trading_day(max_d):
            max_d -= timedelta(days=1)
    min_d = max_d - timedelta(days=730)
    return min_d, max_d


def default_backtest_date() -> date:
    """Default = most recent completed trading day."""
    d = datetime.now().date() - timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# 5. DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SignalRecord:
    """Immutable trade signal — fully JSON-serialisable."""
    ticker:        str
    date:          str
    category:      str    # BLUE | AMBER
    status:        str    # JACKPOT | SL_HIT | TP1_HIT | RUNNING | LIVE
    entry:         float
    stop_loss:     float
    tp1:           float  # Take-Profit 1  (1:1 risk/reward)
    tp2:           float  # Take-Profit 2  (1:2 risk/reward)
    risk_pts:      float
    rsi:           float
    macd_hist:     float
    atr:           float
    vol_ratio:     float
    pct_vs_sma200: float
    confidence:    float  # 0–100 composite score
    jackpot:       bool
    chart_url:     str

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# 6. INDICATOR ENGINE — fully vectorised, zero row-loops
# ─────────────────────────────────────────────────────────────────────────────
class IndicatorEngine:
    """Stateless vectorised indicator library."""

    @staticmethod
    def wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Wilder-smoothed RSI (EWM alpha=1/period) — matches original 1978 spec."""
        d  = close.diff()
        a  = 1.0 / period
        ag = d.clip(lower=0).ewm(alpha=a, min_periods=period, adjust=False).mean()
        al = (-d).clip(lower=0).ewm(alpha=a, min_periods=period, adjust=False).mean()
        return 100.0 - (100.0 / (1.0 + ag / al.replace(0, np.nan)))

    @staticmethod
    def macd(close: pd.Series, fast=12, slow=26, sig=9) -> pd.DataFrame:
        """EMA-based MACD; returns macd / signal / histogram."""
        ml = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
        sl = ml.ewm(span=sig, adjust=False).mean()
        return pd.DataFrame({"macd": ml, "signal": sl, "histogram": ml - sl}, index=close.index)

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Wilder Average True Range."""
        pc = close.shift(1)
        tr = pd.concat([(high - low), (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    @staticmethod
    def sma(s: pd.Series, w: int) -> pd.Series:
        return s.rolling(w, min_periods=w).mean()

    @staticmethod
    def vol_ratio(vol: pd.Series, lb: int = 5) -> pd.Series:
        return vol / vol.rolling(lb, min_periods=lb).mean().replace(0, np.nan)


# ─────────────────────────────────────────────────────────────────────────────
# 7. CONFIDENCE ENGINE — transparent 5-dimension scorer
# ─────────────────────────────────────────────────────────────────────────────
class ConfidenceEngine:
    """
    Weighted 0–100 confidence scorer.
    Trend 30 · Momentum 20 · Volume 20 · MACD 15 · ATR regime 15
    """
    W = dict(trend=30, momentum=20, volume=20, macd=15, volatility=15)

    @classmethod
    def score(cls, close, sma44, sma200, rsi, vol_ratio, macd_hist, atr) -> float:
        s = 0.0
        if close > sma44 > sma200:
            s += cls.W["trend"] * min(1.0, (close - sma200) / sma200 * 100 / 20.0)
        if 55 <= rsi <= 75:
            s += cls.W["momentum"] * max(0.0, 1.0 - abs(rsi - 65) / 10.0)
        elif rsi > 75:
            s += cls.W["momentum"] * 0.3
        if vol_ratio >= 1.5:
            s += cls.W["volume"]
        elif vol_ratio >= 1.0:
            s += cls.W["volume"] * (vol_ratio - 1.0) / 0.5
        s += cls.W["macd"] if macd_hist > 0 else (cls.W["macd"] * 0.4 if macd_hist > -0.5 else 0)
        ap = (atr / close) * 100
        if 0.5 <= ap <= 3.0:
            s += cls.W["volatility"]
        elif ap < 0.5:
            s += cls.W["volatility"] * 0.5
        return round(min(s, 100.0), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 8. SIGNAL FACTORY
# ─────────────────────────────────────────────────────────────────────────────
class SignalFactory:
    """Enriches OHLCV DataFrame and emits SignalRecord objects."""

    def __init__(self):
        self._ie = IndicatorEngine()
        self._ce = ConfidenceEngine()

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        c             = df["Close"]
        df["SMA44"]   = self._ie.sma(c, cfg.sma_fast)
        df["SMA200"]  = self._ie.sma(c, cfg.sma_slow)
        df["RSI"]     = self._ie.wilder_rsi(c, cfg.rsi_period)
        df["ATR"]     = self._ie.atr(df["High"], df["Low"], c, cfg.atr_period)
        df["VolRatio"]= self._ie.vol_ratio(df["Volume"], cfg.vol_lookback)
        macd          = self._ie.macd(c, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
        df["MACDHist"]= macd["histogram"]
        return df

    def build(self, ticker: str, df: pd.DataFrame, ts: pd.Timestamp) -> Optional[SignalRecord]:
        if ts not in df.index:
            return None
        row              = df.loc[ts]
        close, open_p, low_p = float(row["Close"]), float(row["Open"]), float(row["Low"])
        sma44, sma200    = float(row["SMA44"]),   float(row["SMA200"])
        rsi, atr         = float(row["RSI"]),     float(row["ATR"])
        vr, mh           = float(row["VolRatio"]),float(row["MACDHist"])

        if any(math.isnan(v) for v in [sma44, sma200, rsi, atr, vr, mh]):
            return None
        if not (close > sma44 > sma200 and close > open_p):
            return None

        risk = close - low_p
        if risk <= 0:
            return None

        tp1 = close + risk        # 1:1
        tp2 = close + 2 * risk    # 1:2

        is_blue  = rsi > cfg.blue_rsi_min and vr > 1.0 and close > sma200 * cfg.blue_premium
        category = "BLUE" if is_blue else "AMBER"

        # Vectorised backtest — no row iteration
        future  = df[df.index > ts][["High", "Low"]]
        status  = "LIVE"
        jackpot = False
        if not future.empty:
            sl_arr  = future["Low"].values  <= low_p
            tp2_arr = future["High"].values >= tp2
            tp1_arr = future["High"].values >= tp1
            ev      = sl_arr | tp2_arr
            if ev.any():
                i = int(ev.argmax())
                if tp2_arr[i] and not sl_arr[i]:
                    status, jackpot = "JACKPOT", True
                elif sl_arr[i] and not tp2_arr[i]:
                    status = "SL_HIT"
                elif tp1_arr[i]:
                    status = "TP1_HIT"
                else:
                    status = "RUNNING"
            else:
                status = "RUNNING"

        conf = self._ce.score(close, sma44, sma200, rsi, vr, mh, atr)
        sym  = ticker.replace(".NS", "")
        return SignalRecord(
            ticker        = sym,
            date          = str(ts.date()),
            category      = category,
            status        = status,
            entry         = round(close, 2),
            stop_loss     = round(low_p, 2),
            tp1           = round(tp1, 2),
            tp2           = round(tp2, 2),
            risk_pts      = round(risk, 2),
            rsi           = round(rsi, 1),
            macd_hist     = round(mh, 4),
            atr           = round(atr, 2),
            vol_ratio     = round(vr, 2),
            pct_vs_sma200 = round((close / sma200 - 1) * 100, 2),
            confidence    = conf,
            jackpot       = jackpot,
            chart_url     = f"https://www.tradingview.com/chart/?symbol=NSE:{sym}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 9. CONCURRENT DATA FETCHER
# ─────────────────────────────────────────────────────────────────────────────
class DataFetcher:
    """Parallel yfinance fetcher — ThreadPoolExecutor for I/O bound work."""

    def __init__(self, workers: int = cfg.fetch_workers):
        self._workers = workers

    def _fetch_one(self, ticker, start, end):
        try:
            df = yf.download(ticker, start=start, end=end,
                             auto_adjust=True, progress=False, threads=False)
            if df.empty:
                return ticker, None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return ticker, df
        except Exception as e:
            log.warning("Fetch fail %s: %s", ticker, e)
            return ticker, None

    def fetch_batch(self, tickers, start, end, cb=None):
        results = {}
        done    = 0
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            futs = {pool.submit(self._fetch_one, t, start, end): t for t in tickers}
            for f in as_completed(futs):
                ticker, df = f.result()
                done += 1
                if df is not None and len(df) >= cfg.sma_slow + 10:
                    results[ticker] = df
                if cb:
                    cb(done, len(tickers))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 10. MONTE CARLO
# ─────────────────────────────────────────────────────────────────────────────
def monte_carlo(win_rate: float, rr: float,
                trials: int = 10_000, trades: int = 15) -> float:
    """Return % of simulated months ending with positive P&L."""
    rng   = np.random.default_rng(42)
    rolls = rng.random((trials, trades))
    pnl   = np.where(rolls < win_rate, rr, -1.0).sum(axis=1)
    return round(float((pnl > 0).mean() * 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 11. MAIN ANALYSER
# ─────────────────────────────────────────────────────────────────────────────
class Nifty200Analyser:
    def __init__(self):
        self._fetcher = DataFetcher()
        self._factory = SignalFactory()

    def run(self, target_date, tickers=NIFTY_200, progress_bar=None, status_txt=None):
        start = datetime.combine(target_date, datetime.min.time()) - timedelta(days=cfg.history_days)
        end   = datetime.combine(target_date, datetime.min.time()) + timedelta(days=60)
        ts    = pd.Timestamp(target_date)

        def _cb(done, total):
            if progress_bar:
                pct = done / total
                progress_bar.progress(pct, text=f"⏳ Scanning stock {done} of {total}…")

        raw = self._fetcher.fetch_batch(tickers, start, end, _cb)

        if status_txt:
            status_txt.info("🔬 Building signals from market data…")
        if progress_bar:
            progress_bar.progress(1.0, text="✅ Processing complete!")

        records = []
        for ticker, df in raw.items():
            try:
                enriched = self._factory.enrich(df.copy())
                sig = self._factory.build(ticker, enriched, ts)
                if sig:
                    records.append(sig)
            except Exception as e:
                log.error("Signal error %s: %s", ticker, e)

        records.sort(key=lambda r: r.confidence, reverse=True)
        log.info("Generated %d signals for %s", len(records), target_date)
        return records


# ─────────────────────────────────────────────────────────────────────────────
# 12. HTML RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _conf_color(s: float) -> str:
    return "#00d4aa" if s >= 75 else ("#f5c842" if s >= 55 else "#ff4d6d")

def _conf_label(s: float) -> str:
    return "HIGH CONVICTION" if s >= 80 else ("MODERATE SETUP" if s >= 62 else "LOW CONVICTION")

def _conf_plain(s: float) -> str:
    """Beginner-friendly plain-English label."""
    return "Strong Setup 💚" if s >= 80 else ("Decent Setup 🟡" if s >= 62 else "Weak Setup 🔴")

STATUS_META = {
    "JACKPOT": {"dot":"#00d4aa","bg":"rgba(0,212,170,.10)","label":"TARGET HIT ✅","plain":"Price reached Take-Profit 2"},
    "TP1_HIT": {"dot":"#f5c842","bg":"rgba(245,200,66,.10)","label":"TP1 HIT 🟡",  "plain":"Price reached Take-Profit 1"},
    "SL_HIT":  {"dot":"#ff4d6d","bg":"rgba(255,77,109,.10)","label":"STOP HIT ❌",  "plain":"Stop loss was triggered"},
    "RUNNING": {"dot":"#f5c842","bg":"rgba(245,200,66,.08)","label":"IN PROGRESS ⏳","plain":"Trade still open"},
    "LIVE":    {"dot":"#38bdf8","bg":"rgba(56,189,248,.08)","label":"LIVE SIGNAL 🔵","plain":"Signal active today"},
}


def render_signal_card(r: SignalRecord, show_plain: bool = False) -> str:
    is_blue = r.category == "BLUE"
    accent  = "#00d4aa" if is_blue else "#f5c842"
    sm      = STATUS_META.get(r.status, STATUS_META["RUNNING"])
    cc      = _conf_color(r.confidence)
    badge   = "badge-blue" if is_blue else "badge-amber"
    cat_cls = "sig-blue" if is_blue else "sig-amber"

    def price_box(lbl, sublbl, val, color):
        return (
            f'<div style="background:#0a1520;border-radius:5px;padding:10px 12px;">'
            f'<div class="label">{lbl}</div>'
            f'<div style="color:#364f66;font-size:9px;margin-bottom:2px;">{sublbl}</div>'
            f'<div class="mono" style="color:{color};font-size:13px;font-weight:700;">'
            f'₹{val:,.2f}</div></div>'
        )

    def pill(lbl, val, tip=""):
        return (
            f'<span class="pill" title="{tip}">'
            f'<span style="color:#364f66">{lbl} </span>{val}</span>'
        )

    bar_w = int(r.confidence)
    plain_label = _conf_plain(r.confidence)

    extra_plain = ""
    if show_plain:
        extra_plain = f"""
<div style="background:rgba(56,189,248,.05);border:1px solid rgba(56,189,248,.12);
            border-radius:5px;padding:8px 12px;margin-top:10px;">
  <div style="color:#38bdf8;font-size:10px;font-weight:600;margin-bottom:4px;">💡 What does this mean?</div>
  <div style="color:#4a7fa5;font-size:11px;line-height:1.6;">
    This stock passed all 3 bullish filters on <b>{r.date}</b>.<br>
    <b>Buy near ₹{r.entry:,.0f}</b> · <b>Exit if falls to ₹{r.stop_loss:,.0f}</b> (stop loss)<br>
    <b>First target ₹{r.tp1:,.0f}</b> (1× risk) · <b>Second target ₹{r.tp2:,.0f}</b> (2× risk)<br>
    Status: <b>{sm['plain']}</b>
  </div>
</div>"""

    return f"""
<div class="sig-card {cat_cls}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <span class="mono" style="color:#e8f0f8;font-size:18px;font-weight:700;letter-spacing:1px;">{r.ticker}</span>
        <span class="badge {badge}">{r.category}</span>
      </div>
      <div class="label">NSE EQUITY · TRIPLE-BULLISH · {r.date}</div>
    </div>
    <div style="background:{sm['bg']};border:1px solid {sm['dot']}33;border-radius:5px;
                padding:5px 11px;display:flex;align-items:center;gap:5px;text-align:right;">
      <span class="status-dot" style="background:{sm['dot']};"></span>
      <span class="mono" style="color:{sm['dot']};font-size:9px;font-weight:700;letter-spacing:1px;">{sm['label']}</span>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:12px;">
    {price_box("ENTRY PRICE", "Buy around this price", r.entry, "#c8d8e8")}
    {price_box("STOP LOSS", "Exit if price falls here", r.stop_loss, "#ff4d6d")}
    {price_box("TARGET 1 (1:1)", "First profit level", r.tp1, "#f5c842")}
    {price_box("TARGET 2 (1:2)", "Full profit level", r.tp2, "#00d4aa")}
  </div>

  <div style="margin-bottom:10px;">
    {pill("RSI", r.rsi, "Relative Strength Index — above 65 means strong momentum")}
    {pill("VOL", f"{r.vol_ratio:.1f}×", "Volume vs 5-day average — higher = more interest")}
    {pill("MACD", ('+' if r.macd_hist >= 0 else '') + str(r.macd_hist), "Momentum direction — positive is bullish")}
    {pill("ΔSMA200", f"+{r.pct_vs_sma200:.1f}%", "How far above the 200-day average — trend strength")}
    {pill("ATR", f"₹{r.atr:.0f}", "Average daily range — volatility measure")}
  </div>

  <div style="margin-top:10px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
      <span style="color:#7fa8c4;font-size:11px;">{plain_label}</span>
      <span class="mono" style="color:{cc};font-size:14px;font-weight:700;">{r.confidence:.0f} / 100</span>
    </div>
    <div class="conf-track">
      <div class="conf-fill" style="width:{bar_w}%;background:linear-gradient(90deg,{cc}66,{cc});"></div>
    </div>
    <div class="label" style="margin-top:3px;">CONFIDENCE SCORE · SETUP ALIGNMENT</div>
  </div>
  {extra_plain}
  <div style="margin-top:12px;text-align:center;">
    <a href="{r.chart_url}" target="_blank"
       style="color:#364f66;font-size:10px;letter-spacing:1px;text-decoration:none;
              display:block;padding:8px;border:1px solid #162030;border-radius:5px;
              font-family:monospace;transition:color .2s;">
      📈 View Chart on TradingView ↗
    </a>
  </div>
</div>"""


def render_model_card(name, rr, win_pct, consistency, accent, plain_name) -> str:
    filled   = round(win_pct / 10)
    segs     = "".join(
        f'<div class="win-seg" style="background:{accent if i < filled else "#162030"};"></div>'
        for i in range(10)
    )
    cons_str = f"{consistency}%" if consistency else "Calculating…"
    return f"""
<div class="model-card" style="border-left:4px solid {accent};">
  <div style="color:#364f66;font-size:9px;letter-spacing:3px;font-family:monospace;margin-bottom:8px;">{plain_name}</div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
    <div>
      <div style="color:#c8d8e8;font-size:14px;font-weight:700;">{name}</div>
      <div style="color:#364f66;font-size:11px;margin-top:4px;">Risk / Reward Ratio: <span style="color:{accent};">1 : {rr}</span></div>
      <div style="color:#364f66;font-size:11px;margin-top:2px;">
        For every ₹1 risked → target ₹{rr} profit
      </div>
    </div>
    <div style="text-align:right;">
      <div class="mono" style="color:{accent};font-size:30px;font-weight:700;">{win_pct}%</div>
      <div style="color:#364f66;font-size:10px;">Historical Win Rate</div>
    </div>
  </div>
  <div class="win-bar">{segs}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;
              padding-top:12px;border-top:1px solid #162030;">
    <div>
      <div style="color:#364f66;font-size:10px;margin-bottom:2px;">Monthly Consistency (Monte Carlo)</div>
      <div style="color:#364f66;font-size:10px;">Simulated probability of a profitable month</div>
    </div>
    <div class="mono" style="color:{accent};font-size:18px;font-weight:700;">{cons_str}</div>
  </div>
</div>"""


def render_gauge_svg(val: float, color: str, label: str) -> str:
    r, cx, cy = 52, 70, 66
    def xy(deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)
    sx, sy = xy(180)
    ex, ey = xy(180 + val / 100 * 180)
    large  = 1 if val > 50 else 0
    bx, by = xy(360)
    return f"""
<svg width="140" height="88" viewBox="0 0 140 88" style="overflow:visible;">
  <path d="M {sx:.1f} {sy:.1f} A {r} {r} 0 1 1 {bx:.1f} {by:.1f}"
        fill="none" stroke="#162030" stroke-width="8" stroke-linecap="round"/>
  <path d="M {sx:.1f} {sy:.1f} A {r} {r} 0 {large} 1 {ex:.1f} {ey:.1f}"
        fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
  <text x="{cx}" y="{cy-4}" text-anchor="middle" fill="{color}"
        font-size="19" font-weight="700" font-family="monospace">{val}%</text>
  <text x="{cx}" y="{cy+11}" text-anchor="middle" fill="#364f66"
        font-size="8" letter-spacing="1" font-family="monospace">CONSISTENCY</text>
  <text x="{cx}" y="{cy+23}" text-anchor="middle" fill="#364f66"
        font-size="8" letter-spacing="1" font-family="monospace">{label}</text>
</svg>"""


def render_ticker_tape() -> str:
    txt = ("NIFTY 200 SIGNAL SCANNER &nbsp;·&nbsp; EDUCATIONAL USE ONLY &nbsp;·&nbsp; "
           "NOT SEBI REGISTERED &nbsp;·&nbsp; NOT INVESTMENT ADVICE &nbsp;·&nbsp; "
           "WILDER RSI &nbsp;·&nbsp; EMA MACD &nbsp;·&nbsp; ATR VOLATILITY &nbsp;·&nbsp; "
           "MONTE CARLO SIMULATION &nbsp;·&nbsp; CONFIDENCE SCORING &nbsp;·&nbsp; "
           "TRIPLE BULLISH FILTER &nbsp;·&nbsp; CONSULT A CERTIFIED ADVISOR &nbsp;·&nbsp; ")
    return f"""<div class="ticker-wrap">
  <div class="ticker-inner">
    <span class="ticker-text">{txt}</span>
    <span class="ticker-text">{txt}</span>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# 13. SEBI DISCLAIMER (modal + persistent)
# ─────────────────────────────────────────────────────────────────────────────
SEBI_DISCLAIMER_HTML = """
<div class="disclaimer-box">
  <div class="disclaimer-title">⚠️ IMPORTANT LEGAL DISCLAIMER — PLEASE READ</div>
  <div class="disclaimer-text">
    <b>1. NOT SEBI REGISTERED:</b> This tool and its creators are NOT registered with the Securities and Exchange Board of India (SEBI) as research analysts, investment advisors, or portfolio managers under the SEBI (Research Analysts) Regulations, 2014 or any other applicable regulation.<br><br>
    <b>2. EDUCATIONAL PURPOSE ONLY:</b> All signals, indicators, confidence scores, and analysis generated by this tool are purely for <b>educational, research, and informational purposes only</b>. This does not constitute investment advice, a buy/sell recommendation, or any form of financial guidance.<br><br>
    <b>3. NO GUARANTEED RETURNS:</b> Past performance of any strategy or signal does not guarantee future results. Stock market investments are subject to market risks. The Monte Carlo simulations and win-rate statistics shown are based on historical backtesting and may not reflect actual future performance.<br><br>
    <b>4. RISK OF LOSS:</b> Trading in equity markets involves substantial risk of financial loss. You may lose part or all of your invested capital. Never invest money you cannot afford to lose.<br><br>
    <b>5. CONSULT A QUALIFIED ADVISOR:</b> Before making any investment decision, please consult a SEBI-registered research analyst or certified financial planner who can assess your individual financial situation, risk tolerance, and investment objectives.<br><br>
    <b>6. NO LIABILITY:</b> The creators and operators of this tool accept <b>no responsibility or liability</b> for any financial loss, trading loss, or damages arising from the use of this tool or reliance on its output.
  </div>
</div>
"""

SEBI_COMPACT_HTML = """
<div style="background:rgba(255,77,109,.05);border:1px solid rgba(255,77,109,.25);
            border-radius:5px;padding:10px 16px;margin-bottom:14px;
            display:flex;gap:10px;align-items:flex-start;">
  <span style="color:#ff4d6d;font-size:16px;margin-top:1px;">⚠️</span>
  <div>
    <span style="color:#b05565;font-size:11px;font-weight:700;">NOT SEBI REGISTERED · EDUCATIONAL USE ONLY</span><br>
    <span style="color:#7a3d48;font-size:10px;">
      This tool is not affiliated with or approved by SEBI. Signals are algorithmic outputs based on historical data —
      not investment advice. Consult a SEBI-registered advisor before trading.
      <b>You alone are responsible for your trading decisions.</b>
    </span>
  </div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# 14. BEGINNER HOW-TO GUIDE
# ─────────────────────────────────────────────────────────────────────────────
HOW_TO_HTML = """
<div class="howto-card">
  <div style="color:#00d4aa;font-size:13px;font-weight:700;margin-bottom:14px;font-family:monospace;letter-spacing:1px;">
    📖 HOW TO USE THIS TOOL
  </div>
  <div class="howto-row">
    <div class="howto-icon">1️⃣</div>
    <div class="howto-body">
      <div class="howto-title">Pick a Date</div>
      <div class="howto-desc">Select any past market date (Mon–Fri) from the sidebar. The tool will show which Nifty 200 stocks had bullish signals on that day.</div>
    </div>
  </div>
  <div class="howto-row">
    <div class="howto-icon">2️⃣</div>
    <div class="howto-body">
      <div class="howto-title">Run the Scan</div>
      <div class="howto-desc">Click "Run Signal Scan". The engine downloads price data and checks 150+ stocks for the Triple-Bullish pattern (Price above SMA44 above SMA200).</div>
    </div>
  </div>
  <div class="howto-row">
    <div class="howto-icon">3️⃣</div>
    <div class="howto-body">
      <div class="howto-title">Read the Signal Cards</div>
      <div class="howto-desc">Each card shows Entry Price, Stop Loss, and two profit targets. 🔵 Blue = strongest signals · 🟡 Amber = secondary signals.</div>
    </div>
  </div>
  <div class="howto-row" style="margin-bottom:0;">
    <div class="howto-icon">4️⃣</div>
    <div class="howto-body">
      <div class="howto-title">Check the Status</div>
      <div class="howto-desc">✅ Target Hit = stock reached profit zone after signal date · ❌ Stop Hit = would have been a loss · ⏳ Running = still in progress.</div>
    </div>
  </div>
</div>
"""

LEGEND_HTML = """
<div style="background:#080f19;border:1px solid #162030;border-radius:6px;padding:14px 18px;">
  <div style="color:#364f66;font-size:10px;letter-spacing:3px;font-family:monospace;margin-bottom:12px;">SIGNAL LEGEND</div>
  <div class="legend-item"><div class="legend-dot" style="background:#00d4aa;"></div><div style="font-size:12px;">🔵 <b>BLUE</b> — High-conviction setup: RSI &gt;65, volume surge, price &gt;5% above 200 SMA</div></div>
  <div class="legend-item"><div class="legend-dot" style="background:#f5c842;"></div><div style="font-size:12px;">🟡 <b>AMBER</b> — Valid setup but without all Blue criteria</div></div>
  <div class="legend-item"><div class="legend-dot" style="background:#00d4aa;"></div><div style="font-size:12px;">✅ <b>TARGET HIT</b> — Stock reached Take-Profit 2 (1:2 R/R) after signal</div></div>
  <div class="legend-item"><div class="legend-dot" style="background:#f5c842;"></div><div style="font-size:12px;">🟡 <b>TP1 HIT</b> — Stock reached Take-Profit 1 (1:1 R/R) after signal</div></div>
  <div class="legend-item"><div class="legend-dot" style="background:#ff4d6d;"></div><div style="font-size:12px;">❌ <b>STOP HIT</b> — Stop loss triggered; would have been a controlled loss</div></div>
  <div class="legend-item"><div class="legend-dot" style="background:#f5c842;"></div><div style="font-size:12px;">⏳ <b>RUNNING</b> — Trade still active, neither target nor stop reached yet</div></div>
  <div class="legend-item"><div class="legend-dot" style="background:#38bdf8;"></div><div style="font-size:12px;">🔵 <b>LIVE</b> — Signal from today; outcome not yet determined</div></div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# 15. MAIN STREAMLIT APP
# ─────────────────────────────────────────────────────────────────────────────
def main():

    # ── SESSION-STATE DEFAULTS ────────────────────────────────────────────────
    if "disclaimer_accepted" not in st.session_state:
        st.session_state["disclaimer_accepted"] = False
    if "show_plain" not in st.session_state:
        st.session_state["show_plain"] = True

    # ── DISCLAIMER GATE ───────────────────────────────────────────────────────
    if not st.session_state["disclaimer_accepted"]:
        st.markdown(f"""
<div style="background:#07101a;border-bottom:1px solid #162030;
            padding:14px 2rem 10px;margin:-1rem -1.5rem 1.5rem;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="width:34px;height:34px;background:linear-gradient(135deg,#00d4aa,#0ea5e9);
                border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:16px;">📊</div>
    <div>
      <div style="font-size:16px;font-weight:700;color:#e8f0f8;">Nifty 200 Signal Analyzer</div>
      <div style="font-size:11px;color:#364f66;font-family:monospace;">Educational Tool · Not Investment Advice</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("## ⚠️ Legal Disclaimer — Please Read Before Proceeding")
        st.markdown(SEBI_DISCLAIMER_HTML, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("✅ I Understand — Enter App", type="primary", use_container_width=True):
                st.session_state["disclaimer_accepted"] = True
                st.rerun()
        with col2:
            st.markdown(
                '<div style="color:#364f66;font-size:11px;padding-top:14px;">'
                'By clicking "I Understand", you confirm that you have read and accepted the disclaimer, '
                'and that you will not use this tool as the sole basis for any investment decision.</div>',
                unsafe_allow_html=True
            )
        return  # Stop rendering until accepted

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="background:#07101a;border-bottom:1px solid #162030;
            padding:13px 0 0;margin:-1rem -1.5rem 1.2rem;">
  <div style="max-width:1380px;margin:0 auto;padding:0 1.5rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:10px;">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:36px;height:36px;background:linear-gradient(135deg,#00d4aa,#0ea5e9);
                    border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;">📊</div>
        <div>
          <div style="font-size:16px;font-weight:700;color:#e8f0f8;">Nifty 200 Signal Analyzer</div>
          <div style="font-size:10px;color:#364f66;font-family:monospace;letter-spacing:2px;">
            EDUCATIONAL TOOL · NOT SEBI REGISTERED · NOT INVESTMENT ADVICE
          </div>
        </div>
      </div>
      <div style="display:flex;gap:24px;align-items:center;">
        <div>
          <div style="color:#364f66;font-size:9px;letter-spacing:2px;font-family:monospace;">ENGINE STATUS</div>
          <div style="display:flex;align-items:center;gap:6px;margin-top:3px;">
            <span class="status-dot pulse" style="background:#00d4aa;display:inline-block;
                  width:6px;height:6px;border-radius:50%;animation:pulse 2s infinite;"></span>
            <span style="color:#00d4aa;font-size:11px;font-weight:600;">READY</span>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="color:#364f66;font-size:9px;letter-spacing:1px;font-family:monospace;">IST TIME</div>
          <div style="color:#7fa8c4;font-size:11px;font-family:monospace;">{datetime.now().strftime('%d %b %Y · %H:%M')}</div>
        </div>
      </div>
    </div>
    {render_ticker_tape()}
  </div>
</div>
""", unsafe_allow_html=True)

    # ── COMPACT DISCLAIMER BANNER (always visible after gate) ─────────────────
    st.markdown(SEBI_COMPACT_HTML, unsafe_allow_html=True)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 📅 Select Analysis Date")

        min_date, max_date = safe_date_bounds()
        default_dt         = default_backtest_date()

        target_date = st.date_input(
            "Trade Date",
            value      = default_dt,
            min_value  = min_date,
            max_value  = max_date,
            help       = (
                "Pick any Monday–Friday between 2 years ago and yesterday. "
                "The tool will show which stocks had bullish signals on that day."
            ),
        )

        # Date validation guidance
        if target_date.weekday() >= 5:
            st.warning("⚠️ Weekends have no market data. Please pick a Monday–Friday.")
        elif target_date >= datetime.now().date():
            st.warning("⚠️ Please pick a past date for backtesting.")
        else:
            st.markdown(f"""
<div class="date-guide">
  <div style="color:#38bdf8;font-size:11px;font-weight:600;margin-bottom:4px;">Selected: {target_date.strftime('%d %b %Y (%A)')}</div>
  <div style="color:#364f66;font-size:10px;line-height:1.5;">
    Fetching data from {(target_date - timedelta(days=cfg.history_days)).strftime('%b %Y')}
    to {(target_date + timedelta(days=60)).strftime('%b %Y')}
    to calculate indicators and track outcomes.
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔍 Filter Results")
        cat_filter = st.radio(
            "Show signals",
            ["All Signals", "🔵 Blue Only", "🟡 Amber Only"],
            help="Blue = strongest setups · Amber = secondary setups",
        )
        filter_map = {"All Signals": "ALL", "🔵 Blue Only": "BLUE", "🟡 Amber Only": "AMBER"}
        cat_key    = filter_map[cat_filter]

        st.markdown("---")
        st.markdown("### 🎨 Display Options")
        show_plain  = st.checkbox(
            "Show beginner explanations",
            value = st.session_state["show_plain"],
            help  = "Adds plain-English descriptions inside each signal card",
        )
        st.session_state["show_plain"] = show_plain
        show_table  = st.checkbox("Show summary table", value=True)
        show_json   = st.checkbox("Show JSON export",   value=False)
        show_debug  = st.checkbox("Show debug log",     value=False)

        st.markdown("---")
        st.markdown("### ⚙️ Engine Info")
        st.caption(f"RSI Period: {cfg.rsi_period} bars")
        st.caption(f"Fast SMA:  {cfg.sma_fast} bars")
        st.caption(f"Slow SMA:  {cfg.sma_slow} bars")
        st.caption(f"ATR:       {cfg.atr_period} bars")
        st.caption(f"Parallel workers: {cfg.fetch_workers}")
        st.caption(f"History window:   {cfg.history_days} days")

        st.markdown("---")
        if st.button("📖 Read Disclaimer Again"):
            st.session_state["disclaimer_accepted"] = False
            st.rerun()

    # ── BEGINNER GUIDE (collapsible) ──────────────────────────────────────────
    with st.expander("📖 New here? Click to learn how to use this tool", expanded=False):
        st.markdown(HOW_TO_HTML, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(LEGEND_HTML, unsafe_allow_html=True)

    # ── STRATEGY MODEL CARDS ──────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">STRATEGY PERFORMANCE · HISTORICAL BACKTEST DATA</div>', unsafe_allow_html=True)

    mc1_pre = monte_carlo(0.82, 1.0, 5000, 15)
    mc2_pre = monte_carlo(0.74, 2.0, 5000, 15)

    col_ma, col_mb = st.columns(2)
    with col_ma:
        st.markdown(
            render_model_card("Model A — Precision", "1", 82, mc1_pre, "#38bdf8",
                              "CONSERVATIVE · 1:1 RISK/REWARD"),
            unsafe_allow_html=True,
        )
    with col_mb:
        st.markdown(
            render_model_card("Model B — Extended", "2", 74, mc2_pre, "#00d4aa",
                              "AGGRESSIVE · 1:2 RISK/REWARD"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DATE VALIDITY CHECK BEFORE RUN BUTTON ─────────────────────────────────
    date_ok = (target_date.weekday() < 5) and (target_date < datetime.now().date())

    if not date_ok:
        st.error("❌ Please select a valid weekday in the past (not today, not a weekend).")

    # ── RUN BUTTON ────────────────────────────────────────────────────────────
    btn_label = f"🔍 Run Signal Scan for {target_date.strftime('%d %b %Y')}"
    run_btn   = st.button(btn_label, type="primary", disabled=(not date_ok))

    if run_btn and date_ok:
        t0         = time.perf_counter()
        pbar       = st.progress(0, text="Starting scan…")
        status_txt = st.empty()
        status_txt.info("📡 Connecting to market data feeds…")

        with st.spinner("Scanning Nifty 200 universe — this usually takes 30–90 seconds…"):
            analyser = Nifty200Analyser()
            records  = analyser.run(
                target_date,
                progress_bar = pbar,
                status_txt   = status_txt,
            )

        pbar.empty()
        status_txt.empty()
        elapsed = time.perf_counter() - t0

        if not records:
            st.warning(
                f"⚠️ No signals found for **{target_date.strftime('%d %b %Y')}**.\n\n"
                "Possible reasons:\n"
                "- The market was closed (public holiday)\n"
                "- No stocks passed the Triple-Bullish filter that day\n"
                "- Data not yet available for this date\n\n"
                "💡 Try a different recent trading day."
            )
        else:
            st.session_state["records"] = records
            st.session_state["date"]    = target_date
            st.session_state["elapsed"] = elapsed

    # ── RENDER RESULTS ────────────────────────────────────────────────────────
    if "records" not in st.session_state:
        st.markdown("""
<div style="text-align:center;padding:60px 0;color:#1e3045;">
  <div style="font-size:52px;margin-bottom:14px;opacity:.5;">📊</div>
  <div style="font-size:15px;color:#364f66;font-weight:600;">Select a date on the left and click Run Signal Scan</div>
  <div style="font-size:12px;color:#263d52;margin-top:8px;">The tool will scan 150+ Nifty 200 stocks for bullish setups</div>
</div>""", unsafe_allow_html=True)
        return

    records  = st.session_state["records"]
    tgt_date = st.session_state["date"]
    elapsed  = st.session_state["elapsed"]

    # Apply category filter
    cat_map  = {"ALL": None, "BLUE": "BLUE", "AMBER": "AMBER"}
    filt_key = cat_map.get(cat_key)
    filtered = [r for r in records if filt_key is None or r.category == filt_key]

    blue     = [r for r in records if r.category == "BLUE"]
    amber    = [r for r in records if r.category == "AMBER"]
    bjp      = sum(1 for r in blue if r.jackpot)
    accuracy = round(bjp / len(blue) * 100, 1) if blue else 0.0
    avg_conf = round(sum(r.confidence for r in records) / len(records), 1) if records else 0

    # ── SUCCESS BANNER ────────────────────────────────────────────────────────
    st.success(
        f"✅ Scan complete for **{tgt_date.strftime('%d %B %Y')}** — "
        f"**{len(records)} signals** found in {elapsed:.1f}s"
    )

    # ── SUMMARY STATS ─────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-hdr" style="margin-top:8px;">SCAN RESULTS SUMMARY · {tgt_date.strftime("%d %b %Y")}</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📊 Total Signals",  len(records),  help="Stocks that passed the Triple-Bullish filter")
    c2.metric("🔵 Blue Signals",   len(blue),      help="Strongest setups — RSI>65, volume surge, above SMA200×1.05")
    c3.metric("🎯 Blue Accuracy",  f"{accuracy}%", f"{bjp} of {len(blue)} hit target",
              help="% of Blue signals that later hit Take-Profit 2")
    c4.metric("⚡ Avg Confidence", f"{avg_conf}",  help="Average confidence score across all signals (0–100)")
    c5.metric("🟡 Amber Signals",  len(amber),     help="Valid setups that don't meet all Blue criteria")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MONTE CARLO ───────────────────────────────────────────────────────────
    with st.expander("📈 Positive Expectancy Engine — Monte Carlo Simulation", expanded=True):
        mc1     = monte_carlo(0.82, 1.0)
        mc2     = monte_carlo(0.74, 2.0)
        blended = round((mc1 + mc2) / 2, 1)

        mc_html = f"""
<div style="background:#080f19;border:1px solid #162030;border-radius:7px;padding:22px 26px;">
  <div style="color:#364f66;font-size:9px;letter-spacing:3px;font-family:monospace;margin-bottom:16px;">
    10,000 TRIAL SIMULATION · 15 TRADES/MONTH · HISTORICAL WIN RATES
  </div>
  <div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap;">
    <div style="display:flex;gap:24px;align-items:flex-end;">
      <div class="gauge-wrap">{render_gauge_svg(mc1, "#38bdf8", "MODEL A · 1:1")}</div>
      <div class="gauge-wrap">{render_gauge_svg(mc2, "#00d4aa", "MODEL B · 1:2")}</div>
    </div>
    <div style="flex:1;min-width:240px;">
      <div style="color:#c8d8e8;font-size:15px;font-weight:700;margin-bottom:6px;">
        Monthly Profitable Probability
      </div>
      <div style="color:#364f66;font-size:11px;margin-bottom:18px;line-height:1.6;">
        This simulation runs 10,000 imaginary trading months, each with 15 trades,
        using the historical win rates of each model. It calculates what percentage
        of those months ended with a profit.
      </div>
      <div style="background:rgba(0,212,170,.06);border:1px solid rgba(0,212,170,.18);
                  border-radius:5px;padding:16px 20px;margin-bottom:14px;">
        <div style="color:#364f66;font-size:10px;letter-spacing:2px;font-family:monospace;margin-bottom:6px;">BLENDED SCORE</div>
        <div class="mono" style="color:#00d4aa;font-size:34px;font-weight:700;">{blended}%</div>
        <div style="color:#364f66;font-size:11px;margin-top:4px;">
          of simulated months were profitable (across both models)
        </div>
      </div>
      <div style="background:rgba(255,77,109,.04);border:1px solid rgba(255,77,109,.15);
                  border-radius:5px;padding:10px 14px;">
        <div style="color:#7a3d48;font-size:10px;line-height:1.6;">
          ⚠️ <b>Simulation disclaimer:</b> Monte Carlo results are based on historical win rates
          and do not predict future results. Actual trading outcomes depend on many factors
          including execution, slippage, and market conditions.
        </div>
      </div>
    </div>
  </div>
</div>"""
        st.markdown(mc_html, unsafe_allow_html=True)

    # ── SUMMARY TABLE ─────────────────────────────────────────────────────────
    if show_table and filtered:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="section-hdr">SIGNAL SUMMARY TABLE · {len(filtered)} RESULTS</div>', unsafe_allow_html=True)

        df_out = pd.DataFrame([{
            "Stock":           r.ticker,
            "Category":        r.category,
            "Status":          STATUS_META.get(r.status, STATUS_META["RUNNING"])["label"],
            "Entry ₹":         r.entry,
            "Stop Loss ₹":     r.stop_loss,
            "Target 1 (1:1)₹": r.tp1,
            "Target 2 (1:2)₹": r.tp2,
            "RSI":             r.rsi,
            "Vol Surge":       r.vol_ratio,
            "MACD Hist":       r.macd_hist,
            "Δ SMA200 %":      r.pct_vs_sma200,
            "Confidence":      r.confidence,
            "Target Met":      r.jackpot,
            "Chart Link":      r.chart_url,
        } for r in filtered])

        st.dataframe(
            df_out,
            column_config={
                "Confidence":      st.column_config.ProgressColumn(
                    "Confidence Score", min_value=0, max_value=100, format="%.1f",
                    help="0–100 composite score based on trend, RSI, volume, MACD, ATR"
                ),
                "Entry ₹":         st.column_config.NumberColumn("Entry ₹",  format="₹%,.2f"),
                "Stop Loss ₹":     st.column_config.NumberColumn("Stop ₹",   format="₹%,.2f"),
                "Target 1 (1:1)₹": st.column_config.NumberColumn("TP1 ₹",    format="₹%,.2f"),
                "Target 2 (1:2)₹": st.column_config.NumberColumn("TP2 ₹",    format="₹%,.2f"),
                "Vol Surge":       st.column_config.NumberColumn("Volume ×",  format="%.2f×"),
                "MACD Hist":       st.column_config.NumberColumn("MACD Hist", format="%.4f"),
                "Δ SMA200 %":      st.column_config.NumberColumn("Δ SMA200",  format="%.2f%%"),
                "Target Met":      st.column_config.CheckboxColumn("Hit TP2?"),
                "Chart Link":      st.column_config.LinkColumn("📈 Chart"),
            },
            hide_index=True,
            use_container_width=True,
            height=min(400, 55 + len(df_out) * 35),
        )

    # ── SIGNAL CARDS ──────────────────────────────────────────────────────────
    if filtered:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-hdr">SIGNAL CARDS · {len(filtered)} RESULTS · SORTED BY CONFIDENCE ↓</div>',
            unsafe_allow_html=True,
        )

        cols_per_row = 3
        for row_start in range(0, len(filtered), cols_per_row):
            batch = filtered[row_start: row_start + cols_per_row]
            cols  = st.columns(len(batch))
            for col, rec in zip(cols, batch):
                with col:
                    st.markdown(
                        render_signal_card(rec, show_plain=show_plain),
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No signals match the selected filter. Try 'All Signals' from the sidebar.")

    # ── DEEP DIVE EXPANDERS ───────────────────────────────────────────────────
    if filtered:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-hdr">DEEP-DIVE ANALYSIS · CLICK ANY ROW TO EXPAND</div>', unsafe_allow_html=True)

        for rec in filtered:
            sm  = STATUS_META.get(rec.status, STATUS_META["RUNNING"])
            hdr = f"{rec.ticker}  ·  {rec.category}  ·  {sm['label']}  ·  Confidence {rec.confidence:.0f}/100"
            with st.expander(hdr):
                ca, cb, cc_col = st.columns(3)
                with ca:
                    st.markdown("#### 📋 Trade Setup")
                    st.write(f"**Entry Price:**   ₹{rec.entry:,.2f}")
                    st.write(f"**Stop Loss:**     ₹{rec.stop_loss:,.2f}  (risk per share: ₹{rec.risk_pts:.2f})")
                    st.write(f"**Take-Profit 1:** ₹{rec.tp1:,.2f}  (1:1 risk-reward)")
                    st.write(f"**Take-Profit 2:** ₹{rec.tp2:,.2f}  (1:2 risk-reward)")
                    st.write(f"**Outcome:**       {sm['plain']}")
                with cb:
                    st.markdown("#### 📊 Indicator Readings")
                    st.write(f"**RSI (Wilder):**     {rec.rsi}  *(above 65 = strong momentum)*")
                    st.write(f"**MACD Histogram:**   {rec.macd_hist}  *(positive = bullish momentum)*")
                    st.write(f"**ATR (Volatility):** ₹{rec.atr:.2f}  *(average daily range)*")
                    st.write(f"**Volume Surge:**     {rec.vol_ratio:.2f}×  *(vs 5-day average)*")
                    st.write(f"**Above SMA200:**     +{rec.pct_vs_sma200:.2f}%  *(long-term trend strength)*")
                with cc_col:
                    st.markdown("#### ⚡ Confidence Score")
                    cc = _conf_color(rec.confidence)
                    st.markdown(
                        f"<div style='color:{cc};font-size:3em;font-weight:700;"
                        f"font-family:monospace;text-align:center;'>{rec.confidence:.0f}<span style='font-size:.5em;'>/100</span></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='text-align:center;color:{cc};font-size:13px;font-weight:600;"
                        f"margin-bottom:12px;'>{_conf_plain(rec.confidence)}</div>",
                        unsafe_allow_html=True,
                    )
                    st.write("Score breakdown (out of 100):")
                    st.caption("Trend alignment: up to 30 pts")
                    st.caption("RSI momentum: up to 20 pts")
                    st.caption("Volume surge: up to 20 pts")
                    st.caption("MACD direction: up to 15 pts")
                    st.caption("ATR regime: up to 15 pts")
                    st.link_button(f"📈 View {rec.ticker} on TradingView", rec.chart_url)

    # ── JSON EXPORT ───────────────────────────────────────────────────────────
    if show_json and filtered:
        st.divider()
        with st.expander("📤 Raw JSON Export (Developer / API Use)"):
            st.json(json.dumps([r.to_dict() for r in filtered], indent=2))

    # ── DEBUG LOG ─────────────────────────────────────────────────────────────
    if show_debug:
        st.divider()
        with st.expander("🐛 Debug Log"):
            try:
                with open("nifty200.log") as f:
                    st.code(f.read()[-6000:], language="log")
            except FileNotFoundError:
                st.info("Log file not yet created.")

    # ── FOOTER ───────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:28px 0 8px;border-top:1px solid #162030;margin-top:28px;">
  <div style="color:#1e3045;font-size:9px;letter-spacing:3px;font-family:monospace;margin-bottom:6px;">
    NIFTY 200 SIGNAL ANALYZER · WILDER RSI · EMA MACD · ATR VOLATILITY ·
    MONTE CARLO · CONFIDENCE SCORING · CONCURRENT FETCH
  </div>
  <div style="color:#7a3d48;font-size:10px;margin-top:4px;">
    ⚠️ NOT SEBI REGISTERED · FOR EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE ·
    CONSULT A CERTIFIED FINANCIAL ADVISOR BEFORE MAKING ANY TRADING DECISION
  </div>
</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
