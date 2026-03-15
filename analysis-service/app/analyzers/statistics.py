from sqlalchemy.engine import Connection

from app.analyzers.base import fetch_dataframe
from app.models.requests import StatisticsRequest


def run(conn: Connection, req: StatisticsRequest) -> dict:
    df = fetch_dataframe(conn, req.table, req.columns, req.filters)

    result = {}
    for col in req.columns:
        series = df[col]
        numeric = series.dropna()

        if not numeric.empty:
            try:
                numeric = numeric.astype(float)
                result[col] = {
                    "count": int(numeric.count()),
                    "mean": round(float(numeric.mean()), 4),
                    "std": round(float(numeric.std()), 4),
                    "min": round(float(numeric.min()), 4),
                    "q25": round(float(numeric.quantile(0.25)), 4),
                    "median": round(float(numeric.median()), 4),
                    "q75": round(float(numeric.quantile(0.75)), 4),
                    "max": round(float(numeric.max()), 4),
                    "null_count": int(series.isna().sum()),
                }
            except (TypeError, ValueError):
                # 数値でないカラムは頻度集計
                freq = series.value_counts().head(10).to_dict()
                result[col] = {
                    "count": int(series.count()),
                    "null_count": int(series.isna().sum()),
                    "unique": int(series.nunique()),
                    "top_values": {str(k): int(v) for k, v in freq.items()},
                }
        else:
            result[col] = {"count": 0, "null_count": int(series.isna().sum())}

    return result
