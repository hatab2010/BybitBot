from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Union

from pybit.unified_trading import WebSocket
from pydantic import BaseModel, ValidationError
from pydantic.v1 import validator

from schemas import OrderbookSnapshot, TickerSnapshot, Snapshot
from schemas.webcallbacks import SocketEvent


# --websocket_callback--
# {'success': True, 'ret_msg': '', 'op': 'auth', 'conn_id': 'cmjop6gf2tdtup418330-iodm0'}
# float() argument must be a string or a real number, not 'NoneType'
# --websocket_callback--
# {'req_id': '7fe03a9c-793b-498c-9523-dd12c3fe3c1e', 'success': True, 'ret_msg': '', 'op': 'subscribe', 'conn_id': 'cmjop6gf2tdtup418330-iodm0'}
class BaseWebsocket(ABC):
    callback_function: Optional[Callable]
    __is_testnet: bool

    def __init__(self, is_testnet: bool):

        self.__is_testnet = is_testnet

    def stream(
            self,
            callback: Union[OrderbookSnapshot, TickerSnapshot],
            symbol: str,
            channel_type: str = "spot",
            socket_event: Optional[Callable[[SocketEvent], None]] = None
    ):
        self.__socket_event = socket_event
        wrapped_callback = lambda data: self.__validate_and_forward(data, callback)
        socket = WebSocket(testnet=self.__is_testnet, channel_type=channel_type)
        socket.callback = wrapped_callback  # Подписка на сообщения сокета (auth)
        self._stream_impl(socket, symbol, wrapped_callback)
        return socket

    def __validate_and_forward(self, data, callback):
        if 'ret_msg' in data:
            if self.__socket_event:
                try:
                    self.__socket_event(SocketEvent.parse_obj(data))
                except ValidationError as e:
                    print("Ошибка валидации:", e.json())
            return

        try:
            message = Snapshot.parse_obj(data)
            data = self._parse_obj(message.data)
            callback(data)
        except ValidationError as e:
            print("Ошибка валидации:", e.json())

    @abstractmethod
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        pass

    @abstractmethod
    def _parse_obj(self, data):
        pass


class OrderbookWebsocket(BaseWebsocket):
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        socket.orderbook_stream(50, symbol, callback)

    def _parse_obj(self, data):
        return OrderbookSnapshot.parse_obj(data)


class TickerWebsocket(BaseWebsocket):
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        socket.ticker_stream(symbol, callback)

    def _parse_obj(self, data):
        return TickerSnapshot.parse_obj(data)


class OrderWebsocket(BaseWebsocket):
    def _stream_impl(self, socket: WebSocket, symbol: str, callback: Callable):
        raise NotImplemented

    def _parse_obj(self, data):
        raise NotImplemented


class BybitWebsocketClient:
    orderbook: OrderbookWebsocket
    ticker: TickerWebsocket

    def __init__(self, is_testnet: bool):
        self.orderbook = OrderbookWebsocket(is_testnet)
        self.ticker = TickerWebsocket(is_testnet)


__all__ = ["BybitWebsocketClient"]
