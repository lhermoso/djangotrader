import json
import random
import re
import string

import requests
from websocket import create_connection
from tvDatafeed import TvDatafeed, Interval
import pytz
from django.db.models import Q
from django.conf import settings

from django.apps import apps

# pip install --upgrade --no-cache-dir git+https://github.com/StreamAlpha/tvdatafeed.git


tradingview_user = settings.TRADINGVIEW_USER
tradingview_password = settings.TRADINGVIEW_PASSWORD


class RealTime:

    def __init__(self):
        Symbol = apps.get_model("marketdata", "Symbol")
        self.symbols = Symbol.objects.filter(Q(category="1") | Q(category="5"))

    def search(self, query, type):
        res = requests.get(
            f"https://symbol-search.tradingview.com/symbol_search/?text={query}&type={type}"
        )
        if res.status_code == 200:
            res = res.json()

            assert len(res) != 0, "Não encontrado."
            return res[0]
        else:

            print("Nothing Found.")
            return -1

    def generateSession(self):
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "qs_" + random_string

    def prependHeader(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def constructMessage(self, func, paramList):
        return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))

    def createMessage(self, func, paramList):
        return self.prependHeader(self.constructMessage(func, paramList))

    def sendMessage(self, ws, func, args):
        ws.send(self.createMessage(func, args))

    def sendPingPacket(self, ws, result):
        pingStr = re.findall(".......(.*)", result)
        if len(pingStr) != 0:
            pingStr = pingStr[0]
            ws.send("~m~" + str(len(pingStr)) + "~m~" + pingStr)

    def update_quotes(self, ticker, price):
        print(f'{ticker.split(":")[-1]}:{price}')
        self.symbols.filter(ticker=ticker.split(":")[-1]).update(last_bid=price)

    def socketJob(self, ws):
        while True:
            try:
                result = ws.recv()
                if "quote_completed" in result or "session_id" in result:
                    continue
                Res = re.findall("^.*?({.*)$", result)
                if len(Res) != 0:
                    jsonRes = json.loads(Res[0])

                    if jsonRes["m"] == "qsd":
                        ticker = jsonRes["p"][1]["n"]
                        price = jsonRes["p"][1]["v"]["lp"]
                        print(jsonRes["m"])
                        self.update_quotes(ticker, price)


                else:
                    # ping packet
                    self.sendPingPacket(ws, result)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                exit(0)
            except Exception as e:

                continue

    def update_symbol(self, ticker, data,broker):
        Broker = apps.get_model("marketdata", "Broker")
        broker_db, created = Broker.objects.get_or_create(provider=broker)
        currency = data["currency_code"] if "currency_code" in data else ''
        name = data["description"] if "description" in data else ''
        country = data["country"] if "country" in data else ''
        self.symbols.filter(ticker=ticker).update(broker=broker_db, name=name,
                                                  currency=currency, country=country)

    def getSymbolId(self, symbol):
        data = self.search(symbol.ticker, symbol.market())
        if data == -1:
            return data
        symbol_name = data["symbol"]
        try:
            broker = data["prefix"]
        except KeyError:
            broker = data["exchange"]
        symbol_id = f"{broker.upper()}:{symbol_name.upper()}"
        self.update_symbol(symbol_name, data,broker)
        print(symbol_id)
        return symbol_id

    def start(self):

        symbol_ids = []
        for pair in self.symbols:
            symbol_id = pair.tradingview_symbol()
            if symbol_id == -1:
                symbol_id = self.getSymbolId(pair)
            if symbol_id == -1:
                continue
            symbol_ids.append(symbol_id)

        # create tunnel
        tradingViewSocket = "wss://data.tradingview.com/socket.io/websocket"
        headers = json.dumps({"Origin": "https://data.tradingview.com"})
        ws = create_connection(tradingViewSocket, headers=headers)
        session = self.generateSession()

        # Send messages
        self.sendMessage(ws, "quote_create_session", [session])
        self.sendMessage(ws, "quote_set_fields", [session, "lp"])

        [self.sendMessage(ws, "quote_add_symbols", [session, symbol_id]) for symbol_id in symbol_ids]

        # Start job
        self.socketJob(ws)


class Historic:

    def __init__(self, symbols=None):

        username = tradingview_user
        password = tradingview_password
        self.symbols = symbols

        self.tv = TvDatafeed(username, password)

    def update_all_symbols(self, num_bars=1, interval=Interval.in_1_hour):

        for symbol in self.symbols:
            self.update_symbol(symbol=symbol, num_bars=num_bars, interval=interval)

    def update_symbol(self, symbol, num_bars=1, interval=Interval.in_1_hour):
        Quote = apps.get_model("marketdata", "Quote")
        data = self.tv.get_hist(symbol=symbol.ticker, exchange=symbol.broker.provider,
                                interval=interval, n_bars=num_bars)
        quotes = []
        if data is None:
            return
        for index in range(data.shape[0]):
            quotes.append(
                Quote(date=pytz.timezone("UTC").localize(data.index[index]), symbol=symbol, open=data.open[index],
                      high=data.high[index],
                      low=data.low[index],
                      close=data.close[index], volume=data.volume[index]))

        Quote.objects.bulk_create(quotes, ignore_conflicts=True)
