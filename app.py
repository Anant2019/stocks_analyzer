"""
arth_sutra_engine.py
Production-grade signal scanner | Python 3.12+ | Quant-tier quality

SWING TRIPLE BULLISH — exact port of Pine Script v5 logic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pine → Python mapping:

  s44  = ta.sma(close, 44)
  s200 = ta.sma(close, 200)

  is_trending = s44 > s200
                and s44  > s44[2]     ← 44-SMA rising over 2 bars
                and s200 > s200[2]    ← 200-SMA rising over 2 bars

  is_strong   = close > open          ← green candle
                and close > (high+low)/2   ← strong close (above mid-bar)

  buy = is_trending
        and is_strong
        and low  <= s44               ← low touches the 44-SMA
        and close > s44               ← close reclaims above 44-SMA

  sl_val   = low
  entry_val= close
  risk     = close - low
  tgt1     = close + risk             ← 1 : 1 R
  tgt2     = close + risk * 2         ← 1 : 2 R
"""

from __future__ import annotations

import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

import pandas as pd
import streamlit as st
import yfinance as yf

# ── Observability (backend only) ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arth_sutra.engine")

# ── Strategy constants (mirrors Pine Script literals) ─────────────────────────
SMA_FAST_WINDOW:    Final[int]   = 44
SMA_SLOW_WINDOW:    Final[int]   = 200
SLOPE_BARS:         Final[int]   = 2       # Pine: s44 > s44[2]  (2-bar lookback)
RISK_MULTIPLIER_T2: Final[float] = 2.0     # Pine: close + (risk * 2)
MIN_HISTORY_BARS:   Final[int]   = SMA_SLOW_WINDOW + SLOPE_BARS + 2
CONCURRENCY_LIMIT:  Final[int]   = 25
SCAN_LOOKBACK:      Final[str]   = "2y"
SCAN_INTERVAL:      Final[str]   = "1d"
CARDS_PER_ROW:      Final[int]   = 4

FALLBACK_UNIVERSE: Final[list[str]] = [
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS",
    "HINDALCO.NS", "COALINDIA.NS",
]


# ── Value object ──────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class TradingSignal:
    """
    Immutable result of a confirmed Swing Triple Bullish setup.
    Entry = close (Pine: entry_val = close)
    SL    = low   (Pine: sl_val   = low)
    Risk  = close - low
    T1    = close + risk
    T2    = close + risk * 2
    """
    ticker:            str
    entry:             float   # close of signal bar
    stop_loss:         float   # low of signal bar
    target_1:          float   # 1 : 1 R
    target_2:          float   # 1 : 2 R
    sma_fast:          float   # 44-SMA value
    sma_slow:          float   # 200-SMA value
    mid_bar:           float   # (high + low) / 2  — strong-close reference
    scanned_at:        datetime = field(default_factory=datetime.utcnow)

    @property
    def risk(self) -> float:
        return round(self.entry - self.stop_loss, 4)

    @property
    def rr(self) -> float:
        """Reward-to-risk for T2."""
        return round((self.target_2 - self.entry) / self.risk, 2) if self.risk > 0 else 0.0

    @property
    def sma_spread_pct(self) -> float:
        return round((self.sma_fast - self.sma_slow) / self.sma_slow * 100, 2) \
               if self.sma_slow else 0.0


@dataclass(slots=True)
class ScanAuditRecord:
    """Backend-only diagnostics."""
    ticker:     str
    outcome:    str
    reason:     str   = ""
    latency_ms: float = 0.0


