from decimal import Decimal
from pydantic import BaseModel, Field


class Setting(BaseModel):
    is_testnet: bool = Field(..., alias="isTestnet")
    key: str = Field(...)
    secret_key: str = Field(..., alias="secretKey")
    allow_top_price: Decimal = Field(..., alias="allowTopPrice")
    allow_bottom_price: Decimal = Field(..., alias="allowBottomPrice")
    overlap_sell_price: Decimal = Field(..., alias="overlapSellPrice")
    trade_amount: int = Field(..., alias="tradeAmount")
    order_count: int = Field(..., alias="orderCount")
    symbol: str = Field(...)
    trigger_duration_buy: int = Field(..., alias="triggerDurationBuy")
    trigger_duration_sell: int = Field(..., alias="triggerDurationSell")
    side: int = Field(...)


