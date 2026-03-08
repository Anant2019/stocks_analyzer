import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from nsepy import get_history

st.set_page_config(page_title="Arth Sutra NSE Bullish Scanner", layout="wide")
st.title("📈 Arth Sutra NSE Bullish Scanner — Test Signals Today")

# Load a test list of symbols (top NSE stocks)
symbols = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","LT","AXISBANK","ITC","KOTAKBANK",
    "BHARTIARTL","UPL","ADANIPORTS","SBILIFE","ASIANPAINT"
]

# SMA function
def sma(series, period):
    return series.rolling(period).mean()

# Scan function
def scan_stocks(symbols):
    results = []
    today = date.today()
    start = today - timedelta(days=365)

    for sym in symbols:
        try:
            df = get_history(symbol=sym, start=start, end=today)

            if df.shape[0] < 60:
                continue

            df["SMA44"] = sma(df["Close"], 44)
            df["SMA200"] = sma(df["Close"], 200)

            latest = df.iloc[-1]
            close = latest["Close"]
            openp = latest["Open"]
            sma44 = latest["SMA44"]
            sma200 = latest["SMA200"]

            # Condition: bullish candle above SMAs
            if pd.notna(sma44) and pd.notna(sma200):
                if close > openp and close > sma44 and sma44 > sma200:

                    entry = close
                    stoploss = round(close * 0.97, 2)
                    target = round(close * 1.06, 2)

                    results.append({
                        "Symbol": sym,
                        "Close": round(close, 2),
                        "SMA44": round(sma44, 2),
                        "SMA200": round(sma200, 2),
                        "Entry": entry,
                        "Stoploss": stoploss,
                        "Target": target
                    })
        except Exception as e:
            continue

    return pd.DataFrame(results)

# Run scanner
if st.button("Run Today’s Bullish Scanner"):
    with st.spinner("Scanning…"):
        df_signals = scan_stocks(symbols)

    if df_signals.empty:
        st.warning("No signals found in test stocks — expand your symbol list.")
    else:
        st.dataframe(df_signals)