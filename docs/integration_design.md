# opeAnyalyze 統合設計書

## 1. 統合の目的と方針

### 1.1 背景

| システム | 役割 | 現状の課題 |
|---|---|---|
| androidTestSystem | Android端末・計測器の自動試験実行 | 結果はJSON/SharePointのみ。分析・可視化機能がない |
| opeAnyalyze | RF試験データのMySQL分析ダッシュボード | 試験実行機能がない。データ投入が手動CSVのみ |

### 1.2 統合方針

**「androidTestSystem が試験を実行し、opeAnyalyze が結果を分析する」**

```
試験実行 (androidTestSystem) ──→ MySQL ──→ 分析・可視化 (opeAnyalyze)
```

具体的には以下の3点を統合する：

1. **共通データストア**: MySQL を唯一の結果保管先とする
2. **分析サービス追加**: opeAnyalyze バックエンドを Docker サービスとして組み込む
3. **ダッシュボード統合**: opeAnyalyze の Vue 3 フロントエンドで試験制御＋分析を一画面に統一

---

## 2. 統合後アーキテクチャ

### 2.1 全体構成図

```
┌─────────────────────────────────────────────────────────────────────┐
│                    test-system-network (Docker)                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │   dashboard (Vue 3 + Nginx)  :3000                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│  │  │ 試験制御タブ  │  │ リアルタイム  │  │ 分析ダッシュボード│   │   │
│  │  │ シナリオ選択  │  │ ログ・進捗   │  │ KPI・チャート群  │   │   │
│  │  │ 端末・機材   │  │ (WebSocket)  │  │ (ECharts)        │   │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │   │
│  └─────────┼─────────────────┼───────────────────┼─────────────┘   │
│            │                 │                   │                   │
│      REST  │           WebSocket           REST  │                   │
│            ▼                 ▼                   ▼                   │
│  ┌─────────────────┐              ┌──────────────────────────────┐  │
│  │  orchestrator   │              │      analysis-service        │  │
│  │  (FastAPI):8000 │              │  (opeAnyalyze Backend)       │  │
│  │                 │              │      (FastAPI):8001           │  │
│  │  - シナリオ実行  │              │                              │  │
│  │  - 状態管理     │◄────────────►│  - /api/v1/rf/*              │  │
│  │  - 結果保存     │  MySQL       │  - /api/v1/analysis/*        │  │
│  └────────┬────────┘  共有        │  - /api/v1/tables/*          │  │
│           │                       └──────────────┬───────────────┘  │
│           │ SQL write                             │ SQL read          │
│           ▼                                       ▼                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     MySQL 8.4  :3306                            │ │
│  │   DB: testSystemDB                                              │ │
│  │  ┌────────────────────┐   ┌──────────────┐   ┌──────────────┐  │ │
│  │  │ android_test_results│   │android_test_ │   │ rf_test_data │  │ │
│  │  │ (試験サマリ)         │   │    steps     │   │(既存RFデータ)│  │ │
│  │  │                    │   │(ステップ詳細) │   │              │  │ │
│  │  └────────────────────┘   └──────────────┘   └──────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│           │                                                           │
│  ┌────────┴────────┐    ┌─────────────────┐                          │
│  │  android-agent  │    │ equipment-agent │                          │
│  │  (FastAPI):5000 │    │  (FastAPI):5001 │                          │
│  └─────────────────┘    └─────────────────┘                          │
│           │                                                           │
└───────────┼───────────────────────────────────────────────────────────┘
            │ ADB TCP (host.docker.internal:5037)
            ▼
     ┌─────────────┐
     │  Host PC    │
     │  ADB Server │
     └──────┬──────┘
            │ USB
            ▼
     ┌─────────────┐
     │ Android DUT │
     └─────────────┘
```

### 2.2 サービス一覧（統合後）

