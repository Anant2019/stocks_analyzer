import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

# 1. Configuration & Tickers
st.set_page_config(page_title="Global 200 Monitor", layout="wide")

# Ensure this list has no empty strings or non-string objects
TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"] 

# 2. Optimized Data Fetching with Chunking
@st.cache_data(ttl=3600)
def fetch_all_data(ticker_list):
    clean_tickers = [str(t).strip().upper() for t in ticker_list if t and isinstance(t, str)]
    if not clean_tickers:
        return None

    all_dfs = []
    # Process in chunks of 50 to avoid Yahoo's "Large Request" block
    chunk_size = 50
    for i in range(0, len(clean_tickers), chunk_size):
        chunk = clean_tickers[i:i + chunk_size]
        try:
            # Note: Removed 'session' argument to let YF handle curl_cffi internally
            data = yf.download(
                tickers=chunk,
                period="1y",
                interval="1d",
                group_by='ticker',
                threads=True,
                progress=False
            )
            if not data.empty:
                all_dfs.append(data)
            time.sleep(1) # Small pause between chunks to stay under the radar
        except Exception as e:
            st.error(f"Error fetching chunk: {e}")
            continue
            
    if not all_dfs:
        return None
        
    return pd.concat(all_dfs, axis=1)

def analyze_stocks(all_data, ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            # Extract data from multi-index
            df = all_data[ticker].dropna()
            if df.empty or len(df) < 20: continue
            
            current_price = df['Close'].iloc[-1]
            ma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            
            confidence = 0
            if current_price > ma_200: confidence += 50
            if rsi < 40: confidence += 30
            
            results.append({
                "Ticker": ticker,
                "Price": round(current_price, 2),
                "Confidence": confidence
            })
        except:
            continue
    return results

# --- UI LOGIC ---
st.title("🚀 Global 200 Stock Monitor")

if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None

with st.spinner("Analyzing 200 stocks in chunks..."):
    all_raw_data = fetch_all_data(TICKERS)
    if all_raw_data is not None:
        analysis = analyze_stocks(all_raw_data, TICKERS)
        sorted_stocks = sorted(analysis, key=lambda x: x['Confidence'], reverse=True)
    else:
        st.error("Could not retrieve data. Please check your internet connection or ticker symbols.")
        sorted_stocks = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Market Overview")
    for stock in sorted_stocks[:25]:
        if st.button(f"{stock['Ticker']} | ₹{stock['Price']} ({stock['Confidence']}%)", key=f"btn_{stock['Ticker']}"):
            st.session_state.selected_stock = stock['Ticker']

with col2:
    if st.session_state.selected_stock:
        target = st.session_state.selected_stock
        st.header(f"📊 Deep Dive: {target}")
        
        try:
            # Individual ticker object for deep dive
            t_obj = yf.Ticker(target)
            # We use fast_info instead of info where possible to avoid rate limits
            f_info = t_obj.fast_info 
            
            st.metric("Current Price", f"₹{round(f_info['lastPrice'], 2)}")
            
            with st.expander("Strategic Details"):
                # Only use .info as a last resort for things like 'sector'
                full_info = t_obj.info
                st.write(f"**Sector:** {full_info.get('sector', 'N/A')}")
                st.write(f"**Business Summary:** {full_info.get('longBusinessSummary', 'N/A')[:500]}...")
        except Exception:
            st.warning("Deep dive details are currently limited by Yahoo Finance. Core price data is still active.")
    else:
        st.info("Select a stock to see details.")