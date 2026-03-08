import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Arth Sutra PRO 500", layout="wide")
st.title("📊 Arth Sutra PRO 500 - NSE Swing Trading Dashboard")

# --- Load NSE 500 stocks ---
@st.cache_data(ttl=86400)
def load_stocks():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        symbols = df["Symbol"].tolist()
        symbols = [s + ".NS" for s in symbols]
        return symbols
    except:
        # fallback
        return ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS"]

# --- RSI Calculation ---
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100/(1+rs))

# --- Relative Strength vs Nifty ---
def relative_strength(stock_df, index_df):
    stock_return = stock_df["Close"].pct_change().sum()
    index_return = index_df["Close"].pct_change().sum()
    return round((stock_return - index_return)*100,2)

# --- Backtesting Function ---
def backtest(df):
    wins = 0
    trades = 0
    for i in range(200, len(df)-5):
        close = float(df["Close"].iloc[i])
        sma44 = float(df["SMA44"].iloc[i])
        sma200 = float(df["SMA200"].iloc[i])
        r = float(df["RSI"].iloc[i])
        if close > sma44 and sma44 > sma200 and 50 < r < 65:
            entry = close
            target = entry * 1.05
            future = df["Close"].iloc[i:i+5]
            if float(future.max()) >= target:
                wins += 1
            trades += 1
    return round((wins/trades)*100,2) if trades>0 else 0

# --- Scan Individual Stock ---
def scan_stock(stock, index_df):
    try:
        df = yf.download(stock, period="1y", interval="1d", progress=False)
        if df.empty or len(df)<220:
            return None
        df["SMA44"] = df["Close"].rolling(44).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()
        df["RSI"] = rsi(df["Close"])
        df["High20"] = df["High"].rolling(20).max()
        latest = df.iloc[-1]

        close = float(latest["Close"])
        sma44 = float(latest["SMA44"])
        sma200 = float(latest["SMA200"])
        r = float(latest["RSI"])
        high20 = float(latest["High20"])
        volume = float(latest["Volume"])
        avg_vol = float(df["Volume"].mean())

        score = 0
        if close > sma44: score+=20
        if sma44 > sma200: score+=20
        if 50<r<65: score+=20
        if volume>avg_vol: score+=20
        if close>=high20*0.98: score+=20

        rs = relative_strength(df, index_df)
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
        return None

# --- Scan All Stocks (Parallel) ---
def scan_all(stocks):
    results = []
    index_df = yf.download("^NSEI", period="1y", progress=False)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_stock, stock, index_df): stock for stock in stocks}
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results["AI Score"] = pd.to_numeric(df_results["AI Score"], errors='coerce')
        df_results["Relative Strength %"] = pd.to_numeric(df_results["Relative Strength %"], errors='coerce')
        df_results = df_results.dropna(subset=["AI Score","Relative Strength %"])
        df_results = df_results.sort_values(by=["AI Score","Relative Strength %"], ascending=False)
    return df_results

# --- Card Color ---
def get_card_color(score):
    if score>=80: return "#d4edda" # green
    elif score>=60: return "#fff3cd" # yellow
    else: return "#f8d7da" # red

# --- Run Scanner ---
if st.button("Run Arth Sutra PRO 500"):
    stocks = load_stocks()
    with st.spinner("Scanning NSE 500 stocks... This may take a few minutes."):
        data = scan_all(stocks)
    if data.empty:
        st.warning("No strong setups found today")
    else:
        # Display cards in grid
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
                    <b>AI Score:</b> {row['AI Score']} <br>
                    <b>Relative Strength %:</b> {row['Relative Strength %']}<br>
                    <b>WinRate %:</b> {row['Backtest WinRate %']}<br>
                    <b>Entry:</b> {row['Entry']} | <b>Stoploss:</b> {row['Stoploss']} | <b>Target:</b> {row['Target']}
                    </div>
                    """, unsafe_allow_html=True)