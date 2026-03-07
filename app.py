import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Nifty 500 Bullish Scanner", layout="wide")

def get_last_trading_day():
    today = datetime.now()
    if today.weekday() == 5: # Saturday
        return today - timedelta(days=1)
    elif today.weekday() == 6: # Sunday
        return today - timedelta(days=2)
    return today

def get_nifty500_tickers():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        return [f"{s}.NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "TATAMOTORS.NS"]

def scan_stocks(tickers):
    bullish_stocks = []
    progress_bar = st.progress(0)
    total = len(tickers)
    
    for i, ticker in enumerate(tickers):
        try:
            if i % 10 == 0:
                progress_bar.progress((i + 1) / total)
            
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if len(data) < 200: continue
            
            df = data.copy()
            df['SMA44'] = df['Close'].rolling(window=44).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            price_close = float(latest['Close'])
            price_open = float(latest['Open'])
            price_low = float(latest['Low'])
            price_high = float(latest['High'])
            sma44_now = float(latest['SMA44'])
            sma44_prev = float(prev['SMA44'])
            sma200_now = float(latest['SMA200'])
            sma200_prev = float(prev['SMA200'])
            
            is_sma_rising = (sma44_now > sma44_prev) and (sma200_now > sma200_prev)
            is_green_candle = price_close > price_open
            is_at_support = price_low <= (sma44_now * 1.01) 
            
            if is_sma_rising and is_green_candle and is_at_support:
                buy_above = round(price_high, 2)
                sl = round(price_low * 0.998, 2)
                risk = buy_above - sl
                
                if risk > 0:
                    bullish_stocks.append({
                        "Ticker": ticker.replace(".NS", ""),
                        "LTP": round(price_close, 2),
                        "Buy_Above": buy_above,
                        "SL": sl,
                        "T1": round(buy_above + (risk * 1), 2),
                        "T2": round(buy_above + (risk * 2), 2),
                        "Risk": round((risk/buy_above)*100, 2)
                    })
        except:
            continue
            
    progress_bar.empty()
    return bullish_stocks

# --- UI INTERFACE ---
st.title("🛡️ 44/200 SMA Trade Cards")
st.write("Criteria: Rising SMAs + Green Candle Support")

if st.button('🚀 Scan Nifty 500'):
    with st.spinner('Analyzing market...'):
        watchlist = get_nifty500_tickers()
        results = scan_stocks(watchlist)
        
        if results:
            st.success(f"Found {len(results)} Bullish Setups")
            
            # Create a grid: 3 cards per row
            cols = st.columns(3)
            for idx, stock in enumerate(results):
                with cols[idx % 3]:
                    with st.container(border=True):
                        # Header
                        st.subheader(f"{stock['Ticker']}")
                        
                        # Price Info
                        c1, c2 = st.columns(2)
                        c1.metric("LTP", f"₹{stock['LTP']}")
                        c2.metric("Risk", f"{stock['Risk']}%", delta_color="inverse")
                        
                        st.divider()
                        
                        # Strategy Info
                        st.markdown(f"🟢 **Entry Above:** `₹{stock['Buy_Above']}`")
                        st.markdown(f"🔴 **Stop Loss:** `₹{stock['SL']}`")
                        
                        st.info(f"🎯 **Target 1 (1:1):** `₹{stock['T1']}`\n\n"
                                f"🚀 **Target 2 (1:2):** `₹{stock['T2']}`")
        else:
            st.warning("No stocks matched the criteria today.")

st.markdown("---")
st.caption("Last data update: " + get_last_trading_day().strftime('%d %b %Y'))
