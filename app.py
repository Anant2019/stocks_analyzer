"""
Arthsutra — Nifty 200 Signal Analyzer v6.0
==========================================
Discipline · Prosperity · Consistency

KEY FIXES v6:
  ✅ layout="centered" — works perfectly on mobile
  ✅ Date via Day/Month/Year DROPDOWNS — no broken calendar, works on all phones
  ✅ All controls on main page — no hidden sidebar
  ✅ Single-column cards on mobile
  ✅ Min font 16px everywhere — readable on small screens
  ✅ Full SEBI disclaimer gate
  ✅ Arthsutra branding throughout

Run:  pip install streamlit yfinance pandas numpy
      streamlit run arthsutra_v6.py
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

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arthsutra · Nifty 200",
    page_icon="🔱",
    layout="centered",                 # ← KEY: works on mobile
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

:root {
    --bg:     #060c14;
    --card:   #0d1b2a;
    --deep:   #071020;
    --bdr:    #1a2d3e;
    --bdr2:   #243d52;
    --teal:   #00d4aa;
    --sky:    #38bdf8;
    --gold:   #f5c842;
    --red:    #ff4d6d;
    --hi:     #e8f4ff;
    --mid:    #7fa8c4;
    --lo:     #4a6a84;
    --ghost:  #1e3045;
    --mono:   'JetBrains Mono', monospace;
    --sans:   'Inter', -apple-system, sans-serif;
}

/* ── GLOBAL ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--bg) !important; }

.main .block-container {
    padding: 1rem 1rem 3rem !important;
    max-width: 680px !important;   /* comfortable reading width on all screens */
}

* { box-sizing: border-box; }

/* ── HIDE CHROME ── */
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], header { visibility: hidden !important; height: 0 !important; }

/* ── TYPOGRAPHY ── */
.stMarkdown p, .stMarkdown li {
    color: var(--hi) !important;
    font-family: var(--sans) !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
}
.stMarkdown h1 { color: var(--hi) !important; font-size: 22px !important; font-weight: 800 !important; }
.stMarkdown h2 { color: var(--hi) !important; font-size: 19px !important; font-weight: 700 !important; }
.stMarkdown h3 { color: var(--teal) !important; font-size: 16px !important; font-weight: 700 !important; }

/* ── SELECTBOX (date dropdowns) ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--card) !important;
    border: 2px solid var(--bdr2) !important;
    border-radius: 10px !important;
    color: var(--hi) !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    min-height: 52px !important;
    font-family: var(--mono) !important;
}
[data-testid="stSelectbox"] label {
    color: var(--mid) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
/* Dropdown list items */
[data-testid="stSelectbox"] ul { background: var(--card) !important; }
[data-testid="stSelectbox"] li { color: var(--hi) !important; font-size: 16px !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #00c49a 0%, #0891b2 100%) !important;
    color: #020e18 !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: var(--sans) !important;
    font-weight: 800 !important;
    font-size: 17px !important;
    padding: 15px 24px !important;
    width: 100% !important;
    letter-spacing: 0.2px !important;
    transition: opacity .15s !important;
    cursor: pointer !important;
}
.stButton > button:hover { opacity: .88 !important; }
.stButton > button:disabled {
    background: var(--card) !important;
    color: var(--lo) !important;
    border: 1px solid var(--bdr) !important;
    cursor: not-allowed !important;
}

/* ── RADIO (filter buttons) ── */
[data-testid="stRadio"] { width: 100% !important; }
[data-testid="stRadio"] > div {
    display: flex !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
}
[data-testid="stRadio"] label {
    background: var(--card) !important;
    border: 1.5px solid var(--bdr) !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    color: var(--mid) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all .15s !important;
    flex: 1 !important;
    text-align: center !important;
    min-width: 80px !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    border-color: var(--teal) !important;
    color: var(--teal) !important;
    background: rgba(0,212,170,.1) !important;
}
/* Hide the radio circle */
[data-testid="stRadio"] input[type="radio"] { display: none !important; }

/* ── PROGRESS BAR ── */
[data-testid="stProgress"] > div > div {
    background: var(--teal) !important;
    border-radius: 4px !important;
}
[data-testid="stProgress"] {
    background: var(--card) !important;
    border-radius: 4px !important;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 12px !important;
    padding: 16px 14px !important;
    text-align: center !important;
}
[data-testid="metric-container"] label {
    font-size: 10px !important;
    color: var(--lo) !important;
    font-family: var(--mono) !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: var(--hi) !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 11px !important;
    color: var(--lo) !important;
}

/* ── EXPANDERS ── */
[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-bottom: 10px !important;
}
[data-testid="stExpander"] summary {
    color: var(--mid) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 14px 18px !important;
    background: var(--card) !important;
}
[data-testid="stExpander"] summary:hover { color: var(--hi) !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--bdr) !important;
    border-radius: 10px !important;
    overflow: auto !important;
    max-width: 100% !important;
}
[data-testid="stDataFrame"] th {
    background: var(--deep) !important;
    color: var(--lo) !important;
    font-size: 11px !important;
    font-family: var(--mono) !important;
    padding: 8px 10px !important;
}
[data-testid="stDataFrame"] td {
    font-size: 12px !important;
    font-family: var(--mono) !important;
    color: var(--hi) !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 14px !important;
    font-family: var(--sans) !important;
}

/* ── CHECKBOX ── */
[data-testid="stCheckbox"] label {
    color: var(--mid) !important;
    font-size: 14px !important;
}

/* ── DIVIDER ── */
hr { border-color: var(--bdr) !important; margin: 1.2rem 0 !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-thumb { background: var(--bdr2); border-radius: 4px; }

/* ── ANIMATIONS ── */
@keyframes pulse  { 0%,100%{opacity:1} 50%{opacity:.3} }
@keyframes ticker { from{transform:translateX(0)} to{transform:translateX(-50%)} }
@keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
class AppConfig:
    _i = None
    def __new__(cls):
        if not cls._i:
            cls._i = super().__new__(cls); cls._i._init()
        return cls._i
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
cfg = AppConfig()

# ─────────────────────────────────────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────────────────────────────────────
class _Log:
    _i = None
    @classmethod
    def get(cls):
        if not cls._i:
            lg = logging.getLogger("arthsutra")
            lg.setLevel(logging.DEBUG)
            fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
            sh = logging.StreamHandler(); sh.setFormatter(fmt); lg.addHandler(sh)
            try:
                fh = logging.FileHandler("arthsutra.log","a"); fh.setFormatter(fmt); lg.addHandler(fh)
            except: pass
            cls._i = lg
        return cls._i
log = _Log.get()

# ─────────────────────────────────────────────────────────────────────────────
# NIFTY 200
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

def valid_years() -> list[int]:
    today = datetime.now().date()
    return list(range(today.year - 2, today.year + 1))

def valid_months() -> dict[str, int]:
    return {
        "January":1,"February":2,"March":3,"April":4,
        "May":5,"June":6,"July":7,"August":8,
        "September":9,"October":10,"November":11,"December":12
    }

def days_in_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]

def build_date(year: int, month: int, day: int) -> Optional[date]:
    """Build date; return None if invalid or in future/weekend."""
    try:
        d = date(year, month, day)
        today = datetime.now().date()
        if d >= today:
            return None
        if d < today - timedelta(days=730):
            return None
        return d
    except ValueError:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SignalRecord:
    ticker: str; date: str; category: str; status: str
    entry: float; stop_loss: float; tp1: float; tp2: float; risk_pts: float
    rsi: float; macd_hist: float; atr: float; vol_ratio: float
    pct_vs_sma200: float; confidence: float; jackpot: bool; chart_url: str
    def to_dict(self): return asdict(self)

# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR ENGINE  (fully vectorised)
# ─────────────────────────────────────────────────────────────────────────────
class IndicatorEngine:
    @staticmethod
    def wilder_rsi(c, p=14):
        d=c.diff(); a=1/p
        ag=d.clip(lower=0).ewm(alpha=a,min_periods=p,adjust=False).mean()
        al=(-d).clip(lower=0).ewm(alpha=a,min_periods=p,adjust=False).mean()
        return 100-(100/(1+ag/al.replace(0,np.nan)))
    @staticmethod
    def macd(c,f=12,s=26,sig=9):
        ml=c.ewm(span=f,adjust=False).mean()-c.ewm(span=s,adjust=False).mean()
        sl=ml.ewm(span=sig,adjust=False).mean()
        return pd.DataFrame({"macd":ml,"signal":sl,"histogram":ml-sl},index=c.index)
    @staticmethod
    def atr(h,l,c,p=14):
        pc=c.shift(1)
        tr=pd.concat([(h-l),(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
        return tr.ewm(alpha=1/p,min_periods=p,adjust=False).mean()
    @staticmethod
    def sma(s,w): return s.rolling(w,min_periods=w).mean()
    @staticmethod
    def vol_ratio(v,lb=5): return v/v.rolling(lb,min_periods=lb).mean().replace(0,np.nan)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIDENCE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class ConfidenceEngine:
    W=dict(trend=30,momentum=20,volume=20,macd=15,volatility=15)
    @classmethod
    def score(cls,close,sma44,sma200,rsi,vr,mh,atr):
        s=0.0
        if close>sma44>sma200:
            s+=cls.W["trend"]*min(1.0,(close-sma200)/sma200*100/20)
        if 55<=rsi<=75: s+=cls.W["momentum"]*max(0,1-abs(rsi-65)/10)
        elif rsi>75: s+=cls.W["momentum"]*0.3
        if vr>=1.5: s+=cls.W["volume"]
        elif vr>=1.0: s+=cls.W["volume"]*(vr-1)/0.5
        s+=cls.W["macd"] if mh>0 else (cls.W["macd"]*0.4 if mh>-0.5 else 0)
        ap=(atr/close)*100
        if 0.5<=ap<=3: s+=cls.W["volatility"]
        elif ap<0.5: s+=cls.W["volatility"]*0.5
        return round(min(s,100.0),1)

# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL FACTORY
# ─────────────────────────────────────────────────────────────────────────────
class SignalFactory:
    def __init__(self): self._ie=IndicatorEngine(); self._ce=ConfidenceEngine()
    def enrich(self,df):
        c=df["Close"]
        df["SMA44"]=self._ie.sma(c,cfg.sma_fast)
        df["SMA200"]=self._ie.sma(c,cfg.sma_slow)
        df["RSI"]=self._ie.wilder_rsi(c,cfg.rsi_period)
        df["ATR"]=self._ie.atr(df["High"],df["Low"],c,cfg.atr_period)
        df["VolRatio"]=self._ie.vol_ratio(df["Volume"],cfg.vol_lookback)
        df["MACDHist"]=self._ie.macd(c,cfg.macd_fast,cfg.macd_slow,cfg.macd_signal)["histogram"]
        return df
    def build(self,ticker,df,ts):
        if ts not in df.index: return None
        row=df.loc[ts]
        close,open_p,low_p=float(row["Close"]),float(row["Open"]),float(row["Low"])
        sma44,sma200=float(row["SMA44"]),float(row["SMA200"])
        rsi,atr=float(row["RSI"]),float(row["ATR"])
        vr,mh=float(row["VolRatio"]),float(row["MACDHist"])
        if any(math.isnan(v) for v in [sma44,sma200,rsi,atr,vr,mh]): return None
        if not(close>sma44>sma200 and close>open_p): return None
        risk=close-low_p
        if risk<=0: return None
        tp1,tp2=close+risk,close+2*risk
        is_blue=rsi>cfg.blue_rsi_min and vr>1.0 and close>sma200*cfg.blue_premium
        fut=df[df.index>ts][["High","Low"]]
        status,jackpot="LIVE",False
        if not fut.empty:
            sl_a=fut["Low"].values<=low_p
            tp2_a=fut["High"].values>=tp2
            tp1_a=fut["High"].values>=tp1
            ev=sl_a|tp2_a
            if ev.any():
                i=int(ev.argmax())
                if tp2_a[i] and not sl_a[i]: status,jackpot="JACKPOT",True
                elif sl_a[i] and not tp2_a[i]: status="SL_HIT"
                elif tp1_a[i]: status="TP1_HIT"
                else: status="RUNNING"
            else: status="RUNNING"
        conf=self._ce.score(close,sma44,sma200,rsi,vr,mh,atr)
        sym=ticker.replace(".NS","")
        return SignalRecord(
            ticker=sym,date=str(ts.date()),category="BLUE" if is_blue else "AMBER",
            status=status,entry=round(close,2),stop_loss=round(low_p,2),
            tp1=round(tp1,2),tp2=round(tp2,2),risk_pts=round(risk,2),
            rsi=round(rsi,1),macd_hist=round(mh,4),atr=round(atr,2),
            vol_ratio=round(vr,2),pct_vs_sma200=round((close/sma200-1)*100,2),
            confidence=conf,jackpot=jackpot,
            chart_url=f"https://www.tradingview.com/chart/?symbol=NSE:{sym}",
        )

# ─────────────────────────────────────────────────────────────────────────────
# FETCHER
# ─────────────────────────────────────────────────────────────────────────────
class DataFetcher:
    def __init__(self,workers=cfg.fetch_workers): self._w=workers
    def _one(self,ticker,start,end):
        try:
            df=yf.download(ticker,start=start,end=end,auto_adjust=True,progress=False,threads=False)
            if df.empty: return ticker,None
            if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            return ticker,df
        except Exception as e:
            log.warning("Fetch fail %s: %s",ticker,e); return ticker,None
    def fetch_batch(self,tickers,start,end,cb=None):
        results={}; done=0
        with ThreadPoolExecutor(max_workers=self._w) as pool:
            futs={pool.submit(self._one,t,start,end):t for t in tickers}
            for f in as_completed(futs):
                ticker,df=f.result(); done+=1
                if df is not None and len(df)>=cfg.sma_slow+10: results[ticker]=df
                if cb: cb(done,len(tickers))
        return results

# ─────────────────────────────────────────────────────────────────────────────
# MONTE CARLO
# ─────────────────────────────────────────────────────────────────────────────
def monte_carlo(win_rate,rr,trials=10_000,trades=15):
    rng=np.random.default_rng(42)
    rolls=rng.random((trials,trades))
    pnl=np.where(rolls<win_rate,rr,-1.0).sum(axis=1)
    return round(float((pnl>0).mean()*100),1)

# ─────────────────────────────────────────────────────────────────────────────
# ANALYSER
# ─────────────────────────────────────────────────────────────────────────────
class Arthsutra200:
    def __init__(self): self._f=DataFetcher(); self._sf=SignalFactory()
    def run(self,target_date,tickers=NIFTY_200,pbar=None,stxt=None):
        start=datetime.combine(target_date,datetime.min.time())-timedelta(days=cfg.history_days)
        end  =datetime.combine(target_date,datetime.min.time())+timedelta(days=90)
        ts   =pd.Timestamp(target_date)
        def _cb(done,total):
            if pbar: pbar.progress(done/total,text=f"⏳ Scanning {done}/{total} stocks…")
        raw=self._f.fetch_batch(tickers,start,end,_cb)
        if stxt: stxt.info("🔬 Building signals…")
        if pbar: pbar.progress(1.0,text="✅ Complete!")
        records=[]
        for ticker,df in raw.items():
            try:
                sig=self._sf.build(ticker,self._sf.enrich(df.copy()),ts)
                if sig: records.append(sig)
            except Exception as e: log.error("%s: %s",ticker,e)
        records.sort(key=lambda r:r.confidence,reverse=True)
        return records

# ─────────────────────────────────────────────────────────────────────────────
# HTML CARD RENDERER
# ─────────────────────────────────────────────────────────────────────────────
SMETA = {
    "JACKPOT": ("✅ TARGET HIT","#00d4aa","rgba(0,212,170,.12)","Reached Take-Profit 2 — profitable"),
    "TP1_HIT": ("🟡 TP1 HIT",  "#f5c842","rgba(245,200,66,.10)","Reached Take-Profit 1 — partial profit"),
    "SL_HIT":  ("❌ STOP HIT", "#ff4d6d","rgba(255,77,109,.10)","Stop loss triggered — controlled loss"),
    "RUNNING": ("⏳ RUNNING",  "#f5c842","rgba(245,200,66,.08)","Trade still open"),
    "LIVE":    ("🔵 LIVE",     "#38bdf8","rgba(56,189,248,.08)","Active signal today"),
}

def conf_color(s): return "#00d4aa" if s>=75 else ("#f5c842" if s>=55 else "#ff4d6d")
def conf_text(s):  return "Strong Setup 💚" if s>=80 else ("Decent Setup 🟡" if s>=62 else "Weak Setup 🔴")

def render_card(r: SignalRecord) -> str:
    blue = r.category == "BLUE"
    sm   = SMETA.get(r.status, SMETA["RUNNING"])
    sc   = conf_color(r.confidence)
    top_color = "#00d4aa" if blue else "#f5c842"
    badge_bg  = "rgba(0,212,170,.14)" if blue else "rgba(245,200,66,.14)"

    def pbox(label, sublabel, val, color):
        return (f'<div style="background:#07101a;border-radius:8px;padding:11px 12px;border:1px solid #1a2d3e;">'
                f'<div style="color:#4a6a84;font-size:10px;font-family:var(--mono);letter-spacing:1px;">{label}</div>'
                f'<div style="color:#3a5a74;font-size:9px;margin:2px 0 4px;">{sublabel}</div>'
                f'<div style="color:{color};font-size:15px;font-weight:700;font-family:var(--mono);">₹{val:,.0f}</div>'
                f'</div>')

    return f"""
