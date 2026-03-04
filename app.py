import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Strategy Audit", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. LEGAL NOTICE ---
st.error("⚠️ LEGAL DISCLAIMER: NOT SEBI REGISTERED. FOR EDUCATIONAL USE ONLY.")

# --- 3. CORE STRATEGY ENGINE (Optimized for Signals) ---
@st.cache_data(ttl=3600)
def run_arthasutra_engine(target_date):
    results = []
    # Using a reliable subset of Nifty 100 for faster, successful hits
    TICKERS = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'BHARTIARTL.NS', 
        'SBI.NS', 'LICI.NS', 'ITC.NS', 'HINDUNILVR.NS', 'LT.NS', 'BAJFINANCE.NS', 'TATASTEEL.NS', 
        'ADANIENT.NS', 'MARUTI.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'HCLTECH.NS', 'NTPC.NS',
        'TATAMOTORS.NS', 'ASIANPAINT.NS', 'COALINDIA.NS', 'ADANIPORTS.NS', 'KOTAKBANK.NS', 'AXISBANK.NS'
    ]
    
    progress_bar = st.progress(0, text="Searching for Bullish Setups...")
    
    for i, ticker in enumerate(TICKERS):
        try:
            # Download extra buffer for moving averages
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if data.empty or len(data) < 200: continue
            
            # Clean Column Names
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            # Filter up to target date
            valid_data = data[data.index.date <= target_date]
            if valid_data.empty: continue
            
            # Indicators
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            
            # Audit Day Data
            d = data.loc[valid_data.index[-1]]
            
            # --- UPDATED ENTRY CRITERIA (More Signals) ---
            # 1. Price above 44 SMA
            # 2. 44 SMA above 200 SMA (Long term Bullish)
            # 3. Green Candle (Close > Open)
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                
                # High Conviction (BLUE) vs Regular (AMBER)
                is_blue = d['RSI'] > 60 and d['Volume'] > (d['Vol_MA'] * 0.8)
                
                risk = d['Close'] - d['Low']
                if risk <= 0: risk = d['Close'] * 0.01 # Fallback for no-wick candles
                t2 = d['Close'] + (2 * risk)
                
                status, jackpot, days = "⏳ Running", False, "-"
                future = data[data.index > valid_data.index[-1]]
                
                if not future.empty:
                    for idx, (f_dt, f_row) in enumerate(future.iterrows()):
                        days = idx + 1
                        if f_row['Low'] <= d['Low']:
                            status = "🔴 SL Hit"
                            break
                        if f_row['High'] >= t2:
                            status = "🟢 Jackpot Hit"
                            jackpot = True
                            break
                
                results.append({
                    "Stock": ticker.replace(".NS",""), "Type": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": jackpot, "Entry": round(float(d['Close']), 2),
                    "Target": round(float(t2), 2), "SL": round(float(d['Low']), 2), "Days": days,
                    "RSI": round(float(d['RSI']), 1), "Vol": round(float(d['Volume']/d['Vol_MA']), 2)
                })
        except Exception as e:
            continue
        progress_bar.progress((i + 1) / len(TICKERS))
    
    progress_bar.empty()
    return pd.DataFrame(results), target_date

# --- 4. USER INTERFACE ---
st.title("💹 ArthaSutra Audit v4.2")

selected_date = st.date_input("Audit Date (Past Date)", datetime.now().date() - timedelta(days=5))

if st.button('🚀 Execute Strategy Audit', use_container_width=True):
    df, adj_date = run_arthasutra_engine(selected_date)
    
    if not df.empty:
        blue_df = df[df['Type'] == "🔵 BLUE"]
        # Prior Logic: Accuracy based on BLUE signals only
        accuracy = round((len(blue_df[blue_df['Jackpot']==True])/len(blue_df))*100, 1) if not blue_df.empty else 0
        
        st.write(f"### 📊 Report for: {adj_date}")
        m1, m2 = st.columns(2)
        m1.metric("Signals Found", len(df))
        m2.metric("🔵 Blue Accuracy", f"{accuracy}%")
        
        st.download_button("📥 Download Report", df.to_csv(index=False), f"Audit_{adj_date}.csv", use_container_width=True)
        st.divider()

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(f"{row['Stock']} {row['Type']}")
                c2.write(f"**{row['Status']}**")
                
                p1, p2, p3 = st.columns(3)
                p1.caption("ENTRY"); p1.write(f"₹{row['Entry']}")
                p2.caption("SL"); p2.write(f"₹{row['SL']}")
                p3.caption("TARGET"); p3.write(f"₹{row['Target']}")
                
                with st.expander("🔍 Deep Technical Analysis"):
                    st.write(f"• **Exit Timeline:** {row['Days']} Sessions")
                    st.write(f"• **Relative Volume:** {row['Vol']}x")
                    st.write(f"• **RSI Momentum:** {row['RSI']}")
                    st.link_button("View Chart 📈", f"https://www.tradingview.com/chart/?symbol=NSE:{row['Stock']}", use_container_width=True)
    else:
        st.warning(f"No signals found for {selected_date}. Try a date during a market recovery or uptrend.")

st.info("Note: Dates on weekends/holidays will return no data. Please select a valid trading day.")
