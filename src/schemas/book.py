from typing import List, Any

from pydantic import BaseModel, Field


class Book(BaseModel):
    next_page_cursor: str = Field(alias="nextPageCursor")
    category: str
    list: List[Any]


