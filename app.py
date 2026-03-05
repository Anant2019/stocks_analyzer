"""
Nifty 200 Institutional-Grade Signal Analyzer
==============================================
Author: Quantitative Systems
Version: 2.0.0
Standard: PEP 8 Compliant

Architecture: Modular OOP with Strategy Pattern for indicators,
Factory Pattern for signal generation, and Singleton for config/logging.

Pillars:
    1. Vectorized NumPy/Pandas operations — no row-level Python loops
    2. Async-ready data fetching with concurrent.futures
    3. Wilder-smoothed RSI, EMA-based MACD, ATR volatility filter
    4. Confidence scoring, JSON-serializable output, styled DataFrames
"""

from __future__ import annotations

import logging
import os
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# 1. SINGLETON: Application Configuration
# ---------------------------------------------------------------------------

class AppConfig:
    """
    Singleton configuration manager.

    Loads settings from environment variables with sensible defaults,
    making the app portable across dev / staging / prod environments.

    Usage:
        cfg = AppConfig.get_instance()
        print(cfg.rsi_period)
    """

    _instance: Optional[AppConfig] = None

    def __new__(cls) -> AppConfig:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise()
        return cls._instance

    @classmethod
    def get_instance(cls) -> AppConfig:
        return cls()

    def _initialise(self) -> None:
        # Indicator hyper-parameters (override via env vars for A/B testing)
        self.rsi_period: int = int(os.getenv("RSI_PERIOD", "14"))
        self.sma_fast: int = int(os.getenv("SMA_FAST", "44"))
        self.sma_slow: int = int(os.getenv("SMA_SLOW", "200"))
        self.vol_lookback: int = int(os.getenv("VOL_LOOKBACK", "5"))
        self.atr_period: int = int(os.getenv("ATR_PERIOD", "14"))
        self.macd_fast: int = int(os.getenv("MACD_FAST", "12"))
        self.macd_slow: int = int(os.getenv("MACD_SLOW", "26"))
        self.macd_signal: int = int(os.getenv("MACD_SIGNAL", "9"))
        self.fetch_workers: int = int(os.getenv("FETCH_WORKERS", "8"))
        self.history_days: int = int(os.getenv("HISTORY_DAYS", "450"))

        # Blue-chip thresholds
        self.blue_rsi_min: float = float(os.getenv("BLUE_RSI_MIN", "65"))
        self.blue_price_premium: float = float(os.getenv("BLUE_PREMIUM", "1.05"))
        self.risk_reward: float = float(os.getenv("RISK_REWARD", "2.0"))


# ---------------------------------------------------------------------------
# 2. SINGLETON: Structured Logger
# ---------------------------------------------------------------------------

class Logger:
    """
    Singleton logger with both stream (console) and file handlers.
    Streamlit surfaces logs via st.expander in debug mode.
    """

    _instance: Optional[logging.Logger] = None

    @classmethod
    def get(cls) -> logging.Logger:
        if cls._instance is None:
            logger = logging.getLogger("nifty200")
            logger.setLevel(logging.DEBUG)
            fmt = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            # Stream handler
            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            logger.addHandler(sh)
            # File handler (append mode, survives app restarts)
            fh = logging.FileHandler("nifty200_analyzer.log", mode="a")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
            cls._instance = logger
        return cls._instance


log = Logger.get()
cfg = AppConfig.get_instance()

# ---------------------------------------------------------------------------
# 3. NIFTY 200 UNIVERSE
# ---------------------------------------------------------------------------

NIFTY_200: list[str] = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS',
    'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS',
    'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS',
    'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS',
    'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS',
    'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS',
    'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS',
    'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS',
    'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS',
    'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS',
    'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS',
    'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS',
    'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS',
    'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS',
    'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS',
    'PFC.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS',
    'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS',
    'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS',
    'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS',
    'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS',
    'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS',
    'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS',
    'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS',
]

