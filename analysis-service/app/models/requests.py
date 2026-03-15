from typing import Any, Literal
from pydantic import BaseModel, Field


class FilterCondition(BaseModel):
    column: str
    op: Literal["eq", "ne", "gt", "gte", "lt", "lte", "like", "in"] = "eq"
    value: Any


class StatisticsRequest(BaseModel):
    table: str
    columns: list[str] = Field(min_length=1)
    filters: list[FilterCondition] = []


class TimeseriesRequest(BaseModel):
    table: str
    time_column: str
    value_column: str
    agg_func: Literal["sum", "mean", "count"] = "sum"
    freq: str = "1D"
    filters: list[FilterCondition] = []


class DistributionRequest(BaseModel):
    table: str
    column: str
    bins: int = Field(default=30, ge=2, le=200)
    filters: list[FilterCondition] = []


class CorrelationRequest(BaseModel):
    table: str
    columns: list[str] = Field(min_length=2)
    method: Literal["pearson", "spearman"] = "pearson"
    filters: list[FilterCondition] = []


class GroupbyRequest(BaseModel):
    table: str
    group_columns: list[str] = Field(min_length=1)
    agg_column: str
    agg_func: Literal["sum", "mean", "count", "max", "min"] = "sum"
    filters: list[FilterCondition] = []
    limit: int = Field(default=100, ge=1, le=5000)
