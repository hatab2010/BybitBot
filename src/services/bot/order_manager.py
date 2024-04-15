from decimal import Decimal
from typing import List, Union, Callable, Optional

from pybit.unified_trading import WebSocket

from api import BybitClient
from domain_models import OrderStatus
from schemas import SocketOperation, Order
from services.bot import Side


class OrderManager:
    on_order_filled: Optional[Callable[[Order], None]]
    open_orders: List[Order]

    __client: BybitClient
    __is_first_connect: bool
    __order_socket: WebSocket

    def __init__(self, client: BybitClient, symbol: str, category: str):
        self.on_order_filled = None
        self.__is_first_connect = True
        self.__symbol = symbol
        self.__category = category
        self.__client = client

        self.__order_socket = client.websocket.order.stream(
            symbol=symbol,
            callback=self.__order_stream_handler,
            operation_callback=self.__socket_operation_handler,
            channel_type="private"
        )

        self.__reload_open_orders()

    def place_order(self, **kwargs):
        order = self.__client.place_order(**kwargs)
        self.open_orders.append(order)

    def cancel_order(self, **kwargs):
        cancel_order_entity = self.__client.cancel_order(**kwargs)
        self.open_orders = [order for order in self.open_orders if order.order_id != cancel_order_entity.order_id]

    def place_orders_while_possible(self, **kwargs):
        while True:
            try:
                open_order = self.__client.place_order(**kwargs)
                self.open_orders.append(open_order)
            # TODO типизировать ошибку
            except Exception as ex:
                print(f"Ошибка. {ex}")
                break

    def cancel_last_order(self, side: Side):
        exist_orders = [order for order in self.open_orders if order.side == side]

        if exist_orders:
            cancel_order_id = exist_orders[-1].order_id
            self.__client.cancel_order(category=self.__category, orderId=cancel_order_id, symbol=self.__symbol)
            self.open_orders.remove(exist_orders[-1])

    def amend_all_orders(self, side: Side, price: Decimal):
        # Из-за возможных разрывов соединения WebSocket необходимо актуализировать информацию
        self.__reload_open_orders()
        amend_orders = [order for order in self.open_orders if order.side == side]

        for amend_order in amend_orders:
            try:
                self.__client.amend_order(
                    symbol=amend_order.symbol,
                    category=self.__category,
                    orderId=amend_order.order_id,
                    price=price
                )
                amend_order.price = price
            except Exception as ex:
                print(ex)

    def __reload_open_orders(self):
        __open_orders = self.__client.get_open_orders(category=self.__category, symbol=self.__symbol)

    def __order_stream_handler(self, order: Order):
        is_order_filled = order.status == OrderStatus.Filled
        is_order_canceled = order.status == OrderStatus.Cancelled

        if is_order_filled or is_order_canceled:
            self.open_orders = [item for item in self.open_orders if item.order_id != order.order_id]

        if is_order_filled and self.on_order_filled:
            self.on_order_filled(order)

    def __socket_operation_handler(self, operation: SocketOperation):
        is_success_subscription = operation.op == "subscribe" and operation.success is True

        if is_success_subscription and not self.__is_first_connect:
            self.__reload_open_orders()

        if is_success_subscription:
            self.__is_first_connect = False

    def exit(self):
        self.__order_socket.exit()
        self.on_order_filled = None

    def __del__(self):
        self.exit()
