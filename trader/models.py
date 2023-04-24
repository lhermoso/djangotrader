from django.db import models
from django.utils import timezone

# Create your models here.
SERVER_CHOICES = (("R", "REAL"), ("D", "DEMO"))


class Broker(models.Model):
    name = models.CharField(max_length=250)


    def __str__(self):
        return self.name


class Account(models.Model):
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name="accounts")
    account = models.CharField(max_length=250)
    user = models.CharField(max_length=250, blank=True, null=True)
    password = models.CharField(max_length=250, blank=True, null=True)
    token = models.CharField(max_length=250,default="xxxxxxx")
    server = models.CharField(max_length=1, choices=SERVER_CHOICES, default="D")

    def __str__(self):
        return f"{self.get_server_display()} => {self.account}"


class Order(models.Model):
    account = models.ForeignKey(Account, related_name="orders", on_delete=models.CASCADE)
    symbol = models.ForeignKey("marketdata.Symbol", on_delete=models.CASCADE, related_name="orders")
    strategies = models.ForeignKey("strategies.Strategy", on_delete=models.CASCADE, related_name="orders")
    entry_date = models.DateTimeField(default=timezone.now)
    exit_date = models.DateTimeField(default=timezone.now)
    entry_price = models.FloatField(default=0)
    exit_price = models.FloatField(default=0)
    result = models.FloatField(default=0)

    def __str__(self):
        return f'{self.symbol.ticker}: ${self.result}'
