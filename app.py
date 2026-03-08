import streamlit as st
import yfinance as yf
import pandas as pd

stocks = [
"RELIANCE.NS",
"TCS.NS",
"INFY.NS",
"HDFCBANK.NS",
"ICICIBANK.NS",
"SBIN.NS",
"LT.NS"
]

def calculate_rsi(data, period=14):

    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def scan_stocks():

    results = []

    for stock in stocks:

        df = yf.download(stock, period="6mo", interval="1d", progress=False)

        if df.empty or len(df) < 50:
            continue

        df["EMA20"] = df["Close"].ewm(span=20).mean()
        df["EMA50"] = df["Close"].ewm(span=50).mean()
        df["RSI"] = calculate_rsi(df["Close"])

        latest = df.iloc[-1]

        close = float(latest["Close"])
        ema20 = float(latest["EMA20"])
        ema50 = float(latest["EMA50"])
        rsi = float(latest["RSI"])
        volume = float(latest["Volume"])
        avg_volume = float(df["Volume"].mean())

        score = 0

        if close > ema20:
            score += 25

        if ema20 > ema50:
            score += 25

        if 50 < rsi < 65:
            score += 25

        if volume > avg_volume:
            score += 25

        results.append({
            "Stock": stock,
            "Price": round(close,2),
            "RSI": round(rsi,2),
            "Probability %": score
        })

    df_results = pd.DataFrame(results)

    if not df_results.empty:
        df_results = df_results.sort_values(by="Probability %", ascending=False)

    return df_results


st.title("📈 Swing Trading Stock Scanner")

if st.button("Scan Stocks"):

    data = scan_stocks()

    if data.empty:
        st.warning("No strong setups found today.")
    else:
        st.dataframe(data)

        best = data.iloc[0]

        st.success(
            f"Best Stock Today: {best['Stock']} with {best['Probability %']}% probability"
        )