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
        """R:R for T2 — must be > 1 for signal to be valid."""
        return round((self.target_2 - self.entry_trigger) / self.risk_per_unit, 2) if self.risk_per_unit else 0.0


@dataclass(slots=True)
class ScanAuditRecord:
    """Captures scan-level diagnostics — feeds into any observability sink."""
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


# ── Presentation Layer ─────────────────────────────────────────────────────────
_CARD_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Design Tokens ── */
:root {
    --bg-base:          #0d1117;
    --bg-surface:       #161b22;
    --bg-elevated:      #1c2128;
    --bg-glass:         rgba(28, 33, 40, 0.70);

    --border-subtle:    rgba(255, 255, 255, 0.06);
    --border-default:   rgba(255, 255, 255, 0.10);
    --border-strong:    rgba(255, 255, 255, 0.18);

    --accent-blue:      #00d1ff;
    --accent-blue-dim:  rgba(0, 209, 255, 0.12);
    --accent-blue-glow: rgba(0, 209, 255, 0.25);

    --accent-green:     #00ffbd;
    --accent-green-dim: rgba(0, 255, 189, 0.10);
    --accent-green-glow:rgba(0, 255, 189, 0.22);

    --danger:           #ff4d6a;
    --danger-dim:       rgba(255, 77, 106, 0.12);

    --warning:          #ffc857;
    --warning-dim:      rgba(255, 200, 87, 0.10);

    --text-primary:     #e6edf3;
    --text-secondary:   #8b949e;
    --text-muted:       #484f58;

    --radius-sm:        6px;
    --radius-md:        10px;
    --radius-lg:        14px;

    --font-sans:        'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono:        'JetBrains Mono', 'Fira Code', monospace;

    --shadow-card:      0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.3);
    --shadow-glow-blue: 0 0 20px rgba(0, 209, 255, 0.12);
    --shadow-glow-green:0 0 20px rgba(0, 255, 189, 0.10);
}

/* ── Global Reset ── */
*, *::before, *::after { box-sizing: border-box; }

/* ── App Shell ── */
.stApp {
    background-color: var(--bg-base) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0, 209, 255, 0.06) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 90%,  rgba(0, 255, 189, 0.04) 0%, transparent 55%);
    color: var(--text-primary);
    font-family: var(--font-sans);
    min-height: 100vh;
}

/* ── Main content padding ── */
.main .block-container {
    padding: 2.5rem 2rem 4rem !important;
    max-width: 1400px !important;
}

/* ── Brand Header ── */
.brand-header {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    margin-bottom: 4px;
}

.brand-wordmark {
    font-family: var(--font-sans);
    font-size: clamp(2.2rem, 5vw, 3.4rem);
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -1.5px;
    line-height: 1;
    margin: 0;
}

.brand-wordmark .accent {
    color: var(--accent-blue);
    text-shadow: 0 0 28px rgba(0, 209, 255, 0.5);
}

.brand-version-badge {
    font-family: var(--font-mono);
    font-size: 0.62rem;
    font-weight: 600;
    color: var(--accent-blue);
    background: var(--accent-blue-dim);
    border: 1px solid rgba(0, 209, 255, 0.25);
    border-radius: var(--radius-sm);
    padding: 3px 8px;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
}

.brand-tagline {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--text-muted);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 8px;
    margin-bottom: 32px;
}

/* ── Scan Button ── */
div.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue) 0%, #0099cc 100%) !important;
    color: #000 !important;
    font-family: var(--font-sans) !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 14px 32px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 24px rgba(0, 209, 255, 0.30) !important;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #33daff 0%, var(--accent-blue) 100%) !important;
    box-shadow: 0 0 36px rgba(0, 209, 255, 0.50) !important;
    transform: translateY(-1px) !important;
}

div.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Section Header ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 20px;
}

.section-header-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-default) 0%, transparent 100%);
}

.section-title {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-secondary);
    letter-spacing: 3px;
    text-transform: uppercase;
    white-space: nowrap;
}

.signal-count-badge {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--accent-green);
    background: var(--accent-green-dim);
    border: 1px solid rgba(0, 255, 189, 0.20);
    border-radius: 20px;
    padding: 3px 12px;
    letter-spacing: 1px;
}

/* ── Signal Card (Glassmorphism) ── */
.signal-card {
    position: relative;
    background: var(--bg-glass);
    backdrop-filter: blur(12px) saturate(160%);
    -webkit-backdrop-filter: blur(12px) saturate(160%);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 22px 20px 18px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-card);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
}

.signal-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-blue) 0%, var(--accent-green) 100%);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.signal-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-card), var(--shadow-glow-blue);
    border-color: var(--border-default);
}

/* ── Card Header ── */
.card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 14px;
}

