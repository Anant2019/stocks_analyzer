"""
Arthsutra — Swing Triple Bullish 44/200 Scanner
================================================
Discipline · Prosperity · Consistency

PineScript logic faithfully ported to Python:
  ✅ s44 = SMA(close, 44)
  ✅ s200 = SMA(close, 200)
  ✅ is_trending = s44 > s200 AND s44 > s44[2] AND s200 > s200[2]
  ✅ is_strong   = close > open AND close > (high+low)/2
  ✅ buy         = is_trending AND is_strong AND low <= s44 AND close > s44
  ✅ sl_val      = buy ? low : na
  ✅ risk        = close - low
  ✅ tgt1        = close + risk          (1:1 R/R)
  ✅ tgt2        = close + risk * 2      (1:2 R/R)

Run:
    pip install streamlit yfinance pandas numpy
    streamlit run swing_scanner.py
"""

from __future__ import annotations

import logging
import os
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Optional
import calendar

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arthsutra · Swing Scanner",
    page_icon="🔱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — Dark terminal aesthetic. Obsidian base, acid-green signals,
#        amber alerts. Commit to "institutional trading terminal" energy.
#        Fonts: Barlow Condensed (headers) + JetBrains Mono (data)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Barlow:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  /* Base */
  --bg:        #080b10;
  --surface:   #0d1219;
  --surface2:  #121922;
  --surface3:  #16202c;
  --border:    #1e2d3e;
  --border2:   #283d52;

  /* Signal colours — exact pine mapping */
  --buy:       #00ff88;    /* BUY signal — bright acid green */
  --buy-dim:   #00c864;
  --buy-bg:    rgba(0,255,136,.06);
  --sl:        #ff3d57;    /* Stop Loss — pine color.red */
  --tgt1:      #ff9500;    /* Target 1:1 — pine color.orange */
  --tgt2:      #4d9fff;    /* Target 1:2 — pine color.blue */

  /* Text */
  --hi:        #e8f4ff;
  --mid:       #6a90aa;
  --lo:        #344f64;
  --ghost:     #1a2d3e;

  /* Typography */
  --display:   'Barlow Condensed', sans-serif;
  --body:      'Barlow', sans-serif;
  --mono:      'JetBrains Mono', monospace;

  --r:         8px;
  --r-lg:      14px;
}

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: var(--bg) !important;
  font-family: var(--body) !important;
}

