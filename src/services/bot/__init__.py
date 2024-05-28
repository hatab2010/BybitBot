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
from .socket_bridges import TickerBridge, OrderbookBridge, OrderBridge
from services.bot.triggers import TimeRangeTrigger, OrderbookTrigger


@dataclass
class SymbolInfo:
    symbol: str
    tick_size: Decimal
    last_price: Optional[Decimal]


@dataclass
class BotOptions:
    category: str
    symbol: str
    qty: int
    allow_range: TradeRange
    trade_range: TradeRange
    overlap_top_price: Decimal


@dataclass
class SocketBridgesHub:
    ticket: TickerBridge
    orderbook: OrderbookBridge


class BybitBotService:
    __symbol_info: Optional[SymbolInfo]
    __is_order_placement_in_progress: bool

    __client: BybitClient
    __order_manager: OrderManager
    __options: BotOptions

    __time_trigger: TimeRangeTrigger
    __orderbook_trigger: OrderbookTrigger

    def __init__(
            self,
            order_bridge: OrderBridge,
            options: BotOptions,
            client: BybitClient,
            orderbook_trigger: OrderbookTrigger,
            time_trigger: TimeRangeTrigger,
    ):
        self.__order_manager = OrderManager(
            symbol=options.symbol,
            order_bridge=order_bridge,
            category=options.category,
            client=client)

        self.__client = client
        self.__is_order_placement_in_progress = False
        self.__order_manager.on_order_filled = self.__on_order_filled
        self.__options = options
        self.__time_trigger = time_trigger
        self.__orderbook_trigger = orderbook_trigger
        self.__is_overlap_sell_price = self.__options.allow_range.sell == self.__options.trade_range.sell

        time_trigger.on_triggered = self.__on_time_trigger
        orderbook_trigger.on_triggered = self.__on_orderbook_trigger
        self.get_symbol_info()
        self.__two_side_create_orders()

        self.__time_trigger.reset()
        self.__orderbook_trigger.reset()

    def get_symbol_info(self):
        tick_size = self.__client.get_instrument_info(self.__options.symbol, "spot").list[0].priceFilter.tick_size
        self.__symbol_info = SymbolInfo(self.__options.symbol, tick_size, None)
        # TODO order_manager.set_symbol()

    def __on_time_trigger(self, direction: Side):
        self.__offset_trade_range(direction)

        if direction == direction.Sell:
            self.__amend_all_orders(Side.Buy)
        else:
            self.__order_manager.sell_all(price_per_unit=self.__options.trade_range.sell, symbol=self.__options.symbol)

    def __on_orderbook_trigger(self, side: Side):
        if side == Side.Buy:
            self.__offset_trade_range(Side.Buy)
            self.__order_manager.sell_all(price_per_unit=self.__options.trade_range.sell, symbol=self.__options.symbol)
            self.__two_side_create_orders()

    def __on_order_filled(self, order: Order):
        if order.side == Side.Sell:
            side = Side.Buy
        else:
            side = Side.Sell

        self.__create_orders_while_possible(side)

    def __two_side_create_orders(self):
        self.__create_orders_while_possible(Side.Buy)
        self.__create_orders_while_possible(Side.Sell)

    def __offset_trade_range(self, direction: Side):
        logger.info(f"{datetime.now()} TRIGGER")
        is_outside_bottom = self.__options.trade_range.buy <= self.__options.allow_range.buy and direction == Side.Buy
        is_outside_top = self.__options.trade_range.sell >= self.__options.allow_range.sell and direction == Side.Sell

        if is_outside_bottom or is_outside_top:
            logger.info(f"OUTSIDE IN ALLOW PRICE RANGE\n"
                        f"allow_range[{self.__options.allow_range.buy},{self.__options.allow_range.sell}]\n "
                        f"trade_range[{self.__options.trade_range.buy},[{self.__options.trade_range.buy}]]")
            return

        trade_offset = 1 if direction == Side.Sell else -1
        self.__options.trade_range.offset(trade_offset)

        logger.info(f"new trade_range [{self.__options.trade_range.buy},{self.__options.trade_range.sell}]")

        # Обновляем значение триггеров
        self.__time_trigger.set_range_and_restart(self.__options.trade_range)
        self.__orderbook_trigger.set_range_and_restart(self.__options.trade_range)

    def __amend_all_orders(self, side: Side):
        price = self.__options.trade_range.buy if side == Side.Buy else self.__options.trade_range.sell
        self.__order_manager.amend_all_orders(side=side, price=price)

    def __create_orders_while_possible(self, side: Union[str, Side]):
        if self.__is_order_placement_in_progress:
            return

        is_outside_bottom = self.__options.trade_range.buy <= self.__options.allow_range.buy and side == Side.Sell
        is_outside_top = self.__options.trade_range.sell >= self.__options.allow_range.sell and side == Side.Buy

        if is_outside_bottom:
            return

        self.__is_order_placement_in_progress = True

        if side == Side.Sell:
            # Меняем цену продажи на верхней границе торгового коридора
            if is_outside_top:
                price = self.__options.overlap_top_price
            else:
                price = self.__options.trade_range.sell
        else:
            price = self.__options.trade_range.buy

        is_success = self.__order_manager.place_orders_while_possible(
            symbol=self.__symbol_info.symbol,
            side=str(side),
            price=price,
            orderType="Limit",
            timeInForce="GTC",
            category="spot",
            qty=self.__options.qty
        )

        if is_success:
            self.__order_manager.cancel_last_order(side)

        self.__is_order_placement_in_progress = False