# ── Signal computation — exact Pine Script logic ───────────────────────────────
def _compute_signal(ticker: str) -> tuple[TradingSignal | None, ScanAuditRecord]:
    """
    Implements the Pine Script indicator bar-by-bar on the most recent candle.

    Pine condition (verbatim):
        is_trending = s44 > s200 and s44 > s44[2] and s200 > s200[2]
        is_strong   = close > open and close > ((high + low) / 2)
        buy         = is_trending and is_strong and low <= s44 and close > s44
    """
    t0 = time.perf_counter()
    ms = lambda: round((time.perf_counter() - t0) * 1_000, 2)

    try:
        raw: pd.DataFrame = yf.download(
            ticker,
            period=SCAN_LOOKBACK,
            interval=SCAN_INTERVAL,
            progress=False,
            auto_adjust=True,
        )

        if len(raw) < MIN_HISTORY_BARS:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="INSUFFICIENT_DATA",
                reason=f"{len(raw)} bars < {MIN_HISTORY_BARS}.",
                latency_ms=ms(),
            )

        close_s: pd.Series = raw["Close"]
        high_s:  pd.Series = raw["High"]
        low_s:   pd.Series = raw["Low"]
        open_s:  pd.Series = raw["Open"]

        sma44:  pd.Series = close_s.rolling(SMA_FAST_WINDOW,  min_periods=SMA_FAST_WINDOW).mean()
        sma200: pd.Series = close_s.rolling(SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW).mean()

        # ── Current bar scalars (index -1) ────────────────────────────────────
        s44_now:  float = float(sma44.iloc[-1])
        s200_now: float = float(sma200.iloc[-1])

        # Pine: s44[2] and s200[2]  →  two bars ago = iloc[-3]
        s44_2ago:  float = float(sma44.iloc[-3])
        s200_2ago: float = float(sma200.iloc[-3])

        c:    float = float(close_s.iloc[-1])   # close
        h:    float = float(high_s.iloc[-1])    # high
        l:    float = float(low_s.iloc[-1])     # low
        o:    float = float(open_s.iloc[-1])    # open
        mid:  float = (h + l) / 2              # (high + low) / 2

        # ── Pine: is_trending ─────────────────────────────────────────────────
        is_trending: bool = (
            s44_now  > s200_now    # 44 > 200
            and s44_now  > s44_2ago    # 44-SMA rising (2-bar slope)
            and s200_now > s200_2ago   # 200-SMA rising (2-bar slope)
        )

        # ── Pine: is_strong ───────────────────────────────────────────────────
        is_strong: bool = (
            c > o          # green candle
            and c > mid    # strong close — above mid-bar
        )

        # ── Pine: buy ─────────────────────────────────────────────────────────
        buy: bool = (
            is_trending
            and is_strong
            and l  <= s44_now   # low touches 44-SMA (exact Pine condition)
            and c  >  s44_now   # close reclaims above 44-SMA
        )

        if not buy:
            reason_parts = []
            if not is_trending:
                reason_parts.append(
                    f"trend(44>{200}={s44_now>s200_now},"
                    f"44rise={s44_now>s44_2ago},"
                    f"200rise={s200_now>s200_2ago})"
                )
            if not is_strong:
                reason_parts.append(
                    f"strong(green={c>o},above_mid={c>mid})"
                )
            if not (l <= s44_now):
                reason_parts.append(f"touch(low={l:.2f}>sma44={s44_now:.2f})")
            if not (c > s44_now):
                reason_parts.append(f"reclaim(close={c:.2f}<=sma44={s44_now:.2f})")
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=" | ".join(reason_parts),
                latency_ms=ms(),
            )

        # ── Pine: trade levels ────────────────────────────────────────────────
        # entry_val = close,  sl_val = low,  risk = close - low
        risk:   float = c - l
        entry:  float = round(c, 2)
        sl:     float = round(l, 2)
        tgt1:   float = round(c + risk, 2)
        tgt2:   float = round(c + risk * RISK_MULTIPLIER_T2, 2)

        if risk <= 0:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=f"non-positive risk: {risk:.4f}",
                latency_ms=ms(),
            )

        signal = TradingSignal(
            ticker=ticker.replace(".NS", ""),
            entry=entry,
            stop_loss=sl,
            target_1=tgt1,
            target_2=tgt2,
            sma_fast=round(s44_now, 2),
            sma_slow=round(s200_now, 2),
            mid_bar=round(mid, 2),
        )
        return signal, ScanAuditRecord(ticker=ticker, outcome="SIGNAL", latency_ms=ms())

    except Exception as exc:
        logger.error("Error %s: %s", ticker, exc, exc_info=True)
        return None, ScanAuditRecord(
            ticker=ticker, outcome="ERROR", reason=str(exc),
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )


