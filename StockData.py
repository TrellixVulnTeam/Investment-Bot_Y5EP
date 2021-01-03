import Databases
import pandas as pd
import numpy as np

class StockData(object):

    def __init__(self, ticker):
        username = "fluse9"
        password = "allegoryofthecave1"
        dbname = "StockData"
        colname = "Financials"
        host = "mongodb+srv://" + username + ":" + password + "@investmentdata.z4aov.mongodb.net/" + dbname + "?retryWrites=true&w=majority"
        self.col = Databases.MongoConnection(host, dbname, colname).collection
        self.main(ticker)

    def main(self, ticker):
        stock_data = list(self.col.find_one({ 'ticker': ticker }))
        df = pd.DataFrame(stock_data)
        df['discount_to_fcf'] = np.log1p(df.price / (df.intrinsic_value_fcf / df.shares_outstanding))
        df['discount_to_eps'] = np.log1p(df.price / df.intrinsic_value_eps)

        return df