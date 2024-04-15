from typing import Any

from pydantic import BaseModel, Field


class EventMessage(BaseModel):
    topic: str
    timestamp: int = Field(..., alias='ts')
    message_type: str = Field(..., alias='type')
    checksum: int = Field(alias='cs')
    creation_timestamp: int = Field(alias='cts')
    data: Any


class APIResponse:
    ret_code: int = Field(..., alias='retCode')
    ret_msg: str = Field(..., alias='retMsg')
    result: Any = Field(alias='result')


class SocketOperation(BaseModel):
    success: bool
    ret_msg: str
    op: str
    conn_id: str
