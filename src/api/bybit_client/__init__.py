import inspect
from typing import Any, Optional
from pybit.unified_trading import HTTP
from pydantic import ValidationError
from core.log import logger

from domain_models import CoinType
from schemas.account_coin import Coin, Account
from schemas.webcallbacks import APIResponse
from .websockets import BybitWebsocketClient
from data import InstrumentInfo
from schemas import Book, Orderbook
from schemas.order import Order, OrderEntity


class BybitHandler:
    @staticmethod
    def rest_handler(message: dict) -> Any:
        response = APIResponse(**message)
        call_function_name = inspect.currentframe().f_back.f_code.co_name
        if response.ret_code != 0:
            raise Exception(f"[{call_function_name}] Ошибка запроса. Код: {response.ret_code}. "
                            f"\nСообщение: {response.ret_msg}")

        return response.result


# TODO валидация ошибок
# TODO разделить на WebsocketClient и RESTClient
class BybitClient:
    websocket: BybitWebsocketClient

    __key: str
    __secret_key: str
    __session: HTTP
    __is_testnet: bool

    def __init__(
            self,
            key: str,
            secret_key: str,
            is_testnet: bool = False
    ):
        self.websocket = BybitWebsocketClient(key, secret_key)

        self.__is_testnet = is_testnet
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
        result.update({key: str(kwargs[key]) for key in needed_keys})
        result["orderStatus"] = "New"

        logger.info(f"(place order) {result}")

        return Order(**result)

    def get_open_orders(self, symbol: str, category: str) -> [Order]:
        cursor = None
        result = []

        while True:
            response = self.__session.get_open_orders(
                symbol=symbol,
                category=category,
                cursor=cursor,
                limit=50
            )

            book = BybitHandler.rest_handler(response)
            order_book = Book(**book)

            result.extend(Order(**item) for item in order_book.list)

            if not order_book.next_page_cursor:
                break

            cursor = order_book.next_page_cursor

        logger.info(f"(get open orders) {result}")

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

    def wallet_balance(self, coin_name: CoinType) -> Optional[Coin]:
        response = self.__session.get_wallet_balance(
            accountType="UNIFIED",  # TODO хардкод
        )

        result = BybitHandler.rest_handler(response)
        account = result["list"][0]
        logger.info(account)
        account = Account(**account)
        coin = next((item for item in account.coins if item.coin == coin_name), None)

        logger.info(f"(get wallet balance) {coin}")

        return coin

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
        logger.info(f"(amend order) {result}")

    def cancel_all_orders(self, category: str) -> [OrderEntity]:
        response = self.__session.cancel_all_orders(category=category)
        result = BybitHandler.rest_handler(response)
        return [OrderEntity(**item) for item in result["list"]]

    def get_orderbook(self, **kwargs) -> Orderbook:
        response = self.__session.get_orderbook(**kwargs)
        result = BybitHandler.rest_handler(response)
        return Orderbook(**result)
