"""
既存 results/*.json を MySQL testSystemDB に一括インポートするスクリプト。

使い方:
  python scripts/migrate_json_to_mysql.py [--results-dir results] [--dry-run]

環境変数 (または .env) から接続情報を読む:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  未設定時は docker compose のデフォルト値を使用
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートの .env を読み込む
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("ERROR: sqlalchemy が見つかりません。pip install sqlalchemy pymysql cryptography を実行してください。")
    sys.exit(1)


def make_engine():
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "13306"))  # Docker ホスト側マッピング
    name = os.environ.get("DB_NAME", "testSystemDB")
    user = os.environ.get("DB_USER", "testuser")
    password = os.environ.get("DB_PASSWORD", "TestUser2024!")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def migrate(result: dict, conn, dry_run: bool) -> str:
    """1件のJSONを android_test_results + android_test_steps に挿入。戻り値は 'inserted'|'skipped'|'dry-run'"""
    run_id = result.get("run_id")
    if not run_id:
        return "skipped (no run_id)"

    ts_raw = result.get("timestamp", "")
    try:
        started_at = datetime.fromisoformat(ts_raw)
    except ValueError:
        started_at = None

    params = {
        "run_id":      run_id,
        "scenario":    result.get("scenario", ""),
        "device_id":   result.get("device_id", ""),
        "test_site":   result.get("test_site", ""),
        "result":      result.get("result", "FAIL"),
        "total":       result.get("total", 0),
        "pass_count":  result.get("pass_count", 0),
        "fail_count":  result.get("fail_count", 0),
        "started_at":  started_at,
        "finished_at": None,
    }

    if dry_run:
        return "dry-run"

    conn.execute(text("""
        INSERT INTO android_test_results
          (run_id, scenario, device_id, test_site, result, total, pass_count, fail_count, started_at, finished_at)
        VALUES
          (:run_id, :scenario, :device_id, :test_site, :result, :total, :pass_count, :fail_count, :started_at, :finished_at)
        ON DUPLICATE KEY UPDATE
          result=VALUES(result), total=VALUES(total),
          pass_count=VALUES(pass_count), fail_count=VALUES(fail_count)
    """), params)

    conn.execute(text("DELETE FROM android_test_steps WHERE run_id = :run_id"), {"run_id": run_id})

    for step in result.get("steps", []):
        conn.execute(text("""
            INSERT INTO android_test_steps
              (run_id, step_id, action, description, pass, error_msg)
            VALUES
              (:run_id, :step_id, :action, :description, :pass, :error_msg)
        """), {
            "run_id":      run_id,
            "step_id":     step.get("step_id", 0),
            "action":      step.get("action", ""),
            "description": step.get("description", ""),
            "pass":        1 if step.get("pass") else 0,
            "error_msg":   step.get("error", ""),
        })

    return "inserted"


def main():
    parser = argparse.ArgumentParser(description="Migrate JSON results to MySQL")
    parser.add_argument("--results-dir", default="results", help="JSONファイルのディレクトリ (default: results)")
    parser.add_argument("--dry-run", action="store_true", help="実際には書き込まずに確認のみ")
    args = parser.parse_args()

    results_dir = project_root / args.results_dir
    json_files = sorted(results_dir.glob("*.json"))

    if not json_files:
        print(f"JSONファイルが見つかりません: {results_dir}")
        sys.exit(0)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}対象ファイル数: {len(json_files)}")

    engine = make_engine()
    ok = skip = err = 0

    with engine.begin() as conn:
        for path in json_files:
            try:
                data = load_json(path)
                status = migrate(data, conn, args.dry_run)
                print(f"  {status:12s}  {path.name}")
                if "inserted" in status or "dry-run" in status:
                    ok += 1
                else:
                    skip += 1
            except Exception as e:
                print(f"  ERROR        {path.name}: {e}")
                err += 1

    print(f"\n完了: {ok} 件処理, {skip} 件スキップ, {err} 件エラー")
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
