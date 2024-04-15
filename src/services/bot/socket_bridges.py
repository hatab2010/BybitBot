from abc import ABC, abstractmethod

from pybit.unified_trading import WebSocket

from api import BybitClient
from core.event import Event
from schemas import Ticker, Orderbook


class SocketBridgeBase(ABC):
    message_event: Event

    _socket: WebSocket
    _symbol: str
    _category: str
    _client: BybitClient

    def __init__(self, symbol: str, category: str, client: BybitClient):
        self._symbol = symbol
        self._category = category
        self._client = client
        self.impl()

    def exit(self):
        self._socket.exit()
        self.message_event.clear_subscribers()

    @abstractmethod
    def impl(self):
        pass


class TickerEvent(Event[Ticker]):
    pass


class TickerBridge(SocketBridgeBase):
    message_event: TickerEvent

    def __handler(self, message: Ticker):
        self.message_event._fire(message)

    def impl(self):
        self._socket = self._client.websocket.ticker.stream(self._symbol, self._category, self.__handler)
        self.message_event = TickerEvent()


class OrderbookEvent(Event[Orderbook]):
    pass


class OrderbookBridge(SocketBridgeBase):
    message_event: OrderbookEvent

    def __handler(self, message: Orderbook):
        self.message_event._fire(message)

    def impl(self):
        self._socket = self._client.websocket.orderbook.stream(self._symbol, self._category, self.__handler)
        self.message_event = OrderbookEvent()
