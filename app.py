import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="NSE 500 SMA44/SMA200 Bullish Scanner", layout="wide")
st.title("📈 NSE 500 SMA44/SMA200 Bullish Scanner – Full List")

# --- Fetch full NIFTY 500 symbols list dynamically ---
@st.cache_data(ttl=86400)
def fetch_nifty500_symbols():
    import requests
    from bs4 import BeautifulSoup

    url = "https://en.wikipedia.org/wiki/NIFTY_500"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html5lib")
    tables = soup.find_all("table", {"class": "wikitable"})
    symbols = []

    # Parse the first table that contains the constituents
    for table in tables:
        df = pd.read_html(str(table))[0]
        if "Symbol" in df.columns:
            for sym in df["Symbol"].dropna().tolist():
                sym = str(sym).upper().strip() + ".NS"
                symbols.append(sym)

    return list(set(symbols))  # remove duplicates

# --- SMA calculation ---
def sma(series, period):
    return series.rolling(period).mean()

# --- Check bullish condition ---
def check_bullish(df):
    df["SMA44"] = sma(df["Close"], 44)
    df["SMA200"] = sma(df["Close"], 200)

    if len(df) < 2:
        return None

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Bullish trend & green candle above SMA44
    if pd.notna(latest["SMA44"]) and pd.notna(latest["SMA200"]):
        if (latest["Close"] > latest["Open"]
            and latest["Close"] > latest["SMA44"]
            and latest["SMA44"] > latest["SMA200"]
            and latest["SMA44"] > prev["SMA44"]
            and latest["SMA200"] > prev["SMA200"]):
            return {
                "Date": latest.name.date(),
                "Close": round(latest["Close"],2),
                "SMA44": round(latest["SMA44"],2),
                "SMA200": round(latest["SMA200"],2)
            }
    return None

# --- Scan a single symbol ---
def scan_symbol(symbol):
    try:
        df = yf.download(symbol, period="1y", progress=False)
        if df.empty:
            return None
        result = check_bullish(df)
        if result:
            result["Symbol"] = symbol
            return result
    except Exception:
        return None
    return None

# --- Scan all symbols in parallel ---
def run_scan(symbols):
    signals = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(scan_symbol, s): s for s in symbols}
        for future in as_completed(futures):
            res = future.result()
            if res:
                signals.append(res)
    return signals

# --- UI ---
if st.button("Scan NIFTY 500 Bullish Setups"):
    st.info("Fetching NIFTY 500 list → then scanning all symbols… this can take a few minutes.")

    symbols = fetch_nifty500_symbols()
    if not symbols:
        st.error("Failed to fetch NIFTY 500 symbol list.")
    else:
        with st.spinner("Scanning NIFTY 500 symbols for bullish setups…"):
            results = run_scan(symbols)

        if not results:
            st.warning("No bullish setups found today — but the scan completed successfully.")
        else:
            df = pd.DataFrame(results)
            df = df[["Date","Symbol","Close","SMA44","SMA200"]]
            st.success(f"Found {len(df)} bullish setups!")
            st.dataframe(df.sort_values(by="Close", ascending=False))