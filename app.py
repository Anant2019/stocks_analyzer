"""
arth_sutra_engine.py
Production-grade signal scanner | Python 3.12+ | HFT-tier quality
Midnight Dark Theme | Streaming Cards | Zero Technical Noise
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

# ── Observability (backend only — never surfaced in UI) ────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arth_sutra.engine")

# ── Domain Constants ───────────────────────────────────────────────────────────
SMA_FAST_WINDOW:    Final[int]   = 44
SMA_SLOW_WINDOW:    Final[int]   = 200
SUPPORT_TOLERANCE:  Final[float] = 1.03    # 3 % proximity band to 44 SMA
SL_BUFFER_FACTOR:   Final[float] = 0.998
RISK_MULTIPLIER_T2: Final[float] = 2.0
MIN_HISTORY_BARS:   Final[int]   = SMA_SLOW_WINDOW + 1
CONCURRENCY_LIMIT:  Final[int]   = 25
SCAN_LOOKBACK:      Final[str]   = "2y"
SCAN_INTERVAL:      Final[str]   = "1d"
CARDS_PER_ROW:      Final[int]   = 4       # compact 4-column grid

FALLBACK_UNIVERSE: Final[list[str]] = [
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS",
    "HINDALCO.NS", "COALINDIA.NS",
]

# ── Value Objects ──────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class TradingSignal:
    """Immutable value object representing a single actionable entry signal."""
    ticker:            str
    last_traded_price: float
    entry_trigger:     float
    stop_loss:         float
    target_1:          float
    target_2:          float
    sma_fast:          float    # 44-SMA value at signal bar
    sma_slow:          float    # 200-SMA value at signal bar
    sma_proximity_pct: float    # how close Low was to 44-SMA (%)
    scanned_at:        datetime = field(default_factory=datetime.utcnow)

    @property
    def risk_per_unit(self) -> float:
        return round(self.entry_trigger - self.stop_loss, 4)

    @property
    def reward_risk_ratio(self) -> float:
        return round((self.target_2 - self.entry_trigger) / self.risk_per_unit, 2) \
               if self.risk_per_unit else 0.0

    @property
    def sma_spread_pct(self) -> float:
        """44-SMA distance above 200-SMA, as a percentage."""
        return round((self.sma_fast - self.sma_slow) / self.sma_slow * 100, 2) \
               if self.sma_slow else 0.0


@dataclass(slots=True)
class ScanAuditRecord:
    """Backend-only diagnostics — never rendered to end-users."""
    ticker:     str
    outcome:    str
    reason:     str   = ""
    latency_ms: float = 0.0


# ── Data Acquisition ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_nifty500_universe() -> list[str]:
    nse_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        symbols: list[str] = pd.read_csv(nse_url, usecols=["Symbol"])["Symbol"].tolist()
        logger.info("Universe loaded: %d constituents from NSE.", len(symbols))
        return [f"{sym}.NS" for sym in symbols]
    except Exception as exc:
        logger.warning("NSE universe fetch failed (%s). Falling back to seed list.", exc)
        return FALLBACK_UNIVERSE


# ── Signal Computation ─────────────────────────────────────────────────────────
def _compute_signal(ticker: str) -> tuple[TradingSignal | None, ScanAuditRecord]:
    """
    Core Sutra strategy — restored full SMA logic:
      1. 44 SMA ABOVE 200 SMA  (trend confirmation)
      2. Both SMAs rising      (momentum confirmation)
      3. Low touches / near-touches 44 SMA within 3 %
      4. Bullish close (green candle)
    """
    t0 = time.perf_counter()
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
                reason=f"Only {len(raw)} bars; need {MIN_HISTORY_BARS}.",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        close: pd.Series = raw["Close"]
        high:  pd.Series = raw["High"]
        low:   pd.Series = raw["Low"]
        open_: pd.Series = raw["Open"]

        sma_fast: pd.Series = close.rolling(SMA_FAST_WINDOW,  min_periods=SMA_FAST_WINDOW).mean()
        sma_slow: pd.Series = close.rolling(SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW).mean()

        c_sf = float(sma_fast.iloc[-1]);  p_sf = float(sma_fast.iloc[-2])
        c_ss = float(sma_slow.iloc[-1]);  p_ss = float(sma_slow.iloc[-2])

        curr_close = float(close.iloc[-1])
        curr_high  = float(high.iloc[-1])
        curr_low   = float(low.iloc[-1])
        curr_open  = float(open_.iloc[-1])

        # ── Restored Sutra Criteria ───────────────────────────────────────────
        fast_above_slow  = c_sf > c_ss                       # 44 SMA > 200 SMA
        both_rising      = (c_sf > p_sf) and (c_ss > p_ss)  # both trending up
        near_44_support  = curr_low <= (c_sf * SUPPORT_TOLERANCE)
        bullish_candle   = curr_close > curr_open

        if not (fast_above_slow and both_rising and near_44_support and bullish_candle):
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=(f"f_above_s={fast_above_slow} rising={both_rising} "
                        f"support={near_44_support} green={bullish_candle}"),
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        entry_trigger = round(curr_high, 2)
        stop_loss     = round(curr_low * SL_BUFFER_FACTOR, 2)
        risk          = entry_trigger - stop_loss

        if risk <= 0:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=f"Non-positive risk: {risk}.",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        proximity_pct = round(abs(curr_low - c_sf) / c_sf * 100, 2)

        signal = TradingSignal(
            ticker=ticker.replace(".NS", ""),
            last_traded_price=round(curr_close, 2),
            entry_trigger=entry_trigger,
            stop_loss=stop_loss,
            target_1=round(entry_trigger + risk, 2),
            target_2=round(entry_trigger + risk * RISK_MULTIPLIER_T2, 2),
            sma_fast=round(c_sf, 2),
            sma_slow=round(c_ss, 2),
            sma_proximity_pct=proximity_pct,
        )
        return signal, ScanAuditRecord(
            ticker=ticker, outcome="SIGNAL",
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )

    except Exception as exc:
        logger.error("Error processing %s: %s", ticker, exc, exc_info=True)
        return None, ScanAuditRecord(
            ticker=ticker, outcome="ERROR", reason=str(exc),
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )


# ── Streaming scan — yields signals as they arrive ────────────────────────────
def stream_parallel_scan(universe: list[str]):
    """
    Generator that yields TradingSignal objects the instant each worker
    completes. Callers render cards progressively without waiting for the
    full 500-stock sweep to finish.
    """
    with ThreadPoolExecutor(max_workers=CONCURRENCY_LIMIT) as pool:
        future_map = {pool.submit(_compute_signal, t): t for t in universe}
        for future in as_completed(future_map):
            signal, audit = future.result()
            logger.debug("Audit: %s | %s | %.1f ms", audit.ticker, audit.outcome, audit.latency_ms)
            if signal is not None:
                yield signal


# =============================================================================
# PRESENTATION LAYER
# Midnight dark (#0B0E11) | JetBrains Mono | 4-col compact bento grid
# =============================================================================

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:           #0B0E11;
    --bg-card:      #131722;
    --bg-cell:      #0F1318;
    --bg-target:    rgba(0, 200, 100, 0.06);
    --border:       #2F3336;
    --border-card:  #1E2329;
    --border-hover: #3A3F45;

    --mint:         #00C87A;
    --mint-dim:     rgba(0, 200, 122, 0.10);
    --mint-border:  rgba(0, 200, 122, 0.18);

    --rose:         #F0465A;
    --rose-dim:     rgba(240, 70, 90, 0.10);

    --amber:        #F0A500;

    --ink:          #E8EBF0;
    --ink-2:        #9AA0AC;
    --ink-3:        #555D6B;

    --font:  'Inter', -apple-system, sans-serif;
    --mono:  'JetBrains Mono', 'Fira Code', monospace;

    --r-sm: 6px;
    --r-md: 10px;
    --r-lg: 14px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── App Shell ── */
.stApp {
    background-color: var(--bg) !important;
    font-family: var(--font) !important;
    color: var(--ink) !important;
}
.main .block-container {
    padding: 1.75rem 1.5rem 4rem !important;
    max-width: 1440px !important;
}

/* ── Wordmark ── */
.as-word {
    font-family: var(--font);
    font-size: clamp(1.6rem, 3.5vw, 2.2rem);
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -1px;
    line-height: 1;
}
.as-word .g { color: var(--mint); }
.as-word .r { color: var(--rose); opacity: 0.7; }

.as-sub {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 6px;
    margin-bottom: 22px;
}
.as-tag {
    font-family: var(--mono);
    font-size: 0.58rem;
    color: var(--ink-3);
    letter-spacing: 3px;
    text-transform: uppercase;
}
.live-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.56rem;
    font-weight: 600;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 2px 8px;
    letter-spacing: 1px;
}
.live-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--mint);
    animation: pulse 1.6s ease-in-out infinite;
}

/* ── Scan Button ── */
div.stButton > button {
    background: var(--mint) !important;
    color: #000 !important;
    font-family: var(--font) !important;
    font-size: 0.80rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    border: none !important;
    border-radius: var(--r-md) !important;
    padding: 12px 28px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: opacity 0.15s, transform 0.15s !important;
}
div.stButton > button:hover  { opacity: 0.88 !important; transform: translateY(-1px) !important; }
div.stButton > button:active { transform: translateY(0) !important; }

/* ── Progress bar override ── */
div[data-testid="stProgress"] > div > div {
    background: var(--mint) !important;
}
div[data-testid="stProgress"] > div {
    background: var(--border-card) !important;
    border-radius: 4px !important;
}

/* ── Scan status strip ── */
.scan-strip {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--ink-2);
    margin-bottom: 16px;
    padding: 8px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: var(--r-md);
}
.scan-strip .count { color: var(--mint); font-weight: 700; }
@keyframes spin {
    to { transform: rotate(360deg); }
}
.scan-spinner {
    width: 10px; height: 10px;
    border: 1.5px solid var(--border);
    border-top-color: var(--mint);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    flex-shrink: 0;
}

/* ── Section label ── */
.sec-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 4px 0 14px;
}
.sec-rule  { flex: 1; height: 1px; background: var(--border-card); }
.sec-label {
    font-family: var(--mono);
    font-size: 0.58rem;
    color: var(--ink-3);
    letter-spacing: 3px;
    text-transform: uppercase;
    white-space: nowrap;
}
.sec-badge {
    font-family: var(--mono);
    font-size: 0.58rem;
    font-weight: 700;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 2px 9px;
    white-space: nowrap;
}

/* ── Compact Bento Card ── */
.bc {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: var(--r-lg);
    overflow: hidden;
    margin-bottom: 10px;
    transition: border-color 0.18s, transform 0.18s;
    /* entry animation */
    animation: fadeUp 0.25s ease both;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.bc:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
}

.bc-stripe {
    height: 2px;
    background: linear-gradient(90deg, var(--mint) 0%, var(--amber) 100%);
}

.bc-body { padding: 12px 12px 10px; }

/* Card header */
.bc-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 10px;
}
.bc-ticker {
    font-family: var(--font);
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -0.3px;
    line-height: 1;
}
.bc-ltp {
    font-family: var(--mono);
    font-size: 0.58rem;
    color: var(--ink-3);
    margin-top: 3px;
}

/* TradingView link */
.tv-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.58rem;
    font-weight: 600;
    color: var(--ink-2);
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    padding: 4px 8px;
    text-decoration: none !important;
    white-space: nowrap;
    flex-shrink: 0;
    transition: color 0.14s, border-color 0.14s, background 0.14s;
}
.tv-link:hover {
    color: var(--mint) !important;
    border-color: var(--mint-border);
    background: var(--mint-dim);
    text-decoration: none !important;
}
.tv-link svg { width: 9px; height: 9px; opacity: 0.7; }

/* Entry / SL row */
.price-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-bottom: 6px;
}
.p-cell {
    background: var(--bg-cell);
    border: 1px solid var(--border-card);
    border-radius: var(--r-sm);
    padding: 7px 9px;
}
.p-lbl {
    font-family: var(--mono);
    font-size: 0.50rem;
    color: var(--ink-3);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.p-val {
    font-family: var(--mono);
    font-size: 0.80rem;
    font-weight: 700;
    letter-spacing: -0.2px;
    line-height: 1;
}
.p-val.entry { color: var(--ink); }
.p-val.sl    { color: var(--rose); }

/* Target row */
.tgt-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-bottom: 8px;
}
.t-cell {
    background: var(--bg-target);
    border: 1px solid var(--mint-border);
    border-radius: var(--r-sm);
    padding: 7px 9px;
}
.t-lbl {
    font-family: var(--mono);
    font-size: 0.50rem;
    color: var(--mint);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 3px;
    opacity: 0.55;
}
.t-val {
    font-family: var(--mono);
    font-size: 0.80rem;
    font-weight: 700;
    color: var(--mint);
    letter-spacing: -0.2px;
    line-height: 1;
}

/* SMA indicator bar */
.sma-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    padding: 5px 9px;
    background: var(--bg-cell);
    border: 1px solid var(--border-card);
    border-radius: var(--r-sm);
}
.sma-item {
    font-family: var(--mono);
    font-size: 0.52rem;
    color: var(--ink-3);
}
.sma-item span { color: var(--amber); font-weight: 600; }
.sma-sep { color: var(--border); font-size: 0.7rem; }

/* Card footer */
.bc-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 8px;
    border-top: 1px solid var(--border-card);
}
.rr-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.56rem;
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
    animation: pulse 2s ease-in-out infinite;
}
.prox-tag {
    font-family: var(--mono);
    font-size: 0.52rem;
    color: var(--amber);
    background: rgba(240,165,0,0.08);
    border: 1px solid rgba(240,165,0,0.18);
    border-radius: 20px;
    padding: 2px 7px;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.2; }
}

/* ── Alert / warning ── */
div[data-testid="stAlert"] {
    background: rgba(240,165,0,0.07) !important;
    border: 1px solid rgba(240,165,0,0.22) !important;
    border-radius: var(--r-md) !important;
    font-family: var(--font) !important;
    font-size: 0.80rem !important;
    color: var(--amber) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0F1318 !important;
    border-right: 1px solid var(--border-card) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }

.diag-hd {
    font-family: var(--mono);
    font-size: 0.56rem;
    font-weight: 700;
    color: var(--ink-3);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-card);
}
.diag-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--border-card);
}
.d-key { font-family: var(--font);  font-size: 0.68rem; color: var(--ink-2); }
.d-val { font-family: var(--mono); font-size: 0.68rem; font-weight: 600; color: var(--ink); }
.d-val.ok  { color: var(--mint); }
.d-val.hi  { color: var(--amber); }

/* ── Global overrides ── */
h3 { display: none !important; }

/* ── Responsive ── */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem 0.75rem 3.5rem !important; }
    .bc-body                { padding: 10px 10px 8px; }
}
@media (max-width: 520px) {
    .as-word      { font-size: 1.5rem; }
    .price-row    { grid-template-columns: 1fr; }
    .tgt-row      { grid-template-columns: 1fr; }
    .bc-head      { flex-direction: column; gap: 6px; }
    .tv-link      { align-self: flex-start; }
}
</style>
"""

