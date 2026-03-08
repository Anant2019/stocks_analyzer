import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from nsepy import get_history
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="NSE500 SMA44/SMA200 Bullish Scanner", layout="wide")
st.title("📈 NSE 500 SMA44/SMA200 Bullish Scanner")

# Full NSE500 symbols embedded (truncated here; in production, include all 500)
nse500_symbols = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","LT.NS","AXISBANK.NS",
    "ITC.NS","KOTAKBANK.NS","BHARTIARTL.NS","UPL.NS","ADANIPORTS.NS","SBILIFE.NS","ASIANPAINT.NS",
    "HINDUNILVR.NS","MARUTI.NS","NESTLEIND.NS","BAJAJ-AUTO.NS","TECHM.NS","WIPRO.NS","HCLTECH.NS",
    "HDFCLIFE.NS","ULTRACEMCO.NS","DIVISLAB.NS","TITAN.NS","INDUSINDBK.NS","POWERGRID.NS","IOC.NS",
    "ONGC.NS","BPCL.NS","TATAMOTORS.NS","JSWSTEEL.NS","GRASIM.NS","COALINDIA.NS","HDFC.NS","BAJAJFINSV.NS",
    "EICHERMOT.NS","CIPLA.NS","SUNPHARMA.NS","HINDALCO.NS","BRITANNIA.NS","LTIM.NS","ADANIGREEN.NS",
    "ICICIPRULI.NS","SHREECEM.NS","M&M.NS","BAJFINANCE.NS","VEDL.NS","HEROMOTOCO.NS","DRREDDY.NS"
    # Add remaining NSE500 symbols here
]

def sma(series, period):
    return series.rolling(period).mean()

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
    except:
        return None

def check_bullish(df):
    df["SMA44"] = sma(df["Close"], 44)
    df["SMA200"] = sma(df["Close"], 200)
    latest = df.iloc[-1]
    if pd.isna(latest["SMA44"]) or pd.isna(latest["SMA200"]):
        return None
    # Slight tolerance to catch near-bullish candles
    if latest["Close"] >= latest["Open"] and latest["Close"] >= latest["SMA44"]*0.995 and latest["SMA44"] > latest["SMA200"]:
        return {
            "Date": latest.name.date(),
            "Close": round(latest["Close"],2),
            "SMA44": round(latest["SMA44"],2),
            "SMA200": round(latest["SMA200"],2)
        }
    return None

def scan_symbol(sym):
    df = fetch_history(sym)
    if df is None:
        return None
    signal = check_bullish(df)
    if signal:
        signal["Symbol"] = sym
        return signal
    return None

def run_scan(symbols):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_symbol, s): s for s in symbols}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
    return results

if st.button("Scan NSE 500 Bullish Setups"):
    st.info("Scanning NSE 500, please wait...")
    with st.spinner("Processing..."):
        signals = run_scan(nse500_symbols)
    if not signals:
        st.warning("No bullish setups found today, but scan completed successfully.")
    else:
        df_signals = pd.DataFrame(signals)
        df_signals = df_signals[["Date","Symbol","Close","SMA44","SMA200"]]
        st.success(f"Found {len(df_signals)} bullish setups!")
        st.dataframe(df_signals.sort_values(by="Close",ascending=False))