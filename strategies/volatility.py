from scipy import optimize
from django.utils import timezone
import pandas as pd
import numpy as np
import warnings
try:
    from strategies.fxcm import FXCM
except:
    from strategies.fxcm import FXCM
from strategies.models import Strategy
import math
from forexconnect import fxcorepy, Common
from strategies.models import backtest
warnings.filterwarnings("ignore")

class Volatility(FXCM):

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, value):
        self._players = value

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, value):
        self._strategy = value

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, value):
        self._account = value

    def __init__(self, account):

        self.account = account
        self.strategy = Strategy.objects.get(name="Volatility")
        self.players = self.strategy.players.filter(enabled=True)
        self.longs = {}
        self.shorts = {}
        self.data = {}
        self.connect()
        account = Common.get_account(self.fxcm)
        if not account:
            raise Exception(
                "The account '{0}' is not valid".format(self.account))
        else:
            self.account = account.account_id
        for player in self.players:

            self.longs.update({player: None})
            self.shorts.update({player: None})
            self.start_trade(player)

    def on_start(self):
        self.strategy = Volatility

    def on_bar(self, player, pricedata):

        if timezone.now().minute % 15 == 0:
            self.run_optimize(player)
        player.refresh_from_db()
        trigger = player.params.get(name="trigger").value
        periods = int(player.params.get(name="periods").value)
        # if player.symbol.ticker not in self.data:
        #     self.data |= {player.symbol.ticker: pricedata}
        # else:
        #     self.data[player.symbol.ticker] = pricedata

        log_ret = pricedata['BidClose'].apply(math.log).diff().mul(100).fillna(0)
        log_ret_accum = log_ret.rolling(periods).sum().fillna(0)
        buy = (log_ret_accum > -trigger) & (log_ret_accum.shift(1) < -trigger)
        sell = (log_ret_accum < trigger) & (log_ret_accum.shift(1) > trigger)
        if buy.iloc[-1]:
            self.close_trades(player.symbol.ticker, fxcorepy.Constants.BUY)
            print(f"{player.symbol.ticker} BUY SIGNAL!")
            self.buy(player.symbol.ticker, is_fx=player.symbol.broker.provider == "FX")

        elif sell.iloc[-1]:
            self.close_trades(player.symbol.ticker, fxcorepy.Constants.SELL)
            print(f"{player.symbol.ticker} SELL SIGNAL!")
            self.sell(player.symbol.ticker, is_fx=player.symbol.broker.provider == "FX")





        # print(f"{str(timezone.datetime.now())} {player.symbol.ticker}: {player.timeframe.full_name} Volatility:{log_ret_accum.iloc[-1]}...")

    def run_optimize(self, player):
        bounds = ((15,60),(0,1))
        ticker = self.transform_ticker(player.symbol.ticker)
        data = pd.DataFrame(self.fxcm.get_history(ticker, player.timeframe.name, quotes_count=2000))
        data = data.reset_index()
        data = data.drop("Date", axis=1)
        # res = optimize.shgo(lambda x: backtest(data.BidClose, x[0], x[1]), bounds, n=200, iters=5,sampling_method='sobol')
        res = optimize.dual_annealing(lambda x: backtest(data.BidClose, x[0], x[1]), bounds)

        if res.success:
            print(f"{player.symbol.ticker}: Optimization Success")
            player.params.filter(name="periods").update(value=int(res.x[0]))
            player.params.filter(name="trigger").update(value=res.x[1])
            return True
        return False


if __name__ == "__main__":
    Volatility(account=1571013)
    input("Done! Press enter key to exit\n")
