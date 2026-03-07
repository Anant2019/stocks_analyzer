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
SUPPORT_TOLERANCE:   Final[float] = 1.03   # 3 % proximity band
SL_BUFFER_FACTOR:    Final[float] = 0.998
RISK_MULTIPLIER_T2:  Final[float] = 2.0
MIN_HISTORY_BARS:    Final[int]   = SMA_SLOW_WINDOW + 1   # one extra for diff
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
    ticker:         str
    last_traded_price: float
    entry_trigger:  float   # buy-above level
    stop_loss:      float
    target_1:       float
    target_2:       float
    scanned_at:     datetime = field(default_factory=datetime.utcnow)

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
    outcome:    str          # "SIGNAL" | "FILTERED" | "INSUFFICIENT_DATA" | "ERROR"
    reason:     str  = ""
    latency_ms: float = 0.0


# ── Data Acquisition ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_nifty500_universe() -> list[str]:
    """
    Downloads the Nifty 500 constituent list from NSE.
    Cached for one hour — avoids repeated HTTP round-trips across reruns.
    Returns suffixed Yahoo Finance tickers.
    """
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
    Single-ticker signal computation.

    Complexity: O(n) vectorised rolling — no Python-level loops over OHLCV rows.
    Memory: operates on a *view* slice; no defensive copy unless pandas forces CoW.

    Returns
    -------
    (TradingSignal | None, ScanAuditRecord)
        Signal is None when the ticker does not meet entry criteria.
    """
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

        # Vectorised indicators — single-pass rolling means, no intermediate copies
        sma_fast: pd.Series = close.rolling(SMA_FAST_WINDOW,  min_periods=SMA_FAST_WINDOW).mean()
        sma_slow: pd.Series = close.rolling(SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW).mean()

        # Use .iloc[-1] / .iloc[-2] only after confirming validity above
        curr_sma_fast  = float(sma_fast.iloc[-1])
        prev_sma_fast  = float(sma_fast.iloc[-2])
        curr_sma_slow  = float(sma_slow.iloc[-1])
        prev_sma_slow  = float(sma_slow.iloc[-2])

        curr_close = float(close.iloc[-1])
        curr_high  = float(high.iloc[-1])
        curr_low   = float(low.iloc[-1])
        curr_open  = float(open_.iloc[-1])

        # ── Sutra Criteria ────────────────────────────────────────────────────
        rising_averages     = (curr_sma_fast > prev_sma_fast) and (curr_sma_slow > prev_sma_slow)
        near_fast_support   = curr_low <= (curr_sma_fast * SUPPORT_TOLERANCE)
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
    """
    Dispatches `_compute_signal` across the universe using a bounded thread pool.

    Uses `as_completed` so the main thread can collect results as they stream in
    rather than blocking until the slowest worker finishes.
    """
    signals: list[TradingSignal]     = []
    audit_log: list[ScanAuditRecord] = []

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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #040404;
    color: #e8e8e8;
    font-family: 'IBM Plex Mono', monospace;
}

.brand-wordmark {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -2px;
    line-height: 1;
}

.brand-wordmark span {
    color: #0af;
}

.brand-tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #444;
    letter-spacing: 5px;
    text-transform: uppercase;
    margin-top: 6px;
    margin-bottom: 36px;
}

.signal-card {
    background: #0a0a0a;
    border: 1px solid #181818;
    border-top: 2px solid #0af;
    border-radius: 2px;
    padding: 20px 22px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
}

.signal-card:hover { border-top-color: #00ff88; }

.signal-ticker {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.5px;
}

.signal-ltp {
    font-size: 0.72rem;
    color: #444;
    margin-top: 2px;
    margin-bottom: 14px;
}

.signal-divider {
    border: none;
    border-top: 1px solid #161616;
    margin: 12px 0;
}

.label-entry { color: #0af; font-size: 0.78rem; font-weight: 700; }
.label-sl    { color: #ff4455; font-size: 0.78rem; font-weight: 700; }

.target-block {
    margin-top: 14px;
    border-left: 2px solid #00ff88;
    padding-left: 12px;
}

.target-val {
    font-family: 'Syne', sans-serif;
    color: #00ff88;
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.6;
}

.rr-badge {
    display: inline-block;
    background: #001a0a;
    color: #00ff88;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 2px;
    margin-top: 10px;
    letter-spacing: 1px;
}

div.stButton > button {
    background: #fff !important;
    color: #000 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 2px !important;
    padding: 14px !important;
    width: 100% !important;
    font-size: 0.85rem !important;
}

div.stButton > button:hover {
    background: #0af !important;
    color: #000 !important;
}
</style>
"""


def _render_signal_card(signal: TradingSignal) -> str:
    return f"""
    <div class="signal-card">
        <div class="signal-ticker">{signal.ticker}</div>
        <div class="signal-ltp">LTP ₹{signal.last_traded_price:,.2f}</div>
        <hr class="signal-divider">
        <div class="label-entry">↑ BUY ABOVE &nbsp; ₹{signal.entry_trigger:,.2f}</div>
        <div class="label-sl">✕ STOP LOSS &nbsp; ₹{signal.stop_loss:,.2f}</div>
        <div class="target-block">
            <div class="target-val">T1 &nbsp; ₹{signal.target_1:,.2f}</div>
            <div class="target-val">T2 &nbsp; ₹{signal.target_2:,.2f}</div>
        </div>
        <div class="rr-badge">R:R {signal.reward_risk_ratio}x</div>
    </div>
    """


def render_dashboard() -> None:
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    st.markdown('<div class="brand-wordmark">ARTH <span>SUTRA</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tagline">Discipline &nbsp;•&nbsp; Prosperity &nbsp;•&nbsp; Consistency</div>',
        unsafe_allow_html=True,
    )

    if not st.button("INITIATE ENGINE SCAN"):
        return

    universe = fetch_nifty500_universe()

    progress_bar = st.progress(0, text=f"Scanning {len(universe)} instruments…")
    with st.spinner(""):
        signals, audit_log = execute_parallel_scan(universe)
    progress_bar.empty()

    # ── Sidebar diagnostics ────────────────────────────────────────────────────
    total        = len(audit_log)
    error_count  = sum(1 for a in audit_log if a.outcome == "ERROR")
    avg_latency  = round(sum(a.latency_ms for a in audit_log) / total, 1) if total else 0

    with st.sidebar:
        st.markdown("---")
        st.markdown("**SYSTEM DIAGNOSTICS**")
        st.write(f"Universe:      Nifty 500")
        st.write(f"Scanned:       {total}")
        st.write(f"Signals:       {len(signals)}")
        st.write(f"Errors:        {error_count}")
        st.write(f"Avg latency:   {avg_latency} ms / ticker")
        st.write(f"Workers:       {CONCURRENCY_LIMIT}")
        st.write(f"Scan time:     {datetime.utcnow().strftime('%H:%M:%S')} UTC")

    # ── Main grid ─────────────────────────────────────────────────────────────
    if not signals:
        st.warning(
            "No signals surfaced this session. "
            "The 44 SMA is an exacting filter — patience compounds."
        )
        return

    st.markdown(f"### {len(signals)} SIGNAL{'S' if len(signals) != 1 else ''} DETECTED")

    columns = st.columns(3)
    for idx, signal in enumerate(signals):
        with columns[idx % 3]:
            st.markdown(_render_signal_card(signal), unsafe_allow_html=True)


# ── Entrypoint ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Arth Sutra Pro", layout="wide")

if __name__ == "__main__" or True:   # Streamlit reruns the module directly
    render_dashboard()
