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


    def on_tick(self):
        pass

    @property
    @abstractmethod
    def players(self):
        pass


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
