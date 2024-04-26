from abc import ABC, abstractmethod

from pybit.unified_trading import WebSocket
from api import BybitClient
from core.event import Event
from schemas import Ticker, Orderbook, Order


class SocketBridgeBase(ABC):
    _message_event: Event

    _socket: WebSocket
    _symbol: str
    _channel_type: str
    _client: BybitClient

    def __init__(self, symbol: str, category: str, client: BybitClient):
        self._symbol = symbol
        self._channel_type = category
        self._client = client
        self._impl()

    def exit(self):
        self._socket.exit()
        self._message_event.clear_subscribers()

    @abstractmethod
    def _impl(self):
        pass

    @property
    def symbol(self) -> str:
        return self._symbol

    # @property
    # def category(self):
    #     return self._category


class TickerEvent(Event[Ticker]):
    pass


class TickerBridge(SocketBridgeBase):
    _message_event: TickerEvent

    @property
    def message_event(self) -> TickerEvent:
        return self._message_event

    def __handler(self, message: Ticker):
        self._message_event._fire(message)

    def _impl(self):
        self._socket = self._client.websocket.ticker.stream(self._symbol, self._channel_type, self.__handler)
        self._message_event = TickerEvent()


class OrderEvent(Event[Order]):
    pass


class OrderBridge(SocketBridgeBase):
    _message_event: OrderEvent

    @property
    def message_event(self) -> OrderEvent:
        return self._message_event

    def __handler(self, order: Order):
        print(order)
        self._message_event._fire(order)

    def _impl(self):
        self._socket = self._client.websocket.order.stream(self._symbol, self._channel_type, self.__handler)
        self._message_event = OrderEvent()


class OrderbookEvent(Event[Orderbook]):
    pass


class OrderbookBridge(SocketBridgeBase):
    _message_event: OrderbookEvent

    @property
    def message_event(self) -> OrderbookEvent:
        return self._message_event

    def __handler(self, message: Orderbook):
        self._message_event._fire(message)

    def _impl(self):
        self._socket = self._client.websocket.orderbook.stream(self._symbol, self._channel_type, self.__handler)
        self._message_event = OrderbookEvent()