# ── SVG icons ──────────────────────────────────────────────────────────────────
_TV_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/>'
    '<line x1="10" y1="14" x2="21" y2="3"/>'
    '</svg>'
)


# ── Card renderer ──────────────────────────────────────────────────────────────
def _card_html(sig: TradingSignal) -> str:
    """
    All fields resolved to plain Python str BEFORE template interpolation.
    Zero attribute-access inside the HTML string.
    """
    ticker:    str = str(sig.ticker)
    ltp:       str = f"{float(sig.last_traded_price):,.2f}"
    entry:     str = f"{float(sig.entry_trigger):,.2f}"
    sl:        str = f"{float(sig.stop_loss):,.2f}"
    t1:        str = f"{float(sig.target_1):,.2f}"
    t2:        str = f"{float(sig.target_2):,.2f}"
    rr:        str = f"{float(sig.reward_risk_ratio):.2f}"
    sma44:     str = f"{float(sig.sma_fast):,.2f}"
    sma200:    str = f"{float(sig.sma_slow):,.2f}"
    prox:      str = f"{float(sig.sma_proximity_pct):.2f}"
    ts:        str = sig.scanned_at.strftime("%H:%M")
    tv_url:    str = f"https://www.tradingview.com/chart/?symbol=NSE%3A{ticker}"

    return (
        '<div class="bc">'
          '<div class="bc-stripe"></div>'
          '<div class="bc-body">'

            # ── Header ──────────────────────────────────────────────────────
            '<div class="bc-head">'
              '<div>'
                f'<div class="bc-ticker">{ticker}</div>'
                f'<div class="bc-ltp">&#8377;{ltp}</div>'
              '</div>'
              f'<a class="tv-link" href="{tv_url}" target="_blank" rel="noopener noreferrer">'
                f'{_TV_SVG}&nbsp;Chart'
              '</a>'
            '</div>'

            # ── Entry / SL ───────────────────────────────────────────────────
            '<div class="price-row">'
              '<div class="p-cell">'
                '<div class="p-lbl">Buy Above</div>'
                f'<div class="p-val entry">&#8377;{entry}</div>'
              '</div>'
              '<div class="p-cell">'
                '<div class="p-lbl">Stop Loss</div>'
                f'<div class="p-val sl">&#8377;{sl}</div>'
              '</div>'
            '</div>'

            # ── Targets ──────────────────────────────────────────────────────
            '<div class="tgt-row">'
              '<div class="t-cell">'
                '<div class="t-lbl">Target 1</div>'
                f'<div class="t-val">&#8377;{t1}</div>'
              '</div>'
              '<div class="t-cell">'
                '<div class="t-lbl">Target 2</div>'
                f'<div class="t-val">&#8377;{t2}</div>'
              '</div>'
            '</div>'

            # ── SMA indicators ───────────────────────────────────────────────
            '<div class="sma-bar">'
              f'<span class="sma-item">SMA44 <span>{sma44}</span></span>'
              '<span class="sma-sep">|</span>'
              f'<span class="sma-item">SMA200 <span>{sma200}</span></span>'
              '<span class="sma-sep">|</span>'
              f'<span class="sma-item">&#9650; Fast above Slow</span>'
            '</div>'

            # ── Footer ───────────────────────────────────────────────────────
            '<div class="bc-foot">'
              '<div class="rr-pill"><span class="rr-d"></span>'
                f'R:R&nbsp;{rr}x'
              '</div>'
              f'<span class="prox-tag">&#8764;{prox}% to 44 SMA</span>'
            '</div>'

          '</div>'
        '</div>'
    )


