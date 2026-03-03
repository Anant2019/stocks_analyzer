import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Institutional Equity Scanner", layout="wide")

# --- REGULATORY COMPLIANCE HEADER ---
st.warning("⚠️ **LEGAL DISCLAIMER**: This application is strictly for **Educational Purposes** only. We are **NOT SEBI Registered** advisors. The signals generated are based on mathematical algorithms and do not constitute financial advice.")

st.title("🛡️ Strategic Momentum & Trend Filter")

# --- UNIVERSE DEFINITION ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

# Date Input (Standardized to Current Session)
target_dt = st.date_input("Analysis Target Date", datetime.now())

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def execute_scan():
    results = []
    progress_bar = st.progress(0)
    
    # Use a safe period to calculate SMA 200 properly
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
            
            if df.empty or len(df) < 201:
                continue
            
            # Handling date selection for weekend/holiday
            avail_dates = df.index[df.index <= pd.Timestamp(target_dt)]
            if avail_dates.empty:
                continue
            actual_date = avail_dates[-1]
            
            # Technical Overlays
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            
            ref = df.loc[actual_date]
            c, o, l = float(ref['Close']), float(ref['Open']), float(ref['Low'])
            s44, s200, rsi = float(ref['SMA_44']), float(ref['SMA_200']), float(ref['RSI'])
            v, v_avg = float(ref['Volume']), float(ref['Vol_Avg'])

            # Multi-Filter Strategy
            if c > s44 and s44 > s200 and c > o:
                is_blue = rsi > 65 and v > v_avg and (c > s200 * 1.05)
                risk = c - l
                target_2 = c + (2 * risk)
                
                # Fixed the F-String line break issue here
                tech_logic = f"Trend: Price above 44/200 SMA. RSI: {round(rsi,1)}. Volume surge observed."
                
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target (1:2)": round(target_2, 2),
                    "Logic": tech_logic,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except Exception:
            continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results), actual_date if 'actual_date' in locals() else None

if st.button("🚀 Run Institutional Scan"):
    data_output, final_date = execute_scan()
    
    if not data_output.empty:
        st.success(f"Market Session Analyzed: **{final_date.date()}**")
        
        st.dataframe(
            data_output[["Stock", "Category", "Entry", "Stoploss", "Target (1:2)", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn("TradingView")},
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        st.subheader("🔍 Institutional Commentary")
        selected_asset = st.selectbox("Select Asset for Insight:", ["-- Select --"] + data_output["Stock"].tolist())
        
        if selected_asset != "-- Select --":
            asset_info = data_output[data_output["Stock"] == selected_asset].iloc[0]
            st.info(f"**Technical Analysis:** {asset_info['Logic']}")
    else:
        st.error("No valid strategic setups found for the selected session.")

st.divider()
st.caption("Disclaimer: Strictly for educational use. Not SEBI registered advisors. Trading involves financial risk.")
