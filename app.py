import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: Strategy Fix", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ The 90% Strategy Tracker (Final Stable)")

# Input Date
selected_date = st.date_input("Backtest Date", datetime(2025, 12, 12))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_strategy():
    results = []
    # Data fetch dates
    start_dt = selected_date - timedelta(days=500)
    end_dt = selected_date + timedelta(days=90) # Extra days to check targets
    
    target_ts = pd.Timestamp(selected_date)
    
    progress = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            # Important: end date must be after selected_date
            df = yf.download(ticker, start=start_dt, end=end_dt, auto_adjust=True, progress=False)
            
            if df.empty or target_ts not in df.index:
                continue
            
            # Indicators
            df['SMA_44'] = df['Close'].rolling(window=44).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            
            row = df.loc[target_ts]
            close, open_p, low_p = float(row['Close']), float(row['Open']), float(row['Low'])
            sma44, sma200, rsi = float(row['SMA_44']), float(row['SMA_200']), float(row['RSI'])
            vol, vol_avg = float(row['Volume']), float(row['Vol_Avg'])

            # Strategy Logic
            if close > sma44 and sma44 > sma200 and close > open_p:
                is_blue = rsi > 65 and vol > vol_avg and (close > sma200 * 1.05)
                risk = close - low_p
                t2 = close + (2 * risk)
                
                status = "⏳ Running"
                why = f"Trend positive hai. RSI {round(rsi,1)} aur price SMAs ke upar breakout de chuka hai."
                
                # Check Future Outcome
                future = df[df.index > target_ts]
                if not future.empty:
                    for idx, f_row in future.iterrows():
                        if f_row['Low'] <= low_p:
                            status = "🔴 SL Hit"
                            why = f"Support break hua. RSI {round(rsi,1)} ke baad selling heavy rahi."
                            break
                        if f_row['High'] >= t2:
                            status = "🔥 Jackpot Hit"
                            why = f"Momentum Jackpot! High Volume aur strong RSI ne 1:2 target dilaya."
                            break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Entry": round(close, 2),
                    "Stoploss": round(low_p, 2),
                    "Target 1:2": round(t2, 2),
                    "Analysis": why,
                    "TV Link": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except:
            continue
        progress.progress((i + 1) / len(NIFTY_200))
    
    return pd.DataFrame(results)

if st.button("🚀 Run Analysis"):
    final_df = run_strategy()
    
    if not final_df.empty:
        st.subheader(f"📊 Results for {selected_date}")
        
        # Display Table
        st.dataframe(
            final_df[["Stock", "Category", "Status", "Entry", "Stoploss", "Target 1:2", "TV Link"]],
            column_config={"TV Link": st.column_config.LinkColumn("Chart")},
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        # --- DROPDOWN ANALYSIS (Stable Version) ---
        st.subheader("🔍 Detailed Technical Analysis")
        selected_stock = st.selectbox("Select a stock to see 'Why' it moved:", ["-- Choose Stock --"] + final_df["Stock"].tolist())
        
        if selected_stock != "-- Choose Stock --":
            info = final_df[final_df["Stock"] == selected_stock].iloc[0]
            st.info(f"**{selected_stock} Verdict:**")
            st.write(info["Analysis"])
    else:
        st.error(f"No signals found for {selected_date}. Please check if it was a Market Holiday.")
        
