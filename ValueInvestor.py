import MarketData as StockData
import pandas as pd

class ValueInvestor(object):

    def __init__(self):
        self.main()

    def main(self):
        df = StockData.MarketData(True).getMarketData()

        sorted_df = df.sort_values(['holistic_score'], ascending=[False])
        top_30 = sorted_df[-30:]
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        print(top_30)

        sorted_df.to_csv('E:/InvestmentData1.csv')