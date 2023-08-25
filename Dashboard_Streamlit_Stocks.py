import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import sys
import bs4 as bs
import datetime as dt
from datetime import datetime, timedelta
from pandas_datareader import data as pdr
import requests
import yfinance as yf
import pandas as pd

def install(name):
    subprocess.call([sys.executable, '-m', 'pip', 'install', name])



yf.pdr_override()

def get_sp500_tickers():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.replace('.', '-')
        ticker = ticker[:-1]
        tickers.append(ticker)
    Ticker_Dataframe = pd.DataFrame(tickers, columns=['Ticker_Name'])
    Ticker_Dataframe.to_excel("S&P500 Current Ticker List.xlsx", index=False)
    return tickers

def get_data_from_yahoo():

        # Get date from 10 years ago from current date
    start_date = dt.datetime.now() - timedelta(days=365*10)
    end_date = dt.datetime.now()


    all_stock_data = {}  # Dictionary to store all stock DataFrames
    
    tickers = get_sp500_tickers()

    for ticker in tickers:
        try:
            print(ticker)
            df = pdr.get_data_yahoo(ticker, start_date, end_date)
            all_stock_data[ticker] = df
        except:
            print(f"Issue with Ticker: {ticker}")
    
    return all_stock_data

def compile_data(all_stock_data):


    tickers = get_sp500_tickers()

    main_df = pd.DataFrame()

    for count, ticker in enumerate(tickers):
        if ticker in all_stock_data:
            df = all_stock_data[ticker]
            df = df.loc[:,['Adj Close']]  # Select only the 'Adj Close' column
            df.rename(columns={'Adj Close': ticker}, inplace=True)

            if main_df.empty:
                main_df = df
            else:
                main_df = main_df.join(df, how='outer')

        if count % 10 == 0:
            print(count)
    print(main_df.head())
    #main_df.to_csv('sp500_joined_closes.csv')
    return main_df


# Streamlit app
def main():

        # Load data
    data = compile_data(get_data_from_yahoo())
    data['Date'] = pd.to_datetime(data['Date'])

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
    install('matplotlib')
    install('pandas')    
    install('numpy')
    install('pandas-datareader')
    main()

