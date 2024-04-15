from decimal import Decimal
from pydantic import BaseModel, Field


class OrderEntity(BaseModel):
    order_id: str = Field(..., alias="orderId")


class Order(OrderEntity):
    symbol: str = Field(..., alias="symbol")
    side: str = Field(..., alias="side")
    order_type: str = Field(alias="orderType")
    cancel_type: str = Field(alias="cancelType")
    price: Decimal = Field(..., alias="price")
    qty: Decimal = Field(..., alias="qty")
    order_iv: str = Field(alias="orderIv")
    time_in_force: str = Field(..., alias="timeInForce")
    status: str = Field(..., alias="orderStatus")
