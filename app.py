import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# List of tickers to scan
tickers = ["RELIANCE.NS", "TCS.NS", "COALINDIA.NS", "INFY.NS", "ADANIPORTS.NS", "TATAMOTORS.NS"] 

def get_last_trading_day():
    today = datetime.now()
    # 5 is Saturday, 6 is Sunday
    if today.weekday() == 5:
        return today - timedelta(days=1)
    elif today.weekday() == 6:
        return today - timedelta(days=2)
    return today

def scan_stocks():
    last_trading_day = get_last_trading_day()
    date_str = last_trading_day.strftime('%Y-%m-%d')
    bullish_stocks = []
    
    print(f"Scanning for trading date: {date_str}")

    for ticker in tickers:
        # Fetch data up to today to ensure we have the most recent closed candle
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if len(data) < 200: continue
        
        # Calculate SMAs
        data['SMA44'] = data['Close'].rolling(window=44).mean()
        data['SMA200'] = data['Close'].rolling(window=200).mean()
        
        # Get the latest row available (which will be Friday's data if it's the weekend)
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Logic: SMAs rising and Green Candle
        is_sma44_rising = latest['SMA44'] > prev['SMA44']
        is_sma200_rising = latest['SMA200'] > prev['SMA200']
        is_green_candle = latest['Close'] > latest['Open']
        
        # Support check: Low of the candle is near or touching the 44 SMA
        is_at_support = latest['Low'] <= (latest['SMA44'] * 1.01) # Within 1% of SMA44
        
        if is_sma44_rising and is_sma200_rising and is_green_candle and is_at_support:
            bullish_stocks.append({
                "Ticker": ticker,
                "Price": round(float(latest['Close']), 2),
                "Scan Date": date_str,
                "Status": "Bullish Support"
            })
    
    # Save results
    result_df = pd.DataFrame(bullish_stocks)
    if not result_df.empty:
        result_df.to_csv("results.csv", index=False)
        print(f"Found {len(bullish_stocks)} stocks.")
    else:
        # Create an empty file with headers if no stocks found
        pd.DataFrame(columns=["Ticker", "Price", "Scan Date", "Status"]).to_csv("results.csv", index=False)
        print("No stocks matched the criteria today.")

if __name__ == "__main__":
    scan_stocks()
