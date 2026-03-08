import streamlit as st
import pandas as pd
import numpy as np
import requests
from nsetools import Nse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Arth Sutra PRO 500", layout="wide")
st.title("📈 Arth Sutra PRO 500 - NSE 500 Scanner")

nse = Nse()

# Fetch list of symbols
@st.cache_data(ttl=86400)
def get_nse500_symbols():
    try:
        data = nse.get_index_constituents("NIFTY 500")
        return [x["symbol"] for x in data]
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK"]

# Fetch historical data from NSE
def fetch_history(symbol):
    try:
        record = nse.get_history(symbol=symbol, 
                                 start=datetime.now() - timedelta(days=365),
                                 end=datetime.now())
        df = pd.DataFrame(record)
        if df.empty:
            return None
        df.rename(columns={"VWAP":"Close"}, inplace=True)  # fallback
        return df
    except:
        return None

# Scan logic
def scan_stock(symbol):
    df = fetch_history(symbol)
    if df is None or df.shape[0] < 100:
        return None

    df["SMA44"] = df["Close"].rolling(44).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    latest = df.iloc[-1]
    close = latest["Close"]
    openp = latest["Open"]
    sma44 = latest["SMA44"]
    sma200 = latest["SMA200"]

    if pd.isna(sma44) or pd.isna(sma200):
        return None

    # Basic bullish logic
    if close > openp and close > sma44 and sma44 > sma200:

        entry = round(close,2)
        stoploss = round(close * 0.97, 2)
        target = round(close * 1.06, 2)

        return {
            "Symbol": symbol,
            "Close": entry,
            "SMA44": round(sma44,2),
            "SMA200": round(sma200,2),
            "Entry": entry,
            "Stoploss": stoploss,
            "Target": target
        }
    return None

def run_scan(symbols):
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_symbol = {executor.submit(scan_stock, sym): sym for sym in symbols}
        for future in as_completed(future_to_symbol):
            res = future.result()
            if res:
                results.append(res)
    return pd.DataFrame(results)

if st.button("Run NSE 500 Bullish Scanner ⚡"):
    symbols = get_nse500_symbols()
    with st.spinner("Scanning NSE 500 for bullish setups..."):
        df_signals = run_scan(symbols)

    if df_signals.empty:
        st.warning("No bullish setups found today — try expanding parameters.")
    else:
        st.dataframe(df_signals.sort_values(by="Close", ascending=False))