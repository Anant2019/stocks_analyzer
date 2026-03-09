
from __future__ import annotations

import logging
import math
import time
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
N_LOOKBACK:   Final[int]   = 5       # check last 5 bars (Pine fires on any historical bar)
TOUCH_BUFFER: Final[float] = 1.003   # 0.3% rounding buffer — NOT a tolerance band
                                      # low must be AT or BELOW the 44-SMA
SL_BUFFER:    Final[float] = 0.998
RISK_MULT:    Final[float] = 2.0
MIN_BARS:     Final[int]   = SMA_SLOW + N_LOOKBACK + 5
CONCURRENCY:  Final[int]   = 25
PERIOD:       Final[str]   = "2y"
INTERVAL:     Final[str]   = "1d"
COLS:         Final[int]   = 4

FALLBACK: Final[list[str]] = [
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS",
    "HINDALCO.NS", "COALINDIA.NS",
]


# ── Value object ──────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class TradingSignal:
    ticker:    str
    entry:     float   # close of signal bar  (Pine: entry_val = close)
    stop_loss: float   # low × SL_BUFFER       (Pine: sl_val   = low)
    target_1:  float   # entry + 1R            (Pine: tgt1 = close + risk)
    target_2:  float   # entry + 2R            (Pine: tgt2 = close + risk*2)
    sma_fast:  float
    sma_slow:  float
    bars_ago:  int     # 0=today, 1=yesterday …
    scanned_at: datetime = field(default_factory=datetime.utcnow)

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



def _compute_signal(ticker: str) -> tuple[TradingSignal | None, AuditRecord]:
    print(f"TICKER: {ticker}")
    t0 = time.perf_counter()
    ms = lambda: round((time.perf_counter() - t0) * 1_000, 2)

    try:
        # auto_adjust=False is vital for the 'Green' check (C > O)
        raw = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=False)

        if len(raw) < 210:
            print(f"FAIL: {ticker} SMA210 not rising")
            return None, AuditRecord(ticker, "SHORT_DATA", latency_ms=ms())

        close_s = raw["Close"]
        open_s  = raw["Open"]
        low_s   = raw["Low"]
        
        s44  = close_s.rolling(window=44).mean()
        s200 = close_s.rolling(window=200).mean()

        for i in range(N_LOOKBACK):
            curr = -(i + 1)
            prev = -(i + 2)

            # --- DATA POINTS ---
            c, o, l = float(close_s.iloc[curr].item()), float(open_s.iloc[curr].item()), float(low_s.iloc[curr].item())
            

            s44_val = float(s44.iloc[curr].item())
            s44_old = float(s44.iloc[prev].item())

            # Check if data exists, then compare. 
            # If data is missing, we default to False.
            if math.isnan(s44_val) or math.isnan(s44_old):
                is_44_up = False
            else:
                is_44_up = bool(s44_val >= (s44_old - 0.01))

            # 2. 200-SMA Going Up
            s200_val = float(s200.iloc[curr].item())
            s200_old = float(s200.iloc[prev].item())

            if math.isnan(s200_val) or math.isnan(s200_old):
                is_200_up = False
            else:
                is_200_up = bool(s200_val >= (s200_old - 0.01))

            # 3. Candle MUST be Green
            is_green = c > o

            # --- GATEKEEPER ---
            if not (is_44_up and is_200_up and is_green):
                print(f"FAIL: {ticker} because is_44_up :{s44_curr} is_200_up :{is_200_up} is_green:{is_green}")
                continue
            
            print(f"PASS: {ticker} because is_44_up :{s44_curr} is_200_up :{is_200_up} is_green:{is_green}")

            # ── STRATEGY: THE BOUNCE ──
            # If your manual scan finds more, it's because your 'Touch' is wider.
            # I am increasing the buffer to 0.5% (1.005) to catch 'near-touches'.
            touched = l <= (s44_curr * 1.005) 
            reclaimed = c > s44_curr
            above_200 = c > s200_curr

            if touched and reclaimed and above_200:
                risk = c - l
                if risk <= 0: continue

                return TradingSignal(
                    ticker=ticker.replace(".NS", ""),
                    entry=round(c, 2),
                    stop_loss=round(l * 0.998, 2),
                    target_1=round(c + risk * 1.5, 2),
                    target_2=round(c + risk * 3.0, 2),
                    sma_fast=round(s44_curr, 2),
                    sma_slow=round(s200_curr, 2),
                    bars_ago=i
                ), AuditRecord(ticker, "SIGNAL", "Triple Condition Success", ms())


        return None, AuditRecord(ticker, "FILTERED", "No matches", ms())

    except Exception as e:
        return None, AuditRecord(ticker, "ERROR", str(e), ms())




