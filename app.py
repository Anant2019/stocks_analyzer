import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# 1. UI Configuration
st.set_page_config(page_title="Arth Sutra Pro | Institutional Scanner", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    .card { 
        background: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 10px; 
        padding: 1.5rem; 
        margin-bottom: 1rem;
        transition: transform 0.3s;
    }
    .card:hover { border-color: #58a6ff; transform: translateY(-5px); }
    .buy { color: #3fb950; font-size: 1.2rem; font-weight: bold; }
    .metric { font-size: 0.9rem; color: #8b949e; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏹 ARTH SUTRA | Institutional Pullback Engine")
st.caption("Swing Strategy: Mean Reversion + Volume Confirmation (VSA)")

# 2. Advanced Analysis Logic
def analyze_stock(symbol):
    try:
        # Fetching data - Ticker.history is often more stable for loops than yf.download
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 50:
            return None

        # --- Indicator Engine ---
        # Moving Averages for Trend
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        # RSI for Overbought/Oversold
        df['RSI'] = ta.rsi(df['Close'], length=14)
        # ATR for Volatility-based Stop Loss
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        # Volume Average
        df['Vol_Avg'] = ta.sma(df['Volume'], length=20)
        
        curr = df.iloc[-1]
        
        # --- High Conviction Scoring (Total 100) ---
        score = 0
        reasons = []

        # 1. Major Trend (30 pts): Is the stock structurally healthy?
        if curr['Close'] > curr['EMA50']:
            score += 30
            reasons.append("Structural Uptrend")

        # 2. The Pullback Zone (30 pts): Is it near the 20 EMA "Value Area"?
        # Within 2% of EMA20
        dist_to_ema20 = abs(curr['Close'] - curr['EMA20']) / curr['EMA20']
        if dist_to_ema20 <= 0.025: 
            score += 30
            reasons.append("Institutional Buy Zone")

        # 3. Momentum Reset (20 pts): Avoid chasing overextended stocks
        if 40 <= curr['RSI'] <= 60:
            score += 20
            reasons.append("RSI Reset")

        # 4. Volume Confirmation (20 pts): Is there smart money support?
        if curr['Volume'] > curr['Vol_Avg'] * 0.9:
            score += 20
            reasons.append("Volume Support")

        # --- Dynamic Risk Management ---
        # Target = 3x ATR (Volatility Adjusted)
        # Stop Loss = 1.5x ATR below entry
        atr_val = curr['ATR']
        target = curr['Close'] + (atr_val * 3)
        stop_loss = curr['Close'] - (atr_val * 1.5)

        return {
            "Symbol": symbol.replace(".NS", ""),
            "Price": round(curr['Close'], 2),
            "Score": score,
            "RSI": round(curr['RSI'], 1),
            "Target": round(target, 2),
            "SL": round(stop_loss, 2),
            "Reasons": reasons
        }
    except Exception as e:
        return None

# 3. Diversified Watchlist
WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "BHARTIARTL.NS", "HAL.NS", "BEL.NS", 
    "INFY.NS", "ICICIBANK.NS", "HDFCBANK.NS", "TATASTEEL.NS", "ADANIENT.NS",
    "SBIN.NS", "AXISBANK.NS", "LT.NS", "M&M.NS", "TITAN.NS"
]

# 4. Dashboard UI
if st.button("⚡ EXECUTE PRO SCAN"):
    with st.spinner("Analyzing Institutional Order Blocks..."):
        results = [analyze_stock(s) for s in WATCHLIST]
        # Filtering for high conviction (Score >= 70)
        valid_results = [r for r in results if r and r['Score'] >= 70]

    if not valid_results:
        st.warning("No high-probability setups found. Market may be overextended—patience is a virtue.")
    else:
        # Sort by highest score
        valid_results = sorted(valid_results, key=lambda x: x['Score'], reverse=True)
        
        cols = st.columns(3)
        for i, stock in enumerate(valid_results):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 1.5rem; font-weight: bold;">{stock['Symbol']}</span>
                        <span class="buy">{stock['Score']}%</span>
                    </div>
                    <hr style="border-color:#333">
                    <p class="metric">Price: <b style="color:white">₹{stock['Price']}</b> | RSI: <b style="color:white">{stock['RSI']}</b></p>
                    <div style="background:#050505; padding: 12px; border-radius: 5px; margin: 10px 0; border: 1px dashed #444;">
                        <p style="color:#3fb950; margin:0;"><b>🎯 TGT: ₹{stock['Target']}</b></p>
                        <p style="color:#f85149; margin:0;"><b>🛡️ SL:  ₹{stock['SL']}</b></p>
                    </div>
                    <p style="font-size: 0.8rem; color: #8b949e;">{" • ".join(stock['Reasons'])}</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("Ready to scan. This engine looks for 'Deep Value' pullbacks in Blue-chip stocks.")