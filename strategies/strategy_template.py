from abc import ABC, abstractmethod
import time
from django.utils import timezone


class TradingStrategy(ABC):

    @property
    @abstractmethod
    def strategy(self):
        pass

    @property
    @abstractmethod
    def on_start(self):
        pass

    @property
    @abstractmethod
    def on_bar(self, *args, **kwargs):
        pass

    def __init__(self):
        self.on_start()


    def on_tick(self):
        pass

    @property
    @abstractmethod
    def players(self):
        pass

    def _on_start(self):
        self.orders = []
        self.start()

    def start(self):
        pass

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = value

    @property
    @abstractmethod
    def buy(self, *args,**kwargs):
        pass

    @property
    @abstractmethod
    def sell(self, *args,**kwargs):
        pass

    @property
    def orders(self):
        return self._orders

    @orders.setter
    def orders(self, value):
        self._orders = value

