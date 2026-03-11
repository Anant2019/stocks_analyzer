from __future__ import annotations

import logging
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Final

import pandas as pd
import streamlit as st
import yfinance as yf

# ── Logging (backend only) ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arth_sutra.engine")

# ── Strategy constants — exact Pine Script values ─────────────────────────────
SMA_FAST:     Final[int]   = 44
SMA_SLOW:     Final[int]   = 200
MIN_BARS:     Final[int]   = 210
CONCURRENCY:  Final[int]   = 12
PERIOD:       Final[str]   = "2y"
INTERVAL:     Final[str]   = "1d"
COLS:         Final[int]   = 4

FALLBACK: Final[list[str]] =[
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS",
    "HINDALCO.NS", "COALINDIA.NS",
]

# ── Value object ──────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class TradingSignal:
    ticker:      str
    signal_date: str     # Stores the exact date of the scanned candle
    entry:       float   
    stop_loss:   float   
    target_1:    float   
    target_2:    float   
    sma_fast:    float
    sma_slow:    float
    scanned_at:  datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def risk(self) -> float:
        return round(self.entry - self.stop_loss, 4)

    @property
    def rr(self) -> float:
        return round((self.target_2 - self.entry) / self.risk, 2) if self.risk > 0 else 0.0

    @property
    def sma_spread_pct(self) -> float:
        return round((self.sma_fast - self.sma_slow) / self.sma_slow * 100, 2) \
               if self.sma_slow else 0.0

@dataclass(slots=True)
class AuditRecord:
    ticker:     str
    outcome:    str
    reason:     str   = ""
    latency_ms: float = 0.0

def scalar(v):
    return float(v.iloc[0] if hasattr(v, "iloc") else v)

