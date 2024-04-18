from typing import Any, Optional, Dict

from pydantic import BaseModel, Field


class EventMessage(BaseModel):
    topic: str
    timestamp: int = Field(..., alias='ts')
    message_type: str = Field(..., alias='type')
    checksum: Optional[int] = Field(alias='cs', default=None)
    creation_timestamp: Optional[int] = Field(alias='cts', default=None)
    data: Dict


class APIResponse(BaseModel):
    ret_code: int = Field(alias='retCode')
    ret_msg: str = Field(alias='retMsg')
    result: Any = Field(alias='result')


class SocketOperation(BaseModel):
    success: bool
    ret_msg: str
    op: str
    conn_id: str
