import json

from pybit.unified_trading import HTTP, WebSocket
from typing import Callable

from data import RestResponse


class BybitClient:
    websocket_callback: Callable[[str], None]

    __key: str
    __secret_key: str
    __is_testnet: bool
    __socket: WebSocket
    __session: HTTP

    def __init__(
            self,
            key: str,
            secret_key: str,
            is_testnet: bool,
            handler: Callable[[str], None],
            websocket_callback: Callable[[str], None] = None,
    ):
        self.websocket_callback = websocket_callback
        self.__is_testnet = is_testnet
        self.__key = key
        self.__secret_key = secret_key

        self.__session = HTTP(
            testnet=is_testnet,
            api_key=key,
            api_secret=secret_key
        )

        self.__socket = WebSocket(
            testnet=self.__is_testnet,
            channel_type="private",
            rsa_authentication=False,
            api_key=self.__key,
            api_secret=self.__secret_key,
            trace_logging=True,
            retries=30,
            ping_interval=20,
            ping_timeout=10,
            restart_on_error=True,
            private_auth_expire=1,
            callback_function=self.websocket_callback
        )

        self.__socket.order_stream(self.handler_ctx)

    def handler_ctx(self, message):
        print("---handler---")
        print(message)
        pass

    def place_order(self, symbol: str, side: str, qty: int, price: float) -> RestResponse:
        price = f"{price:.4f}"
        responce = self.__session.place_order(
            category="spot",
            symbol=symbol,
            side=side,
            orderType="Limit",
            qty=qty,
            price=price,
            timeInForce="GTC"
        )

        return RestResponse.from_dict(responce)