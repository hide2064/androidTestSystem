from sqlalchemy.engine import Connection

from app.analyzers.base import fetch_dataframe, validate_identifier, build_where_clause
from app.models.requests import GroupbyRequest
from sqlalchemy import text


def run(conn: Connection, req: GroupbyRequest) -> dict:
    all_columns = req.group_columns + [req.agg_column]

    group_cols = ", ".join(validate_identifier(c) for c in req.group_columns)
    agg_col = validate_identifier(req.agg_column)
    tbl = validate_identifier(req.table)
    where, params = build_where_clause(req.filters)

    agg_map = {
        "sum": f"SUM({agg_col})",
        "mean": f"AVG({agg_col})",
        "count": f"COUNT({agg_col})",
        "max": f"MAX({agg_col})",
        "min": f"MIN({agg_col})",
    }
    agg_expr = agg_map[req.agg_func]
    result_col = f"{req.agg_column}_{req.agg_func}"

    params["limit"] = req.limit
    sql = (
        f"SELECT {group_cols}, {agg_expr} AS `{result_col}` "
        f"FROM {tbl} {where} "
        f"GROUP BY {group_cols} "
        f"ORDER BY `{result_col}` DESC "
        f"LIMIT :limit"
    )

    result = conn.execute(text(sql), params)
    rows = result.fetchall()
    columns = list(result.keys())

    return {
        "columns": columns,
        "rows": [
            [str(v) if v is not None else None for v in row]
            for row in rows
        ],
    }
