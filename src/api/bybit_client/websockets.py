from abc import ABC, abstractmethod
from typing import Callable, Optional

from pybit.unified_trading import WebSocket
from pydantic import ValidationError

from schemas import Orderbook, Ticker, EventMessage
from schemas.order import Order
from schemas.webcallbacks import SocketOperation


# --websocket_callback-- {'success': True, 'ret_msg': '', 'op': 'auth', 'conn_id': 'cmjop6gf2tdtup418330-iodm0'}
# float() argument must be a string or a real number, not 'NoneType' --websocket_callback-- {'req_id':
# '7fe03a9c-793b-498c-9523-dd12c3fe3c1e', 'success': True, 'ret_msg': '', 'op': 'subscribe', 'conn_id':
# 'cmjop6gf2tdtup418330-iodm0'}


class WebsocketBase(ABC):
    __socket: WebSocket
    __is_testnet: bool

    def __init__(self, is_testnet: bool):
        self.__is_testnet = is_testnet

    def stream(
            self,
            symbol: str,
            channel_type: str,
            callback: Callable,
            operation_callback: Optional[Callable[[SocketOperation], None]] = None
    ) -> WebSocket:
        def wrapped_callback(data):
            self.__validate_and_forward(data, callback, operation_callback)

        self.__socket = self._create_socket(channel_type, self.__is_testnet)
        self.__socket.callback = wrapped_callback  # Подписка на сообщения сокета (auth, subscribe)
        self._stream_impl(self.__socket, symbol, wrapped_callback)
        return self.__socket

    def __validate_and_forward(self, data, callback, operation_callback):
        is_operation_message = 'ret_msg' in data
        is_normal_message = 'topic' in data

        if is_operation_message and operation_callback:
            try:
                operation = SocketOperation(**data)
            except ValidationError as e:
                print("Ошибка валидации:", e.json())
                return

            operation_callback(operation)

        if is_normal_message:
            try:
                snapshot = EventMessage(**data)
                data_parsed = self._parse_obj(snapshot.data)
            except ValidationError as e:
                print("Ошибка валидации:", e.json())
                return

            callback(data_parsed)

    def _create_socket(self, channel_type, is_testnet) -> WebSocket:
        return WebSocket(testnet=is_testnet, channel_type=channel_type)

    @abstractmethod
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        pass

    @abstractmethod
    def _parse_obj(self, data):
        pass


class PrivateWebsocket(WebsocketBase):
    __key: str
    __secret: str

    def __init__(self, key: str, secret: str, is_testnet: bool = False):
        super().__init__(is_testnet)

        self.__key = key
        self.__secret = secret

    def _create_socket(self, channel_type, is_testnet) -> WebSocket:
        return WebSocket(
            testnet=is_testnet,
            api_key=self.__key,
            api_secret=self.__secret,
            channel_type=channel_type
        )

    @abstractmethod
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        pass

    @abstractmethod
    def _parse_obj(self, data):
        pass


class OrderbookWebsocket(WebsocketBase):
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        socket.orderbook_stream(50, symbol, callback)

    def _parse_obj(self, data):
        return Orderbook.parse_obj(**data)


class TickerWebsocket(WebsocketBase):
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        socket.ticker_stream(symbol, callback)

    def _parse_obj(self, data):
        return Ticker(**data)


class OrderWebsocket(PrivateWebsocket):

    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        socket.order_stream(callback)

    def _parse_obj(self, data):
        return Order(**data)


class BybitWebsocketClient:
    orderbook: OrderbookWebsocket
    ticker: TickerWebsocket
    order: OrderWebsocket

    def __init__(self, key: str, secret: str, is_testnet: bool = False):
        self.orderbook = OrderbookWebsocket(is_testnet)
        self.ticker = TickerWebsocket(is_testnet)
        self.order = OrderWebsocket(key, secret)


__all__ = ["BybitWebsocketClient"]