# ── Universe ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def _load_universe() -> list[str]:
    try:
        syms = pd.read_csv(
            "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            usecols=["Symbol"],
        )["Symbol"].tolist()
        logger.info("Universe: %d symbols loaded.", len(syms))
        return [f"{s}.NS" for s in syms]
    except Exception as exc:
        logger.warning("NSE fetch failed (%s). Using fallback.", exc)
        return list(FALLBACK_UNIVERSE)


# =============================================================================
# PRESENTATION LAYER
# Midnight dark · JetBrains Mono · 4-col streaming bento · zero technical noise
# =============================================================================

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:           #0B0E11;
    --bg-card:      #131722;
    --bg-cell:      #0D1016;
    --bg-target:    rgba(0, 210, 110, 0.055);
    --bg-sl:        rgba(240, 68, 96, 0.06);

    --border:       #252B33;
    --border-card:  #1A1F27;
    --border-hover: #353D47;

    --mint:         #00D47A;
    --mint-dim:     rgba(0, 212, 122, 0.09);
    --mint-border:  rgba(0, 212, 122, 0.18);

    --rose:         #F04460;
    --rose-dim:     rgba(240, 68, 96, 0.09);
    --rose-border:  rgba(240, 68, 96, 0.20);

    --amber:        #F0A500;
    --amber-dim:    rgba(240, 165, 0, 0.08);
    --amber-border: rgba(240, 165, 0, 0.18);

    --ink:          #E4E8EF;
    --ink-2:        #8D95A3;
    --ink-3:        #4A5260;

    --font:  'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono:  'JetBrains Mono', 'Fira Code', monospace;

    --r-xs: 4px;
    --r-sm: 6px;
    --r-md: 10px;
    --r-lg: 14px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background-color: var(--bg) !important;
    font-family: var(--font) !important;
    color: var(--ink) !important;
}
.main .block-container {
    padding: 1.75rem 1.5rem 4rem !important;
    max-width: 1440px !important;
}

/* ── Brand ── */
.aw {
    font-family: var(--font);
    font-size: clamp(1.5rem, 3.2vw, 2.1rem);
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -1px;
    line-height: 1;
}
.aw .g { color: var(--mint); }
.aw .d { color: var(--rose); opacity: 0.55; }

.aw-sub {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 7px;
    margin-bottom: 18px;
}
.aw-tag {
    font-family: var(--mono);
    font-size: 0.56rem;
    color: var(--ink-3);
    letter-spacing: 3.5px;
    text-transform: uppercase;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.55rem;
    font-weight: 700;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 2px 9px;
    letter-spacing: 0.8px;
}
.live-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--mint);
    animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.12} }

