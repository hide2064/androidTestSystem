from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.models.requests import FilterCondition


ALLOWED_OPS = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
    "in": "IN",
}


def validate_identifier(name: str) -> str:
    """テーブル名・カラム名にバッククォートを付けてSQLインジェクションを防ぐ。"""
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"Invalid identifier: {name!r}")
    return f"`{name}`"


def build_where_clause(
    filters: list[FilterCondition],
) -> tuple[str, dict[str, Any]]:
    """WHERE句とバインドパラメータを生成する。"""
    if not filters:
        return "", {}

    clauses = []
    params: dict[str, Any] = {}

    for i, f in enumerate(filters):
        col = validate_identifier(f.column)
        op = ALLOWED_OPS[f.op]
        param_key = f"p_{i}"

        if f.op == "in":
            if not isinstance(f.value, list):
                raise ValueError("'in' operator requires a list value")
            keys = [f"{param_key}_{j}" for j in range(len(f.value))]
            placeholders = ", ".join(f":{k}" for k in keys)
            clauses.append(f"{col} IN ({placeholders})")
            for k, v in zip(keys, f.value):
                params[k] = v
        else:
            clauses.append(f"{col} {op} :{param_key}")
            params[param_key] = f.value

    return "WHERE " + " AND ".join(clauses), params


def fetch_dataframe(
    conn: Connection,
    table: str,
    columns: list[str],
    filters: list[FilterCondition],
) -> pd.DataFrame:
    """指定カラムをDataFrameとして取得する。"""
    col_list = ", ".join(validate_identifier(c) for c in columns)
    tbl = validate_identifier(table)
    where, params = build_where_clause(filters)

    sql = f"SELECT {col_list} FROM {tbl} {where}"
    result = conn.execute(text(sql), params)
    return pd.DataFrame(result.fetchall(), columns=result.keys())