.signal-ticker {
    font-family: var(--font-sans);
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
    line-height: 1.1;
}

.signal-ltp {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--text-muted);
    margin-top: 4px;
    letter-spacing: 0.5px;
}

/* ── TradingView Chart Link ── */
.chart-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font-sans);
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--accent-blue);
    background: var(--accent-blue-dim);
    border: 1px solid rgba(0, 209, 255, 0.18);
    border-radius: var(--radius-sm);
    padding: 5px 10px;
    text-decoration: none !important;
    letter-spacing: 0.5px;
    transition: background 0.15s, box-shadow 0.15s;
    white-space: nowrap;
    flex-shrink: 0;
}

.chart-link:hover {
    background: rgba(0, 209, 255, 0.22);
    box-shadow: 0 0 12px rgba(0, 209, 255, 0.25);
    color: var(--accent-blue) !important;
    text-decoration: none !important;
}

.chart-link svg {
    width: 11px;
    height: 11px;
    flex-shrink: 0;
}

/* ── Card Divider ── */
.card-divider {
    border: none;
    border-top: 1px solid var(--border-subtle);
    margin: 12px 0 14px;
}

/* ── Price Rows ── */
.price-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
}

.price-label {
    font-family: var(--font-sans);
    font-size: 0.70rem;
    font-weight: 500;
    color: var(--text-secondary);
    letter-spacing: 0.5px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 6px;
}

.price-label .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-entry { background: var(--accent-blue); box-shadow: 0 0 6px rgba(0, 209, 255, 0.6); }
.dot-sl    { background: var(--danger);       box-shadow: 0 0 6px rgba(255, 77, 106, 0.6); }

.price-value {
    font-family: var(--font-mono);
    font-size: 0.88rem;
    font-weight: 600;
    letter-spacing: -0.3px;
}

.price-value.entry { color: var(--accent-blue); }
.price-value.sl    { color: var(--danger); }

/* ── Target Block ── */
.target-section {
    background: var(--accent-green-dim);
    border: 1px solid rgba(0, 255, 189, 0.12);
    border-radius: var(--radius-md);
    padding: 12px 14px;
    margin-top: 14px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 12px;
}

.target-label {
    font-family: var(--font-sans);
    font-size: 0.62rem;
    font-weight: 600;
    color: rgba(0, 255, 189, 0.55);
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.target-val {
    font-family: var(--font-mono);
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--accent-green);
    letter-spacing: -0.3px;
}

/* ── Card Footer ── */
.card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 14px;
}

.rr-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--font-mono);
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--accent-green);
    background: var(--accent-green-dim);
    border: 1px solid rgba(0, 255, 189, 0.18);
    border-radius: 20px;
    padding: 4px 10px;
    letter-spacing: 0.5px;
}

.rr-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--accent-green);
    animation: pulse-green 2s ease-in-out infinite;
}

@keyframes pulse-green {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

.sidebar-header {
    font-family: var(--font-mono);
    font-size: 0.62rem;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-subtle);
}

.diag-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--border-subtle);
}

.diag-key {
    font-family: var(--font-sans);
    font-size: 0.72rem;
    color: var(--text-secondary);
}

.diag-val {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-primary);
}

.diag-val.success { color: var(--accent-green); }
.diag-val.danger  { color: var(--danger); }
.diag-val.warning { color: var(--warning); }
.diag-val.blue    { color: var(--accent-blue); }

/* ── Status Pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font-sans);
    font-size: 0.65rem;
    font-weight: 600;
    border-radius: 20px;
    padding: 3px 9px;
    letter-spacing: 0.3px;
}

.status-pill.live {
    color: var(--accent-green);
    background: var(--accent-green-dim);
    border: 1px solid rgba(0, 255, 189, 0.20);
}

.status-pulse {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--accent-green);
    animation: pulse-green 1.5s ease-in-out infinite;
}

/* ── Streamlit overrides ── */
h3 { display: none; }  /* hide st.markdown ### — we render our own header */

.stSpinner > div { border-top-color: var(--accent-blue) !important; }

[data-testid="stNotification"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-default) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-sans) !important;
    font-size: 0.82rem !important;
}

/* ── Responsive Grid ── */
@media (max-width: 768px) {
    .main .block-container { padding: 1.5rem 1rem 3rem !important; }
    .brand-wordmark         { font-size: 2rem; }
    .signal-card            { padding: 18px 16px 14px; }
    .target-section         { grid-template-columns: 1fr 1fr; }
    .card-header            { flex-direction: column; gap: 10px; }
    .chart-link             { align-self: flex-start; }
}