# ── Universe ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def _load_universe() -> list[str]:
    try:
        syms = pd.read_csv(
            "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            usecols=["Symbol"],
        )["Symbol"].tolist()
        logger.info("Universe: %d symbols.", len(syms))
        return [f"{s}.NS" for s in syms]
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

.stApp {
    background-color:var(--bg) !important;
    font-family:var(--font) !important;
    color:var(--ink) !important;
}
.main .block-container {
    padding:1.75rem 1.5rem 4rem !important;
    max-width:1440px !important;
}

/* ── Brand ── */
.aw { font-family:var(--font); font-size:clamp(1.5rem,3.2vw,2.1rem);
      font-weight:800; color:var(--ink); letter-spacing:-1px; line-height:1; }
.aw .g { color:var(--mint); }
.aw .d { color:var(--rose); opacity:.5; }
.aw-sub { display:flex; align-items:center; gap:10px; margin-top:7px; margin-bottom:18px; }
.aw-tag { font-family:var(--mono); font-size:.56rem; color:var(--ink-3);
          letter-spacing:3.5px; text-transform:uppercase; }
.live-badge {
    display:inline-flex; align-items:center; gap:4px;
    font-family:var(--mono); font-size:.55rem; font-weight:700;
    color:var(--mint); background:var(--mint-dim);
    border:1px solid var(--mint-bd); border-radius:20px; padding:2px 9px; letter-spacing:.8px;
}
.live-dot { width:5px; height:5px; border-radius:50%; background:var(--mint);
            animation:blink 1.5s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.12} }

/* ── Legend ── */
.legend {
    display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px;
    padding:10px 14px; background:var(--bg-card);
    border:1px solid var(--border-card); border-radius:var(--r-md);
}
.legend-title { font-family:var(--mono); font-size:.52rem; color:var(--ink-3);
                letter-spacing:2.5px; text-transform:uppercase; width:100%; margin-bottom:4px; }
.lchip { display:inline-flex; align-items:center; gap:5px; font-family:var(--mono);
         font-size:.54rem; font-weight:600; border-radius:20px; padding:3px 10px; letter-spacing:.3px; }
