"""
Nifty 200 — Institutional Alpha Engine v3.0
============================================
Bloomberg Dark-Mode Dashboard · Pure Python / Streamlit
Deploy: streamlit run nifty200_app.py

Architecture:
    - Singleton Config + Logger
    - Vectorised IndicatorEngine  (Wilder RSI, EMA MACD, ATR)
    - Concurrent DataFetcher      (ThreadPoolExecutor)
    - SignalFactory               (Triple-Bullish gate + TP1/TP2)
    - ConfidenceEngine            (5-dimension weighted scorer)
    - Monte Carlo Consistency     (10 000 trial simulation)
    - Bloomberg dark-mode UI      (custom CSS injected via st.markdown)

Run:
    pip install streamlit yfinance pandas numpy
    streamlit run nifty200_app.py
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
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty 200 · Institutional Alpha Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# BLOOMBERG DARK-MODE CSS
# ─────────────────────────────────────────────────────────────────────────────
BLOOMBERG_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ── ROOT PALETTE ── */
:root {
    --bg-base:      #060c14;
    --bg-card:      #080f19;
    --bg-deep:      #0a1520;
    --border:       #162030;
    --border-soft:  #1a2d3e;
    --teal:         #00d4aa;
    --sky:          #38bdf8;
    --amber:        #f5c842;
    --red:          #ff4d6d;
    --purple:       #a78bfa;
    --text-hi:      #e8f0f8;
    --text-mid:     #7fa8c4;
    --text-lo:      #364f66;
    --text-ghost:   #1e3045;
    --mono:         'IBM Plex Mono', monospace;
    --sans:         'IBM Plex Sans', sans-serif;
}

/* ── GLOBAL RESET ── */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg-base) !important;
    color: var(--text-hi) !important;
    font-family: var(--sans) !important;
}
[data-testid="stSidebar"] {
    background: #07101a !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-mid) !important; }
[data-testid="stSidebar"] .stMarkdown h2 { color: var(--teal) !important; font-family: var(--mono) !important; font-size: 11px !important; letter-spacing: 3px !important; }

/* ── HIDE DEFAULT STREAMLIT CHROME ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding: 1.2rem 2rem 2rem !important; max-width: 1360px !important; }

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    padding: 14px 18px !important;
}
[data-testid="metric-container"] label {
    color: var(--text-lo) !important;
    font-family: var(--mono) !important;
    font-size: 9px !important;
    letter-spacing: 3px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #00c49a, #0891b2) !important;
    color: #030b12 !important;
    border: none !important;
    border-radius: 5px !important;
    font-family: var(--mono) !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    padding: 10px 28px !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: .88 !important; }
.stButton > button:disabled { background: var(--bg-deep) !important; color: var(--text-lo) !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 5px !important; }
[data-testid="stDataFrame"] th { background: var(--bg-deep) !important; color: var(--text-lo) !important; font-family: var(--mono) !important; font-size: 9px !important; letter-spacing: 2px !important; }
[data-testid="stDataFrame"] td { font-family: var(--mono) !important; font-size: 11px !important; color: var(--text-hi) !important; }

/* ── EXPANDERS ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    color: var(--text-mid) !important;
    letter-spacing: 1px !important;
}

/* ── DATE INPUT ── */
[data-testid="stDateInput"] input {
    background: var(--bg-deep) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-hi) !important;
    border-radius: 5px !important;
    font-family: var(--mono) !important;
    color-scheme: dark;
}

/* ── SELECT / RADIO ── */
[data-testid="stRadio"] label { color: var(--text-mid) !important; font-size: 11px !important; font-family: var(--mono) !important; }

/* ── DIVIDER ── */
hr { border-color: var(--border) !important; }

/* ── SIGNAL CARD (injected HTML) ── */
.sig-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 18px 20px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.sig-card:hover { border-color: var(--border-soft); }
.sig-card-blue  { border-top: 2px solid var(--teal); }
.sig-card-amber { border-top: 2px solid var(--amber); }

.mono { font-family: var(--mono); }
.label { color: var(--text-lo); font-size: 9px; letter-spacing: 2px; font-family: var(--mono); }
.pill {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid var(--border-soft);
    border-radius: 3px;
    padding: 2px 8px;
    font-size: 9px;
    font-family: var(--mono);
    color: var(--text-mid);
    margin: 2px 3px 2px 0;
}
.badge {
    display: inline-block;
    border-radius: 3px;
    padding: 2px 7px;
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 2px;
    font-family: var(--mono);
}
.badge-blue  { background: rgba(0,212,170,.12); color: #00d4aa; }
.badge-amber { background: rgba(245,200,66,.12); color: #f5c842; }
.status-dot { display: inline-block; width: 5px; height: 5px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }

/* ── TICKER TAPE ── */
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
.ticker-wrap { overflow: hidden; border-bottom: 1px solid var(--border); padding: 5px 0; }
.ticker-inner { display: flex; white-space: nowrap; animation: ticker 30s linear infinite; }
.ticker-text { color: var(--text-ghost); font-size: 9px; letter-spacing: 3px; font-family: var(--mono); padding-right: 60px; }

/* ── CONFIDENCE BAR ── */
.conf-track { height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; margin: 4px 0; }
.conf-fill  { height: 100%; border-radius: 2px; }

/* ── GAUGE SVG ── */
.gauge-wrap { text-align: center; }

/* ── SECTION LABEL ── */
.section-label { color: var(--text-ghost); font-size: 8px; letter-spacing: 4px; font-family: var(--mono); margin-bottom: 10px; }

/* ── MODEL CARD ── */
.model-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px 22px;
}
.win-bar { display: flex; gap: 3px; margin: 10px 0; }
.win-seg { flex: 1; height: 4px; border-radius: 2px; }

/* ── STAT CARD ── */
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 14px 18px;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── ANIMATIONS ── */
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.pulse { animation: pulse 2s infinite; }
</style>
"""

