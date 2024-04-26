from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class Coin(BaseModel):
    available_to_borrow: str = Field(alias='availableToBorrow')
    bonus: str
    accrued_interest: Optional[str] = Field(alias='accruedInterest')
    available_to_withdraw: Decimal = Field(alias='availableToWithdraw')
    total_order_im: str = Field(alias='totalOrderIM')
    equity: Decimal
    total_position_mm: str = Field(alias='totalPositionMM')
    usd_value: Decimal = Field(alias='usdValue')
    unrealised_pnl: str = Field(alias='unrealisedPnl')
    collateral_switch: bool = Field(alias='collateralSwitch')
    spot_hedging_qty: str = Field(alias='spotHedgingQty')
    borrow_amount: str = Field(alias='borrowAmount')
    total_position_im: str = Field(alias='totalPositionIM')
    wallet_balance: Decimal = Field(alias='walletBalance')
    cum_realised_pnl: str = Field(alias='cumRealisedPnl')
    locked: str
    margin_collateral: bool = Field(alias='marginCollateral')
    coin: str


class Account(BaseModel):
    total_equity: str = Field(alias='totalEquity')
    account_im_rate: str = Field(alias='accountIMRate')
    total_margin_balance: Decimal = Field(alias='totalMarginBalance')
    total_initial_margin: Decimal = Field(alias='totalInitialMargin')
    account_type: str = Field(alias='accountType')
    total_available_balance: Decimal = Field(alias='totalAvailableBalance')
    account_mm_rate: str = Field(alias='accountMMRate')
    total_perp_upl: str = Field(alias='totalPerpUPL')
    total_wallet_balance: Decimal = Field(alias='totalWalletBalance')
    account_ltv: str = Field(alias='accountLTV')
    total_maintenance_margin: str = Field(alias='totalMaintenanceMargin')
    coins: List[Coin] = Field(alias="coin")
