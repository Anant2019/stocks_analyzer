import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Arth Sutra: Final Fix", layout="wide")

# --- Step 1: Logic ko split karein ---
# Hum sirf DataFrame return karenge jo serializable hai
@st.cache_data(ttl=3600)
def get_clean_price_data(ticker):
    df = yf.download(ticker, period="2y", progress=False)
    return df

@st.cache_data(ttl=3600)
def get_clean_info(ticker):
    t = yf.Ticker(ticker)
    # Poora object nahi, sirf zaruri info dictionary return karein
    return t.info

# --- Step 2: Main UI ---
st.title("🛡️ Arth Sutra: Stability Engine")

ticker = st.sidebar.text_input("Enter NSE Ticker", "RELIANCE.NS")

if st.sidebar.button("Nikalye Kundali"):
    with st.spinner("Analyzing..."):
        try:
            # Data Fetching
            df = get_clean_price_data(ticker)
            info = get_clean_info(ticker)
            
            if not df.empty:
                # 1. Technical Analysis logic (DataFrame is safe here)
                df['SMA44'] = ta.sma(df['Close'], length=44)
                df['SMA200'] = ta.sma(df['Close'], length=200)
                
                # --- Row 1: The Verdict ---
                st.header(f"📊 {info.get('longName', ticker)}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("Technical View")
                    st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(200))
                
                with col2:
                    st.subheader("Fundamental Health")
                    st.metric("PE Ratio", info.get('trailingPE', 'N/A'))
                    st.metric("Debt/Equity", info.get('debtToEquity', 'N/A'))
                    st.write(f"**Business:** {info.get('longBusinessSummary')[:300]}...")
            
        except Exception as e:
            st.error(f"Logic Error: {e}")