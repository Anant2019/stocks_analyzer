import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Arth Sutra PRO", layout="wide")
st.title("📈 Arth Sutra PRO - NSE Swing Trading Scanner")

# Load NSE 500 stocks
@st.cache_data
def load_stocks():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        symbols = df["Symbol"].tolist()
        symbols = [s + ".NS" for s in symbols]
        return symbols
    except:
        return ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS"]  # fallback

# RSI calculation
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100/(1+rs))

# Relative Strength vs Nifty
def relative_strength(stock_df, index_df):
    stock_return = stock_df["Close"].pct_change().sum()
    index_return = index_df["Close"].pct_change().sum()
    return round((stock_return - index_return)*100,2)

# Backtesting function
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
    if trades == 0:
        return 0
    return round((wins/trades)*100,2)

# Main scanner
def scan():
    stocks = load_stocks()
    results = []
    # Download Nifty for relative strength
    index_df = yf.download("^NSEI", period="1y", progress=False)
    for stock in stocks[:100]:  # limit 100 for speed; remove slice for full NSE500
        try:
            df = yf.download(stock, period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 220:
                continue
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
            if close > sma44:
                score += 20
            if sma44 > sma200:
                score += 20
            if 50 < r < 65:
                score += 20
            if volume > avg_vol:
                score += 20
            if close >= high20 * 0.98:
                score += 20
            rs = relative_strength(df, index_df)
            entry = round(close,2)
            stoploss = round(close*0.97,2)
            target = round(close*1.06,2)
            winrate = backtest(df)
            results.append({
                "Stock": stock,
                "AI Score": score,
                "Relative Strength %": rs,
                "Backtest WinRate %": winrate,
                "Entry": entry,
                "Stoploss": stoploss,
                "Target": target
            })
        except:
            continue
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results["AI Score"] = pd.to_numeric(df_results["AI Score"], errors='coerce')
        df_results["Relative Strength %"] = pd.to_numeric(df_results["Relative Strength %"], errors='coerce')
        df_results = df_results.dropna(subset=["AI Score","Relative Strength %"])
        df_results = df_results.sort_values(by=["AI Score","Relative Strength %"], ascending=False)
    return df_results

# UI
if st.button("Run Arth Sutra PRO Scanner"):
    with st.spinner("Scanning NSE stocks..."):
        data = scan()
    if data.empty:
        st.warning("No strong setups found today")
    else:
        st.dataframe(data)
        best = data.iloc[0]
        st.success(
            f"Top Stock: {best['Stock']} | Score {best['AI Score']} | WinRate {best['Backtest WinRate %']}%"
        )