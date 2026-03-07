def scan_market():
    matches = []
    for ticker in STOCK_LIST:
        try:
            # Download data
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            
            if df.empty:
                continue

            # --- THE FIX: Flatten Multi-Index ---
            # If yfinance gives us a double header, we just take the first level
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Calculate SMAs using pandas_ta
            df['44_SMA'] = ta.sma(df['Close'], length=44)
            df['200_SMA'] = ta.sma(df['Close'], length=200)
            
            # Use .iloc[-1] to get the last row as a simple Series
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2] # To check if SMA is rising
            
            # Convert to float to ensure no comparison errors
            curr_low = float(last_row['Low'])
            sma44 = float(last_row['44_SMA'])
            sma200 = float(last_row['200_SMA'])
            
            # Strategy Logic
            is_bullish_trend = sma44 > sma200
            # Buffer: within 0.5% of SMA 44
            near_sma44 = curr_low <= (sma44 * 1.005)
            
            if is_bullish_trend and near_sma44:
                matches.append({
                    "Ticker": ticker,
                    "Price": round(float(last_row['Close']), 2),
                    "SMA 44": round(sma44, 2),
                    "Status": "🔥 Strategy Hit"
                })
        except Exception as e:
            st.warning(f"Skipping {ticker} due to error: {e}")
            continue
            
    return matches