/* ── Logic legend ── */
.legend {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 16px;
    padding: 10px 14px;
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: var(--r-md);
}
.legend-title {
    font-family: var(--mono);
    font-size: 0.52rem;
    color: var(--ink-3);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    width: 100%;
    margin-bottom: 4px;
}
.lchip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 0.54rem;
    font-weight: 600;
    border-radius: 20px;
    padding: 3px 10px;
    letter-spacing: 0.3px;
}
.lchip.trend  { color: var(--mint);  background: var(--mint-dim);   border: 1px solid var(--mint-border); }
.lchip.candle { color: var(--amber); background: var(--amber-dim);  border: 1px solid var(--amber-border); }
.lchip.touch  { color: #A78BFA;     background: rgba(167,139,250,.08); border: 1px solid rgba(167,139,250,.18); }

/* ── CTA ── */
div.stButton > button {
    background: var(--mint) !important;
    color: #000 !important;
    font-family: var(--font) !important;
    font-size: 0.80rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    border: none !important;
    border-radius: var(--r-md) !important;
    padding: 12px 28px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: opacity .15s, transform .15s !important;
}
div.stButton > button:hover  { opacity:.85 !important; transform:translateY(-1px) !important; }
div.stButton > button:active { transform:translateY(0)  !important; }

/* ── Progress ── */
div[data-testid="stProgress"] > div > div { background: var(--mint) !important; }
div[data-testid="stProgress"] > div {
    background: var(--border-card) !important;
    border-radius: 4px !important;
}

/* ── Scan status strip ── */
.ss {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--ink-2);
    margin-bottom: 14px;
    padding: 8px 14px;
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: var(--r-md);
}
.ss .ct { color: var(--mint); font-weight: 700; }
@keyframes spin { to { transform: rotate(360deg); } }
.ss-spin {
    width: 10px; height: 10px;
    border: 1.5px solid var(--border);
    border-top-color: var(--mint);
    border-radius: 50%;
    animation: spin .65s linear infinite;
    flex-shrink: 0;
}

/* ── Section divider ── */
.sec-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 4px 0 14px;
}
.sec-rule { flex:1; height:1px; background: var(--border-card); }
.sec-lbl {
    font-family: var(--mono);
    font-size: 0.56rem;
    color: var(--ink-3);
    letter-spacing: 3px;
    text-transform: uppercase;
    white-space: nowrap;
}
.sec-badge {
    font-family: var(--mono);
    font-size: 0.56rem;
    font-weight: 700;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 2px 9px;
    white-space: nowrap;
}

/* ── Bento card ── */
.bc {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: var(--r-lg);
    overflow: hidden;
    margin-bottom: 10px;
    transition: border-color .18s, transform .18s;
    animation: fadeUp .22s ease both;
}
@keyframes fadeUp {
    from { opacity:0; transform:translateY(7px); }
    to   { opacity:1; transform:translateY(0); }
}
.bc:hover { border-color: var(--border-hover); transform: translateY(-2px); }

/* Top stripe: mint (SMA44 color in Pine) → amber */
.bc-stripe {
    height: 2px;
    background: linear-gradient(90deg, var(--mint) 0%, var(--amber) 100%);
}

.bc-body { padding: 11px 12px 10px; }

/* Card header */
.bc-hd {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 9px;
}
.bc-ticker {
    font-family: var(--font);
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -.3px;
    line-height: 1;
}
.bc-ltp {
    font-family: var(--mono);
    font-size: 0.56rem;
    color: var(--ink-3);
    margin-top: 3px;
}

/* TradingView link */
.tv {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.55rem;
    font-weight: 600;
    color: var(--ink-2);
    background: rgba(255,255,255,.035);
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    padding: 4px 8px;
    text-decoration: none !important;
    white-space: nowrap;
    flex-shrink: 0;
    transition: color .14s, border-color .14s, background .14s;
}
.tv:hover {
    color: var(--mint) !important;
    border-color: var(--mint-border);
    background: var(--mint-dim);
    text-decoration: none !important;
}
.tv svg { width:9px; height:9px; opacity:.6; }

/* ── Entry label (Pine: plot close as entry) ── */
.entry-label {
    font-family: var(--mono);
    font-size: 0.48rem;
    color: var(--ink-3);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 5px;
}
.entry-val {
    font-family: var(--mono);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -.5px;
    margin-bottom: 9px;
}

/* SL / Targets grid (mirrors Pine cross plots) */
.lvl-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 5px;
    margin-bottom: 8px;
}
.lvl-cell {
    border-radius: var(--r-sm);
    padding: 7px 9px;
}
.lvl-cell.sl  { background: var(--bg-sl);     border: 1px solid var(--rose-border); }
.lvl-cell.t1  { background: var(--amber-dim); border: 1px solid var(--amber-border); }
.lvl-cell.t2  { background: var(--bg-target); border: 1px solid var(--mint-border); }

