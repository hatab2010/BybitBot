from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class OrderEntity(BaseModel):
    order_id: str = Field(..., alias="orderId")


class Order(OrderEntity):
    symbol: str = Field(..., alias="symbol")
    side: str = Field(..., alias="side")
    order_type: Optional[str] = Field(alias="orderType", default=None)
    cancel_type: Optional[str] = Field(alias="cancelType", default=None)
    price: Decimal = Field(..., alias="price")
    qty: Decimal = Field(..., alias="qty")
    order_iv: Optional[str] = Field(alias="orderIv", default=None)
    # time_in_force: str = Field(alias="timeInForce", default=datetime.now)
    status: str = Field(..., alias="orderStatus")
