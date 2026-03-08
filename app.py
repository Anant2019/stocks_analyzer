import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

st.set_page_config(page_title="Arth Sutra PRO 500", layout="wide")
st.title("📊 Arth Sutra PRO 500 - Bullish Candle Scanner (SMA44 & SMA200)")

# --- Load NSE 500 tickers ---
@st.cache_data(ttl=86400)
def load_stocks():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        symbols = df["Symbol"].tolist()
        symbols = [s + ".NS" for s in symbols]
        return symbols
    except:
        return ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS"]

# --- Relative Strength ---
def relative_strength(stock_df, index_df):
    stock_return = stock_df["Close"].pct_change().sum()
    index_return = index_df["Close"].pct_change().sum()
    return round((stock_return - index_return)*100,2)

# --- Backtest ---
def backtest(df):
    wins, trades = 0, 0
    for i in range(200, len(df)-5):
        close = float(df["Close"].iloc[i])
        sma44 = float(df["SMA44"].iloc[i])
        sma200 = float(df["SMA200"].iloc[i])
        open_price = float(df["Open"].iloc[i])
        if close > open_price and close > sma44 and sma44 > sma200:
            entry = close
            target = entry * 1.05
            future = df["Close"].iloc[i:i+5]
            if future.max() >= target: wins+=1
            trades+=1
    return round((wins/trades)*100,2) if trades>0 else 0

# --- Scan single stock ---
def scan_stock(stock, index_df):
    for attempt in range(2):
        try:
            df = yf.download(stock, period="1y", interval="1d", progress=False)
            if df.empty or len(df)<220:
                continue
            df["SMA44"] = df["Close"].rolling(44).mean()
            df["SMA200"] = df["Close"].rolling(200).mean()
            df["High20"] = df["High"].rolling(20).max()
            latest = df.iloc[-1]

            close = float(latest["Close"])
            open_price = float(latest["Open"])
            sma44 = float(latest["SMA44"])
            sma200 = float(latest["SMA200"])
            high20 = float(latest["High20"])
            volume = float(latest["Volume"])
            avg_vol = float(df["Volume"].mean())

            # Bullish candle and trend check
            score = 0
            score += 30 if close > sma44 and sma44 > sma200 else 0
            score += 20 if close > open_price else 0
            score += 20 if volume > avg_vol else 0
            score += 20 if close >= high20*0.95 else 0

            rs = relative_strength(df, index_df)
            score += 10 if rs>0 else 0

            winrate = backtest(df)

            return {
                "Stock": stock,
                "AI Score": score,
                "Relative Strength %": rs,
                "Backtest WinRate %": winrate,
                "Entry": round(close,2),
                "Stoploss": round(close*0.97,2),
                "Target": round(close*1.06,2)
            }
        except:
            time.sleep(0.5)
            continue
    return None

# --- Parallel scan with progress ---
def scan_all(stocks):
    results=[]
    index_df = yf.download("^NSEI", period="1y", progress=False)
    total = len(stocks)
    progress = st.progress(0)
    completed = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scan_stock, stock, index_df): stock for stock in stocks}
        for future in as_completed(futures):
            res = future.result()
            if res and res["AI Score"]>=40:
                results.append(res)
            completed+=1
            progress.progress(completed/total)

    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values(by=["AI Score","Relative Strength %"], ascending=False)
    return df_results

# --- Card color ---
def get_card_color(score):
    if score>=70: return "#d4edda"  # green
    elif score>=50: return "#fff3cd" # yellow
    else: return "#f8d7da" # red

# --- Run scanner ---
if st.button("Run Arth Sutra PRO 500"):
    stocks = load_stocks()
    with st.spinner("Scanning NSE 500 stocks for bullish candles above SMA44 & SMA200..."):
        data = scan_all(stocks[:200])  # scan first 200 for speed; increase for full 500
    if data.empty:
        st.warning("No bullish candle setups found today")
    else:
        cols_per_row = 3
        for i in range(0, len(data), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i+j < len(data):
                    row = data.iloc[i+j]
                    color = get_card_color(row["AI Score"])
                    col.markdown(f"""
                    <div style='background-color:{color}; padding:15px; border-radius:10px; margin-bottom:10px'>
                    <h4>{row['Stock']}</h4>
                    <b>AI Score:</b> {row['AI Score']}<br>
                    <b>Relative Strength %:</b> {row['Relative Strength %']}<br>
                    <b>WinRate %:</b> {row['Backtest WinRate %']}<br>
                    <b>Entry:</b> {row['Entry']} | <b>Stoploss:</b> {row['Stoploss']} | <b>Target:</b> {row['Target']}
                    </div>
                    """, unsafe_allow_html=True)