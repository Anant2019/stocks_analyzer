import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Institutional Grade Equity Scanner", layout="wide")

st.title("🛡️ Professional Momentum & Trend Filter")
st.markdown("""
This system filters the Nifty 200 universe based on **Triple Bullish Confirmation**: 
Price > SMA 44 > SMA 200, supplemented by RSI and Volume thrust metrics.
""")

# --- UNIVERSE DEFINITION ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

# --- PARAMETERS ---
selected_date = st.date_input("Execution Date (Backtest/Live)", datetime(2025, 12, 12))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def execute_analysis():
    results = []
    # Dynamic Date Range for Technical Integrity
    start_fetch = selected_date - timedelta(days=550) 
    end_fetch = selected_date + timedelta(days=5) # Buffer for indexing
    
    progress_ui = st.progress(0)
    
    for i, ticker in enumerate(NIFTY_200):
        try:
            df = yf.download(ticker, start=start_fetch, end=end_fetch, auto_adjust=True, progress=False)
            
            if df.empty or len(df) < 200:
                continue
            
            # Handling Weekends/Holidays: Select the nearest valid trading date
            available_dates = df.index[df.index <= pd.Timestamp(selected_date)]
            if available_dates.empty: continue
            analysis_date = available_dates[-1]
            
            # Technical Overlays
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            
            # Data Extraction for Analysis Date
            ref = df.loc[analysis_date]
            c, o, l = float(ref['Close']), float(ref['Open']), float(ref['Low'])
            s44, s200, rsi = float(ref['SMA_44']), float(ref['SMA_200']), float(ref['RSI'])
            v, v_avg = float(ref['Volume']), float(ref['Vol_Avg'])

            # Core Quantitative Strategy
            if c > s44 and s44 > s200 and c > o:
                # High Probability 'Blue' Classification
                is_blue = rsi > 65 and v > v_avg and (c > s200 * 1.05)
                
                # Risk/Reward Projection
                risk = c - l
                target_2 = c + (2 * risk)
                
                status = "Active/Running"
                logic_summary = f"Bullish Structure Confirmed: Price is trading above both 44 & 200 SMAs. RSI at {round(rsi,1)} indicates strong momentum."

                # Future Outcome Simulation
                future_performance = df[df.index > analysis_date]
                if not future_performance.empty:
                    for _, f_row in future_performance.iterrows():
                        if f_row['Low'] <= l:
                            status = "Stoploss Triggered"
                            logic_summary = f"Structural Failure: Support level (Day Low) was breached. RSI was {round(rsi,1)} at entry."
                            break
                        if f_row['High'] >= target_2:
                            status = "Target Achieved (1:2)"
                            logic_summary = f"Momentum Jackpot: Institutional buying pressure drove price to 1:2 Reward ratio. Volume thrust was {round(v/v_avg,1)}x."
                            break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Entry": round(c, 2),
                    "Stoploss": round(l, 2),
                    "Target (1:2)": round(target_2, 2),
                    "Technical Logic": logic_summary,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except Exception:
            continue
        progress_ui.progress((i + 1) / len(NIFTY_200))
        
    return pd.DataFrame(results)

if st.button("🚀 Execute Strategic Scan"):
    data_output = execute_analysis()
    
    if not data_output.empty:
        st.subheader(f"Equity Analysis Report: {selected_date}")
        
        # Primary Data Display
        st.dataframe(
            data_output[["Stock", "Category", "Status", "Entry", "Stoploss", "Target (1:2)", "Chart"]],
            column_config={"Chart": st.column_config.LinkColumn("View Chart")},
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        
        # Qualitative Analysis Section
        st.subheader("💡 Strategic Insights")
        selected_asset = st.selectbox("Select Asset for Detailed Logic:", ["-- Select Asset --"] + data_output["Stock"].tolist())
        
        if selected_asset != "-- Select Asset --":
            asset_info = data_output[data_output["Stock"] == selected_asset].iloc[0]
            with st.container():
                st.info(f"**Asset:** {selected_asset} | **Classification:** {asset_info['Category']}")
                st.write(f"**Analyst Commentary:** {asset_info['Technical Logic']}")
    else:
        st.error("No valid strategic setups identified for the selected period. Ensure the date is a valid market session.")
