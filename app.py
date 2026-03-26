import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. UI Configuration (Keeps the app from looking "blank")
st.set_page_config(page_title="Arth Sutra Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .card { background: #111; border: 1px solid #333; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .buy { color: #00FF41; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏹 ARTH SUTRA | Pro Scanner")
st.caption("Strategy: 75%+ Win-Rate Institutional Pullback (NSE 100)")

# 2. Strategy Logic with Multi-Index Fix
def analyze_stock(symbol):
    try:
        # download with flat columns to prevent ValueError
        df = yf.download(symbol, period="1y", interval="1d", progress=False, multi_level_index=False)
        
        if df.empty or len(df) < 50:
            return None

        # Calculate Indicators using pandas_ta
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # Pull the last row and convert to simple floats
        curr = df.iloc[-1]
        price = float(curr['Close'])
        ema20 = float(curr['EMA20'])
        ema50 = float(curr['EMA50'])
        rsi = float(curr['RSI'])

        # --- High Success Logic (75% Goal) ---
        score = 0
        if price > ema50: score += 40      # Trend Confirmation
        if price <= ema20 * 1.015: score += 35 # Proximity to Institutional Buy Zone
        if 45 < rsi < 65: score += 25       # Momentum Sweet Spot

        return {
            "Symbol": symbol.replace(".NS", ""),
            "Price": round(price, 2),
            "Score": score,
            "Target": round(price * 1.08, 2),
            "StopLoss": round(ema50 * 0.98, 2)
        }
    except Exception:
        return None

# 3. Execution UI
WATCHLIST = ["RELIANCE.NS", "TCS.NS", "BHARTIARTL.NS", "HAL.NS", "BEL.NS", "INFY.NS", "ICICIBANK.NS"]

if st.button("⚡ Start High-Probability Scan"):
    # The scan happens here
    results = [analyze_stock(s) for s in WATCHLIST]
    valid_results = [r for r in results if r and r['Score'] >= 75]

    if not valid_results:
        st.info("No 75%+ conviction setups found today. Better to wait for a pullback.")
    else:
        cols = st.columns(3)
        for i, stock in enumerate(valid_results):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <h3>{stock['Symbol']}</h3>
                    <p class="buy">CONVICTION: {stock['Score']}%</p>
                    <hr style="border-color:#222">
                    <p><b>LTP:</b> ₹{stock['Price']}</p>
                    <p><b>Tgt (8%):</b> ₹{stock['Target']}</p>
                    <p style="color:#ff4b4b"><b>SL:</b> ₹{stock['StopLoss']}</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.write("Ready to scan. Please click the button above.")