import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- Architecture: Using Streamlit's native cache instead of requests_cache ---
@st.cache_data(ttl=600) # 10 mins tak data memory me rahega
def fetch_stock_data(ticker_symbol):
    try:
        # Session hatane se curl_cffi internally handle ho jayega
        t = yf.Ticker(ticker_symbol)
        df = t.history(period="2y")
        if df.empty or len(df) < 200:
            return None, None, "Insufficient data (Needs 200+ days)"
        
        info = t.info
        news = t.news
        return df, info, news
    except Exception as e:
        return None, None, str(e)

st.set_page_config(page_title="Arth Sutra: Fixed Engine", layout="wide")

# UI Logic
st.title("🚀 Arth Sutra: Wealth Engine (Fixed)")

# Sample List
nifty200 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "ITC.NS"]
selected_stock = st.sidebar.selectbox("Select Stock", nifty200)

if st.sidebar.button("Analyze Now"):
    with st.spinner(f"Fetching {selected_stock}..."):
        df, info, news = fetch_stock_data(selected_stock)
        
        if df is not None:
            # --- Technical Logic ---
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            
            curr = df.iloc[-1]
            
            # Confidence Scoring
            score = 0
            if curr['Close'] > curr['SMA200']: score += 50
            if abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.03: score += 50
            
            # --- Display ---
            st.metric("Confidence Score", f"{score}%")
            st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(250))
            
            st.subheader("Fundamental Insights")
            st.write(f"**Business:** {info.get('longName')}")
            st.write(f"**PE Ratio:** {info.get('trailingPE')}")
            
            st.subheader("Latest News")
            for n in news[:3]:
                st.info(f"📰 {n['title']}")
        else:
            st.error(f"Error: {news}") # 'news' here contains the error message