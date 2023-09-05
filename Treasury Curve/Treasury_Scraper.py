import pandas as pd
from ust import save_xml, read_rates, available_years, date_generator,get_spreads
from datetime import date
from datetime import datetime
import datetime as dt
import os
import sys
import numpy as np
import time
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import bs4
import pandas as pd
import requests
import low_trough as lt

start_time = time.time()

#set year variables
start_year = 1990
end_year = 2023

__all__ = ["save_xml", "read_rates", "available_years","date_generator","get_spreads"]
    
BC_KEYS = [
    "BC_1MONTH",
    "BC_2MONTH", #added 2 month, quality check
    "BC_3MONTH",
    "BC_4MONTH",
    "BC_6MONTH",
    "BC_1YEAR",
    "BC_2YEAR",
    "BC_3YEAR",
    "BC_5YEAR",
    "BC_7YEAR",
    "BC_10YEAR",
    "BC_20YEAR",
    "BC_30YEAR","BC_30YEARDISPLAY"]
BC_KEYS_REAL = [
    "BC_5YEAR",
    "BC_7YEAR",
    "BC_10YEAR",
    "BC_20YEAR",
    "BC_30YEAR"]

# Create a list of columns that align with Treasury.Gov
DF_COLUMNS = ["date"] + BC_KEYS
DF_COLUMNS_REAL = ["date"] + BC_KEYS_REAL

BASE_URL = (
    "https://home.treasury.gov/resource-center/"
    "data-chart-center/interest-rates/pages/xml?"
    "data=daily_treasury_yield_curve&field_tdr_date_value={}")

BASE_URL_REAL = (
    "https://home.treasury.gov/resource-center/"
    "data-chart-center/interest-rates/pages/xml?"
    "data=daily_treasury_real_yield_curve&field_tdr_date_value={}")
    
#BASE_URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=all")
#)
def assign_identifiers(inversions_dict):
    """
    Assign a unique identifier to each inversion period.
    
    Args:
    - inversions_dict (dict): Dictionary with spread names as keys and lists of inversion periods as values.
    
    Returns:
    - Dictionary with spread names as keys and lists of tuples as values. Each tuple contains an inversion period
      and its unique identifier.
    """
    identifiers_dict = {}
    for spread, inversions in inversions_dict.items():
        identifiers = [f"{spread}_{i+1}" for i in range(len(inversions))]
        identifiers_dict[spread] = list(zip(inversions, identifiers))
    
    return identifiers_dict

def add_inversion_date_range(data, inversions_dict):
    """
    Add inversion start and end date columns to the dataset.
    
    Args:
    - data (pd.DataFrame): Dataset with date as the index.
    - inversions_dict (dict): Dictionary with spread names as keys and lists of tuples as values. 
      Each tuple contains an inversion period and its unique identifier.
    
    Returns:
    - Updated DataFrame with new columns.
    """
    for spread, inversions in inversions_dict.items():
        data[f"{spread}_START_DATE"] = None
        data[f"{spread}_END_DATE"] = None
        
        for period, _ in inversions:
            mask = (data.index >= period[0]) & (data.index <= period[1])
            data.loc[mask, f"{spread}_START_DATE"] = period[0]
            data.loc[mask, f"{spread}_END_DATE"] = period[1]
    
    return data

def add_inversion_counter(data, numeric_columns):
    """
    Add inversion indicator and counter columns to the original dataset.
    
    Args:
    - data (pd.DataFrame): Original dataset with date as the index.
    
    Returns:
    - Updated DataFrame with new columns.
    """

    print(data.columns)
    for spread in numeric_columns:
        # Create inversion indicator column initialized with zeros
        data[f"{spread}_INVERTED"] = (data[spread] < 0).astype(int)
        
        # Create counter column for inversion days
        data[f"{spread}_COUNTER"] = 0
        counter = 0
        for i in range(len(data)):
            if data[f"{spread}_INVERTED"].iloc[i] == 1:
                counter += 1
                data[f"{spread}_COUNTER"].iloc[i] = counter
            else:
                counter = 0
    
    return data


def add_inversion_columns(data, inversions_dict):
    """
    Add inversion indicator and identifier columns to the original dataset.
    
    Args:
    - data (pd.DataFrame): Original dataset with date as the index.
    - inversions_dict (dict): Dictionary with spread names as keys and lists of tuples as values. 
      Each tuple contains an inversion period and its unique identifier.
    
    Returns:
    - Updated DataFrame with new columns.
    """
    for spread, inversions in inversions_dict.items():
        # Create inversion indicator column initialized with zeros
        data[f"{spread}_INVERTED"] = 0
        data[f"{spread}_ID"] = None
        
        for period, identifier in inversions:
            mask = (data.index >= period[0]) & (data.index <= period[1])
            data.loc[mask, f"{spread}_INVERTED"] = 1
            data.loc[mask, f"{spread}_ID"] = identifier
    
    return data

