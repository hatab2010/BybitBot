from typing import Any

from pydantic import BaseModel, Field


class Snapshot(BaseModel):
    topic: str
    timestamp: int = Field(..., alias='ts')
    message_type: str = Field(..., alias='type')
    checksum: int = Field(alias='cs')
    creation_timestamp: int = Field(alias='cts')
    data: Any


class RestMessage:
    ret_code: int = Field(..., alias='retCode')
    ret_msg: str = Field(..., alias='retMsg')
    result: Any = Field(alias='result')


class SocketEvent(BaseModel):
    success: bool
    ret_msg: str
    operation: str
    connection_id: str
