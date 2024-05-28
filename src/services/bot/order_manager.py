from decimal import Decimal
from typing import List, Callable, Optional, Union

from api import BybitClient
from domain_models import OrderStatus, CoinType
from schemas import SocketOperation, Order
from services.bot import Side
from core.log import logger
from services.bot.socket_bridges import OrderBridge


class OrderManager:
    on_order_filled: Optional[Callable[[Order], None]]

    __open_orders: List[Order]
    __client: BybitClient
    __is_first_connect: bool

    def __init__(
            self,
            client: BybitClient,
            order_bridge: OrderBridge,
            category: str,
            symbol: str
    ):
        self.on_order_filled = None
        self.__is_first_connect = True
        self.__symbol = symbol
        self.__category = category
        self.__client = client
        self.__order_bridge = order_bridge

        order_bridge.message_event.subscribe(self.__on_order_state_change)

        self.__reload_open_orders()

    @property
    def open_orders(self):
        return self.__open_orders

    def place_order(self, **kwargs):
        order = self.__client.place_order(**kwargs)
        self.__open_orders.append(order)

    def cancel_order(self, **kwargs):
        cancel_order_entity = self.__client.cancel_order(**kwargs)
        self.__open_orders = [order for order in self.__open_orders if order.order_id != cancel_order_entity.order_id]

    def place_orders_while_possible(self, **kwargs):
        while True:
            try:
                open_order = self.__client.place_order(**kwargs)
                self.__open_orders.append(open_order)
            # TODO типизировать ошибку
            except Exception as ex:
                logger.warning(f"Ошибка. {ex}")
                break

    def cancel_last_order(self, side: Side):
        exist_orders = [order for order in self.__open_orders if order.side == side]

        if not exist_orders:
            return

        cancel_order_id = exist_orders[-1].order_id

        try:
            self.__client.cancel_order(category=self.__category, orderId=cancel_order_id, symbol=self.__symbol)
            self.__open_orders.remove(exist_orders[-1])
            logger.info(f"(cancel last order) {exist_orders[-1]}")

        except Exception as ex:
            logger.warning(ex)

    def amend_all_orders(self, side: Side, price: Decimal):
        # Из-за возможных разрывов соединения WebSocket необходимо актуализировать информацию
        self.__reload_open_orders()
        amend_orders = [order for order in self.__open_orders if order.side == side]

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
                logger.warning(ex, exc_info=True)

    def exit(self):
        self.on_order_filled = None

    def sell_all(self, price_per_unit: Decimal, symbol: str):
        coins_names = [member.value for name, member in CoinType.__members__.items()]
        matches = []
        for coin_name in coins_names:
            if coin_name in symbol:
                matches.append(coin_name)

        if len(matches) != 2:
            raise ValueError()

        if symbol.index(matches[0]) == 0:
            base_coin = matches[0]
        else:
            base_coin = matches[1]

        self.__client.cancel_all_orders(category=self.__category)
        self.__open_orders = list()
        base_coin_balance = self.__client.wallet_balance(base_coin)

        if not base_coin_balance:
            return

        placed_order = self.__client.place_order(
            symbol=self.__symbol,
            orderType="Limit",
            category=self.__category,
            price=price_per_unit,
            qty=base_coin_balance.wallet_balance,
            side=Side.Sell
        )

        self.__open_orders = [placed_order]

    def __on_order_state_change(self, orders: [Order]):
        # for order in orders:
        #     if order.status == OrderStatus.Filled:
        #         self.__open_orders = [item for item in self.__open_orders if item.order_id != order.order_id]
        #         self.on_order_filled(order)

        # TODO заплатка
        for order in orders:
            if order.status == OrderStatus.Filled:
                self.__open_orders = [item for item in self.__open_orders if item.order_id != order.order_id]
                self.on_order_filled(order)
            break

    def __reload_open_orders(self):
        self.__open_orders = self.__client.get_open_orders(category=self.__category, symbol=self.__symbol)

    def __order_stream_handler(self, orders: [Order]):
        for order in orders:
            is_order_filled = order.status == OrderStatus.Filled
            is_order_canceled = order.status == OrderStatus.Cancelled

            if is_order_filled or is_order_canceled:
                self.__open_orders = [item for item in self.__open_orders if item.order_id != order.order_id]

            if is_order_filled and self.on_order_filled:
                self.on_order_filled(order)
            break # TODO заплатка

    def __socket_operation_handler(self, operation: SocketOperation):
        is_success_subscription = operation.op == "subscribe" and operation.success is True

        if is_success_subscription and not self.__is_first_connect:
            self.__reload_open_orders()

        if is_success_subscription:
            self.__is_first_connect = False

    def __del__(self):
        self.exit()