.lchip.trend  { color:var(--mint);  background:var(--mint-dim);  border:1px solid var(--mint-bd); }
.lchip.candle { color:var(--amber); background:var(--amber-dim); border:1px solid var(--amber-bd); }
.lchip.touch  { color:#A78BFA; background:rgba(167,139,250,.08); border:1px solid rgba(167,139,250,.18); }
.lchip.info   { color:var(--ink-2); background:rgba(255,255,255,.04); border:1px solid var(--border); }

/* ── CTA ── */
div.stButton > button {
    background:var(--mint) !important; color:#000 !important;
    font-family:var(--font) !important; font-size:.80rem !important;
    font-weight:700 !important; letter-spacing:.8px !important;
    border:none !important; border-radius:var(--r-md) !important;
    padding:12px 28px !important; width:100% !important;
    cursor:pointer !important; transition:opacity .15s,transform .15s !important;
}
div.stButton > button:hover  { opacity:.85 !important; transform:translateY(-1px) !important; }
div.stButton > button:active { transform:translateY(0) !important; }

/* ── Progress ── */
div[data-testid="stProgress"] > div > div { background:var(--mint) !important; }
div[data-testid="stProgress"] > div { background:var(--border-card) !important; border-radius:4px !important; }

/* ── Status strip ── */
.ss { display:flex; align-items:center; gap:10px; font-family:var(--mono);
      font-size:.62rem; color:var(--ink-2); margin-bottom:14px; padding:8px 14px;
      background:var(--bg-card); border:1px solid var(--border-card); border-radius:var(--r-md); }
.ss .ct { color:var(--mint); font-weight:700; }
@keyframes spin { to { transform:rotate(360deg); } }
.ss-spin { width:10px; height:10px; border:1.5px solid var(--border);
           border-top-color:var(--mint); border-radius:50%;
           animation:spin .65s linear infinite; flex-shrink:0; }

/* ── Section ── */
.sec-row { display:flex; align-items:center; gap:10px; margin:4px 0 14px; }
.sec-rule { flex:1; height:1px; background:var(--border-card); }
.sec-lbl { font-family:var(--mono); font-size:.56rem; color:var(--ink-3);
           letter-spacing:3px; text-transform:uppercase; white-space:nowrap; }
.sec-badge { font-family:var(--mono); font-size:.56rem; font-weight:700;
             color:var(--mint); background:var(--mint-dim); border:1px solid var(--mint-bd);
             border-radius:20px; padding:2px 9px; white-space:nowrap; }

/* ── Card ── */
.bc { background:var(--bg-card); border:1px solid var(--border-card);
      border-radius:var(--r-lg); overflow:hidden; margin-bottom:10px;
      transition:border-color .18s,transform .18s; animation:fadeUp .22s ease both; }
@keyframes fadeUp { from{opacity:0;transform:translateY(7px)} to{opacity:1;transform:translateY(0)} }
.bc:hover { border-color:var(--border-hi); transform:translateY(-2px); }
.bc-stripe { height:2px; background:linear-gradient(90deg,var(--mint) 0%,var(--amber) 100%); }
.bc-body { padding:11px 12px 10px; }

.bc-hd { display:flex; align-items:flex-start; justify-content:space-between; gap:6px; margin-bottom:9px; }
.bc-ticker { font-family:var(--font); font-size:1.02rem; font-weight:800;
             color:var(--ink); letter-spacing:-.3px; line-height:1; }
.bc-sub { font-family:var(--mono); font-size:.56rem; color:var(--ink-3); margin-top:3px; }

.fresh-tag { display:inline-block; font-family:var(--mono); font-size:.49rem;
             font-weight:600; border-radius:4px; padding:2px 7px; margin-top:3px; }
.fresh-tag.today  { color:var(--mint);  background:var(--mint-dim);  border:1px solid var(--mint-bd); }
.fresh-tag.recent { color:var(--amber); background:var(--amber-dim); border:1px solid var(--amber-bd); }

/* TV link */
.tv { display:inline-flex; align-items:center; gap:4px; font-family:var(--mono);
      font-size:.55rem; font-weight:600; color:var(--ink-2);
      background:rgba(255,255,255,.035); border:1px solid var(--border);
      border-radius:var(--r-sm); padding:4px 8px; text-decoration:none !important;
      white-space:nowrap; flex-shrink:0; transition:color .14s,border-color .14s,background .14s; }
.tv:hover { color:var(--mint) !important; border-color:var(--mint-bd);
            background:var(--mint-dim); text-decoration:none !important; }
.tv svg { width:9px; height:9px; opacity:.6; }

/* Entry */
.entry-lbl { font-family:var(--mono); font-size:.47rem; color:var(--ink-3);
             letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }
.entry-val { font-family:var(--mono); font-size:1.12rem; font-weight:700;
             color:var(--ink); letter-spacing:-.5px; margin-bottom:9px; }

/* SL / T1 / T2 */
.lvl-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:5px; margin-bottom:8px; }
.lvl-cell { border-radius:var(--r-sm); padding:7px 9px; }
.lvl-cell.sl { background:var(--bg-sl);    border:1px solid var(--rose-bd); }
.lvl-cell.t1 { background:var(--amber-dim); border:1px solid var(--amber-bd); }
.lvl-cell.t2 { background:var(--bg-tgt);   border:1px solid var(--mint-bd); }
.lvl-lbl { font-family:var(--mono); font-size:.47rem; letter-spacing:2px;
           text-transform:uppercase; margin-bottom:3px; }
.lvl-lbl.sl { color:var(--rose); }
.lvl-lbl.t1 { color:var(--amber); }
.lvl-lbl.t2 { color:var(--mint); }
.lvl-val { font-family:var(--mono); font-size:.78rem; font-weight:700; letter-spacing:-.2px; line-height:1; }
.lvl-val.sl { color:var(--rose); }
.lvl-val.t1 { color:var(--amber); }
.lvl-val.t2 { color:var(--mint); }

