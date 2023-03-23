from django.utils import timezone

try:
    from strategies.fxcm import FXCM
except:
    from strategies.fxcm import FXCM
from strategies.models import Strategy
import math
from forexconnect import fxcorepy, Common


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

    def __init__(self, account):
        self.account = account
        self.strategy = Strategy.objects.get(name="Volatility")
        self.players = self.strategy.players.filter(enabled=True)
        self.longs = {}
        self.shorts = {}
        self.connect()
        account = Common.get_account(self.fxcm)
        if not account:
            raise Exception(
                "The account '{0}' is not valid".format(self.account))
        else:
            self.account = account.account_id
        for player in self.players:
            self.longs |= {player: None}
            self.shorts |= {player: None}
            self.start_trade(player)

    def on_start(self):
        self.strategy = Volatility

    def on_bar(self, player, pricedata):
        player.refresh_from_db()
        trigger = player.params.get(name="trigger").value
        periods = int(player.params.get(name="periods").value)

        log_ret = (pricedata['BidClose'].apply(math.log).diff(1) * 100).fillna(0)
        log_ret_accum = log_ret.rolling(periods).sum().fillna(0)
        buy = (log_ret_accum < -trigger) & (log_ret_accum.shift(1) > -trigger)
        sell = (log_ret_accum > trigger) & (log_ret_accum.shift(1) < trigger)


        if buy.iloc[-1]:
            self.close_trades(player.symbol.ticker, fxcorepy.Constants.BUY)
            print(f"{player.symbol.ticker} BUY SIGNAL!")
            self.buy(player.symbol.ticker, is_fx=player.symbol.broker.provider == "FX")

        elif sell.iloc[-1]:
            self.close_trades(player.symbol.ticker, fxcorepy.Constants.SELL)
            print(f"{player.symbol.ticker} SELL SIGNAL!")
            self.sell(player.symbol.ticker, is_fx=player.symbol.broker.provider == "FX")
        # print(f"{str(timezone.datetime.now())} {player.symbol.ticker}: {player.timeframe.full_name} Volatility:{log_ret_accum.iloc[-1]}...")


if __name__ == "__main__":
    Volatility(account=1571013)
    input("Done! Press enter key to exit\n")
