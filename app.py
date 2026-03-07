import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Nifty 500 Bullish Scanner", layout="wide")

# --- CUSTOM TRENDY CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .stock-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #eef2f6;
        margin-bottom: 20px;
        transition: transform 0.2s ease;
    }
    .stock-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    .ticker-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .price-badge {
        background-color: #f1f5f9;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 600;
        color: #475569;
    }
    .target-green {
        background-color: #dcfce7;
        color: #166534;
        padding: 8px;
        border-radius: 10px;
        margin-top: 5px;
        font-weight: 600;
        text-align: center;
    }
    .sl-red {
        color: #dc2626;
        font-weight: 600;
    }
    .entry-blue {
        color: #2563eb;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- CORE LOGIC (UNTOUCHED) ---
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
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

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
            
            p_close = float(latest['Close'])
            p_open = float(latest['Open'])
            p_low = float(latest['Low'])
            p_high = float(latest['High'])
            sma44_now = float(latest['SMA44'])
            sma44_prev = float(prev['SMA44'])
            sma200_now = float(latest['SMA200'])
            sma200_prev = float(prev['SMA200'])
            
            is_sma_rising = (sma44_now > sma44_prev) and (sma200_now > sma200_prev)
            is_green_candle = p_close > p_open
            is_at_support = p_low <= (sma44_now * 1.01) 
            
            if is_sma_rising and is_green_candle and is_at_support:
                buy_above = round(p_high, 2)
                sl = round(p_low * 0.998, 2)
                risk = buy_above - sl
                if risk > 0:
                    bullish_stocks.append({
                        "Ticker": ticker.replace(".NS", ""),
                        "LTP": round(p_close, 2),
                        "Buy_Above": buy_above,
                        "SL": sl,
                        "T1": round(buy_above + (risk * 1), 2),
                        "T2": round(buy_above + (risk * 2), 2),
                        "Risk_Pct": round((risk/buy_above)*100, 2)
                    })
        except: continue
    progress_bar.empty()
    return bullish_stocks

# --- UI INTERFACE ---
st.title("⚡ Pro Market Scanner")
st.markdown("##### 44 SMA + 200 SMA Bullish Momentum")

if st.button('🚀 Scan Nifty 500 Now'):
    with st.spinner('Analyzing market trends...'):
        watchlist = get_nifty500_tickers()
        results = scan_stocks(watchlist)
        
        if results:
            st.write(f"### Found {len(results)} Opportunities")
            
            # Displaying in a Grid
            cols = st.columns(3)
            for idx, stock in enumerate(results):
                with cols[idx % 3]:
                    # Modern Card using Markdown + CSS
                    st.markdown(f"""
                    <div class="stock-card">
                        <div class="ticker-name">{stock['Ticker']}</div>
                        <span class="price-badge">LTP: ₹{stock['LTP']}</span>
                        <p style="margin-top:10px;">
                            <span class="entry-blue">Entry Above: ₹{stock['Buy_Above']}</span><br>
                            <span class="sl-red">Stop Loss: ₹{stock['SL']}</span> (Risk: {stock['Risk_Pct']}%)
                        </p>
                        <div class="target-green">Target 1: ₹{stock['T1']}</div>
                        <div class="target-green" style="background-color: #bbf7d0;">Target 2: ₹{stock['T2']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No stocks matched the criteria today.")

st.sidebar.caption(f"Data Date: {get_last_trading_day().strftime('%d %b %Y')}")