# ---------------------------------------------------------------------------
# 4. DATA MODEL: Signal Record
# ---------------------------------------------------------------------------

@dataclass
class SignalRecord:
    """
    Immutable value object representing a single trade signal.

    All fields are JSON-serialisable (float / str / bool / int).
    Serialise to dict via ``asdict(record)`` for API responses.
    """

    ticker: str
    date: str
    category: str           # "BLUE" | "AMBER"
    status: str             # "SL_HIT" | "JACKPOT" | "RUNNING" | "LIVE"
    entry: float
    stop_loss: float
    target: float
    risk_pts: float
    reward_pts: float
    rsi: float
    macd_hist: float        # MACD histogram — momentum confirmation
    atr: float              # Average True Range — volatility context
    vol_ratio: float        # Day volume / 5-day avg volume
    price_vs_sma200: float  # % above 200 SMA — trend strength
    confidence_score: float # 0–100 composite score
    jackpot: bool
    chart_url: str

    def to_dict(self) -> dict:
        """Return JSON-serialisable dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# 5. STRATEGY: Technical Indicator Engine (fully vectorised)
# ---------------------------------------------------------------------------

class IndicatorEngine:
    """
    Stateless, vectorised indicator engine.

    All methods operate on entire Series/DataFrames — zero Python-level loops.

    References:
        - Wilder RSI: Welles Wilder, "New Concepts in Technical Trading Systems" (1978)
        - ATR: same source
        - MACD: Gerald Appel (1979)
    """

    @staticmethod
    def wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """
        Wilder-smoothed RSI (exponential smoothing, alpha=1/period).

        Superior to simple rolling-mean RSI because it matches the original
        specification and reduces lag without introducing overshoot.

        Args:
            close: Closing price series (datetime-indexed).
            period: Lookback window (default 14).

        Returns:
            RSI series in range [0, 100].
        """
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)

        # Wilder smoothing = EMA with alpha = 1/period
        alpha = 1.0 / period
        avg_gain = gain.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        """
        Standard MACD with EMA crossover and histogram.

        Args:
            close: Closing price series.
            fast: Fast EMA period (default 12).
            slow: Slow EMA period (default 26).
            signal: Signal line EMA period (default 9).

        Returns:
            DataFrame with columns ['macd', 'signal', 'histogram'].
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return pd.DataFrame(
            {"macd": macd_line, "signal": signal_line, "histogram": histogram},
            index=close.index,
        )

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average True Range (Wilder smoothing).

        ATR normalises stop-loss distances to market volatility, reducing
        the risk of stops being placed inside normal noise.

        Args:
            high: Daily high series.
            low: Daily low series.
            close: Daily close series.
            period: ATR period (default 14).

        Returns:
            ATR series.
        """
        prev_close = close.shift(1)
        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    @staticmethod
    def sma(series: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average."""
        return series.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def vol_ratio(volume: pd.Series, lookback: int = 5) -> pd.Series:
        """Current volume divided by rolling average — volume surge detector."""
        avg = volume.rolling(window=lookback, min_periods=lookback).mean()
        return volume / avg.replace(0, np.nan)


# ---------------------------------------------------------------------------
# 6. CONFIDENCE SCORING ENGINE
# ---------------------------------------------------------------------------

