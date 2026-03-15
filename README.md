# Android 自動試験システム + opeAnyalyze 統合ダッシュボード

Android 端末・計測器の自動試験実行と、RF/Android 試験データの分析・可視化を統合したシステムです。

## 機能概要

| タブ | 機能 |
|---|---|
| 試験実行 | シナリオ選択・端末指定・開始/停止・リアルタイムログ |
| Android分析 | KPI カード・合否率グラフ・PASS率推移・試験結果一覧 |
| RF分析 | RF試験データのスライサー・分布・トレンド・マージン分析 |
| 汎用分析 | 任意テーブルへの統計・時系列・相関分析 |

## アーキテクチャ

```
ブラウザ (localhost:3000) — Vue 3 + ECharts + Element Plus
    │  /api/orchestrator/  (REST + WebSocket)
    │  /api/analysis/      (REST)
    ▼
Nginx (dashboard コンテナ)
    ├── orchestrator:8000  ← 試験司令塔 (FastAPI)
    │       ├── Android Agent:5000  ← ADB + Appium
    │       └── Equipment Agent:5001 ← 計測器制御
    └── analysis-service:8001  ← 分析API (FastAPI / opeAnyalyze backend)

MySQL:13306 (ホスト) / 3306 (コンテナ内)
    ├── testSystemDB    ← Android試験結果
    └── cellularAnylyze ← RF試験データ (opeAnyalyze)
```

## セットアップ（初回のみ）

### 1. 前提ソフトウェア

| ソフトウェア | 説明 |
|---|---|
| Docker Desktop | コンテナ実行環境 |
| Android Platform Tools | ADB コマンド (`adb version` が通ること) |

### 2. リポジトリ取得

```bash
git clone https://github.com/hide2064/androidTestSystem
cd androidTestSystem
```

### 3. 環境設定ファイルの作成

```bash
cp .env.example .env
# .env を編集（MySQLパスワード等）
```

`.env` の主要な設定:

```env
MYSQL_ROOT_PASSWORD=TestSystem2024!   # MySQL root パスワード
DB_PASSWORD=TestUser2024!             # testuser パスワード
TEST_SITE=local-dev                   # 試験拠点名
```

### 4. 起動

```bash
docker compose up -d
```

`http://localhost:3000` をブラウザで開けば完了です。

### 5. Android 端末の接続

```bash
adb devices  # 端末が認識されていることを確認
```

---

## RF データの取り込み

opeAnyalyze の CSV インポートスクリプトを使います:

```bash
# analysis-service コンテナ内で実行
docker compose exec analysis-service \
  python scripts/load_csv.py \
  --csv /path/to/rf_test_data.csv
```

または、ホストの opeAnyalyze リポジトリ側から直接 MySQL に投入:

```bash
# ホスト側 opeAnyalyze/.env の DB_PORT を 13306 に変更してから
cd /path/to/opeAnyalyze
backend/.venv/Scripts/python.exe scripts/load_csv.py --csv your_data.csv
```

---

## 既存 JSON 結果のマイグレーション

`results/*.json` を MySQL に一括インポート:

```bash
python scripts/migrate_json_to_mysql.py          # 本番実行
python scripts/migrate_json_to_mysql.py --dry-run  # 確認のみ
```

---

## バックアップ

```bash
bash scripts/backup_mysql.sh           # ./backups/ に保存
bash scripts/backup_mysql.sh /mnt/nas  # 保存先指定
```

30 日以上前のバックアップは自動削除されます。

cron 設定例 (毎日 2:00 AM):
```
0 2 * * * cd /path/to/androidTestSystem && bash scripts/backup_mysql.sh >> logs/backup.log 2>&1
```

---

## バージョンアップ

```bash
git pull
docker compose build
docker compose up -d
```

---

## 試験シナリオの作成

`orchestrator/scenarios/` フォルダに YAML ファイルを追加します。

