def analyze_stock(symbol):
    try:
        # 1. Use multi_level_index=False to avoid the MultiIndex error
        df = yf.download(symbol, period="1y", interval="1d", progress=False, multi_level_index=False)
        
        if df.empty or len(df) < 50: 
            return None
        
        # 2. Ensure columns are simple strings (Fix for the Traceback error)
        # This removes any lingering multi-level labels
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Calculate Pro Indicators
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # Get the latest row as a Series
        curr = df.iloc[-1]
        
        # --- 75% Win-Rate Logic ---
        score = 0
        
        # Logic A: Institutional Trend (Price > 50 EMA)
        # Using .item() or float() ensures we compare raw numbers, not Series objects
        close_price = float(curr['Close'])
        ema50 = float(curr['EMA50'])
        ema20 = float(curr['EMA20'])
        rsi_val = float(curr['RSI'])

        if close_price > ema50: 
            score += 40
            
        # Logic B: The Buy Zone (Price is near or touching 20 EMA)
        if float(df.iloc[-1]['Low']) <= ema20 * 1.01: 
            score += 35
            
        # Logic C: Momentum Check (RSI is strong but not exhausted)
        if 45 < rsi_val < 65: 
            score += 25
        
        return {
            "Symbol": symbol.replace(".NS", ""),
            "Price": round(close_price, 2),
            "Score": score,
            "Signal": "🚀 HIGH CONVICTION" if score >= 75 else "WATCH" if score >= 60 else "SKIP",
            "Target": round(close_price * 1.08, 2), # 8% Swing Target
            "StopLoss": round(ema50 * 0.98, 2)      # 2% below Institutional Support
        }
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None