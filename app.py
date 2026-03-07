import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

def get_nifty500_tickers():
    """Fetch the latest Nifty 500 list from NSE"""
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        # Convert symbols to Yahoo Finance format (e.g., RELIANCE -> RELIANCE.NS)
        return [f"{s}.NS" for s in df['Symbol'].tolist()]
    except Exception as e:
        st.error(f"Could not fetch Nifty 500 list: {e}")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"] # Fallback

def scan_stocks(tickers):
    bullish_stocks = []
    progress_bar = st.progress(0)
    total = len(tickers)
    
    for i, ticker in enumerate(tickers):
        try:
            # Update progress bar every 10 stocks
            if i % 10 == 0:
                progress_bar.progress((i + 1) / total)
            
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if len(data) < 200: continue
            
            # Use .copy() to avoid SettingWithCopy warnings
            df = data.copy()
            df['SMA44'] = df['Close'].rolling(window=44).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Numeric conversion to avoid Pandas label errors
            price_close = float(latest['Close'])
            price_open = float(latest['Open'])
            price_low = float(latest['Low'])
            sma44_now = float(latest['SMA44'])
            sma44_prev = float(prev['SMA44'])
            sma200_now = float(latest['SMA200'])
            sma200_prev = float(prev['SMA200'])
            
            # YOUR CRITERIA
            is_sma44_rising = sma44_now > sma44_prev
            is_sma200_rising = sma200_now > sma200_prev
            is_green_candle = price_close > price_open
            is_at_support = price_low <= (sma44_now * 1.01) # Near 44 SMA
            
            if is_sma44_rising and is_sma200_rising and is_green_candle and is_at_support:
                bullish_stocks.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Price": round(price_close, 2),
                    "SMA44": round(sma44_now, 2),
                    "SMA200": round(sma200_now, 2)
                })
        except:
            continue
            
    progress_bar.empty()
    return pd.DataFrame(bullish_stocks)

# --- Streamlit UI ---
st.title("🔥 Nifty 500 Bullish Scanner")
st.write("Criteria: 44 SMA & 200 SMA Rising + Green Candle Support")

if st.button('🚀 Start Full Market Scan'):
    with st.spinner('Fetching Nifty 500 and scanning...'):
        watchlist = get_nifty500_tickers()
        results = scan_stocks(watchlist)
        
        if not results.empty:
            st.success(f"Found {len(results)} stocks!")
            st.dataframe(results, use_container_width=True)
            # Option to download the results
            csv = results.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "bullish_stocks.csv", "text/csv")
        else:
            st.info("No stocks matched the criteria today.")