```yaml
name: サンプル試験
version: "1.0"
description: 試験の説明

steps:
  - id: 1
    description: 端末情報を取得する
    action: adb
    command: shell getprop ro.product.model

  - id: 2
    description: 5秒待機
    action: wait
    seconds: 5

  - id: 3
    description: 電圧を測定する
    action: equipment_measure
    device: power_supply
    parameter: voltage_ch1
    expect:
      between: [3.5, 4.2]
    on_fail: stop

  - id: 4
    description: 画面のボタンをタップ
    action: tap
    locator_type: text
    locator_value: "設定"
```

### action 一覧

| action | 説明 | 必須パラメータ |
|---|---|---|
| `adb` | ADB shell コマンド実行 | `command` |
| `tap` | 画面要素をタップ | `locator_type`, `locator_value` |
| `input_text` | テキストを入力 | `locator_type`, `locator_value`, `text` |
| `assert_text` | テキストを確認 | `locator_type`, `locator_value`, `expect` |
| `assert_exists` | 要素の存在確認 | `locator_type`, `locator_value` |
| `equipment_measure` | 計測器で測定 | `device`, `parameter`, `expect` |
| `equipment_method` | 計測器のメソッド呼び出し | `device`, `method`, `args` |
| `equipment_command` | 計測器に生コマンド送信 | `device`, `command` |
| `screenshot` | スクリーンショット保存 | `save_path` (任意) |
| `wait` | 待機 | `seconds` |

---

## 計測器の追加

`equipment-agent/drivers/` フォルダにドライバファイルを追加します。

```python
# equipment-agent/drivers/visa/my_instrument.py
import sys; sys.path.insert(0, "/app")
from base_driver import BaseDriver, MeasureResult

class Driver(BaseDriver):
    def connect(self): ...
    def disconnect(self): ...
    def send_command(self, command): ...
    def measure(self, parameter): ...
```

`equipment-agent/config/equipment.yaml` に追記:

```yaml
instruments:
  my_instrument:
    driver: visa.my_instrument
    address: "GPIB0::10::INSTR"
    description: "私の計測器"
```

---

## ディレクトリ構成

```
androidTestSystem/
├── docker-compose.yml
├── .env.example
├── dashboard/               ← Vue 3 + Nginx ダッシュボード
│   ├── src/
│   │   ├── views/           ← TestControlView, AndroidDashboardView, RfDashboardView
│   │   ├── stores/          ← testStore, androidStore, rfStore, schemaStore
│   │   ├── components/      ← rf/, filters/, layout/
│   │   └── api/             ← orchestrator.ts, android.ts, rf.ts
│   ├── nginx.conf
│   └── Dockerfile
├── orchestrator/            ← 試験司令塔 (FastAPI :8000)
│   ├── main.py
│   ├── scenario_runner.py
│   ├── result_manager.py    ← JSON + MySQL 書き込み
│   └── scenarios/           ← YAML シナリオ置き場
├── analysis-service/        ← 分析API (FastAPI :8001 / opeAnyalyze backend)
│   └── app/
│       ├── routers/         ← android.py, rf.py, schema.py, analysis.py
│       ├── analyzers/       ← statistics, timeseries, distribution, correlation, groupby
│       └── config.py        ← 2DB 接続設定
├── android-agent/           ← ADB + Appium (FastAPI :5000)
├── equipment-agent/         ← 計測器制御 (FastAPI :5001)
│   ├── drivers/             ← visa/, serial/, rest/, mock/
│   └── config/equipment.yaml
├── mysql/
│   └── init/                ← 01_create_databases.sql, 02_create_android_tables.sql
├── scripts/
│   ├── migrate_json_to_mysql.py  ← 既存JSONをMySQLへ一括移行
│   └── backup_mysql.sh           ← MySQLバックアップ
├── docs/
│   └── integration_design.md    ← 統合設計書
└── tests/
```
