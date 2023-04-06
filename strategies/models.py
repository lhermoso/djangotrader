import math
import time

import fxcmpy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from django.db import models
from scipy import optimize

from marketdata.models import Symbol
from .utils import sharpe_ratio

longs = None
shorts = None

fxcm_connection = None
pricedata = None
from django.utils import timezone


# Create your models here.


class Timeframe(models.Model):
    full_name = models.CharField(max_length=10)
    name = models.CharField(max_length=10)
    resample = models.CharField(max_length=10)

    def __str__(self):
        return self.full_name


class PlayerManager(models.Manager):

    def run_backtests(self):
        print("Atualizando Cotações...", sep=" ")
        Symbol.objects.update_all_from_tradingview(5000)
        print("Feito!")
        print("Realizando Backtests...")
        for volatility in self.filter(strategy__name="volatility"):
            print(f"Ativo:{volatility.symbol.ticker} TimeFrame:{volatility.timeframe.full_name}...", sep=' ')
            volatility.backtest(plot=False)
            print("Feito!")


class Strategy(models.Model):
    name = models.CharField("Strategy Name", max_length=250, unique=True)
    potential_text = models.CharField(max_length=100, null=True, default="Potential")
    trigger_text = models.CharField(max_length=100, null=True, default="Signal")
    description = models.TextField(null=True)
    enabled = models.BooleanField(default=True)
    multi_timeframe = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Strategies"

    def __str__(self):
        return self.name


class Player(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="players")
    timeframe = models.ForeignKey(Timeframe, on_delete=models.CASCADE, related_name="players")
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="players")
    factor = models.FloatField(default=0.25)
    sharpe = models.FloatField(default=0)
    signal = models.IntegerField(default=0)
    enabled = models.BooleanField(default=False)

    objects = PlayerManager()

    class Meta:
        verbose_name_plural = "Players"

    def __str__(self):
        return f'{self.symbol.ticker}: {self.sharpe}'

    def on_start(self):
        global fxcm_connection
        global pricedata

        if fxcm_connection is None:
            fxcm_connection = fxcmpy.fxcmpy(access_token='cfc5bbee9b20c01474c018e3753f36e3d1ec91c5', log_level='error',
                                            log_file='log.txt', server='demo')

        symbol = f'{self.symbol.ticker[:3]}/{self.symbol.ticker[3:]}'
        numberofcandles = 300
        timeframe = "m1"
        pricedata = fxcm_connection.get_candles(symbol, period=timeframe, number=numberofcandles)
        while True:
            currenttime = timezone.datetime.now()
            if timeframe == "m1" and currenttime.second == 0 and self.get_last_pricedata(timeframe, numberofcandles,
                                                                                         symbol):
                self.on_bar(timeframe, symbol)
            time.sleep(1)

    def on_bar(self, timeframe, symbol):
        global pricedata
        global longs
        global shorts

        print(str(timezone.datetime.now()) + " " + timeframe + " Bar Closed - Running Update Function...")
        log_ret = (pricedata.bidclose.apply(math.log).diff(1) * 100).fillna(0)
        log_ret_accum = log_ret.rolling(self.log_periods).sum().fillna(0)
        buy = (log_ret_accum > -self.trigger) & (log_ret_accum.shift(1) < -self.trigger)
        sell = (log_ret_accum < self.trigger) & (log_ret_accum.shift(1) > self.trigger)
        if buy.iloc[-1]:
            print("	  BUY SIGNAL!")
            if longs is None:
                fxcm_connection.close_all_for_symbol(symbol=symbol)
                shorts = None
            longs = fxcm_connection.open_trade(symbol=symbol, amount=1, is_buy=True, time_in_force="GTC",
                                               order_type="AtMarket")

        elif sell.iloc[-1]:
            print("	  SELL SIGNAL!")
            if shorts is None:
                fxcm_connection.close_all_for_symbol(symbol=symbol)
                longs = None

            shorts = fxcm_connection.open_trade(symbol=symbol, amount=1, is_buy=False, time_in_force="GTC",
                                                order_type="AtMarket")

    def get_last_pricedata(self, timeframe, numberofcandles, symbol):
        global pricedata

        # Normal operation will update pricedata on first attempt
        new_pricedata = fxcm_connection.get_candles(symbol, period=timeframe, number=numberofcandles)
        if new_pricedata.index.values[len(new_pricedata.index.values) - 1] != pricedata.index.values[
            len(pricedata.index.values) - 1]:
            pricedata = new_pricedata
            return True

    def generate_signal(self):
        data = self.symbol.get_quotes(timeframe=self.timeframe, lookback="YTD")
        log_ret = (data.close.apply(math.log).diff(1) * 100).fillna(0)
        log_ret_accum = log_ret.rolling(self.log_periods).sum().fillna(0)
        buy = (log_ret_accum > -self.trigger) & (log_ret_accum.shift(1) < -self.trigger)
        sell = (log_ret_accum < self.trigger) & (log_ret_accum.shift(1) > self.trigger)

        if buy.iloc[-1]:
            self.signal = 1
            self.save()
        elif sell.iloc[-1]:
            self.signal = -1
            self.save()

    def backtest(self, plot=False):
        data = self.symbol.get_quotes(timeframe=self.timeframe.resample)
        log_ret = (data.close.apply(math.log).diff(1) * 100).fillna(0)
        log_ret_accum = log_ret.rolling(self.log_periods).sum().fillna(0)
        buy = (log_ret_accum > -self.trigger) & (log_ret_accum.shift(1) < -self.trigger)
        sell = (log_ret_accum < self.trigger) & (log_ret_accum.shift(1) > self.trigger)
        buy = buy.shift(1).fillna(False)
        sell = sell.shift(1).fillna(False)
        signals = pd.Series(np.zeros(log_ret.shape[0]))
        if buy.iloc[-1]:
            self.signal = 1
        elif sell.iloc[-1]:
            self.signal = -1
        signals[buy.values] = 1
        signals[sell.values] = -1
        signals[signals == 0] = np.nan
        signals = signals.ffill().fillna(0)
        returns = data.pct_change()
        returns_port = returns.multiply(signals.values, axis=0)
        returns_port_accum = returns_port.cumsum() * self.symbol.standard_lot
        sharpe = sharpe_ratio(returns_port)
        self.sharpe = sharpe
        if sharpe > 3:
            self.factor = 1
        elif sharpe > 2:
            self.factor = 0.5
        elif sharpe > 1.5:
            self.factor = 0.3
        self.save()
        print(f"Sharpe Ratio Anualizado:{sharpe}")

        if plot:
            returns_port_accum.plot(figsize=(20, 10))
            plt.title(f"{self.symbol.name} | Retornos Acumulados| Sharpe Ratio {round(sharpe, 2)}")
            plt.show()
        return signals


