import streamlit as st
import pandas as pd

st.set_page_config(page_title="Daily Stock Scanner", layout="wide")
st.title("📈 5 PM Bullish Scanner")
st.write("Criteria: 44 SMA Rising + 200 SMA Rising + Green Candle Support")

try:
    df = pd.read_csv("results.csv")
    st.table(df)
    st.success(f"Last updated at: {df['Time'].iloc[0]}")
except:
    st.warning("No data found. The first scan will run today at 5 PM.")