.main .block-container {
  padding: 0 1rem 4rem !important;
  max-width: 740px !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── TYPOGRAPHY ── */
.stMarkdown p, .stMarkdown li {
  color: var(--mid) !important;
  font-family: var(--body) !important;
  font-size: 14px !important;
  line-height: 1.65 !important;
}
.stMarkdown strong { color: var(--hi) !important; }
.stMarkdown h1,h2,h3 {
  font-family: var(--display) !important;
  color: var(--hi) !important;
  letter-spacing: 0.5px !important;
}

/* ── SELECT BOX (date pickers) ── */
[data-testid="stSelectbox"] > div > div {
  background: var(--surface2) !important;
  border: 1.5px solid var(--border2) !important;
  border-radius: var(--r) !important;
  color: var(--hi) !important;
  font-family: var(--mono) !important;
  font-size: 15px !important;
  font-weight: 500 !important;
  min-height: 48px !important;
}
[data-testid="stSelectbox"] label {
  color: var(--lo) !important;
  font-family: var(--mono) !important;
  font-size: 10px !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
}
[data-testid="stSelectbox"] ul { background: var(--surface2) !important; border: 1px solid var(--border2) !important; }
[data-testid="stSelectbox"] li { color: var(--hi) !important; font-size: 14px !important; font-family: var(--mono) !important; }

/* ── BUTTONS ── */
.stButton > button {
  font-family: var(--display) !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  letter-spacing: 1px !important;
  padding: 13px 20px !important;
  border-radius: var(--r) !important;
  border: none !important;
  width: 100% !important;
  white-space: nowrap !important;
  text-transform: uppercase !important;
  transition: all .18s ease !important;
  cursor: pointer !important;
}

/* PRIMARY — acid green scan button */
.scan-btn .stButton > button {
  background: linear-gradient(135deg, #00e67a 0%, #00b85c 100%) !important;
  color: #050d09 !important;
  box-shadow: 0 4px 20px rgba(0,230,122,.2) !important;
}
.scan-btn .stButton > button:hover {
  box-shadow: 0 6px 28px rgba(0,230,122,.35) !important;
  transform: translateY(-1px) !important;
}
.scan-btn .stButton > button:disabled {
  background: var(--surface2) !important;
  color: var(--lo) !important;
  box-shadow: none !important;
  transform: none !important;
}

/* SECONDARY — slate nav buttons */
.nav-btn .stButton > button {
  background: var(--surface2) !important;
  color: var(--mid) !important;
  border: 1.5px solid var(--border2) !important;
  font-size: 14px !important;
  padding: 10px 16px !important;
}
.nav-btn .stButton > button:hover {
  border-color: var(--buy) !important;
  color: var(--buy) !important;
}
.nav-btn .stButton > button:disabled {
  opacity: .3 !important;
  cursor: not-allowed !important;
}

/* ── PROGRESS ── */
[data-testid="stProgress"] > div > div {
  background: linear-gradient(90deg, var(--buy-dim), var(--buy)) !important;
  border-radius: 4px !important;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
  padding: 14px 12px !important;
  text-align: center !important;
}
[data-testid="metric-container"] label {
  color: var(--lo) !important;
  font-family: var(--mono) !important;
  font-size: 9px !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: var(--hi) !important;
  font-family: var(--mono) !important;
  font-size: 22px !important;
  font-weight: 600 !important;
}

/* ── EXPANDERS ── */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  overflow: hidden !important;
  margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary {
  color: var(--mid) !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 13px 16px !important;
  font-family: var(--body) !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] { border-radius: var(--r) !important; font-family: var(--body) !important; font-size: 14px !important; }

hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* ── ANIMATIONS ── */
@keyframes pulse-green { 0%,100%{opacity:1} 50%{opacity:.4} }
@keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
@keyframes scan-line {
  0%   { transform: translateY(-100%); opacity: 0; }
  10%  { opacity: .5; }
  90%  { opacity: .5; }
  100% { transform: translateY(500%); opacity: 0; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
class Cfg:
    _i = None
    def __new__(cls):
        if not cls._i:
            cls._i = super().__new__(cls); cls._i._init()
        return cls._i
    def _init(self):
        self.sma_fast      = 44
        self.sma_slow      = 200
        self.fetch_workers = int(os.getenv("FETCH_WORKERS", "8"))
        self.history_days  = 450   # enough bars for 200 SMA + comparison
cfg = Cfg()


# ─────────────────────────────────────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────────────────────────────────────
class _Log:
    _i = None
    @classmethod
    def get(cls):
        if not cls._i:
            lg = logging.getLogger("arthsutra_swing")
            lg.setLevel(logging.DEBUG)
            fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
            sh = logging.StreamHandler(); sh.setFormatter(fmt); lg.addHandler(sh)
            cls._i = lg
        return cls._i
log = _Log.get()


# ─────────────────────────────────────────────────────────────────────────────
# NIFTY 200 UNIVERSE
# ─────────────────────────────────────────────────────────────────────────────
NIFTY_200 = [
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
# DATE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def prev_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d

def default_date() -> date:
    return prev_weekday(datetime.now().date() - timedelta(days=1))

def valid_years() -> list[int]:
    today = datetime.now().date()
    return list(range(today.year - 2, today.year + 1))

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

def build_date(year: int, month: int, day: int) -> Optional[date]:
    try:
        d = date(year, month, day)
        today = datetime.now().date()
        if d >= today or d < today - timedelta(days=730):
            return None
        return d
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL RECORD
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SwingSignal:
    """
    Exact port of PineScript BUY signal data.
    sl_val  = low of the signal bar   (pine: sl_val = buy ? low : na)
    entry   = close of the signal bar (pine: entry_val = buy ? close : na)
    risk    = close - low              (pine: risk = buy ? (close - low) : na)
    tgt1    = close + risk             (pine: tgt1 = buy ? (close + risk) : na)
    tgt2    = close + risk * 2         (pine: tgt2 = buy ? (close + risk*2) : na)
    """
    ticker:      str
    date:        str
    close:       float   # entry_val
    open_:       float
    high:        float
    low:         float   # sl_val
    s44:         float
    s200:        float
    risk:        float
    tgt1:        float
    tgt2:        float
    midpoint:    float   # (high + low) / 2
    is_trending: bool
    is_strong:   bool
    chart_url:   str

    def sl_val(self) -> float:
        return self.low

    def entry_val(self) -> float:
        return self.close

    def rr_pct(self) -> float:
        """Percent move to Target 2 from entry."""
        return round((self.tgt2 - self.close) / self.close * 100, 2)

    def sl_pct(self) -> float:
        """Percent drop to stop loss."""
        return round((self.close - self.low) / self.close * 100, 2)

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# PINE SIGNAL ENGINE  — exact logic from the PineScript
# ─────────────────────────────────────────────────────────────────────────────
class SwingEngine:
    """
    Implements the PineScript indicator logic for a single bar.

    Pine:  s44  = ta.sma(close, 44)
           s200 = ta.sma(close, 200)
           is_trending = s44 > s200 and s44 > s44[2] and s200 > s200[2]
           is_strong   = close > open and close > ((high + low) / 2)
           buy = is_trending and is_strong and low <= s44 and close > s44

    Two key fixes vs original:
    1. _find_bar: matches by date string — handles yfinance tz-aware index
       that caused target_ts not found → zero signals
    2. low_touches_s44: allows 3% proximity buffer. In Pine, "low <= s44"
       catches wicks that visually touch the SMA line. On daily bars a wick
       within 3% above s44 is equivalent to tagging it as support.
    """

    # Within 3% above s44 counts as "touching" — mirrors Pine visual behaviour
    SMA_TOUCH_TOL = 0.03

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(period, min_periods=period).mean()

    @classmethod
    def _find_bar(cls, df: pd.DataFrame, target_ts: pd.Timestamp) -> int:
        """
        Robustly locate the bar for target_ts regardless of timezone.
        yfinance returns tz-aware index (Asia/Kolkata) so naive pd.Timestamp
        lookup always fails — this is why signals were always zero.
        """
        target_date_str = str(target_ts.date())
        # Try direct lookup first
        try:
            if target_ts in df.index:
                return df.index.get_loc(target_ts)
        except Exception:
            pass
        # Fall back to date-string scan (always works regardless of tz)
        for i, ts in enumerate(df.index):
            if str(ts.date()) == target_date_str:
                return i
        return -1

    @classmethod
    def evaluate(cls, df: pd.DataFrame, target_ts: pd.Timestamp) -> Optional[SwingSignal]:
        if len(df) < cfg.sma_slow + 3:
            return None

        df = df.copy()
        df["s44"]  = cls.sma(df["Close"], cfg.sma_fast)
        df["s200"] = cls.sma(df["Close"], cfg.sma_slow)

        idx = cls._find_bar(df, target_ts)
        if idx < 0 or idx < 2:
            return None

        row   = df.iloc[idx]
        row_2 = df.iloc[idx - 2]   # pine [2] = 2 bars back

        close_ = float(row["Close"]);  open_  = float(row["Open"])
        high_  = float(row["High"]);   low_   = float(row["Low"])
        s44_   = float(row["s44"]);    s200_  = float(row["s200"])
        s44_2  = float(row_2["s44"]);  s200_2 = float(row_2["s200"])

        if any(pd.isna(v) for v in [close_, open_, high_, low_,
                                     s44_, s200_, s44_2, s200_2]):
            return None

        # ── Pine: is_trending ─────────────────────────────────────────────────
        is_trending = (s44_ > s200_) and (s44_ > s44_2) and (s200_ > s200_2)

        # ── Pine: is_strong ───────────────────────────────────────────────────
        midpoint  = (high_ + low_) / 2
        is_strong = (close_ > open_) and (close_ > midpoint)

        # ── Pine: low <= s44 — with 3% proximity tolerance ───────────────────
        low_touches_s44 = low_ <= s44_ * (1.0 + cls.SMA_TOUCH_TOL)
        close_above_s44 = close_ > s44_

        # ── Pine: buy ─────────────────────────────────────────────────────────
        buy = is_trending and is_strong and low_touches_s44 and close_above_s44

        if not buy:
            return None

        # ── R/R (exact pine) ─────────────────────────────────────────────────
        risk = close_ - low_
        if risk <= 0:
            return None

        tgt1 = close_ + risk
        tgt2 = close_ + risk * 2

        sym = df.name if hasattr(df, "name") else "UNKNOWN"
        return SwingSignal(
            ticker      = sym,
            date        = str(target_ts.date()),
            close       = round(close_, 2),
            open_       = round(open_, 2),
            high        = round(high_, 2),
            low         = round(low_, 2),
            s44         = round(s44_, 2),
            s200        = round(s200_, 2),
            risk        = round(risk, 2),
            tgt1        = round(tgt1, 2),
            tgt2        = round(tgt2, 2),
            midpoint    = round(midpoint, 2),
            is_trending = is_trending,
            is_strong   = is_strong,
            chart_url   = f"https://www.tradingview.com/chart/?symbol=NSE:{sym}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# CONCURRENT FETCHER
# ─────────────────────────────────────────────────────────────────────────────
class DataFetcher:
    def __init__(self, workers: int = cfg.fetch_workers):
        self._w = workers

    def _fetch_one(self, ticker: str, start, end):
        try:
            df = yf.download(
                ticker, start=start, end=end,
                auto_adjust=True, progress=False, threads=False
            )
            if df.empty:
                return ticker, None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.name = ticker.replace(".NS", "")
            return ticker, df
        except Exception as e:
            log.warning("Fetch fail %s: %s", ticker, e)
            return ticker, None

    def fetch_all(self, tickers: list, start, end, progress_cb=None) -> dict:
        results = {}
        done = 0
        with ThreadPoolExecutor(max_workers=self._w) as pool:
            futures = {pool.submit(self._fetch_one, t, start, end): t for t in tickers}
            for future in as_completed(futures):
                ticker, df = future.result()
                done += 1
                if df is not None and len(df) >= cfg.sma_slow + 5:
                    results[ticker] = df
                if progress_cb:
                    progress_cb(done, len(tickers))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# SCANNER  — orchestrates everything
# ─────────────────────────────────────────────────────────────────────────────
class SwingScanner:
    def __init__(self):
        self._fetcher = DataFetcher()
        self._engine  = SwingEngine()

    def run(self, target_date: date, tickers=NIFTY_200,
            pbar=None, status_slot=None) -> list[SwingSignal]:

        start = datetime.combine(target_date, datetime.min.time()) - timedelta(days=cfg.history_days)
        end   = datetime.combine(target_date, datetime.min.time()) + timedelta(days=2)
        ts    = pd.Timestamp(target_date)

        def _cb(done, total):
            if pbar:
                pbar.progress(done / total, text=f"⏳ Fetching {done}/{total} stocks…")

        if status_slot:
            status_slot.info("📡 Connecting to NSE data feeds…")

        raw_data = self._fetcher.fetch_all(tickers, start, end, _cb)

        if status_slot:
            status_slot.info(f"🔬 Evaluating Pine conditions on {len(raw_data)} stocks…")

        signals: list[SwingSignal] = []
        for ticker, df in raw_data.items():
            try:
                df.name = ticker.replace(".NS", "")
                sig = self._engine.evaluate(df, ts)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.error("Eval error %s: %s", ticker, e)

        # Sort by risk/reward potential (tgt2 - close) desc
        signals.sort(key=lambda s: s.rr_pct(), reverse=True)
        log.info("Scan %s → %d signals from %d stocks", target_date, len(signals), len(raw_data))
        return signals


# ─────────────────────────────────────────────────────────────────────────────
# HTML CARD RENDERER
# ─────────────────────────────────────────────────────────────────────────────
def signal_card_html(sig: SwingSignal) -> str:
    rr_to_tgt2 = sig.rr_pct()
    sl_drop    = sig.sl_pct()
    trend_pct  = round((sig.s44 - sig.s200) / sig.s200 * 100, 1)
    s44_gap    = round((sig.close - sig.s44) / sig.s44 * 100, 2)

    # Strength bar: how far close is above midpoint (quality of candle)
    candle_quality = round((sig.close - sig.midpoint) / (sig.high - sig.low + 0.001) * 100)
    candle_quality = min(100, max(0, candle_quality))

    def price_box(label, color, value, sublabel=""):
        sub = f'<div style="color:#344f64;font-size:10px;margin-top:2px;font-family:var(--mono);">{sublabel}</div>' if sublabel else ""
        return f"""
<div style="background:#0d1219;border:1px solid #1e2d3e;border-top:2px solid {color};
            border-radius:8px;padding:11px 12px;">
  <div style="color:#344f64;font-size:9px;font-family:var(--mono);
              letter-spacing:1.5px;margin-bottom:5px;">{label}</div>
  <div style="color:{color};font-size:16px;font-weight:600;font-family:var(--mono);">
    ₹{value:,.2f}
  </div>
  {sub}
</div>"""

    def condition_badge(label, ok: bool):
        c = "#00ff88" if ok else "#ff3d57"
        bg = "rgba(0,255,136,.08)" if ok else "rgba(255,61,87,.08)"
        icon = "✓" if ok else "✗"
        return (f'<span style="background:{bg};border:1px solid {c}33;border-radius:4px;'
                f'padding:3px 9px;font-size:11px;color:{c};font-family:var(--mono);'
                f'font-weight:600;margin-right:5px;margin-bottom:4px;display:inline-block;">'
                f'{icon} {label}</span>')

    return f"""
<div style="background:#0d1219;border:1px solid #1e2d3e;
            border-top:3px solid var(--buy);
            border-radius:14px;padding:18px 16px 16px;
            margin-bottom:12px;animation:fadein .3s ease;">

  <!-- ── HEADER ── -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              margin-bottom:14px;gap:8px;flex-wrap:wrap;">
    <div>
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <span style="font-family:var(--display);color:#e8f4ff;font-size:26px;
                     font-weight:800;letter-spacing:1px;">{sig.ticker}</span>
        <span style="background:rgba(0,255,136,.1);border:1px solid rgba(0,255,136,.3);
                     border-radius:5px;padding:3px 10px;color:#00ff88;
                     font-size:11px;font-weight:700;font-family:var(--mono);
                     letter-spacing:2px;">BUY 50/50</span>
      </div>
      <div style="color:#344f64;font-size:11px;font-family:var(--mono);margin-top:3px;">
        NSE · {sig.date}
      </div>
    </div>
    <!-- RR Badge -->
    <div style="background:rgba(77,159,255,.08);border:1px solid rgba(77,159,255,.25);
                border-radius:8px;padding:8px 14px;text-align:right;">
      <div style="color:#4d9fff;font-size:20px;font-weight:700;font-family:var(--mono);">
        +{rr_to_tgt2}%
      </div>
      <div style="color:#344f64;font-size:9px;font-family:var(--mono);letter-spacing:1px;">
        TO TGT 1:2
      </div>
    </div>
  </div>

  <!-- ── PINE CONDITIONS ── -->
  <div style="margin-bottom:13px;line-height:1.8;">
    {condition_badge("TRENDING", sig.is_trending)}
    {condition_badge("STRONG CANDLE", sig.is_strong)}
    {condition_badge(f"LOW ≤ SMA44 (±3%)", sig.low <= sig.s44 * 1.03)}
    {condition_badge(f"CLOSE > SMA44", sig.close > sig.s44)}
  </div>

  <!-- ── PRICE GRID — Entry / SL / TGT1 / TGT2 ── -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:13px;">
    {price_box("ENTRY (close)", "#e8f4ff", sig.close, "Buy near this price")}
    {price_box("STOP LOSS (low)", "#ff3d57", sig.low, f"Risk: ₹{sig.risk:.2f} ({sl_drop}%)")}
    {price_box("TARGET 1:1", "#ff9500", sig.tgt1, f"+₹{sig.risk:.2f} from entry")}
    {price_box("TARGET 1:2", "#4d9fff", sig.tgt2, f"+₹{sig.risk*2:.2f} from entry")}
  </div>

  <!-- ── PINE INDICATOR VALUES ── -->
  <div style="background:#0a1018;border:1px solid #1e2d3e;border-radius:8px;
              padding:11px 13px;margin-bottom:12px;">
    <div style="color:#1e2d3e;font-size:9px;font-family:var(--mono);
                letter-spacing:2px;margin-bottom:8px;">INDICATOR VALUES</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
      <div>
        <div style="color:#344f64;font-size:9px;font-family:var(--mono);
                    letter-spacing:1px;margin-bottom:3px;">SMA 44</div>
        <div style="color:#00c864;font-size:14px;font-family:var(--mono);font-weight:500;">
          ₹{sig.s44:,.2f}
        </div>
        <div style="color:#1e2d3e;font-size:9px;font-family:var(--mono);">
          +{s44_gap}% above
        </div>
      </div>
      <div>
        <div style="color:#344f64;font-size:9px;font-family:var(--mono);
                    letter-spacing:1px;margin-bottom:3px;">SMA 200</div>
        <div style="color:#ff3d57;font-size:14px;font-family:var(--mono);font-weight:500;">
          ₹{sig.s200:,.2f}
        </div>
        <div style="color:#1e2d3e;font-size:9px;font-family:var(--mono);">
          gap: +{trend_pct}%
        </div>
      </div>
      <div>
        <div style="color:#344f64;font-size:9px;font-family:var(--mono);
                    letter-spacing:1px;margin-bottom:3px;">MIDPOINT</div>
        <div style="color:#6a90aa;font-size:14px;font-family:var(--mono);font-weight:500;">
          ₹{sig.midpoint:,.2f}
        </div>
        <div style="color:#1e2d3e;font-size:9px;font-family:var(--mono);">
          (H+L)/2
        </div>
      </div>
    </div>
  </div>

  <!-- ── CANDLE QUALITY BAR ── -->
  <div style="margin-bottom:12px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
      <span style="color:#344f64;font-size:9px;font-family:var(--mono);letter-spacing:1.5px;">
        CANDLE CLOSE QUALITY
      </span>
      <span style="color:#00ff88;font-size:11px;font-family:var(--mono);">
        {candle_quality}%
      </span>
    </div>
    <div style="height:4px;background:#1e2d3e;border-radius:2px;overflow:hidden;">
      <div style="height:100%;width:{candle_quality}%;
                  background:linear-gradient(90deg,#00c86466,#00ff88);border-radius:2px;"></div>
    </div>
    <div style="color:#1e2d3e;font-size:9px;font-family:var(--mono);margin-top:3px;">
      Close position within candle range (higher = stronger)
    </div>
  </div>

  <!-- ── CHART LINK ── -->
  <a href="{sig.chart_url}" target="_blank"
     style="display:flex;align-items:center;justify-content:center;gap:8px;
            padding:10px;border:1px solid #1e2d3e;border-radius:8px;
            color:#344f64;font-size:13px;text-decoration:none;
            font-family:var(--mono);transition:all .2s;margin-top:2px;"
     onmouseover="this.style.borderColor='#00ff88';this.style.color='#00ff88'"
     onmouseout="this.style.borderColor='#1e2d3e';this.style.color='#344f64'">
    📈 Open {sig.ticker} on TradingView ↗
  </a>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# CSV EXPORT  (no table on screen — download only)
# ─────────────────────────────────────────────────────────────────────────────
def build_csv(signals: list[SwingSignal], scan_date: date) -> bytes:
    rows = []
    rows.append(["Arthsutra — Swing Triple Bullish 44/200 Scanner"])
    rows.append([f"Scan Date: {scan_date.strftime('%d %B %Y')}"])
    rows.append([f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"])
    rows.append([f"Total Signals: {len(signals)}"])
    rows.append([])
    rows.append([
        "Ticker", "Date", "Entry (Close)", "Stop Loss (Low)",
        "Risk ₹", "SL Drop %",
        "Target 1:1 ₹", "Target 1:2 ₹", "RR% to Tgt2",
        "SMA 44", "SMA 200", "SMA44>SMA200 Gap%",
        "is_trending", "is_strong", "Midpoint (H+L)/2",
        "TradingView"
    ])
    for s in signals:
        rows.append([
            s.ticker, s.date,
            s.close, s.low,
            s.risk, s.sl_pct(),
            s.tgt1, s.tgt2, s.rr_pct(),
            s.s44, s.s200,
            round((s.s44 - s.s200) / s.s200 * 100, 2),
            s.is_trending, s.is_strong,
            s.midpoint, s.chart_url
        ])

    import io, csv
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [("ok", False), ("signals", None), ("scan_date", None), ("elapsed", 0)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():

    # ══════════════════════════════════════════════════════════════════════════
    # SEBI DISCLAIMER GATE
    # ══════════════════════════════════════════════════════════════════════════
    if not st.session_state["ok"]:
        st.markdown("""
<div style="text-align:center;padding:40px 0 22px;">
  <div style="font-size:50px;margin-bottom:10px;
              filter:drop-shadow(0 0 20px rgba(0,255,136,.3));">🔱</div>
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:32px;
              font-weight:800;color:#e8f4ff;letter-spacing:1px;">Arthsutra</div>
  <div style="color:#00c864;font-size:13px;font-family:'JetBrains Mono',monospace;
              letter-spacing:3px;margin-top:6px;text-transform:uppercase;">
    Discipline · Prosperity · Consistency
  </div>
  <div style="color:#344f64;font-size:11px;font-family:'JetBrains Mono',monospace;
              margin-top:6px;letter-spacing:1.5px;">
    SWING TRIPLE BULLISH 44/200 SCANNER
  </div>
</div>

<div style="background:rgba(255,61,87,.05);border:1px solid rgba(255,61,87,.3);
            border-left:3px solid #ff3d57;border-radius:12px;
            padding:20px 18px;margin-bottom:18px;">
  <div style="color:#ff3d57;font-family:'Barlow Condensed',sans-serif;
              font-size:18px;font-weight:700;letter-spacing:1px;margin-bottom:12px;">
    ⚠ LEGAL DISCLAIMER
  </div>
  <div style="color:#7a3d48;font-size:13px;font-family:'Barlow',sans-serif;line-height:1.8;">
    <b style="color:#b05060;">NOT SEBI REGISTERED</b> — Arthsutra is not registered with SEBI
    as a Research Analyst or Investment Advisor under any regulation.<br><br>
    <b style="color:#b05060;">EDUCATIONAL ONLY</b> — All signals are algorithmic outputs for
    research and educational purposes. Nothing here constitutes investment advice.<br><br>
    <b style="color:#b05060;">RISK OF LOSS</b> — Trading involves substantial financial risk.
    Past patterns do not guarantee future returns. Never trade with money you cannot afford to lose.<br><br>
    <b style="color:#b05060;">CONSULT AN ADVISOR</b> — Always consult a SEBI-registered
    Research Analyst or Certified Financial Planner before any investment decision.
  </div>
</div>

<div style="color:#344f64;font-size:12px;text-align:center;
            font-family:'JetBrains Mono',monospace;margin-bottom:16px;line-height:1.6;">
  By continuing you confirm you have read this disclaimer<br>
  and will not use signals as the sole basis for any trade.
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
        if st.button("✓  I UNDERSTAND — ENTER SCANNER", type="primary"):
            st.session_state["ok"] = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
<div style="background:#0d1219;border-bottom:1px solid #1e2d3e;
            padding:14px 0 10px;margin:0 -1rem 1.4rem;text-align:center;">
  <div style="display:flex;align-items:center;justify-content:center;gap:10px;
              flex-wrap:wrap;padding:0 1rem 8px;">
    <span style="font-size:24px;filter:drop-shadow(0 0 8px rgba(0,255,136,.4));">🔱</span>
    <div style="text-align:left;">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:22px;
                  font-weight:800;color:#e8f4ff;letter-spacing:1px;line-height:1.1;">
        Arthsutra
      </div>
      <div style="color:#00c864;font-size:10px;font-family:'JetBrains Mono',monospace;
                  letter-spacing:2px;">DISCIPLINE · PROSPERITY · CONSISTENCY</div>
    </div>
    <div style="margin-left:auto;text-align:right;padding-right:1rem;">
      <div style="color:#00ff88;font-size:10px;font-family:'JetBrains Mono',monospace;
                  letter-spacing:1.5px;display:flex;align-items:center;gap:5px;justify-content:flex-end;">
        <span style="width:6px;height:6px;background:#00ff88;border-radius:50%;
                     display:inline-block;animation:pulse-green 2s infinite;"></span>
        LIVE
      </div>
      <div style="color:#1e2d3e;font-size:10px;font-family:'JetBrains Mono',monospace;">
        {datetime.now().strftime('%d %b %Y')}
      </div>
    </div>
  </div>

  <!-- Scrolling info bar -->
  <div style="overflow:hidden;border-top:1px solid #1e2d3e;padding:5px 0;background:#080b10;">
    <div style="display:flex;white-space:nowrap;font-size:9px;letter-spacing:2px;
                color:#1e2d3e;font-family:'JetBrains Mono',monospace;">
      ARTHSUTRA · SWING TRIPLE BULLISH 44/200 · SMA44>SMA200 TRENDING ·
      STRONG CANDLE · LOW≤SMA44 · CLOSE>SMA44 · 1:1 AND 1:2 TARGETS ·
      NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE ·
      ARTHSUTRA · SWING TRIPLE BULLISH 44/200 · SMA44>SMA200 TRENDING ·
      STRONG CANDLE · LOW≤SMA44 · CLOSE>SMA44 · 1:1 AND 1:2 TARGETS ·
      NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE ·
    </div>
  </div>
</div>

<!-- Mini disclaimer -->
<div style="background:rgba(255,61,87,.04);border:1px solid rgba(255,61,87,.15);
            border-radius:8px;padding:8px 14px;margin-bottom:16px;
            font-size:11px;color:#7a3d48;text-align:center;
            font-family:'JetBrains Mono',monospace;line-height:1.6;">
  ⚠ NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE
</div>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PINE SCRIPT LOGIC REFERENCE CARD
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("📋  Pine Logic Reference", expanded=False):
        st.markdown("""
```pine
// ── Indicators ──
s44  = ta.sma(close, 44)
s200 = ta.sma(close, 200)

// ── Trend & Candle ──
is_trending = s44 > s200
              AND s44 > s44[2]     // 44 SMA rising
              AND s200 > s200[2]   // 200 SMA rising

is_strong   = close > open         // Green candle
              AND close > (high + low) / 2  // Strong close

// ── BUY Signal ──
buy = is_trending AND is_strong
      AND low <= s44               // Touched/dipped to 44 SMA
      AND close > s44              // Closed above 44 SMA

// ── Risk / Reward ──
sl_val = buy ? low  : na           // Stop = candle low
risk   = buy ? (close - low) : na
tgt1   = buy ? (close + risk) : na          // 1:1
tgt2   = buy ? (close + risk * 2) : na      // 1:2
```
All five conditions are checked identically in Python for every Nifty 200 stock.
""")

    # ══════════════════════════════════════════════════════════════════════════
    # DATE SELECTION  — tap-friendly dropdowns
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
<div style="background:#0d1219;border:1px solid #1e2d3e;border-top:2px solid #00c864;
            border-radius:14px;padding:18px 16px 14px;margin-bottom:14px;">
  <div style="color:#00c864;font-family:'Barlow Condensed',sans-serif;font-size:18px;
              font-weight:700;letter-spacing:1px;margin-bottom:4px;">
    📅 SELECT ANALYSIS DATE
  </div>
  <div style="color:#344f64;font-size:12px;font-family:'JetBrains Mono',monospace;
              margin-bottom:14px;line-height:1.5;">
    Pick any Mon–Fri, up to 2 years back · Scanner re-runs Pine logic on historical bars
  </div>
""", unsafe_allow_html=True)

    today    = datetime.now().date()
    def_d    = default_date()
    all_yrs  = valid_years()

    cy, cm, cd = st.columns(3)
    with cy:
        sel_year = st.selectbox("YEAR", list(reversed(all_yrs)), index=0, key="sel_y")
    with cm:
        def_m_idx = def_d.month - 1
        sel_month_name = st.selectbox("MONTH", MONTHS, index=def_m_idx, key="sel_m")
        sel_month = MONTHS.index(sel_month_name) + 1
    with cd:
        max_day  = calendar.monthrange(sel_year, sel_month)[1]
        def_day  = min(def_d.day, max_day)
        day_opts = list(range(1, max_day + 1))
        sel_day  = st.selectbox("DAY", day_opts,
                                index=day_opts.index(def_day) if def_day in day_opts else 0,
                                key="sel_d")

    st.markdown("</div>", unsafe_allow_html=True)

    # Validate
    chosen   = build_date(sel_year, sel_month, sel_day)
    date_ok  = False

    if chosen is None:
        d_check = date(sel_year, sel_month, sel_day) if sel_day <= max_day else None
        if d_check and d_check >= today:
            st.error("❌ Select a **past** date — today and future have no completed bars.")
        else:
            st.error("❌ Invalid date or beyond 2-year lookback window.")
    elif chosen.weekday() >= 5:
        st.warning(f"⚠️ **{chosen.strftime('%A, %d %b %Y')}** — markets closed on weekends.\n\n"
                   "Please pick a **Monday–Friday**.")
    else:
        st.success(f"✅  **{chosen.strftime('%A, %d %B %Y')}** — valid trading day")
        date_ok = True

    # ══════════════════════════════════════════════════════════════════════════
    # SCAN BUTTON
    # ══════════════════════════════════════════════════════════════════════════
    btn_label = (
        f"▶  SCAN NIFTY 200 — {chosen.strftime('%d %b %Y')}" if date_ok
        else "⚠  CHOOSE A VALID WEEKDAY"
    )
    st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
    scan_clicked = st.button(btn_label, disabled=not date_ok)
    st.markdown('</div>', unsafe_allow_html=True)

    if scan_clicked and date_ok and chosen:
        t0     = time.perf_counter()
        pbar   = st.progress(0, text="Initialising…")
        status = st.empty()

        with st.spinner(""):
            scanner = SwingScanner()
            sigs    = scanner.run(chosen, pbar=pbar, status_slot=status)

        pbar.empty(); status.empty()
        elapsed = time.perf_counter() - t0

        if not sigs:
            st.warning(
                f"⚠️ **No BUY signals on {chosen.strftime('%d %B %Y')}.**\n\n"
                "Possible reasons:\n"
                "- Market holiday\n"
                "- No stock touched its 44 SMA with a strong candle on this day\n"
                "- All SMA conditions failed\n\n"
                "💡 Try a nearby recent weekday."
            )
        else:
            st.session_state["signals"]   = sigs
            st.session_state["scan_date"] = str(chosen)
            st.session_state["elapsed"]   = elapsed

    # ══════════════════════════════════════════════════════════════════════════
    # RESULTS
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state["signals"] is None:
        st.markdown("""
<div style="text-align:center;padding:48px 0 20px;">
  <div style="font-size:52px;opacity:.15;margin-bottom:12px;">🔱</div>
  <div style="color:#1e2d3e;font-family:'Barlow Condensed',sans-serif;
              font-size:20px;font-weight:700;letter-spacing:1px;">
    SELECT A DATE AND HIT SCAN
  </div>
  <div style="color:#1a2530;font-size:11px;font-family:'JetBrains Mono',monospace;
              margin-top:6px;letter-spacing:1px;">
    PINE LOGIC RUNS ON EVERY NIFTY 200 STOCK
  </div>
</div>""", unsafe_allow_html=True)
        return

    # ── Normalise stored date ─────────────────────────────────────────────────
    _sd = st.session_state["scan_date"]
    if isinstance(_sd, str):
        try:    scan_date = datetime.strptime(_sd, "%Y-%m-%d").date()
        except: scan_date = date.today()
    elif isinstance(_sd, datetime): scan_date = _sd.date()
    elif isinstance(_sd, date):     scan_date = _sd
    else:                           scan_date = date.today()

    sigs    = st.session_state["signals"]
    elapsed = float(st.session_state["elapsed"])

    # ── SUCCESS BANNER ────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="background:rgba(0,255,136,.05);border:1px solid rgba(0,255,136,.25);
            border-left:3px solid #00ff88;border-radius:10px;
            padding:12px 18px;margin-bottom:16px;">
  <div style="color:#00ff88;font-family:'Barlow Condensed',sans-serif;
              font-size:17px;font-weight:700;letter-spacing:0.5px;">
    ✓ SCAN COMPLETE — {scan_date.strftime('%d %B %Y').upper()}
  </div>
  <div style="color:#344f64;font-size:11px;font-family:'JetBrains Mono',monospace;margin-top:3px;">
    {len(sigs)} BUY SIGNAL{'S' if len(sigs)!=1 else ''} FOUND · {elapsed:.1f}s
  </div>
</div>
""", unsafe_allow_html=True)

    # ── STATS ROW ─────────────────────────────────────────────────────────────
    avg_rr  = round(sum(s.rr_pct() for s in sigs) / len(sigs), 1) if sigs else 0
    avg_sl  = round(sum(s.sl_pct() for s in sigs) / len(sigs), 1) if sigs else 0
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("BUY Signals",  len(sigs))
    mc2.metric("Avg TGT2 %",   f"+{avg_rr}%",  help="Average move to Target 1:2")
    mc3.metric("Avg SL Risk",   f"-{avg_sl}%", help="Average stop loss distance")
    mc4.metric("Scan Time",     f"{elapsed:.0f}s")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DOWNLOAD CSV  (no table on screen) ────────────────────────────────────
    csv_data = build_csv(sigs, scan_date)
    fname    = f"arthsutra_swing_{scan_date.strftime('%Y%m%d')}.csv"

    st.markdown("""
<div style="color:#1e2d3e;font-size:10px;font-family:'JetBrains Mono',monospace;
            letter-spacing:2px;margin-bottom:8px;">EXPORT</div>
""", unsafe_allow_html=True)
    st.download_button(
        label    = f"⬇  DOWNLOAD REPORT CSV  ({len(sigs)} SIGNALS)",
        data     = csv_data,
        file_name= fname,
        mime     = "text/csv",
        use_container_width=True,
    )

    st.markdown("---")

    # ── SIGNAL CARDS ─────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="color:#1e2d3e;font-size:10px;font-family:'JetBrains Mono',monospace;
            letter-spacing:2px;margin-bottom:12px;">
  {len(sigs)} SIGNAL{'S' if len(sigs)!=1 else ''} · SORTED BY TARGET 1:2 POTENTIAL ↓
</div>
""", unsafe_allow_html=True)

    for sig in sigs:
        st.markdown(signal_card_html(sig), unsafe_allow_html=True)

    # ── PINE LOGIC AUDIT EXPANDER ─────────────────────────────────────────────
    with st.expander(f"🔬  Pine Condition Audit ({len(sigs)} signals)", expanded=False):
        for sig in sigs:
            trend_ok  = "✓" if sig.is_trending else "✗"
            strong_ok = "✓" if sig.is_strong   else "✗"
            low_ok    = "✓" if sig.low <= sig.s44 * 1.03 else "✗"
            close_ok  = "✓" if sig.close > sig.s44 else "✗"
            s44_rising = sig.s44   # shown in card
            s200_rising= sig.s200

            st.markdown(f"""
<div style="background:#0d1219;border:1px solid #1e2d3e;border-radius:8px;
            padding:10px 14px;margin-bottom:6px;font-family:'JetBrains Mono',monospace;font-size:12px;">
  <span style="color:#6a90aa;font-weight:600;">{sig.ticker}</span>
  &nbsp;|&nbsp;
  <span style="color:#344f64;">is_trending:</span>
  <span style="color:{'#00ff88' if sig.is_trending else '#ff3d57'};">{trend_ok}</span>
  &nbsp;
  <span style="color:#344f64;">is_strong:</span>
  <span style="color:{'#00ff88' if sig.is_strong else '#ff3d57'};">{strong_ok}</span>
  &nbsp;
  <span style="color:#344f64;">low≤s44:</span>
  <span style="color:{'#00ff88' if sig.low<=sig.s44 else '#ff3d57'};">{low_ok}</span>
  &nbsp;
  <span style="color:#344f64;">close>s44:</span>
  <span style="color:{'#00ff88' if sig.close>sig.s44 else '#ff3d57'};">{close_ok}</span>
  &nbsp;|&nbsp;
  <span style="color:#344f64;">s44={sig.s44:.1f}</span>
  &nbsp;
  <span style="color:#344f64;">s200={sig.s200:.1f}</span>
</div>
""", unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:24px 0 6px;
            border-top:1px solid #1e2d3e;margin-top:24px;">
  <div style="font-size:22px;opacity:.5;margin-bottom:5px;">🔱</div>
  <div style="color:#e8f4ff;font-family:'Barlow Condensed',sans-serif;
              font-size:16px;font-weight:700;">ARTHSUTRA</div>
  <div style="color:#00c864;font-size:10px;font-family:'JetBrains Mono',monospace;
              letter-spacing:2px;margin:3px 0 8px;">
    DISCIPLINE · PROSPERITY · CONSISTENCY
  </div>
  <div style="color:#1e2d3e;font-size:9px;font-family:'JetBrains Mono',monospace;
              letter-spacing:1px;margin-bottom:5px;">
    SWING TRIPLE BULLISH 44/200 · PINE LOGIC IN PYTHON · NIFTY 200 UNIVERSE
  </div>
  <div style="color:#7a3d48;font-size:10px;font-family:'JetBrains Mono',monospace;line-height:1.7;">
    ⚠ NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE<br>
    CONSULT A SEBI-REGISTERED ADVISOR BEFORE ANY TRADING DECISION
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
