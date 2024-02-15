from decimal import Decimal, ROUND_HALF_UP
from pybit.unified_trading import HTTP, WebSocket
from typing import Callable, Optional
from data import Order, RestResponse, InstrumentInfo, TickerResponse, WebsocketResponse


class BybitClient:
    order_callback: Callable[[list[Order]], None]

    __websocket_callback: Callable[[str], None]
    __ticker_callback: Callable[[TickerResponse], None]
    __key: str
    __secret_key: str
    __is_testnet: bool
    __session: HTTP
    __socket: WebSocket
    __ticker_socket: Optional[WebSocket]

    def __init__(
            self,
            key: str,
            secret_key: str,
            is_testnet: bool,
            # websocket_callback: Callable[[str], None] = None,
    ):
        # self.__websocket_callback = websocket_callback
        self.__is_testnet = is_testnet
        self.__key = key
        self.__secret_key = secret_key
        self.__ticker_socket = None

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
            callback_function=self.__websocket_handler
        )

        self.__socket.order_stream(self.handler_ctx)

    def __websocket_handler(self, message: dict):
        print("--websocket_callback--")
        print("message")

        try:
            response = WebsocketResponse.from_dict(message)
            if self.order_callback:
                self.order_callback(response.data)
        except Exception as ex:
            print(ex)

    def get_instrument_info(self, symbol) -> InstrumentInfo:
        response = self.__session.get_instruments_info(
            category="spot",
            symbol=symbol
        )

        response = RestResponse.from_dict(response)
        if response.retCode != 0:
            raise Exception
        else:
            return InstrumentInfo.from_dict(response.result)

    #TODO проверить
    def handler_ctx(self, message):
        print(message)
        pass

    def remove_order(self, symbol: str, order_id: str):
        self.__session.cancel_order(
            category="spot",
            symbol=symbol,
            orderId=order_id
        )

    def amend_order(self, symbol: str, order_id: str, price: Decimal):
        self.__session.amend_order(
            category="spot",
            symbol=symbol,
            orderId=order_id,
            price=price.quantize(Decimal("1.0000"), ROUND_HALF_UP) #TODO заплатка. Необходима проверка на минимальный tick size
        )

    def place_order(self, symbol: str, side: str, qty: int, price: Decimal) -> Order:
        price = f"{price:.4f}" #TODO Сделать округление числа до значимых знаков в соответствии с tickSize пары
        response = self.__session.place_order(
            category="spot",
            symbol=symbol,
            side=side,
            orderType="Limit",
            qty=qty,
            price=price,
            timeInForce="GTC"
        )
        response = RestResponse.from_dict(response)
        response.result["side"] = side
        response.result["price"] = price
        response.result["qty"] = qty
        response.result["symbol"] = symbol

        if response.retCode != 0:
            raise Exception
        else:
            return Order.from_dict(response.result)

    def __ticker_handler(self, message: dict):
        #TODO добавить обработку исключений. Написать класс для handler
        try:
            self.__ticker_callback(TickerResponse.from_dict(message))
        except Exception as ex:
            print(ex)

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

        self.__ticker_socket.ticker_stream(symbol, self.__ticker_handler)