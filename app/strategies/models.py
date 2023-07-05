from django.db import models
from marketdata.models import Symbol


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
    lot_size = models.PositiveIntegerField(default=1)
    factor = models.FloatField(default=0)
    sharpe = models.FloatField(default=0)
    signal = models.IntegerField(default=0)
    enabled = models.BooleanField(default=False)

    objects = PlayerManager()

    class Meta:
        verbose_name_plural = "Players"

    def __str__(self):
        return f'{self.symbol.ticker}: {self.sharpe}'


class Param(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="params")
    name = models.CharField(max_length=250)
    value = models.FloatField()

    def __str__(self):
        return f'{self.name}:{self.value}'



