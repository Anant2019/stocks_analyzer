import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- UI Configuration ---
st.set_page_config(page_title="Arth Sutra: Professional Terminal", layout="wide")

# --- Custom Professional Styling ---
st.markdown("""
    <style>
    .stock-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .stock-card:hover { border-color: #58a6ff; transform: translateY(-5px); }
    .conf-high { color: #3fb950; font-weight: bold; font-size: 22px; }
    .conf-mid { color: #d29922; font-weight: bold; font-size: 22px; }
    .conf-low { color: #f85149; font-weight: bold; font-size: 22px; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Persistence ---
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = None

# --- Core Intelligence Engine ---
@st.cache_data(ttl=1800)
def get_market_intelligence(ticker_list):
    results = []
    # Bulk download with threads for efficiency
    raw_data = yf.download(ticker_list, period="2y", group_by='ticker', threads=True)
    
    for ticker in ticker_list:
        try:
            df = raw_data[ticker].copy()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if df.empty or len(df) < 200: continue
            
            # Technical Indicators
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            
            curr = df.iloc[-1]
            
            # Confidence Scoring (Logic: Trend + Support + Volume)
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

# --- Sidebar Controls ---
st.sidebar.title("🛡️ Engine Controls")
sort_opt = st.sidebar.selectbox("Sort By", ["Confidence (High to Low)", "Alphabetical"])
min_conf = st.sidebar.slider("Minimum Confidence Threshold", 0, 100, 50)

# --- Main Dashboard ---
st.title("🛡️ Arth Sutra Wealth Engine")
st.caption("Strategic wealth creation through high-probability technical setups.")

# Portfolio Tickers
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "INFY.NS", "ITC.NS", "ZOMATO.NS", "ADANIENT.NS", "BHARTIARTL.NS"]

with st.spinner("Aggregating Market Intelligence..."):
    intel_df = get_market_intelligence(tickers)

if not intel_df.empty:
    # Applying Logic Filters
    display_df = intel_df[intel_df['Confidence'] >= min_conf]
    if "Confidence" in sort_opt:
        display_df = display_df.sort_values(by="Confidence", ascending=False)
    else:
        display_df = display_df.sort_values(by="Ticker")

    # Grid Architecture
    st.subheader(f"Active Opportunities: {len(display_df)}")
    rows = [display_df.iloc[i:i+3] for i in range(0, len(display_df), 3)]
    
    for row_df in rows:
        cols = st.columns(3)
        for i, (idx, stock) in enumerate(row_df.iterrows()):
            with cols[i]:
                conf_val = stock['Confidence']
                conf_style = "conf-high" if conf_val >= 80 else "conf-mid" if conf_val >= 50 else "conf-low"
                
                st.markdown(f"""
                    <div class="stock-card">
                        <h2 style="margin-bottom:0px;">{stock['Ticker']}</h2>
                        <p class="{conf_style}">Strategy Confidence: {conf_val}%</p>
                        <p>Market Price: <b>₹{stock['Price']}</b></p>
                        <p style="font-size:14px;">Exit (SL): <span style="color:#f85149;">₹{stock['Stop_Loss']}</span> | Target: <span style="color:#3fb950;">₹{stock['Target']}</span></p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Strategic Report: {stock['Ticker']}", key=f"btn_{stock['Ticker']}"):
                    st.session_state['selected_stock'] = stock['Ticker']

# --- Persistent Strategic Analysis Report ---
if st.session_state['selected_stock']:
    st.divider()
    target = st.session_state['selected_stock']
    
    with st.spinner(f"Generating Financial Blueprint for {target}..."):
        t_obj = yf.Ticker(target)
        info = t_obj.info if t_obj.info else {}
        hist = t_obj.history(period="1y")
        news = t_obj.news if t_obj.news else []
        
        st.subheader(f"📑 Strategic Financial Blueprint: {target}")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### Technical Trend (1 Year)")
            if not hist.empty:
                st.line_chart(hist['Close'])
            
            st.markdown("### Corporate Overview")
            st.write(info.get('longBusinessSummary', 'Business profile currently unavailable.')[:900] + "...")
            
        with col_right:
            st.markdown("### Fundamental Metrics")
            st.write(f"**Industry:** {info.get('industry', 'N/A')}")
            st.write(f"**Trailing P/E:** {info.get('trailingPE', 'N/A')}")
            st.write(f"**Debt to Equity:** {info.get('debtToEquity', 'N/A')}")
            st.write(f"**ROE:** {info.get('returnOnEquity', 'N/A')}")
            
            st.markdown("### Market Intelligence Feed")
            if news:
                for item in news[:4]:
                    # Safe fetch for news title to avoid KeyError
                    title = item.get('title', 'Headline unavailable')
                    link = item.get('link', '#')
                    st.info(f"📰 [{title}]({link})")
            else:
                st.write("No recent intelligence reports found.")