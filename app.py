import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
try:
    from pygooglenews import GoogleNews
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False

st.set_page_config(page_title="Arth Sutra: Hybrid Engine", layout="wide")

# --- Source A: Technical & Fundamental (yfinance) ---
@st.cache_data(ttl=3600)
def get_market_data(ticker):
    t = yf.Ticker(ticker)
    df = t.history(period="2y")
    return t, df

# --- Source B: Sentiment (Google News) ---
def get_sentiment(stock_name):
    if not NEWS_AVAILABLE:
        return []
    gn = GoogleNews(lang='en', country='IN')
    search = gn.search(f'{stock_name} share price')
    return search['entries'][:5]

st.title("🛡️ Arth Sutra: Multi-Source Engine")

selected_stock = st.sidebar.text_input("Enter NSE Ticker", "RELIANCE.NS")

if st.sidebar.button("Nikalye Master Kundali"):
    t_obj, df = get_market_data(selected_stock)
    
    if not df.empty:
        # 1. Technical Analysis
        df['SMA44'] = ta.sma(df['Close'], length=44)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Technical Chart")
            st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(200))
            
        with col2:
            st.subheader("📑 Financial Health")
            info = t_obj.info
            st.metric("PE Ratio", info.get('trailingPE', 'N/A'))
            st.metric("Debt/Equity", info.get('debtToEquity', 'N/A'))
            
        st.divider()
        
        # 2. News/Sentiment Section
        st.subheader("🗞️ News Sentiment (Multi-Source)")
        if NEWS_AVAILABLE:
            news = get_sentiment(info.get('longName', selected_stock))
            for n in news:
                st.info(f"**{n.title}** \n [Link]({n.link})")
        else:
            st.warning("News Module (pygooglenews) not installed. Running Technicals only.")