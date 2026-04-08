import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from pygooglenews import GoogleNews # For Sentiment Source

# --- Caching for Stability ---
@st.cache_data(ttl=3600)
def get_price_data(ticker):
    # Source A: yfinance for Technicals
    return yf.download(ticker, period="2y", interval="1d")

@st.cache_data(ttl=3600)
def get_fundamental_data(ticker):
    # Source B: yfinance Info for Fundamentals
    t = yf.Ticker(ticker)
    return t.info

def get_sentiment_news(stock_name):
    # Source C: Google News for Sentiments
    gn = GoogleNews(lang='en', country='IN')
    search = gn.search(f'{stock_name} share stock market')
    return search['entries'][:5]

# --- UI Setup ---
st.title("🛡️ Arth Sutra: Multi-Source Wealth Engine")

selected_stock = st.sidebar.text_input("Enter NSE Ticker", "TATAMOTORS.NS")

if st.sidebar.button("Nikalye Master Kundali"):
    try:
        # Technical Logic
        df = get_price_data(selected_stock)
        info = get_fundamental_data(selected_stock)
        
        st.header(f"📊 Analysis: {info.get('longName', selected_stock)}")
        
        # --- Multi-Source Dashboard ---
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Technical Source (44/200 SMA)")
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(200))
            
        with col2:
            st.subheader("📑 Fundamental Source")
            st.metric("PE Ratio", info.get('trailingPE', 'N/A'))
            st.metric("Debt/Equity", info.get('debtToEquity', 'N/A'))
            st.metric("Profit Growth", f"{info.get('earningsGrowth', 0)*100:.1f}%")

        st.divider()

        # --- News/Sentiment Source ---
        st.subheader("🗞️ Sentiment Source (Google News)")
        news_list = get_sentiment_news(info.get('longName', selected_stock))
        for n in news_list:
            st.info(f"**{n.title}** \n[Read More]({n.link})")

    except Exception as e:
        st.error(f"Error connecting to sources: {e}")