.lvl-lbl {
    font-family: var(--mono);
    font-size: 0.48rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.lvl-lbl.sl { color: var(--rose); }
.lvl-lbl.t1 { color: var(--amber); }
.lvl-lbl.t2 { color: var(--mint); }

.lvl-val {
    font-family: var(--mono);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: -.2px;
    line-height: 1;
}
.lvl-val.sl { color: var(--rose); }
.lvl-val.t1 { color: var(--amber); }
.lvl-val.t2 { color: var(--mint); }

/* SMA bar */
.sma-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
    margin-bottom: 7px;
}
.sma-cell {
    background: var(--bg-cell);
    border: 1px solid var(--border-card);
    border-radius: var(--r-sm);
    padding: 6px 8px;
}
.sma-lbl {
    font-family: var(--mono);
    font-size: 0.47rem;
    color: var(--ink-3);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.sma-val {
    font-family: var(--mono);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: -.2px;
}
.sma-val.fast { color: var(--mint); }   /* Pine: color.green */
.sma-val.slow { color: var(--rose); }   /* Pine: color.red */

/* Card footer */
.bc-ft {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 7px;
    border-top: 1px solid var(--border-card);
}
.rr-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.54rem;
    font-weight: 700;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 3px 8px;
}
.rr-d {
    width: 4px; height: 4px;
    border-radius: 50%;
    background: var(--mint);
    animation: blink 2s ease-in-out infinite;
}
.spread-tag {
    font-family: var(--mono);
    font-size: 0.50rem;
    color: var(--amber);
    background: var(--amber-dim);
    border: 1px solid var(--amber-border);
    border-radius: 20px;
    padding: 2px 7px;
}

/* ── Alert ── */
div[data-testid="stAlert"] {
    background: rgba(240,165,0,.06) !important;
    border: 1px solid rgba(240,165,0,.20) !important;
    border-radius: var(--r-md) !important;
    font-family: var(--font) !important;
    font-size: 0.79rem !important;
    color: var(--amber) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D1016 !important;
    border-right: 1px solid var(--border-card) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }

.sb-hd {
    font-family: var(--mono);
    font-size: 0.54rem;
    font-weight: 700;
    color: var(--ink-3);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-card);
}
.sb-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--border-card);
}
.sb-k { font-family: var(--font);  font-size: 0.67rem; color: var(--ink-2); }
.sb-v { font-family: var(--mono); font-size: 0.67rem; font-weight: 600; color: var(--ink); }
.sb-v.ok { color: var(--mint); }
.sb-v.hl { color: var(--amber); }
.sb-v.rd { color: var(--rose); }

/* ── Global ── */
h3 { display: none !important; }

