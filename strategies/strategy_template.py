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
        raise NotImplementedError("Essa função tem que ser implementada")

    @property
    @abstractmethod
    def on_bar(self, *args, **kwargs):
        raise NotImplementedError("Essa função tem que ser implementada")

    @property
    @abstractmethod
    def signal(self, *args, **kwargs):
        raise NotImplementedError("Essa função tem que ser implementada")

    def __init__(self):
        self._on_start()

    def on_tick(self):
        pass

    def run_optimize(self, *args, **kwargs):
        raise NotImplementedError("Essa função tem que ser implementada")

    @property
    @abstractmethod
    def players(self):
        pass

    def _on_start(self):
        self.orders = {}
        self.start()

    def start(self):
        pass

    @property
    @abstractmethod
    def buy(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def sell(self, *args, **kwargs):
        pass

    @property
    def orders(self):
        return self._orders

    @orders.setter
    def orders(self, value):
        self._orders = value

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = value