class ConfidenceEngine:
    """
    Transparent, weighted confidence scorer.

    Each sub-score is capped at its weight and the total sums to 100.
    Weights are intentionally visible to build user trust.

    Dimension weights (must sum to 100):
        Trend alignment      : 30
        Momentum (RSI)       : 20
        Volume confirmation  : 20
        MACD confirmation    : 15
        Volatility regime    : 15
    """

    WEIGHTS = {
        "trend": 30,
        "momentum": 20,
        "volume": 20,
        "macd": 15,
        "volatility": 15,
    }

    @classmethod
    def score(
        cls,
        close: float,
        sma44: float,
        sma200: float,
        rsi: float,
        vol_ratio: float,
        macd_hist: float,
        atr: float,
    ) -> float:
        """
        Compute 0–100 confidence score for a single signal.

        Args:
            close: Entry close price.
            sma44: 44-period SMA at entry.
            sma200: 200-period SMA at entry.
            rsi: Wilder RSI at entry.
            vol_ratio: Volume surge ratio.
            macd_hist: MACD histogram value.
            atr: Average True Range at entry.

        Returns:
            Composite confidence score in [0, 100].
        """
        score = 0.0

        # --- Trend Alignment (30 pts) ---
        if close > sma44 > sma200:
            spread_pct = (close - sma200) / sma200 * 100
            # Full 30 pts if 5–20 % above SMA200 (sweet spot); taper outside
            score += cls.WEIGHTS["trend"] * min(1.0, spread_pct / 20.0)

        # --- Momentum via RSI (20 pts) ---
        # Optimal RSI zone: 55–75 (strong but not overbought)
        if 55 <= rsi <= 75:
            normalised = 1.0 - abs(rsi - 65) / 10.0
            score += cls.WEIGHTS["momentum"] * max(0.0, normalised)
        elif rsi > 75:
            # Overbought penalty
            score += cls.WEIGHTS["momentum"] * 0.3

        # --- Volume Surge (20 pts) ---
        if vol_ratio >= 1.5:
            score += cls.WEIGHTS["volume"]
        elif vol_ratio >= 1.0:
            score += cls.WEIGHTS["volume"] * (vol_ratio - 1.0) / 0.5

        # --- MACD Histogram Confirmation (15 pts) ---
        if macd_hist > 0:
            score += cls.WEIGHTS["macd"]
        elif macd_hist > -0.5:
            score += cls.WEIGHTS["macd"] * 0.4

        # --- Volatility Regime via ATR (15 pts) ---
        # Reward trades where ATR/Close is in a tradeable range (0.5%–3%)
        atr_pct = (atr / close) * 100
        if 0.5 <= atr_pct <= 3.0:
            score += cls.WEIGHTS["volatility"]
        elif atr_pct < 0.5:
            score += cls.WEIGHTS["volatility"] * 0.5  # Too quiet
        # > 3 % = too volatile, 0 pts

        return round(min(score, 100.0), 1)


# ---------------------------------------------------------------------------
# 7. FACTORY: Signal Generator
# ---------------------------------------------------------------------------