class Param(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="params")
    name = models.CharField(max_length=250)
    value = models.FloatField()

    def __str__(self):
        return f'{self.name}:{self.value}'


def run_optimize():
    bounds = optimize.Bounds([3, 0], [40, 1])
    for player in Player.objects.filter(enabled=True):
        data = player.symbol.get_quotes("1min")
        data = data.reset_index()
        data = data.drop("date", axis=1)
        res = optimize.dual_annealing(lambda x: backtest(data.close, x[0], x[1]), bounds)
        player.params.filter(name="periods").update(value=int(res.x[0]))
        player.params.filter(name="trigger").update(value=res.x[1])


def backtest(data, periods, trigger,exit_trigger, plot=False):
    if np.isnan(periods) or np.isnan(trigger):
        return 50
    periods = int(periods)
    log_ret = data.apply(math.log).diff(1).mul(100).fillna(0)
    log_ret_accum = log_ret.rolling(periods).sum().fillna(0)
    buy = (log_ret_accum > -trigger) & (log_ret_accum.shift(1) < -trigger)
    sell = (log_ret_accum < trigger) & (log_ret_accum.shift(1) > trigger)
    exit_long = log_ret_accum > exit_trigger
    exit_short = log_ret_accum < -exit_trigger
    signals = pd.Series(np.zeros(log_ret.shape[0]))
    num_trades = buy.sum() + sell.sum()
    signals[buy.values] = 1
    signals[sell.values] = -1
    signals[signals == 0] = np.nan
    signals[(exit_long.values) | (exit_short.values)] = 0
    signals = signals.ffill().fillna(0)
    returns = data.pct_change()
    returns_port = returns.shift(-1).multiply(signals.values, axis=0)
    if plot:
        returns_port_accum = returns_port.cumsum()
        fig, axs = plt.subplots(2)
        axs[0].plot(returns_port_accum)
        axs[1].plot(log_ret_accum)
        axs[1].axhline(y=trigger, color='r', linestyle='-')
        axs[1].axhline(y=-trigger, color='r', linestyle='-')
        axs[1].axhline(y=exit_trigger, color='b', linestyle='-')
        axs[1].axhline(y=-exit_trigger, color='b', linestyle='-')
        plt.show()
    sharpe = sharpe_ratio(returns_port) * -1 * num_trades ** (1/2)
    return 0 if np.isnan(sharpe) else sharpe
