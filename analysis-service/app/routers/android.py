"""
Android試験結果専用 API
テーブル: android_test_results, android_test_steps
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text

from app.database import get_android_connection

router = APIRouter(prefix="/api/v1/android", tags=["android"])


def _where(
    scenarios:  list[str],
    device_ids: list[str],
    results:    list[str],
    test_sites: list[str],
    date_from:  Optional[str],
    date_to:    Optional[str],
) -> tuple[str, dict]:
    clauses = []
    params: dict = {}

    def add_in(col: str, vals: list[str], key: str):
        if vals:
            placeholders = ", ".join(f":{key}_{i}" for i in range(len(vals)))
            clauses.append(f"`{col}` IN ({placeholders})")
            for i, v in enumerate(vals):
                params[f"{key}_{i}"] = v

    add_in("scenario",  scenarios,  "sc")
    add_in("device_id", device_ids, "di")
    add_in("result",    results,    "rs")
    add_in("test_site", test_sites, "ts")

    if date_from:
        clauses.append("started_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("started_at <= :date_to")
        params["date_to"] = date_to

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


# ---------------------------------------------------------------------------
# 1. フィルタ選択肢
# ---------------------------------------------------------------------------

@router.get("/filters")
def get_filters():
    """シナリオ・端末ID・結果・拠点のユニーク値一覧を返す"""
    cols = {
        "scenarios":  "SELECT DISTINCT scenario  FROM android_test_results ORDER BY scenario",
        "device_ids": "SELECT DISTINCT device_id FROM android_test_results ORDER BY device_id",
        "results":    "SELECT DISTINCT result    FROM android_test_results ORDER BY result",
        "test_sites": "SELECT DISTINCT test_site FROM android_test_results ORDER BY test_site",
    }
    out = {}
    try:
        with get_android_connection() as conn:
            for key, sql in cols.items():
                rows = conn.execute(text(sql)).fetchall()
                out[key] = [str(r[0]) for r in rows if r[0] is not None]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return out


# ---------------------------------------------------------------------------
# 2. 合否サマリ（KPIカード用）
# ---------------------------------------------------------------------------

@router.get("/summary")
def get_summary(
    scenarios:  Annotated[list[str], Query()] = [],
    device_ids: Annotated[list[str], Query()] = [],
    results:    Annotated[list[str], Query()] = [],
    test_sites: Annotated[list[str], Query()] = [],
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
):
    where, params = _where(scenarios, device_ids, results, test_sites, date_from, date_to)
    sql = f"""
        SELECT
            COUNT(*)                                              AS total,
            SUM(result = 'PASS')                                  AS pass_count,
            SUM(result = 'FAIL')                                  AS fail_count,
            ROUND(SUM(result = 'PASS') / COUNT(*) * 100, 2)       AS yield_pct
        FROM android_test_results {where}
    """
    try:
        with get_android_connection() as conn:
            row = conn.execute(text(sql), params).fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "total":      int(row[0] or 0),
        "pass_count": int(row[1] or 0),
        "fail_count": int(row[2] or 0),
        "yield_pct":  float(row[3] or 0),
    }


# ---------------------------------------------------------------------------
# 3. 合否率（グループ別）
# ---------------------------------------------------------------------------

@router.get("/yield")
def get_yield(
    group_by:   str = "scenario",
    scenarios:  Annotated[list[str], Query()] = [],
    device_ids: Annotated[list[str], Query()] = [],
    results:    Annotated[list[str], Query()] = [],
    test_sites: Annotated[list[str], Query()] = [],
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
):
    allowed = {"scenario", "device_id", "test_site", "device_model"}
    if group_by not in allowed:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {allowed}")

    where, params = _where(scenarios, device_ids, results, test_sites, date_from, date_to)
    sql = f"""
        SELECT
            `{group_by}`,
            SUM(result = 'PASS') AS pass_count,
            SUM(result = 'FAIL') AS fail_count,
            COUNT(*)             AS total
        FROM android_test_results {where}
        GROUP BY `{group_by}`
        ORDER BY total DESC
        LIMIT 50
    """
    try:
        with get_android_connection() as conn:
            rows = conn.execute(text(sql), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "group_by": group_by,
        "items": [
            {
                "label":      str(r[0]),
                "pass_count": int(r[1] or 0),
                "fail_count": int(r[2] or 0),
                "total":      int(r[3]),
                "yield_pct":  round(int(r[1] or 0) / int(r[3]) * 100, 2) if r[3] else 0,
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# 4. 時系列 PASS率推移
# ---------------------------------------------------------------------------

@router.get("/trend")
def get_trend(
    freq:       str = "1D",
    scenarios:  Annotated[list[str], Query()] = [],
    device_ids: Annotated[list[str], Query()] = [],
    test_sites: Annotated[list[str], Query()] = [],
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
):
    import pandas as pd

    where, params = _where(scenarios, device_ids, [], test_sites, date_from, date_to)
    sql = f"""
        SELECT started_at, result
        FROM android_test_results {where}
        ORDER BY started_at
    """
    try:
        with get_android_connection() as conn:
            rows = conn.execute(text(sql), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        return {"metric": "yield", "labels": [], "values": []}

    df = pd.DataFrame(rows, columns=["started_at", "result"])
    df["started_at"] = pd.to_datetime(df["started_at"])
    df = df.set_index("started_at").sort_index()
    df["is_pass"] = (df["result"] == "PASS").astype(int)
    resampled = (df["is_pass"].resample(freq).mean() * 100).round(2).dropna()

    return {
        "metric": "yield",
        "unit":   "%",
        "labels": resampled.index.strftime("%Y-%m-%d %H:%M").tolist(),
        "values": resampled.values.tolist(),
    }


# ---------------------------------------------------------------------------
# 5. 試験結果一覧（ページング）
# ---------------------------------------------------------------------------

@router.get("/results")
def list_results(
    scenarios:  Annotated[list[str], Query()] = [],
    device_ids: Annotated[list[str], Query()] = [],
    results:    Annotated[list[str], Query()] = [],
    test_sites: Annotated[list[str], Query()] = [],
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
    limit:      int = 50,
    offset:     int = 0,
):
    where, params = _where(scenarios, device_ids, results, test_sites, date_from, date_to)
    params["limit"]  = min(limit, 200)
    params["offset"] = offset

    sql = f"""
        SELECT run_id, scenario, device_id, device_model,
               test_site, result, total, pass_count, fail_count,
               started_at, finished_at
        FROM android_test_results {where}
        ORDER BY started_at DESC
        LIMIT :limit OFFSET :offset
    """
    sql_count = f"SELECT COUNT(*) FROM android_test_results {where}"

    try:
        with get_android_connection() as conn:
            rows = conn.execute(text(sql), params).fetchall()
            total = conn.execute(text(sql_count), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items = [
        {
            "run_id":       r[0],
            "scenario":     r[1],
            "device_id":    r[2],
            "device_model": r[3],
            "test_site":    r[4],
            "result":       r[5],
            "total":        r[6],
            "pass_count":   r[7],
            "fail_count":   r[8],
            "started_at":   str(r[9]) if r[9] else None,
            "finished_at":  str(r[10]) if r[10] else None,
        }
        for r in rows
    ]
    return {"total": total, "items": items}


# ---------------------------------------------------------------------------
# 6. 試験結果詳細（ステップ含む）
# ---------------------------------------------------------------------------

@router.get("/results/{run_id}")
def get_result(run_id: str):
    sql_summary = """
        SELECT run_id, scenario, device_id, device_model,
               test_site, result, total, pass_count, fail_count,
               started_at, finished_at, note
        FROM android_test_results
        WHERE run_id = :run_id
    """
    sql_steps = """
        SELECT step_id, action, description, response,
               measured_value, unit, upper_limit, lower_limit,
               pass, error_msg, executed_at
        FROM android_test_steps
        WHERE run_id = :run_id
        ORDER BY step_id
    """
    try:
        with get_android_connection() as conn:
            row = conn.execute(text(sql_summary), {"run_id": run_id}).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
            step_rows = conn.execute(text(sql_steps), {"run_id": run_id}).fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    steps = [
        {
            "step_id":       r[0],
            "action":        r[1],
            "description":   r[2],
            "response":      r[3],
            "measured_value": float(r[4]) if r[4] is not None else None,
            "unit":          r[5],
            "upper_limit":   float(r[6]) if r[6] is not None else None,
            "lower_limit":   float(r[7]) if r[7] is not None else None,
            "pass":          bool(r[8]),
            "error_msg":     r[9],
            "executed_at":   str(r[10]) if r[10] else None,
        }
        for r in step_rows
    ]

    return {
        "run_id":       row[0],
        "scenario":     row[1],
        "device_id":    row[2],
        "device_model": row[3],
        "test_site":    row[4],
        "result":       row[5],
        "total":        row[6],
        "pass_count":   row[7],
        "fail_count":   row[8],
        "started_at":   str(row[9]) if row[9] else None,
        "finished_at":  str(row[10]) if row[10] else None,
        "note":         row[11],
        "steps":        steps,
    }
