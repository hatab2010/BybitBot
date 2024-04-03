from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Callable, Optional, Union

from pybit.unified_trading import WebSocket

from data import Bayer, Order, TickerResponse
from src.api.bybit_client import BybitClient
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


class BuyerOrderbookTrigger:
    triggered: Optional[Callable[[Side], None]]
    is_complete: bool

    __trade_range: Range
    __min_bid_size: Decimal

    def __init__(self, trade_range: Range, min_bid_size: Decimal):
        self.__trade_range = trade_range
        self.__min_bid_size = min_bid_size

    def set_range(self, trade_range: Range):
        pass


class TimeRangeTrigger:
    triggered: Optional[Callable[[Side], None]]

    __top_range: Range
    __bottom_range: Range
    __timer: Optional[Timer]
    __values: list[Decimal]
    __trigger_duration_buy: int
    __side: Side

    def __init__(
            self,
            target_range: Range,
            trigger_duration_buy: int,
            trigger_duration_sell: int
    ):
        self.triggered = None
        self.__timer = None
        self.__values = list()
        self.__trigger_duration_buy = trigger_duration_buy
        self.__trigger_duration_sell = trigger_duration_sell
        self.set_range(target_range)
        self.__side = Side.Buy

    def set_range(self, target_range):
        accept_height = target_range.height
        r_top_top = target_range.top + accept_height #* 2
        r_top_bottom = r_top_top - accept_height
        self.__top_range = Range(r_top_top, r_top_bottom)
        r_bottom_top = target_range.bottom #- accept_height
        r_bottom_bottom = r_bottom_top - accept_height
        self.__bottom_range = Range(r_bottom_top, r_bottom_bottom)
        print(f"{datetime.now()} SET TRIGGER AREA\n"
              f"BUY in:{r_top_top} out:{r_top_bottom}\n"
              f"SELL in:{r_bottom_bottom} out:{r_bottom_top}")
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
                    trigger_duration = self.__trigger_duration_buy
                else:
                    self.__side = Side.Sell
                    trigger_duration = self.__trigger_duration_sell

                self.__values.append(price)
                self.__timer = Timer(trigger_duration, self.__trigger)
                self.__timer.start()
                print(f"{datetime.now()} TRIGGER START\n"
                      f"side:{self.__side.value} price:{price}")

        is_outside_top_trigger_area = self.__side == Side.Buy and price < self.__top_range.bottom
        is_outside_bottom_trigger_area = self.__side == Side.Sell and price > self.__bottom_range.top
        if is_trigger_start and (is_outside_top_trigger_area or is_outside_bottom_trigger_area):
            print(f"{datetime.now()} TRIGGER STOP\n"
                  f"side:{self.__side.value} price:{price}")
            self.__reset()

    def __trigger(self):
        average_price = sum(self.__values) / len(self.__values)
        print("TRIGGER\n"
              f"average_price:{average_price}")

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
            else:
                self.__reset()

    def __reset(self):
        print("TRIGGER RESET")
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
    __trigger_time: int
    __is_overlap_top: bool
    __is_order_process: bool

    def __init__(
            self,
            client: BybitClient,
            trade_range: Range,
            qty: int,
            trigger: TimeRangeTrigger,
            allow_range: Range,
            overlap_top_price: Decimal,
            symbol: str
    ):
        self.__is_order_process = False
        self.__allow_range = allow_range
        self.__client = client
        self.__trade_range = trade_range
        self.__qty = qty
        self.__trigger = trigger
        self.__isDowngrade = False
        self.__overlap_top_price = overlap_top_price
        self.__is_overlap_top = self.__allow_range.top == self.__trade_range.top

        trigger.triggered = self.__offset_trade_range
        client.order_callback = self.__order_handler
        client.subscribe = self.__validate_open_orders
        self.set_symbol(symbol)

    def set_symbol(self, symbol: str):
        tick_size = self.__client.get_instrument_info(symbol).list[0].priceFilter.tick_size
        self.__symbol_info = SymbolInfo(symbol, tick_size, None)
        self.__client.ticker_stream(symbol, self.__ticker_handler)

    def set_orders_count(self, count: int, side: Side):
        open_orders = self.__client.get_open_orders(self.__symbol_info.symbol)
        need_to_create = count - len(open_orders)
        price = self.__trade_range.bottom if side == Side.Buy else self.__trade_range.top

        if need_to_create > 0:
            for index in range(need_to_create):
                self.__client.place_order(
                    symbol=self.__symbol_info.symbol,
                    side=str(side.value),
                    price=price,
                    qty=self.__qty
                )

    def __validate_open_orders(self):
        print("VALIDATE ORDERS")

        # if ht_order is not None:
        self.__order_process(Side.Buy)
        self.__order_process(Side.Sell)

    def __offset_trade_range(self, direction: Side):
        print(f"{datetime.now()} TRIGGER")
        is_outside_bottom = self.__trade_range.bottom <= self.__allow_range.bottom and direction == Side.Sell
        is_outside_top = self.__trade_range.top >= self.__allow_range.top and direction == Side.Buy

        if is_outside_bottom or is_outside_top:
            print(f"OUTSIDE IN ALLOW PRICE RANGE\n"
                  f"allow_range[{self.__allow_range.bottom},{self.__allow_range.top}]\n "
                  f"trade_range[{self.__trade_range.bottom},[{self.__trade_range.bottom}]]")
            return

        if direction == Side.Buy:
            self.__trade_range.offset(1)
        else:
            self.__trade_range.offset(-1)

        print(f"new trade_range [{self.__trade_range.bottom},{self.__trade_range.top}]")

        self.__is_overlap_top = self.__allow_range.top == self.__trade_range.top

        self.__update_orders(direction)
        self.__trigger.set_range(self.__trade_range)

    def __update_orders(self, side: Side):
        print(f"UPDATE ORDERS")
        open_orders = self.__client.get_open_orders(self.__symbol_info.symbol)
        update_orders = [order for order in open_orders if order.side == side]
        price = self.__trade_range.bottom if side == Side.Buy else self.__trade_range.top

        for order in update_orders:
            try:
                self.__client.amend_order(
                    order.symbol,
                    order.orderId,
                    price
                )
            except Exception as ex:
                print(ex)

    def __order_handler(self, orders: list[Order]):
        for order in orders:
            if order.orderStatus == OrderStatus.Filled:
                self.__order_process(order.side)

    def __order_process(self, side: Union[str, Side]):
        if self.__is_order_process:
            return

        self.__is_order_process = True
        last_open_order = None

        while True:
            try:
                # Выполнен ордер на закупку
                if side == Side.Buy:
                    # Меняем цену продажи на верхней границе торгового коридора
                    if self.__is_overlap_top:
                        ctx_price = self.__overlap_top_price
                    else:
                        ctx_price = self.__trade_range.top
                    ctx_side = Side.Sell.value
                # Выполнен ордер на продажу
                else:
                    ctx_price = self.__trade_range.bottom
                    ctx_side = Side.Buy.value

                open_order = self.__client.place_order(
                    symbol=self.__symbol_info.symbol,
                    side=ctx_side,
                    price=ctx_price,
                    qty=self.__qty
                )
                last_open_order = open_order
            except Exception as ex:
                if last_open_order is not None and side == Side.Sell:
                    self.__client.remove_order(self.__symbol_info.symbol, last_open_order.orderId)
                self.__is_order_process = False
                print(f"ошибка. {ex}")
                break

    def __ticker_handler(self, response: TickerResponse):
        lastPrice = response.data.lastPrice
        self.__trigger.push(Decimal(lastPrice))
        self.__symbol_info.last_price = lastPrice