class SignalFactory:
    """
    Applies the Triple-Bullish strategy to a fully-enriched OHLCV DataFrame
    and manufactures ``SignalRecord`` objects.

    The entire enrichment pipeline uses vectorised Pandas — the only loop
    iterates over stocks, not over rows within a stock.
    """

    def __init__(self) -> None:
        self._ind = IndicatorEngine()
        self._conf = ConfidenceEngine()

    def enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add all indicator columns to ``data`` in-place (vectorised).

        Args:
            data: Raw OHLCV DataFrame from yfinance.

        Returns:
            Enriched DataFrame with additional indicator columns.
        """
        c = data["Close"]
        data["SMA_44"] = self._ind.sma(c, cfg.sma_fast)
        data["SMA_200"] = self._ind.sma(c, cfg.sma_slow)
        data["RSI"] = self._ind.wilder_rsi(c, cfg.rsi_period)
        data["ATR"] = self._ind.atr(data["High"], data["Low"], c, cfg.atr_period)
        data["Vol_Ratio"] = self._ind.vol_ratio(data["Volume"], cfg.vol_lookback)

        macd_df = self._ind.macd(c, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
        data["MACD_Hist"] = macd_df["histogram"]
        return data

    def build_signal(
        self, ticker: str, data: pd.DataFrame, target_date: pd.Timestamp
    ) -> Optional[SignalRecord]:
        """
        Evaluate Triple-Bullish conditions at ``target_date`` and return
        a ``SignalRecord`` if conditions are met, else ``None``.

        Triple-Bullish Conditions:
            1. Close > SMA_44 > SMA_200   (trend alignment)
            2. Close > Open               (bullish daily candle)

        Blue vs Amber classification:
            Blue: RSI > threshold AND volume surge AND price > SMA200 × premium
            Amber: Meets triple-bullish but not all Blue criteria

        Args:
            ticker: Exchange ticker string (e.g., "RELIANCE.NS").
            data: Enriched OHLCV DataFrame.
            target_date: The analysis/backtest timestamp.

        Returns:
            ``SignalRecord`` or ``None`` if conditions not met.
        """
        if target_date not in data.index:
            return None

        row = data.loc[target_date]
        close = float(row["Close"])
        open_p = float(row["Open"])
        low_p = float(row["Low"])
        sma44 = float(row["SMA_44"])
        sma200 = float(row["SMA_200"])
        rsi = float(row["RSI"])
        atr = float(row["ATR"])
        vol_ratio = float(row["Vol_Ratio"])
        macd_hist = float(row["MACD_Hist"])

        # Skip if any indicator is NaN
        if any(np.isnan(v) for v in [sma44, sma200, rsi, atr, vol_ratio, macd_hist]):
            return None

        # --- Triple-Bullish Gate ---
        if not (close > sma44 > sma200 and close > open_p):
            return None

        # --- Stop-loss & Target ---
        risk_pts = close - low_p
        if risk_pts <= 0:
            return None
        target_price = close + (cfg.risk_reward * risk_pts)

        # --- Category ---
        is_blue = (
            rsi > cfg.blue_rsi_min
            and vol_ratio > 1.0
            and close > sma200 * cfg.blue_price_premium
        )
        category = "BLUE" if is_blue else "AMBER"

        # --- Backtest outcome (vectorised slice, no row loop) ---
        future = data[data.index > target_date][["High", "Low"]]
        status = "LIVE"
        jackpot = False

        if not future.empty:
            sl_hit = (future["Low"] <= low_p).values
            tgt_hit = (future["High"] >= target_price).values
            combined = np.column_stack([sl_hit, tgt_hit])

            # Find first event using argmax on any-True mask
            event_mask = combined.any(axis=1)
            if event_mask.any():
                first_idx = int(event_mask.argmax())
                if combined[first_idx, 1] and not combined[first_idx, 0]:
                    status = "JACKPOT"
                    jackpot = True
                elif combined[first_idx, 0]:
                    status = "SL_HIT"
                else:
                    status = "RUNNING"
            else:
                status = "RUNNING"

        # --- Confidence Score ---
        confidence = self._conf.score(
            close, sma44, sma200, rsi, vol_ratio, macd_hist, atr
        )

        symbol = ticker.replace(".NS", "")
        return SignalRecord(
            ticker=symbol,
            date=str(target_date.date()),
            category=category,
            status=status,
            entry=round(close, 2),
            stop_loss=round(low_p, 2),
            target=round(target_price, 2),
            risk_pts=round(risk_pts, 2),
            reward_pts=round(target_price - close, 2),
            rsi=round(rsi, 1),
            macd_hist=round(macd_hist, 4),
            atr=round(atr, 2),
            vol_ratio=round(vol_ratio, 2),
            price_vs_sma200=round((close / sma200 - 1) * 100, 2),
            confidence_score=confidence,
            jackpot=jackpot,
            chart_url=f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}",
        )


# ---------------------------------------------------------------------------
# 8. DATA FETCHER: Concurrent, fault-tolerant
# ---------------------------------------------------------------------------

class DataFetcher:
    """
    Concurrent OHLCV data fetcher using ThreadPoolExecutor.

    yfinance is I/O-bound so threading (not multiprocessing) is appropriate.
    Workers are configurable via ``FETCH_WORKERS`` env var.
    """

    def __init__(self, workers: int = cfg.fetch_workers) -> None:
        self._workers = workers

    def _fetch_one(
        self, ticker: str, start: datetime, end: datetime
    ) -> tuple[str, Optional[pd.DataFrame]]:
        """Fetch a single ticker; returns (ticker, df) or (ticker, None) on error."""
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if df.empty:
                return ticker, None
            # Flatten MultiIndex columns produced by yfinance ≥ 0.2
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return ticker, df
        except Exception as exc:
            log.warning("Fetch failed for %s: %s", ticker, exc)
            return ticker, None

    def fetch_batch(
        self,
        tickers: list[str],
        start: datetime,
        end: datetime,
        progress_callback=None,
    ) -> dict[str, pd.DataFrame]:
        """
        Concurrently fetch OHLCV data for a list of tickers.

        Args:
            tickers: List of exchange ticker strings.
            start: History start date.
            end: History end date (usually today).
            progress_callback: Optional callable(completed, total) for UI updates.

        Returns:
            Dict mapping ticker → enriched DataFrame (failed tickers omitted).
        """
        results: dict[str, pd.DataFrame] = {}
        completed = 0

        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            futures = {
                pool.submit(self._fetch_one, t, start, end): t for t in tickers
            }
            for future in as_completed(futures):
                ticker, df = future.result()
                completed += 1
                if df is not None and len(df) >= cfg.sma_slow + 10:
                    results[ticker] = df
                if progress_callback:
                    progress_callback(completed, len(tickers))

        log.info("Fetched %d / %d tickers successfully.", len(results), len(tickers))
        return results


# ---------------------------------------------------------------------------
# 9. ANALYSER: Orchestrates fetch → enrich → signal → output
# ---------------------------------------------------------------------------

class Nifty200Analyser:
    """
    Top-level orchestrator.

    Coordinates the DataFetcher, SignalFactory, and output rendering.
    Designed to be called from Streamlit or a CLI / REST endpoint.
    """

    def __init__(self) -> None:
        self._fetcher = DataFetcher()
        self._factory = SignalFactory()

    def run(
        self, target_date: datetime.date, tickers: list[str] = NIFTY_200
    ) -> list[SignalRecord]:
        """
        Full pipeline: fetch → enrich → screen → score → return records.

        Args:
            target_date: Date to evaluate signals on.
            tickers: Universe of tickers (defaults to Nifty 200).

        Returns:
            List of ``SignalRecord`` objects sorted by confidence desc.
        """
        start = datetime.combine(target_date, datetime.min.time()) - timedelta(
            days=cfg.history_days
        )
        end = datetime.now()
        t_ts = pd.Timestamp(target_date)

        # --- Progress bar setup ---
        progress_bar = st.progress(0, text="Fetching market data…")

        def _update(done: int, total: int) -> None:
            pct = done / total
            progress_bar.progress(pct, text=f"Processing {done}/{total} stocks…")

        raw_data = self._fetcher.fetch_batch(tickers, start, end, _update)
        progress_bar.progress(1.0, text="Generating signals…")

        records: list[SignalRecord] = []
        for ticker, df in raw_data.items():
            try:
                enriched = self._factory.enrich(df.copy())
                signal = self._factory.build_signal(ticker, enriched, t_ts)
                if signal:
                    records.append(signal)
            except Exception as exc:
                log.error("Signal error for %s: %s", ticker, exc, exc_info=True)

        progress_bar.empty()
        records.sort(key=lambda r: r.confidence_score, reverse=True)
        log.info("Generated %d signals for %s.", len(records), target_date)
        return records


# ---------------------------------------------------------------------------
# 10. STREAMLIT UI
# ---------------------------------------------------------------------------

def _confidence_colour(score: float) -> str:
    """Map confidence score to a traffic-light hex colour."""
    if score >= 75:
        return "#00c853"  # green
    if score >= 50:
        return "#ffd600"  # amber
    return "#ff1744"      # red


def _status_emoji(status: str) -> str:
    return {
        "JACKPOT": "🔥",
        "SL_HIT": "🔴",
        "RUNNING": "⏳",
        "LIVE": "🟢",
    }.get(status, "❓")


def render_dashboard(records: list[SignalRecord], target_date) -> None:
    """
    Render the Streamlit UI from a list of SignalRecord objects.

    Args:
        records: Sorted list of signals from ``Nifty200Analyser.run()``.
        target_date: The date string / date used for the analysis.
    """
    if not records:
        st.warning("No signals found for the selected date.")
        return

    df = pd.DataFrame([r.to_dict() for r in records])

    # ---- Summary metrics ----
    blue = df[df["category"] == "BLUE"]
    amber = df[df["category"] == "AMBER"]
    blue_jackpots = int(blue["jackpot"].sum())
    blue_total = len(blue)
    accuracy = round(blue_jackpots / blue_total * 100, 1) if blue_total else 0.0

    st.subheader(f"📊 Dashboard — {target_date}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔵 Blue Signals", blue_total)
    c2.metric("🟡 Amber Signals", len(amber))
    c3.metric("🔥 Blue Jackpots", blue_jackpots)
    c4.metric("🎯 Blue Accuracy", f"{accuracy}%")
    c5.metric("⚡ Avg Confidence", f"{df['confidence_score'].mean():.1f}")

    st.divider()

    # ---- Styled Signal Table ----
    st.write("### 📋 Signal Table (sorted by Confidence)")

    display_cols = [
        "ticker", "category", "status", "entry", "stop_loss", "target",
        "rsi", "vol_ratio", "macd_hist", "atr", "confidence_score",
        "price_vs_sma200", "jackpot", "chart_url",
    ]
    display_df = df[display_cols].copy()
    display_df["status"] = display_df["status"].apply(
        lambda s: f"{_status_emoji(s)} {s}"
    )
    display_df["category"] = display_df["category"].apply(
        lambda c: f"🔵 {c}" if c == "BLUE" else f"🟡 {c}"
    )

    st.dataframe(
        display_df,
        column_config={
            "ticker": st.column_config.TextColumn("Stock"),
            "category": st.column_config.TextColumn("Category"),
            "status": st.column_config.TextColumn("Status"),
            "entry": st.column_config.NumberColumn("Entry ₹", format="₹%.2f"),
            "stop_loss": st.column_config.NumberColumn("Stop ₹", format="₹%.2f"),
            "target": st.column_config.NumberColumn("Target ₹", format="₹%.2f"),
            "rsi": st.column_config.NumberColumn("RSI", format="%.1f"),
            "vol_ratio": st.column_config.NumberColumn("Vol Surge", format="%.2fx"),
            "macd_hist": st.column_config.NumberColumn("MACD Hist", format="%.4f"),
            "atr": st.column_config.NumberColumn("ATR ₹", format="₹%.2f"),
            "confidence_score": st.column_config.ProgressColumn(
                "Confidence", min_value=0, max_value=100, format="%.1f"
            ),
            "price_vs_sma200": st.column_config.NumberColumn(
                "% vs SMA200", format="%.2f%%"
            ),
            "jackpot": st.column_config.CheckboxColumn("Target Met"),
            "chart_url": st.column_config.LinkColumn("TradingView"),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    # ---- Individual Expanders ----
    st.write("### 💡 Deep-Dive Analysis")
    for rec in records:
        colour = _confidence_colour(rec.confidence_score)
        header = (
            f"{_status_emoji(rec.status)} {rec.ticker} "
            f"| {rec.category} "
            f"| Confidence: {rec.confidence_score}/100"
        )
        with st.expander(header):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown("**Trade Setup**")
                st.write(f"Entry: ₹{rec.entry:,.2f}")
                st.write(f"Stop Loss: ₹{rec.stop_loss:,.2f} (risk ₹{rec.risk_pts:.2f})")
                st.write(f"Target (1:{cfg.risk_reward:.0f}): ₹{rec.target:,.2f}")
            with col_b:
                st.markdown("**Indicator Readings**")
                st.write(f"RSI (Wilder): {rec.rsi}")
                st.write(f"MACD Histogram: {rec.macd_hist}")
                st.write(f"ATR: ₹{rec.atr}")
                st.write(f"Volume Surge: {rec.vol_ratio:.2f}×")
            with col_c:
                st.markdown("**Confidence Breakdown**")
                st.markdown(
                    f"<span style='color:{colour}; font-size:2em; "
                    f"font-weight:bold;'>{rec.confidence_score}/100</span>",
                    unsafe_allow_html=True,
                )
                st.write(f"% above SMA200: {rec.price_vs_sma200:.2f}%")
                st.link_button(f"📈 {rec.ticker} on TradingView", rec.chart_url)


def main() -> None:
    """Streamlit entry point."""

    st.set_page_config(
        page_title="Nifty 200 | Institutional Signal Engine",
        layout="wide",
        page_icon="🛡️",
    )

    # --- SEBI Compliance Banner ---
    st.error("⚠️ DISCLAIMER: FOR EDUCATIONAL PURPOSES ONLY — NOT SEBI REGISTERED")
    st.markdown(
        """
        <div style="background:#fff3cd;padding:12px;border-radius:8px;
                    border:1px solid #ffeeba;margin-bottom:1rem;">
            <b style="color:#856404;">⚠️ Risk Warning:</b>
            <span style="color:#856404;font-size:0.9em;">
            Signals are generated algorithmically from historical data.
            Not investment advice. Trading involves substantial risk of loss.
            Consult a SEBI-registered advisor before acting on any signal.
            We accept no liability for financial losses.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.title("🛡️ Nifty 200 — Institutional Signal Engine v2.0")
    st.caption(
        "Wilder RSI · EMA MACD · ATR Stop-Loss · Volume Surge · "
        "Confidence Scoring · Concurrent Fetch"
    )

    # --- Sidebar Controls ---
    with st.sidebar:
        st.header("⚙️ Parameters")
        target_date = st.date_input(
            "Analysis Date",
            datetime.now().date() - timedelta(days=1),
            help="Select a past date for backtesting or today for live signals.",
        )
        show_debug = st.checkbox("Show debug logs", value=False)
        st.divider()
        st.markdown("**Indicator Settings** (override env vars)")
        st.caption(f"RSI Period: {cfg.rsi_period} | SMA Fast: {cfg.sma_fast} | SMA Slow: {cfg.sma_slow}")
        st.caption(f"ATR Period: {cfg.atr_period} | Fetch Workers: {cfg.fetch_workers}")

    if st.button("🚀 Run Institutional Analysis", type="primary"):
        t0 = time.perf_counter()
        analyser = Nifty200Analyser()

        with st.spinner("Running vectorised signal pipeline…"):
            records = analyser.run(target_date)

        elapsed = time.perf_counter() - t0
        st.success(
            f"✅ Scan complete — {len(records)} signals found in {elapsed:.1f}s"
        )

        render_dashboard(records, target_date)

        # --- JSON export ---
        st.divider()
        with st.expander("📤 Export — Raw JSON (API-ready)"):
            import json
            st.json(json.dumps([r.to_dict() for r in records], indent=2))

        if show_debug:
            with st.expander("🐛 Debug Logs"):
                try:
                    with open("nifty200_analyzer.log") as f:
                        st.code(f.read()[-5000:], language="log")
                except FileNotFoundError:
                    st.info("Log file not yet created.")

    st.divider()
    st.caption(
        "Institutional-Grade Vectorised Engine | "
        "Wilder RSI | EMA MACD | ATR Volatility | Confidence Scoring | "
        "Concurrent Data Fetch"
    )


if __name__ == "__main__":
    main()
