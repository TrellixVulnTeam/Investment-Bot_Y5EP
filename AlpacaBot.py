import alpaca_trade_api as tradeapi
import yahoo_fin.stock_info as si

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
for ticker in sp500_list:

    stock = api.get_barset(ticker, 'day', limit=500)

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

    MA10 = (stock.df.__getattr__(ticker).close.tail(9).sum() + current_price) / 10
    MA20 = (stock.df.__getattr__(ticker).close.tail(19).sum() + current_price) / 20
    MA50 = (stock.df.__getattr__(ticker).close.tail(49).sum() + current_price) / 50
    MA100 = (stock.df.__getattr__(ticker).close.tail(99).sum() + current_price) / 100
    MA200 = (stock.df.__getattr__(ticker).close.tail(199).sum() + current_price) / 200

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

    avg_gain = gains / gainer_count
    avg_loss = losses / loser_count

    rs = ((avg_gain * 13 + current_gain) / 14) / ((avg_loss * 13 + current_loss) / 14)

    rsi = 100 - (100 / (1 + rs))

    #Reversals Method
    if ((current_price - MA10) > 0 and ((current_price - MA10) / current_price) < 0.01 and rsi < 40):
        #api.submit_order(ticker, 1, 'buy', 'market', 'day')
        print(ticker)

    #Momentum Method
    if ((current_price - MA200) > 0 and ((current_price - MA200) / current_price) < 0.01 and rsi > 70):
        #api.submit_order(ticker, 1, 'buy', 'market', 'day')
        print(ticker)