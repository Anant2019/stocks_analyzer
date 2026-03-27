import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. Professional Theme Mapping
st.set_page_config(page_title="Arth Sutra Ultra", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: #e0e0e0; }
    .card { 
        background: linear-gradient(145deg, #111, #0a0a0a); 
        border: 1px solid #333; 
        border-radius: 15px; 
        padding: 24px; 
        margin-bottom: 20px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.5);
    }
    .buy { color: #00FF41; font-family: 'Courier New'; font-size: 1.2rem; }
    .stat { color: #888; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏹 ARTH SUTRA | Ultra Scanner")
st.caption("Advanced Multi-Factor Institutional Swing Analysis")

def analyze_stock(symbol):
    try:
        # Use Ticker object for more reliable data fetching
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 50:
            return None

        # --- Indicator Engine ---
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ADX'] = ta.adx(df['High'], df['Low'], df['Close'])['ADX_14']
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['Vol_Avg'] = ta.sma(df['Volume'], length=20)
        
        curr = df.iloc[-1]
        
        # --- Scoring Logic (Max 100) ---
        score = 0
        if curr['Close'] > curr['EMA50']: score += 30 # Trend
        if abs(curr['Close'] - curr['EMA20']) / curr['EMA20'] < 0.02: score += 30 # Pullback
        if 45 < curr['RSI'] < 65: score += 20 # Momentum Sweet Spot
        if curr['ADX'] > 20: score += 10 # Trend Strength
        if curr['Volume'] > curr['Vol_Avg'] * 0.8: score += 10 # Volume Health

        # Exit Strategy (ATR Based)
        # Target: 2.5x ATR | SL: 1.5x ATR
        target = curr['Close'] + (curr['ATR'] * 2.5)
        sl = curr['Close'] - (curr['ATR'] * 1.5)

        return {
            "Symbol": symbol.replace(".NS", ""),
            "Price": round(curr['Close'], 2),
            "Score": score,
            "RSI": round(curr['RSI'], 1),
            "ADX": round(curr['ADX'], 1),
            "Target": round(target, 2),
            "SL": round(sl, 2)
        }
    except:
        return None

# Expanded Blue-Chip Watchlist (NSE)
WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "BHARTIARTL.NS", "HAL.NS", "BEL.NS", 
    "INFY.NS", "ICICIBANK.NS", "HDFCBANK.NS", "TATASTEEL.NS", "ADANIENT.NS",
    "SBIN.NS", "AXISBANK.NS", "LT.NS", "M&M.NS", "TITAN.NS", "SUNPHARMA.NS",
    "POWERGRID.NS", "NTPC.NS", "BAJFINANCE.NS", "MARUTI.NS", "COALINDIA.NS"
]

if st.button("⚡ EXECUTE DEEP SCAN"):
    with st.spinner("Analyzing Market Structure..."):
        results = [analyze_stock(s) for s in WATCHLIST]
        # Allow setups with 70%+ score for more opportunities without sacrificing quality
        valid_results = [r for r in results if r and r['Score'] >= 70]

    if not valid_results:
        st.error("MARKET STATUS: Overextended. No 'High-Value' pullbacks detected in the Top 20.")
        st.info("Strategy Tip: Institutional money is currently waiting. Avoid FOMO entries.")
    else:
        valid_results = sorted(valid_results, key=lambda x: x['Score'], reverse=True)
        cols = st.columns(3)
        for i, stock in enumerate(valid_results):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <h2 style="margin:0;">{stock['Symbol']}</h2>
                    <p class="buy">CONVICTION: {stock['Score']}%</p>
                    <hr style="border-color:#222">
                    <p class="stat">Price: <span style="color:white">₹{stock['Price']}</span></p>
                    <p class="stat">RSI: <span style="color:white">{stock['RSI']}</span> | ADX: <span style="color:white">{stock['ADX']}</span></p>
                    <div style="background:#000; padding:10px; border-radius:8px; margin-top:10px;">
                        <p style="color:#00FF41; margin:0;"><b>TGT: ₹{stock['Target']}</b></p>
                        <p style="color:#FF4B4B; margin:0;"><b>SL:  ₹{stock['SL']}</b></p>
                    </div>
                </div>
                """, unsafe_allow_html=True)