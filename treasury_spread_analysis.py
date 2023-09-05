import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas.tseries.offsets import *

#Tenor Conversion Function
def Tenor_Conversion(row):
    if row['Tenor'] == '1 mo':
        return 1
    elif row['Tenor'] == '2 mo':
        return 2
    elif row['Tenor'] == '3 mo':
        return 3
    elif row['Tenor'] == '6 mo':
        return 6
    elif row['Tenor'] == '1 yr':
        return 12
    elif row['Tenor'] == '2 yr':
        return 24
    elif row['Tenor'] == '3 yr':
        return 36
    elif row['Tenor'] == '5 yr':
        return 60
    elif row['Tenor'] == '7 yr':
        return 84
    elif row['Tenor'] == '10 yr':
        return 120
    elif row['Tenor'] == '15 yr':
        return 180
    elif row['Tenor'] == '20 yr':
        return 240
    elif row['Tenor'] == '30 yr':
        return 360
    
def Tenor_Conversion_Treasury(row):
    if row['Tenor'] == 'BC_1MONTH':
        return 1
    elif row['Tenor'] == 'BC_2MONTH':
        return 2
    elif row['Tenor'] == 'BC_3MONTH':
        return 3
    elif row['Tenor'] == 'BC_4MONTH':
        return 4
    elif row['Tenor'] == 'BC_6MONTH':
        return 6   
    elif row['Tenor'] == 'BC_1YEAR':
        return 12
    elif row['Tenor'] == 'BC_2YEAR':
        return 24
    elif row['Tenor'] == 'BC_3YEAR':
        return 36
    elif row['Tenor'] == 'BC_5YEAR':
        return 60
    elif row['Tenor'] == 'BC_7YEAR':
        return 84
    elif row['Tenor'] == 'BC_10YEAR':
        return 120
    elif row['Tenor'] == 'BC_20YEAR':
        return 240
    elif row['Tenor'] == 'BC_30YEAR':
        return 360

def Average_Interpolated_Curve_Treasury(df,number):
    
    #Convert & sort descending
    df['date'] = pd.to_datetime(df['date'])
    sorted_data = (df.sort_values(by=['date'],ascending=False,ignore_index=False)).iloc[:number]

    ##Create Average Dateframe
    avg_df = pd.DataFrame({'Avg Tenor Value':sorted_data.mean(axis=0)}).reset_index(drop=False).rename(columns={'index':'Tenor'})
    print(avg_df)
    avg_df['Term'] = avg_df.apply(Tenor_Conversion_Treasury,axis=1)

    #Create Term DF (1 through 360) and merge on average dataframe
    Combined_Term_df = (pd.DataFrame({'Term':pd.Series(range(1,361))}).merge(avg_df,how='left',left_on = 'Term',right_on='Term')).drop(columns=['Tenor'])
    Combined_Term_df['Avg Tenor Value'] = Combined_Term_df['Avg Tenor Value'].interpolate()
    
    #write to csv
    Combined_Term_df.to_csv('Average_'+str(number)+'_Day_Interpolated_Treasury_Par_Rates.csv',index=False) 

    print('Sucess in writing interpolated curves to directories')
    return Combined_Term_df  
    
def Treasury_Main():
    
    #Load the dataset
    data = pd.read_csv('treasury_spreads.csv')

    #Load the Treasury Rates for Interpolation
    data_interpolation = (pd.read_csv('treasury_rates.csv')).drop(columns=["BC_30YEARDISPLAY"], axis=1)

    #Display the first few rows of the dataset
    data.head()
    
    # Interpolated the 14 and 30 day average for Treasury Par Rates
    Average_14_Day_Treasury_Interpolated = Average_Interpolated_Curve_Treasury(data_interpolation,14)
    Average_30_Day_Treasury_Interpolated = Average_Interpolated_Curve_Treasury(data_interpolation,30)
    
    # Summary statistics for numerical columns
    numerical_summary = data.describe(include=[np.number])

    # Summary statistics for categorical and datetime columns
    categorical_summary = data.describe(include=[np.object])

    # Convert date to datetime
    data['date'] = pd.to_datetime(data['date'])

    # Filter out non-inversion periods for 2Y10Y and 3M10Y
    inversion_data_2Y10Y = data[data['Identifier_Group (2Y10Y)'] > 0]
    inversion_data_3M10Y = data[data['Identifier_Group(10Y3M)'] > 0]

    #Create Aggregation Dictionary to get spread and end date
    f_1 = {'10Y2Y_SPREAD':['min', 'max','count'],'date':['max']}
    f_2 = {'10Y3M_SPREAD':['min', 'max','count'],'date':['max']}

    # Group by identifier and calculate max and min spread for each group
    grouped_inversion_2Y10Y = inversion_data_2Y10Y.groupby('Start Date Inversion (2Y10Y)').agg(f_1)
    grouped_inversion_3M10Y = inversion_data_3M10Y.groupby('Start Date Inversion (10Y3M)').agg(f_2)

    #reset indices and keep date as column and rename start_date column
    (grouped_inversion_2Y10Y.reset_index(drop=False,inplace=True))
    grouped_inversion_3M10Y.reset_index(drop=False,inplace=True)
    grouped_inversion_2Y10Y.rename(columns={'Start Date Inversion (2Y10Y)':'Start_Date_Inversion'},inplace=True)
    grouped_inversion_3M10Y.rename(columns={'Start Date Inversion (10Y3M)':'Start_Date_Inversion'},inplace=True)

    #Check date dtype
    data['date'] = pd.to_datetime(data['date'],format = '%Y-%m-%d')

    #Write to CSV
    grouped_inversion_2Y10Y.to_csv('2Y10Y_Inversion_Groups.csv',index=False)
    grouped_inversion_3M10Y.to_csv('3M10Y_Inversion_Groups.csv',index=False)

    #Calling hist_plot function
    Hist_Plot.hist_plot(data)

    print('UST Spread Analysis Script Complete')
    
Treasury_Main()

print('reasury Spread Analysis scripts are complete')