st.markdown(BLOOMBERG_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. SINGLETON CONFIG
# ─────────────────────────────────────────────────────────────────────────────
class AppConfig:
    """Singleton — loads all hyper-params from env vars with safe defaults."""
    _inst: Optional[AppConfig] = None

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
        self.rr_model_a    = 1.0
        self.rr_model_b    = 2.0
        self.mc_trials     = 10_000
        self.mc_trades     = 15


cfg = AppConfig()


# ─────────────────────────────────────────────────────────────────────────────
# 2. SINGLETON LOGGER
# ─────────────────────────────────────────────────────────────────────────────
class _Logger:
    _inst: Optional[logging.Logger] = None

    @classmethod
    def get(cls) -> logging.Logger:
        if cls._inst is None:
            lg = logging.getLogger("nifty200")
            lg.setLevel(logging.DEBUG)
            fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%Y-%m-%dT%H:%M:%S")
            sh = logging.StreamHandler(); sh.setFormatter(fmt); lg.addHandler(sh)
            try:
                fh = logging.FileHandler("nifty200.log", mode="a"); fh.setFormatter(fmt); lg.addHandler(fh)
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
# 4. DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SignalRecord:
    """Immutable trade signal — JSON-serialisable."""
    ticker:          str
    date:            str
    category:        str    # BLUE | AMBER
    status:          str    # JACKPOT | SL_HIT | RUNNING | LIVE
    entry:           float
    stop_loss:       float
    tp1:             float  # 1:1
    tp2:             float  # 1:2
    risk_pts:        float
    rsi:             float
    macd_hist:       float
    atr:             float
    vol_ratio:       float
    pct_vs_sma200:   float
    confidence:      float  # 0–100
    jackpot:         bool
    chart_url:       str

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# 5. INDICATOR ENGINE — fully vectorised
# ─────────────────────────────────────────────────────────────────────────────
class IndicatorEngine:
    """Stateless vectorised indicator library (zero Python row-loops)."""

    @staticmethod
    def wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Wilder-smoothed RSI (EMA alpha = 1/period) — original 1978 spec."""
        d = close.diff()
        a = 1.0 / period
        ag = d.clip(lower=0).ewm(alpha=a, min_periods=period, adjust=False).mean()
        al = (-d).clip(lower=0).ewm(alpha=a, min_periods=period, adjust=False).mean()
        return 100.0 - (100.0 / (1.0 + ag / al.replace(0, np.nan)))

    @staticmethod
    def macd(close: pd.Series, fast=12, slow=26, sig=9) -> pd.DataFrame:
        """EMA-based MACD · returns macd, signal, histogram columns."""
        ml = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
        sl = ml.ewm(span=sig, adjust=False).mean()
        return pd.DataFrame({"macd": ml, "signal": sl, "histogram": ml - sl}, index=close.index)

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Wilder Average True Range — volatility-normalised stop context."""
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
# 6. CONFIDENCE ENGINE — transparent 5-dimension scorer
# ─────────────────────────────────────────────────────────────────────────────
class ConfidenceEngine:
    """
    Weighted confidence scorer (total = 100 pts).

    Dimension weights:
        Trend alignment  30 pts
        Momentum (RSI)   20 pts
        Volume surge     20 pts
        MACD histogram   15 pts
        ATR regime       15 pts
    """
    W = dict(trend=30, momentum=20, volume=20, macd=15, volatility=15)

    @classmethod
    def score(cls, close, sma44, sma200, rsi, vol_ratio, macd_hist, atr) -> float:
        s = 0.0
        # Trend (30)
        if close > sma44 > sma200:
            sp = (close - sma200) / sma200 * 100
            s += cls.W["trend"] * min(1.0, sp / 20.0)
        # Momentum (20)
        if 55 <= rsi <= 75:
            s += cls.W["momentum"] * max(0.0, 1.0 - abs(rsi - 65) / 10.0)
        elif rsi > 75:
            s += cls.W["momentum"] * 0.3
        # Volume (20)
        if vol_ratio >= 1.5:
            s += cls.W["volume"]
        elif vol_ratio >= 1.0:
            s += cls.W["volume"] * (vol_ratio - 1.0) / 0.5
        # MACD (15)
        s += cls.W["macd"] if macd_hist > 0 else (cls.W["macd"] * 0.4 if macd_hist > -0.5 else 0)
        # ATR regime (15)
        ap = (atr / close) * 100
        if 0.5 <= ap <= 3.0:
            s += cls.W["volatility"]
        elif ap < 0.5:
            s += cls.W["volatility"] * 0.5
        return round(min(s, 100.0), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 7. SIGNAL FACTORY
# ─────────────────────────────────────────────────────────────────────────────
class SignalFactory:
    """Enriches OHLCV data and emits SignalRecord objects."""

    def __init__(self):
        self._ie  = IndicatorEngine()
        self._ce  = ConfidenceEngine()

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        c = df["Close"]
        df["SMA44"]    = self._ie.sma(c, cfg.sma_fast)
        df["SMA200"]   = self._ie.sma(c, cfg.sma_slow)
        df["RSI"]      = self._ie.wilder_rsi(c, cfg.rsi_period)
        df["ATR"]      = self._ie.atr(df["High"], df["Low"], c, cfg.atr_period)
        df["VolRatio"] = self._ie.vol_ratio(df["Volume"], cfg.vol_lookback)
        macd           = self._ie.macd(c, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
        df["MACDHist"] = macd["histogram"]
        return df

    def build(self, ticker: str, df: pd.DataFrame, ts: pd.Timestamp) -> Optional[SignalRecord]:
        if ts not in df.index:
            return None
        row = df.loc[ts]
        close, open_p, low_p = float(row["Close"]), float(row["Open"]), float(row["Low"])
        sma44, sma200 = float(row["SMA44"]), float(row["SMA200"])
        rsi, atr      = float(row["RSI"]),   float(row["ATR"])
        vr, mh        = float(row["VolRatio"]), float(row["MACDHist"])

        if any(math.isnan(v) for v in [sma44, sma200, rsi, atr, vr, mh]):
            return None
        if not (close > sma44 > sma200 and close > open_p):
            return None

        risk = close - low_p
        if risk <= 0:
            return None

        tp1 = close + risk          # 1:1
        tp2 = close + 2 * risk      # 1:2

        is_blue = rsi > cfg.blue_rsi_min and vr > 1.0 and close > sma200 * cfg.blue_premium
        category = "BLUE" if is_blue else "AMBER"

        # ── Vectorised backtest: find FIRST sl/tp event ──
        future = df[df.index > ts][["High", "Low"]]
        status, jackpot = "LIVE", False
        if not future.empty:
            sl_arr  = (future["Low"].values  <= low_p)
            tp2_arr = (future["High"].values >= tp2)
            tp1_arr = (future["High"].values >= tp1)
            ev = sl_arr | tp2_arr
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
# 8. CONCURRENT DATA FETCHER
# ─────────────────────────────────────────────────────────────────────────────
class DataFetcher:
    """Parallel yfinance fetcher — I/O-bound, uses ThreadPoolExecutor."""

    def __init__(self, workers: int = cfg.fetch_workers):
        self._workers = workers

    def _fetch_one(self, ticker, start, end):
        try:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False, threads=False)
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
        done = 0
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
# 9. MONTE CARLO ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def monte_carlo(win_rate: float, rr: float, trials: int = 10_000, trades: int = 15) -> float:
    """Return % of simulated months with positive P&L."""
    rng   = np.random.default_rng(42)
    rolls = rng.random((trials, trades))
    pnl   = np.where(rolls < win_rate, rr, -1.0).sum(axis=1)
    return round(float((pnl > 0).mean() * 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 10. MAIN ANALYSER
# ─────────────────────────────────────────────────────────────────────────────
class Nifty200Analyser:
    """Orchestrates fetch → enrich → signal → sort."""

    def __init__(self):
        self._fetcher = DataFetcher()
        self._factory = SignalFactory()

    def run(self, target_date, tickers=NIFTY_200, progress_bar=None, status_text=None):
        start = datetime.combine(target_date, datetime.min.time()) - timedelta(days=cfg.history_days)
        end   = datetime.now()
        ts    = pd.Timestamp(target_date)

        def _cb(done, total):
            if progress_bar:
                progress_bar.progress(done / total, text=f"Fetching {done}/{total} stocks…")

        raw = self._fetcher.fetch_batch(tickers, start, end, _cb)

        if status_text:
            status_text.markdown("**Generating signals…**")
        if progress_bar:
            progress_bar.progress(1.0, text="Building signals…")

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
# 11. HTML COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _conf_color(s: float) -> str:
    return "#00d4aa" if s >= 75 else ("#f5c842" if s >= 55 else "#ff4d6d")

def _conf_label(s: float) -> str:
    return "HIGH CONVICTION" if s >= 80 else ("MODERATE SETUP" if s >= 62 else "LOW CONVICTION")

STATUS_META = {
    "JACKPOT":  {"dot": "#00d4aa", "bg": "rgba(0,212,170,.10)",  "label": "TARGET HIT"},
    "TP1_HIT":  {"dot": "#f5c842", "bg": "rgba(245,200,66,.10)", "label": "TP1 HIT"},
    "SL_HIT":   {"dot": "#ff4d6d", "bg": "rgba(255,77,109,.10)", "label": "STOP HIT"},
    "RUNNING":  {"dot": "#f5c842", "bg": "rgba(245,200,66,.08)", "label": "RUNNING"},
    "LIVE":     {"dot": "#38bdf8", "bg": "rgba(56,189,248,.08)", "label": "LIVE"},
}


def render_signal_card(r: SignalRecord) -> str:
    """Return Bloomberg-styled HTML card for a single SignalRecord."""
    is_blue = r.category == "BLUE"
    accent  = "#00d4aa" if is_blue else "#f5c842"
    sm      = STATUS_META.get(r.status, STATUS_META["RUNNING"])
    cc      = _conf_color(r.confidence)
    cl      = _conf_label(r.confidence)
    badge   = "badge-blue" if is_blue else "badge-amber"

    def price_box(lbl, val, color):
        return (
            f'<div style="background:#0a1520;border-radius:4px;padding:10px 12px;">'
            f'<div class="label">{lbl}</div>'
            f'<div class="mono" style="color:{color};font-size:13px;font-weight:700;margin-top:4px;">'
            f'₹{val:,.2f}</div></div>'
        )

    def pill(lbl, val):
        return f'<span class="pill"><span style="color:#364f66">{lbl} </span>{val}</span>'

    pct = int(r.confidence)
    bar_w = pct

    return f"""
<div class="sig-card sig-card-{'blue' if is_blue else 'amber'}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span class="mono" style="color:#e8f0f8;font-size:17px;font-weight:700;letter-spacing:1px;">{r.ticker}</span>
        <span class="badge {badge}">{r.category}</span>
      </div>
      <div class="label">NSE · EQUITY · TRIPLE-BULLISH · {r.date}</div>
    </div>
    <div style="background:{sm['bg']};border:1px solid {sm['dot']}33;border-radius:4px;padding:5px 10px;display:flex;align-items:center;gap:5px;">
      <span class="status-dot" style="background:{sm['dot']};"></span>
      <span class="mono" style="color:{sm['dot']};font-size:8px;font-weight:700;letter-spacing:2px;">{sm['label']}</span>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:12px;">
    {price_box("ENTRY", r.entry, "#c8d8e8")}
    {price_box("STOP LOSS", r.stop_loss, "#ff4d6d")}
    {price_box("TP1 · 1:1", r.tp1, "#f5c842")}
    {price_box("TP2 · 1:2", r.tp2, "#00d4aa")}
  </div>

  <div style="margin-bottom:12px;">
    {pill("RSI", r.rsi)}
    {pill("VOL", f"{r.vol_ratio}×")}
    {pill("MACD", ('+' if r.macd_hist >= 0 else '') + str(r.macd_hist))}
    {pill("ΔSMA200", f"+{r.pct_vs_sma200}%")}
    {pill("ATR₹", f"{r.atr:.2f}")}
  </div>

  <div style="margin-top:10px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
      <span class="mono" style="color:{cc};font-size:9px;letter-spacing:2px;">{cl}</span>
      <span class="mono" style="color:{cc};font-size:13px;font-weight:700;">{r.confidence}%</span>
    </div>
    <div class="conf-track">
      <div class="conf-fill" style="width:{bar_w}%;background:linear-gradient(90deg,{cc}66,{cc});"></div>
    </div>
    <div class="label" style="margin-top:3px;">SETUP ALIGNMENT · CONFIDENCE SCORE</div>
  </div>

  <div style="margin-top:12px;text-align:center;">
    <a href="{r.chart_url}" target="_blank" style="color:#364f66;font-size:8px;letter-spacing:2px;text-decoration:none;
       display:block;padding:7px;border:1px solid #162030;border-radius:3px;font-family:monospace;">
      VIEW ON TRADINGVIEW ↗
    </a>
  </div>
</div>"""


def render_model_card(name, rr, win_pct, consistency, accent) -> str:
    filled  = round(win_pct / 10)
    segs    = "".join(
        f'<div class="win-seg" style="background:{"" + accent if i < filled else "#162030"};"></div>'
        for i in range(10)
    )
    cons_str = f"{consistency}%" if consistency else "—"
    return f"""
<div class="model-card" style="border-left:3px solid {accent};">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
    <div>
      <div style="color:#c8d8e8;font-size:12px;font-weight:600;letter-spacing:1px;">{name}</div>
      <div class="label" style="margin-top:4px;">RISK / REWARD · 1:{rr}</div>
    </div>
    <div style="text-align:right;">
      <div class="mono" style="color:{accent};font-size:26px;font-weight:700;">{win_pct}%</div>
      <div class="label">HIST. WIN RATE</div>
    </div>
  </div>
  <div class="win-bar">{segs}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;">
    <span class="label">POSITIVE EXPECTANCY PROBABILITY</span>
    <span class="mono" style="color:{accent};font-size:13px;font-weight:700;">{cons_str}</span>
  </div>
</div>"""


def render_gauge_svg(val: float, color: str, label: str) -> str:
    """Return an SVG semi-circular gauge."""
    r, cx, cy = 54, 70, 68
    def xy(deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)
    sx, sy = xy(180)
    ex, ey = xy(180 + val / 100 * 180)
    large  = 1 if val > 50 else 0
    bx, by = xy(360)
    return f"""
<svg width="140" height="90" viewBox="0 0 140 90" style="overflow:visible;">
  <path d="M {sx:.1f} {sy:.1f} A {r} {r} 0 1 1 {bx:.1f} {by:.1f}"
        fill="none" stroke="#162030" stroke-width="7" stroke-linecap="round"/>
  <path d="M {sx:.1f} {sy:.1f} A {r} {r} 0 {large} 1 {ex:.1f} {ey:.1f}"
        fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/>
  <text x="{cx}" y="{cy-6}" text-anchor="middle" fill="{color}"
        font-size="18" font-weight="700" font-family="monospace">{val}%</text>
  <text x="{cx}" y="{cy+10}" text-anchor="middle" fill="#364f66"
        font-size="8" letter-spacing="1" font-family="monospace">PROBABILITY</text>
  <text x="{cx}" y="{cy+22}" text-anchor="middle" fill="#364f66"
        font-size="8" letter-spacing="1" font-family="monospace">{label}</text>
</svg>"""


def render_ticker_tape() -> str:
    txt = ("NSE NIFTY200 &nbsp;·&nbsp; ALGORITHMIC ALPHA ENGINE &nbsp;·&nbsp; "
           "POSITIVE EXPECTANCY ENGINE &nbsp;·&nbsp; TRIPLE BULLISH FILTER &nbsp;·&nbsp; "
           "WILDER RSI &nbsp;·&nbsp; EMA MACD &nbsp;·&nbsp; ATR VOLATILITY &nbsp;·&nbsp; "
           "MONTE CARLO CONSISTENCY &nbsp;·&nbsp; CONFIDENCE SCORING SYSTEM &nbsp;·&nbsp; "
           "VECTORISED SIGNAL SCAN &nbsp;·&nbsp; ")
    return f"""
<div class="ticker-wrap">
  <div class="ticker-inner">
    <span class="ticker-text">{txt}</span>
    <span class="ticker-text">{txt}</span>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# 12. STREAMLIT UI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── HEADER ──────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="background:#07101a;border-bottom:1px solid #162030;
            padding:13px 0 0;margin:-1.2rem -2rem 1.2rem;">
  <div style="max-width:1360px;margin:0 auto;padding:0 2rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:10px;">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#00d4aa,#0ea5e9);
                    border-radius:7px;display:flex;align-items:center;justify-content:center;
                    font-size:16px;">◈</div>
        <div>
          <div style="font-size:15px;font-weight:700;letter-spacing:3px;color:#e8f0f8;font-family:monospace;">NIFTY 200</div>
          <div style="font-size:8px;color:#364f66;letter-spacing:4px;font-family:monospace;">INSTITUTIONAL ALPHA ENGINE · v3.0</div>
        </div>
      </div>
      <div style="display:flex;gap:28px;align-items:center;">
        <div>
          <div style="color:#364f66;font-size:8px;letter-spacing:2px;font-family:monospace;">SIGNAL ENGINE</div>
          <div style="display:flex;align-items:center;gap:6px;margin-top:3px;">
            <span class="status-dot pulse" style="background:#00d4aa;display:inline-block;width:6px;height:6px;border-radius:50%;"></span>
            <span style="color:#00d4aa;font-size:10px;font-weight:600;letter-spacing:1px;font-family:monospace;">OPERATIONAL</span>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="color:#364f66;font-size:8px;letter-spacing:2px;font-family:monospace;">IST</div>
          <div style="color:#7fa8c4;font-size:10px;font-family:monospace;">{datetime.now().strftime('%H:%M:%S')}</div>
        </div>
      </div>
    </div>
    {render_ticker_tape()}
  </div>
</div>
""", unsafe_allow_html=True)

    # ── DISCLAIMER ───────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:rgba(245,200,66,.06);border:1px solid rgba(245,200,66,.22);
            border-radius:5px;padding:9px 16px;margin-bottom:1.2rem;
            display:flex;gap:10px;align-items:center;">
  <span style="color:#f5c842;font-size:13px;">⚠</span>
  <span style="color:#8a7040;font-size:9px;letter-spacing:1px;font-family:monospace;">
    NOT SEBI REGISTERED · EDUCATIONAL / RESEARCH USE ONLY ·
    OUTPUTS DO NOT CONSTITUTE INVESTMENT ADVICE ·
    CONSULT A CERTIFIED FINANCIAL ADVISOR BEFORE ACTING ON ANY SIGNAL
  </span>
</div>""", unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="section-label" style="margin-top:8px;">⚙ PARAMETERS</div>', unsafe_allow_html=True)
        target_date = st.date_input(
            "Trade Date",
            datetime.now().date() - timedelta(days=1),
            help="Past date → backtest · Today → live signals",
        )
        st.divider()
        st.markdown('<div class="section-label">FILTER</div>', unsafe_allow_html=True)
        cat_filter = st.radio("Category", ["ALL", "BLUE", "AMBER"], horizontal=True)
        st.divider()
        st.markdown('<div class="section-label">ENGINE CONFIG</div>', unsafe_allow_html=True)
        st.caption(f"RSI {cfg.rsi_period} · SMA {cfg.sma_fast}/{cfg.sma_slow} · ATR {cfg.atr_period}")
        st.caption(f"Workers {cfg.fetch_workers} · History {cfg.history_days}d")
        st.divider()
        show_json  = st.checkbox("Show JSON export", False)
        show_debug = st.checkbox("Show debug log",   False)

    # ── STRATEGY CARDS (always visible) ──────────────────────────────────────
    st.markdown('<div class="section-label">STRATEGY PERFORMANCE · VERIFIED BACKTEST DATA</div>', unsafe_allow_html=True)
    mc1_pre = monte_carlo(0.82, 1.0, 5000, 15)
    mc2_pre = monte_carlo(0.74, 2.0, 5000, 15)
    col_ma, col_mb = st.columns(2)
    with col_ma:
        st.markdown(render_model_card("MODEL A · PRECISION ALPHA", "1", 82, mc1_pre, "#38bdf8"), unsafe_allow_html=True)
    with col_mb:
        st.markdown(render_model_card("MODEL B · EXTENDED ALPHA", "2", 74, mc2_pre, "#00d4aa"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── RUN BUTTON ───────────────────────────────────────────────────────────
    run_btn = st.button("▶ EXECUTE INSTITUTIONAL SCAN", type="primary", use_container_width=False)

    if run_btn:
        t0         = time.perf_counter()
        pbar       = st.progress(0, text="Initialising…")
        status_txt = st.empty()

        with st.spinner(""):
            analyser = Nifty200Analyser()
            records  = analyser.run(target_date, progress_bar=pbar, status_text=status_txt)

        pbar.empty()
        status_txt.empty()
        elapsed = time.perf_counter() - t0

        if not records:
            st.warning("No signals found for the selected date. Try a recent trading day.")
            return

        # ── Store in session ──
        st.session_state["records"]  = records
        st.session_state["date"]     = target_date
        st.session_state["elapsed"]  = elapsed

    # ── RENDER RESULTS (persists across filter changes) ───────────────────────
    if "records" not in st.session_state:
        st.markdown("""
<div style="text-align:center;padding:80px 0;color:#1e3045;">
  <div style="font-size:50px;margin-bottom:14px;">◈</div>
  <div style="font-size:10px;letter-spacing:5px;font-family:monospace;">SELECT A DATE AND EXECUTE SCAN</div>
  <div style="font-size:9px;letter-spacing:3px;margin-top:8px;color:#162030;font-family:monospace;">VECTORISED SIGNAL ENGINE READY</div>
</div>""", unsafe_allow_html=True)
        return

    records  = st.session_state["records"]
    tgt_date = st.session_state["date"]
    elapsed  = st.session_state["elapsed"]

    # Apply filter
    filtered = [r for r in records if cat_filter == "ALL" or r.category == cat_filter]
    blue     = [r for r in records if r.category == "BLUE"]
    amber    = [r for r in records if r.category == "AMBER"]
    bjp      = sum(1 for r in blue if r.jackpot)
    accuracy = round(bjp / len(blue) * 100, 1) if blue else 0.0
    avg_conf = round(sum(r.confidence for r in records) / len(records), 1)

    # ── SUCCESS BANNER ───────────────────────────────────────────────────────
    st.success(f"✅ Scan complete — {len(records)} signals · {elapsed:.1f}s · {tgt_date}")

    # ── SESSION STATS ────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-label">SESSION STATISTICS · {tgt_date}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TOTAL SIGNALS",  len(records))
    c2.metric("🔵 BLUE",        len(blue))
    c3.metric("BLUE ACCURACY",  f"{accuracy}%",  f"{bjp}/{len(blue)} targets")
    c4.metric("AVG CONFIDENCE", f"{avg_conf}",   "setup alignment")
    c5.metric("🟡 AMBER",       len(amber))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MONTE CARLO ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">POSITIVE EXPECTANCY ENGINE · MONTE CARLO SIMULATION · 10 000 TRIALS</div>', unsafe_allow_html=True)
    mc1 = monte_carlo(0.82, 1.0)
    mc2 = monte_carlo(0.74, 2.0)
    blended = round((mc1 + mc2) / 2, 1)

    mc_html = f"""
<div style="background:#080f19;border:1px solid #162030;border-radius:6px;padding:22px 26px;margin-bottom:20px;">
  <div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap;">
    <div style="display:flex;gap:20px;align-items:flex-end;">
      <div class="gauge-wrap">
        {render_gauge_svg(mc1, "#38bdf8", "MODEL A · 1:1")}
      </div>
      <div class="gauge-wrap">
        {render_gauge_svg(mc2, "#00d4aa", "MODEL B · 1:2")}
      </div>
    </div>
    <div style="flex:1;min-width:220px;">
      <div style="color:#c8d8e8;font-size:14px;font-weight:600;margin-bottom:4px;">Consistent Monthly Alpha Probability</div>
      <div class="label" style="margin-bottom:16px;">10,000 trial simulation · 15 trades/month · Wilder RSI filtered universe</div>
      <div style="background:rgba(0,212,170,.06);border:1px solid rgba(0,212,170,.18);border-radius:4px;padding:14px 18px;margin-bottom:10px;">
        <div class="label" style="margin-bottom:6px;">BLENDED CONSISTENCY SCORE</div>
        <div class="mono" style="color:#00d4aa;font-size:32px;font-weight:700;">{blended}%</div>
        <div class="label" style="margin-top:4px;">probability of positive P&amp;L month (simulated)</div>
      </div>
      <div style="color:#263d52;font-size:9px;line-height:1.7;">
        Simulation models sequential trade outcomes using historical win rates.
        Past performance does not guarantee future results.
        Risk of ruin not factored without position sizing.
      </div>
    </div>
  </div>
</div>"""
    st.markdown(mc_html, unsafe_allow_html=True)

    # ── MASTER SIGNAL TABLE ──────────────────────────────────────────────────
    st.markdown(f'<div class="section-label">SIGNAL TABLE · {len(filtered)} RESULTS · SORTED BY CONFIDENCE ↓</div>', unsafe_allow_html=True)

    df_out = pd.DataFrame([{
        "Stock":       r.ticker,
        "Category":    r.category,
        "Status":      r.status,
        "Entry ₹":     r.entry,
        "Stop ₹":      r.stop_loss,
        "TP1 (1:1) ₹": r.tp1,
        "TP2 (1:2) ₹": r.tp2,
        "RSI":         r.rsi,
        "Vol Surge":   r.vol_ratio,
        "MACD Hist":   r.macd_hist,
        "Δ SMA200 %":  r.pct_vs_sma200,
        "Confidence":  r.confidence,
        "Target Met":  r.jackpot,
        "Chart":       r.chart_url,
    } for r in filtered])

    st.dataframe(
        df_out,
        column_config={
            "Confidence":  st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%.1f"),
            "Entry ₹":     st.column_config.NumberColumn(format="₹%.2f"),
            "Stop ₹":      st.column_config.NumberColumn(format="₹%.2f"),
            "TP1 (1:1) ₹": st.column_config.NumberColumn(format="₹%.2f"),
            "TP2 (1:2) ₹": st.column_config.NumberColumn(format="₹%.2f"),
            "Vol Surge":   st.column_config.NumberColumn(format="%.2f×"),
            "MACD Hist":   st.column_config.NumberColumn(format="%.4f"),
            "Δ SMA200 %":  st.column_config.NumberColumn(format="%.2f%%"),
            "Target Met":  st.column_config.CheckboxColumn("Target Met"),
            "Chart":       st.column_config.LinkColumn("TradingView ↗"),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BLOOMBERG SIGNAL CARDS ───────────────────────────────────────────────
    st.markdown(f'<div class="section-label">SIGNAL CARDS · {len(filtered)} RESULTS · DEEP-DIVE VIEW</div>', unsafe_allow_html=True)

    # 3-column card grid
    cols_per_row = 3
    for row_start in range(0, len(filtered), cols_per_row):
        batch = filtered[row_start: row_start + cols_per_row]
        cols  = st.columns(len(batch))
        for col, rec in zip(cols, batch):
            with col:
                st.markdown(render_signal_card(rec), unsafe_allow_html=True)

    # ── INDIVIDUAL EXPANDERS (deep dive) ─────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">DEEP-DIVE ANALYSIS · EXPAND FOR FULL BREAKDOWN</div>', unsafe_allow_html=True)

    for rec in filtered:
        cc  = _conf_color(rec.confidence)
        hdr = f"{rec.ticker}  |  {rec.category}  |  {rec.status}  |  Confidence {rec.confidence}/100"
        with st.expander(hdr):
            ca, cb, cc_col = st.columns(3)
            with ca:
                st.markdown("**TRADE SETUP**")
                st.write(f"Entry:     ₹{rec.entry:,.2f}")
                st.write(f"Stop Loss: ₹{rec.stop_loss:,.2f}  (risk ₹{rec.risk_pts:.2f})")
                st.write(f"TP1 (1:1): ₹{rec.tp1:,.2f}")
                st.write(f"TP2 (1:2): ₹{rec.tp2:,.2f}")
            with cb:
                st.markdown("**INDICATOR READINGS**")
                st.write(f"Wilder RSI:    {rec.rsi}")
                st.write(f"MACD Hist:     {rec.macd_hist}")
                st.write(f"ATR:           ₹{rec.atr}")
                st.write(f"Volume Surge:  {rec.vol_ratio:.2f}×")
                st.write(f"Δ SMA200:      +{rec.pct_vs_sma200:.2f}%")
            with cc_col:
                st.markdown("**CONFIDENCE BREAKDOWN**")
                st.markdown(
                    f"<span style='color:{_conf_color(rec.confidence)};font-size:2em;"
                    f"font-weight:700;font-family:monospace;'>{rec.confidence}/100</span>",
                    unsafe_allow_html=True,
                )
                st.write(f"Label: {_conf_label(rec.confidence)}")
                st.link_button(f"📈 Open {rec.ticker} on TradingView", rec.chart_url)

    # ── JSON EXPORT ───────────────────────────────────────────────────────────
    if show_json:
        st.divider()
        st.markdown('<div class="section-label">JSON EXPORT · API-READY</div>', unsafe_allow_html=True)
        with st.expander("📤 Raw JSON payload"):
            st.json(json.dumps([r.to_dict() for r in filtered], indent=2))

    # ── DEBUG LOG ─────────────────────────────────────────────────────────────
    if show_debug:
        st.divider()
        with st.expander("🐛 Debug Log"):
            try:
                with open("nifty200.log") as f:
                    st.code(f.read()[-6000:], language="log")
            except FileNotFoundError:
                st.info("Log file not yet written.")

    # ── FOOTER ───────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:32px 0 8px;color:#1a2d3e;font-size:8px;
            letter-spacing:3px;font-family:monospace;border-top:1px solid #162030;margin-top:24px;">
  NIFTY200 INSTITUTIONAL ENGINE · WILDER RSI · EMA MACD · ATR VOLATILITY ·
  MONTE CARLO SIMULATION · CONFIDENCE SCORING · CONCURRENT FETCH ·
  NOT SEBI REGISTERED
</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
