import streamlit as st
import pandas as pd
import pandas_ta as ta
# Hum multiple sources try karenge
import yfinance as yf 
from pygooglenews import GoogleNews

st.set_page_config(page_title="Arth Sutra: Multi-Source", layout="wide")

# --- SOURCE 1: News from Google News (Best for Sentiment) ---
def get_market_sentiment(stock_name):
    gn = GoogleNews(lang='en', country='IN')
    search = gn.search(f'{stock_name} share price news')
    news_items = []
    for entry in search['entries'][:3]:
        news_items.append({"title": entry.title, "link": entry.link})
    return news_items

# --- SOURCE 2: Technicals from yfinance (Stable for OHLC data) ---
@st.cache_data(ttl=600)
def get_technical_data(ticker):
    # Sirf price data ke liye yf best hai
    df = yf.download(ticker, period="2y", progress=False)
    return df

# --- SOURCE 3: Fundamentals (Specialized logic) ---
def get_fundamental_kundali(ticker):
    t = yf.Ticker(ticker)
    info = t.info # Isme financial ratios acche milte hain
    return info

# --- THE AGGREGATOR (Sabko milane wala logic) ---
st.title("🛡️ Arth Sutra: Hybrid Intelligence Engine")

ticker = st.sidebar.text_input("Stock Ticker (e.g. RELIANCE.NS)", "RELIANCE.NS")

if st.sidebar.button("Nikalye Master Kundali"):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Source 2 se Price Data
        df = get_technical_data(ticker)
        if not df.empty:
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            st.subheader("📈 Chart Intelligence (Source: Market Data)")
            st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(200))
            
    with col2:
        # Source 3 se Fundamentals
        st.subheader("📑 Business Health")
        info = get_fundamental_kundali(ticker)
        st.write(f"**Market Cap:** ₹{info.get('marketCap', 0)//10**7} Cr")
        st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
        
    st.divider()
    
    # Source 1 se News
    st.subheader("🗞️ Latest Sentiment (Source: Google News)")
    news = get_market_sentiment(info.get('longName', ticker))
    for n in news:
        st.info(f"🔹 {n['title']} [Read]({n['link']})")