from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Union, Optional

from pybit.unified_trading import WebSocket

from api import BybitClient
from core.log import logger
from schemas.order import Order
from domain_models import Side, TradeRange
from services.bot.order_manager import OrderManager
from .socket_bridges import TickerBridge, OrderbookBridge
from services.bot.triggers import TimeRangeTrigger, OrderbookTrigger


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
    __time_trigger: TimeRangeTrigger
    __orderbook_trigger: OrderbookTrigger
    __symbol_info: SymbolInfo
    __ticker_socket: WebSocket
    __trigger_time: int
    __is_overlap_sell_price: bool
    __is_order_placement_in_progress: bool
    __client: BybitClient

    __order_manager: OrderManager
    __options: BotOptions

    __ticker_bridge: TickerBridge

    def __init__(
            self,
            symbol: str,
            options: BotOptions,
            client: BybitClient,
            orderbook_trigger: OrderbookTrigger,
            time_trigger: TimeRangeTrigger,
            bridge_hub: SocketBridgesHub
    ):
        self.__order_manager = OrderManager(symbol=options.symbol, category=options.category, client=client)
        self.__order_manager.on_order_filled = self.__on_order_filled
        self.__options = options
        self.__is_order_placement_in_progress = False
        self.__time_trigger = time_trigger
        self.__is_overlap_sell_price = self.__options.allow_range.sell == self.__options.trade_range.sell

        # time_trigger.on_triggered = self.__offset_trade_range
        time_trigger.on_triggered = self.__on_time_trigger
        orderbook_trigger.on_triggered = self.__on_orderbook_trigger
        self.set_symbol(options.symbol)

    def set_symbol(self, symbol: str):
        tick_size = self.__client.get_instrument_info(symbol, "spot").list[0].priceFilter.tick_size
        self.__symbol_info = SymbolInfo(symbol, tick_size, None)
        self.__order_manager.exit()
        self.__order_manager = OrderManager(self.__client, symbol, self.__options.category)

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

    def __on_time_trigger(self, side: Side):
        self.__offset_trade_range(side)

    def __on_orderbook_trigger(self, side: Side):
        if side == Side.Buy:
            self.__offset_trade_range(Side.Buy)

    def __on_order_filled(self, order: Order):
        self.__create_orders_while_possible(order.side)

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

        # Обновляем значение триггеров
        self.__time_trigger.set_range_and_restart(self.__options.trade_range)
        self.__orderbook_trigger.set_range_and_restart(self.__options.trade_range)

    def __amend_all_orders(self, side: Side):
        print(f"Amend all orders in side {side.value}")
        price = self.__options.trade_range.buy if side == Side.Buy else self.__options.trade_range.sell
        self.__order_manager.amend_all_orders(side=side, price=price)

    def __create_orders_while_possible(self, side: Union[str, Side]):

        if self.__is_order_placement_in_progress:
            return

        self.__is_order_placement_in_progress = True

        if side == Side.Sell:
            # Меняем цену продажи на верхней границе торгового коридора
            if self.__is_overlap_sell_price:
                price = self.__options.overlap_top_price
            else:
                price = self.__options.trade_range.sell
            # ctx_side = Side.Sell.value
        else:
            price = self.__options.trade_range.buy
            # ctx_side = Side.Buy.value

        if type(side) is Side:
            side = side.value

        self.__order_manager.place_orders_while_possible(
            symbol=self.__symbol_info.symbol,
            side=str(side),
            price=price,
            orderType="Limit",
            timeInForce="GTC",
            category="spot",
            qty=self.__options.qty
        )
        self.__order_manager.cancel_last_order(side)

        self.__is_order_placement_in_progress = False
