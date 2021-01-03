import alpaca_trade_api as tradeapi

key = "PKDMJ3EFG7K6RBAQNPT3"
sec = "gogIZwlzCnbkBbxcdBWPdiUxrrRJDyoPNR88GO4K"

#API endpoint URL
url = "https://paper-api.alpaca.markets"

#api_version v2 refers to the version that we'll use
#very important for the documentation
api = tradeapi.REST(key, sec, url, api_version='v2')

#Init our account var
account = api.get_account()