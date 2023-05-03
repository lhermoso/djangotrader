import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import optimize
from scipy.stats import linregress

from strategies.utils import sharpe_ratio

try:
    from strategies.fxcm import FXCM
except SystemError:
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

    def __init__(self, account, run_opt=False, trade=True):

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
            self.orders.update({player: {"Long": False, "Short": False}})
            if run_opt:
                self.run_optimize(player)
            elif trade:
                self.start_trade(player)

        if run_opt:
            self.fxcm.logout()

    def on_start(self):
        self.strategy = Volatility

    def signal(self, data, periods, trigger, exit_trigger, cost=0.1, is_opt=False, plot=False):
        cost /= 100
        if np.isnan(periods):
            return 0
        periods = int(periods)
        exit_level = trigger * (1 + exit_trigger)
        log_ret = data.apply(math.log).diff().mul(100).fillna(0)
        log_ret_accum: np.ndarray = log_ret.rolling(periods).sum().fillna(0)
        buy: pd.Series = (log_ret_accum > -trigger) & (log_ret_accum.shift(1) < -trigger)
        sell: pd.Series = (log_ret_accum < trigger) & (log_ret_accum.shift(1) > trigger)
        exit_long: pd.Series = log_ret_accum > exit_level
        exit_short: pd.Series = log_ret_accum < -exit_level
        signals = pd.Series(np.zeros(log_ret.shape[0]))
        signals[buy.values] = 1
        signals[sell.values] = -1
        signals[signals == 0] = np.nan
        signals[exit_long.values | exit_short.values] = 0
        if is_opt or plot:
            signals = signals.ffill().fillna(0)
            cost = signals.diff().abs().fillna(0) * cost / 2
            returns = data.pct_change()
            returns_port = returns.shift(-1).multiply(signals.values, axis=0).sub(cost).ffill().fillna(0)
            sharpe = sharpe_ratio(returns_port)
            returns_port_accum = returns_port.add(1).cumprod().sub(1) * 100
            if sharpe > 0:
                result = linregress(returns_port_accum.index, returns_port_accum.values)
                sharpe *= math.degrees(math.atan(result.slope)) * result.rvalue
            sharpe *= -1
            if plot:
                returns_port_accum.plot(figsize=(20, 10))
                plt.title(f"Retornos Acumulados| Sharpe Ratio {round(sharpe * -1, 2)}")
                plt.show()
                return
            return 0 if np.isnan(sharpe) else sharpe
        else:
            return signals

    def get_signal(self, player, price_data=None, plot=False):
        player.refresh_from_db()
        if price_data is None:
            price_data = self.get_data(player)

        trigger = player.params.get(name="trigger").value
        periods = int(player.params.get(name="periods").value)
        exit_trigger = player.params.get(name="exit_trigger").value
        signals = self.signal(price_data['BidClose'], periods, trigger, exit_trigger, plot=plot)
        if plot:
            return

        if player.signal == 0:
            return signals.iloc[-1]

        signals = signals.ffill().fillna(0)
        return signals.iloc[-1]

    def plot(self, player):
        self.get_signal(player, plot=True)

    def run_optimize(self, player, run=True):
        if run:
            print(f"{player.symbol.ticker}: Starting Optimization...")
            bounds = ([15, 120], [0, 1], [0, 0.3])
            data = self.get_data(player)
            res = optimize.dual_annealing(
                lambda x: self.signal(data.BidClose, x[0], x[1], x[2], is_opt=True, cost=0.1), bounds)
            if res.success:
                print(f"{player.symbol.ticker}: Optimization Success")
                periods = int(res.x[0])
                trigger = res.x[1]
                exit_trigger = res.x[2]
                player.params.update_or_create(name="periods", defaults={"value": periods})
                player.params.update_or_create(name="trigger", defaults={"value": trigger})
                player.params.update_or_create(name="exit_trigger", defaults={"value": exit_trigger})
            sharpe = res.fun * -1
            player.refresh_from_db()
            player.factor = 1
            if sharpe is None or sharpe < 1:
                player.factor = 0
            if sharpe is not None:
                player.sharpe = sharpe
            player.save()
            print(f"{player.symbol.ticker}: Starting Optimization done! Sharpe: {round(sharpe, 2)}")

    def on_bar(self, player, price_data):
        signal = self.get_signal(player, price_data)
        if signal == 1 and not self.orders[player]["Long"] and player.factor > 0:
            print(f"{player.symbol.ticker} BUY SIGNAL!")
            self.close_shorts(player.symbol.ticker)
            self.buy(player, amount=player.lot_size)
            self.orders[player]["Long"] = True
            self.orders[player]["Short"] = False
            player.signal = signal

        elif signal == -1 and not self.orders[player]["Short"] and player.factor > 0:
            print(f"{player.symbol.ticker} SELL SIGNAL!")
            self.close_longs(player.symbol.ticker)
            self.sell(player, amount=player.lot_size)
            self.orders[player]["Long"] = False
            self.orders[player]["Short"] = True
            player.signal = signal

        elif signal == 0 or player.factor == 0:
            self.close_longs(player.symbol.ticker)
            self.close_shorts(player.symbol.ticker)
            self.orders[player]["Long"] = False
            self.orders[player]["Short"] = False
            player.signal = 0
        player.save()


if __name__ == "__main__":
    Volatility(account=1571013)
    input("Done! Press enter key to exit\n")
