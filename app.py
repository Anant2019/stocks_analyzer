import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- Core Engine: The Triple-Check Logic ---
def get_wealth_engine_analysis(symbol):
    t = yf.Ticker(symbol)
    df = t.history(period="1y")
    info = t.info
    
    if df.empty or len(df) < 200: return None

    # 1. Technical Indicators
    df['SMA44'] = ta.sma(df['Close'], length=44)
    df['SMA200'] = ta.sma(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['Volume_Avg'] = ta.sma(df['Volume'], length=20)
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # --- ACCURACY FILTERS ---
    # Filter A: Price must be above 200 SMA (Long term Bullish)
    is_bullish = curr['Close'] > curr['SMA200']
    
    # Filter B: Price near 44 SMA (The Entry Zone)
    near_44 = abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.02
    
    # Filter C: Volume Surge (The "Truth" Filter)
    volume_surge = curr['Volume'] > (df['Volume_Avg'].iloc[-1] * 1.5)
    
    # Filter D: RSI Reversal (Strength check)
    rsi_ok = 40 < curr['RSI'] < 65

    # Confidence Calculation (0 to 100)
    confidence = 0
    if is_bullish: confidence += 30
    if near_44: confidence += 25
    if volume_surge: confidence += 25
    if rsi_ok: confidence += 20

    # Stop Loss & Target (Based on Volatility)
    stop_loss = curr['Close'] - (2 * curr['ATR'])
    target = curr['Close'] + (4 * curr['ATR']) # 1:2 Risk-Reward

    return {
        "ticker": symbol,
        "price": round(curr['Close'], 2),
        "confidence": confidence,
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "volume_status": "HIGH" if volume_surge else "NORMAL",
        "news": t.news[:3]
    }

# --- Streamlit Dashboard ---
st.title("🛡️ Arth Sutra: Wealth Creation Engine")
st.markdown("Helping common people build wealth through data-driven accuracy.")

# Simplified Nifty 200 List (Aap yahan CSV load kar sakte ho)
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "ITC.NS", "SBIN.NS"]

high_conf_picks = []

for s in tickers:
    data = get_wealth_engine_analysis(s)
    if data and data['confidence'] >= 70:
        high_conf_picks.append(data)

# Display Analysis
if high_conf_picks:
    for pick in high_conf_picks:
        with st.expander(f"📌 {pick['ticker']} - Confidence: {pick['confidence']}%"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"₹{pick['price']}")
            col2.metric("Stop Loss (SL)", f"₹{pick['stop_loss']}", delta_color="inverse")
            col3.metric("Target", f"₹{pick['target']}")
            
            st.write(f"**Volume Status:** {pick['volume_status']}")
            st.subheader("Latest News Insights")
            for n in pick['news']:
                st.write(f"- {n['title']} ([Link]({n['link']}))")
else:
    st.info("No high-accuracy signals found today. Cash is also a position!")