def _compute_signal(ticker: str) -> tuple[TradingSignal | None, AuditRecord]:
    t0 = time.perf_counter()
    ms = lambda: round((time.perf_counter() - t0) * 1_000, 2)

    try:
        raw = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False, auto_adjust=False)

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        raw = raw.loc[:, ~raw.columns.duplicated()]
        raw = raw.dropna()

        if raw.empty or len(raw) < MIN_BARS:
            return None, AuditRecord(ticker, "SHORT_DATA", latency_ms=ms())

        if not all(col in raw.columns for col in ["Close", "Open", "Low", "High"]):
            return None, AuditRecord(ticker, "MISSING_COLS", latency_ms=ms())

        close_s = raw["Close"]
        open_s  = raw["Open"]
        low_s   = raw["Low"]

        # ── FAST TREND PREFILTER (skip weak stocks early) ──
        if close_s.iloc[-1] < close_s.iloc[-50]:
            return None, AuditRecord(ticker, "FILTERED", "Weak trend", ms())
        
        s44  = close_s.rolling(window=SMA_FAST).mean()
        s200 = close_s.rolling(window=SMA_SLOW).mean()

        if pd.isna(s200.iloc[-1]):
            return None, AuditRecord(ticker, "SHORT_DATA", latency_ms=ms())

        # EXACTLY ONLY EVALUATE THE VERY LAST DAY (-1) TO PREVENT FALSE POSITIVES
        curr = -2
        prev = -3

        c = scalar(close_s.iloc[curr])
        o = scalar(open_s.iloc[curr])
        l = scalar(low_s.iloc[curr])      

        s44_val = scalar(s44.iloc[curr])
        s44_old = scalar(s44.iloc[prev])

        s200_val = scalar(s200.iloc[curr])
        s200_old = scalar(s200.iloc[prev])

        # Get exact date of the evaluated candle
        candle_date = raw.index[curr].strftime("%d %b %Y")

        print("Ticker: ",ticker)
        print("Candle date: ",candle_date)
        print("Close: ", c)
        print("Open: ", o)
        print("Low: ", l)
        print("SMA44: ", s44_val)
        print("SMA200: ", s200_val)

        if math.isnan(s44_val) or math.isnan(s44_old) or math.isnan(s200_val):
            return None, AuditRecord(ticker, "FILTERED", "NaN in moving averages", ms())

        # ── 1. TREND CONDITIONS ──
        is_trend_up = s44_val > s200_val
        is_44_up = s44_val > s44_old
        is_200_up = s200_val >= s200_old

        # if not (is_trend_up and is_44_up and is_200_up):
        #     return None, AuditRecord(ticker, "FILTERED", "MAs are not strictly rising or 44 < 200", ms())
        if not (is_trend_up and is_44_up and is_200_up):
            return None, AuditRecord(ticker, "FILTERED", "Trend not valid", ms())

        # ── 2. CANDLE CONDITION ──
        # is_green = c > o
        # if not is_green:
        #     return None, AuditRecord(ticker, "FILTERED", "Not a Green Candle", ms())
        if c <= o:
            return None, AuditRecord(ticker, "FILTERED", "Not green", ms())
        
        # ── 3. PRICE vs SMA POSITION ("over it") ──
        # Both Open & Close must be fully above 44 MA so it is truly "over it"
        # is_body_above = (c > s44_val) and (o > s44_val)

        # is_body_above = c > s44_val

        # if not is_body_above:
        #     return None, AuditRecord(ticker, "FILTERED", "Candle body is not entirely over the 44-SMA", ms())

        # ── 3. CLOSE ABOVE SMA ──
        if c <= s44_val:
            return None, AuditRecord(ticker, "FILTERED", "Close below 44 SMA", ms())

        # ── 4. BOUNCE PROXIMITY ──
        # (l <= s44_val * 1.05) and (l >= s44_val * 0.985)
        # is_near_support = abs(l - s44_val) / s44_val <= 0.05 

        distance = abs(l - s44_val) / s44_val
       
        if distance > 0.05:
            return None, AuditRecord(ticker, "FILTERED", "Too far from SMA", ms())

        # if not is_near_support:
        #     return None, AuditRecord(ticker, "FILTERED", "Price is flying too high or broke down support", ms())

        # If it passed EVERY strict test, calculate secure targets
        stop_loss = round(min(l, s44_val) * 0.985, 2) # Place SL slightly below the wick or the moving average
        risk = c - stop_loss
        
        if risk <= 0: 
            return None, AuditRecord(ticker, "FILTERED", "Invalid Risk Calculation", ms())

        return TradingSignal(
            ticker=ticker.replace(".NS", ""),
            signal_date=candle_date,
            entry=round(c, 2),
            stop_loss=stop_loss,
            target_1=round(c + risk * 1.0, 2), # 1:1 RR Target
            target_2=round(c + risk * 2.0, 2), # 1:2 RR Target
            sma_fast=round(s44_val, 2),
            sma_slow=round(s200_val, 2)
        ), AuditRecord(ticker, "SIGNAL", "Triple Condition Success", ms())


    except Exception as e:
        logger.error(f"CRITICAL ERROR for {ticker}: {e}") 
        return None, AuditRecord(ticker, "ERROR", str(e), ms())

# ── Universe ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def _load_universe() -> list[str]:
    try:
        syms = pd.read_csv(
            "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            usecols=["Symbol"],
            storage_options={'User-Agent': 'Mozilla/5.0'}
        )["Symbol"].tolist()
        logger.info("Universe: %d symbols.", len(syms))
        return[f"{s}.NS" for s in syms]
    except Exception as exc:
        logger.warning("NSE fetch failed (%s). Using fallback.", exc)
        return list(FALLBACK)

# =============================================================================
# PRESENTATION — Midnight Dark · JetBrains Mono · 4-col streaming bento
# =============================================================================
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:           #0B0E11;
    --bg-card:      #131722;
    --bg-cell:      #0D1016;
    --bg-tgt:       rgba(0,212,122,.055);
    --bg-sl:        rgba(240,68,96,.06);
    --border:       #252B33;
    --border-card:  #1A1F27;
    --border-hi:    #353D47;
    --mint:         #00D47A;
    --mint-dim:     rgba(0,212,122,.09);
    --mint-bd:      rgba(0,212,122,.18);
    --rose:         #F04460;
    --rose-dim:     rgba(240,68,96,.09);
    --rose-bd:      rgba(240,68,96,.20);
    --amber:        #F0A500;
    --amber-dim:    rgba(240,165,0,.08);
    --amber-bd:     rgba(240,165,0,.18);
    --ink:          #E4E8EF;
    --ink-2:        #8D95A3;
    --ink-3:        #4A5260;
    --font: 'Inter', -apple-system, sans-serif;
    --mono: 'JetBrains Mono', monospace;
    --r-sm: 6px; --r-md: 10px; --r-lg: 14px;
}

