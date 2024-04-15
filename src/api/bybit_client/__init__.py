import inspect
from decimal import Decimal
from typing import Any, Callable, Optional

from pybit.unified_trading import HTTP, WebSocket

from .websockets import BybitWebsocketClient
from data import InstrumentInfo, RestResponse, TickerResponse, WebsocketResponse
from schemas import Book, Order
from schemas.order import Order, OrderEntity


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
    __websocket_callback: Callable[[str], None]
    __ticker_callback: Optional[Callable[[TickerResponse], None]]
    __key: str
    __secret_key: str
    __session: HTTP
    __ticker_socket: Optional[WebSocket]
    __is_testnet: bool

    def __init__(
            self,
            key: str,
            secret_key: str,
            is_testnet: bool
    ):
        self.websocket = BybitWebsocketClient(key, secret_key)
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

    def place_order(self, **kwargs) -> Order:
        needed_keys = ["side", "price", "qty", "symbol"]
        if not all(key in kwargs for key in needed_keys):
            raise ValueError("Не все обязательные ключи предоставлены")

        response = self.__session.place_order(**kwargs)
        result = BybitHandler.rest_handler(response)
        result.update({key: kwargs[key] for key in needed_keys})

        print(f"(place order) {result}")
        return Order(**result)

    def get_open_orders(self, symbol: str, category: str) -> [Order]:
        cursor = None
        result = []

        while True:
            response = self.__session.get_open_orders(
                category=category,
                symbol=symbol,
                limit=50,
                cursor=cursor
            )

            book = BybitHandler.rest_handler(response)
            order_book = Book(**book)

            result.extend(Order.parse_obj(item) for item in order_book.list)

            if not order_book.next_page_cursor:
                break

            cursor = order_book.next_page_cursor

        return result

    def get_order_history(self, symbol: str):
        cursor = None
        result = []

        while True:
            result = BybitHandler.rest_handler(self.__session.get_order_history(
                category="spot",
                symbol=symbol,
                limit=50,
                cursor=cursor
            ))
            book = Book.parse_obj(result)

            result += book.list

            if not book.next_page_cursor:
                break

            cursor = book.next_page_cursor

        return result

    def get_instrument_info(self, symbol: str, category: str) -> InstrumentInfo:
        response = self.__session.get_instruments_info(
            category=category,
            symbol=symbol
        )

        result = BybitHandler.rest_handler(response)
        return InstrumentInfo.from_dict(result)

    def cancel_order(self, **kwargs) -> OrderEntity:
        response = self.__session.cancel_order(**kwargs)
        result = BybitHandler.rest_handler(response)
        return OrderEntity(**result)

    def amend_order(self, **kwargs):
        response = self.__session.amend_order(**kwargs)
        result = BybitHandler.rest_handler(response)
        print(f"(amend order) {result}")

    def cancel_all_orders(self, category: str) -> [OrderEntity]:
        response = self.__session.cancel_all_orders(category=category)
        result = BybitHandler.rest_handler(response)
        return [OrderEntity(**item) for item in result]

    # def __order_stream_handler(self, message: dict):
    #     print(message)
    #     is_auth_message = message.get("op") == "auth" or message.get("type") == "AUTH_RESP"
    #     is_subscription_message = message.get("op") == "subscribe" or message.get("type") == "COMMAND_RESP"
    #     is_normal_message = not is_auth_message and not is_subscription_message
    #
    #     if is_auth_message:
    #         return
    #     elif is_subscription_message and message["success"] is True:
    #         self.on_success_subscribe()
    #     elif is_normal_message:
    #         try:
    #             response = WebsocketResponse.from_dict(message)
    #             if self.order_callback:
    #                 self.order_callback(response.data)
    #         except Exception as ex:
    #             print(ex)
