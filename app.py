import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
import io

st.set_page_config(page_title="NSE 200 Scanner", layout="wide")

# --- Function to get Nifty 200 Tickers with Headers ---
@st.cache_data
def get_nifty_200_tickers():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
        # Chrome browser ka 'mask' lagane ke liye headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df_nse = pd.read_csv(io.StringIO(response.text))
            tickers = [symbol + ".NS" for symbol in df_nse['Symbol']]
            return tickers
        else:
            st.error(f"NSE block kar raha hai. Status Code: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

st.title("🎯 NSE 200 Pro Scanner (44 & 200 SMA)")
st.write(f"Scanning for: Price > SMA 44 > SMA 200 | Green Candle")

# --- Scanning Logic ---
def scan_nifty_200():
    tickers = get_nifty_200_tickers()
    if not tickers: 
        st.warning("Tickers list empty hai!")
        return pd.DataFrame()

    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Sirf scanning limit (Taaki fast ho, aap ise badha sakte hain)
    for i, ticker in enumerate(tickers):
        try:
            status_text.text(f"Checking {i+1}/{len(tickers)}: {ticker}")
            
            # Data fetch (1 year for SMA 200)
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            
            if len(df) < 200: continue
            
            # SMA Calculation
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last = df.iloc[-1]
            price = last['Close']
            open_p = last['Open']
            sma44 = last['SMA_44']
            sma200 = last['SMA_200']

            # Strategy Check
            if price > sma44 and sma44 > sma200 and price > open_p:
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Price": round(float(price), 2),
                    "SMA 44": round(float(sma44), 2),
                    "SMA 200": round(float(sma200), 2),
                    "Change %": round(((price - open_p)/open_p)*100, 2)
                })
        except:
            continue
        
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.text("Scan Complete!")
    return pd.DataFrame(found_stocks)

if st.button('🔍 Start NSE 200 Scan'):
    results = scan_nifty_200()
    if not results.empty:
        st.success(f"Dhun liya! {len(results)} stocks bullish hain.")
        st.dataframe(results.sort_values(by="Change %", ascending=False), use_container_width=True)
    else:
        st.warning("Criteria match nahi hua.")