@media (max-width: 480px) {
    .target-section { grid-template-columns: 1fr; }
}
</style>
"""

# ── TradingView chart link SVG icon ──
_TV_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/>'
    '<line x1="10" y1="14" x2="21" y2="3"/>'
    '</svg>'
)


def _render_signal_card(signal: TradingSignal) -> str:
    tv_url   = f"https://www.tradingview.com/chart/?symbol=NSE%3A{signal.ticker}"
    rr_color = "success" if signal.reward_risk_ratio >= 2 else "warning"
    return f"""
    <div class="signal-card">
        <div class="card-header">
            <div>
                <div class="signal-ticker">{signal.ticker}</div>
                <div class="signal-ltp">LTP &nbsp;₹{signal.last_traded_price:,.2f}</div>
            </div>
            <a class="chart-link" href="{tv_url}" target="_blank" rel="noopener noreferrer">
                {_TV_ICON} View Chart
            </a>
        </div>

        <hr class="card-divider">

        <div class="price-row">
            <div class="price-label">
                <span class="dot dot-entry"></span>Buy Above
            </div>
            <div class="price-value entry">₹{signal.entry_trigger:,.2f}</div>
        </div>
        <div class="price-row">
            <div class="price-label">
                <span class="dot dot-sl"></span>Stop Loss
            </div>
            <div class="price-value sl">₹{signal.stop_loss:,.2f}</div>
        </div>

        <div class="target-section">
            <div>
                <div class="target-label">Target 1</div>
                <div class="target-val">₹{signal.target_1:,.2f}</div>
            </div>
            <div>
                <div class="target-label">Target 2</div>
                <div class="target-val">₹{signal.target_2:,.2f}</div>
            </div>
        </div>

        <div class="card-footer">
            <div class="rr-badge">
                <span class="rr-dot"></span> R:R &nbsp;{signal.reward_risk_ratio}x
            </div>
        </div>
    </div>
    """


def _render_sidebar_diagnostics(
    total: int,
    signal_count: int,
    error_count: int,
    avg_latency: float,
) -> None:
    error_cls   = "danger"  if error_count > 0       else "success"
    latency_cls = "danger"  if avg_latency > 2000    else \
                  "warning" if avg_latency > 1000    else "success"

    rows = [
        ("Universe",    "Nifty 500",                                     "blue"),
        ("Scanned",     str(total),                                       ""),
        ("Signals",     str(signal_count),                               "success" if signal_count > 0 else ""),
        ("Errors",      str(error_count),                                error_cls),
        ("Avg latency", f"{avg_latency} ms",                             latency_cls),
        ("Workers",     str(CONCURRENCY_LIMIT),                          "blue"),
        ("Scan UTC",    datetime.utcnow().strftime("%H:%M:%S"),           ""),
    ]

    html_rows = "".join(
        f'<div class="diag-row">'
        f'  <span class="diag-key">{k}</span>'
        f'  <span class="diag-val {cls}">{v}</span>'
        f'</div>'
        for k, v, cls in rows
    )

    st.sidebar.markdown(
        f'<div class="sidebar-header">System Diagnostics</div>{html_rows}',
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    # ── Brand ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="brand-wordmark">ARTH <span class="accent">SUTRA</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="brand-tagline">Discipline &nbsp;•&nbsp; Prosperity &nbsp;•&nbsp; Consistency</div>',
        unsafe_allow_html=True,
    )

    if not st.button("⚡ INITIATE ENGINE SCAN"):
        return

    universe = fetch_nifty500_universe()

    with st.spinner(f"Scanning {len(universe)} instruments across Nifty 500…"):
        signals, audit_log = execute_parallel_scan(universe)

    # ── Compute diagnostics ────────────────────────────────────────────────────
    total        = len(audit_log)
    error_count  = sum(1 for a in audit_log if a.outcome == "ERROR")
    avg_latency  = round(sum(a.latency_ms for a in audit_log) / total, 1) if total else 0.0

    with st.sidebar:
        st.markdown("---")
        _render_sidebar_diagnostics(total, len(signals), error_count, avg_latency)

    # ── Signal grid ────────────────────────────────────────────────────────────
    if not signals:
        st.warning(
            "No signals surfaced this session. "
            "The 44 SMA is an exacting filter — patience compounds."
        )
        return

    count = len(signals)
    st.markdown(
        f'<div class="section-header">'
        f'  <div class="section-line" style="flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,0.06),transparent)"></div>'
        f'  <span class="section-title">Active Signals</span>'
        f'  <span class="signal-count-badge">{count} FOUND</span>'
        f'  <div class="section-line" style="flex:1;height:1px;background:linear-gradient(270deg,rgba(255,255,255,0.06),transparent)"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(3)
    for idx, signal in enumerate(signals):
        with columns[idx % 3]:
            st.markdown(_render_signal_card(signal), unsafe_allow_html=True)


# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arth Sutra Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__" or True:
    render_dashboard()