def _sidebar_html(total: int, signal_count: int) -> None:
    """
    Sidebar shows only user-relevant summary.
    No error counts, worker counts, or latency metrics exposed.
    """
    rows: list[tuple[str, str, str]] = [
        ("Universe",  "Nifty 500",   "hi"),
        ("Scanned",   str(total),    ""),
        ("Signals",   str(signal_count), "ok" if signal_count > 0 else ""),
        ("Strategy",  "44/200 SMA",  "hi"),
        ("Condition", "Fast > Slow", "ok"),
        ("Risk:Reward","1 : 2",      "ok"),
        ("Scan UTC",  datetime.utcnow().strftime("%H:%M:%S"), ""),
    ]

    rows_html = "".join(
        f'<div class="diag-row">'
        f'  <span class="d-key">{k}</span>'
        f'  <span class="d-val {c}">{v}</span>'
        f'</div>'
        for k, v, c in rows
    )
    st.sidebar.markdown(
        f'<div class="diag-hd">Scan Summary</div>{rows_html}',
        unsafe_allow_html=True,
    )


# ── Main dashboard ─────────────────────────────────────────────────────────────
def render_dashboard() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    # Wordmark
    st.markdown(
        '<div class="as-word">Arth<span class="g">Sutra</span>'
        '<span class="r">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="as-sub">'
        '  <span class="as-tag">44 SMA &middot; Trend Filter &middot; NSE 500</span>'
        '  <span class="live-pill"><span class="live-dot"></span>LIVE</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not st.button("Run Signal Scan \u2192"):
        return

    universe = fetch_nifty500_universe()
    total    = len(universe)

    # ── Streaming progress UI ─────────────────────────────────────────────────
    progress_bar    = st.progress(0, text="Initialising scan engine\u2026")
    status_slot     = st.empty()    # live "X signals found" strip
    section_slot    = st.empty()    # section label appears after first hit
    col_slots       = [st.empty() for _ in range(CARDS_PER_ROW)]

    # Per-column card buffers
    col_cards: list[list[str]] = [[] for _ in range(CARDS_PER_ROW)]
    signals_found = 0
    processed     = 0

    def _flush_columns() -> None:
        """Re-render all four column placeholders from their buffers."""
        for ci, slot in enumerate(col_slots):
            with slot.container():
                cols = st.columns(CARDS_PER_ROW)
                for ci2, col in enumerate(cols):
                    with col:
                        if col_cards[ci2]:
                            st.markdown(
                                "".join(col_cards[ci2]),
                                unsafe_allow_html=True,
                            )

    with ThreadPoolExecutor(max_workers=CONCURRENCY_LIMIT) as pool:
        future_map = {pool.submit(_compute_signal, t): t for t in universe}

        for future in as_completed(future_map):
            signal, audit = future.result()
            logger.debug(
                "Audit: %s | %s | %.1f ms",
                audit.ticker, audit.outcome, audit.latency_ms,
            )
            processed += 1

            # Progress bar (pct complete)
            pct = math.ceil(processed / total * 100)
            progress_bar.progress(
                min(pct, 100),
                text=f"Scanning\u2026 {processed}/{total} instruments",
            )

            if signal is None:
                continue

            signals_found += 1

            # Show section header on first signal
            if signals_found == 1:
                section_slot.markdown(
                    '<div class="sec-row">'
                    '  <div class="sec-rule"></div>'
                    '  <span class="sec-label">Active Signals</span>'
                    '  <div class="sec-rule"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # Live status strip
            status_slot.markdown(
                f'<div class="scan-strip">'
                f'  <div class="scan-spinner"></div>'
                f'  Scanning &nbsp;&mdash;&nbsp; '
                f'  <span class="count">{signals_found} signal'
                f'{"s" if signals_found != 1 else ""} found</span>'
                f'  &nbsp;&mdash;&nbsp; {processed}/{total} processed'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Append card to correct column buffer and re-render
            col_idx = (signals_found - 1) % CARDS_PER_ROW
            col_cards[col_idx].append(_card_html(signal))
            _flush_columns()

    # ── Scan complete ─────────────────────────────────────────────────────────
    progress_bar.empty()

    if signals_found == 0:
        status_slot.empty()
        section_slot.empty()
        st.warning(
            "No signals found this session. "
            "Both SMAs must be rising with 44 SMA above 200 SMA \u2014 patience is the edge."
        )
        return

    # Final status (no spinner)
    status_slot.markdown(
        f'<div class="scan-strip">'
        f'  <span class="count">{signals_found} signal'
        f'{"s" if signals_found != 1 else ""} detected</span>'
        f'  &nbsp;&mdash;&nbsp; {processed} instruments scanned'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Update section label with final count
    section_slot.markdown(
        f'<div class="sec-row">'
        f'  <div class="sec-rule"></div>'
        f'  <span class="sec-label">Active Signals</span>'
        f'  <span class="sec-badge">{signals_found} Found</span>'
        f'  <div class="sec-rule"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("---")
        _sidebar_html(processed, signals_found)


# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArtSutra Pro",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__" or True:
    render_dashboard()
