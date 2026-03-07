import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="44-200 SMA Bullish Scanner", layout="wide")
st.title("📈 Swing Triple Bullish Scanner")

# List of Nifty 50 stocks (Sample - you can add all 50)
TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
           "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS", "TATAMOTORS.NS", "ITC.NS"]

def get_clean_data(symbol):
    try:
        # Download 2 years of data
        df = yf.download(symbol, period="2y", interval="1d", progress=False)
        
        if df.empty or len(df) < 200:
            return None

        # FIX: YFinance Multi-Index headers often crash calculations
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        st.error(f"Error fetching {symbol}: {e}")
        return None

def check_strategy(df):
    # Calculate SMAs
    df['sma44'] = ta.sma(df['Close'], length=44)
    df['sma200'] = ta.sma(df['Close'], length=200)

    # Get the most recent available trading data
    # (Automatically handles Saturday/Sunday by taking the last row)
    curr = df.iloc[-1]
    prev2 = df.iloc[-3]

    # 1. Trend Condition (44 > 200 and 44 is rising)
    is_trending = float(curr['sma44']) > float(curr['sma200']) and float(curr['sma44']) > float(prev2['sma44'])
    
    # 2. Bullish Candle Condition (Green candle)
    is_green = float(curr['Close']) > float(curr['Open'])
    
    # 3. Entry Condition (Low touches or dips below 44 SMA)
    is_touching = float(curr['Low']) <= float(curr['sma44'])

    if is_trending and is_green and is_touching:
        return {
            "Price": round(float(curr['Close']), 2),
            "SMA 44": round(float(curr['sma44']), 2),
            "SMA 200": round(float(curr['sma200']), 2),
            "Status": "🔥 BULLISH HIT"
        }
    return None

# --- UI INTERFACE ---
st.sidebar.header("Scanner Settings")
loose_scan = st.sidebar.checkbox("Show 'Near Misses' (Within 1% of SMA)")

if st.button("🔍 Scan for Friday/Latest Results"):
    hits = []
    st.info(f"Scanning {len(TICKERS)} stocks. Please wait...")
    
    prog_bar = st.progress(0)
    
    for i, symbol in enumerate(TICKERS):
        data = get_clean_data(symbol)
        if data is not None:
            result = check_strategy(data)
            
            # If loose scan is on, we show stocks near the 44 SMA even if no "perfect" hit
            if result:
                result["Ticker"] = symbol
                hits.append(result)
            elif loose_scan:
                curr = data.iloc[-1]
                # Logic for "Near 44 SMA" within 1%
                if float(curr['Low']) <= (float(curr['sma44']) * 1.01) and float(curr['Close']) > float(curr['sma44']):
                    hits.append({
                        "Ticker": symbol,
                        "Price": round(float(curr['Close']), 2),
                        "SMA 44": round(float(curr['sma44']), 2),
                        "SMA 200": round(float(curr['sma200']), 2),
                        "Status": "👀 Near 44 SMA"
                    })
        
        prog_bar.progress((i + 1) / len(TICKERS))

    # --- RESULTS DISPLAY ---
    if hits:
        st.success(f"Analysis Complete! Found {len(hits)} signals.")
        df_results = pd.DataFrame(hits)
        # Reorder columns to put Ticker first
        cols = ['Ticker', 'Status', 'Price', 'SMA 44', 'SMA 200']
        st.table(df_results[cols])
    else:
        st.warning("No Triple Bullish hits found. The market was very weak on Friday.")
        st.write("Tip: Most stocks had Red candles on Friday, which fails your 'Bullish' rule.")
