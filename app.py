import time

# --- Scan All Stocks (Parallel with progress) ---
def scan_all(stocks):
    results = []
    index_df = yf.download("^NSEI", period="1y", progress=False)
    progress = st.progress(0)
    total = len(stocks)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scan_stock, stock, index_df): stock for stock in stocks}
        completed = 0
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)
            completed += 1
            progress.progress(completed / total)
            time.sleep(0.05)  # slight delay to reduce overload
    
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results["AI Score"] = pd.to_numeric(df_results["AI Score"], errors='coerce')
        df_results["Relative Strength %"] = pd.to_numeric(df_results["Relative Strength %"], errors='coerce')
        df_results = df_results.dropna(subset=["AI Score","Relative Strength %"])
        df_results = df_results.sort_values(by=["AI Score","Relative Strength %"], ascending=False)
    return df_results