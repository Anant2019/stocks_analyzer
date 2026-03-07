"""
arth_sutra_engine.py
Production-grade signal scanner | Python 3.12+ | Fintech-tier quality
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

import pandas as pd
import streamlit as st
import yfinance as yf

# ── Observability ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arth_sutra.engine")

# ── Domain Constants ───────────────────────────────────────────────────────────
SMA_FAST_WINDOW:     Final[int]   = 44
SMA_SLOW_WINDOW:     Final[int]   = 200
SUPPORT_TOLERANCE:   Final[float] = 1.03
SL_BUFFER_FACTOR:    Final[float] = 0.998
RISK_MULTIPLIER_T2:  Final[float] = 2.0
MIN_HISTORY_BARS:    Final[int]   = SMA_SLOW_WINDOW + 1
CONCURRENCY_LIMIT:   Final[int]   = 25
SCAN_LOOKBACK:       Final[str]   = "2y"
SCAN_INTERVAL:       Final[str]   = "1d"

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
    scanned_at:        datetime = field(default_factory=datetime.utcnow)

    @property
    def risk_per_unit(self) -> float:
        return round(self.entry_trigger - self.stop_loss, 4)

    @property
    def reward_risk_ratio(self) -> float:
        """R:R for T2 -- must be > 1 for signal to be valid."""
        return round((self.target_2 - self.entry_trigger) / self.risk_per_unit, 2) if self.risk_per_unit else 0.0


@dataclass(slots=True)
class ScanAuditRecord:
    """Captures scan-level diagnostics -- feeds into any observability sink."""
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
    import time
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
            audit = ScanAuditRecord(
                ticker=ticker,
                outcome="INSUFFICIENT_DATA",
                reason=f"Only {len(raw)} bars; need {MIN_HISTORY_BARS}.",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )
            return None, audit

        close: pd.Series = raw["Close"]
        high:  pd.Series = raw["High"]
        low:   pd.Series = raw["Low"]
        open_: pd.Series = raw["Open"]

        sma_fast: pd.Series = close.rolling(SMA_FAST_WINDOW,  min_periods=SMA_FAST_WINDOW).mean()
        sma_slow: pd.Series = close.rolling(SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW).mean()

        curr_sma_fast  = float(sma_fast.iloc[-1])
        prev_sma_fast  = float(sma_fast.iloc[-2])
        curr_sma_slow  = float(sma_slow.iloc[-1])
        prev_sma_slow  = float(sma_slow.iloc[-2])

        curr_close = float(close.iloc[-1])
        curr_high  = float(high.iloc[-1])
        curr_low   = float(low.iloc[-1])
        curr_open  = float(open_.iloc[-1])

        rising_averages      = (curr_sma_fast > prev_sma_fast) and (curr_sma_slow > prev_sma_slow)
        near_fast_support    = curr_low <= (curr_sma_fast * SUPPORT_TOLERANCE)
        bullish_confirmation = curr_close > curr_open

        if not (rising_averages and near_fast_support and bullish_confirmation):
            audit = ScanAuditRecord(
                ticker=ticker,
                outcome="FILTERED",
                reason=(
                    f"rising={rising_averages} "
                    f"support={near_fast_support} "
                    f"green={bullish_confirmation}"
                ),
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )
            return None, audit

        entry_trigger = round(curr_high, 2)
        stop_loss     = round(curr_low * SL_BUFFER_FACTOR, 2)
        risk          = entry_trigger - stop_loss

        if risk <= 0:
            audit = ScanAuditRecord(
                ticker=ticker,
                outcome="FILTERED",
                reason=f"Non-positive risk unit: {risk}.",
                latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
            )
            return None, audit

        signal = TradingSignal(
            ticker=ticker.replace(".NS", ""),
            last_traded_price=round(curr_close, 2),
            entry_trigger=entry_trigger,
            stop_loss=stop_loss,
            target_1=round(entry_trigger + risk, 2),
            target_2=round(entry_trigger + risk * RISK_MULTIPLIER_T2, 2),
        )
        audit = ScanAuditRecord(
            ticker=ticker,
            outcome="SIGNAL",
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )
        return signal, audit

    except Exception as exc:
        logger.error("Unhandled exception processing %s: %s", ticker, exc, exc_info=True)
        audit = ScanAuditRecord(
            ticker=ticker,
            outcome="ERROR",
            reason=str(exc),
            latency_ms=round((time.perf_counter() - t0) * 1_000, 2),
        )
        return None, audit


def execute_parallel_scan(universe: list[str]) -> tuple[list[TradingSignal], list[ScanAuditRecord]]:
    signals:   list[TradingSignal]     = []
    audit_log: list[ScanAuditRecord]   = []

    with ThreadPoolExecutor(max_workers=CONCURRENCY_LIMIT) as pool:
        future_map = {pool.submit(_compute_signal, ticker): ticker for ticker in universe}
        for future in as_completed(future_map):
            signal, audit = future.result()
            audit_log.append(audit)
            if signal is not None:
                signals.append(signal)

    return signals, audit_log


# =============================================================================
# PRESENTATION LAYER
# Gen Z Fintech -- Bento Grid -- Electric Mint + Cyber Rose -- Light neutral bg
# =============================================================================

_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&family=DM+Mono:wght@400;500;600&display=swap');

:root {
    --bg:            #F4F4F6;
    --bg-card:       #FFFFFF;
    --bg-chip:       #F0F0F3;
    --border:        #E2E2E8;
    --border-hover:  #C8C8D4;

    --mint:          #00FFC2;
    --mint-dim:      rgba(0, 255, 194, 0.10);
    --mint-border:   rgba(0, 200, 150, 0.20);
    --mint-text:     #007A5E;

    --rose:          #EF5777;
    --rose-dim:      rgba(239, 87, 119, 0.08);
    --rose-text:     #C0203E;

    --success:       #00C896;
    --success-bg:    rgba(0, 200, 150, 0.08);

    --ink:           #1A1A2E;
    --muted:         #8A8A9A;
    --subtle:        #B8B8C8;

    --font:   'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono:   'DM Mono', 'Fira Code', monospace;

    --r-sm: 8px;
    --r-md: 12px;
    --r-lg: 16px;
    --r-xl: 20px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background-color: var(--bg) !important;
    font-family: var(--font) !important;
    color: var(--ink) !important;
}

.main .block-container {
    padding: 2rem 1.75rem 5rem !important;
    max-width: 1340px !important;
}

/* Wordmark */
.as-wordmark {
    font-family: var(--font);
    font-size: clamp(1.9rem, 4.5vw, 2.75rem);
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -1.5px;
    line-height: 1;
}
.as-wordmark .hi { color: var(--mint-text); }
.as-wordmark .dot { color: var(--rose); }

.as-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
    margin-bottom: 26px;
}

.as-tagline {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--subtle);
    letter-spacing: 3.5px;
    text-transform: uppercase;
}

.as-live {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 0.58rem;
    font-weight: 600;
    color: var(--success);
    background: var(--success-bg);
    border: 1px solid rgba(0, 200, 150, 0.22);
    border-radius: 20px;
    padding: 3px 9px;
    letter-spacing: 1px;
}

.live-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--success);
    animation: blink 1.8s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.2; }
}

/* CTA Button */
div.stButton > button {
    background: var(--ink) !important;
    color: #FFF !important;
    font-family: var(--font) !important;
    font-size: 0.84rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    border: none !important;
    border-radius: var(--r-md) !important;
    padding: 14px 32px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.18s, transform 0.15s !important;
}
div.stButton > button:hover {
    background: #2D2D40 !important;
    transform: translateY(-1px) !important;
}
div.stButton > button:active { transform: translateY(0) !important; }

/* Stats Bar */
.stats-bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 22px 0 18px;
}

.stat-chip {
    display: flex;
    flex-direction: column;
    gap: 3px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 12px 16px;
    min-width: 100px;
    flex: 1;
}

.stat-label {
    font-family: var(--mono);
    font-size: 0.56rem;
    font-weight: 500;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
}

.stat-value {
    font-family: var(--mono);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -0.5px;
}
.stat-value.go   { color: var(--mint-text); }
.stat-value.stop { color: var(--rose-text); }

/* Section divider */
.section-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}
.section-rule  { flex: 1; height: 1px; background: var(--border); }
.section-label {
    font-family: var(--mono);
    font-size: 0.60rem;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    white-space: nowrap;
}
.section-badge {
    font-family: var(--mono);
    font-size: 0.62rem;
    font-weight: 700;
    color: var(--mint-text);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 3px 11px;
    white-space: nowrap;
}

/* Bento Card */
.bento-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    margin-bottom: 14px;
    overflow: hidden;
    transition: border-color 0.18s, transform 0.18s;
}
.bento-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
}

.card-stripe {
    height: 3px;
    background: linear-gradient(90deg, var(--mint) 0%, #00D4E8 100%);
}

.card-body { padding: 18px 18px 14px; }

/* Card Header */
.card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 14px;
}

.card-ticker {
    font-family: var(--font);
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -0.5px;
    line-height: 1;
}

.card-ltp {
    font-family: var(--mono);
    font-size: 0.63rem;
    color: var(--muted);
    margin-top: 4px;
}

/* Quick View button */
.qv-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font);
    font-size: 0.66rem;
    font-weight: 600;
    color: var(--ink);
    background: var(--bg-chip);
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    padding: 6px 11px;
    text-decoration: none !important;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.qv-btn:hover {
    background: var(--mint-dim);
    border-color: var(--mint-border);
    color: var(--mint-text) !important;
    text-decoration: none !important;
}
.qv-btn svg { width: 10px; height: 10px; opacity: 0.55; }

/* Bento inner 2-col grid */
.inner-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 8px;
}

.inner-cell {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 10px 12px;
}

.cell-label {
    font-family: var(--mono);
    font-size: 0.55rem;
    font-weight: 500;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.cell-value {
    font-family: var(--mono);
    font-size: 0.90rem;
    font-weight: 700;
    letter-spacing: -0.2px;
    line-height: 1;
}
.cell-value.entry { color: var(--ink); }
.cell-value.sl    { color: var(--rose-text); }

/* Target row */
.target-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
}

.target-cell {
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: var(--r-md);
    padding: 10px 12px;
}

.target-label {
    font-family: var(--mono);
    font-size: 0.55rem;
    font-weight: 500;
    color: var(--mint-text);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 4px;
    opacity: 0.65;
}

.target-value {
    font-family: var(--mono);
    font-size: 0.90rem;
    font-weight: 700;
    color: var(--mint-text);
    letter-spacing: -0.2px;
    line-height: 1;
}

/* Card footer */
.card-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 10px;
    border-top: 1px solid var(--border);
}

.rr-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 0.60rem;
    font-weight: 700;
    color: var(--mint-text);
    background: var(--mint-dim);
    border: 1px solid var(--mint-border);
    border-radius: 20px;
    padding: 4px 10px;
    letter-spacing: 0.5px;
}

.rr-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--success);
    animation: blink 2s ease-in-out infinite;
}

.scan-ts {
    font-family: var(--mono);
    font-size: 0.58rem;
    color: var(--subtle);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }

.diag-hd {
    font-family: var(--mono);
    font-size: 0.58rem;
    font-weight: 700;
    color: var(--subtle);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}

.diag-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
}
.diag-key { font-family: var(--font);  font-size: 0.70rem; color: var(--muted); }
.diag-val { font-family: var(--mono); font-size: 0.70rem; font-weight: 600; color: var(--ink); }
.diag-val.ok     { color: var(--success); }
.diag-val.bad    { color: var(--rose-text); }
.diag-val.warn   { color: #A06000; }
.diag-val.accent { color: var(--mint-text); }

/* Streamlit overrides */
h3 { display: none !important; }
div[data-testid="stSpinner"] > div { border-top-color: var(--ink) !important; }
div[data-testid="stAlert"] {
    background: #FFFBF0 !important;
    border: 1px solid #E8D890 !important;
    border-radius: var(--r-md) !important;
    font-family: var(--font) !important;
    font-size: 0.82rem !important;
    color: #7A6000 !important;
}

/* Responsive */
@media (max-width: 768px) {
    .main .block-container { padding: 1.25rem 1rem 4rem !important; }
    .card-body              { padding: 16px 14px 12px; }
    .stats-bar              { gap: 8px; }
}
@media (max-width: 520px) {
    .as-wordmark   { font-size: 1.75rem; }
    .inner-grid    { grid-template-columns: 1fr; }
    .target-grid   { grid-template-columns: 1fr; }
    .stats-bar     { display: grid; grid-template-columns: 1fr 1fr; }
    .card-head     { flex-direction: column; gap: 10px; }
    .qv-btn        { align-self: flex-start; }
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


def _render_signal_card(signal: TradingSignal) -> str:
    """
    Renders a Bento-style signal card.

    All TradingSignal fields are explicitly cast to Python primitives and
    formatted via format-spec strings BEFORE being interpolated into the
    HTML template. This eliminates any possibility of raw attribute-access
    expressions or unevaluated code leaking into the rendered output.
    """
    # -- Resolve every value to a plain string up front ----------------------
    ticker_text: str = str(signal.ticker)
    ltp_text:    str = f"{float(signal.last_traded_price):,.2f}"
    entry_text:  str = f"{float(signal.entry_trigger):,.2f}"
    sl_text:     str = f"{float(signal.stop_loss):,.2f}"
    t1_text:     str = f"{float(signal.target_1):,.2f}"
    t2_text:     str = f"{float(signal.target_2):,.2f}"
    rr_text:     str = f"{float(signal.reward_risk_ratio):.2f}"
    ts_text:     str = signal.scanned_at.strftime("%H:%M UTC")
    tv_url:      str = (
        f"https://www.tradingview.com/chart/?symbol=NSE%3A{ticker_text}"
    )

    # -- Build HTML from resolved strings only -- no attribute access inside template
    return (
        '<div class="bento-card">'
          '<div class="card-stripe"></div>'
          '<div class="card-body">'

            # Header
            '<div class="card-head">'
              '<div>'
                f'<div class="card-ticker">{ticker_text}</div>'
                f'<div class="card-ltp">LTP &nbsp;&#8377;{ltp_text}</div>'
              '</div>'
              f'<a class="qv-btn" href="{tv_url}" target="_blank" rel="noopener noreferrer">'
                f'{_TV_SVG} Quick View'
              '</a>'
            '</div>'

            # Entry + SL
            '<div class="inner-grid">'
              '<div class="inner-cell">'
                '<div class="cell-label">Buy Above</div>'
                f'<div class="cell-value entry">&#8377;{entry_text}</div>'
              '</div>'
              '<div class="inner-cell">'
                '<div class="cell-label">Stop Loss</div>'
                f'<div class="cell-value sl">&#8377;{sl_text}</div>'
              '</div>'
            '</div>'

            # Targets
            '<div class="target-grid">'
              '<div class="target-cell">'
                '<div class="target-label">Target 1</div>'
                f'<div class="target-value">&#8377;{t1_text}</div>'
              '</div>'
              '<div class="target-cell">'
                '<div class="target-label">Target 2</div>'
                f'<div class="target-value">&#8377;{t2_text}</div>'
              '</div>'
            '</div>'

            # Footer
            '<div class="card-foot">'
              '<div class="rr-pill">'
                '<span class="rr-dot"></span>'
                f'R:R &nbsp;{rr_text}x'
              '</div>'
              f'<span class="scan-ts">{ts_text}</span>'
            '</div>'

          '</div>'
        '</div>'
    )


def _stats_bar_html(total: int, signal_count: int, error_count: int, avg_latency: float) -> str:
    signal_cls  = "go"   if signal_count > 0 else ""
    error_cls   = "stop" if error_count  > 0 else ""

    chips: list[tuple[str, str, str]] = [
        ("Scanned",  str(total),                         ""),
        ("Signals",  str(signal_count),                  signal_cls),
        ("Errors",   str(error_count),                   error_cls),
        ("Avg ms",   f"{avg_latency}",                   ""),
        ("Workers",  str(CONCURRENCY_LIMIT),             ""),
    ]

    inner = "".join(
        f'<div class="stat-chip">'
        f'  <span class="stat-label">{lbl}</span>'
        f'  <span class="stat-value {cls}">{val}</span>'
        f'</div>'
        for lbl, val, cls in chips
    )
    return f'<div class="stats-bar">{inner}</div>'


def _render_sidebar(total: int, signal_count: int, error_count: int, avg_latency: float) -> None:
    error_cls   = "bad"  if error_count > 0      else "ok"
    latency_cls = "bad"  if avg_latency > 2000   else \
                  "warn" if avg_latency > 1000   else "ok"

    rows: list[tuple[str, str, str]] = [
        ("Universe",    "Nifty 500",                             "accent"),
        ("Scanned",     str(total),                              ""),
        ("Signals",     str(signal_count),                       "ok" if signal_count > 0 else ""),
        ("Errors",      str(error_count),                        error_cls),
        ("Avg latency", f"{avg_latency} ms",                     latency_cls),
        ("Workers",     str(CONCURRENCY_LIMIT),                  "accent"),
        ("Scan UTC",    datetime.utcnow().strftime("%H:%M:%S"),  ""),
    ]

    rows_html = "".join(
        f'<div class="diag-row">'
        f'  <span class="diag-key">{k}</span>'
        f'  <span class="diag-val {cls}">{v}</span>'
        f'</div>'
        for k, v, cls in rows
    )
    st.sidebar.markdown(
        f'<div class="diag-hd">System Diagnostics</div>{rows_html}',
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)

    # Brand
    st.markdown(
        '<div class="as-wordmark">'
        'Arth<span class="hi">Sutra</span><span class="dot">.</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="as-meta">'
        '  <span class="as-tagline">Discipline &middot; Prosperity &middot; Consistency</span>'
        '  <span class="as-live"><span class="live-dot"></span>LIVE</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not st.button("Run Signal Scan  \u2192"):
        return

    universe = fetch_nifty500_universe()

    with st.spinner(f"Scanning {len(universe)} instruments\u2026"):
        signals, audit_log = execute_parallel_scan(universe)

    total       = len(audit_log)
    error_count = sum(1 for a in audit_log if a.outcome == "ERROR")
    avg_latency = round(sum(a.latency_ms for a in audit_log) / total, 1) if total else 0.0

    st.markdown(_stats_bar_html(total, len(signals), error_count, avg_latency), unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        _render_sidebar(total, len(signals), error_count, avg_latency)

    if not signals:
        st.warning(
            "No signals this session. "
            "The 44 SMA is an exacting filter \u2014 patience compounds."
        )
        return

    count = len(signals)
    st.markdown(
        f'<div class="section-row">'
        f'  <div class="section-rule"></div>'
        f'  <span class="section-label">Active Signals</span>'
        f'  <span class="section-badge">{count} Found</span>'
        f'  <div class="section-rule"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(3)
    for idx, signal in enumerate(signals):
        with columns[idx % 3]:
            st.markdown(_render_signal_card(signal), unsafe_allow_html=True)


# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArtSutra Pro",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__" or True:
    render_dashboard()
