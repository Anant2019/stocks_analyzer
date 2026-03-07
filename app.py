import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- FORCED DARK MODE CONFIG ---
st.set_page_config(page_title="Nifty 500 Scanner", layout="wide")

# --- CUSTOM ULTRA-DARK CSS ---
st.markdown("""
    <style>
    /* Full screen black background */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Card Design */
    .stock-card {
        background-color: #111111;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #222222;
        margin-bottom: 20px;
        transition: border 0.3s ease;
    }
    .stock-card:hover {
        border: 1px solid #33bbff; /* Subtle blue glow on hover */
    }
    
    /* Typography */
    .ticker-name {
        font-size: 1.6rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .price-badge {
        color: #888888;
        font-size: 0.9rem;
        font-family: monospace;
    }
    
    /* Action Colors */
    .entry-text { color: #33bbff; font-weight: 700; }
    .sl-text { color: #ff4444; font-weight: 700; }
    .target-box {
        background-color: #0a2a12;
        color: #00ff44;
        padding: 10px;
        border-radius: 6px;
        margin-top: 8px;
        font-weight: 700;
        text-align: center;
        border: 1px solid #004411;
    }
    
    /* Button Styling */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        width: 100% !important;
        border: none !important;
    }
    
    /* Hide Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- LOGIC (RETAINED AS IS) ---
def get_last_trading_day():
    today = datetime.now()
    if today.weekday() == 5: return today - timedelta(days=1)
    elif today.weekday() == 6: return today - timedelta(days=2)
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
    for i, ticker in enumerate(tickers):
        try:
            if i % 10 == 0: progress_bar.progress((i + 1) / len(tickers))
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if len(data) < 200: continue
            df = data.copy()
            df['SMA44'] = df['Close'].rolling(window=44).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            l, p = df.iloc[-1], df.iloc[-2]
            
            # Logic conditions
            if (l['SMA44'] > p['SMA44']) and (l['SMA200'] > p['SMA200']) and \
               (l['Close'] > l['Open']) and (l['Low'] <= (l['SMA44'] * 1.01)):
                
                buy, sl = round(float(l['High']), 2), round(float(l['Low']) * 0.998, 2)
                risk = buy - sl
                if risk > 0:
                    bullish_stocks.append({
                        "T": ticker.replace(".NS", ""), "L": round(float(l['Close']), 2),
                        "B": buy, "S": sl, "T1": round(buy + risk, 2), "T2": round(buy + (risk*2), 2),
                        "R": round((risk/buy)*100, 2)
                    })
        except: continue
    progress_bar.empty()
    return bullish_stocks

# --- UI ---
st.title("⚡ DARK SCANNER")
st.write(f"NIFTY 500 • {get_last_trading_day().strftime('%d %b %Y')}")

if st.button('RUN MARKET ANALYSIS'):
    results = scan_stocks(get_nifty500_tickers())
    
    if results:
        cols = st.columns(3)
        for idx, s in enumerate(results):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="stock-card">
                    <div class="ticker-name">{s['T']}</div>
                    <div class="price-badge">LTP: ₹{s['L']}</div>
                    <hr style="border: 0.5px solid #222; margin: 15px 0;">
                    <div style="margin-bottom:10px;">
                        <span class="entry-text">BUY ABOVE: ₹{s['B']}</span><br>
                        <span class="sl-text">STOP LOSS: ₹{s['S']}</span> <small style="color:#555">({s['R']}%)</small>
                    </div>
                    <div class="target-box">TARGET 1: ₹{s['T1']}</div>
                    <div class="target-box" style="background-color:#00ff44; color:#000;">TARGET 2: ₹{s['T2']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No patterns detected in current session.")
