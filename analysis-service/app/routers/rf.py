"""
RF試験データ専用 API
テーブル: rf_test_data
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text

from app.database import get_connection

router = APIRouter(prefix="/api/v1/rf", tags=["rf"])

TABLE = "rf_test_data"

# ---------------------------------------------------------------------------
# フィルタ条件をWHERE句に変換するヘルパー
# ---------------------------------------------------------------------------

def _where(
    dut_models: list[str],
    technologies: list[str],
    bands: list[str],
    test_items: list[str],
    temperatures: list[str],
    voltages: list[str],
    judgments: list[str],
    operators: list[str],
) -> tuple[str, dict]:
    clauses = []
    params: dict = {}

    def add_in(col: str, vals: list[str], key: str):
        if vals:
            placeholders = ", ".join(f":{key}_{i}" for i in range(len(vals)))
            clauses.append(f"`{col}` IN ({placeholders})")
            for i, v in enumerate(vals):
                params[f"{key}_{i}"] = v

    add_in("DUT_Model",      dut_models,   "dm")
    add_in("Technology",     technologies, "tc")
    add_in("Band",           bands,        "bd")
    add_in("Test_Item",      test_items,   "ti")
    add_in("Temperature_C",  temperatures, "tp")
    add_in("Supply_Voltage_V", voltages,   "vt")
    add_in("Judgment",       judgments,    "jd")
    add_in("Operator_ID",    operators,    "op")

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


# ---------------------------------------------------------------------------
# 1. フィルタ選択肢の取得
# ---------------------------------------------------------------------------

@router.get("/filters")
def get_filters():
    """各フィルタ列のユニーク値一覧を返す"""
    cols = [
        "DUT_Model", "Technology", "Band", "Test_Item",
        "Temperature_C", "Supply_Voltage_V", "Judgment", "Operator_ID",
        "Channel_Position",
    ]
    result = {}
    try:
        with get_connection() as conn:
            for col in cols:
                rows = conn.execute(
                    text(f"SELECT DISTINCT `{col}` FROM `{TABLE}` WHERE `{col}` IS NOT NULL ORDER BY `{col}`")
                ).fetchall()
                result[col] = [str(r[0]) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result


# ---------------------------------------------------------------------------
# 2. 合否サマリ（KPIカード用）
# ---------------------------------------------------------------------------

@router.get("/summary")
def get_summary(
    dut_models:    Annotated[list[str], Query()] = [],
    technologies:  Annotated[list[str], Query()] = [],
    bands:         Annotated[list[str], Query()] = [],
    test_items:    Annotated[list[str], Query()] = [],
    temperatures:  Annotated[list[str], Query()] = [],
    voltages:      Annotated[list[str], Query()] = [],
    judgments:     Annotated[list[str], Query()] = [],
    operators:     Annotated[list[str], Query()] = [],
):
    where, params = _where(dut_models, technologies, bands, test_items,
                           temperatures, voltages, judgments, operators)
    sql = f"""
        SELECT
            COUNT(*)                                          AS total,
            SUM(Judgment = 'PASS')                           AS pass_count,
            SUM(Judgment = 'FAIL')                           AS fail_count,
            ROUND(SUM(Judgment='PASS') / COUNT(*) * 100, 2) AS yield_pct
        FROM `{TABLE}` {where}
    """
    try:
        with get_connection() as conn:
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
    group_by:      str = "Test_Item",
    dut_models:    Annotated[list[str], Query()] = [],
    technologies:  Annotated[list[str], Query()] = [],
    bands:         Annotated[list[str], Query()] = [],
    test_items:    Annotated[list[str], Query()] = [],
    temperatures:  Annotated[list[str], Query()] = [],
    voltages:      Annotated[list[str], Query()] = [],
    judgments:     Annotated[list[str], Query()] = [],
    operators:     Annotated[list[str], Query()] = [],
):
    allowed = {"Test_Item","DUT_Model","Technology","Band","Temperature_C",
               "Supply_Voltage_V","Operator_ID","Channel_Position","Modulation"}
    if group_by not in allowed:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {allowed}")

    where, params = _where(dut_models, technologies, bands, test_items,
                           temperatures, voltages, judgments, operators)
    sql = f"""
        SELECT
            `{group_by}`,
            SUM(Judgment = 'PASS') AS pass_count,
            SUM(Judgment = 'FAIL') AS fail_count,
            COUNT(*)               AS total
        FROM `{TABLE}` {where}
        GROUP BY `{group_by}`
        ORDER BY total DESC
        LIMIT 50
    """
    try:
        with get_connection() as conn:
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
# 4. 測定値分布（ボックスプロット用）
# ---------------------------------------------------------------------------

@router.get("/distribution")
def get_distribution(
    test_item:     str,
    group_by:      str = "DUT_Model",
    dut_models:    Annotated[list[str], Query()] = [],
    technologies:  Annotated[list[str], Query()] = [],
    bands:         Annotated[list[str], Query()] = [],
    temperatures:  Annotated[list[str], Query()] = [],
    voltages:      Annotated[list[str], Query()] = [],
    operators:     Annotated[list[str], Query()] = [],
):
    allowed = {"DUT_Model","Technology","Band","Temperature_C","Supply_Voltage_V","Operator_ID"}
    if group_by not in allowed:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {allowed}")

    # test_itemを必ずフィルタに含める
    where, params = _where(dut_models, technologies, bands, [test_item],
                           temperatures, voltages, [], operators)
    sql = f"""
        SELECT
            `{group_by}`,
            MIN(Measured_Value)                        AS min_val,
            MAX(Measured_Value)                        AS max_val,
            AVG(Measured_Value)                        AS avg_val,
            STDDEV(Measured_Value)                     AS std_val,
            COUNT(*)                                   AS cnt,
            MIN(Upper_Limit)                           AS upper_limit,
            MIN(Lower_Limit)                           AS lower_limit,
            MIN(Unit)                                  AS unit
        FROM `{TABLE}` {where}
        GROUP BY `{group_by}`
        ORDER BY `{group_by}`
    """

    # 生データも取得（散布図・ヒストグラム用）
    sql_raw = f"""
        SELECT `{group_by}`, Measured_Value, Judgment
        FROM `{TABLE}` {where}
        ORDER BY `{group_by}`
    """
    try:
        with get_connection() as conn:
            stats_rows = conn.execute(text(sql), params).fetchall()
            raw_rows = conn.execute(text(sql_raw), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    stats = [
        {
            "group":       str(r[0]),
            "min":         float(r[1]) if r[1] is not None else None,
            "max":         float(r[2]) if r[2] is not None else None,
            "avg":         round(float(r[3]), 4) if r[3] is not None else None,
            "std":         round(float(r[4]), 4) if r[4] is not None else None,
            "count":       int(r[5]),
            "upper_limit": float(r[6]) if r[6] is not None else None,
            "lower_limit": float(r[7]) if r[7] is not None else None,
            "unit":        str(r[8]) if r[8] else "",
        }
        for r in stats_rows
    ]

    raw = [
        {"group": str(r[0]), "value": float(r[1]) if r[1] is not None else None, "judgment": str(r[2])}
        for r in raw_rows
        if r[1] is not None
    ]

    return {"test_item": test_item, "group_by": group_by, "stats": stats, "raw": raw}


# ---------------------------------------------------------------------------
# 5. 時系列推移
# ---------------------------------------------------------------------------

@router.get("/trend")
def get_trend(
    test_item:     str,
    freq:          str = "1D",
    metric:        str = "yield",   # yield | avg_value
    dut_models:    Annotated[list[str], Query()] = [],
    technologies:  Annotated[list[str], Query()] = [],
    bands:         Annotated[list[str], Query()] = [],
    temperatures:  Annotated[list[str], Query()] = [],
    voltages:      Annotated[list[str], Query()] = [],
    operators:     Annotated[list[str], Query()] = [],
):
    import pandas as pd

    where, params = _where(dut_models, technologies, bands, [test_item],
                           temperatures, voltages, [], operators)
    sql = f"""
        SELECT Timestamp, Measured_Value, Judgment
        FROM `{TABLE}` {where}
        ORDER BY Timestamp
    """
    try:
        with get_connection() as conn:
            rows = conn.execute(text(sql), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        return {"test_item": test_item, "metric": metric, "labels": [], "values": []}

    df = pd.DataFrame(rows, columns=["Timestamp", "Measured_Value", "Judgment"])
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.set_index("Timestamp").sort_index()

    if metric == "yield":
        df["is_pass"] = (df["Judgment"] == "PASS").astype(int)
        resampled = (df["is_pass"].resample(freq).mean() * 100).round(2)
        unit = "%"
    else:
        resampled = df["Measured_Value"].astype(float).resample(freq).mean().round(4)
        unit = ""

    resampled = resampled.dropna()
    return {
        "test_item": test_item,
        "metric":    metric,
        "unit":      unit,
        "labels":    resampled.index.strftime("%Y-%m-%d %H:%M").tolist(),
        "values":    resampled.values.tolist(),
    }


# ---------------------------------------------------------------------------
# 6. マージン分析（上下限との距離）
# ---------------------------------------------------------------------------

@router.get("/margin")
def get_margin(
    test_item:     str,
    x_axis:        str = "Temperature_C",
    dut_models:    Annotated[list[str], Query()] = [],
    technologies:  Annotated[list[str], Query()] = [],
    bands:         Annotated[list[str], Query()] = [],
    temperatures:  Annotated[list[str], Query()] = [],
    voltages:      Annotated[list[str], Query()] = [],
    operators:     Annotated[list[str], Query()] = [],
):
    allowed_x = {"Temperature_C", "Supply_Voltage_V", "UL_Frequency_MHz", "DL_Frequency_MHz"}
    if x_axis not in allowed_x:
        raise HTTPException(status_code=400, detail=f"x_axis must be one of {allowed_x}")

    where, params = _where(dut_models, technologies, bands, [test_item],
                           temperatures, voltages, [], operators)
    sql = f"""
        SELECT
            `{x_axis}`,
            Measured_Value,
            Upper_Limit,
            Lower_Limit,
            Judgment,
            DUT_Model
        FROM `{TABLE}` {where}
        ORDER BY `{x_axis}`
    """
    try:
        with get_connection() as conn:
            rows = conn.execute(text(sql), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    points = []
    for r in rows:
        x_val, measured, upper, lower, judgment, dut = r
        if x_val is None or measured is None:
            continue
        margin_upper = round(float(upper) - float(measured), 4) if upper is not None else None
        margin_lower = round(float(measured) - float(lower), 4) if lower is not None else None
        points.append({
            "x":            float(x_val),
            "measured":     float(measured),
            "upper_limit":  float(upper) if upper is not None else None,
            "lower_limit":  float(lower) if lower is not None else None,
            "margin_upper": margin_upper,
            "margin_lower": margin_lower,
            "judgment":     str(judgment),
            "dut_model":    str(dut),
        })

    return {"test_item": test_item, "x_axis": x_axis, "points": points}
