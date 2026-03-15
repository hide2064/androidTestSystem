from sqlalchemy.engine import Connection

from app.analyzers.base import fetch_dataframe
from app.models.requests import CorrelationRequest


def run(conn: Connection, req: CorrelationRequest) -> dict:
    df = fetch_dataframe(conn, req.table, req.columns, req.filters)

    numeric_df = df[req.columns].apply(lambda s: s.astype(float)).dropna()

    corr_matrix = numeric_df.corr(method=req.method)

    matrix = [
        [round(float(v), 4) for v in row]
        for row in corr_matrix.values.tolist()
    ]

    return {
        "columns": req.columns,
        "matrix": matrix,
    }
