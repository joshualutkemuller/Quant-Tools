import numpy as np
import pandas as pd

def compute_low_troughs(data,column):
    # Create a running minimum of the BC_10YEAR column
    data['All_Time_Low - ' + column] = data[column].cummin()

    # Display the first few rows of the dataframe with the new column
    data.tail()

    # Calculate the spread relative to the all-time low
    data['Spread_to_Low - ' + column] = data[column] - data['All_Time_Low - '+column]

    # Display the first few rows of the dataframe with the new column

    # Identify where a new low occurs
    data['New_Low_Flag - '+column] = (data[column] == data['All_Time_Low - '+column]).astype(int)

    # Compute the days since the last all-time low
    data['Days_Since_Low - '+column] = data['New_Low_Flag - '+column].cumsum()
    data['Days_Since_Low - '+column] = data.groupby('Days_Since_Low - '+column).cumcount() + 1
    
    # Assign a unique label when a new all-time low is reached
    data['Low_Label - '+column] = data['New_Low_Flag - '+column].cumsum().where(data['New_Low_Flag - '+column] == 1, None)

    #Forward fill nulls with the flag for easier plotting
    data.loc[:,'Low_Label - ' + column] = data.loc[:,'Low_Label - '+column].ffill()

    # Aggregation
    data['date'] = pd.to_datetime(data['date'])
    low_label = 'Days_Since_Low - '+column
    low_label_group = 'Low_Label - ' + column
    f = {low_label:['max'],'date':['max','min']}
    
    #Generate Labels for 10 Longest
    top_10_df = ((data.groupby(by=['Low_Label - '+column]).agg(f))).sort_values(by=(low_label,'max'),ascending=False)
    
    #Creating Rank Column
    top_10_df[('Rank','Value')] = range(1,len(top_10_df.reset_index(drop=True))+1)

    #Create Top 10 Check
    data['Top 10 Lengths - ' + column] = data['Low_Label - '+column].isin((top_10_df.head(n=10)).index)
    
    #Resetting index to get Low Label as column
    top_10_df.reset_index(drop=False,inplace=True)
    top_10_df.columns = [low_label_group,low_label,'Max Date - '+ column, 'Min Date - '+column,'Rank - '+column]
    top_10_df = top_10_df.head(n=10)
    
    #Merge
    data = data.merge(top_10_df[[low_label_group,'Max Date - '+ column, 'Min Date - '+column,'Rank - '+column]], how='left',left_on = low_label_group,right_on=low_label_group)
    print(data['Min Date - '+ column])
    
    return data

def iterate_function(input_path):
    """The purpose of this function is to read file and 
    iterate through the columns using the 'compute_low_troughs' function"""
    
    data = pd.read_csv(input_path)

    # Calculate troughs for each column except data column
    for i, k in enumerate(data.columns[1:]):
        data = compute_low_troughs(data,k)
        
    return data
    
def writer_function(input_path, output_path):
    
    import time
    
    # Start timer
    start_time = time.time()
    
    data = iterate_function(input_path)
    # Functions
    data.to_csv(output_path, index=False)

    # End
    print(f'The Treasury Trough analysis script took {time.time()-start_time} seconds to complete')
    