*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }

.stApp { background-color:var(--bg) !important; font-family:var(--font) !important; color:var(--ink) !important; }
.main .block-container { padding:1.75rem 1.5rem 4rem !important; max-width:1440px !important; }

/* ── Brand ── */
.aw { font-family:var(--font); font-size:clamp(1.5rem,3.2vw,2.1rem); font-weight:800; color:var(--ink); letter-spacing:-1px; line-height:1; }
.aw .g { color:var(--mint); }
.aw .d { color:var(--rose); opacity:.5; }
.aw-sub { display:flex; align-items:center; gap:10px; margin-top:7px; margin-bottom:18px; }
.aw-tag { font-family:var(--mono); font-size:.56rem; color:var(--ink-3); letter-spacing:3.5px; text-transform:uppercase; }
.live-badge { display:inline-flex; align-items:center; gap:4px; font-family:var(--mono); font-size:.55rem; font-weight:700; color:var(--mint); background:var(--mint-dim); border:1px solid var(--mint-bd); border-radius:20px; padding:2px 9px; letter-spacing:.8px; }
.live-dot { width:5px; height:5px; border-radius:50%; background:var(--mint); animation:blink 1.5s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.12} }

/* ── Legend ── */
.legend { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px; padding:10px 14px; background:var(--bg-card); border:1px solid var(--border-card); border-radius:var(--r-md); }
.legend-title { font-family:var(--mono); font-size:.52rem; color:var(--ink-3); letter-spacing:2.5px; text-transform:uppercase; width:100%; margin-bottom:4px; }
.lchip { display:inline-flex; align-items:center; gap:5px; font-family:var(--mono); font-size:.54rem; font-weight:600; border-radius:20px; padding:3px 10px; letter-spacing:.3px; }
.lchip.trend  { color:var(--mint);  background:var(--mint-dim);  border:1px solid var(--mint-bd); }
.lchip.candle { color:var(--amber); background:var(--amber-dim); border:1px solid var(--amber-bd); }
.lchip.touch  { color:#A78BFA; background:rgba(167,139,250,.08); border:1px solid rgba(167,139,250,.18); }
.lchip.info   { color:var(--ink-2); background:rgba(255,255,255,.04); border:1px solid var(--border); }

/* ── CTA ── */
div.stButton > button { background:var(--mint) !important; color:#000 !important; font-family:var(--font) !important; font-size:.80rem !important; font-weight:700 !important; letter-spacing:.8px !important; border:none !important; border-radius:var(--r-md) !important; padding:12px 28px !important; width:100% !important; cursor:pointer !important; transition:opacity .15s,transform .15s !important; }
div.stButton > button:hover  { opacity:.85 !important; transform:translateY(-1px) !important; }

/* ── Progress ── */
div[data-testid="stProgress"] > div > div { background:var(--mint) !important; }
div[data-testid="stProgress"] > div { background:var(--border-card) !important; border-radius:4px !important; }

/* ── Status strip ── */
.ss { display:flex; align-items:center; gap:10px; font-family:var(--mono); font-size:.62rem; color:var(--ink-2); margin-bottom:14px; padding:8px 14px; background:var(--bg-card); border:1px solid var(--border-card); border-radius:var(--r-md); }
.ss .ct { color:var(--mint); font-weight:700; }
@keyframes spin { to { transform:rotate(360deg); } }
.ss-spin { width:10px; height:10px; border:1.5px solid var(--border); border-top-color:var(--mint); border-radius:50%; animation:spin .65s linear infinite; flex-shrink:0; }

/* ── Section ── */
.sec-row { display:flex; align-items:center; gap:10px; margin:4px 0 14px; }
.sec-rule { flex:1; height:1px; background:var(--border-card); }
.sec-lbl { font-family:var(--mono); font-size:.56rem; color:var(--ink-3); letter-spacing:3px; text-transform:uppercase; white-space:nowrap; }
.sec-badge { font-family:var(--mono); font-size:.56rem; font-weight:700; color:var(--mint); background:var(--mint-dim); border:1px solid var(--mint-bd); border-radius:20px; padding:2px 9px; white-space:nowrap; }

/* ── Card ── */
.bc { background:var(--bg-card); border:1px solid var(--border-card); border-radius:var(--r-lg); overflow:hidden; margin-bottom:10px; transition:border-color .18s,transform .18s; animation:fadeUp .22s ease both; }
@keyframes fadeUp { from{opacity:0;transform:translateY(7px)} to{opacity:1;transform:translateY(0)} }
.bc:hover { border-color:var(--border-hi); transform:translateY(-2px); }
.bc-stripe { height:2px; background:linear-gradient(90deg,var(--mint) 0%,var(--amber) 100%); }
.bc-body { padding:11px 12px 10px; }

.bc-hd { display:flex; align-items:flex-start; justify-content:space-between; gap:6px; margin-bottom:9px; }
.bc-ticker { font-family:var(--font); font-size:1.02rem; font-weight:800; color:var(--ink); letter-spacing:-.3px; line-height:1; }
.bc-sub { font-family:var(--mono); font-size:.56rem; color:var(--ink-3); margin-top:3px; }

.fresh-tag { display:inline-block; font-family:var(--mono); font-size:.49rem; font-weight:600; border-radius:4px; padding:2px 7px; margin-top:3px; color:var(--mint); background:var(--mint-dim); border:1px solid var(--mint-bd); }

/* TV link */
.tv { display:inline-flex; align-items:center; gap:4px; font-family:var(--mono); font-size:.55rem; font-weight:600; color:var(--ink-2); background:rgba(255,255,255,.035); border:1px solid var(--border); border-radius:var(--r-sm); padding:4px 8px; text-decoration:none !important; white-space:nowrap; flex-shrink:0; transition:color .14s,border-color .14s,background .14s; }
.tv:hover { color:var(--mint) !important; border-color:var(--mint-bd); background:var(--mint-dim); text-decoration:none !important; }
.tv svg { width:9px; height:9px; opacity:.6; }

/* Entry */
.entry-lbl { font-family:var(--mono); font-size:.47rem; color:var(--ink-3); letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }
.entry-val { font-family:var(--mono); font-size:1.12rem; font-weight:700; color:var(--ink); letter-spacing:-.5px; margin-bottom:9px; }

/* SL / T1 / T2 */
.lvl-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:5px; margin-bottom:8px; }
.lvl-cell { border-radius:var(--r-sm); padding:7px 9px; }
.lvl-cell.sl { background:var(--bg-sl);    border:1px solid var(--rose-bd); }
.lvl-cell.t1 { background:var(--amber-dim); border:1px solid var(--amber-bd); }
.lvl-cell.t2 { background:var(--bg-tgt);   border:1px solid var(--mint-bd); }
.lvl-lbl { font-family:var(--mono); font-size:.47rem; letter-spacing:2px; text-transform:uppercase; margin-bottom:3px; }
.lvl-lbl.sl { color:var(--rose); }
.lvl-lbl.t1 { color:var(--amber); }
.lvl-lbl.t2 { color:var(--mint); }
.lvl-val { font-family:var(--mono); font-size:.78rem; font-weight:700; letter-spacing:-.2px; line-height:1; }
.lvl-val.sl { color:var(--rose); }
.lvl-val.t1 { color:var(--amber); }
.lvl-val.t2 { color:var(--mint); }

/* SMA row */
.sma-row { display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-bottom:7px; }
.sma-cell { background:var(--bg-cell); border:1px solid var(--border-card); border-radius:var(--r-sm); padding:6px 8px; }
.sma-lbl { font-family:var(--mono); font-size:.46rem; color:var(--ink-3); letter-spacing:2px; text-transform:uppercase; margin-bottom:2px; }
.sma-val { font-family:var(--mono); font-size:.72rem; font-weight:700; letter-spacing:-.2px; }
.sma-val.fast { color:var(--mint); }
.sma-val.slow { color:var(--rose); }

/* Footer */
.bc-ft { display:flex; align-items:center; justify-content:space-between; padding-top:7px; border-top:1px solid var(--border-card); }
.rr-pill { display:inline-flex; align-items:center; gap:4px; font-family:var(--mono); font-size:.54rem; font-weight:700; color:var(--mint); background:var(--mint-dim); border:1px solid var(--mint-bd); border-radius:20px; padding:3px 8px; }
.rr-d { width:4px; height:4px; border-radius:50%; background:var(--mint); animation:blink 2s ease-in-out infinite; }
.spread-tag { font-family:var(--mono); font-size:.50rem; color:var(--amber); background:var(--amber-dim); border:1px solid var(--amber-bd); border-radius:20px; padding:2px 7px; }

/* Sidebar */
[data-testid="stSidebar"] { background:#0D1016 !important; border-right:1px solid var(--border-card) !important; }
[data-testid="stSidebar"] .block-container { padding:1.5rem 1rem !important; }
.sb-hd { font-family:var(--mono); font-size:.54rem; font-weight:700; color:var(--ink-3); letter-spacing:3px; text-transform:uppercase; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid var(--border-card); }
.sb-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid var(--border-card); }
.sb-k { font-family:var(--font); font-size:.67rem; color:var(--ink-2); }
.sb-v { font-family:var(--mono); font-size:.67rem; font-weight:600; color:var(--ink); }
.sb-v.ok { color:var(--mint); } .sb-v.hl { color:var(--amber); } .sb-v.rd { color:var(--rose); }
h3 { display:none !important; }
</style>
"""

_TV_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
)

_LEGEND = f"""
<div class="legend">
  <div class="legend-title">Strict Swing Trade Conditions</div>
  <div class="lchip trend">&#9650; Uptrend: 44-SMA &gt; 200-SMA</div>
  <div class="lchip trend">&#9650; MAs Rising: Both strictly pointing up</div>
  <div class="lchip candle">&#9646; Green Candle (Close &gt; Open)</div>
  <div class="lchip touch">&#9650; Over It: Body fully above 44-SMA</div>
  <div class="lchip touch">&#9660; Proximity: Wick tests support (near 44-SMA)</div>
  <div class="lchip info">&#9675; Evaluates ONLY the absolute latest candle</div>
</div>
"""

def _card_html(sig: TradingSignal) -> str:
    ticker = str(sig.ticker)
    entry  = f"{float(sig.entry):,.2f}"
    sl     = f"{float(sig.stop_loss):,.2f}"
    t1     = f"{float(sig.target_1):,.2f}"
    t2     = f"{float(sig.target_2):,.2f}"
    rr     = f"{float(sig.rr):.2f}"
    sf     = f"{float(sig.sma_fast):,.2f}"
    ss     = f"{float(sig.sma_slow):,.2f}"
    spd    = f"{float(sig.sma_spread_pct):.2f}"
    tv_url = f"https://www.tradingview.com/chart/?symbol=NSE%3A{ticker}"

    return (
        '<div class="bc"><div class="bc-stripe"></div><div class="bc-body">'
        '<div class="bc-hd"><div>'
        f'<div class="bc-ticker">{ticker}</div>'
        f'<div class="bc-sub">200-SMA &#8377;{ss}</div>'
        f'<div class="fresh-tag">Candle: {sig.signal_date}</div>'
        '</div>'
        f'<a class="tv" href="{tv_url}" target="_blank" rel="noopener noreferrer">{_TV_SVG}&thinsp;Chart</a></div>'
        '<div class="entry-lbl">Entry (Close)</div>'
        f'<div class="entry-val">&#8377;{entry}</div>'
        '<div class="lvl-grid">'
        '<div class="lvl-cell sl"><div class="lvl-lbl sl">&#10007; Stop Loss</div>'
        f'<div class="lvl-val sl">&#8377;{sl}</div></div>'
        '<div class="lvl-cell t1"><div class="lvl-lbl t1">&#9670; Target 1:1</div>'
        f'<div class="lvl-val t1">&#8377;{t1}</div></div>'
        '<div class="lvl-cell t2"><div class="lvl-lbl t2">&#9670; Target 1:2</div>'
        f'<div class="lvl-val t2">&#8377;{t2}</div></div>'
        '</div>'
        '<div class="sma-row">'
        '<div class="sma-cell"><div class="sma-lbl">44-SMA (green)</div>'
        f'<div class="sma-val fast">&#8377;{sf}</div></div>'
        '<div class="sma-cell"><div class="sma-lbl">200-SMA (red)</div>'
        f'<div class="sma-val slow">&#8377;{ss}</div></div>'
        '</div>'
        '<div class="bc-ft">'
        f'<div class="rr-pill"><span class="rr-d"></span>R:R&thinsp;{rr}x</div>'
        f'<span class="spread-tag">+{spd}% above 200-SMA</span>'
        '</div>'
        '</div></div>'
    )

def _sidebar(scanned: int, found: int) -> None:
    rows =[
        ("Universe",  "Nifty 500",             "hl"),
        ("Strategy",  "Swing Triple Bullish",   "ok"),
        ("Trend",     "44>200, strictly rising","ok"),
        ("Reclaim",   "Body fully > 44-SMA",    "ok"),
        ("Candle",    "Green (C > O)",          "ok"),
        ("Lookback",  "Single Latest Candle",   "hl"),
        ("R:R",       "1 : 2",                 "ok"),
        ("Scanned",   str(scanned),            ""),
        ("Signals",   str(found), "ok" if found > 0 else "rd"),
        ("Time",      datetime.now(UTC).strftime("%H:%M UTC"), "")
    ]
    html = "".join(f'<div class="sb-row"><span class="sb-k">{k}</span><span class="sb-v {c}">{v}</span></div>' for k, v, c in rows)
    st.sidebar.markdown(f'<div class="sb-hd">Scan Summary</div>{html}', unsafe_allow_html=True)

# ── Dashboard ──────────────────────────────────────────────────────────────────
def render_dashboard() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="aw">Arth<span class="g">Sutra</span><span class="d">.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="aw-sub"><span class="aw-tag">Swing Triple Bullish · 44/200 SMA · NSE 500</span><span class="live-badge"><span class="live-dot"></span>BUY SIGNAL</span></div>', unsafe_allow_html=True)
    st.markdown(_LEGEND, unsafe_allow_html=True)

    if not st.button("Run Strict Swing Scanner \u2192"):
        return

    universe = _load_universe()
    total    = len(universe)

    progress_bar = st.progress(0, text="Initialising\u2026")
    status_slot  = st.empty()
    section_slot = st.empty()
    col_ph:  list =[st.empty() for _ in range(COLS)]
    col_buf: list[list[str]] = [[] for _ in range(COLS)]
    found = 0
    done  = 0

    def _flush():
        for ci, ph in enumerate(col_ph):
            if col_buf[ci]:
                ph.markdown("".join(col_buf[ci]), unsafe_allow_html=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        fmap = {pool.submit(_compute_signal, t): t for t in universe}
        for future in as_completed(fmap):
            sig, audit = future.result()
            done += 1
            progress_bar.progress(min(math.ceil(done / total * 100), 100), text=f"Scanning\u2026 {done} / {total}")
            
            if sig is None:
                continue

            found += 1
            if found == 1:
                section_slot.markdown('<div class="sec-row"><div class="sec-rule"></div><span class="sec-lbl">BUY Signals</span><div class="sec-rule"></div></div>', unsafe_allow_html=True)

            status_slot.markdown(f'<div class="ss"><div class="ss-spin"></div>Scanning &mdash; <span class="ct">{found} signal{"s" if found!=1 else ""} found</span> &mdash; {done}/{total}</div>', unsafe_allow_html=True)
            col_buf[(found - 1) % COLS].append(_card_html(sig))
            _flush()

    progress_bar.empty()

    if found == 0:
        status_slot.empty()
        section_slot.empty()
        st.warning(f"No strict setups found across {done} instruments.")
    else:
        status_slot.markdown(f'<div class="ss"><span class="ct">{found} signal{"s" if found!=1 else ""} detected</span> &mdash; {done} instruments scanned</div>', unsafe_allow_html=True)
        section_slot.markdown(f'<div class="sec-row"><div class="sec-rule"></div><span class="sec-lbl">BUY Signals</span><span class="sec-badge">{found} Found</span><div class="sec-rule"></div></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        _sidebar(done, found)

# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ArthSutra — Swing Triple Bullish", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

if __name__ == "__main__":
    render_dashboard()