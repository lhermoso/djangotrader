from django.db import models
from django import db
import multiprocessing
from django.utils import timezone
from django.db.models import Q
import numpy as np
import yfinance as yf
from django_pandas.io import read_frame
import pandas as pd
import pytz
from django.apps import apps
from tvDatafeed import Interval

from .tradingview import Historic, RealTime

TRADINGVIEW_CHOICES = (("1", "forex"),
                       ("2", 'stock'),
                       ("3", 'futures'),
                       ("4", 'cfd'),
                       ("5", 'crypto'),
                       )


class SymbolManager(models.Manager):

    def update_all_from_tradingview(self, num_bars=1, interval=Interval.in_1_hour):
        symbols = self.filter(Q(category="1") | Q(category="2"))
        historic = Historic(symbols=symbols)
        historic.update_all_symbols(num_bars, interval)


# Create your models here.
class QuoteManager(models.Manager):

    def create_timestamp(self):

        quotes = Quote.objects.filter(date_timestamp=0)
        db.connections.close_all()
        pool = multiprocessing.Pool(5)
        pool.map(self._create_ts, quotes)

    def _create_ts(self, quote):
        # quote.date_timestamp = int(timezone.datetime.timestamp(
        #     timezone.datetime.combine(quote.date, timezone.datetime.min.time()))) * 1000
        quote.date_timestamp = timezone.datetime.timestamp(quote.date) * 1000
        quote.save()

    def update_from_yahoo(self):
        symbols = Symbol.objects.filter(Q(category="1") | Q(category="2"))
        for symbol in symbols:
            suffix = ".SA" if symbol.category == "2" else "=X"
            ticker = yf.Ticker(f'{symbol.ticker}{suffix}')
            quotes = []
            history = ticker.history(period="7d", interval="1m")
            history.replace([np.inf, -np.inf], np.nan, inplace=True)
            for index in range(history.shape[0]):
                data = history.iloc[index]
                quote = Quote(date=data.name, open=data.Open, high=data.High, low=data.Low, close=data.Close,
                              volume=data.Volume, symbol=symbol)
                quotes.append(quote)

            Quote.objects.bulk_create(quotes, ignore_conflicts=True)


class Broker(models.Model):
    provider = models.CharField(max_length=250)

    def __str__(self):
        return self.provider

    class Meta:
        verbose_name_plural = "Corretoras"


class Category(models.Model):
    name = models.CharField(max_length=50)
    yahoo_suffix = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categorias"


class Symbol(models.Model):
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, related_name="symbols", blank=True)
    ticker = models.CharField(max_length=150)
    name = models.CharField(max_length=150, blank=True)
    currency = models.CharField(max_length=3, default="BRL")
    country = models.CharField(max_length=3, default="BR")
    digits = models.IntegerField(default=5)
    standard_lot = models.IntegerField(default=100)
    tick_size = models.FloatField(default=0.01)
    pip_size = models.FloatField(default=1)
    bid = models.FloatField(default=0)
    ask = models.FloatField(default=0)
    enabled = models.BooleanField(default=True)
    category = models.ForeignKey(Category, default=1, on_delete=models.CASCADE, related_name="symbols")
    seac_best_year = models.PositiveIntegerField(default=1)

    objects = SymbolManager()

    def __str__(self):
        return self.ticker

    class Meta:
        ordering = ('ticker',)
        verbose_name_plural = "Ativos"

    def tradingview_symbol(self):
        return f'{self.broker.provider}:{self.ticker}' if self.broker is not None else -1

    def market(self):
        return self.category.name

    def update_broker(self):
        td = RealTime()
        td.getSymbolId(self)

    def update_quotes(self, num_bars=1,interval=Interval.in_1_hour):

        historic = Historic()
        historic.update_symbol(self, num_bars=num_bars,interval=interval)

    def get_quotes(self, timeframe="1H", lookback="All", dashboard=False):
        qs = self.get_historical(timeframe, lookback, True, get_quotes=True)
        data = read_frame(qs, fieldnames=["date", "open", "high", "low", "close"],index_col="date")
        # data = data[data.index.map(lambda x: x.weekday() not in [5, 6])]
        data = data.resample(timeframe).agg({"open": 'first', "high": 'max', "low": 'min', "close": 'last'})
        data = data.dropna()
        # data = data[data.index.map(lambda x: x.weekday() not in [5, 6])]
        if not dashboard:
            return data
        data.reset_index(inplace=True)

        return {"results": data.to_dict(orient="records")}

    def get_historical(self, timeframe="1D", lookback="YTD", price_perfomance=False, get_quotes=False):

        qs = Quote.objects.filter(symbol=self)
        if lookback is not None:
            lookback = lookback.upper()

        if lookback == "YTD":
            qs = qs.filter(date__year=timezone.now().year)
        elif lookback == "1D":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=1))
        elif lookback == "5D":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=5))
        elif lookback == "1M":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=30))
        elif lookback == "3M":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=90))
        elif lookback == "6M":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=180))
        elif lookback == "1Y":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=360))
        elif lookback == "5Y":
            qs = qs.filter(date__gte=timezone.now().date() - timezone.timedelta(days=360 * 5))

        if qs.count() == 0:
            return []

        if get_quotes:
            return qs
        data = read_frame(qs, index_col="date", fieldnames=["date", "close"])

        data = data.resample(timeframe).last()
        data = data.dropna()
        if price_perfomance:
            return data
        data.reset_index(inplace=True)
        return data.to_dict(orient="records")

    def get_seac(self, years, dashboard=True, get_years=False, fxguide=False, timeframe="1D"):
        pass

    def get_seac_fx_guide(self):
        return self.get_seac(years=[timezone.now().year, self.seac_best_year], fxguide=True)

    def get_seac_average(self, asset):
        pass

    def get_key_indicators(self):
        pass

    def get_price_perfomance(self):

        pass

    def get_sessions(self):
        pass

    def get_session(self, start, end, data, last):
        pass

    def get_volatility(self):
        pass


class Quote(models.Model):
    date = models.DateTimeField("Quote Date")
    date_timestamp = models.FloatField(default=0)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="quotes")
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField(default=0)

    objects = QuoteManager()

    def __str__(self):
        return "{} | {} : {}".format(self.date, self.symbol, self.close)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("date", "symbol"), name="unique_quote")]
        verbose_name_plural = "Cotações"

    def save(self, *args, **kwargs):
        self.open = round(self.open, 2)
        self.high = round(self.high, 2)
        self.low = round(self.low, 2)
        self.close = round(self.close, 2)
        super().save(*args, **kwargs)
