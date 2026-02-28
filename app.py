import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="NSE 200 Bullish Scanner", layout="wide")

# --- Function to get Nifty 200 Tickers from NSE ---
@st.cache_data # Isse baar-baar download nahi hoga, speed badhegi
def get_nifty_200_tickers():
    try:
        # NSE Official Nifty 200 CSV Link
        url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
        df_nse = pd.read_csv(url)
        # Yahoo Finance ke liye .NS lagana zaroori hai
        tickers = [symbol + ".NS" for symbol in df_nse['Symbol']]
        return tickers
    except Exception as e:
        st.error(f"NSE list fetch nahi ho payi: {e}")
        return []

st.title("🎯 NSE 200 Pro Scanner (44 & 200 SMA)")
st.write(f"Strategy: Price > SMA 44 > SMA 200 | Filter: Bullish Green Candle")

# --- Scanning Logic ---
def scan_nifty_200():
    tickers = get_nifty_200_tickers()
    if not tickers: return pd.DataFrame()

    found_stocks = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers):
        try:
            status_text.text(f"Scanning: {ticker} ({i+1}/{len(tickers)})")
            
            # 1 Year data for SMA calculation
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            
            if len(df) < 200: continue
            
            # Calculating Averages
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            last = df.iloc[-1]
            price = last['Close']
            open_p = last['Open']
            sma44 = last['SMA_44']
            sma200 = last['SMA_200']

            # --- Logic Check ---
            # 1. Price is above SMA 44
            # 2. SMA 44 is above SMA 200 (Uptrend)
            # 3. Green Candle (Close > Open)
            if price > sma44 and sma44 > sma200 and price > open_p:
                found_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Current Price": round(float(price), 2),
                    "SMA 44": round(float(sma44), 2),
                    "SMA 200": round(float(sma200), 2),
                    "Gain %": round(((price - open_p)/open_p)*100, 2)
                })
        except:
            continue
        
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.text("Scan Complete!")
    return pd.DataFrame(found_stocks)

# --- UI Controls ---
if st.button('🔍 Start NSE 200 Scan'):
    results = scan_nifty_200()
    
    if not results.empty:
        st.success(f"Found {len(results)} Bullish Stocks!")
        st.dataframe(results.sort_values(by="Gain %", ascending=False), use_container_width=True)
    else:
        st.warning("No stocks matched the 44/200 SMA criteria today.")

st.info("💡 Raat ko 8 baje scan karne par aapko pure din ka final trend dikhega.")