| サービス名 | ポート | 役割 | 変更 |
|---|---|---|---|
| `dashboard` | 3000 | Vue 3 統合フロントエンド | **置き換え** (HTML→Vue 3) |
| `orchestrator` | 8000 | 試験実行・WebSocket | **変更** (MySQL書き込み追加) |
| `analysis-service` | 8001 | RF/Android データ分析API | **新規追加** (opeAnyalyze backend) |
| `mysql` | 3306 | 共通データストア | **新規追加** |
| `android-agent` | 5000/4723 | ADB + Appium | 変更なし |
| `equipment-agent` | 5001 | 計測器制御 | 変更なし |

---

## 3. データベース設計

### 3.1 新規テーブル: `android_test_results`

試験実行1回のサマリを格納する。

```sql
CREATE TABLE android_test_results (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id        VARCHAR(64)  NOT NULL UNIQUE,  -- UUID (例: 20240315T103045_wifi_test_SM-A536B)
    scenario      VARCHAR(128) NOT NULL,
    device_id     VARCHAR(64)  NOT NULL,
    device_model  VARCHAR(128),
    test_site     VARCHAR(64)  DEFAULT 'unknown',
    operator_id   VARCHAR(64),
    started_at    DATETIME     NOT NULL,
    finished_at   DATETIME,
    total         INT          DEFAULT 0,
    pass_count    INT          DEFAULT 0,
    fail_count    INT          DEFAULT 0,
    result        ENUM('PASS','FAIL','RUNNING','ABORTED') DEFAULT 'RUNNING',
    note          TEXT,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3.2 新規テーブル: `android_test_steps`

各ステップの詳細結果を格納する。

```sql
CREATE TABLE android_test_steps (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id       VARCHAR(64)  NOT NULL,
    step_id      INT          NOT NULL,
    action       VARCHAR(64)  NOT NULL,
    description  TEXT,
    response     TEXT,
    measured_value DOUBLE,
    unit         VARCHAR(32),
    upper_limit  DOUBLE,
    lower_limit  DOUBLE,
    pass         BOOLEAN      NOT NULL DEFAULT FALSE,
    error_msg    TEXT,
    executed_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id),
    FOREIGN KEY (run_id) REFERENCES android_test_results(run_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3.3 既存テーブル: `rf_test_data`

opeAnyalyze の既存テーブルをそのまま利用する。変更なし。

### 3.4 データベース名

| DB名 | 用途 |
|---|---|
| `testSystemDB` | androidTestSystem の結果（新規） |
| `cellularAnylyze` | opeAnyalyze の RF データ（既存） |

※ 同じ MySQL インスタンス上に両DBを共存させる。

---

## 4. Docker Compose 変更設計

### 4.1 統合後 docker-compose.yml

```yaml
version: "3.9"

services:

  # ① 統合ダッシュボード (Vue 3 + Nginx)
  dashboard:
    build: ./dashboard
    ports:
      - "3000:80"
    depends_on:
      - orchestrator
      - analysis-service
    restart: unless-stopped

  # ② Test Orchestrator（試験実行）
  orchestrator:
    build: ./orchestrator
    ports:
      - "8000:8000"
    volumes:
      - ./orchestrator/scenarios:/app/scenarios
      - ./results:/app/results
    environment:
      - ANDROID_AGENT_URL=http://android-agent:5000
      - EQUIPMENT_AGENT_URL=http://equipment-agent:5001
      - SHAREPOINT_SITE_URL=${SHAREPOINT_SITE_URL}
      - SHAREPOINT_TENANT_ID=${SHAREPOINT_TENANT_ID}
      - SHAREPOINT_CLIENT_ID=${SHAREPOINT_CLIENT_ID}
      - SHAREPOINT_CLIENT_SECRET=${SHAREPOINT_CLIENT_SECRET}
      - TEST_SITE=${TEST_SITE:-default}
      # MySQL 接続 (新規追加)
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=testuser
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=testSystemDB
    depends_on:
      mysql:
        condition: service_healthy
      android-agent:
        condition: service_started
      equipment-agent:
        condition: service_started
    restart: unless-stopped

  # ③ Analysis Service（opeAnyalyze バックエンド）- 新規追加
  analysis-service:
    build: ./analysis-service
    ports:
      - "8001:8001"
    environment:
      # RF データ (cellularAnylyze)
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=testuser
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=cellularAnylyze
      # Android 試験結果 (testSystemDB)
      - ANDROID_DB_HOST=mysql
      - ANDROID_DB_PORT=3306
      - ANDROID_DB_USER=testuser
      - ANDROID_DB_PASSWORD=${DB_PASSWORD}
      - ANDROID_DB_NAME=testSystemDB
    depends_on:
      mysql:
        condition: service_healthy
    restart: unless-stopped

  # ④ Android Agent（ADB + Appium）- 変更なし
  android-agent:
    build: ./android-agent
    ports:
      - "5000:5000"
      - "4723:4723"
    environment:
      - ADB_SERVER_HOST=host.docker.internal
      - ADB_SERVER_PORT=5037
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  # ⑤ Equipment Agent（計測器制御）- 変更なし
  equipment-agent:
    build: ./equipment-agent
    ports:
      - "5001:5001"
    volumes:
      - ./equipment-agent/config:/app/config
    restart: unless-stopped

  # ⑥ MySQL 8.4 - 新規追加
  mysql:
    image: mysql:8.4
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_USER=testuser
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d  # 初期化SQL
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  mysql_data:

networks:
  default:
    name: test-system-network
```

---

## 5. 変更・追加コンポーネント詳細

### 5.1 orchestrator/result_manager.py の変更

**変更内容**: `save_and_send()` に MySQL 書き込みを追加する。

```
現在のフロー:
  summarize() → save_and_send() → [JSON保存] + [SharePoint送信]

変更後のフロー:
  summarize() → save_and_send() → [JSON保存] + [MySQL書き込み] + [SharePoint送信]
```

**新メソッド**: `_save_to_mysql(summary: dict) -> None`

```python
# 書き込みイメージ (SQLAlchemy core)
async def _save_to_mysql(self, summary: dict) -> None:
    # 1. android_test_results に1行 INSERT (サマリ)
    # 2. android_test_steps に N行 INSERT (ステップ詳細)
    #    - equipment_measure の場合: measured_value, unit, upper_limit, lower_limit を保存
```

**MySQL 障害時の挙動**: SharePoint と同様、MySQL 書き込みに失敗しても試験全体はエラーにしない。ローカルJSON保存は必ず実行する。

### 5.2 analysis-service ディレクトリ構成

opeAnyalyze の `backend/` をベースに、Android 試験結果分析 API を追加する。

```
analysis-service/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py           # FastAPI エントリーポイント (port 8001)
│   ├── config.py         # 2つのDB接続設定 (RF用 + Android用)
│   ├── database.py       # get_rf_connection() / get_android_connection()
│   ├── routers/
│   │   ├── schema.py     # (opeAnyalyze 既存) テーブル情報
│   │   ├── analysis.py   # (opeAnyalyze 既存) 汎用分析
│   │   ├── rf.py         # (opeAnyalyze 既存) RF試験データ専用API
│   │   └── android.py    # (新規) Android試験結果専用API
│   └── analyzers/        # (opeAnyalyze 既存そのまま)
│       ├── base.py
│       ├── statistics.py
│       ├── timeseries.py
│       ├── distribution.py
│       ├── correlation.py
│       └── groupby.py
```

### 5.3 analysis-service の新規 API: `/api/v1/android/*`

Android 試験結果分析専用エンドポイント。

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `GET /android/summary` | GET | 総合 PASS/FAIL KPI |
| `GET /android/yield?group_by=scenario` | GET | シナリオ・端末別 合否率 |
| `GET /android/trend?freq=1D` | GET | 時系列 合否率推移 |
| `GET /android/results` | GET | 試験結果一覧（ページング） |
| `GET /android/results/{run_id}` | GET | 試験1件の詳細（ステップ含む） |
| `GET /android/filters` | GET | フィルタ用ユニーク値一覧 |

**クエリパラメータ（フィルタ）**:
```
?scenarios[]=wifi_test&scenarios[]=bt_test
&device_ids[]=SM-A536B
&results[]=FAIL
&date_from=2024-01-01&date_to=2024-12-31
```

### 5.4 dashboard (Vue 3) の変更

opeAnyalyze の `frontend/` をベースに、試験制御タブを追加する。

```
dashboard/
├── Dockerfile            # Nginx でビルド成果物を配信
├── src/
│   ├── api/
│   │   ├── rf.ts         # (opeAnyalyze 既存) RF API クライアント
│   │   ├── schema.ts     # (opeAnyalyze 既存)
│   │   ├── analysis.ts   # (opeAnyalyze 既存)
│   │   ├── android.ts    # (新規) Android 試験結果 API クライアント
│   │   └── orchestrator.ts # (新規) Orchestrator API クライアント
│   ├── stores/
│   │   ├── rfStore.ts    # (opeAnyalyze 既存)
│   │   ├── androidStore.ts # (新規) Android 試験結果ストア
│   │   └── testStore.ts  # (新規) 試験制御状態ストア（WebSocket管理）
│   ├── views/
│   │   ├── RfDashboardView.vue     # (opeAnyalyze 既存) RF分析
│   │   ├── AndroidDashboardView.vue # (新規) Android試験結果分析
│   │   └── TestControlView.vue     # (新規) 試験実行制御
│   └── components/
│       ├── filters/      # (opeAnyalyze 既存)
│       ├── charts/       # (opeAnyalyze 既存)
│       ├── rf/           # (opeAnyalyze 既存)
│       ├── android/      # (新規)
│       │   ├── AndroidKpiCards.vue
│       │   ├── AndroidYieldChart.vue
│       │   ├── AndroidTrendChart.vue
│       │   └── ResultTable.vue
│       └── control/      # (新規)
│           ├── ScenarioSelector.vue
│           ├── DeviceSelector.vue
│           ├── TestControlPanel.vue   # 開始/停止ボタン
│           └── RealtimeLogViewer.vue  # WebSocket ログ
```

**画面タブ構成**:

```
┌──────────────────────────────────────────────────────┐
│  [試験実行] [Android分析] [RF分析] [汎用分析]          │
└──────────────────────────────────────────────────────┘

試験実行タブ:
  ┌────────────────┬────────────────────────────────────┐
  │ シナリオ選択   │ リアルタイムログ (WebSocket)        │
  │ 端末選択       │ [INFO] ステップ1: adb shell ...     │
  │ [開始] [停止]  │ [PASS] ステップ2: assert_text ...   │
  │                │ [FAIL] ステップ3: equipment_measure │
  │ステップ進捗:   │                                    │
  │ ████████░░ 8/10│                                    │
  └────────────────┴────────────────────────────────────┘

Android分析タブ:
  ┌──────────┬──────────┬──────────┬──────────────────┐
  │ 総試験数  │ PASS     │ FAIL     │ PASS率           │
  │  1,234   │   987    │   247    │   79.9%          │
  └──────────┴──────────┴──────────┴──────────────────┘
  ┌────────────────────────┬─────────────────────────────┐
  │ シナリオ別合否率 (棒)   │ 時系列 PASS率推移 (折線)    │
  └────────────────────────┴─────────────────────────────┘
  [ 結果一覧テーブル + 詳細展開 ]
```

---

## 6. MySQL 初期化スクリプト

`mysql/init/` 配下に配置し、MySQL 起動時に自動実行される。

### mysql/init/01_create_databases.sql

```sql
CREATE DATABASE IF NOT EXISTS testSystemDB
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS cellularAnylyze
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON testSystemDB.* TO 'testuser'@'%';
GRANT ALL PRIVILEGES ON cellularAnylyze.* TO 'testuser'@'%';
FLUSH PRIVILEGES;
```

### mysql/init/02_create_android_tables.sql

```sql
USE testSystemDB;

CREATE TABLE IF NOT EXISTS android_test_results (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id        VARCHAR(64)  NOT NULL UNIQUE,
    scenario      VARCHAR(128) NOT NULL,
    device_id     VARCHAR(64)  NOT NULL,
    device_model  VARCHAR(128),
    test_site     VARCHAR(64)  DEFAULT 'unknown',
    operator_id   VARCHAR(64),
    started_at    DATETIME     NOT NULL,
    finished_at   DATETIME,
    total         INT          DEFAULT 0,
    pass_count    INT          DEFAULT 0,
    fail_count    INT          DEFAULT 0,
    result        ENUM('PASS','FAIL','RUNNING','ABORTED') DEFAULT 'RUNNING',
    note          TEXT,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS android_test_steps (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id         VARCHAR(64)  NOT NULL,
    step_id        INT          NOT NULL,
    action         VARCHAR(64)  NOT NULL,
    description    TEXT,
    response       TEXT,
    measured_value DOUBLE,
    unit           VARCHAR(32),
    upper_limit    DOUBLE,
    lower_limit    DOUBLE,
    pass           BOOLEAN      NOT NULL DEFAULT FALSE,
    error_msg      TEXT,
    executed_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id),
    FOREIGN KEY (run_id) REFERENCES android_test_results(run_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 7. API リクエスト/レスポンス例

### 7.1 Android 試験サマリ

**リクエスト**
```
GET /api/v1/android/summary?scenarios[]=wifi_test&date_from=2024-01-01
```

**レスポンス**
```json
{
  "total": 150,
  "pass_count": 132,
  "fail_count": 18,
  "yield_pct": 88.0
}
```

### 7.2 Android 合否率 (グループ別)

**リクエスト**
```
GET /api/v1/android/yield?group_by=scenario
```

**レスポンス**
```json
[
  { "label": "wifi_test",    "pass_count": 45, "fail_count": 5, "total": 50, "yield_pct": 90.0 },
  { "label": "bt_test",      "pass_count": 48, "fail_count": 2, "total": 50, "yield_pct": 96.0 },
  { "label": "camera_test",  "pass_count": 39, "fail_count": 11,"total": 50, "yield_pct": 78.0 }
]
```

### 7.3 試験結果詳細

**リクエスト**
```
GET /api/v1/android/results/20240315T103045_wifi_test_SM-A536B
```

**レスポンス**
```json
{
  "run_id": "20240315T103045_wifi_test_SM-A536B",
  "scenario": "wifi_test",
  "device_id": "SM-A536B",
  "device_model": "Galaxy A53",
  "result": "PASS",
  "started_at": "2024-03-15T10:30:45",
  "finished_at": "2024-03-15T10:32:18",
  "total": 10,
  "pass_count": 10,
  "fail_count": 0,
  "steps": [
    {
      "step_id": 1,
      "action": "adb",
      "description": "WiFi ON",
      "response": "",
      "pass": true
    },
    {
      "step_id": 5,
      "action": "equipment_measure",
      "description": "RF電力測定",
      "measured_value": -28.5,
      "unit": "dBm",
      "upper_limit": -20.0,
      "lower_limit": -40.0,
      "pass": true
    }
  ]
}
```

---

## 8. フロントエンド API プロキシ設定

Vue 3 から2つのバックエンドにアクセスするため、Nginx でパスベースのプロキシを設定する。

### dashboard/nginx.conf

```nginx
server {
    listen 80;

    # Orchestrator API + WebSocket
    location /api/orchestrator/ {
        proxy_pass http://orchestrator:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Analysis Service API (RF + Android + 汎用分析)
    location /api/analysis/ {
        proxy_pass http://analysis-service:8001/;
    }

    # Vue 3 静的ファイル
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

### frontend/vite.config.ts (開発時プロキシ)

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api/orchestrator': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api\/orchestrator/, ''),
        ws: true,  // WebSocket 対応
      },
      '/api/analysis': {
        target: 'http://localhost:8001',
        rewrite: (path) => path.replace(/^\/api\/analysis/, ''),
      },
    },
  },
})
```

---

## 9. .env ファイル設計

`.env.example` に以下を追記する。

```dotenv
# MySQL (統合後追加)
MYSQL_ROOT_PASSWORD=change_this_root_pw
DB_PASSWORD=change_this_user_pw

