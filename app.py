import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- UI Configuration ---
st.set_page_config(page_title="Arth Sutra: Strategy Terminal", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .stock-card { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 15px; }
    .logic-box { background-color: #0d1117; padding: 15px; border-radius: 8px; border: 1px dashed #58a6ff; margin-top: 10px; }
    .status-green { color: #3fb950; font-weight: bold; }
    .status-red { color: #f85149; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = None

# --- Core Intelligence Engine ---
@st.cache_data(ttl=1800)
def get_detailed_analysis(ticker_list):
    results = []
    raw_data = yf.download(ticker_list, period="2y", group_by='ticker', threads=True)
    
    for ticker in ticker_list:
        try:
            df = raw_data[ticker].copy()
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 200: continue
            
            # Technical Indicators
            df['SMA44'] = ta.sma(df['Close'], length=44)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            
            curr = df.iloc[-1]
            prev_vol = df['Volume'].tail(20).mean()
            
            # Strategy Logic Checks
            is_above_200 = curr['Close'] > curr['SMA200']
            near_44 = abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.03
            high_vol = curr['Volume'] > prev_vol
            
            # Scoring
            score = 0
            reasons = []
            if is_above_200: 
                score += 40
                reasons.append("✅ Long-term Trend is Bullish (Above 200 SMA)")
            else:
                reasons.append("❌ Bearish Trend (Below 200 SMA)")
                
            if near_44: 
                score += 40
                reasons.append("✅ Ideal Entry Zone (Near 44 SMA Support)")
            else:
                reasons.append("⚠️ Overextended (Far from 44 SMA)")
                
            if high_vol: 
                score += 20
                reasons.append("✅ Accumulation detected (High Volume)")
            
            results.append({
                "Ticker": ticker, "Price": round(float(curr['Close']), 2),
                "Confidence": int(score), "Reasons": reasons,
                "SL": round(float(curr['Close'] - (1.5 * curr['ATR'])), 2),
                "Target": round(float(curr['Close'] + (3 * curr['ATR'])), 2)
            })
        except: continue
    return pd.DataFrame(results)

# --- Main Dashboard ---
st.title("🛡️ Arth Sutra Wealth Engine")
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "INFY.NS", "ITC.NS", "ZOMATO.NS"]

with st.spinner("Analyzing Technical & Fundamental Data..."):
    intel_df = get_detailed_analysis(tickers)

if not intel_df.empty:
    # Sort by Confidence
    intel_df = intel_df.sort_values(by="Confidence", ascending=False)
    
    rows = [intel_df.iloc[i:i+2] for i in range(0, len(intel_df), 2)]
    for row_df in rows:
        cols = st.columns(2)
        for i, (idx, stock) in enumerate(row_df.iterrows()):
            with cols[i]:
                st.markdown(f"""
                    <div class="stock-card">
                        <h3>{stock['Ticker']} | ₹{stock['Price']}</h3>
                        <h4 style="color:#58a6ff;">Strategy Confidence: {stock['Confidence']}%</h4>
                        <div class="logic-box">
                            <small><b>TECHNICAL REASONS:</b></small><br>
                            {'<br>'.join(stock['Reasons'])}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Strategic Blueprint: {stock['Ticker']}", key=f"btn_{stock['Ticker']}"):
                    st.session_state['selected_stock'] = stock['Ticker']

# --- Deep Analysis Section (Dividend & Fundamental Growth) ---
if st.session_state['selected_stock']:
    st.divider()
    target = st.session_state['selected_stock']
    t_obj = yf.Ticker(target)
    info = t_obj.info
    
    st.subheader(f"📑 Strategic Financial Blueprint: {target}")
    
    col1, col2, col3 = st.columns(3)
    # Dividend & Growth Logic
    div_yield = info.get('dividendYield', 0)
    div_status = "✅ Regular Dividend Payer" if div_yield and div_yield > 0 else "❌ Low/No Dividend"
    
    col1.metric("Dividend Yield", f"{div_yield*100:.2f}%" if div_yield else "0.00%", help=div_status)
    col2.metric("Profit Growth (YoY)", f"{info.get('earningsGrowth', 0)*100:.1f}%")
    col3.metric("Debt to Equity", info.get('debtToEquity', 'N/A'))

    st.markdown(f"### Why this stock might move?")
    st.write(f"1. **Dividends:** {div_status}. Long term wealth creation ke liye dividends reinvest karna zaruri hai.")
    st.write(f"2. **Growth Driver:** Iska profit growth {info.get('earningsGrowth', 0)*100:.1f}% hai, jo confidence score ko support karta hai.")
    st.write(f"3. **Financial Risk:** Debt-to-Equity ratio {info.get('debtToEquity', 'N/A')} hai. (Ideal < 1.0).")