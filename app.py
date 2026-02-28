import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- Page Settings ---
st.set_page_config(page_title="My 8PM Stock Tracker", page_icon="📈")

# Custom Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.title("📊 My Daily Stocks (8 PM View)")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"Last Updated: **{current_time}**")

# --- Your Stock List ---
# Inko aap kabhi bhi change kar sakte hain
MY_STOCKS = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'TATAMOTORS.NS']

def get_data(tickers):
    results = []
    for t in tickers:
        stock = yf.Ticker(t)
        # 5 din ka data lete hain safe side ke liye
        hist = stock.history(period="5d")
        if not hist.empty:
            last_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change = last_close - prev_close
            pct_change = (change / prev_close) * 100
            
            results.append({
                "Ticker": t.replace(".NS", ""),
                "Current Price": round(last_close, 2),
                "Change (Points)": round(change, 2),
                "Change (%)": round(pct_change, 2)
            })
    return pd.DataFrame(results)

# --- Loading Data ---
with st.spinner('Fetching Prices...'):
    df = get_data(MY_STOCKS)

# --- Display Sections ---
if not df.empty:
    # Top Row: Highlights
    cols = st.columns(len(df))
    for i, row in df.iterrows():
        color = "normal" if row['Change (%)'] >= 0 else "inverse"
        cols[i].metric(
            label=row['Ticker'], 
            value=f"₹{row['Current Price']}", 
            delta=f"{row['Change (%)']}%"
        )

    st.divider()

    # Table View
    st.subheader("Detailed Report")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Simple Manual Refresh Button
    if st.button('🔄 Update Now'):
        st.rerun()
else:
    st.error("Data fetch nahi ho paya. Please try again.")

st.caption("Note: Indian Markets close at 3:30 PM. 8 PM par aapko final closing rates dikhenge.")