# SharePoint (既存)
SHAREPOINT_SITE_URL=
SHAREPOINT_TENANT_ID=
SHAREPOINT_CLIENT_ID=
SHAREPOINT_CLIENT_SECRET=

# 試験環境識別子
TEST_SITE=line1
```

---

## 10. 移行手順

### フェーズ1: 基盤整備（優先度: 高）

1. `mysql/init/` SQL ファイル作成
2. `docker-compose.yml` に `mysql` サービス追加
3. `orchestrator/result_manager.py` に MySQL 書き込み追加
4. `orchestrator/requirements.txt` に `sqlalchemy`, `pymysql` 追加
5. テスト: `docker compose up mysql orchestrator` → 試験実行 → MySQL に結果確認

### フェーズ2: 分析サービス追加（優先度: 高）

6. `analysis-service/` ディレクトリ作成（opeAnyalyze `backend/` をコピー）
7. `analysis-service/app/routers/android.py` 新規作成
8. `analysis-service/app/config.py` を2DB対応に改修
9. `docker-compose.yml` に `analysis-service` サービス追加
10. テスト: `GET /api/v1/android/summary` が動作すること

### フェーズ3: ダッシュボード統合（優先度: 中）

11. `dashboard/` を opeAnyalyze `frontend/` で置き換え
12. `TestControlView.vue` 新規作成（試験制御 + WebSocket ログ）
13. `AndroidDashboardView.vue` 新規作成（Android 試験結果分析）
14. Nginx プロキシ設定
15. E2E テスト: 試験実行 → MySQL → 分析画面に反映

### フェーズ4: 仕上げ（優先度: 低）

16. 既存 HTML dashboard を削除
17. 既存 JSON ファイル結果のマイグレーション（オプション）
18. SharePoint との二重書き込み継続 or 廃止を決定
19. 本番環境向け MySQL バックアップ設定

---

## 11. ファイル変更一覧

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `docker-compose.yml` | 変更 | mysql / analysis-service 追加、orchestrator に DB 環境変数追加 |
| `.env.example` | 変更 | MySQL 認証情報追加 |
| `mysql/init/01_create_databases.sql` | 新規 | DB・ユーザー作成 |
| `mysql/init/02_create_android_tables.sql` | 新規 | テーブル定義 |
| `orchestrator/result_manager.py` | 変更 | MySQL 書き込みメソッド追加 |
| `orchestrator/requirements.txt` | 変更 | sqlalchemy, pymysql 追加 |
| `analysis-service/` | 新規 | opeAnyalyze backend ベースの分析サービス |
| `analysis-service/app/routers/android.py` | 新規 | Android 試験結果 API |
| `analysis-service/app/config.py` | 新規 | 2DB 接続設定 |
| `dashboard/` | 置き換え | HTML → Vue 3 + Nginx |
| `dashboard/src/views/TestControlView.vue` | 新規 | 試験制御画面 |
| `dashboard/src/views/AndroidDashboardView.vue` | 新規 | Android 分析画面 |

---

## 12. 設計上のトレードオフ

| 決定事項 | 採用案 | 理由 |
|---|---|---|
| DB統合方法 | 同一MySQL、別DB名 | 既存opeAnyalyzeのDB名変更なし。同コンテナで管理が容易 |
| 分析サービスの配置 | 独立コンテナ | Orchestrator と責務分離。RF/Android 両方のデータを参照可能 |
| フロントエンド | opeAnyalyze frontend を流用 | Vue 3 + ECharts の資産再利用。新規開発コスト削減 |
| JSON保存の扱い | MySQL 追加後も継続 | 後退互換性確保。MySQL障害時のフォールバック |
| SharePointの扱い | 継続（廃止しない） | 現場ユーザーが既にSharePointレポートを利用している可能性 |