/* ── Responsive ── */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem .75rem 3.5rem !important; }
    .bc-body                { padding: 10px 10px 8px; }
}
@media (max-width: 520px) {
    .aw        { font-size: 1.4rem; }
    .lvl-grid  { grid-template-columns: 1fr; }
    .sma-row   { grid-template-columns: 1fr; }
    .bc-hd     { flex-direction: column; gap: 6px; }
    .tv        { align-self: flex-start; }
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

# Logic legend: maps every Pine variable to a user-readable chip
_LEGEND = """
<div class="legend">
  <div class="legend-title">Pine Script Logic — Active Filters</div>
  <div class="lchip trend">&#9650; 44-SMA &gt; 200-SMA</div>
  <div class="lchip trend">&#9650; 44-SMA rising (2-bar)</div>
  <div class="lchip trend">&#9650; 200-SMA rising (2-bar)</div>
  <div class="lchip candle">&#9646; Close &gt; Open (green)</div>
  <div class="lchip candle">&#9646; Close &gt; Mid-bar</div>
  <div class="lchip touch">&#9670; Low &le; 44-SMA (touch)</div>
  <div class="lchip touch">&#9670; Close &gt; 44-SMA (reclaim)</div>
</div>
"""


def _card_html(sig: TradingSignal) -> str:
    """
    Resolves every field to plain str before interpolation.
    Layout mirrors the Pine Script plot order:
        plot(s44)  plot(s200)         → SMA row
        plotshape(buy, text="BUY")    → ticker / entry
        plot(sl_val)  cross red       → SL cell
        plot(tgt1)    cross orange    → T1 cell
        plot(tgt2)    cross blue→mint → T2 cell
    """
    ticker: str = str(sig.ticker)
    entry:  str = f"{float(sig.entry):,.2f}"
    sl:     str = f"{float(sig.stop_loss):,.2f}"
    t1:     str = f"{float(sig.target_1):,.2f}"
    t2:     str = f"{float(sig.target_2):,.2f}"
    rr:     str = f"{float(sig.rr):.2f}"
    sf:     str = f"{float(sig.sma_fast):,.2f}"
    ss:     str = f"{float(sig.sma_slow):,.2f}"
    spd:    str = f"{float(sig.sma_spread_pct):.2f}"
    mid:    str = f"{float(sig.mid_bar):,.2f}"
    tv_url: str = f"https://www.tradingview.com/chart/?symbol=NSE%3A{ticker}"

    return (
        '<div class="bc">'
          '<div class="bc-stripe"></div>'
          '<div class="bc-body">'

            # ── Header ──────────────────────────────────────────────────────
            '<div class="bc-hd">'
              '<div>'
                f'<div class="bc-ticker">{ticker}</div>'
                f'<div class="bc-ltp">Mid-bar &#8377;{mid}</div>'
              '</div>'
              f'<a class="tv" href="{tv_url}" target="_blank" rel="noopener noreferrer">'
                f'{_TV_SVG}&thinsp;Chart'
              '</a>'
            '</div>'

            # ── Entry (Pine: entry_val = close) ───────────────────────────
            '<div class="entry-label">Entry (Close)</div>'
            f'<div class="entry-val">&#8377;{entry}</div>'

            # ── SL / T1 / T2 — mirrors Pine cross plots ───────────────────
            '<div class="lvl-grid">'
              '<div class="lvl-cell sl">'
                '<div class="lvl-lbl sl">&#10007; Stop Loss</div>'
                f'<div class="lvl-val sl">&#8377;{sl}</div>'
              '</div>'
              '<div class="lvl-cell t1">'
                '<div class="lvl-lbl t1">&#9670; Target 1:1</div>'
                f'<div class="lvl-val t1">&#8377;{t1}</div>'
              '</div>'
              '<div class="lvl-cell t2">'
                '<div class="lvl-lbl t2">&#9670; Target 1:2</div>'
                f'<div class="lvl-val t2">&#8377;{t2}</div>'
              '</div>'
            '</div>'

            # ── SMA values (Pine: plot s44 green, s200 red) ───────────────
            '<div class="sma-row">'
              '<div class="sma-cell">'
                '<div class="sma-lbl">44-SMA (green)</div>'
                f'<div class="sma-val fast">&#8377;{sf}</div>'
              '</div>'
              '<div class="sma-cell">'
                '<div class="sma-lbl">200-SMA (red)</div>'
                f'<div class="sma-val slow">&#8377;{ss}</div>'
              '</div>'
            '</div>'

            # ── Footer ────────────────────────────────────────────────────
            '<div class="bc-ft">'
              '<div class="rr-pill"><span class="rr-d"></span>'
                f'R:R&thinsp;{rr}x'
              '</div>'
              f'<span class="spread-tag">44 leads 200 by +{spd}%</span>'
            '</div>'

          '</div>'
        '</div>'
    )


def _sidebar(scanned: int, found: int) -> None:
    rows: list[tuple[str, str, str]] = [
        ("Universe",   "Nifty 500",              "hl"),
        ("Strategy",   "Swing Triple Bullish",    "ok"),
        ("is_trending","44>200 · both rising",    "ok"),
        ("is_strong",  "Green · above mid-bar",   "ok"),
        ("buy filter", "Low≤44 · Close>44",       "ok"),
        ("SL",         "Signal bar Low",          "rd"),
        ("T1 / T2",    "1R · 2R from entry",      "ok"),
        ("Scanned",    str(scanned),              ""),
        ("Signals",    str(found), "ok" if found > 0 else ""),
        ("UTC",        datetime.utcnow().strftime("%H:%M:%S"), ""),
    ]
    rows_html = "".join(
        f'<div class="sb-row">'
        f'  <span class="sb-k">{k}</span>'
        f'  <span class="sb-v {c}">{v}</span>'
        f'</div>'
        for k, v, c in rows
    )
    st.sidebar.markdown(
        f'<div class="sb-hd">Pine Script Logic</div>{rows_html}',
        unsafe_allow_html=True,
    )


# ── Main dashboard ─────────────────────────────────────────────────────────────
def render_dashboard() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="aw">Arth<span class="g">Sutra</span>'
        '<span class="d">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="aw-sub">'
        '  <span class="aw-tag">Swing Triple Bullish · 44/200 SMA · NSE 500</span>'
        '  <span class="live-badge"><span class="live-dot"></span>BUY 50/50</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(_LEGEND, unsafe_allow_html=True)

    if not st.button("Run Swing Scanner \u2192"):
        return

    universe = _load_universe()
    total    = len(universe)

    progress_bar = st.progress(0, text="Initialising\u2026")
    status_slot  = st.empty()
    section_slot = st.empty()

    col_ph: list[st.empty] = [st.empty() for _ in range(CARDS_PER_ROW)]
    col_buf: list[list[str]] = [[] for _ in range(CARDS_PER_ROW)]

    found     = 0
    processed = 0

    def _flush() -> None:
        for ci, ph in enumerate(col_ph):
            if col_buf[ci]:
                ph.markdown("".join(col_buf[ci]), unsafe_allow_html=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY_LIMIT) as pool:
        fmap = {pool.submit(_compute_signal, t): t for t in universe}

        for future in as_completed(fmap):
            signal, audit = future.result()
            logger.debug(
                "Audit %s | %s | %.1f ms",
                audit.ticker, audit.outcome, audit.latency_ms,
            )
            processed += 1
            progress_bar.progress(
                min(math.ceil(processed / total * 100), 100),
                text=f"Scanning\u2026 {processed} / {total}",
            )

            if signal is None:
                continue

            found += 1

            if found == 1:
                section_slot.markdown(
                    '<div class="sec-row">'
                    '  <div class="sec-rule"></div>'
                    '  <span class="sec-lbl">BUY 50/50 Signals</span>'
                    '  <div class="sec-rule"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            status_slot.markdown(
                f'<div class="ss">'
                f'  <div class="ss-spin"></div>'
                f'  Scanning &mdash; '
                f'  <span class="ct">{found} setup{"s" if found != 1 else ""} found</span>'
                f'  &mdash; {processed}/{total}'
                f'</div>',
                unsafe_allow_html=True,
            )

            col_buf[(found - 1) % CARDS_PER_ROW].append(_card_html(signal))
            _flush()

    progress_bar.empty()

    if found == 0:
        status_slot.empty()
        section_slot.empty()
        st.warning(
            "No Swing Triple Bullish setups detected this session. "
            "All seven Pine conditions must hold on the same bar \u2014 "
            "the filter is intentionally strict."
        )
    else:
        status_slot.markdown(
            f'<div class="ss">'
            f'  <span class="ct">{found} BUY 50/50 setup{"s" if found != 1 else ""}</span>'
            f'  &mdash; {processed} instruments scanned'
            f'</div>',
            unsafe_allow_html=True,
        )
        section_slot.markdown(
            f'<div class="sec-row">'
            f'  <div class="sec-rule"></div>'
            f'  <span class="sec-lbl">BUY 50/50 Signals</span>'
            f'  <span class="sec-badge">{found} Found</span>'
            f'  <div class="sec-rule"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.markdown("---")
        _sidebar(processed, found)


# ── Entrypoint ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArtSutra — Swing Triple Bullish",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__" or True:
    render_dashboard()
