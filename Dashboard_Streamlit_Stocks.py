import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
data = pd.read_csv('sp500_joined_closes.csv')
data['Date'] = pd.to_datetime(data['Date'])

# Streamlit app
def main():
    st.title('S&P 500 Stock Explorer')
    
    # Date Range Selector
    start_date = pd.Timestamp(st.date_input("Start date", data['Date'].min().date()))
    end_date = pd.Timestamp(st.date_input("End date", data['Date'].max().date()))
    
    # Stock Selector
    stock_options = data.columns[1:].tolist()
    selected_stock = st.selectbox('Select a stock to visualize', stock_options)
    
    # Filter data based on selections
    mask = (data['Date'] >= start_date) & (data['Date'] <= end_date)
    filtered_data = data[mask][['Date', selected_stock]]
    
    # Calculate daily returns and cumulative returns
    filtered_data['Daily Returns'] = filtered_data[selected_stock].pct_change()
    filtered_data['Cumulative Returns'] = (1 + filtered_data['Daily Returns']).cumprod() - 1
    
    # Time Series Plot with Moving Averages
    st.subheader(f'Closing Prices and Moving Averages of {selected_stock} from {start_date} to {end_date}')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(filtered_data['Date'], filtered_data[selected_stock], label=selected_stock)
    ax.plot(filtered_data['Date'], filtered_data[selected_stock].rolling(window=50).mean(), label='50-day MA', alpha=0.8)
    ax.plot(filtered_data['Date'], filtered_data[selected_stock].rolling(window=200).mean(), label='200-day MA', alpha=0.8)
    ax.set_xlabel('Date')
    ax.set_ylabel('Closing Price')
    ax.legend()
    st.pyplot(fig)
    
    # Display Daily Returns and Cumulative Returns
    st.subheader(f'Daily and Cumulative Returns for {selected_stock}')
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    ax[0].plot(filtered_data['Date'], filtered_data['Daily Returns'], label='Daily Returns', color='blue')
    ax[0].set_title('Daily Returns')
    ax[1].plot(filtered_data['Date'], filtered_data['Cumulative Returns'], label='Cumulative Returns', color='green')
    ax[1].set_title('Cumulative Returns')
    plt.tight_layout()
    st.pyplot(fig)
    
    # Histogram of Returns
    st.subheader(f'Distribution of Daily Returns for {selected_stock}')
    plt.figure(figsize=(10, 6))
    plt.hist(filtered_data['Daily Returns'].dropna(), bins=50, alpha=0.75)
    plt.title('Histogram of Daily Returns')
    plt.xlabel('Return')
    plt.ylabel('Frequency')
    st.pyplot(plt)
    
    # Display Summary Statistics
    st.subheader(f'Summary Statistics for {selected_stock}')
    st.write(filtered_data[[selected_stock, 'Daily Returns', 'Cumulative Returns']].describe())
    
    # Display Volatility
    volatility = filtered_data['Daily Returns'].std()
    st.subheader(f'Volatility for {selected_stock}')
    st.write(f"Volatility (Standard Deviation of Daily Returns): {volatility:.2%}")
    
if __name__ == '__main__':
    main()
