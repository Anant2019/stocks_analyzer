"""
arth_sutra_engine.py
Production-grade signal scanner | Python 3.12+ | Quant-tier quality

TRIPLE BULLISH STRATEGY
━━━━━━━━━━━━━━━━━━━━━━
Condition 1 — Trend Alignment : 44_SMA > 200_SMA
Condition 2 — Positive Slope  : Both SMAs rising over last 5 candles
                                 (linear regression slope > 0, not just 1-bar diff)
Condition 3 — Touch Trigger   : Low[0] or Low[-1] ≤ 44_SMA × 1.005  (0.5 % buffer)
Condition 4 — Candle Confirm  : Close > Open  (green / bullish body)

ALL four conditions must be True simultaneously. Any bearish-leaning logic
(44_SMA < 200_SMA, resistance tests, etc.) is absent by design.
"""

from __future__ import annotations

import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ── Observability (backend only — never surfaces in the UI) ───────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arth_sutra.engine")

# ── Strategy constants ────────────────────────────────────────────────────────
SMA_FAST_WINDOW:      Final[int]   = 44
SMA_SLOW_WINDOW:      Final[int]   = 200
SLOPE_LOOKBACK:       Final[int]   = 5        # candles used for slope calculation
TOUCH_BUFFER:         Final[float] = 1.005    # 0.5 % above 44-SMA counts as "touch"
SL_BUFFER_FACTOR:     Final[float] = 0.998    # SL sits 0.2 % below the touch low
RISK_MULTIPLIER_T2:   Final[float] = 2.0      # 1 : 2 risk-reward for T2
MIN_HISTORY_BARS:     Final[int]   = SMA_SLOW_WINDOW + SLOPE_LOOKBACK + 2
CONCURRENCY_LIMIT:    Final[int]   = 25
SCAN_LOOKBACK:        Final[str]   = "2y"
SCAN_INTERVAL:        Final[str]   = "1d"
CARDS_PER_ROW:        Final[int]   = 4

FALLBACK_UNIVERSE: Final[list[str]] = [
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS",
    "HINDALCO.NS", "COALINDIA.NS",
]


# ── Value objects ─────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class TradingSignal:
    """Immutable result of a confirmed Triple Bullish setup."""
    ticker:            str
    last_traded_price: float
    entry_trigger:     float   # buy-stop above the signal candle high
    stop_loss:         float   # 0.2 % below the touch low
    target_1:          float   # 1 : 1 R
    target_2:          float   # 1 : 2 R
    sma_fast:          float   # 44-SMA at signal bar
    sma_slow:          float   # 200-SMA at signal bar
    sma_spread_pct:    float   # how far 44-SMA is above 200-SMA (%)
    touch_proximity_pct: float # how close Low was to 44-SMA (0 = exact touch)
    slope_fast:        float   # 44-SMA 5-bar linear slope (pts/bar)
    slope_slow:        float   # 200-SMA 5-bar linear slope (pts/bar)
    scanned_at:        datetime = field(default_factory=datetime.utcnow)

    @property
    def risk_per_unit(self) -> float:
        return round(self.entry_trigger - self.stop_loss, 4)

    @property
    def reward_risk_ratio(self) -> float:
        return (
            round((self.target_2 - self.entry_trigger) / self.risk_per_unit, 2)
            if self.risk_per_unit > 0 else 0.0
        )


@dataclass(slots=True)
class ScanAuditRecord:
    """Backend-only diagnostics — never rendered to end-users."""
    ticker:     str
    outcome:    str     # SIGNAL | FILTERED | INSUFFICIENT_DATA | ERROR
    reason:     str   = ""
    latency_ms: float = 0.0


# ── Helpers ───────────────────────────────────────────────────────────────────
def _linear_slope(series: np.ndarray) -> float:
    """
    Returns the OLS slope (points per bar) of the last `n` values.
    Uses closed-form formula — no scipy dependency.
    """
    n = len(series)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=np.float64)
    x_mean = x.mean()
    y_mean = series.mean()
    numerator   = float(((x - x_mean) * (series - y_mean)).sum())
    denominator = float(((x - x_mean) ** 2).sum())
    return numerator / denominator if denominator != 0 else 0.0