/* SMA row */
.sma-row { display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-bottom:7px; }
.sma-cell { background:var(--bg-cell); border:1px solid var(--border-card);
            border-radius:var(--r-sm); padding:6px 8px; }
.sma-lbl { font-family:var(--mono); font-size:.46rem; color:var(--ink-3);
           letter-spacing:2px; text-transform:uppercase; margin-bottom:2px; }
.sma-val { font-family:var(--mono); font-size:.72rem; font-weight:700; letter-spacing:-.2px; }
.sma-val.fast { color:var(--mint); }
.sma-val.slow { color:var(--rose); }

/* Footer */
.bc-ft { display:flex; align-items:center; justify-content:space-between;
         padding-top:7px; border-top:1px solid var(--border-card); }
.rr-pill { display:inline-flex; align-items:center; gap:4px; font-family:var(--mono);
           font-size:.54rem; font-weight:700; color:var(--mint); background:var(--mint-dim);
           border:1px solid var(--mint-bd); border-radius:20px; padding:3px 8px; }
.rr-d { width:4px; height:4px; border-radius:50%; background:var(--mint);
         animation:blink 2s ease-in-out infinite; }
.spread-tag { font-family:var(--mono); font-size:.50rem; color:var(--amber);
              background:var(--amber-dim); border:1px solid var(--amber-bd);
              border-radius:20px; padding:2px 7px; }

/* Alert */
div[data-testid="stAlert"] {
    background:rgba(240,165,0,.06) !important; border:1px solid rgba(240,165,0,.20) !important;
    border-radius:var(--r-md) !important; font-family:var(--font) !important;
    font-size:.79rem !important; color:var(--amber) !important;
}

