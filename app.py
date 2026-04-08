import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- UI Setup ---
st.set_page_config(page_title="Arth Sutra: Professional Terminal", layout="wide")

# --- Custom Professional Card CSS ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #161b22;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #30363d;
        text-align: center;
        margin-bottom: 10px;
    }
    .confidence-high { color: #238636; font-weight: bold; font-size: 24px; }
    .confidence-mid { color: #d29922; font-weight: bold; font-size: 24px; }
    .confidence-low { color: #f85149; font-weight: bold; font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

# --- State Management Initialization ---
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = None

# --- Data Engine ---
@st.cache_data(ttl=1800)
def get_market_intelligence(ticker_list):
    results = []
    # Using bulk download for efficiency
    raw_data = yf.download(ticker_list, period="2y", group_by='ticker', threads=True)
    
    for ticker in ticker_list:
        try:
            df = raw_data[ticker].copy()
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            
            # Technical Logic (44/200 SMA)
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            
            curr = df.iloc[-1]
            
            # Professional Confidence Scoring
            score = 0
            if curr['Close'] > curr['SMA200']: score += 40
            if abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.03: score += 40
            if curr['Volume'] > df['Volume'].tail(20).mean(): score += 20
            
            results.append({
                "Ticker": ticker,
                "Price": round(float(curr['Close']), 2),
                "Confidence": int(score),
                "Stop_Loss": round(float(curr['Close'] - (1.5 * curr['ATR'])), 2),
                "Target": round(float(curr['Close'] + (3 * curr['ATR'])), 2)
            })
        except: continue
    return pd.DataFrame(results)

# --- Sidebar Filters ---
st.sidebar.title("🔍 Search & Filter")
sort_option = st.sidebar.selectbox("Sort Intelligence By", ["Confidence (Desc)", "Alphabetical"])
min_conf = st.sidebar.slider("Minimum Confidence Threshold", 0, 100, 50)

# --- Main Dashboard ---
st.title("🛡️ Arth Sutra: Wealth Creation Engine")
st.caption("Professional-grade technical and fundamental analysis for long-term wealth.")

tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "INFY.NS", "ITC.NS", "ZOMATO.NS"]
intel_df = get_market_intelligence(tickers)

if not intel_df.empty:
    # Applying Filters
    final_df = intel_df[intel_df['Confidence'] >= min_conf]
    if "Confidence" in sort_option:
        final_df = final_df.sort_values(by="Confidence", ascending=False)
    else:
        final_df = final_df.sort_values(by="Ticker")

    # Grid Display
    rows = [final_df.iloc[i:i+3] for i in range(0, len(final_df), 3)]
    for row_df in rows:
        cols = st.columns(3)
        for i, (index, stock) in enumerate(row_df.iterrows()):
            with cols[i]:
                conf_class = "confidence-high" if stock['Confidence'] >= 80 else "confidence-mid" if stock['Confidence'] >= 50 else "confidence-low"
                
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>{stock['Ticker']}</h3>
                        <p class="{conf_class}">Confidence: {stock['Confidence']}%</p>
                        <p>Market Price: <b>₹{stock['Price']}</b></p>
                        <p>Exit (SL): <span style="color:#f85149;">₹{stock['Stop_Loss']}</span> | Target: <span style="color:#238636;">₹{stock['Target']}</span></p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Persistence logic for details
                if st.button(f"View Deep Analysis: {stock['Ticker']}", key=f"btn_{stock['Ticker']}"):
                    st.session_state['selected_stock'] = stock['Ticker']

# --- Persistent Deep Analysis Section ---
if st.session_state['selected_stock']:
    st.divider()
    target_ticker = st.session_state['selected_stock']
    st.subheader(f"📈 Deep Analysis Report: {target_ticker}")
    
    # Fetching Detailed Info
    with st.spinner(f"Compiling Financial Blueprint for {target_ticker}..."):
        detail_ticker = yf.Ticker(target_ticker)
        info = detail_ticker.info
        hist = detail_ticker.history(period="1y")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.line_chart(hist['Close'])
            st.write(f"**Business Summary:** {info.get('longBusinessSummary', 'No data available.')[:800]}...")
            
        with col_right:
            st.write("### Key Metrics")
            st.write(f"**Sector:** {info.get('sector')}")
            st.write(f"**P/E Ratio:** {info.get('trailingPE')}")
            st.write(f"**Debt to Equity:** {info.get('debtToEquity')}")
            
            st.write("### Recent News Feed")
            for item in detail_ticker.news[:3]:
                st.info(f"🔗 {item['title']}")