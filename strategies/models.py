import matplotlib.pyplot as plt
from django.db import models
from marketdata.models import Symbol
from django.core.validators import MinValueValidator
import pandas as pd
import numpy as np
import math
from .utils import sharpe_ratio


# Create your models here.


class Timeframe(models.Model):
    full_name = models.CharField(max_length=10)
    name = models.CharField(max_length=10)
    resample = models.CharField(max_length=10)

    def __str__(self):
        return self.full_name


class VolatilityManager(models.Manager):

    def run_backtests(self):
        print("Atualizando Cotações...", sep=" ")
        Symbol.objects.update_all_from_tradingview(5000)
        print("Feito!")
        print("Realizando Backtests...")
        for volatility in self.all():
            print(f"Ativo:{volatility.symbol.ticker} TimeFrame:{volatility.timeframe.full_name}...", sep=' ')
            volatility.backtest(plot=False)
            print("Feito!")


class Strategy(models.Model):
    timeframe = models.ForeignKey(Timeframe, on_delete=models.CASCADE, related_name="strategies")

    class Meta:
        abstract = True


class Volatility(Strategy):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="vols")
    log_periods = models.PositiveIntegerField(default=20)
    trigger = models.FloatField(default=0.25, validators=[MinValueValidator(0)])
    factor = models.FloatField(default=0.25)
    sharpe = models.FloatField(default=0)
    signal = models.IntegerField(default=0)

    objects = VolatilityManager()

    class Meta:
        verbose_name_plural = "Volatilities"

    def __str__(self):
        return f'{self.symbol.ticker}: {self.sharpe}'

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
        signals = pd.Series(np.zeros(log_ret.shape[0]))
        if buy.iloc[-1]:
            self.signal = 1
        elif sell.iloc[-1]:
            self.signal = -1
        signals[buy.values] = 1
        signals[sell.values] = -1
        signals[signals == 0] = np.nan
        signals = signals.ffill().fillna(0)
        returns = data.close.diff()
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
