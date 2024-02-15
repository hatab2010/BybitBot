from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Callable, Optional, Union

from pybit.unified_trading import WebSocket

from data import Order, TickerResponse
from models import BybitClient
from threading import Timer


class OrderStatus(str, Enum):
    Filled = "Filled",
    New = "New"


class Side(str, Enum):
    Buy = "Buy",
    Sell = "Sell"


class Range:
    __top: Decimal
    __bottom: Decimal

    def __init__(self, top: Decimal, bottom: Decimal):
        self.__bottom = bottom
        self.__top = top

    @property
    def top(self) -> Decimal:
        return self.__top

    @property
    def bottom(self) -> Decimal:
        return self.__bottom

    @property
    def height(self) -> Decimal:
        return abs(self.__top - self.__bottom)

    def offset(self, step_offset: Union[int, Decimal]):
        length = self.height * step_offset
        self.__top = self.__top + length
        self.__bottom = self.__bottom + length


@dataclass
class SymbolInfo:
    symbol: str
    tick_size: Decimal
    last_price: Optional[Decimal]


class TimeRangeTrigger:
    triggered: Optional[Callable[[Side], None]]

    __top_range: Range
    __bottom_range: Range
    __timer: Optional[Timer]
    __values: list[Decimal]
    __accept_duration: int
    __side: Side

    def __init__(
            self,
            target_range: Range,
            accept_height: Decimal, #TODO дополнрительный параметр
            trigger_duration: int
    ):
        self.__timer = None
        self.__values = list()
        self.__accept_duration = trigger_duration
        self.set_range(target_range)
        self.__side = Side.Buy

    def set_range(self, target_range):
        accept_height = target_range.height
        r_top_top = target_range.top + accept_height * 2
        r_top_bottom = r_top_top - accept_height
        self.__top_range = Range(r_top_top, r_top_bottom)
        r_bottom_top = target_range.bottom - accept_height
        r_bottom_bottom = r_bottom_top - accept_height
        self.__bottom_range = Range(r_bottom_top, r_bottom_bottom)
        self.__reset()

    def push(self, price: Decimal):
        is_trigger_start = self.__timer is not None

        if is_trigger_start:
            self.__values.append(price)

        if not is_trigger_start:
            is_trigger_area = price >= self.__top_range.top or price <= self.__bottom_range.bottom

            if is_trigger_area:
                self.__values = list()

                if price >= self.__top_range.bottom:
                    self.__side = Side.Buy
                else:
                    self.__side = Side.Sell

                self.__values.append(price)
                self.__timer = Timer(self.__accept_duration, self.__trigger)
                self.__timer.start()

        is_outside_top_trigger_area = self.__side == Side.Buy and price < self.__top_range.bottom
        is_outside_bottom_trigger_area = self.__side == Side.Sell and price > self.__bottom_range.top
        if is_trigger_start and (is_outside_top_trigger_area or is_outside_bottom_trigger_area):
            self.__reset()

    def __trigger(self):
        average_price = sum(self.__values)/len(self.__values)

        if self.__side == Side.Buy:
            offset_top = self.__top_range.top - average_price
            offset_bottom = average_price - self.__top_range.bottom

            if offset_top < offset_bottom or average_price >= self.__top_range.top:

                if self.triggered:
                    self.triggered(self.__side)
                    self.__reset()
            else:
                self.__reset()
        else:
            offset_top = self.__bottom_range.top - average_price
            offset_bottom = average_price - self.__bottom_range.bottom
            if offset_bottom < offset_top or average_price < self.__bottom_range.bottom:

                if self.triggered:
                    self.triggered(self.__side)
                    self.__reset()

    def __reset(self):
        if self.__timer:
            self.__timer.cancel()
        self.__timer = None
        self.__values = list()


class BybitBotService:
    __trade_range: Range
    __allow_range: Range
    __trigger: TimeRangeTrigger
    __qty: int
    __symbol_info: SymbolInfo
    __ticker_socket: WebSocket
    __client: BybitClient
    __open_orders: list[Order] = list()
    __trigger_time: int

    def __init__(
            self,
            client: BybitClient,
            trade_range: Range,
            qty: int,
            trigger: TimeRangeTrigger,
            allow_range: Range
    ):
        self.__allow_range = allow_range
        self.__client = client
        self.__trade_range = trade_range
        self.__qty = qty
        self.__trigger = trigger
        self.__trigger.triggered = self.__triggered

        client.order_callback = self.__order_callback

    def set_symbol(self, symbol: str):
        tick_size = self.__client.get_instrument_info(symbol).list[0].priceFilter.tick_size

        self.__open_orders = list()
        self.__symbol_info = SymbolInfo(symbol, tick_size, None)
        self.__client.ticker_stream(symbol, self.__ticker_callback)

    def start(self, order_pool_count: int):
        for index in range(order_pool_count):
            open_order = self.__client.place_order(
                symbol=self.__symbol_info.symbol,
                side=str(Side.Buy.value),
                price=self.__trade_range.bottom,
                qty=self.__qty
            )

            self.__open_orders.append(open_order)

    def __triggered(self, side: Side):
        is_outside_bottom = self.__allow_range.bottom > self.__trade_range.bottom
        is_outside_top = self.__allow_range.top < self.__trade_range.top

        # TODO Изменить метод проверки
        if is_outside_bottom or is_outside_top:
            print("Outside in allow price range")
            return

        if side == Side.Buy:
            self.__trade_range.offset(1)
            self.__upgrade_buy_order()

        if side == Side.Sell:
            self.__downgrade_sell_order()
            self.__trade_range.offset(-1)

        self.__trigger.set_range(self.__trade_range)

    def __upgrade_buy_order(self) -> int:
        buy_orders = [order for order in self.__open_orders if order.side == Side.Buy]

        for order in buy_orders:
            order.price = self.__trade_range.bottom
            # self.__client.remove_order(order.symbol, order.orderId)
            self.__client.amend_order(
                order.symbol,
                order.orderId,
                order.price
            )
            # self.__open_orders.remove(order)

        return len(buy_orders)

    def __downgrade_sell_order(self):
        sell_orders = [order for order in self.__open_orders if order.side == Side.Sell]

        for order in sell_orders:
            order.price = self.__trade_range.bottom

            self.__client.amend_order(
                order.symbol,
                order.orderId,
                order.price
            )

    def __order_callback(self, orders: list[Order]):
        for order in orders:
            if order.orderStatus == OrderStatus.Filled:
                ctx_order = next((item for item in self.__open_orders if item.orderId == order.orderId), None)

                if ctx_order is None:
                    return

                self.__open_orders.remove(ctx_order)

                if order.side == Side.Buy:
                    ctx_price = self.__trade_range.top
                    ctx_side = Side.Sell.value
                else:
                    ctx_price = self.__trade_range.bottom
                    ctx_side = Side.Buy.value

                open_order = self.__client.place_order(
                    symbol=self.__symbol_info.symbol,
                    side=ctx_side,
                    price=ctx_price,
                    qty=self.__qty
                )

                self.__open_orders.append(open_order)

    def __ticker_callback(self, response: TickerResponse):
        lastPrice = response.data.lastPrice
        print(f"{datetime.now()}: {self.__symbol_info.symbol} price {lastPrice}")
        self.__trigger.push(Decimal(lastPrice))
        self.__symbol_info.last_price = lastPrice