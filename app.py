import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- Page Config ---
st.set_page_config(page_title="Arth Sutra: Wealth Cards", layout="wide")

# --- Custom Styling for Cards ---
st.markdown("""
    <style>
    .stock-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #4e5d6e;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .stock-card:hover { border-color: #00ffcc; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- Engine: Multi-Factor Analysis ---
@st.cache_data(ttl=1800)
def analyze_nifty_200(ticker_list):
    results = []
    # Bulk download for speed and to avoid rate limits
    data = yf.download(ticker_list, period="2y", group_by='ticker', threads=True)
    
    for ticker in ticker_list:
        try:
            df = data[ticker].copy()
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            if df.empty: continue
            
            # Technical Indicators
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            
            curr = df.iloc[-1]
            
            # Confidence Logic
            score = 0
            if curr['Close'] > curr['SMA200']: score += 40
            if abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.03: score += 40
            if curr['Volume'] > df['Volume'].tail(20).mean(): score += 20
            
            results.append({
                "Ticker": ticker,
                "Price": round(curr['Close'], 2),
                "Confidence": score,
                "SL": round(curr['Close'] - (1.5 * curr['ATR']), 2),
                "Target": round(curr['Close'] + (3 * curr['ATR']), 2)
            })
        except: continue
    return pd.DataFrame(results)

# --- Main App ---
st.title("🛡️ Arth Sutra Wealth Engine")

# 1. Filters & Sorting
nifty_list = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "INFY.NS", "ITC.NS", "ZOMATO.NS"]

col_f1, col_f2 = st.columns(2)
with col_f1:
    min_conf = st.slider("Minimum Confidence (%)", 0, 100, 50)
with col_f2:
    sort_by = st.selectbox("Sort By", ["Confidence (High to Low)", "Name (A-Z)"])

# 2. Data Processing
raw_results = analyze_nifty_200(nifty_list)
if not raw_results.empty:
    filtered_df = raw_results[raw_results['Confidence'] >= min_conf]
    
    if "Confidence" in sort_by:
        filtered_df = filtered_df.sort_values(by="Confidence", ascending=False)
    else:
        filtered_df = filtered_df.sort_values(by="Ticker")

    # 3. Display Cards in Grid
    st.subheader(f"Showing {len(filtered_df)} Opportunities")
    
    # 3 cards per row
    rows = [filtered_df.iloc[i:i+3] for i in range(0, len(filtered_df), 3)]
    
    for row_df in rows:
        cols = st.columns(3)
        for i, (index, stock) in enumerate(row_df.iterrows()):
            with cols[i]:
                with st.container():
                    st.markdown(f"""
                        <div class="stock-card">
                            <h3>{stock['Ticker']}</h3>
                            <h4 style="color: #00ffcc;">Confidence: {stock['Confidence']}%</h4>
                            <p><b>Price:</b> ₹{stock['Price']}</p>
                            <p style="color: #ff4b4b;"><b>SL:</b> ₹{stock['SL']}</p>
                            <p style="color: #28a745;"><b>Target:</b> ₹{stock['Target']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Kundali: {stock['Ticker']}", key=stock['Ticker']):
                        st.session_state['selected_stock'] = stock['Ticker']

# 4. Deep-Dive Section (Click karne par khulega)
if 'selected_stock' in st.session_state:
    st.divider()
    st.subheader(f"Detailed Kundali: {st.session_state['selected_stock']}")
    # Yahan pe aapka puraana deep-dive wala logic (News + Fundamentals) aa jayega
    st.write("Fetching News & Fundamentals for", st.session_state['selected_stock'])