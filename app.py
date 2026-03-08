import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from nsepy import get_history
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="NSE 500 SMA44/SMA200 Bullish Scanner", layout="wide")
st.title("📈 NSE 500 Bullish SMA44/SMA200 Scanner (Stable, No HTML Parsing)")

# ------------------------
# Fetch NIFTY 500 symbols from a static CSV (GitHub hosted)
# ------------------------
@st.cache_data(ttl=86400)
def fetch_nifty500_list():
    url = "https://raw.githubusercontent.com/datasets/nifty-500/main/data/nifty-500-symbols.csv"
    try:
        df = pd.read_csv(url)
        symbols = df["Symbol"].astype(str).tolist()
        symbols = [sym.strip().upper() + ".NS" for sym in symbols]
        return symbols
    except Exception as e:
        st.error(f"Error fetching NIFTY 500 symbols: {e}")
        return []

# ------------------------
# SMA calculation
# ------------------------
def sma(series, period):
    return series.rolling(period).mean()

# ------------------------
# Fetch OHLC from NSE
# ------------------------
def fetch_history(symbol):
    try:
        df = get_history(
            symbol=symbol.replace(".NS", ""),
            start=datetime.now() - timedelta(days=365),
            end=datetime.now()
        )
        if df.empty:
            return None
        return df
    except Exception:
        return None

# ------------------------
# Bullish condition
# ------------------------
def check_bullish(df):
    df["SMA44"] = sma(df["Close"], 44)
    df["SMA200"] = sma(df["Close"], 200)

    latest = df.iloc[-1]
    if pd.isna(latest["SMA44"]) or pd.isna(latest["SMA200"]):
        return None

    # Green candle above SMA44 & SMA44 above SMA200
    if latest["Close"] > latest["Open"] and latest["Close"] > latest["SMA44"] and latest["SMA44"] > latest["SMA200"]:
        return {
            "Date": latest.name.date(),
            "Close": round(latest["Close"], 2),
            "SMA44": round(latest["SMA44"], 2),
            "SMA200": round(latest["SMA200"], 2)
        }
    return None

# ------------------------
# Scan symbol
# ------------------------
def scan_symbol(sym):
    df = fetch_history(sym)
    if df is None:
        return None
    signal = check_bullish(df)
    if signal:
        signal["Symbol"] = sym
        return signal
    return None

# ------------------------
# Run full scan
# ------------------------
def run_scan(symbols):
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(scan_symbol, s): s for s in symbols}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
    return results

# ------------------------
# Streamlit UI
# ------------------------
if st.button("Scan All NIFTY 500 Bullish Setups"):
    st.info("Fetching NIFTY 500 list and scanning, please wait...")
    symbols = fetch_nifty500_list()
    if not symbols:
        st.error("Failed to fetch symbols. Check your internet connection or CSV URL.")
    else:
        with st.spinner("Scanning all 500 symbols... this can take a few minutes"):
            signals = run_scan(symbols)

        if not signals:
            st.warning("No bullish setups found today with your criteria.")
        else:
            df_signals = pd.DataFrame(signals)
            df_signals = df_signals[["Date", "Symbol", "Close", "SMA44", "SMA200"]]
            st.success(f"Found {len(df_signals)} bullish setups!")
            st.dataframe(df_signals.sort_values(by="Close", ascending=False))