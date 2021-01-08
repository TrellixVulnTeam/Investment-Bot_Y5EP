import alpaca_trade_api as tradeapi
import yahoo_fin.stock_info as si
import time

class AlpacaBot(object):


    def __init__(self):
        self.stocks = []

        self.stock = {
            'PREVIOUS_EMA12': None,
            'EMA12': None,
            'EMA26': None,
            'EMA50': None,
            'EMA200': None,
            'MACD': [],
            'SIGNAL': None
        }

        self.Closing_Levels = []
        self.Period_5ROC = []
        self.Period_15ROC = []
        self.Period_25ROC = []
        self.Sum_ROC = []

        self.ROC_TABLE = {
            'CLOSE': self.Closing_Levels,
            '5_PERIOD_ROC': self.Period_5ROC,
            '15_PERIOD_ROC': self.Period_15ROC,
            '25_PERIOD_ROC': self.Period_25ROC,
            'SUM_ROC': self.Sum_ROC,
        }
        self.setup()
        self.tripleMomentum()

    def setup(self):
        key = "PKDMJ3EFG7K6RBAQNPT3"
        sec = "gogIZwlzCnbkBbxcdBWPdiUxrrRJDyoPNR88GO4K"

        # API endpoint URL
        url = "https://paper-api.alpaca.markets"

        # api_version v2 refers to the version that we'll use
        # very important for the documentation
        api = tradeapi.REST(key, sec, url, api_version='v2')

        # Init our account var
        account = api.get_account()

        # sp500_list = si.tickers_sp500()
        sp500_list = si.tickers_sp500()

        for i in range(len(sp500_list)):
            if (i % 10 == 0):
                dict = {
                    'ticker': sp500_list[i],
                    'closing_levels': [],
                    'period_5roc': [],
                    'period_15roc': [],
                    'period_25roc': [],
                    'sum_roc': []
                }
                self.stocks.append(dict)

    def divergence(self):
        key = "PKDMJ3EFG7K6RBAQNPT3"
        sec = "gogIZwlzCnbkBbxcdBWPdiUxrrRJDyoPNR88GO4K"

        #API endpoint URL
        url = "https://paper-api.alpaca.markets"

        #api_version v2 refers to the version that we'll use
        #very important for the documentation
        api = tradeapi.REST(key, sec, url, api_version='v2')

        #Init our account var
        account = api.get_account()

        sp500_list = si.tickers_sp500()

        while True:
            for i in range(len(sp500_list)):
                ticker = sp500_list[i]
                stock = api.get_barset(ticker, '1Min', limit=200)

                current_price = api.get_last_trade(ticker).price
                current_change = current_price - stock.df.__getattr__(ticker).close.iat[-1]
                if (current_change < 0):
                    current_loss = current_change
                    current_gain = 0
                elif (current_change > 0):
                    current_loss = 0
                    current_gain = current_change
                else:
                    current_loss = 0
                    current_gain = 0

                previous_close = stock.df.__getattr__(ticker).close.iat[-1]
                MA10 = (stock.df.__getattr__(ticker).close.tail(9).sum() + current_price) / 10
                MA20 = (stock.df.__getattr__(ticker).close.tail(19).sum() + current_price) / 20
                MA21 = (stock.df.__getattr__(ticker).close.tail(20).sum()) / 20
                MA50 = (stock.df.__getattr__(ticker).close.tail(49).sum() + current_price) / 50
                MA100 = (stock.df.__getattr__(ticker).close.tail(99).sum() + current_price) / 100
                MA200 = (stock.df.__getattr__(ticker).close.tail(199).sum() + current_price) / 200



                if (self.stock['EMA12'] == None):
                    self.stock['EMA12'] = current_price * (2 / (1 + 12)) + (stock.df.__getattr__(ticker).close.tail(12).sum() / 12) * (1 - (2 / (1 + 12)))
                    self.stock['EMA26'] = current_price * (2 / (1 + 26)) + (stock.df.__getattr__(ticker).close.tail(26).sum() / 26) * (1 - (2 / (1 + 26)))
                    self.stock['EMA50'] = current_price * (2 / (1 + 50)) + (stock.df.__getattr__(ticker).close.tail(50).sum() / 50) * (1 - (2 / (1 + 50)))
                    self.stock['EMA200'] = current_price * (2 / (1 + 200)) + (stock.df.__getattr__(ticker).close.tail(200).sum() / 200) * (1 - (2 / (1 + 200)))
                else:
                    self.stock['PREVIOUS_EMA12'] = self.stock['EMA12']
                    self.stock['EMA12'] = current_price * (2 / (1 + 12)) + (self.stock['PREVIOUS_EMA12']) * (1 - (2 / (1 + 12)))
                    self.stock['EMA26'] = current_price * (2 / (1 + 26)) + (self.stock['EMA26']) * (1 - (2 / (1 + 26)))
                    self.stock['EMA50'] = current_price * (2 / (1 + 50)) + (self.stock['EMA50']) * (1 - (2 / (1 + 50)))
                    self.stock['EMA200'] = current_price * (2 / (1 + 200)) + (self.stock['EMA200']) * (1 - (2 / (1 + 200)))

                MACD = self.stock['EMA12'] - self.stock['EMA26']
                self.stock['MACD'].append(MACD)

                if (len(self.stock['MACD']) > 9):
                    self.stock['MACD'].pop(0)

                if (self.stock['SIGNAL'] == None and len(self.stock['MACD']) == 9):
                    sum = 0
                    for i in range(9):
                        sum += self.stock['MACD'][i]
                    SMA = sum / 9
                    self.stock['SIGNAL'] = MACD * (2 / (1 + 9)) + (SMA) * (1 - (2 / (1 + 9)))
                elif (self.stock['SIGNAL'] != None):
                    self.stock['SIGNAL'] = MACD * (2 / (1 + 9)) + (self.stock['SIGNAL']) * (1 - (2 / (1 + 9)))

                list = stock.df.__getattr__(ticker).close.tail(14).to_numpy()

                loser_count = 0
                gainer_count = 0
                losses = 0
                gains = 0
                for i in range(len(list) - 1):
                    if (list[i + 1] < list[i]):
                        loser_count += 1
                        losses += abs(list[i + 1] - list[i])
                    if (list[i + 1] > list[i]):
                        gainer_count += 1
                        gains += abs(list[i + 1] - list[i])

                if (gainer_count > 0):
                    avg_gain = gains / gainer_count
                else:
                    avg_gain = 0
                if (loser_count > 0):
                    avg_loss = losses / loser_count
                else:
                    avg_loss = 0

                rs = ((avg_gain * 13 + current_gain) / 14) / ((avg_loss * 13 + current_loss) / 14)
                rsi = 100 - (100 / (1 + rs))
                '''
                #Reversals Method
                if (current_price > MA10 and previous_close < MA10 and rsi < 40):
                    #api.submit_order(ticker, 1, 'buy', 'market', 'day')
                    pass

                #Momentum Method
                if (MA20 > MA200 and MA21 < MA200 and rsi > 70):
                    api.submit_order(ticker, 1, 'buy', 'market', 'day')
                    print(ticker + ' buy')
                try:
                    if (MA20 < MA200 and MA21 > MA200 and int(api.get_position(ticker).qty) > 0):
                        qty = int(api.get_position(ticker).qty)
                        api.submit_order(ticker, qty, 'sell', 'market', 'day')
                        print(ticker + ' sell')
                except:
                    pass
                '''

                # Divergence Method
                if (self.stock['SIGNAL'] != None):
                    if (self.stock['MACD'][8] > self.stock['SIGNAL'] and self.stock['MACD'][7] < self.stock['SIGNAL'] and int(api.get_position(ticker).qty) == 0):
                        api.submit_order(ticker, 1, 'buy', 'market', 'day')
                        print(ticker + ' buy')
                    try:
                        if (self.stock['MACD'][8] < self.stock['SIGNAL'] and self.stock['EMA12'] - self.stock['PREVIOUS_EMA12'] <= 0 and int(api.get_position(ticker).qty) > 0):
                            qty = int(api.get_position(ticker).qty)
                            api.submit_order(ticker, qty, 'sell', 'market', 'day')
                            print(ticker + ' sell')
                    except:
                        pass

    def tripleMomentum(self):
        key = "PKDMJ3EFG7K6RBAQNPT3"
        sec = "gogIZwlzCnbkBbxcdBWPdiUxrrRJDyoPNR88GO4K"

        #API endpoint URL
        url = "https://paper-api.alpaca.markets"

        #api_version v2 refers to the version that we'll use
        #very important for the documentation
        api = tradeapi.REST(key, sec, url, api_version='v2')

        #Init our account var
        account = api.get_account()

        #sp500_list = si.tickers_sp500()
        sp500_list = si.tickers_sp500()

        while True:
            for i in range(len(self.stocks)):
                ticker = sp500_list[i]
                stock = api.get_barset(ticker, '1Min', limit=26)

                closing_levels = stock.df.__getattr__(ticker).close.to_numpy()

                self.stocks[i]['closing_levels'].append(closing_levels[25])
                self.stocks[i]['period_25roc'].append((closing_levels[25] - closing_levels[0]) / closing_levels[0])
                self.stocks[i]['period_15roc'].append((closing_levels[25] - closing_levels[10]) / closing_levels[0])
                self.stocks[i]['period_5roc'].append((closing_levels[25] - closing_levels[20]) / closing_levels[0])
                self.stocks[i]['sum_roc'].append(self.stocks[i]['period_25roc'][-1] + self.stocks[i]['period_15roc'][-1] + self.stocks[i]['period_5roc'][-1])

                if (len(self.stocks[i]['sum_roc']) > 2):
                    self.stocks[i]['closing_levels'].pop(0)
                    self.stocks[i]['period_25roc'].pop(0)
                    self.stocks[i]['period_15roc'].pop(0)
                    self.stocks[i]['period_5roc'].pop(0)
                    self.stocks[i]['sum_roc'].pop(0)

                if (len(self.stocks[i]['sum_roc']) == 2):
                    try:
                        if (self.stocks[i]['sum_roc'][1] > 0.001 and self.stocks[i]['sum_roc'][0] < 0.0001):
                            api.submit_order(ticker, 1, 'buy', 'market', 'day')
                            print(ticker + ' buy')
                        elif (self.stocks[i]['sum_roc'][1] < 0.0001 and self.stocks[i]['sum_roc'][0] > 0.0001 and int(api.get_position(ticker).qty) > 0):
                            qty = int(api.get_position(ticker).qty)
                            api.submit_order(ticker, qty, 'sell', 'market', 'day')
                            print(ticker + ' sell')
                    except:
                        pass
            print('sleeping...')
            time.sleep(55)

AlpacaBot()
