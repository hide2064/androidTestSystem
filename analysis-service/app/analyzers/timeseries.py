import pandas as pd
from sqlalchemy.engine import Connection

from app.analyzers.base import fetch_dataframe
from app.models.requests import TimeseriesRequest


def run(conn: Connection, req: TimeseriesRequest) -> dict:
    df = fetch_dataframe(
        conn,
        req.table,
        [req.time_column, req.value_column],
        req.filters,
    )

    df[req.time_column] = pd.to_datetime(df[req.time_column])
    df = df.dropna(subset=[req.time_column])
    df = df.set_index(req.time_column).sort_index()

    series = df[req.value_column].astype(float)

    agg_map = {"sum": "sum", "mean": "mean", "count": "count"}
    resampled = series.resample(req.freq).agg(agg_map[req.agg_func])
    resampled = resampled.dropna()

    labels = resampled.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    values = [round(float(v), 4) for v in resampled.values]

    return {
        "labels": labels,
        "series": [
            {
                "name": f"{req.value_column}_{req.agg_func}",
                "values": values,
            }
        ],
    }
