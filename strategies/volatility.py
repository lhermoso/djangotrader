import multiprocessing as mp
import warnings

import numpy as np
import pandas as pd
from django.utils import timezone
from scipy import optimize

from strategies.utils import sharpe_ratio

try:
    from strategies.fxcm import FXCM
except:
    from strategies.fxcm import FXCM
from strategies.models import Strategy
import math
from forexconnect import Common

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

    def __init__(self, account, run_opt=False):

        super().__init__()
        self.account = account
        self.strategy = Strategy.objects.get(name="Volatility")
        self.players = self.strategy.players.filter(enabled=True)
        self.connect()
        account = Common.get_account(self.fxcm)
        if not account:
            raise Exception(
                "The account '{0}' is not valid".format(self.account))
        else:
            self.account = account.account_id

        for player in self.players:
            if run_opt:
                self.run_optimize(player)
            else:
                self.start_trade(player)

        if run_opt:
            self.fxcm.logout()

    def on_start(self):
        self.strategy = Volatility

    def signal(self, data, periods, trigger, exit_trigger, is_opt=False):
        periods = int(periods)
        log_ret = data.apply(math.log).diff().mul(100).fillna(0)
        log_ret_accum = log_ret.rolling(periods).sum().fillna(0)
        buy = (log_ret_accum > -trigger) & (log_ret_accum.shift(1) < -trigger)
        sell = (log_ret_accum < trigger) & (log_ret_accum.shift(1) > trigger)
        exit_long = log_ret_accum > exit_trigger
        exit_short = log_ret_accum < -exit_trigger
        signals = pd.Series(np.zeros(log_ret.shape[0]))

        signals[buy.values] = 1
        signals[sell.values] = -1
        signals[signals == 0] = np.nan
        signals[(exit_long.values) | (exit_short.values)] = 0


        if is_opt:
            signals = signals.ffill().fillna(0)
            num_trades = buy.sum() + sell.sum()
            returns = data.pct_change()
            returns_port = returns.shift(-1).multiply(signals.values, axis=0)
            sharpe = sharpe_ratio(returns_port) * -1 * num_trades ** (1 / 2)
            return 0 if np.isnan(sharpe) else sharpe
        else:

            return signals.iloc[-1]

    def on_bar(self, player, pricedata):


        player.refresh_from_db()
        trigger = player.params.get(name="trigger").value
        periods = int(player.params.get(name="periods").value)
        exit_trigger = player.params.get(name="exit_trigger").value
        signal = self.signal(pricedata['BidClose'], periods, trigger, exit_trigger)

        if signal == 1:
            print(f"{player.symbol.ticker} BUY SIGNAL!")
            self.close_shorts(player.symbol.ticker)
            self.buy(player)

        elif signal == -1:
            print(f"{player.symbol.ticker} SELL SIGNAL!")
            self.close_longs(player.symbol.ticker)
            self.sell(player)

        else:
            self.close_longs(player.symbol.ticker)
            self.close_shorts(player.symbol.ticker)
        # print(
        #     f"{str(timezone.datetime.now())} {player.symbol.ticker}: {player.timeframe.full_name} signal:{signal}")

    def run_optimize(self, player, run=True):
        if run:
            print(f"{player.symbol.ticker}: Starting Optimization...")
            bounds = ([15, 60], [0, 1], [0, 1])
            ticker = self.transform_ticker(player.symbol.ticker)
            data = pd.DataFrame(self.fxcm.get_history(ticker, player.timeframe.name, quotes_count=5000))
            data = data.reset_index()
            data = data.drop("Date", axis=1)
            res = optimize.dual_annealing(lambda x: self.signal(data.BidClose, x[0], x[1], x[2], True), bounds)

            if res.success:
                print(f"{player.symbol.ticker}: Optimization Success")
                periods = int(res.x[0])
                trigger = res.x[1]
                exit_trigger = res.x[2]
                player.params.filter(name="periods").update(value=periods)
                player.params.filter(name="trigger").update(value=trigger)
                player.params.filter(name="exit_trigger").update(value=exit_trigger)
            print(f"{player.symbol.ticker}: Starting Optimization done")


if __name__ == "__main__":
    Volatility(account=1571013)
    input("Done! Press enter key to exit\n")
