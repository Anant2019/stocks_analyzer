import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- UI Setup ---
st.set_page_config(page_title="Arth Sutra: Stock Kundali", layout="wide")
st.title("🔎 Arth Sutra: Stock Deep-Dive Terminal")

# Nifty 200 List (Sample)
nifty200 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "ITC.NS", "INFY.NS", "BHARTIARTL.NS"]

# --- Sidebar: Stock Selection ---
selected_stock = st.sidebar.selectbox("Kiski Kundali nikalni hai?", nifty200)

@st.cache_data(ttl=600) # 10 mins cache taaki Yahoo block na kare
def get_stock_kundali(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        # Fetch data safely
        hist = t.history(period="2y")
        info = t.info
        news = t.news
        return t, hist, info, news
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        return None, None, None, None

t_obj, df, info, news = get_stock_kundali(selected_stock)

if t_obj and not df.empty:
    # --- 1. Top Bar: Quick Stats ---
    st.header(f"📊 {info.get('longName', selected_stock)} ({selected_stock})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price", f"₹{round(df['Close'].iloc[-1], 2)}")
    c2.metric("PE Ratio", info.get('trailingPE', 'N/A'))
    c3.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 'N/A')}")
    c4.metric("Market Cap", f"₹{round(info.get('marketCap', 0)/10**11, 2)} L Cr")

    # --- 2. Technical Kundali ---
    st.subheader("📈 Technical Analysis (44/200 SMA)")
    df['SMA44'] = ta.sma(df['Close'], length=44)
    df['SMA200'] = ta.sma(df['Close'], length=200)
    
    # Custom Plotly Chart (Streamlit Line Chart for Speed)
    st.line_chart(df[['Close', 'SMA44', 'SMA200']])

    # --- 3. Fundamental & News ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📑 Business Fundamentals")
        f_data = {
            "Debt to Equity": info.get('debtToEquity', 'N/A'),
            "Return on Equity (ROE)": info.get('returnOnEquity', 'N/A'),
            "Profit Margin": info.get('profitMargins', 'N/A'),
            "Dividend Yield": info.get('dividendYield', 'N/A')
        }
        st.json(f_data)
        st.write(f"**Description:** {info.get('longBusinessSummary', 'No summary available.')[:500]}...")

    with col_right:
        st.subheader("🗞️ Latest News & Sentiments")
        if news:
            for item in news[:5]:
                st.info(f"📅 **{item['title']}**")
                st.caption(f"Source: {item['publisher']} | [Read Full Story]({item['link']})")
        else:
            st.warning("No recent news found for this stock.")

else:
    st.warning("Patience! Fetching data from Yahoo Finance...")