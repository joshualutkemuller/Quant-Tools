import argparse
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time

#e.g.  python DCF_Model_MC.py --FCF 150 --RF 4 --TGR 3 --Beta 1 --ERP 6.5 --GRMean 7 --GRSTD 2 --NumSims 10000 --YEARS 5

#Calling Argument Parser
CLI = argparse.ArgumentParser()

CLI.add_argument(
    "--FCF", #name on the CLI, drop the '--' for the positional/required parameters
    help='Test', #0 or more values expected ==> creates a list
    type=int,
    default = 150 #default if nothing is provided
)
CLI.add_argument(
    "--RF",
    type = float,
    default = 3
)
CLI.add_argument(
    "--TGR",
    type = float,
    default = 2.5
)
CLI.add_argument(
    "--Beta",
    type = float,
    default = 1
)
CLI.add_argument(
    "--ERP",
    type = float,
    default = 7
)
CLI.add_argument(
    "--GRMean",
    type=float,
    default = 7.5
)
CLI.add_argument(
    "--GRSTD",
    type=float,
    default = 2
)
CLI.add_argument(
    "--NumSims",
    type=int,
    default = 10000
)
CLI.add_argument(
    "--YEARS",
    type=int,
    default = 5
)

args = CLI.parse_args()

def main():
    """
    Following variables are used: \n
    FCF : Free Cash Flows, entered as numbers with spaces, this argument takes n FCFs
    ERP : Equity Risk Premium
    Beta : Sensitivity to market return
    TGR : Terminal Growth Rate
    Risk Free Rate: Risk Free Rate used in CAPM to determine
    GRMean: Mean Growth Rate used in normal distribution generation
    GRSTD: Growth rate standard deviation, used with GRMean to produce randomly generated growth rate
    NumSims: Number of simulations in the MonteCarlo
    YEARS: Periods we are forecasting with randomly generated growth rate and discounting back to time zero
    """
    #Calling DCF model
    Discount_Cash_Flows, cash_flows, five_year_cagr = DCF(args.FCF,args.YEARS,args.GRMean,args.GRSTD)

    #Calling TV model
    Discount_Terminal_Value = TV(cash_flows,args.TGR,CAPM(args.Beta,args.RF,args.ERP))

    Total_Value = Discount_Cash_Flows + Discount_Terminal_Value

    COE = CAPM(args.Beta,args.RF,args.ERP)

    return Total_Value, five_year_cagr, Discount_Cash_Flows, Discount_Terminal_Value, COE

def CAPM(beta,rf,equity_risk_premium):
    """This function generates the cost of equity
    from the CAPM model which is used as the discount rate"""

    coe = args.RF + (args.Beta * args.ERP)

    return coe/100

def DCF(fcf,years,mean_growth,std_growth):

    #calling CAPM model to derive coe
    coe = CAPM(args.Beta,args.RF,args.ERP)

    #Normalizing Mean & Standard Deviation variables
    mean_growth /= 100
    std_growth /= 100

    #Assining first cash flow to list
    cash_flows = [fcf]

    #Building additional cash flows with normal distribution (mean & std inputs)

    for i in range(years):
        next_cash_flow = cash_flows[-1]*(1 + np.random.normal(mean_growth,std_growth))
        cash_flows.append(next_cash_flow)

    avg_five_year_growth_simulated = (cash_flows[-1]/cash_flows[0])-1

    #Removing first item in cash_flow list, time 0
    cash_flows = cash_flows[1:]

    discount_cash_flows = [ f / (1+(coe/100))**(i+1) for i , f in enumerate(cash_flows)]


    return sum(discount_cash_flows), cash_flows,avg_five_year_growth_simulated

def TV(fcf,tgr,coe):


    #TV
    terminal_value = (fcf[-1] * (1+(tgr/100))/(coe-(tgr/100)))

    #Discount TV
    discount_terminal_value = (terminal_value) / (1+coe) **(len(fcf))

    return discount_terminal_value

if __name__ == "__main__":
    #print(main.__doc__)
    start_time = time.time()
    df = pd.DataFrame(columns = ['Iteration #','Equity Value'
                                 ,'5 Year CAGR', 'Discounted Cash Flows'
                                 ,'Discounted Terminal Value','Cost of Equity'])

    for i in range(args.NumSims):
        ev, growth, discount_cashflows, discount_tv, coe = main()
        df.loc[i] = [i+1,ev,growth, discount_cashflows, discount_tv, coe]
    
    df.to_csv('DCF_MonteCarlo_Output.csv',index=False)
    time_elapse = time.time() - start_time
    print(f'MC Simulation took {time_elapse} seconds')

    #Plotting the results
    plt.hist(df['Equity Value'], bins=40, color='skyblue', edgecolor = 'red')
    plt.xlabel('Valuation')
    plt.ylabel('Frequency')
    plt.title('DCF Valuation Monte Carlo Simulation')
    plt.show()

