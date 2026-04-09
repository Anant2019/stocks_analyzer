import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. Configuration & Ticker List
st.set_page_config(page_title="Global 200 Monitor", layout="wide")

# Expand this list to your full 200 tickers
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "INFY.NS", "ITC.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS"
    # ... Add all other tickers here
]

# 2. Optimized Data Fetching
@st.cache_data(ttl=3600)
def fetch_all_data(ticker_list):
    # Clean list: ensure strings, remove whitespace, remove empty values
    clean_tickers = [str(t).strip().upper() for t in ticker_list if t and isinstance(t, str)]
    
    if not clean_tickers:
        return None

    # Batch download (much faster than a loop)
    data = yf.download(
        tickers=clean_tickers,
        period="2y",
        interval="1d",
        group_by='ticker',
        threads=True,
        progress=False
    )
    return data

# 3. Batch Analysis Logic
def analyze_stocks(all_data, ticker_list):
    results = []
    clean_tickers = [str(t).strip().upper() for t in ticker_list if t and isinstance(t, str)]
    
    for ticker in clean_tickers:
        try:
            # Handle yfinance multi-index structure
            if len(clean_tickers) > 1:
                df = all_data[ticker].dropna()
            else:
                df = all_data.dropna()

            if df.empty or len(df) < 200:
                continue

            # Technical Indicators
            current_price = df['Close'].iloc[-1]
            ema_200 = ta.ema(df['Close'], length=200).iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]

            confidence = 0
            reasons = []

            if current_price > ema_200:
                confidence += 40
                reasons.append("Above 200 EMA")
            if rsi < 30:
                confidence += 30
                reasons.append("Oversold (RSI)")
            elif rsi > 70:
                confidence -= 20
                reasons.append("Overbought (RSI)")

            results.append({
                "Ticker": ticker,
                "Price": round(current_price, 2),
                "Confidence": max(0, confidence),
                "Reasons": reasons
            })
        except Exception:
            continue
    return results

# 4. Main UI
st.title("🚀 Strategic Stock Monitor (200+)")

if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None

with st.spinner(f"Analyzing {len(TICKERS)} stocks..."):
    raw_data = fetch_all_data(TICKERS)
    
    if raw_data is not None:
        analysis = analyze_stocks(raw_data, TICKERS)
        # Sort by highest confidence
        sorted_stocks = sorted(analysis, key=lambda x: x['Confidence'], reverse=True)
    else:
        st.error("Failed to fetch data. Check your ticker list.")
        sorted_stocks = []

# Layout: Sidebar for list, Main for details
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("High Confidence Picks")
    for stock in sorted_stocks[:20]: # Show top 20 cards
        with st.container():
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; border:1px solid #444; margin-bottom:10px; background-color:#1e1e1e">
                <h3 style="margin:0; color:white;">{stock['Ticker']}</h3>
                <p style="margin:0; color:#888;">Price: ₹{stock['Price']}</p>
                <h4 style="margin:5px 0; color:#58a6ff;">Confidence: {stock['Confidence']}%</h4>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Analyze {stock['Ticker']}", key=f"btn_{stock['Ticker']}"):
                st.session_state.selected_stock = stock['Ticker']

with col2:
    if st.session_state.selected_stock:
        target = st.session_state.selected_stock
        st.header(f"📊 Deep Dive: {target}")
        
        # Only call .info here (the slow part) for the SINGLE selected stock
        ticker_obj = yf.Ticker(target)
        with st.expander("View Financial Stats", expanded=True):
            info = ticker_obj.info
            st.json({
                "Sector": info.get('sector'),
                "PE Ratio": info.get('trailingPE'),
                "Dividend Yield": info.get('dividendYield'),
                "Market Cap": info.get('marketCap')
            })
    else:
        st.info("Select a stock from the left to see the Strategic Blueprint.")