def identify_inversions(spread_data):
    """
    Identify inversion periods in a spread column.
    
    Args:
    - spread_data (pd.Series): Series of spread values with datetime index.
    
    Returns:
    - List of tuples where each tuple contains the start and end date of an inversion period.
    """
    # Identify where the spread is negative
    inversions = spread_data < 0
    # Identify the start of a new inversion period (shift and compare to identify changes)
    starts = (inversions & ~inversions.shift(fill_value=False)).where(lambda x: x).dropna().index
    # Identify the end of an inversion period
    ends = (~inversions & inversions.shift(fill_value=False)).where(lambda x: x).dropna().index
    
    # Create list of inversion periods
    inversion_periods = [(start, end) for start, end in zip(starts, ends)]
    
    # Handle cases where the last inversion period doesn't have an end yet
    if len(starts) > len(ends):
        inversion_periods.append((starts[-1], spread_data.index[-1]))

    
    return inversion_periods, starts,ends


def main():

    full_month, full_year, number_month = date_generator()

    print(full_month, full_year, number_month)



    """Run Code Here"""


    # save UST yield rates to local folder for selected years
    for year in available_years():
        save_xml(year, folder="xml",df_columns=DF_COLUMNS,BASE_URL=BASE_URL,BC_KEYS=BC_KEYS)

    # run later - force update last year (overwrites existing file)
    save_xml(end_year, folder="xml", overwrite=True, df_columns=DF_COLUMNS,BASE_URL=BASE_URL,BC_KEYS=BC_KEYS)


    # read UST yield rates as pandas dataframe, reset index
    df = read_rates(start_year=1990, end_year=end_year, folder="xml",df_columns=DF_COLUMNS,BASE_URL=BASE_URL,BC_KEYS=BC_KEYS)
    df.reset_index(inplace=True)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')


    # save UST Real yield rates to local folder for selected years, assigning real columns and url for functions
    for year in available_years():
        save_xml(year,
                 folder="realratesxml",
                 df_columns=DF_COLUMNS_REAL,BASE_URL=BASE_URL_REAL,
                 BC_KEYS=BC_KEYS_REAL)

    # run later - force update last year (overwrites existing file)
    save_xml(end_year, folder="realratesxml", overwrite=True,df_columns=DF_COLUMNS_REAL,BASE_URL=BASE_URL_REAL,BC_KEYS=BC_KEYS_REAL)



    """     # read UST yield rates as pandas dataframe, reset index
        df_real = read_rates(start_year=1990,
                            end_year=end_year, 
                            folder="realratesxml",df_columns=DF_COLUMNS_REAL,BASE_URL=BASE_URL_REAL,BC_KEYS=BC_KEYS_REAL)
        
        df_real.reset_index(inplace=True)
        df_real['date'] = pd.to_datetime(df_real['date']).dt.strftime('%Y-%m-%d')

    """
    # read UST spreads & sort based on date descending & counter inversion
    df_copy = df.copy()
    spread_df = get_spreads(df_copy)
    spread_df = spread_df.sort_values(by = 'date', ascending = True)

    # run inversion analysis
    spread_df['date'] = pd.to_datetime(spread_df['date'])
    spread_df.set_index('date', inplace=True)

    # Identify inversion periods for each spread
    inversions_dict = {}
    for column in spread_df.columns:
        inversions_dict[column], starts,ends = identify_inversions(spread_df[column])

    # Call assign identifiers function and pass to updated spread function
    identified_inversions = assign_identifiers(inversions_dict)
    updated_spread_df = add_inversion_columns(spread_df,identified_inversions)

    # Add Inversion Counter
    non_numeric_columns = updated_spread_df.columns[updated_spread_df.dtypes=='object']
    numeric_columns = [i for i in updated_spread_df.columns if i not in non_numeric_columns]
    updated_spread_df = add_inversion_counter(updated_spread_df.copy(), numeric_columns)
    
    # Add Inversion Date Range Columns
    updated_spread_df = add_inversion_date_range(updated_spread_df.copy(), identified_inversions)

    #write to general folder for manipulation
    df.to_csv("treasury_rates.csv", index = False)
    updated_spread_df.to_csv("treasury_spreads.csv")
    #df_real.to_csv("/treasury_real_rates.csv", index = False)

    most_recent_date = df.at[df.index.max(),'date']
    
    #Trough Analysis
    lt.writer_function(input_path = 'treasury_rates.csv',
                output_path = 'treasury_trough_analysis.csv')

    print(f'Code complete, the most recent date pull is {most_recent_date}')
    print(starts)
    print(ends)


if __name__ == "__main__":
    main()
    print(f'The total code took {time.time() - start_time} seconds to run')

else:
    main()
