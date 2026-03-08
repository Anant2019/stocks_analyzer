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

        if len(df) < 50:
            continue

        df["EMA20"] = df["Close"].ewm(span=20).mean()
        df["EMA50"] = df["Close"].ewm(span=50).mean()
        df["RSI"] = calculate_rsi(df["Close"])

        latest = df.iloc[-1]

        score = 0

        if latest["Close"] > latest["EMA20"]:
            score += 25

        if latest["EMA20"] > latest["EMA50"]:
            score += 25

        if 50 < latest["RSI"] < 65:
            score += 25

        if latest["Volume"] > df["Volume"].mean():
            score += 25

        results.append({
            "Stock": stock,
            "Price": round(latest["Close"],2),
            "RSI": round(latest["RSI"],2),
            "Probability %": score
        })

    df = pd.DataFrame(results)
    df = df.sort_values(by="Probability %", ascending=False)

    return df


st.title("📈 Swing Trading Stock Scanner")

if st.button("Scan Stocks"):

    data = scan_stocks()

    st.dataframe(data)

    best = data.iloc[0]

    st.success(f"Best Stock: {best['Stock']} with {best['Probability %']}% probability")