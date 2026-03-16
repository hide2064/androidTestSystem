# システムアーキテクチャ設計書

| 項目 | 内容 |
|---|---|
| ドキュメント番号 | AND-TEST-ARCH-001 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-16 |
| 関連ドキュメント | [詳細設計書 design.md](./design.md) |

---

## 目次

1. [全体ブロック構成図](#1-全体ブロック構成図)
2. [Dockerコンテナ構成図](#2-dockerコンテナ構成図)
3. [起動シーケンス](#3-起動シーケンス)
4. [テスト実行シーケンス](#4-テスト実行シーケンス)
5. [リアルタイムログ配信シーケンス](#5-リアルタイムログ配信シーケンス)
6. [分析データ参照シーケンス](#6-分析データ参照シーケンス)
7. [Equipment Agent プラグイン構造](#7-equipment-agent-プラグイン構造)
8. [データフロー概要](#8-データフロー概要)

---

## 1. 全体ブロック構成図

### 1.1 システム全体像

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ホストPC（Windows / Mac / Linux）                                            ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  🌐 ブラウザ（Chrome / Edge）                                          │    ║
║  │     localhost:3000                                                   │    ║
║  └──────────────────────┬──────────────────────────────────────────────┘    ║
║                         │ HTTP                                               ║
║  ╔══════════════════════╪══════════════════════════════════════════════╗     ║
║  ║  🐳 Docker Network: test-system-network                             ║     ║
║  ║                      │                                              ║     ║
║  ║         ┌────────────▼─────────────┐                               ║     ║
║  ║         │  📊 dashboard  :3000     │                               ║     ║
║  ║         │  Nginx + Vue 3           │                               ║     ║
║  ║         └────────┬─────────┬───────┘                               ║     ║
║  ║     /api/orchestrator/    /api/analysis/                           ║     ║
║  ║                  │                │                                ║     ║
║  ║    ┌─────────────▼──────┐  ┌──────▼─────────────────┐            ║     ║
║  ║    │  🎯 orchestrator   │  │  📈 analysis-service   │            ║     ║
║  ║    │  FastAPI  :8000    │  │  FastAPI+pandas :8001  │            ║     ║
║  ║    └──┬──────────────┬──┘  └──────────────┬─────────┘            ║     ║
║  ║       │              │                     │                      ║     ║
║  ║  ┌────▼───┐    ┌─────▼──────┐        ┌────▼──────────┐          ║     ║
║  ║  │📱      │    │ 🔧         │        │  🗄️ mysql     │          ║     ║
║  ║  │android │    │ equipment  │        │  MySQL 8.4    │          ║     ║
║  ║  │-agent  │    │ -agent     │        │  :3306        │          ║     ║
║  ║  │:5000   │    │ :5001      │   ┌────┤               ├────┐     ║     ║
║  ║  └────┬───┘    └─────┬──────┘   │    └───────────────┘    │     ║     ║
║  ║       │              │          │                          │     ║     ║
║  ║  ┌────▼───┐          │     testSystemDB          cellularAnylyze ║     ║
║  ║  │🤖      │          │   (Android試験結果)          (RF試験データ)  ║     ║
║  ║  │appium  │          │                                            ║     ║
║  ║  │:4723   │          │                                            ║     ║
║  ╚══╪════════╪══════════╪════════════════════════════════════════════╝     ║
║     │        │          │                                                   ║
║  ADB:5037    │    VISA/Serial                                               ║
║     │        │          │                                                   ║
║  ┌──▼──┐     │    ┌─────▼──────────────┐                                   ║
║  │ 📱  │     │    │  ⚡ 計測器          │                                   ║
║  │Android   │    │  電源・スペアナ等    │                                   ║
║  │端末(DUT)│     │  GPIB/USB/LAN       │                                   ║
║  └─────┘     │    └────────────────────┘                                   ║
║              │                                                              ║
║         SharePoint                                                          ║
║         (試験結果クラウド保存)                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 1.2 ブロック間接続の概要

```mermaid
graph TB
    Browser(["🌐 ブラウザ\nlocalhost:3000"])

    subgraph Docker["🐳 Docker Network: test-system-network"]
        Dashboard["📊 dashboard\nNginx + Vue 3\n:3000"]

        subgraph Backend["バックエンド層"]
            Orchestrator["🎯 orchestrator\nFastAPI\n:8000"]
            Analysis["📈 analysis-service\nFastAPI + pandas\n:8001"]
        end

        subgraph Agents["エージェント層"]
            AndroidAgent["📱 android-agent\nFastAPI + ADB\n:5000"]
            Appium["🤖 appium\nAppium Server\n:4723"]
            EquipmentAgent["🔧 equipment-agent\nFastAPI\n:5001"]
        end

        MySQL[("🗄️ mysql\nMySQL 8.4\n:3306")]
    end

    subgraph HostDevices["💻 ホスト接続デバイス"]
        ADBServer["ADB Server\n:5037"]
        Android["📱 Android端末\nDUT"]
        Instruments["⚡ 計測器\nVISA / Serial"]
    end

    SP["☁️ SharePoint\n試験結果クラウド"]

    Browser -->|"HTTP"| Dashboard
    Dashboard -->|"REST /api/orchestrator/"| Orchestrator
    Dashboard -->|"REST /api/analysis/"| Analysis
    Dashboard <-->|"WebSocket /api/orchestrator/ws/log"| Orchestrator

    Orchestrator -->|"HTTP REST"| AndroidAgent
    Orchestrator -->|"HTTP REST"| EquipmentAgent
    Orchestrator -->|"SQL"| MySQL
    Orchestrator -.->|"HTTPS (試験完了時)"| SP

    AndroidAgent -->|"Appium WebDriver"| Appium
    AndroidAgent -->|"adb -H"| ADBServer

    Appium -->|"adb -H host.docker.internal"| ADBServer
    ADBServer -->|"USB / WiFi"| Android

    Analysis -->|"SQL"| MySQL

    EquipmentAgent -->|"VISA / PySerial"| Instruments

    style Docker fill:#e8f4fd,stroke:#2196F3
    style HostDevices fill:#f3e8fd,stroke:#9C27B0
    style Backend fill:#e8fde8,stroke:#4CAF50
    style Agents fill:#fde8e8,stroke:#F44336
```

---

## 2. Dockerコンテナ構成図

```mermaid
graph LR
    subgraph Compose["docker-compose.yml"]
        direction TB

        subgraph layer4["起動順序 ④ (最後)"]
            Dashboard["📊 dashboard\nbuild: ./dashboard\nports: 3000:3000\nhealthcheck: wget :3000"]
        end

        subgraph layer3["起動順序 ③"]
            Orchestrator["🎯 orchestrator\nbuild: ./orchestrator\nports: 8000:8000\nhealthcheck: python urllib :8000/health"]
        end

        subgraph layer2["起動順序 ②"]
            AndroidAgent["📱 android-agent\nbuild: ./android-agent\nports: 5000:5000\nhealthcheck: curl :5000/health"]
            EquipmentAgent["🔧 equipment-agent\nbuild: ./equipment-agent\nports: 5001:5001\nhealthcheck: python urllib :5001/health"]
            Analysis["📈 analysis-service\nbuild: ./analysis-service\nports: 8001:8001\nhealthcheck: python urllib :8001/health"]
        end

        subgraph layer1["起動順序 ① (先行起動)"]
            Appium["🤖 appium\nimage: appium/appium:latest\nports: 4723:4723\nhealthcheck: curl :4723/status\nstart_period: 30s"]
            MySQL[("🗄️ mysql\nimage: mysql:8.4\nports: 13306:3306\nhealthcheck: mysqladmin ping")]
        end
    end

    MySQL -->|"service_healthy"| Orchestrator
    MySQL -->|"service_healthy"| Analysis
    Appium -->|"service_healthy"| AndroidAgent
    AndroidAgent -->|"service_healthy"| Orchestrator
    EquipmentAgent -->|"service_healthy"| Orchestrator
    Orchestrator -->|"service_healthy"| Dashboard
    Analysis -->|"service_healthy"| Dashboard

    style layer1 fill:#fff3cd,stroke:#ffc107
    style layer2 fill:#d4edda,stroke:#28a745
    style layer3 fill:#cce5ff,stroke:#004085
    style layer4 fill:#f8d7da,stroke:#721c24
```

### 2.1 ボリューム・ネットワーク構成

```
volumes:
  mysql_data ─────────────── mysql:/var/lib/mysql          (永続データ)

bind mounts:
  ./orchestrator/scenarios ─ orchestrator:/app/scenarios   (YAMLシナリオ)
  ./results ──────────────── orchestrator:/app/results     (試験結果JSON)
  ./equipment-agent/config ─ equipment-agent:/app/config   (機器設定YAML)
  ./mysql/init ────────────── mysql:/docker-entrypoint-initdb.d (初期化SQL)

network:
  test-system-network (bridge) ─ 全コンテナ間通信
  host.docker.internal ─────── Dockerコンテナ→ホストPC (ADB接続用)
```

---

## 3. 起動シーケンス

### 3.1 `docker compose up -d` 実行時の起動フロー

```mermaid
sequenceDiagram
    actor User as 👤 ユーザー
    participant DC as 🐳 Docker Compose
    participant MySQL as 🗄️ mysql
    participant Appium as 🤖 appium
    participant EQ as 🔧 equipment-agent
    participant AA as 📱 android-agent
    participant ORC as 🎯 orchestrator
    participant AN as 📈 analysis-service
    participant DASH as 📊 dashboard

    User->>DC: docker compose up -d
    DC->>MySQL: コンテナ起動
    DC->>Appium: コンテナ起動
    DC->>EQ: コンテナ起動
    DC->>AA: コンテナ起動（appium healthy 待機）
    DC->>AN: コンテナ起動（mysql healthy 待機）
    DC->>ORC: コンテナ起動（mysql / android-agent / equipment-agent healthy 待機）
    DC->>DASH: コンテナ起動（orchestrator / analysis-service healthy 待機）

    Note over MySQL: mysqladmin ping ループ（10s間隔）
    MySQL-->>DC: ✅ service_healthy

    Note over Appium: curl :4723/status ループ（15s間隔 / 最大30s待機）
    Appium-->>DC: ✅ service_healthy

    Note over EQ: python urllib :5001/health ループ
    EQ-->>DC: ✅ service_healthy

    Note over AA: appium healthy 確認後 FastAPI 起動
    AA-->>DC: ✅ service_healthy

    Note over AN: mysql healthy 確認後 FastAPI 起動
    AN-->>DC: ✅ service_healthy

    Note over ORC: 全依存サービス healthy 確認後 FastAPI 起動
    ORC-->>DC: ✅ service_healthy

    Note over DASH: orchestrator / analysis-service healthy 確認後 Nginx 起動
    DASH-->>DC: ✅ service_healthy

    DC-->>User: 全サービス起動完了
    User->>DASH: http://localhost:3000 アクセス
```

### 3.2 healthcheck 依存チェーン

```
[appium]────────────────────────────┐
                                    ▼
[mysql]──────┬──────────────► [android-agent]──┐
             │                                  ├──► [orchestrator]──► [dashboard]
             │               [equipment-agent]──┘
             │
             └──────────────► [analysis-service]──────────────────► [dashboard]
```

---

## 4. テスト実行シーケンス

### 4.1 試験開始から完了までの全体フロー

```mermaid
sequenceDiagram
    actor User as 👤 試験員
    participant DASH as 📊 dashboard
    participant ORC as 🎯 orchestrator
    participant AA as 📱 android-agent
    participant APPIUM as 🤖 appium
    participant EQ as 🔧 equipment-agent
    participant INST as ⚡ 計測器
    participant DUT as 📱 Android端末(DUT)
    participant DB as 🗄️ mysql
    participant SP as ☁️ SharePoint

    User->>DASH: シナリオ選択・端末指定・[開始] ボタン押下
    DASH->>ORC: POST /api/orchestrator/test/start\n{scenario, device_id}

    ORC->>ORC: YAMLシナリオ読み込み・パース
    ORC->>ORC: StateManager: idle → running

    loop 各ステップ実行
        alt action: adb
            ORC->>AA: POST /adb/command\n{device_id, command}
            AA->>DUT: adb shell {command}
            DUT-->>AA: stdout
            AA-->>ORC: {output, returncode}

        else action: tap / input_text / assert_text
            ORC->>AA: POST /appium/tap\n{device_id, locator_type, locator_value}
            AA->>APPIUM: Appium WebDriver API\n(capabilities付きセッション)
            APPIUM->>DUT: UiAutomator2 操作
            DUT-->>APPIUM: 操作結果
            APPIUM-->>AA: WebDriver response
            AA-->>ORC: {status}

        else action: equipment_measure
            ORC->>EQ: POST /instruments/{name}/measure/{parameter}
            EQ->>INST: VISA/Serial コマンド送信\n(例: MEAS:VOLT:DC?)
            INST-->>EQ: 測定値
            EQ-->>ORC: {value, unit, pass/fail}

        else action: wait
            ORC->>ORC: asyncio.sleep(seconds)
        end

        ORC->>ORC: ステップ結果をlog_queueに投入\n(WebSocket配信用)
    end

    ORC->>ORC: ResultManager: 結果集計・合否判定
    ORC->>DB: INSERT test_results, test_steps
    ORC->>SP: POST 試験結果（SharePoint Lists）
    ORC->>ORC: StateManager: running → finished

    ORC-->>DASH: HTTP 200 {test_id, status: "finished"}
    DASH-->>User: 試験完了表示
```

### 4.2 ステップ実行の詳細フロー（on_fail 制御）

```mermaid
flowchart TD
    A([試験開始]) --> B[次のステップを取得]
    B --> C{action種別}

    C -->|adb| D[ADB shell実行]
    C -->|tap/input/assert| E[Appium UI操作]
    C -->|equipment_measure| F[計測器測定]
    C -->|wait| G[待機]
    C -->|screenshot| H[スクリーンショット保存]

    D --> I{期待値あり?}
    E --> I
    F --> I
    G --> J[ステップ成功]
    H --> J

    I -->|No| J
    I -->|Yes| K{期待値一致?}

    K -->|PASS| J
    K -->|FAIL| L{on_fail設定}

    L -->|stop| M([試験中断・FAIL])
    L -->|continue / 未設定| N[警告ログ出力]
    N --> J

    J --> O{全ステップ完了?}
    O -->|No| B
    O -->|Yes| P([試験完了・結果集計])

    style M fill:#f8d7da,stroke:#721c24
    style P fill:#d4edda,stroke:#155724
```

---

## 5. リアルタイムログ配信シーケンス

```mermaid
sequenceDiagram
    participant DASH as 📊 dashboard\n(Vue 3)
    participant NGINX as 🔀 Nginx\n(WebSocket Proxy)
    participant ORC as 🎯 orchestrator\n(FastAPI)

    DASH->>NGINX: WebSocket Upgrade\nGET /api/orchestrator/ws/log
    NGINX->>ORC: WebSocket Upgrade\nws://orchestrator:8000/ws/log
    ORC-->>NGINX: 101 Switching Protocols
    NGINX-->>DASH: 101 Switching Protocols
    Note over DASH,ORC: WebSocket 接続確立

    loop テスト実行中（各ステップ完了ごと）
        ORC->>ORC: log_queue.put(log_entry)
        ORC->>NGINX: WebSocket frame\n{"step": 3, "action": "adb",\n"status": "pass", "output": "..."}
        NGINX->>DASH: WebSocket frame（中継）
        DASH->>DASH: ログ一覧にリアルタイム追記
    end

    ORC->>NGINX: WebSocket frame\n{"status": "finished", "result": "PASS"}
    NGINX->>DASH: WebSocket frame（中継）
    DASH->>DASH: 試験完了表示

    ORC->>NGINX: WebSocket Close
    NGINX->>DASH: WebSocket Close
    Note over DASH,ORC: 接続クローズ
```

### 5.1 Nginx WebSocket プロキシ設定

```nginx
# dashboard/nginx.conf（抜粋）

location /api/orchestrator/ {
    proxy_pass         http://orchestrator:8000/;
    proxy_http_version 1.1;

    # WebSocket に必要なヘッダー
    proxy_set_header   Upgrade    $http_upgrade;
    proxy_set_header   Connection "upgrade";
    proxy_set_header   Host       $host;
}
```

---

## 6. 分析データ参照シーケンス

### 6.1 Android試験結果分析

```mermaid
sequenceDiagram
    actor User as 👤 試験員
    participant DASH as 📊 dashboard\n(Android分析タブ)
    participant AN as 📈 analysis-service
    participant DB as 🗄️ mysql\n(testSystemDB)

    User->>DASH: Android分析タブを開く

    par KPIカード取得
        DASH->>AN: GET /api/analysis/android/kpi
        AN->>DB: SELECT COUNT(*), SUM(CASE WHEN result='PASS'...) FROM test_results
        DB-->>AN: 集計結果
        AN-->>DASH: {total: 120, pass: 98, fail: 22, pass_rate: 81.7}
    and 合否率グラフ
        DASH->>AN: GET /api/analysis/android/pass-rate-trend
        AN->>DB: SELECT DATE(created_at), pass_rate FROM test_results GROUP BY DATE
        DB-->>AN: 日次データ
        AN-->>DASH: [{date, pass_rate}, ...]
    and 試験結果一覧
        DASH->>AN: GET /api/analysis/android/results?limit=50
        AN->>DB: SELECT * FROM test_results ORDER BY created_at DESC LIMIT 50
        DB-->>AN: レコード一覧
        AN-->>DASH: [{test_id, device, scenario, result, duration}, ...]
    end

    DASH->>DASH: EChartsでグラフ描画
    DASH-->>User: ダッシュボード表示
```

### 6.2 RF試験データ分析（汎用分析）

```mermaid
sequenceDiagram
    actor User as 👤 試験員
    participant DASH as 📊 dashboard\n(RF分析タブ)
    participant AN as 📈 analysis-service
    participant DB as 🗄️ mysql\n(cellularAnylyze)

    User->>DASH: スライサー条件を設定\n(周波数帯・端末・日付範囲)
    DASH->>AN: GET /api/analysis/rf/schema\n(テーブル・カラム一覧取得)
    AN->>DB: SHOW TABLES / DESCRIBE {table}
    DB-->>AN: スキーマ情報
    AN-->>DASH: [{table, columns, types}]

    User->>DASH: 分析実行ボタン押下
    DASH->>AN: POST /api/analysis/rf/analyze\n{table, filters, analysis_type: "distribution"}

    AN->>DB: SELECT {columns} FROM {table}\nWHERE {filters}
    DB-->>AN: 生データ（pandas DataFrameに変換）

    AN->>AN: analyzers/distribution.py\n- ヒストグラム計算\n- 統計量算出(mean/std/min/max)
    AN-->>DASH: {bins, counts, stats: {mean, std, ...}}

    DASH->>DASH: EChartsで分布グラフ描画
    DASH-->>User: 分析結果表示
```

---

## 7. Equipment Agent プラグイン構造

### 7.1 プラグインアーキテクチャ

```mermaid
graph TD
    Config["📄 equipment.yaml\n\ninstruments:\n  power_supply:\n    driver: visa.keysight_e3631a\n    address: GPIB0::5::INSTR\n  spectrum_analyzer:\n    driver: visa.rohde_fsp\n    address: GPIB0::20::INSTR"]

    subgraph Agent["🔧 equipment-agent"]
        Main["main.py\nFastAPI :5001"]
        AgentCore["agent.py\nEquipmentAgent\n_load_config()"]
        Base["base_driver.py\nBaseDriver (abstract)\n- connect()\n- disconnect()\n- measure()\n- send_command()"]
    end

    subgraph Drivers["drivers/ (プラグイン)"]
        VISA1["visa/keysight_e3631a.py\nDriver(BaseDriver)\n- measure('voltage_ch1')\n- set_voltage(v)"]
        VISA2["visa/rohde_fsp.py\nDriver(BaseDriver)\n- measure('peak_power')\n- set_center_freq(f)"]
        Serial["serial/custom_device.py\nDriver(BaseDriver)"]
        Mock["mock/dummy.py\nDriver(BaseDriver)\n(開発・テスト用)"]
    end

    subgraph Instruments["⚡ 物理計測器"]
        PSU["電源装置\nGPIB0::5"]
        SA["スペアナ\nGPIB0::20"]
    end

    Config -->|"起動時 _load_config()"| AgentCore
    Main --> AgentCore
    AgentCore -->|"importlib.import_module()"| VISA1
    AgentCore -->|"importlib.import_module()"| VISA2
    AgentCore -->|"importlib.import_module()"| Serial
    AgentCore -->|"importlib.import_module()"| Mock
    VISA1 --> Base
    VISA2 --> Base
    Serial --> Base
    Mock --> Base
    VISA1 -->|"pyvisa"| PSU
    VISA2 -->|"pyvisa"| SA
```

### 7.2 計測器追加手順

```
1. drivers/{type}/{instrument_name}.py を追加
   └── class Driver(BaseDriver) を実装

2. equipment.yaml に追記
   └── instruments:
         my_instrument:
           driver: visa.my_instrument
           address: "GPIB0::10::INSTR"

3. docker compose restart equipment-agent
   └── 再起動のみでOK（コードの変更不要）
```

---

## 8. データフロー概要

### 8.1 試験結果データの流れ

```mermaid
flowchart LR
    subgraph Input["入力"]
        YAML["📄 シナリオ YAML\nsteps定義"]
        DUT["📱 Android端末\nADB/Appium応答"]
        INST["⚡ 計測器\n測定値"]
    end

    subgraph Processing["処理"]
        ORC["🎯 orchestrator\nステップ実行・結果集計"]
        RM["ResultManager\n合否判定"]
    end

    subgraph Storage["保存"]
        JSON["📁 results/*.json\nローカルバックアップ"]
        DB1[("🗄️ testSystemDB\ntest_results\ntest_steps")]
        CLOUD["☁️ SharePoint Lists\nクラウド共有"]
    end

    subgraph Analysis["分析・可視化"]
        AN["📈 analysis-service\npandas + scipy"]
        DASH["📊 dashboard\nECharts グラフ"]
    end

    YAML --> ORC
    DUT --> ORC
    INST --> ORC
    ORC --> RM
    RM --> JSON
    RM --> DB1
    RM --> CLOUD
    DB1 --> AN
    AN --> DASH
```

### 8.2 RFデータの流れ

```mermaid
flowchart LR
    subgraph Import["データ取り込み"]
        CSV["📄 RF試験 CSV\n(opeAnyalyzeで計測)"]
        Script["scripts/load_csv.py"]
    end

    subgraph Storage["保存"]
        DB2[("🗄️ cellularAnylyze\nRFデータテーブル")]
    end

    subgraph Analysis["分析"]
        AN["📈 analysis-service\nrouters/rf.py\nanalyzers/\n  distribution.py\n  timeseries.py\n  correlation.py"]
        DASH["📊 dashboard\nRF分析タブ\nECharts"]
    end

    CSV --> Script
    Script -->|"INSERT"| DB2
    DB2 -->|"SELECT + pandas"| AN
    AN --> DASH
```

### 8.3 MySQLデータベース構成

```
mysql:3306
  ├── testSystemDB          ← Android試験結果
  │     ├── test_results    (試験ID・シナリオ・端末・合否・日時)
  │     └── test_steps      (ステップID・アクション・期待値・実測値・合否)
  │
  └── cellularAnylyze       ← RF試験データ (opeAnyalyze)
        └── {動的テーブル}   (スキーマはCSVインポート時に自動生成)
```

---

## 付録: ポート一覧

| サービス | コンテナポート | ホストポート | 用途 |
|---|---|---|---|
| dashboard | 3000 | 3000 | ブラウザアクセス |
| orchestrator | 8000 | 8000 | REST API / WebSocket |
| android-agent | 5000 | 5000 | ADB/Appium REST API |
| appium | 4723 | 4723 | Appium WebDriver Server |
| equipment-agent | 5001 | 5001 | 計測器制御 REST API |
| analysis-service | 8001 | 8001 | 分析 REST API |
| mysql | 3306 | **13306** | MySQL (ホスト3306は別用途のため) |
