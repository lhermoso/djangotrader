from abc import ABC, abstractmethod
from .strategy_template import TradingStrategy
from trader.models import Account
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
try:
    from forexconnect import fxcorepy, ForexConnect, LiveHistory, ResponseListener, Common
except:
    from forexconnect import fxcorepy, ForexConnect, LiveHistory, ResponseListener, Common


class FXCM(TradingStrategy):
    fxcm = None
    login_data = None

    @property
    @abstractmethod
    def account(self):
        pass

    def transform_ticker(self,instrument):
        return  f"{instrument[:3]}/{instrument[3:]}"


    def connect(self):
        login_data = Account.objects.filter(account=self.account).first()
        if login_data is None:
            raise Exception("FXCM account not found, check settings.")
        if self.fxcm is not None:
            self.fxcm.close()
        self.fxcm = ForexConnect()
        self.fxcm.login(login_data.user, login_data.password, connection=login_data.get_server_display())
        self.login_data = login_data

    def start_trade(self, player):
        instrument = f"{player.symbol.ticker[:3]}/{player.symbol.ticker[3:]}"
        timeframe = player.timeframe.name
        live_history = LiveHistory.LiveHistoryCreator(timeframe)
        on_bar_added_callback = self.on_bar_added(player)
        live_history.subscribe(on_bar_added_callback)

        session_status_changed_callback = self.session_status_changed(live_history, instrument, True)
        session_status_changed_callback(self.fxcm.session, self.fxcm.session.session_status)
        self.fxcm.set_session_status_listener(session_status_changed_callback)
        print(f"{instrument}: Getting history...")
        history = self.fxcm.get_history(instrument, timeframe)
        print(f"{instrument}: Updating history...")
        live_history.history = history
        on_bar_added_callback(live_history.history)

    def buy(self, instrument, amount=1, is_fx=False):
        self.create_open_market_order(instrument, amount, "B", is_fx)

    def sell(self, instrument, amount=1, is_fx=False):
        self.create_open_market_order(instrument, amount, "S", is_fx)

    def on_bar_added(self, player):
        def _on_bar_added(history):
            self.on_bar(player, history[:-1])

        return _on_bar_added

    def create_open_market_order(self, instrument, lots, buy_sell, is_fx=False):
        instrument = f"{instrument[:3]}/{instrument[3:]}"
        try:

            offer = Common.get_offer(self.fxcm, instrument)

            if not offer:
                raise Exception(
                    "The instrument '{0}' is not valid".format(instrument))

            if is_fx:
                lots *= 1000

            print("\nCreating order for instrument {0}...".format(offer.instrument))
            response_listener = ResponseListener(self.fxcm.session)
            try:
                request = self.fxcm.create_order_request(
                    order_type=fxcorepy.Constants.Orders.TRUE_MARKET_OPEN,
                    ACCOUNT_ID=self.account,
                    BUY_SELL=buy_sell,
                    AMOUNT=lots,
                    SYMBOL=offer.instrument
                )

                self.fxcm.send_request_async(request, response_listener)
            except Exception as e:
                print("Failed")


        except Exception as e:
            print("Failed")

    def close_trades(self, instrument, side):
        instrument = f"{instrument[:3]}/{instrument[3:]}"
        table_manager = self.fxcm.table_manager
        orders_table = table_manager.get_table(ForexConnect.TRADES)
        response_listener = ResponseListener(self.fxcm.session)
        for trade in orders_table:
            if trade.instrument == instrument and trade.buy_sell != side:
                offer = Common.get_offer(self.fxcm, instrument)

                order_id = None
                request = self.fxcm.create_order_request(
                    order_type=fxcorepy.Constants.Orders.TRUE_MARKET_CLOSE,
                    OFFER_ID=offer.offer_id,
                    ACCOUNT_ID=self.account,
                    BUY_SELL=side,
                    AMOUNT=trade.amount,
                    TRADE_ID=trade.trade_id
                )
                self.fxcm.send_request_async(request, response_listener)

    def session_status_changed(self, live_history, instrument, reconnect_on_disconnected):
        offers_listener = None
        first_call = reconnect_on_disconnected
        orders_listener = None

        def _session_status_changed(session, status):
            nonlocal offers_listener
            nonlocal first_call
            nonlocal orders_listener
            if status == fxcorepy.AO2GSessionStatus.O2GSessionStatus.CONNECTED:
                orders_table = self.fxcm.get_table(ForexConnect.ORDERS)
                orders_listener = Common.subscribe_table_updates(orders_table)

                offers = self.fxcm.get_table(ForexConnect.OFFERS)
                if live_history is not None:
                    on_changed_callback = self.on_changed(live_history, instrument)
                    offers_listener = Common.subscribe_table_updates(offers, on_change_callback=on_changed_callback)
            elif status == fxcorepy.AO2GSessionStatus.O2GSessionStatus.DISCONNECTING or \
                    status == fxcorepy.AO2GSessionStatus.O2GSessionStatus.RECONNECTING or \
                    status == fxcorepy.AO2GSessionStatus.O2GSessionStatus.SESSION_LOST:
                if orders_listener is not None:
                    orders_listener.unsubscribe()
                    orders_listener = None
                if offers_listener is not None:
                    offers_listener.unsubscribe()
                    offers_listener = None
            elif status == fxcorepy.AO2GSessionStatus.O2GSessionStatus.DISCONNECTED and reconnect_on_disconnected:
                self.fxcm.login(self.login_data.user, self.login_data.password,
                                connection=self.login_data.get_server_display())

        return _session_status_changed

    def on_changed(self, live_history, instrument):
        def _on_changed(table_listener, row_id, row):
            del table_listener, row_id
            try:

                if row.table_type == fxcorepy.O2GTableType.OFFERS and row.instrument == instrument:
                    live_history.add_or_update(row)
            except Exception as e:
                return

        return _on_changed
