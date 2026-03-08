import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Arth Sutra", layout="wide")

st.title("📈 Arth Sutra - Swing Trading Scanner")

# NSE sample stocks (you can expand later)
stocks = [
"RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
"SBIN.NS","LT.NS","AXISBANK.NS","ITC.NS","KOTAKBANK.NS"
]

# RSI calculation
def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100/(1+rs))


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
            stop = entry * 0.97

            future = df["Close"].iloc[i:i+5]

            if float(future.max()) >= target:
                wins += 1

            trades += 1

    if trades == 0:
        return 0

    return round((wins/trades)*100,2)


# Scanner
def scan():

    results = []

    for stock in stocks:

        df = yf.download(stock, period="1y", interval="1d", progress=False)

        if df.empty or len(df) < 220:
            continue

        # Indicators
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

        # Trend conditions
        if close > sma44:
            score += 20

        if sma44 > sma200:
            score += 20

        # Momentum
        if 50 < r < 65:
            score += 20

        # Volume spike
        if volume > avg_vol:
            score += 20

        # Breakout
        breakout = close >= high20 * 0.98

        if breakout:
            score += 20

        # Trade levels
        entry = round(close,2)
        stoploss = round(close*0.97,2)
        target = round(close*1.06,2)

        winrate = backtest(df)

        results.append({
            "Stock": stock,
            "Price": entry,
            "AI Probability %": score,
            "Backtest WinRate %": winrate,
            "Entry": entry,
            "Stoploss": stoploss,
            "Target": target
        })

    df_results = pd.DataFrame(results)

    if not df_results.empty:
        df_results = df_results.sort_values(by="AI Probability %", ascending=False)

    return df_results


# UI button
if st.button("Run Arth Sutra Scanner"):

    data = scan()

    if data.empty:

        st.warning("No strong setups found today")

    else:

        st.dataframe(data)

        best = data.iloc[0]

        st.success(
            f"Top Stock: {best['Stock']} | Probability {best['AI Probability %']}% | Backtest WinRate {best['Backtest WinRate %']}%"
        )