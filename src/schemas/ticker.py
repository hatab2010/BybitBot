from decimal import Decimal

from pydantic import BaseModel, Field


class TickerSnapshot(BaseModel):
    symbol: str
    last_price: Decimal = Field(..., alias='lastPrice')
    high_price_24h: Decimal = Field(..., alias='highPrice24h')
    low_price_24h: Decimal = Field(..., alias='lowPrice24h')
    previous_price_24h: Decimal = Field(..., alias='prevPrice24h')
    volume_24h: Decimal = Field(..., alias='volume24h')
    turnover_24h: Decimal = Field(..., alias='turnover24h')
    price_change_percent_24h: str = Field(..., alias='price24hPcnt')
    usd_index_price: Decimal = Field(..., alias='usdIndexPrice')