import alpaca_trade_api as tradeapi
import yahoo_fin.stock_info as si
import math
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import pymongo
import statsmodels.api as sm
import YahooFinance as yf
from scipy import stats

class MongoConnection(object):
    client = None
    database = None
    collection = None

    def __init__(self, host, dbname, colname):
        self.client = pymongo.MongoClient(host)
        self.database = self.client[dbname]
        self.collection = self.database[colname]

    def getDocument(self, id):
        return self.collection.find_one({'_id': id})

    def insertDocument(self, doc):
        return self.collection.insert_one(doc)

class StockData(object):

    def __init__(self, analyze):
        if (analyze == False):
            self.main()
            self.logData()
            self.getFinancials()

        elif (analyze == True):
            self.runAnalytics()

    def main(self):
        username = "fluse9"
        password = "allegoryofthecave1"
        dbname = "StockData"
        colname = "Financials"
        host = "mongodb+srv://" + username + ":" + password + "@investmentdata.z4aov.mongodb.net/" + dbname + "?retryWrites=true&w=majority"

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
        all_tickers = sorted(list(filter(None, set(dow_list + sp500_list))))

        for ticker in all_tickers:
            try:
                price = si.get_live_price(ticker)
                quote_table = si.get_quote_table(ticker, True)
                balance_sheet = yf.get_balance_sheet(ticker)
                income_statement = yf.get_income_statement(ticker)
                cash_flow = yf.get_cash_flow(ticker)
                stats = si.get_stats(ticker)
                valuation = si.get_stats_valuation(ticker)
                analysts_info = si.get_analysts_info(ticker)
                earnings = si.get_earnings(ticker)
                oneyear_return = (si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'].iloc[-1] - si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'][0])/si.get_data(ticker, start_date=datetime.today()-timedelta(days=365), end_date=datetime.today())['close'][0]

                financials = self.logData(ticker, price, quote_table, balance_sheet, income_statement, cash_flow, stats, valuation, analysts_info, earnings, oneyear_return)
                MongoConnection(host, dbname, colname).insertDocument(financials)
            except:
                pass

    def cleanData(self, num):
        num_str = str(num)
        if (num_str[-1] == 'M'):
            new_num = float(num[:-1]) * 1000000
        if (num_str[-1] == 'B'):
            new_num = float(num[:-1]) * 1000000000
        if (num_str[-1] == 'T'):
            new_num = float(num[:-1]) * 1000000000000
        return new_num

    def cleanFinancials(self, num, units):
        if (units == 'thousands'):
            new_num = num * 1000
        elif (units == 'millions'):
            new_num = num * 1000000
        elif (units == 'billions'):
            new_num = num * 1000000000
        elif (units == 'trillions'):
            new_num = num * 1000000000000
        return new_num

    def fcf_valuation(self):
        d = 0.12
        if (self.last_4yr_fcf_growth > 0.2):
            g = 0.2
        elif (self.last_4yr_fcf_growth < 0.05):
            g = 0.05
        else:
            g = self.last_4yr_fcf_growth
        intrinsic_value = self.fcf * ((
            ((g + 1) / (d + 1)) +
            (((g + 1) ** 2) / ((d + 1) ** 2)) +
            (((g + 1) ** 3) / ((d + 1) ** 3)) +
            (((g + 1) ** 4) / ((d + 1) ** 4)) +
            (((g + 1) ** 5) / ((d + 1) ** 5)) +
            (((g + 1) ** 6) / ((d + 1) ** 6)) +
            (((g + 1) ** 7) / ((d + 1) ** 7)) +
            (((g + 1) ** 8) / ((d + 1) ** 8)) +
            (((g + 1) ** 9) / ((d + 1) ** 9)) +
            (((g + 1) ** 10) / ((d + 1) ** 10))) +
            ((self.fcf * (((g + 1) ** 10) / ((d + 1) ** 10))) * ((1 + 0.05) / (1 + d)))
        )
        return intrinsic_value / self.shares_outstanding

    def earnings_valuation(self):
        d = 0.12
        if (self.last_5yr_earnings > 0.2):
            g = 0.2
        elif (self.last_5yr_earnings < 0.05):
            g = 0.05
        else:
            g = self.last_5yr_earnings
        intrinsic_value = self.eps * ((
            ((g + 1) / (d + 1)) +
            (((g + 1) ** 2) / ((d + 1) ** 2)) +
            (((g + 1) ** 3) / ((d + 1) ** 3)) +
            (((g + 1) ** 4) / ((d + 1) ** 4)) +
            (((g + 1) ** 5) / ((d + 1) ** 5)) +
            (((g + 1) ** 6) / ((d + 1) ** 6)) +
            (((g + 1) ** 7) / ((d + 1) ** 7)) +
            (((g + 1) ** 8) / ((d + 1) ** 8)) +
            (((g + 1) ** 9) / ((d + 1) ** 9)) +
            (((g + 1) ** 10) / ((d + 1) ** 10))) +
            ((self.eps * (((g + 1) ** 10) / ((d + 1) ** 10))) * ((1 + 0.05) / (1 + d)))
        )
        return intrinsic_value

    def logData(self, ticker, price, quote_table, balance_sheet, income_statement, cash_flow, stats, valuation, analysts_info, earnings, oneyear_return):
        self.ticker = ticker
        try:
            self.price = float(price)
        except:
            self.price = None
        try:
            self.eps = float(quote_table['EPS (TTM)'])
        except:
            self.eps = None
        try:
            self.shares_outstanding = self.cleanData(
                stats.loc[stats['Attribute'] == 'Shares Outstanding 5', 'Value'].values[0])
        except:
            self.shares_outstanding = None
        try:
            self.pe_ratio = self.price / self.eps
        except:
            self.pe_ratio = None
        try:
            self.last_5yr_earnings = float(analysts_info['Growth Estimates'].iloc[[5], [1]].values[0][0][:-1]) / 100
        except:
            self.last_5yr_earnings = None
        try:
            self.next_5yr_earnings = float(analysts_info['Growth Estimates'].iloc[[4], [1]].values[0][0][:-1]) / 100
        except:
            self.next_5yr_earnings = None
        try:
            self.peg_ratio = self.pe_ratio / (self.next_5yr_earnings * 100)
        except:
            self.peg_ratio = None
        try:
            self.ev = self.cleanData(valuation.iloc[[1], [1]].values[0][0])
        except:
            self.ev = None
        try:
            self.ebit = float(income_statement.loc[income_statement[0] == 'EBIT', 1].values[0].replace(',', '')) * 1000
        except:
            self.ebit = None
        try:
            self.earnings_yield = self.ebit / self.ev
        except:
            self.earnings_yield = None
        try:
            self.equity_per_share = float(
                stats.loc[stats['Attribute'] == 'Book Value Per Share (mrq)', 'Value'].values[0])
        except:
            self.equity_per_share = None
        try:
            self.price_book_ratio = self.price / self.equity_per_share
        except:
            self.price_book_ratio = None
        try:
            self.fcf = float(cash_flow.loc[cash_flow[0] == 'Free Cash Flow', 2].values[0].replace(',', '')) * 1000
        except:
            self.fcf = None
        try:
            self.last_4yr_fcf_growth = (float(
                cash_flow.loc[cash_flow[0] == 'Free Cash Flow', 2].values[0].replace(',', '')) * 1000 - float(
                cash_flow.loc[cash_flow[0] == 'Free Cash Flow', 5].values[0].replace(',', '')) * 1000) / float(
                cash_flow.loc[cash_flow[0] == 'Free Cash Flow', 5].values[0].replace(',', '')) * 1000
        except:
            self.last_4yr_fcf_growth = None
        try:
            self.current_assets = float(
                balance_sheet.loc[balance_sheet[0] == 'Current Assets', 1].values[0].replace(',', '')) * 1000
        except:
            self.current_assets = None
        try:
            self.total_assets = float(
                balance_sheet.loc[balance_sheet[0] == 'Total Assets', 1].values[0].replace(',', '')) * 1000
        except:
            self.total_assets = None
        try:
            self.current_liabilities = float(
                balance_sheet.loc[balance_sheet[0] == 'Current Liabilities', 1].values[0].replace(',', '')) * 1000
        except:
            self.current_liabilities = None
        try:
            self.total_liabilities = float(
                balance_sheet.loc[balance_sheet[0] == 'Total Liabilities Net Minority Interest', 1].values[0].replace(
                    ',', '')) * 1000
        except:
            self.total_liabilities = None
        try:
            self.total_equity = float(
                balance_sheet.loc[balance_sheet[0] == 'Total Equity Gross Minority Interest', 1].values[0].replace(',',
                                                                                                                   '')) * 1000
        except:
            self.total_equity = None
        try:
            self.cash = float(
                balance_sheet.loc[balance_sheet[0] == 'Cash And Cash Equivalents', 1].values[0].replace(',', '')) * 1000
        except:
            self.cash = None
        try:
            self.current_ratio = self.current_assets / self.current_liabilities
        except:
            self.current_ratio = None
        try:
            self.total_debt_ratio = self.total_liabilities / self.current_assets
        except:
            self.total_debt_ratio = None
        try:
            self.debt_equity_ratio = self.total_liabilities / self.total_equity
        except:
            self.debt_equity_ratio = None
        try:
            self.cash_ratio = self.cash / self.current_liabilities
        except:
            self.cash_ratio = None
        try:
            self.net_fixed_assets = float(
                balance_sheet.loc[balance_sheet[0] == 'Net PPE', 1].values[0].replace(',', '')) * 1000
        except:
            self.net_fixed_assets = None
        try:
            self.working_capital = self.current_assets - self.current_liabilities
        except:
            self.working_capital = None
        try:
            self.return_on_capital = self.ebit / (self.net_fixed_assets + self.working_capital)
        except:
            self.return_on_capital = None
        try:
            self.interest_expense = float(
                income_statement.loc[income_statement[0] == 'Interest Expense', 1].values[0].replace(',', '')) * 1000
        except:
            self.interest_expense = None
        try:
            self.total_debt = float(
                balance_sheet.loc[balance_sheet[0] == 'Total Debt', 1].values[0].replace(',', '')) * 1000
        except:
            self.total_debt = None
        try:
            self.cost_of_debt = self.interest_expense / self.total_debt * 100
        except:
            self.cost_of_debt = None
        try:
            self.beta = float(stats.iloc[[0], [1]].values[0][0])
        except:
            self.beta = None
        try:
            self.cost_of_equity = 0.025 + self.beta * (0.1 - 0.025)
        except:
            self.cost_of_equity = None
        try:
            self.mvoe = self.cleanData(quote_table['Market Cap'])
        except:
            self.mvoe = None
        try:
            self.wavg_time_to_maturity = 5.3
        except:
            self.wavg_time_to_maturity = None
        try:
            self.mvod = self.interest_expense * (
                        (1 - (1 / ((1 + self.cost_of_debt) ** self.wavg_time_to_maturity))) / self.cost_of_debt) + (
                                    self.total_debt / ((1 + self.cost_of_debt) ** self.wavg_time_to_maturity))
        except:
            self.mvod = None
        try:
            self.wavg_cost_of_capital = (self.mvoe / (self.mvoe + self.mvod)) * self.cost_of_equity + (
                        self.mvod / (self.mvoe + self.mvod)) * self.cost_of_debt * (1 - 0.21)
        except:
            self.wavg_cost_of_capital = None
        try:
            self.value_added = self.return_on_capital - self.wavg_cost_of_capital
        except:
            self.value_added = None
        try:
            self.intrinsic_value_fcf = self.fcf_valuation()
        except:
            self.intrinsic_value_fcf = None
        try:
            self.intrinsic_value_eps = self.earnings_valuation()
        except:
            self.intrinsic_value_eps = None
        try:
            self.payout_ratio = float(stats.iloc[[23], [1]].values[0][0][:-1])
        except:
            self.payout_ratio = None
        try:
            self.one_year_return = oneyear_return
        except:
            self.one_year_return = None

    def getFinancials(self):
        dict = {
            "ticker": self.ticker,
            "price": self.price,
            "eps": self.eps,
            "shares_outstanding": self.shares_outstanding,
            "pe_ratio": self.pe_ratio,
            "last_5yr_earnings": self.last_5yr_earnings,
            "next_5yr_earnings": self.next_5yr_earnings,
            "peg_ratio": self.peg_ratio,
            "ev": self.ev,
            "ebit": self.ebit,
            "earnings_yield": self.earnings_yield,
            "equity_per_share": self.equity_per_share,
            "price_book_ratio": self.price_book_ratio,
            "fcf": self.fcf,
            "last_4yr_fcf_growth": self.last_4yr_fcf_growth,
            "current_assets": self.current_assets,
            "total_assets": self.total_assets,
            "current_liabilities": self.current_liabilities,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "cash": self.cash,
            "current_ratio": self.current_ratio,
            "total_debt_ratio": self.total_debt_ratio,
            "debt_equity_ratio": self.debt_equity_ratio,
            "cash_ratio": self.cash_ratio,
            "net_fixed_assets": self.net_fixed_assets,
            "working_capital": self.working_capital,
            "return_on_capital": self.return_on_capital,
            "interest_expense": self.interest_expense,
            "total_debt": self.total_debt,
            "cost_of_debt": self.cost_of_debt,
            "beta": self.beta,
            "cost_of_equity": self.cost_of_equity,
            "mvoe": self.mvoe,
            "wavg_time_to_maturity": self.wavg_time_to_maturity,
            "movd": self.mvod,
            "wavg_cost_of_capital": self.wavg_cost_of_capital,
            "value_added": self.value_added,
            "intrinsic_value_fcf": self.intrinsic_value_fcf,
            "intrinsic_value_eps": self.intrinsic_value_eps,
            "payout_ratio": self.payout_ratio,
            "one_year_return": self.one_year_return
        }

        return dict

    def runAnalytics(self):
        username = "fluse9"
        password = "allegoryofthecave1"
        dbname = "StockData"
        colname = "Financials"
        host = "mongodb+srv://" + username + ":" + password + "@investmentdata.z4aov.mongodb.net/" + dbname + "?retryWrites=true&w=majority"

        stock_data = list(MongoConnection(host, dbname, colname).collection.find())

        df = pd.DataFrame(stock_data).dropna()
        df['discount_to_fcf'] = np.log1p(df.price / (df.intrinsic_value_fcf / df.shares_outstanding))
        df['discount_to_eps'] = np.log1p(df.price / df.intrinsic_value_eps)

        df = df.dropna()

        df_filtered = df[(df['pe_ratio'] < df['pe_ratio'].quantile(0.99)) & (df['pe_ratio'] > df['pe_ratio'].quantile(0.01))]

        x, y = df[['pe_ratio', 'peg_ratio', 'last_5yr_earnings', 'next_5yr_earnings', 'earnings_yield',
                   'price_book_ratio', 'last_4yr_fcf_growth', 'current_ratio', 'total_debt_ratio', 'debt_equity_ratio',
                   'cash_ratio', 'return_on_capital', 'value_added', 'discount_to_fcf', 'discount_to_eps',
                   'payout_ratio']], df['one_year_return']

        x = sm.add_constant(x)

        model = sm.OLS(y, x)
        results = model.fit()

        print(results.summary())

        return results

    def getStockData(self):
        username = "fluse9"
        password = "allegoryofthecave1"
        dbname = "StockData"
        colname = "Financials"
        host = "mongodb+srv://" + username + ":" + password + "@investmentdata.z4aov.mongodb.net/" + dbname + "?retryWrites=true&w=majority"

        stock_data = list(MongoConnection(host, dbname, colname).collection.find())

        df = pd.DataFrame(stock_data).dropna()
        df['discount_to_fcf'] = np.log1p(df.price / (df.intrinsic_value_fcf / df.shares_outstanding))
        df['discount_to_eps'] = np.log1p(df.price / df.intrinsic_value_eps)
        df = df.dropna()
        df['value_rank'] = df['discount_to_eps'].rank(ascending=True)
        df['future_growth_rank'] = df['next_5yr_earnings'].rank(ascending=False)
        df['roc_rank'] = df['return_on_capital'].rank(ascending=False)
        df['health1_rank'] = df['current_ratio'].rank(ascending=False)
        df['health2_rank'] = df['total_debt_ratio'].rank(ascending=True)
        df['past_growth_rank'] = df['last_5yr_earnings'].rank(ascending=False)
        df['holistic_score'] = 0.5 * df['future_growth_rank'] + 0.2 * df['roc_rank'] + 0.1 * \
                               df['health1_rank'] + 0.1 * df['health2_rank'] + 0.1 * df['past_growth_rank']

        return df

class ValueInvestorBot(object):

    def __init__(self):
        self.main()

    def main(self):
        df = StockData(True).getStockData()

        sorted_df = df.sort_values(['holistic_score'], ascending=[False])
        top_30 = sorted_df[-30:]
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        print(top_30)

        sorted_df.to_csv('E:/InvestmentData1.csv')

ValueInvestorBot()
