from pyrh import Robinhood
from datetime import datetime
import numpy as np
impor tulipy as ti
import sched
import time

#A Simple Robinhood Python Trading Bot using RSI (buy <=30 and sell >=70 RSI) and with support and resistance.
#Youtube : Jacob Amaral
# Log in to Robinhood app (will prompt for two-factor)
rh = Robinhood()
rh.login(username="fluse9@gmail.com", password="password")

#Setup our variables, we haven't entered a trade yet and our RSI period
enteredTrade = False
rsiPeriod = 5

#Initiate our scheduler so we can keep checking every minute for new price changes
s = sched.scheduler(time.time, time.sleep)

def run(sc):
    global enteredTrade
    global rsiPeriod
    print("Getting historical quotes")
    # Get 5 minute bar data for Ford stock
    historical_quotes = rh.get_historical_quotes("F", "5minute", "day")
    closePrices = []
    #format close prices for RSI
    currentIndex = 0
    currentSupport  = 0
    currentResistance = 0
    for key in historical_quotes["results"][0]["historicals"]:
        if (currentIndex >= len(historical_quotes["results"][0]["historicals"]) - (rsiPeriod + 1)):
            if (currentIndex >= (rsiPeriod-1) and datetime.strptime(key['begins_at'], '%Y-%m-%dT%H:%M:%SZ').minute == 0):
                currentSupport = 0
                currentResistance = 0
                print("Resetting support and resistance")
            if(float(key['close_price']) < currentSupport or currentSupport == 0):
               currentSupport = float(key['close_price'])
               print("Current Support is : ")
               print(currentSupport)
            if(float(key['close_price']) > currentResistance):
               currentResistance = float(key['close_price'])
               print("Current Resistance is : ")
               print(currentResistance)
            closePrices.append(float(key['close_price']))
        currentIndex += 1
    DATA = np.array(closePrices)
    if (len(closePrices) > (rsiPeriod)):
        #Calculate RSI
        rsi = ti.rsi(DATA, period=rsiPeriod)
        instrument = rh.instruments("F")[0]
        #If rsi is less than or equal to 30 buy
        if rsi[len(rsi) - 1] <= 30 and float(key['close_price']) <= currentSupport and not enteredTrade:
            print("Buying RSI is below 30!")
            rh.place_buy_order(instrument, 1)
            enteredTrade = True
        #Sell when RSI reaches 70
        if rsi[len(rsi) - 1] >= 70 and float(key['close_price']) >= currentResistance and currentResistance > 0 and enteredTrade:
            print("Selling RSI is above 70!")
            rh.place_sell_order(instrument, 1)
            enteredTrade = False
        print(rsi)
    #call this method again every 5 minutes for new price changes
    s.enter(300, 1, run, (sc,))

s.enter(1, 1, run, (s,))
s.run()

import alpaca_trade_api as tradeapi
import yahoo_fin.stock_info as si
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pymongo
import statsmodels.api as sm

key = "PKDMJ3EFG7K6RBAQNPT3"
sec = "gogIZwlzCnbkBbxcdBWPdiUxrrRJDyoPNR88GO4K"

#API endpoint URL
url = "https://paper-api.alpaca.markets"

#api_version v2 refers to the version that we'll use
#very important for the documentation
api = tradeapi.REST(key, sec, url, api_version='v2')

#Init our account var
account = api.get_account()

dow_list = si.tickers_dow()
sp500_list = si.tickers_sp500()
nasdaq_list = si.tickers_nasdaq()
all_tickers = sorted(list(filter(None, set(dow_list + sp500_list + nasdaq_list))))

"""
all_historical = {}
for ticker in all_tickers:
    all_historical[ticker] = si.get_data(ticker)
    print(ticker)

dow_historical = {}
for ticker in dow_list:
    dow_historical = si.get_data(ticker, start_date='1990-01-01', end_date='2020-01-01', interval='1d')
    print(ticker)

print(si.get_quote_table('AAPL'))
print(si.get_stats('AAPL')[si.get_stats('AAPL')['Attribute'] == 'EBITDA']['Value'].iloc[0])
"""
all_data = {}
for ticker in {'AMZN'}:
    balance_sheet = si.get_balance_sheet(ticker, False)
    income_statement = si.get_income_statement(ticker, False)
    cash_flow = si.get_cash_flow(ticker, False)
    stats = si.get_stats(ticker)
    analysts_info = si.get_analysts_info(ticker)
    earnings = si.get_earnings(ticker)
    oneyear_return = (si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'].iloc[-1] - si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'][0])/si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'][0]

    stats.columns = ['Labels', 'Values']

    stats_labels = []
    stats_values = []
    for i in range(stats.shape[0]):
        stats_labels.append(stats.iat[i, 0])
        stats_values.append(stats.iat[i, 1])
    stats_df = pd.DataFrame({'Values': stats_values}, index=stats_labels)

    print(analysts_info['Earnings Estimate'])
    earnings_estimate = analysts_info['Earnings Estimate'].iloc[[]]

    yearly_revenue_growth = earnings['yearly_revenue_earnings'].iloc[[3], [1]].values[0][0] - earnings['yearly_revenue_earnings'].iloc[[0], [1]].values[0][0]
    quarterly_revenue_growth = earnings['quarterly_revenue_earnings'].iloc[[3], [1]].values[0][0] - earnings['quarterly_revenue_earnings'].iloc[[0], [1]].values[0][0]
    yearly_earnings_growth = earnings['yearly_revenue_earnings'].iloc[[3], [2]].values[0][0] - earnings['yearly_revenue_earnings'].iloc[[0], [2]].values[0][0]
    quarterly_earnings_growth = earnings['quarterly_revenue_earnings'].iloc[[3], [2]].values[0][0] - earnings['quarterly_revenue_earnings'].iloc[[0], [2]].values[0][0]
    for i in [0, 1, 2, 3]:
        avg_quarterly_results = 0.25 * (earnings['quarterly_results'].iloc[[i], [1]].values[0][0] - earnings['quarterly_results'].iloc[[i], [2]].values[0][0])

    earnings_df = pd.DataFrame({
        'Values': [yearly_revenue_growth, yearly_earnings_growth, quarterly_revenue_growth, quarterly_earnings_growth, avg_quarterly_results]},
        index=['yearly_revenue_growth', 'yearly_earnings_growth', 'quarterly_revenue_growth', 'quarterly_earnings_growth', 'avg_quarterly_results'])

    return_df = pd.DataFrame({
        'Values': [oneyear_return]},
        index=['1yr_return'])

    values = []
    labels = []
    for i in [balance_sheet, income_statement, cash_flow, stats_df, earnings_df, return_df]:
        for j in i.index.values:
            labels.append(j)
        for j in range(i.shape[0]):
            values.append(i.iat[j, 0])

    data = {'labels': labels, 'values': values}
    df = pd.DataFrame({'Values': values}, index=labels)
    print(df)

model = sm.OLS(oneyear_return, all_data).fit()


dow_earnings = {}
for ticker in dow_list:
    first_close = si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'][0]
    last_close = si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'].iloc[-1]
    total_return = (last_close - first_close)/first_close
    dow_earnings[str(ticker)] = total_return
    print(ticker)

sorted_earnings = sorted(dow_earnings.items(), key=lambda x: x[1], reverse=True)

print(sorted_earnings)