# ── Data acquisition ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_nifty500_universe() -> list[str]:
    nse_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        symbols: list[str] = (
            pd.read_csv(nse_url, usecols=["Symbol"])["Symbol"].tolist()
        )
        logger.info("Universe loaded: %d symbols from NSE.", len(symbols))
        return [f"{sym}.NS" for sym in symbols]
    except Exception as exc:
        logger.warning("NSE fetch failed (%s). Using fallback list.", exc)
        return FALLBACK_UNIVERSE


# ── Triple Bullish signal computation ────────────────────────────────────────
def _compute_signal(ticker: str) -> tuple[TradingSignal | None, ScanAuditRecord]:
    """
    Evaluates the Triple Bullish setup for a single ticker.

    The four gates are applied in order of cheapest-to-compute first
    so that slow I/O (yfinance download) is the only unavoidable cost.

    Gate 1  Trend  : sma_fast  > sma_slow           (44 > 200)
    Gate 2  Slope  : slope(sma_fast,  5) > 0        (44-SMA rising)
                     slope(sma_slow,  5) > 0        (200-SMA rising)
    Gate 3  Touch  : Low[0] ≤ sma_fast × 1.005  OR
                     Low[-1] ≤ sma_fast × 1.005     (current or prior candle)
    Gate 4  Candle : Close[0] > Open[0]             (green candle)
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
                reason=f"{len(raw)} bars < {MIN_HISTORY_BARS} required.",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        close: pd.Series = raw["Close"]
        high:  pd.Series = raw["High"]
        low:   pd.Series = raw["Low"]
        open_: pd.Series = raw["Open"]

        # ── Indicators ────────────────────────────────────────────────────────
        sma_fast: pd.Series = close.rolling(
            SMA_FAST_WINDOW, min_periods=SMA_FAST_WINDOW
        ).mean()
        sma_slow: pd.Series = close.rolling(
            SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW
        ).mean()

        # Scalar values for the signal candle (index -1)
        sf_now:  float = float(sma_fast.iloc[-1])
        ss_now:  float = float(sma_slow.iloc[-1])

        # 5-bar slope arrays  (iloc[-5:] → last 5 values including today)
        sf_window: np.ndarray = sma_fast.iloc[-SLOPE_LOOKBACK:].to_numpy(dtype=np.float64)
        ss_window: np.ndarray = sma_slow.iloc[-SLOPE_LOOKBACK:].to_numpy(dtype=np.float64)

        slope_sf: float = _linear_slope(sf_window)
        slope_ss: float = _linear_slope(ss_window)

        curr_close: float = float(close.iloc[-1])
        curr_open:  float = float(open_.iloc[-1])
        curr_high:  float = float(high.iloc[-1])
        curr_low:   float = float(low.iloc[-1])
        prev_low:   float = float(low.iloc[-2])

        touch_threshold: float = sf_now * TOUCH_BUFFER   # 44-SMA + 0.5 %

        # ── Gate 1 : Trend Alignment (44-SMA strictly above 200-SMA) ─────────
        trend_ok: bool = sf_now > ss_now
        if not trend_ok:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=f"G1_FAIL trend: sma44={sf_now:.2f} <= sma200={ss_now:.2f}",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        # ── Gate 2 : Positive Slope on both SMAs over last 5 candles ─────────
        slope_ok: bool = (slope_sf > 0.0) and (slope_ss > 0.0)
        if not slope_ok:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=(
                    f"G2_FAIL slope: sf={slope_sf:.4f} ss={slope_ss:.4f}"
                ),
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        # ── Gate 3 : Touch / Near-Touch of 44-SMA (current OR prior candle) ──
        touch_ok: bool = (curr_low <= touch_threshold) or (prev_low <= touch_threshold)
        if not touch_ok:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=(
                    f"G3_FAIL touch: low={curr_low:.2f} "
                    f"prev_low={prev_low:.2f} threshold={touch_threshold:.2f}"
                ),
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        # ── Gate 4 : Bullish Candle Confirmation ──────────────────────────────
        candle_ok: bool = curr_close > curr_open
        if not candle_ok:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=f"G4_FAIL candle: close={curr_close:.2f} <= open={curr_open:.2f}",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        # ── All gates passed — compute trade levels ───────────────────────────
        # Use the candle whose low touched the SMA as the reference low
        reference_low: float = curr_low if curr_low <= touch_threshold else prev_low

        entry_trigger: float = round(curr_high, 2)
        stop_loss:     float = round(reference_low * SL_BUFFER_FACTOR, 2)
        risk:          float = entry_trigger - stop_loss

        if risk <= 0:
            return None, ScanAuditRecord(
                ticker=ticker, outcome="FILTERED",
                reason=f"G5_FAIL non-positive risk: {risk:.4f}",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )

        # Proximity: 0 % = exact touch, positive = how far above the SMA low is
        touch_proximity_pct: float = round(
            abs(reference_low - sf_now) / sf_now * 100, 3
        )

        signal = TradingSignal(
            ticker=ticker.replace(".NS", ""),
            last_traded_price=round(curr_close, 2),
            entry_trigger=entry_trigger,
            stop_loss=stop_loss,
            target_1=round(entry_trigger + risk, 2),
            target_2=round(entry_trigger + risk * RISK_MULTIPLIER_T2, 2),
            sma_fast=round(sf_now, 2),
            sma_slow=round(ss_now, 2),
            sma_spread_pct=round((sf_now - ss_now) / ss_now * 100, 2),
            touch_proximity_pct=touch_proximity_pct,
            slope_fast=round(slope_sf, 4),
            slope_slow=round(slope_ss, 4),
        )
        return signal, ScanAuditRecord(
            ticker=ticker, outcome="SIGNAL",
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )

    except Exception as exc:
        logger.error("Unhandled error processing %s: %s", ticker, exc, exc_info=True)
        return None, ScanAuditRecord(
            ticker=ticker, outcome="ERROR", reason=str(exc),
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )


# ── Universe acquisition ──────────────────────────────────────────────────────
def fetch_nifty500_universe() -> list[str]:  # type: ignore[override]
    # Re-declared without @st.cache_data so it can be called inside a thread
    # context; the cached version is used when called from render_dashboard.
    pass  # shadowed below — see entrypoint note


# =============================================================================
# PRESENTATION LAYER
# Midnight dark (#0B0E11) · JetBrains Mono · 4-col streaming bento grid
# No technical noise surfaced to the user (no workers / ms / error counts)
# =============================================================================

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:            #0B0E11;
    --bg-card:       #131722;
    --bg-cell:       #0D1016;
    --bg-target:     rgba(0, 210, 110, 0.055);

    --border:        #2A2F35;
    --border-card:   #1A1F27;
    --border-hover:  #383E47;

    --mint:          #00D47A;
    --mint-dim:      rgba(0, 212, 122, 0.09);
    --mint-border:   rgba(0, 212, 122, 0.16);

    --rose:          #F04460;
    --amber:         #F0A500;
    --amber-dim:     rgba(240, 165, 0, 0.08);
    --amber-border:  rgba(240, 165, 0, 0.16);

    --ink:           #E4E8EF;
    --ink-2:         #8D95A3;
    --ink-3:         #4E5663;

    --font:  'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono:  'JetBrains Mono', 'Fira Code', monospace;

    --r-xs: 4px;
    --r-sm: 6px;
    --r-md: 10px;
    --r-lg: 14px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Shell ── */
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
.aw {
    font-family: var(--font);
    font-size: clamp(1.5rem, 3.2vw, 2.1rem);
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -1px;
    line-height: 1;
}
.aw .g { color: var(--mint); }
.aw .d { color: var(--rose); opacity: 0.6; }

.aw-sub {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 7px;
    margin-bottom: 20px;
}
.aw-tag {
    font-family: var(--mono);
    font-size: 0.57rem;
    color: var(--ink-3);
    letter-spacing: 3.5px;
    text-transform: uppercase;
}

/* Triple-Bullish badge */
.tb-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 0.56rem;
    font-weight: 700;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 2px 9px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
.tb-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--mint);
    animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.15} }

/* ── CTA Button ── */
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
    transition: opacity 0.15s, transform 0.15s !important;
}
div.stButton > button:hover  { opacity: 0.85 !important; transform: translateY(-1px) !important; }
div.stButton > button:active { transform: translateY(0) !important; }

/* ── Progress bar ── */
div[data-testid="stProgress"] > div > div { background: var(--mint) !important; }
div[data-testid="stProgress"] > div {
    background: var(--border-card) !important;
    border-radius: 4px !important;
}

/* ── Live scan strip ── */
.ss {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--mono);
    font-size: 0.63rem;
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
    animation: spin 0.65s linear infinite;
    flex-shrink: 0;
}

/* ── Strategy gate legend ── */
.gate-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 18px;
}
.gate-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 0.55rem;
    font-weight: 600;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 3px 10px;
    letter-spacing: 0.4px;
}
.gate-chip .n {
    font-size: 0.50rem;
    opacity: 0.55;
    margin-right: 2px;
}

/* ── Section row ── */
.sec-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 4px 0 14px;
}
.sec-rule  { flex: 1; height: 1px; background: var(--border-card); }
.sec-lbl {
    font-family: var(--mono);
    font-size: 0.57rem;
    color: var(--ink-3);
    letter-spacing: 3px;
    text-transform: uppercase;
    white-space: nowrap;
}
.sec-badge {
    font-family: var(--mono);
    font-size: 0.57rem;
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
    animation: fadeUp 0.22s ease both;
}
@keyframes fadeUp {
    from { opacity:0; transform: translateY(7px); }
    to   { opacity:1; transform: translateY(0); }
}
.bc:hover { border-color: var(--border-hover); transform: translateY(-2px); }

/* Gradient top-stripe: mint → amber (full-bull palette) */
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
    letter-spacing: -0.3px;
    line-height: 1;
}
.bc-ltp {
    font-family: var(--mono);
    font-size: 0.57rem;
    color: var(--ink-3);
    margin-top: 3px;
}

/* TradingView chart link */
.tv {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 0.56rem;
    font-weight: 600;
    color: var(--ink-2);
    background: rgba(255,255,255,0.035);
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
.tv svg { width: 9px; height: 9px; opacity: .65; }

/* Entry / SL cells */
.pr {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
    margin-bottom: 5px;
}
.pc {
    background: var(--bg-cell);
    border: 1px solid var(--border-card);
    border-radius: var(--r-sm);
    padding: 7px 9px;
}
.pc-l {
    font-family: var(--mono);
    font-size: 0.49rem;
    color: var(--ink-3);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.pc-v {
    font-family: var(--mono);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: -0.2px;
    line-height: 1;
}
.pc-v.en { color: var(--ink); }
.pc-v.sl { color: var(--rose); }

/* Target cells */
.tr {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
    margin-bottom: 7px;
}
.tc {
    background: var(--bg-target);
    border: 1px solid var(--mint-border);
    border-radius: var(--r-sm);
    padding: 7px 9px;
}
.tc-l {
    font-family: var(--mono);
    font-size: 0.49rem;
    color: var(--mint);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 3px;
    opacity: .5;
}
.tc-v {
    font-family: var(--mono);
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--mint);
    letter-spacing: -0.2px;
    line-height: 1;
}

/* SMA indicator row */
.si {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 8px;
    margin-bottom: 7px;
    background: var(--bg-cell);
    border: 1px solid var(--border-card);
    border-radius: var(--r-sm);
}
.si-item {
    font-family: var(--mono);
    font-size: 0.50rem;
    color: var(--ink-3);
}
.si-item b { color: var(--amber); font-weight: 600; }
.si-sep { color: var(--border); }

/* Slope row (positive slope confirmation display) */
.slope-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
    margin-bottom: 7px;
}
.sl-cell {
    background: var(--bg-cell);
    border: 1px solid var(--border-card);
    border-radius: var(--r-sm);
    padding: 5px 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.sl-label {
    font-family: var(--mono);
    font-size: 0.48rem;
    color: var(--ink-3);
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.sl-val {
    font-family: var(--mono);
    font-size: 0.62rem;
    font-weight: 700;
    color: var(--mint);     /* always positive — bearish filtered out */
}
.sl-arrow { margin-right: 3px; }

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
    font-size: 0.55rem;
    font-weight: 700;
    color: var(--mint);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 3px 8px;
}
.rr-dot {
    width: 4px; height: 4px;
    border-radius: 50%;
    background: var(--mint);
    animation: blink 2s ease-in-out infinite;
}
.prox-tag {
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
    background: rgba(240,165,0,0.06) !important;
    border: 1px solid rgba(240,165,0,0.20) !important;
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

/* ── Global overrides ── */
h3 { display: none !important; }

/* ── Responsive ── */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem 0.75rem 3.5rem !important; }
    .bc-body                { padding: 10px 10px 8px; }
    .gate-row               { gap: 4px; }
}
@media (max-width: 520px) {
    .aw       { font-size: 1.4rem; }
    .pr       { grid-template-columns: 1fr; }
    .tr       { grid-template-columns: 1fr; }
    .slope-row{ grid-template-columns: 1fr; }
    .bc-hd    { flex-direction: column; gap: 6px; }
    .tv       { align-self: flex-start; }
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

# Strategy gate legend (rendered once, above the card grid)
_GATE_LEGEND = (
    '<div class="gate-row">'
    '  <div class="gate-chip"><span class="n">G1</span> 44-SMA &gt; 200-SMA</div>'
    '  <div class="gate-chip"><span class="n">G2</span> Both slopes rising (5-bar)</div>'
    '  <div class="gate-chip"><span class="n">G3</span> Low touches 44-SMA ±0.5%</div>'
    '  <div class="gate-chip"><span class="n">G4</span> Green candle</div>'
    '</div>'
)


# ── Card renderer ─────────────────────────────────────────────────────────────
def _card_html(sig: TradingSignal) -> str:
    """
    Resolves every TradingSignal field to a plain Python str before
    interpolation. Zero attribute-access expressions inside the HTML.
    """
    ticker: str = str(sig.ticker)
    ltp:    str = f"{float(sig.last_traded_price):,.2f}"
    entry:  str = f"{float(sig.entry_trigger):,.2f}"
    sl:     str = f"{float(sig.stop_loss):,.2f}"
    t1:     str = f"{float(sig.target_1):,.2f}"
    t2:     str = f"{float(sig.target_2):,.2f}"
    rr:     str = f"{float(sig.reward_risk_ratio):.2f}"
    sf:     str = f"{float(sig.sma_fast):,.2f}"
    ss:     str = f"{float(sig.sma_slow):,.2f}"
    spd:    str = f"{float(sig.sma_spread_pct):.2f}"
    prox:   str = f"{float(sig.touch_proximity_pct):.3f}"
    slopef: str = f"+{float(sig.slope_fast):.4f}"   # always positive (gate enforced)
    slopes: str = f"+{float(sig.slope_slow):.4f}"   # always positive (gate enforced)
    tv_url: str = f"https://www.tradingview.com/chart/?symbol=NSE%3A{ticker}"

    return (
        '<div class="bc">'
          '<div class="bc-stripe"></div>'
          '<div class="bc-body">'

            # Header
            '<div class="bc-hd">'
              '<div>'
                f'<div class="bc-ticker">{ticker}</div>'
                f'<div class="bc-ltp">&#8377;{ltp}</div>'
              '</div>'
              f'<a class="tv" href="{tv_url}" target="_blank" rel="noopener noreferrer">'
                f'{_TV_SVG}&thinsp;Chart'
              '</a>'
            '</div>'

            # Entry + SL
            '<div class="pr">'
              '<div class="pc">'
                '<div class="pc-l">Buy Above</div>'
                f'<div class="pc-v en">&#8377;{entry}</div>'
              '</div>'
              '<div class="pc">'
                '<div class="pc-l">Stop Loss</div>'
                f'<div class="pc-v sl">&#8377;{sl}</div>'
              '</div>'
            '</div>'

            # Targets
            '<div class="tr">'
              '<div class="tc">'
                '<div class="tc-l">Target 1 (1R)</div>'
                f'<div class="tc-v">&#8377;{t1}</div>'
              '</div>'
              '<div class="tc">'
                '<div class="tc-l">Target 2 (2R)</div>'
                f'<div class="tc-v">&#8377;{t2}</div>'
              '</div>'
            '</div>'

            # SMA values + spread
            '<div class="si">'
              f'<span class="si-item">SMA44 <b>{sf}</b></span>'
              '<span class="si-sep">&#xb7;</span>'
              f'<span class="si-item">SMA200 <b>{ss}</b></span>'
              '<span class="si-sep">&#xb7;</span>'
              f'<span class="si-item">Spread <b>+{spd}%</b></span>'
            '</div>'

            # Positive slope confirmation
            '<div class="slope-row">'
              '<div class="sl-cell">'
                '<span class="sl-label">Slope 44</span>'
                f'<span class="sl-val"><span class="sl-arrow">&#9650;</span>{slopef}</span>'
              '</div>'
              '<div class="sl-cell">'
                '<span class="sl-label">Slope 200</span>'
                f'<span class="sl-val"><span class="sl-arrow">&#9650;</span>{slopes}</span>'
              '</div>'
            '</div>'

            # Footer
            '<div class="bc-ft">'
              '<div class="rr-pill">'
                '<span class="rr-dot"></span>'
                f'R:R&thinsp;{rr}x'
              '</div>'
              f'<span class="prox-tag">&#8764;{prox}% from 44-SMA</span>'
            '</div>'

          '</div>'
        '</div>'
    )


def _sidebar_html(scanned: int, found: int) -> None:
    rows: list[tuple[str, str, str]] = [
        ("Universe",    "Nifty 500",          "hl"),
        ("Strategy",    "Triple Bullish",      "ok"),
        ("G1",          "44-SMA > 200-SMA",    "ok"),
        ("G2",          "5-bar slope > 0",     "ok"),
        ("G3",          "Touch ± 0.5 %",       "ok"),
        ("G4",          "Green candle",        "ok"),
        ("R:R",         "1 : 2",               "ok"),
        ("Scanned",     str(scanned),          ""),
        ("Signals",     str(found),            "ok" if found > 0 else ""),
        ("Scan UTC",    datetime.utcnow().strftime("%H:%M:%S"), ""),
    ]
    rows_html = "".join(
        f'<div class="sb-row">'
        f'  <span class="sb-k">{k}</span>'
        f'  <span class="sb-v {c}">{v}</span>'
        f'</div>'
        for k, v, c in rows
    )
    st.sidebar.markdown(
        f'<div class="sb-hd">Triple Bullish</div>{rows_html}',
        unsafe_allow_html=True,
    )


# ── Main dashboard ─────────────────────────────────────────────────────────────
def render_dashboard() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    # Brand
    st.markdown(
        '<div class="aw">Arth<span class="g">Sutra</span>'
        '<span class="d">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="aw-sub">'
        '  <span class="aw-tag">Triple Bullish &middot; NSE 500 &middot; 44/200 SMA</span>'
        '  <span class="tb-badge"><span class="tb-dot"></span>Triple Bullish Active</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Strategy gate legend (always visible, above the scan button)
    st.markdown(_GATE_LEGEND, unsafe_allow_html=True)

    if not st.button("Run Triple Bullish Scan \u2192"):
        return

    # Cached universe fetch
    universe = fetch_nifty500_universe.__wrapped__(  # type: ignore[attr-defined]
    ) if hasattr(fetch_nifty500_universe, "__wrapped__") else fetch_nifty500_universe()

    # Safer: just call the cached version directly
    universe = _load_universe()
    total    = len(universe)

    progress_bar  = st.progress(0, text="Initialising\u2026")
    status_slot   = st.empty()
    section_slot  = st.empty()

    # Four column placeholders for streaming cards
    col_placeholders = [st.empty() for _ in range(CARDS_PER_ROW)]
    col_buffers: list[list[str]] = [[] for _ in range(CARDS_PER_ROW)]

    signals_found = 0
    processed     = 0

    def _flush() -> None:
        for ci, ph in enumerate(col_placeholders):
            if col_buffers[ci]:
                ph.markdown("".join(col_buffers[ci]), unsafe_allow_html=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY_LIMIT) as pool:
        future_map = {pool.submit(_compute_signal, t): t for t in universe}

        for future in as_completed(future_map):
            signal, audit = future.result()
            logger.debug(
                "Audit %s | %s | %.1f ms",
                audit.ticker, audit.outcome, audit.latency_ms,
            )
            processed += 1

            pct = math.ceil(processed / total * 100)
            progress_bar.progress(
                min(pct, 100),
                text=f"Scanning\u2026 {processed} / {total}",
            )

            if signal is None:
                continue

            signals_found += 1

            if signals_found == 1:
                section_slot.markdown(
                    '<div class="sec-row">'
                    '  <div class="sec-rule"></div>'
                    '  <span class="sec-lbl">Triple Bullish Setups</span>'
                    '  <div class="sec-rule"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            status_slot.markdown(
                f'<div class="ss">'
                f'  <div class="ss-spin"></div>'
                f'  Scanning &mdash; '
                f'  <span class="ct">{signals_found} setup'
                f'{"s" if signals_found != 1 else ""} found</span>'
                f'  &mdash; {processed}/{total}'
                f'</div>',
                unsafe_allow_html=True,
            )

            col_idx = (signals_found - 1) % CARDS_PER_ROW
            col_buffers[col_idx].append(_card_html(signal))
            _flush()

    # ── Scan complete ─────────────────────────────────────────────────────────
    progress_bar.empty()

    if signals_found == 0:
        status_slot.empty()
        section_slot.empty()
        st.warning(
            "No Triple Bullish setups found this session. "
            "All four gates must pass simultaneously \u2014 the filter is intentionally strict."
        )
    else:
        status_slot.markdown(
            f'<div class="ss">'
            f'  <span class="ct">{signals_found} Triple Bullish setup'
            f'{"s" if signals_found != 1 else ""}</span>'
            f'  &mdash; {processed} instruments scanned'
            f'</div>',
            unsafe_allow_html=True,
        )
        section_slot.markdown(
            f'<div class="sec-row">'
            f'  <div class="sec-rule"></div>'
            f'  <span class="sec-lbl">Triple Bullish Setups</span>'
            f'  <span class="sec-badge">{signals_found} Found</span>'
            f'  <div class="sec-rule"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.markdown("---")
        _sidebar_html(processed, signals_found)


# ── Internal cached universe loader (avoids __wrapped__ hacks) ────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def _load_universe() -> list[str]:
    nse_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        symbols: list[str] = (
            pd.read_csv(nse_url, usecols=["Symbol"])["Symbol"].tolist()
        )
        logger.info("Universe loaded: %d symbols from NSE.", len(symbols))
        return [f"{sym}.NS" for sym in symbols]
    except Exception as exc:
        logger.warning("NSE fetch failed (%s). Using fallback list.", exc)
        return list(FALLBACK_UNIVERSE)


# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArtSutra Pro — Triple Bullish",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__" or True:
    render_dashboard()
