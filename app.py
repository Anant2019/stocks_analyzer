import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def execute_climax_backtest(ticker='RELIANCE.NS'):
    # 1. Data Retrieval
    df = yf.download(ticker, period='2y', interval='1d', auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # 2. Vectorized Technical Indicators
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # Volume Filter
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    
    # 3. Vectorized Signal Logic (RSI < 30 + Vol > 2x MA)
    df['Signal'] = np.where((df['RSI'] < 30) & (df['Volume'] > 2 * df['Vol_MA']), 1, 0)
    
    # 4. Success Rate Calculation (Fixed 5% Exit)
    # We look forward 10 bars to see if price hits +5% before hitting -2% SL
    df['Target'] = df['Close'] * 1.05
    df['Stop'] = df['Close'] * 0.98
    
    results = []
    signals = df[df['Signal'] == 1].index
    
    for sig in signals:
        future = df.loc[sig:].iloc[1:11] # 10-day lookahead
        if future.empty: continue
        
        hit_target = future[future['High'] >= df.loc[sig, 'Target']]
        hit_stop = future[future['Low'] <= df.loc[sig, 'Stop']]
        
        if not hit_target.empty and (hit_stop.empty or hit_target.index[0] <= hit_stop.index[0]):
            results.append(1) # Win
        else:
            results.append(0) # Loss

    # 5. Statistical Validation
    win_rate = (sum(results) / len(results)) * 100 if results else 0
    profit_factor = (sum(results) * 5) / ((len(results) - sum(results)) * 2) if (len(results) - sum(results)) > 0 else 5.0

    return win_rate, len(results), profit_factor, df

win_rate, count, pf, full_df = execute_climax_backtest()
print(f"Executive Summary: [{win_rate:.1f}%, {count}, {pf:.2f}]")
