import inspect
from decimal import Decimal
from typing import Any, Callable, Optional

from pybit.unified_trading import HTTP, WebSocket

from .websockets import BybitWebsocketClient
from data import Book, InstrumentInfo, Order, RestResponse, TickerResponse, WebsocketResponse


class BybitHandler:
    @staticmethod
    def rest_handler(message: dict) -> Any:
        response = RestResponse.from_dict(message)
        call_function_name = inspect.currentframe().f_back.f_code.co_name
        if response.retCode != 0:
            raise Exception(f"[{call_function_name}] Ошибка запроса. Код: {response.retCode}. "
                            f"\nСообщение: {response.retMsg}")

        return response.result


# TODO разделить на WebsocketClient и RESTClient
class BybitClient:
    order_callback: Callable[[list[Order]], None]
    subscribe: Callable

    __category: str = "spot"

    __websocket_callback: Callable[[str], None]
    __ticker_callback: Optional[Callable[[TickerResponse], None]]
    __key: str
    __secret_key: str
    __session: HTTP
    __socket: WebSocket
    __ticker_socket: Optional[WebSocket]
    __is_testnet: bool

    def __init__(
            self,
            key: str,
            secret_key: str,
            is_testnet: bool
    ):
        self.__websocket_client = BybitWebsocketClient(is_testnet)
        self.__is_testnet = is_testnet
        self.__ticker_callback = None
        self.__ticker_socket = None
        self.__key = key
        self.__secret_key = secret_key

        self.__session = HTTP(
            testnet=is_testnet,
            api_key=key,
            api_secret=secret_key
        )

        self.__orderbook_socket = WebSocket(
            testnet=is_testnet,
            channel_type="spot"
        )

        self.__socket = WebSocket(
            testnet=is_testnet,
            channel_type="private",
            rsa_authentication=False,
            api_key=key,
            api_secret=secret_key,
            trace_logging=True,
            retries=30,
            ping_interval=30,
            ping_timeout=20,
            restart_on_error=True,
            private_auth_expire=1,
            callback_function=self.__order_handler
        )

    def get_open_orders(self, symbol: str) -> [Order]:
        cursor = None
        data = list()

        def request():
            return self.__session.get_open_orders(
                category="spot",
                symbol=symbol,
                limit=50,
                cursor=cursor
            )

        # TODO бесконечный цикл
        while True:
            result = BybitHandler.rest_handler(request())
            book = Book.from_dict(result)

            if not book.nextPageCursor:
                break

            data += book.list
            cursor = book.nextPageCursor

        result = list()
        for item in data:
            result.append(Order.from_dict(item))

        return result

    def get_order_history(self, symbol: str):
        cursor = None
        data = list()

        def request():
            return self.__session.get_order_history(
                category="spot",
                symbol=symbol,
                limit=50,
                cursor=cursor
            )

        # TODO бесконечный цикл
        while True:
            result = BybitHandler.rest_handler(request())
            book = Book.from_dict(result)

            if not book.nextPageCursor:
                break

            data += book.list
            cursor = book.nextPageCursor

        # result = list()
        # for item in data:
        #     result.append(Order.from_dict(item))

        return data

    def get_instrument_info(self, symbol) -> InstrumentInfo:
        response = self.__session.get_instruments_info(
            category="spot",
            symbol=symbol
        )

        result = BybitHandler.rest_handler(response)
        return InstrumentInfo.from_dict(result)

    def remove_order(self, symbol: str, order_id: str):
        self.__session.cancel_order(
            category="spot",
            symbol=symbol,
            orderId=order_id
        )

    def amend_order(self, symbol: str, order_id: str, price: Decimal):
        response = self.__session.amend_order(
            category="spot",
            symbol=symbol,
            orderId=order_id,
            price=price
        )

        result = BybitHandler.rest_handler(response)
        print(f"(amend order) {result}")

    def place_order(self, symbol: str, side: str, qty: int, price: Decimal) -> Order:
        response = self.__session.place_order(
            category="spot",
            symbol=symbol,
            side=side,
            orderType="Limit",
            qty=qty,
            price=price,
            timeInForce="GTC"
        )

        result = BybitHandler.rest_handler(response)
        result["side"] = side
        result["price"] = price
        result["qty"] = qty
        result["symbol"] = symbol

        print(f"(place order) {result}")
        return Order.from_dict(result)

    def ticker_stream(self, symbol: str, callback: Callable[[TickerResponse], None]):
        if self.__ticker_socket:
            self.__ticker_socket.exit()

        self.__ticker_callback = callback

        self.__ticker_socket = WebSocket(
            testnet=self.__is_testnet,
            api_key=self.__key,
            api_secret=self.__secret_key,
            channel_type="spot"
        )

        def ticker_handler(message):
            if self.__ticker_callback is not None:
                # TODO сделать валидацию входящего сообщения
                try:
                    self.__ticker_callback(TickerResponse.from_dict(message))
                except Exception as ex:
                    print(ex)

        self.__ticker_socket.ticker_stream(symbol, ticker_handler)

    def cancel_all_orders(self):
        self.__session.cancel_all_orders(category="spot")

    def __order_handler(self, message: dict):
        print("--websocket_callback--")
        print(message)

        # TODO сделать валидацию входящего сообщения, убрать магию.
        try:
            if message["op"] == "subscribe" and message["success"] is True:
                self.subscribe()
        except:
            pass

        try:
            response = WebsocketResponse.from_dict(message)
            if self.order_callback:
                self.order_callback(response.data)
        except Exception as ex:
            print(ex)
