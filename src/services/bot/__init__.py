from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Union, Optional

from pybit.unified_trading import WebSocket

from api import BybitClient
from schemas.order import Order
from domain_models import Side, TradeRange
from services.bot.order_manager import OrderManager
from socket_bridges import TickerBridge, OrderbookBridge
from services.bot.triggers import TimeRangeTrigger


@dataclass
class SymbolInfo:
    symbol: str
    tick_size: Decimal
    last_price: Optional[Decimal]


@dataclass
class BotOptions:
    trade_range: TradeRange
    qty: int
    allow_range: TradeRange
    overlap_top_price: Decimal
    symbol: str
    category: str

@dataclass
class SocketBridgesHub:
    ticket: TickerBridge
    orderbook: OrderbookBridge


class BybitBotService:
    __trigger: TimeRangeTrigger
    __symbol_info: SymbolInfo
    __ticker_socket: WebSocket
    __trigger_time: int
    __is_overlap_sell_price: bool
    __is_order_process: bool

    __order_manager: OrderManager
    __options: BotOptions

    def __init__(
            self,
            options: BotOptions,
            client: BybitClient,
            trigger: TimeRangeTrigger
    ):
        self.__order_manager = OrderManager(symbol=options.symbol, category=options.category, client=client)
        self.__order_manager.on_order_filled = self.on_order_filled
        self.__options = options
        self.__is_order_process = False
        self.__trigger = trigger
        self.__is_overlap_sell_price = self.__options.allow_range.sell == self.__options.trade_range.sell

        trigger.triggered = self.__offset_trade_range
        # client.order_callback = self.__order_handler
        # client.on_success_subscribe = self.__two_side_create_orders
        self.set_symbol(options.symbol)

    def set_symbol(self, symbol: str):
        tick_size = self.__client.get_instrument_info(symbol, "spot").list[0].priceFilter.tick_size
        self.__symbol_info = SymbolInfo(symbol, tick_size, None)
        del self.__order_manager
        self.__order_manager = OrderManager(self.__client, symbol, self.__options.category)
        self.__client.websocket.ticker.stream(symbol, "spot", self.__ticker_handler)

    def set_orders_count(self, count: int, side: Side):
        need_to_create = count - len(self.__order_manager.open_orders)
        price = self.__options.trade_range.buy if side == Side.Buy else self.__options.trade_range.sell

        if need_to_create > 0:
            for index in range(need_to_create):
                self.__order_manager.place_order(
                    category="spot",
                    symbol=self.__symbol_info.symbol,
                    side=str(side.value),
                    price=price,
                    qty=self.__options.qty
                )

    def __two_side_create_orders(self):
        print("VALIDATE ORDERS")

        self.__create_orders_while_possible(Side.Buy)
        self.__create_orders_while_possible(Side.Sell)

    def __offset_trade_range(self, direction: Side):
        print(f"{datetime.now()} TRIGGER")
        is_outside_bottom = self.__options.trade_range.buy <= self.__options.allow_range.buy and direction == Side.Sell
        is_outside_top = self.__options.trade_range.sell >= self.__options.allow_range.sell and direction == Side.Buy

        if is_outside_bottom or is_outside_top:
            print(f"OUTSIDE IN ALLOW PRICE RANGE\n"
                  f"allow_range[{self.__options.allow_range.buy},{self.__options.allow_range.sell}]\n "
                  f"trade_range[{self.__options.trade_range.buy},[{self.__options.trade_range.buy}]]")
            return

        if direction == Side.Buy:
            self.__options.trade_range.offset(1)
        else:
            self.__options.trade_range.offset(-1)

        print(f"new trade_range [{self.__options.trade_range.buy},{self.__options.trade_range.sell}]")

        self.__is_overlap_sell_price = self.__options.allow_range.sell == self.__options.trade_range.sell

        self.__amend_all_orders(direction)
        self.__trigger.set_range(self.__options.trade_range)

    def __amend_all_orders(self, side: Side):
        print(f"Amend all orders in side {side.value}")
        price = self.__options.trade_range.buy if side == Side.Buy else self.__options.trade_range.sell
        self.__order_manager.amend_all_orders(side=side, price=price)

    def on_order_filled(self, order: Order):
        self.__create_orders_while_possible(order.side)

    # def __order_handler(self, orders: list[Order]):
    #     for order in orders:
    #         if order.status == OrderStatus.Filled:
    #             pass

    def __create_orders_while_possible(self, side: Union[str, Side]):
        if self.__is_order_process:
            return

        self.__is_order_process = True
        last_open_order = None

        while True:
            try:
                # Выполнен ордер на закупку
                if side == Side.Buy:
                    # Меняем цену продажи на верхней границе торгового коридора
                    if self.__is_overlap_sell_price:
                        ctx_price = self.__overlap_top_price
                    else:
                        ctx_price = self.__trade_range.sell
                    ctx_side = Side.Sell.value
                # Выполнен ордер на продажу
                else:
                    ctx_price = self.__trade_range.buy
                    ctx_side = Side.Buy.value

                open_order = self.__client.place_order(
                    symbol=self.__symbol_info.symbol,
                    side=ctx_side,
                    price=ctx_price,
                    orderType="Limit",
                    timeInForce="GTC",
                    category="spot",
                    qty=self.__qty
                )

                last_open_order = open_order
            except Exception as ex:
                if last_open_order is not None and side == Side.Sell:
                    self.__client.cancel_order(
                        category="spot",
                        symbol=self.__symbol_info.symbol,
                        orderId=last_open_order.order_id
                    )
                self.__is_order_process = False
                print(f"ошибка. {ex}")
                break

    def __ticker_handler(self, response: TickerResponse):
        self.__trigger.__push(Decimal(response.data.lastPrice))
        self.__symbol_info.last_price = response.data.lastPrice
