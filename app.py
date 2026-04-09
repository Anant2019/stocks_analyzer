import streamlit as st
import yfinance as yf
import pandas as pd
import time

# List of 200 tickers (Truncated for brevity)
TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", ...] 

@st.cache_data(ttl=3600)  # Refresh every hour
def fetch_all_data(ticker_list):
    # Download 2 years of daily data for all 200 stocks in one go
    # group_by='ticker' makes it easy to iterate later
    data = yf.download(ticker_list, period="2y", interval="1d", group_by='ticker', threads=True)
    return data

def analyze_stocks(data, tickers):
    results = []
    for ticker in tickers:
        try:
            # Extract ticker-specific dataframe from the multi-index data
            df = data[ticker].dropna()
            if df.empty: continue
            
            # Simplified Logic: RSI / Moving Average (Calculated once per ticker)
            current_price = df['Close'].iloc[-1]
            ma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
            
            # Example Confidence Logic
            confidence = 0
            reasons = []
            if current_price > ma_200:
                confidence += 40
                reasons.append("Price above 200 EMA (Bullish)")
            
            results.append({
                'Ticker': ticker,
                'Price': round(current_price, 2),
                'Confidence': confidence,
                'Reasons': reasons
            })
        except Exception:
            continue
    return results

# --- Main App ---
st.title("🚀 Global 200 Stock Monitor")

with st.spinner("Analyzing 200 Stocks..."):
    all_raw_data = fetch_all_data(TICKERS)
    analysis_results = analyze_stocks(all_raw_data, TICKERS)

# Sort by confidence
sorted_results = sorted(analysis_results, key=lambda x: x['Confidence'], reverse=True)

# UI Rendering (Limit to Top 50 for performance, then click for deep dive)
for stock in sorted_results[:50]:
    with st.container():
        st.markdown(f"""
            <div style="padding:10px; border-radius:5px; border:1px solid #333; margin-bottom:10px">
                <h3>{stock['Ticker']} - ₹{stock['Price']}</h3>
                <h4 style="color:#58a6ff;">Confidence: {stock['Confidence']}%</h4>
                <p><b>Analysis:</b> {' | '.join(stock['Reasons'])}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Strategic Blueprint: {stock['Ticker']}", key=f"btn_{stock['Ticker']}"):
            st.session_state['selected_stock'] = stock['Ticker']

# --- Deep Analysis Section ---
if st.session_state.get('selected_stock'):
    st.divider()
    target = st.session_state['selected_stock']
    
    # ONLY call .info for the ONE stock selected to keep it fast
    t_obj = yf.Ticker(target)
    info = t_obj.info
    st.subheader(f"📑 Strategic Financial Blueprint: {target}")
    # ... rest of your deep analysis code ...