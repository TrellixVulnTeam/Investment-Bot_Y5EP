from pyrh import Robinhood

class RobinhoodBot(object):
    enteredTrade = None

    def __init__(self, stock, action, quantity):
        self.enteredTrade = False
        self.main(stock, action, quantity)

    def main(self, stock, action, quantity):
        username = ""
        password = ""

        rh = Robinhood()
        rh.login(username=username, password=password)

        instrument = rh.instruments(stock)[0]

        if (action == "buy"):
            rh.place_buy_order(instrument, quantity)
            self.enteredTrade = True

        if (action == "sell"):
            rh.place_sell_order(instrument, quantity)
            self.enteredTrade = False