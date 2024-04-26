from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator


class Setting(BaseModel):
    is_testnet: bool = Field(..., alias="isTestnet")
    key: str = Field(...)
    secret_key: str = Field(..., alias="secretKey")
    allow_top_price: Decimal = Field(..., alias="allowTopPrice")
    allow_bottom_price: Decimal = Field(..., alias="allowBottomPrice")
    overlap_sell_price: Decimal = Field(..., alias="overlapSellPrice", validate_default=True)
    trade_amount: int = Field(..., alias="tradeAmount")
    order_count: int = Field(..., alias="orderCount")
    symbol: str = Field(...)
    min_bid_size: Decimal = Field(..., alias="MinBidSize")
    min_ask_size: Decimal = Field(..., alias="MinAskSize")
    trigger_duration_buy: int = Field(..., alias="triggerDurationBuy")
    trigger_duration_sell: int = Field(..., alias="triggerDurationSell")
    side: int = Field(...)

    @model_validator(mode="after")
    def validate_overlap_price(self):
        if self.overlap_sell_price < self.allow_top_price:
            raise Exception("Неверно заданы настройки: overlapSellPrice < allowTopPrice")
        pass