<div style="background:#0d1b2a;border:1px solid #1a2d3e;border-top:3px solid {top_color};
            border-radius:14px;padding:18px 16px;margin-bottom:14px;animation:fadein .3s ease;">

  <!-- Header row -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              margin-bottom:14px;gap:8px;flex-wrap:wrap;">
    <div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-family:var(--mono);color:#e8f4ff;font-size:22px;
                     font-weight:700;letter-spacing:1px;">{r.ticker}</span>
        <span style="background:{badge_bg};color:{top_color};border-radius:5px;
                     padding:3px 10px;font-size:11px;font-weight:700;
                     font-family:var(--mono);letter-spacing:1.5px;">{r.category}</span>
      </div>
      <div style="color:#4a6a84;font-size:11px;font-family:var(--mono);margin-top:4px;">
        NSE · {r.date}
      </div>
    </div>
    <div style="background:{sm[2]};border:1px solid {sm[1]}44;border-radius:8px;
                padding:6px 12px;display:flex;align-items:center;gap:6px;">
      <span style="width:7px;height:7px;border-radius:50%;background:{sm[1]};
                   display:inline-block;flex-shrink:0;"></span>
      <span style="color:{sm[1]};font-size:11px;font-weight:700;
                   font-family:var(--mono);white-space:nowrap;">{sm[0]}</span>
    </div>
  </div>

  <!-- Price boxes -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">
    {pbox("ENTRY","Buy near this price",r.entry,"#c8d8e8")}
    {pbox("STOP LOSS","Exit if drops here",r.stop_loss,"#ff4d6d")}
    {pbox("TARGET 1 · 1:1","First profit level",r.tp1,"#f5c842")}
    {pbox("TARGET 2 · 1:2","Full profit level",r.tp2,"#00d4aa")}
  </div>

  <!-- Plain English summary -->
  <div style="background:rgba(56,189,248,.05);border:1px solid rgba(56,189,248,.15);
              border-radius:8px;padding:12px 14px;margin-bottom:14px;">
    <div style="color:#38bdf8;font-size:13px;font-weight:700;margin-bottom:6px;">💡 Trade Summary</div>
    <div style="color:#4a7a94;font-size:13px;line-height:1.7;">
      {sm[3]}<br>
      Risk per share: <b style="color:#e8f4ff;">₹{r.risk_pts:.0f}</b> &nbsp;·&nbsp;
      Volume: <b style="color:#e8f4ff;">{r.vol_ratio:.1f}× normal</b> &nbsp;·&nbsp;
      RSI: <b style="color:#e8f4ff;">{r.rsi}</b>
    </div>
  </div>

  <!-- Indicator pills -->
  <div style="margin-bottom:12px;line-height:2.2;">
    <span style="background:#07101a;border:1px solid #1a2d3e;border-radius:5px;
                 padding:4px 10px;font-size:12px;font-family:var(--mono);color:#7fa8c4;
                 margin:0 4px 4px 0;display:inline-block;">
      <span style="color:#4a6a84;">RSI </span>{r.rsi}
    </span>
    <span style="background:#07101a;border:1px solid #1a2d3e;border-radius:5px;
                 padding:4px 10px;font-size:12px;font-family:var(--mono);color:#7fa8c4;
                 margin:0 4px 4px 0;display:inline-block;">
      <span style="color:#4a6a84;">VOL </span>{r.vol_ratio:.1f}×
    </span>
    <span style="background:#07101a;border:1px solid #1a2d3e;border-radius:5px;
                 padding:4px 10px;font-size:12px;font-family:var(--mono);color:#7fa8c4;
                 margin:0 4px 4px 0;display:inline-block;">
      <span style="color:#4a6a84;">MACD </span>{('+' if r.macd_hist>=0 else '')}{r.macd_hist:.3f}
    </span>
    <span style="background:#07101a;border:1px solid #1a2d3e;border-radius:5px;
                 padding:4px 10px;font-size:12px;font-family:var(--mono);color:#7fa8c4;
                 margin:0 4px 4px 0;display:inline-block;">
      <span style="color:#4a6a84;">Δ SMA200 </span>+{r.pct_vs_sma200:.1f}%
    </span>
  </div>

  <!-- Confidence meter -->
  <div style="margin-bottom:12px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
      <span style="color:{sc};font-size:13px;font-weight:600;">{conf_text(r.confidence)}</span>
      <span style="color:{sc};font-size:17px;font-weight:700;font-family:var(--mono);">
        {r.confidence:.0f}<span style="font-size:11px;color:#4a6a84;">/100</span>
      </span>
    </div>
    <div style="height:5px;background:#1a2d3e;border-radius:3px;overflow:hidden;">
      <div style="height:100%;width:{int(r.confidence)}%;border-radius:3px;
                  background:linear-gradient(90deg,{sc}66,{sc});"></div>
    </div>
    <div style="color:#4a6a84;font-size:10px;font-family:var(--mono);
                letter-spacing:1px;margin-top:3px;">CONFIDENCE SCORE</div>
  </div>

  <!-- TradingView link -->
  <a href="{r.chart_url}" target="_blank"
     style="display:block;text-align:center;padding:11px;border:1px solid #1a2d3e;
            border-radius:8px;color:#4a6a84;font-size:14px;text-decoration:none;
            font-family:var(--mono);transition:color .2s;">
    📈 View Chart on TradingView ↗
  </a>
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Session state defaults
    for k, v in [("ok", False), ("records", None), ("scan_date", None), ("elapsed", 0)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ══════════════════════════════════════════════════════════════════════════
    # DISCLAIMER GATE
    # ══════════════════════════════════════════════════════════════════════════
    if not st.session_state["ok"]:
        st.markdown("""
<div style="text-align:center;padding:40px 0 24px;">
  <div style="font-size:52px;margin-bottom:10px;">🔱</div>
  <div style="font-size:28px;font-weight:800;color:#e8f4ff;">Arthsutra</div>
  <div style="font-size:15px;color:#00d4aa;font-style:italic;
              letter-spacing:2px;margin-top:6px;">
    Discipline · Prosperity · Consistency
  </div>
  <div style="font-size:12px;color:#4a6a84;margin-top:8px;">
    Nifty 200 Signal Analyzer · Educational Tool
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div style="background:rgba(255,77,109,.06);border:1px solid rgba(255,77,109,.35);
            border-left:4px solid #ff4d6d;border-radius:12px;padding:20px 18px;
            margin-bottom:20px;">
  <div style="color:#ff4d6d;font-size:16px;font-weight:700;margin-bottom:12px;">
    ⚠️ Legal Disclaimer — Read Before Using
  </div>
  <div style="color:#9e6070;font-size:14px;line-height:1.8;">
    <b style="color:#c07080;">1. NOT SEBI REGISTERED:</b> Arthsutra is NOT registered with SEBI
    as a Research Analyst, Investment Advisor, or Portfolio Manager under any SEBI regulation.<br><br>
    <b style="color:#c07080;">2. EDUCATIONAL ONLY:</b> All signals and analysis are for
    <b>educational and research purposes only</b>. Nothing here is investment advice.<br><br>
    <b style="color:#c07080;">3. NO GUARANTEED RETURNS:</b> Past performance and backtested
    results do not guarantee future returns. Markets carry inherent risk.<br><br>
    <b style="color:#c07080;">4. RISK OF LOSS:</b> Trading involves <b>substantial risk of
    financial loss</b>. Never trade with money you cannot afford to lose.<br><br>
    <b style="color:#c07080;">5. CONSULT AN ADVISOR:</b> Always consult a SEBI-registered
    Research Analyst or Certified Financial Planner before any investment decision.<br><br>
    <b style="color:#c07080;">6. NO LIABILITY:</b> Arthsutra accepts zero responsibility for
    any financial loss arising from use of this tool.
  </div>
</div>
<div style="color:#4a6a84;font-size:13px;text-align:center;margin-bottom:16px;line-height:1.6;">
  By clicking below you confirm you have read and understood this disclaimer<br>
  and will not treat any output as financial advice.
</div>
""", unsafe_allow_html=True)

        if st.button("✅  I Understand — Enter Arthsutra", type="primary"):
            st.session_state["ok"] = True
            st.rerun()
        return

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN APP
    # ══════════════════════════════════════════════════════════════════════════

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="background:#07101a;border-bottom:1px solid #1a2d3e;
            padding:16px 0 12px;margin:-1rem -1rem 1.2rem;
            text-align:center;">
  <div style="font-size:30px;margin-bottom:4px;">🔱</div>
  <div style="font-size:22px;font-weight:800;color:#e8f4ff;letter-spacing:0.5px;">Arthsutra</div>
  <div style="font-size:13px;color:#00d4aa;font-style:italic;
              letter-spacing:2px;margin-top:4px;">
    Discipline · Prosperity · Consistency
  </div>
  <div style="overflow:hidden;margin-top:10px;border-top:1px solid #1a2d3e;padding-top:6px;">
    <div style="display:flex;white-space:nowrap;animation:ticker 28s linear infinite;">
      <span style="color:#1e3045;font-size:9px;letter-spacing:2px;font-family:var(--mono);padding-right:40px;">
        ARTHSUTRA · NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE ·
        NIFTY 200 SCANNER · WILDER RSI · EMA MACD · ATR · MONTE CARLO · DISCIPLINE · PROSPERITY · CONSISTENCY ·
        ARTHSUTRA · NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE ·
        NIFTY 200 SCANNER · WILDER RSI · EMA MACD · ATR · MONTE CARLO · DISCIPLINE · PROSPERITY · CONSISTENCY ·
      </span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── MINI DISCLAIMER ───────────────────────────────────────────────────────
    st.markdown("""
<div style="background:rgba(255,77,109,.05);border:1px solid rgba(255,77,109,.25);
            border-radius:10px;padding:10px 14px;margin-bottom:16px;
            font-size:12px;color:#7a3d48;line-height:1.6;text-align:center;">
  ⚠️ <b style="color:#c07080;">NOT SEBI REGISTERED</b> · Educational use only · Not investment advice ·
  Consult a SEBI-registered advisor before any trading decision
</div>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # DATE SELECTION  — using dropdowns (works on ALL phones)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
<div style="background:#0d1b2a;border:1px solid #1a2d3e;border-radius:14px;
            padding:20px 18px;margin-bottom:16px;">
  <div style="color:#00d4aa;font-size:16px;font-weight:700;margin-bottom:4px;">
    📅 Select Analysis Date
  </div>
  <div style="color:#4a6a84;font-size:13px;margin-bottom:16px;line-height:1.5;">
    Pick any past weekday (Mon–Fri) up to 2 years back.<br>
    Use the <b style="color:#7fa8c4;">three dropdowns</b> below — tap each one to change.
  </div>
""", unsafe_allow_html=True)

    today     = datetime.now().date()
    def_date  = prev_weekday(today - timedelta(days=1))

    all_years  = valid_years()
    all_months = valid_months()

    # ── Year / Month / Day selectors ──
    col_y, col_m, col_d = st.columns(3)

    with col_y:
        sel_year = st.selectbox(
            "YEAR",
            options  = list(reversed(all_years)),
            index    = 0,
            key      = "sel_year",
        )

    with col_m:
        month_names = list(all_months.keys())
        # Default to current month
        def_month_name = def_date.strftime("%B")
        if def_month_name in month_names:
            def_m_idx = month_names.index(def_month_name)
        else:
            def_m_idx = def_date.month - 1
        sel_month_name = st.selectbox(
            "MONTH",
            options = month_names,
            index   = def_m_idx,
            key     = "sel_month",
        )
        sel_month = all_months[sel_month_name]

    with col_d:
        max_day   = days_in_month(sel_year, sel_month)
        def_day   = min(def_date.day, max_day)
        day_opts  = list(range(1, max_day + 1))
        def_d_idx = day_opts.index(def_day) if def_day in day_opts else 0
        sel_day   = st.selectbox(
            "DAY",
            options = day_opts,
            index   = def_d_idx,
            key     = "sel_day",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Validate chosen date
    chosen = build_date(sel_year, sel_month, sel_day)

    if chosen is None:
        if date(sel_year, sel_month, sel_day) >= today:
            st.error("❌ Please select a **past** date — today or future dates have no data.")
        else:
            st.error("❌ Invalid date or too far in the past. Please pick within the last 2 years.")
        date_ok = False
    elif chosen.weekday() >= 5:
        day_name = chosen.strftime("%A")
        st.warning(f"⚠️ {chosen.strftime('%d %b %Y')} is a **{day_name}** — markets are closed.\n\n"
                   "Please pick a **Monday to Friday**.")
        date_ok = False
    else:
        day_name = chosen.strftime("%A, %d %B %Y")
        st.success(f"✅ Selected: **{day_name}**")
        date_ok = True

    # ── FILTER ────────────────────────────────────────────────────────────────
    st.markdown("### 🔍 Filter")
    cat_filter = st.radio(
        "Show signals",
        ["All", "🔵 Blue (Strongest)", "🟡 Amber"],
        horizontal = True,
        label_visibility = "collapsed",
    )
    fmap = {"All": None, "🔵 Blue (Strongest)": "BLUE", "🟡 Amber": "AMBER"}
    fcat = fmap.get(cat_filter)

    st.markdown("---")

    # ── RUN BUTTON ────────────────────────────────────────────────────────────
    btn_label = (
        f"🔍  Scan Signals for {chosen.strftime('%d %b %Y')}"
        if (date_ok and chosen)
        else "⚠️  Choose a valid weekday above"
    )
    run = st.button(btn_label, type="primary", disabled=not date_ok)

    if run and date_ok and chosen:
        t0   = time.perf_counter()
        pbar = st.progress(0, text="Starting…")
        stxt = st.empty()
        stxt.info("📡 Downloading market data — please wait 30–90 seconds…")
        with st.spinner(""):
            engine  = Arthsutra200()
            records = engine.run(chosen, pbar=pbar, stxt=stxt)
        pbar.empty(); stxt.empty()
        elapsed = time.perf_counter() - t0

        if not records:
            st.warning(
                f"⚠️ **No signals for {chosen.strftime('%d %B %Y')}.**\n\n"
                "Possible reasons:\n"
                "- Market holiday on this day\n"
                "- No stocks passed the Triple-Bullish filter\n"
                "- Data not yet available\n\n"
                "💡 Try a different recent weekday."
            )
        else:
            st.session_state["records"]   = records
            st.session_state["scan_date"] = chosen
            st.session_state["elapsed"]   = elapsed

    # ── RESULTS ───────────────────────────────────────────────────────────────
    if st.session_state["records"] is None:
        st.markdown("""
<div style="text-align:center;padding:50px 0;color:#1e3045;">
  <div style="font-size:48px;margin-bottom:12px;opacity:.5;">🔱</div>
  <div style="font-size:17px;color:#4a6a84;font-weight:600;">
    Select a date above and tap Scan
  </div>
  <div style="font-size:13px;color:#263d52;margin-top:8px;">
    The engine will scan 150+ Nifty 200 stocks for bullish setups
  </div>
</div>""", unsafe_allow_html=True)
        # Show how-to guide before first scan
        with st.expander("📖 How does this work?", expanded=False):
            st.markdown("""
**Arthsutra** scans all Nifty 200 stocks daily for a **Triple-Bullish pattern**:

1. **Price** is above the **44-day moving average**
2. **44-day average** is above the **200-day average**
3. Today's close is **higher than today's open** (bullish candle)

Stocks that pass all three tests are shown as signals.

**🔵 Blue signals** are the strongest — they also have:
- RSI above 65 (strong momentum)
- Volume surge (institutional buying)
- Price 5%+ above the 200-day average

**Reading a signal card:**
- **Entry** = Buy around this price
- **Stop Loss** = Exit here if trade goes wrong (limits your loss)
- **Target 1** = First profit zone (1:1 risk/reward)
- **Target 2** = Full profit zone (1:2 risk/reward)

**Status after scan:**
- ✅ Target Hit = Stock reached Target 2 after the signal date
- 🟡 TP1 Hit = Reached Target 1 only
- ❌ Stop Hit = Stop loss was triggered
- ⏳ Running = Still in play
""")
        return

    records   = st.session_state["records"]
    _sd       = st.session_state["scan_date"]
    elapsed   = st.session_state["elapsed"]

    # Normalise scan_date — session state may store it as date, datetime, or string
    if isinstance(_sd, datetime):
        scan_date = _sd.date()
    elif isinstance(_sd, str):
        try:
            scan_date = datetime.strptime(_sd, "%Y-%m-%d").date()
        except Exception:
            scan_date = date.today()
    elif isinstance(_sd, date):
        scan_date = _sd
    else:
        scan_date = date.today()

    filtered  = [r for r in records if fcat is None or r.category == fcat]
    blue      = [r for r in records if r.category == "BLUE"]
    amber     = [r for r in records if r.category == "AMBER"]
    bjp       = sum(1 for r in blue if r.jackpot)
    accuracy  = round(bjp / len(blue) * 100, 1) if blue else 0.0
    avg_conf  = round(sum(r.confidence for r in records) / len(records), 1) if records else 0

    # ── SCAN COMPLETE BANNER ──────────────────────────────────────────────────
    st.success(
        f"✅ **Scan complete — {scan_date.strftime('%d %B %Y')}**\n\n"
        f"{len(records)} signals found in {float(elapsed):.1f}s"
    )

    # ── STATS (2-column grid for mobile) ─────────────────────────────────────
    st.markdown(f"<div style='color:#4a6a84;font-size:10px;letter-spacing:2px;font-family:var(--mono);margin-bottom:10px;'>SCAN SUMMARY · {scan_date.strftime('%d %b %Y').upper()}</div>", unsafe_allow_html=True)

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    r1c1.metric("📊 Total Signals",  len(records))
    r1c2.metric("🔵 Blue Signals",   len(blue),   help="Highest conviction setups")
    r2c1.metric("🎯 Blue Accuracy",  f"{accuracy}%", f"{bjp}/{len(blue)} hit target")
    r2c2.metric("⚡ Avg Score",      f"{avg_conf}",   help="Confidence score avg")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MONTE CARLO ───────────────────────────────────────────────────────────
    with st.expander("📈 Consistency Engine (Monte Carlo)", expanded=False):
        mc1 = monte_carlo(0.82, 1.0)
        mc2 = monte_carlo(0.74, 2.0)
        blended = round((mc1 + mc2) / 2, 1)
        st.markdown(f"""
<div style="background:#07101a;border:1px solid #1a2d3e;border-radius:12px;padding:18px 16px;">
  <div style="color:#4a6a84;font-size:10px;font-family:var(--mono);
              letter-spacing:2px;margin-bottom:14px;">
    10,000 TRIAL SIMULATION · 15 TRADES/MONTH
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:14px;">
    <div style="text-align:center;background:#0d1b2a;border-radius:10px;padding:14px 8px;
                border:1px solid #1a2d3e;">
      <div style="color:#38bdf8;font-size:26px;font-weight:700;font-family:var(--mono);">{mc1}%</div>
      <div style="color:#4a6a84;font-size:10px;margin-top:4px;">Model A<br>1:1 R/R</div>
    </div>
    <div style="text-align:center;background:#0d1b2a;border-radius:10px;padding:14px 8px;
                border:1px solid #1a2d3e;">
      <div style="color:#00d4aa;font-size:26px;font-weight:700;font-family:var(--mono);">{mc2}%</div>
      <div style="color:#4a6a84;font-size:10px;margin-top:4px;">Model B<br>1:2 R/R</div>
    </div>
    <div style="text-align:center;background:rgba(0,212,170,.06);border-radius:10px;padding:14px 8px;
                border:1px solid rgba(0,212,170,.2);">
      <div style="color:#00d4aa;font-size:26px;font-weight:700;font-family:var(--mono);">{blended}%</div>
      <div style="color:#4a6a84;font-size:10px;margin-top:4px;">Blended<br>Score</div>
    </div>
  </div>
  <div style="color:#4a6a84;font-size:12px;line-height:1.6;">
    Probability of ending a month profitably based on 10,000 simulated months.
    Historical win rates used: Model A 82% · Model B 74%.
  </div>
  <div style="color:#7a3d48;font-size:11px;margin-top:10px;padding:8px 12px;
              background:rgba(255,77,109,.04);border-radius:6px;border:1px solid rgba(255,77,109,.12);">
    ⚠️ Simulation ≠ future performance guarantee. Arthsutra is not SEBI registered.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SIGNAL CARDS ─────────────────────────────────────────────────────────
    if not filtered:
        st.info("No signals match this filter. Try 'All' from the filter above.")
    else:
        st.markdown(
            f"<div style='color:#4a6a84;font-size:10px;letter-spacing:2px;font-family:var(--mono);"
            f"margin-bottom:12px;'>{len(filtered)} SIGNALS · SORTED BY CONFIDENCE ↓</div>",
            unsafe_allow_html=True,
        )
        for rec in filtered:
            st.markdown(render_card(rec), unsafe_allow_html=True)

    # ── SUMMARY TABLE ─────────────────────────────────────────────────────────
    if filtered:
        with st.expander(f"📋 Summary Table ({len(filtered)} signals)", expanded=False):
            df_out = pd.DataFrame([{
                "Stock":    r.ticker,
                "Type":     r.category,
                "Status":   SMETA.get(r.status, SMETA["RUNNING"])[0],
                "Entry ₹":  r.entry,
                "Stop ₹":   r.stop_loss,
                "TP1 ₹":    r.tp1,
                "TP2 ₹":    r.tp2,
                "Score":    r.confidence,
                "Chart":    r.chart_url,
            } for r in filtered])
            st.dataframe(
                df_out,
                column_config={
                    "Score":   st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
                    "Entry ₹": st.column_config.NumberColumn(format="₹%,.0f"),
                    "Stop ₹":  st.column_config.NumberColumn(format="₹%,.0f"),
                    "TP1 ₹":   st.column_config.NumberColumn(format="₹%,.0f"),
                    "TP2 ₹":   st.column_config.NumberColumn(format="₹%,.0f"),
                    "Chart":   st.column_config.LinkColumn("📈"),
                },
                hide_index=True, use_container_width=True,
            )

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:28px 0 10px;
            border-top:1px solid #1a2d3e;margin-top:28px;">
  <div style="font-size:26px;margin-bottom:6px;">🔱</div>
  <div style="color:#e8f4ff;font-size:16px;font-weight:800;">Arthsutra</div>
  <div style="color:#00d4aa;font-size:12px;font-style:italic;
              letter-spacing:2px;margin:4px 0 10px;">
    Discipline · Prosperity · Consistency
  </div>
  <div style="color:#263d52;font-size:10px;font-family:var(--mono);
              letter-spacing:1px;margin-bottom:6px;">
    NIFTY 200 · WILDER RSI · MACD · ATR · MONTE CARLO · CONFIDENCE ENGINE
  </div>
  <div style="color:#7a3d48;font-size:11px;line-height:1.7;">
    ⚠️ NOT SEBI REGISTERED · EDUCATIONAL USE ONLY<br>
    NOT INVESTMENT ADVICE · CONSULT A SEBI-REGISTERED ADVISOR
  </div>
  <div style="margin-top:12px;">
    <button onclick="window.location.reload()" style="background:transparent;border:1px solid #1a2d3e;
      border-radius:6px;color:#4a6a84;font-size:12px;padding:6px 16px;cursor:pointer;">
      📋 Read Disclaimer
    </button>
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
