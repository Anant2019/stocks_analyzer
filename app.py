import datetime

def check_strategy(ticker):
    try:
        # 1. Determine the "End Date" for analysis
        today = datetime.datetime.now()
        
        # If Saturday (5) or Sunday (6), set end_date to Friday
        if today.weekday() == 5: # Saturday
            end_date = today - datetime.timedelta(days=1)
        elif today.weekday() == 6: # Sunday
            end_date = today - datetime.timedelta(days=2)
        else:
            end_date = today
            
        # 2. Fetch data up to that Friday
        # Use 'period' to ensure we have enough history for the 200 SMA
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        
        if len(data) < 200: return None
        
        # Calculate Indicators
        data['sma44'] = ta.sma(data['Close'], length=44)
        data['sma200'] = ta.sma(data['Close'], length=200)
        
        # Get the very last available trading row (Friday's close)
        curr = data.iloc[-1]
        prev2 = data.iloc[-3]
        
        # Triple Bullish Logic
        is_trending = curr['sma44'] > curr['sma200'] and curr['sma44'] > prev2['sma44']
        is_strong = curr['Close'] > curr['Open'] and curr['Low'] <= curr['sma44']
        
        if is_trending and is_strong:
            return {
                "Ticker": ticker,
                "Friday Close": round(float(curr['Close']), 2),
                "44 SMA": round(float(curr['sma44']), 2)
            }
    except Exception as e:
        return None