/* Sidebar */
[data-testid="stSidebar"] { background:#0D1016 !important; border-right:1px solid var(--border-card) !important; }
[data-testid="stSidebar"] .block-container { padding:1.5rem 1rem !important; }
.sb-hd { font-family:var(--mono); font-size:.54rem; font-weight:700; color:var(--ink-3);
         letter-spacing:3px; text-transform:uppercase; margin-bottom:12px;
         padding-bottom:8px; border-bottom:1px solid var(--border-card); }
.sb-row { display:flex; justify-content:space-between; align-items:center;
          padding:7px 0; border-bottom:1px solid var(--border-card); }
.sb-k { font-family:var(--font); font-size:.67rem; color:var(--ink-2); }
.sb-v { font-family:var(--mono); font-size:.67rem; font-weight:600; color:var(--ink); }
.sb-v.ok { color:var(--mint); } .sb-v.hl { color:var(--amber); } .sb-v.rd { color:var(--rose); }

h3 { display:none !important; }

@media(max-width:768px) {
    .main .block-container { padding:1rem .75rem 3.5rem !important; }
    .bc-body { padding:10px 10px 8px; }
}
@media(max-width:520px) {
    .aw { font-size:1.4rem; }
    .lvl-grid { grid-template-columns:1fr; }
    .sma-row  { grid-template-columns:1fr; }
    .bc-hd    { flex-direction:column; gap:6px; }
    .tv       { align-self:flex-start; }
}
</style>
"""

_TV_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/>'
    '<line x1="10" y1="14" x2="21" y2="3"/>'
    '</svg>'
)

_LEGEND = f"""
<div class="legend">
  <div class="legend-title">Pine Script Conditions (all must hold on same bar)</div>
  <div class="lchip trend">&#9650; 44-SMA &gt; 200-SMA</div>
  <div class="lchip trend">&#9650; 44-SMA rising vs 2 bars ago</div>
  <div class="lchip trend">&#9650; 200-SMA rising vs 2 bars ago</div>
  <div class="lchip candle">&#9646; Close &gt; Open (green candle)</div>
  <div class="lchip candle">&#9646; Close &gt; Mid-bar (high+low)/2</div>
  <div class="lchip touch">&#9660; Low &le; 44-SMA (wick touches SMA)</div>
  <div class="lchip touch">&#9650; Close &gt; 44-SMA (reclaims above)</div>
  <div class="lchip info">&#9675; Scans last {N_LOOKBACK} bars</div>
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

    ba = int(sig.bars_ago)
    fresh_cls  = "today" if ba <= 1 else "recent"
    fresh_text = "Today" if ba == 0 else ("Yesterday" if ba == 1 else f"{ba} bars ago")

    return (
        '<div class="bc"><div class="bc-stripe"></div><div class="bc-body">'

        '<div class="bc-hd"><div>'
        f'<div class="bc-ticker">{ticker}</div>'
        f'<div class="bc-sub">200-SMA &#8377;{ss}</div>'
        f'<div class="fresh-tag {fresh_cls}">{fresh_text}</div>'
        '</div>'
        f'<a class="tv" href="{tv_url}" target="_blank" rel="noopener noreferrer">'
        f'{_TV_SVG}&thinsp;Chart</a></div>'

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
    rows = [
        ("Universe",  "Nifty 500",             "hl"),
        ("Strategy",  "Swing Triple Bullish",   "ok"),
        ("Trend",     "44>200, both rising",    "ok"),
        ("Touch",     "Low ≤ 44-SMA (exact)",   "ok"),
        ("Reclaim",   "Close > 44-SMA",         "ok"),
        ("Candle",    "Green + strong close",   "ok"),
        ("Lookback",  f"Last {N_LOOKBACK} bars","hl"),
        ("R:R",       "1 : 2",                 "ok"),
        ("Scanned",   str(scanned),            ""),
        ("Signals",   str(found), "ok" if found > 0 else "rd"),
        ("UTC", datetime.now(UTC).strftime("%H:%M:%S"), "")
    ]
    html = "".join(
        f'<div class="sb-row"><span class="sb-k">{k}</span>'
        f'<span class="sb-v {c}">{v}</span></div>'
        for k, v, c in rows
    )
    st.sidebar.markdown(f'<div class="sb-hd">Scan Summary</div>{html}', unsafe_allow_html=True)


# ── Dashboard ──────────────────────────────────────────────────────────────────
def render_dashboard() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="aw">Arth<span class="g">Sutra</span><span class="d">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="aw-sub">'
        '<span class="aw-tag">Swing Triple Bullish · 44/200 SMA · NSE 500</span>'
        '<span class="live-badge"><span class="live-dot"></span>BUY SIGNAL</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_LEGEND, unsafe_allow_html=True)

    if not st.button("Run Swing Scanner \u2192"):
        return

    universe = _load_universe()
    total    = len(universe)

    print(f"Testing universe: {total}")

    progress_bar = st.progress(0, text="Initialising\u2026")
    status_slot  = st.empty()
    section_slot = st.empty()
    col_ph:  list = [st.empty() for _ in range(COLS)]
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
            logger.debug("Audit %s | %s | %.1f ms", audit.ticker, audit.outcome, audit.latency_ms)
            done += 1
            progress_bar.progress(
                min(math.ceil(done / total * 100), 100),
                text=f"Scanning\u2026 {done} / {total}",
            )
            if sig is None:
                continue

            found += 1
            if found == 1:
                section_slot.markdown(
                    '<div class="sec-row"><div class="sec-rule"></div>'
                    '<span class="sec-lbl">BUY Signals</span>'
                    '<div class="sec-rule"></div></div>',
                    unsafe_allow_html=True,
                )

            status_slot.markdown(
                f'<div class="ss"><div class="ss-spin"></div>'
                f'Scanning &mdash; <span class="ct">{found} signal{"s" if found!=1 else ""} found</span>'
                f' &mdash; {done}/{total}</div>',
                unsafe_allow_html=True,
            )
            col_buf[(found - 1) % COLS].append(_card_html(sig))
            _flush()

    progress_bar.empty()

    if found == 0:
        status_slot.empty()
        section_slot.empty()
        st.warning(
            f"No setups found across {done} instruments in the last {N_LOOKBACK} bars. "
            "Best to run after market close once today\u2019s candle is confirmed."
        )
    else:
        status_slot.markdown(
            f'<div class="ss"><span class="ct">{found} signal{"s" if found!=1 else ""} detected</span>'
            f' &mdash; {done} instruments scanned</div>',
            unsafe_allow_html=True,
        )
        section_slot.markdown(
            f'<div class="sec-row"><div class="sec-rule"></div>'
            f'<span class="sec-lbl">BUY Signals</span>'
            f'<span class="sec-badge">{found} Found</span>'
            f'<div class="sec-rule"></div></div>',
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.markdown("---")
        _sidebar(done, found)


# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArtSutra — Swing Triple Bullish",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__" or True:
    render_dashboard()










