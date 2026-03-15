from typing import Any
from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool


class TablesResponse(BaseModel):
    tables: list[str]


class ColumnsResponse(BaseModel):
    table: str
    columns: list[ColumnInfo]


class AnalysisResponse(BaseModel):
    type: str
    data: Any


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
