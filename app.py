from flask import Flask
import yfinance as yf
import pandas as pd

app = Flask(__name__)

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
    loss = -1 * delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def scan():

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

        probability = score

        results.append({
            "stock": stock,
            "price": round(latest["Close"],2),
            "rsi": round(latest["RSI"],2),
            "probability": probability
        })

    results = sorted(results, key=lambda x: x["probability"], reverse=True)

    return results


@app.route("/")
def home():

    data = scan()

    html = """
    <h1 style='text-align:center'>Swing Trading Stock Scanner</h1>
    <table border=1 style='margin:auto;border-collapse:collapse;font-size:18px'>
    <tr>
    <th>Stock</th>
    <th>Price</th>
    <th>RSI</th>
    <th>Success Probability %</th>
    </tr>
    """

    for d in data:

        color = "green" if d["probability"] >= 75 else "orange"

        html += f"""
        <tr>
        <td>{d['stock']}</td>
        <td>{d['price']}</td>
        <td>{d['rsi']}</td>
        <td style='color:{color}'>{d['probability']}%</td>
        </tr>
        """

    html += "</table>"

    return html


app.run()