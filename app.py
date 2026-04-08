import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Arth Sutra: Final Index Fix", layout="wide")

@st.cache_data(ttl=3600)
def get_clean_data(ticker):
    # Download data
    df = yf.download(ticker, period="2y", progress=False)
    
    # --- CRITICAL FIX: Flattening the Multi-Index ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    return df

@st.cache_data(ttl=3600)
def get_clean_info(ticker):
    return yf.Ticker(ticker).info

# --- Main UI ---
st.title("🛡️ Arth Sutra: Wealth Engine (Index Fixed)")

ticker = st.sidebar.text_input("Enter NSE Ticker", "RELIANCE.NS")

if st.sidebar.button("Nikalye Kundali"):
    with st.spinner("Processing Data..."):
        try:
            df = get_clean_data(ticker)
            info = get_clean_info(ticker)
            
            if not df.empty:
                # Ab ye columns asani se mil jayenge
                df['SMA44'] = ta.sma(df['Close'], length=44)
                df['SMA200'] = ta.sma(df['Close'], length=200)
                
                # --- Visual Dashboard ---
                st.header(f"📊 {info.get('longName', ticker)}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("Technical Strategy (44/200 SMA)")
                    # Plotting simplified columns
                    st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(250))
                
                with col2:
                    st.subheader("Financial Summary")
                    st.metric("Current Price", f"₹{round(df['Close'].iloc[-1], 2)}")
                    st.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
            
        except Exception as e:
            # Debugging ke liye full error dikhayenge
            st.error(f"Index Error Fixed, but something else went wrong: {e}")