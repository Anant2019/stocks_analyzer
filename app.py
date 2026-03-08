import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from nsepy import get_history
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Swing Triple Bullish 44-200 NSE 500", layout="wide")
st.title("📈 Swing Triple Bullish 44-200 NSE 500 Scanner")

# ------------------------
# Helpers
# ------------------------
def sma(series, period):
    return series.rolling(period).mean()

def fetch_stock(symbol):
    try:
        df = get_history(symbol=symbol,
                         start=datetime.now() - timedelta(days=365),
                         end=datetime.now())
        if df.empty:
            return None
        return df
    except:
        return None

def check_bullish(df):
    df["SMA44"] = sma(df["Close"], 44)
    df["SMA200"] = sma(df["Close"], 200)
    df["SMA44_prev2"] = df["SMA44"].shift(2)
    df["SMA200_prev2"] = df["SMA200"].shift(2)

    buy_signals = []
    for i in range(2, len(df)):
        row = df.iloc[i]
        if pd.isna(row["SMA44"]) or pd.isna(row["SMA200"]):
            continue
        is_trending = row["SMA44"] > row["SMA200"] and row["SMA44"] > df.iloc[i-2]["SMA44"] and row["SMA200"] > df.iloc[i-2]["SMA200"]
        is_strong = row["Close"] > row["Open"] and row["Close"] > (row["High"] + row["Low"])/2
        buy = is_trending and is_strong and row["Low"] <= row["SMA44"] and row["Close"] > row["SMA44"]
        if buy:
            entry = row["Close"]
            sl = row["Low"]
            risk = entry - sl
            tgt1 = entry + risk
            tgt2 = entry + 2*risk
            buy_signals.append({
                "Date": row.name.date(),
                "Entry": round(entry,2),
                "SL": round(sl,2),
                "Target1": round(tgt1,2),
                "Target2": round(tgt2,2)
            })
    return buy_signals

def scan_symbol(symbol):
    df = fetch_stock(symbol)
    if df is None:
        return None
    signals = check_bullish(df)
    if signals:
        for s in signals:
            s["Symbol"] = symbol
        return signals
    return None

# ------------------------
# NSE 500 symbols (dynamic fetch recommended, fallback static subset)
# ------------------------
nse500_symbols = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","LT","AXISBANK",
    "ITC","KOTAKBANK","BHARTIARTL","UPL","ADANIPORTS","SBILIFE","ASIANPAINT",
    "HINDUNILVR","MARUTI","NESTLEIND","BAJAJ-AUTO","TECHM","WIPRO","HCLTECH",
    "HDFCLIFE","ULTRACEMCO","DIVISLAB","TITAN","INDUSINDBK","POWERGRID","IOC",
    "ONGC","BPCL","TATAMOTORS","JSWSTEEL","GRASIM","COALINDIA","HDFC","BAJAJFINSV",
    "EICHERMOT","CIPLA","SUNPHARMA","HINDALCO","BRITANNIA","LTIM","ADANIGREEN",
    "ICICIPRULI","SHREECEM","M&M","BAJFINANCE","VEDL","HEROMOTOCO","DRREDDY"
]  # expand to all 500 symbols for real deployment

# ------------------------
# Streamlit UI
# ------------------------
if st.button("Run Swing Triple Bullish Scanner ⚡"):
    st.info("Scanning NSE 500 stocks. This may take 5-10 minutes...")
    all_signals = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_symbol, sym): sym for sym in nse500_symbols}
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_signals.extend(res)

    if not all_signals:
        st.warning("No bullish setups found today — this happens on strict trend days")
    else:
        df_res = pd.DataFrame(all_signals)
        df_res = df_res[["Date","Symbol","Entry","SL","Target1","Target2"]]
        st.success(f"Found {len(df_res)} bullish setups today!")
        st.dataframe(df_res.sort_values(by="Entry", ascending=False))