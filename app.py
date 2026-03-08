import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Arth Sutra", layout="wide")

st.title("📈 Arth Sutra - AI Swing Trading Scanner")

# Sample NSE stocks (you can expand to NSE 500 list)
stocks = [
"RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
"SBIN.NS","LT.NS","AXISBANK.NS","ITC.NS","KOTAKBANK.NS"
]

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100/(1+rs))


def backtest(df):

    wins = 0
    trades = 0

    for i in range(50, len(df)-5):

        close = df["Close"].iloc[i]
        ema20 = df["EMA20"].iloc[i]
        ema50 = df["EMA50"].iloc[i]
        r = df["RSI"].iloc[i]

        if close > ema20 and ema20 > ema50 and 50 < r < 65:

            entry = close
            target = entry * 1.05
            stop = entry * 0.97

            future = df["Close"].iloc[i:i+5]

            if future.max() >= target:
                wins += 1

            trades += 1

    if trades == 0:
        return 0

    return round((wins/trades)*100,2)


def scan():

    results = []

    for stock in stocks:

        df = yf.download(stock, period="6mo", interval="1d", progress=False)

        if df.empty or len(df) < 100:
            continue

        df["EMA20"] = df["Close"].ewm(span=20).mean()
        df["EMA50"] = df["Close"].ewm(span=50).mean()
        df["RSI"] = rsi(df["Close"])

        df["High20"] = df["High"].rolling(20).max()

        latest = df.iloc[-1]

        close = float(latest["Close"])
        ema20 = float(latest["EMA20"])
        ema50 = float(latest["EMA50"])
        r = float(latest["RSI"])
        high20 = float(latest["High20"])
        volume = float(latest["Volume"])
        avg_vol = float(df["Volume"].mean())

        score = 0

        if close > ema20:
            score += 20

        if ema20 > ema50:
            score += 20

        if 50 < r < 65:
            score += 20

        if volume > avg_vol:
            score += 20

        breakout = close >= high20*0.98

        if breakout:
            score += 20

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


if st.button("Run Arth Sutra Scanner"):

    data = scan()

    if data.empty:

        st.warning("No strong setups found today")

    else:

        st.dataframe(data)

        best = data.iloc[0]

        st.success(
            f"Top Opportunity: {best['Stock']} | Probability {best['AI Probability %']}% | Backtest WinRate {best['Backtest WinRate %']}%"
        )