import numpy as np
from sqlalchemy.engine import Connection

from app.analyzers.base import fetch_dataframe
from app.models.requests import DistributionRequest


def run(conn: Connection, req: DistributionRequest) -> dict:
    df = fetch_dataframe(conn, req.table, [req.column], req.filters)

    series = df[req.column].dropna().astype(float)

    counts, bin_edges = np.histogram(series, bins=req.bins)

    # ビンのラベルは中央値
    bin_centers = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()

    return {
        "bin_edges": [round(float(e), 4) for e in bin_edges.tolist()],
        "bin_centers": [round(float(c), 4) for c in bin_centers],
        "counts": counts.tolist(),
        "total": int(series.count()),
        "null_count": int(df[req.column].isna().sum()),
    }
