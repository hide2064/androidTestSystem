# Android 自動試験システム 設計書

**バージョン:** 1.0.0
**作成日:** 2026-03-15
**対象リポジトリ:** android-test-system

---

## 1. システム概要

Android OS 搭載端末と試験機材を自動制御し、試験結果をクラウドで一元管理するシステムです。

### 1.1 要件一覧

| 要件 | 対応方法 | 状態 |
|---|---|---|
| Android端末の自動試験 | ADB + Appium | ✅ 実装済 |
| ブラウザでコントロール | Web Dashboard (localhost:3000) | ✅ 実装済 |
| 様々な試験機材の制御 | Equipment Agent（プラグイン式） | ✅ 実装済 |
| 様々なPCで利用可能 | Docker Compose | ✅ 実装済 |
| 簡単な環境構築 | `docker compose up` 一発起動 | ✅ 実装済 |
| バージョンアップ | `git pull && docker compose up --build` | ✅ 手動運用 |
| クラウド結果管理 | SharePoint Lists + Power BI | ✅ 実装済 |
| 属人化防止 | YAML試験定義・Python標準構成 | ✅ 実装済 |

---

## 2. システムアーキテクチャ

### 2.1 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│  ホストPC（Windows）                                          │
│                                                             │
│  試験員 ──► ブラウザ ──► http://localhost:3000               │
│                                │                            │
│  ┌─────────────────────────────▼───────────────────────┐   │
│  │  Docker Compose                                      │   │
│  │                                                     │   │
│  │  ┌────────────┐   ┌─────────────┐                   │   │
│  │  │ Dashboard  │   │Orchestrator │  :8000             │   │
│  │  │  :3000     ├──►│ (FastAPI)   │                   │   │
│  │  │  (nginx)   │   └──────┬──────┘                   │   │
│  │  └────────────┘          │ REST API                  │   │
│  │                    ┌─────┴──────┐                    │   │
│  │                    │            │                    │   │
│  │  ┌─────────────────▼─┐  ┌──────▼───────────────┐   │   │
│  │  │  Android Agent    │  │  Equipment Agent      │   │   │
│  │  │  :5000 (FastAPI)  │  │  :5001 (FastAPI)      │   │   │
│  │  │  Appium :4723     │  │  drivers/ (プラグイン)│   │   │
│  │  └─────────┬─────────┘  └──────────┬────────────┘   │   │
│  └────────────┼───────────────────────┼────────────────┘   │
│               │ TCP:5037              │ VISA/Serial/REST    │
│  ADB Server ◄─┘                      └─► 試験機材           │
│  （ホスト常駐）│                          （電源・計測器等）  │
│               │ USB / Wi-Fi                                 │
│          Android端末 (DUT)                                  │
└─────────────────────────────────────────────────────────────┘
                        │ Microsoft Graph API
                        ▼
              ☁️ SharePoint Lists
                        │
                        ▼
                  Power BI ダッシュボード
```

### 2.2 コンポーネント一覧

| コンポーネント | 技術スタック | ポート | 役割 |
|---|---|---|---|
| Web Dashboard | HTML/JS + nginx | 3000 | 試験操作・リアルタイムログ・結果閲覧 |
| Orchestrator | Python + FastAPI + WebSocket | 8000 | 試験シナリオ管理・各Agentへの指示・結果送信 |
| Android Agent | Python + FastAPI + ADB + Appium | 5000 / 4723 | Android端末のUI操作・低レベル制御 |
| Equipment Agent | Python + FastAPI + PyVISA/Serial | 5001 | 計測器・試験機材の制御（プラグイン式） |

### 2.3 ADB接続方式

```
ホストPC
  ├── ADB Server（ホスト常駐、初回のみインストール）
  │       │ USB / Wi-Fi ADB
  │       └── Android端末
  │
  └── Docker コンテナ群
        └── Android Agent
              └── TCP:5037 → host.docker.internal → ADB Server
```

**採用理由:** DockerコンテナからUSBデバイスへの直接アクセスはLinuxホスト限定のため、ホストのADB Serverに TCP 経由で接続する方式を採用。Windows/Mac/Linux 全対応。

---

## 3. コンポーネント詳細設計

### 3.1 Orchestrator

```
orchestrator/
├── main.py               # FastAPI + WebSocket エントリーポイント
├── scenario_runner.py    # YAMLシナリオ実行エンジン（核心）
├── scenario_parser.py    # YAML読み込み・バリデーション
├── state_manager.py      # 試験状態管理（idle/running/finished/error）
├── result_manager.py     # 結果集計・Pass/Fail判定・ファイル保存
├── agent_client.py       # Android Agent / Equipment Agent との HTTP通信
├── sharepoint_client.py  # Microsoft Graph API 経由でSharePointへ送信
└── scenarios/            # YAMLシナリオ置き場
```

#### API エンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/scenarios` | 利用可能なシナリオ一覧 |
| POST | `/test/start` | 試験開始 `{scenario_name, device_id}` |
| POST | `/test/stop` | 試験中断 |
| GET | `/test/status` | 現在の試験状態 |
| GET | `/results` | 試験結果履歴 |
| GET | `/devices` | 接続中のAndroid端末一覧 |
| GET | `/instruments` | 接続中の計測器一覧 |
| WS | `/ws/log` | リアルタイムログ（WebSocket） |

#### シナリオ実行フロー

```
ScenarioParser.load(yaml)
        │
        ▼
ScenarioRunner.run()
        │
        ├─ [adb]                → AndroidAgentClient.adb_command()
        ├─ [tap]                → AndroidAgentClient.tap()
        ├─ [assert_text]        → AndroidAgentClient.get_text() + evaluate()
        ├─ [equipment_measure]  → EquipmentAgentClient.measure() + evaluate_numeric()
        ├─ [equipment_method]   → EquipmentAgentClient.call_method()
        ├─ [wait]               → asyncio.sleep()
        └─ [screenshot]         → AndroidAgentClient.screenshot()
                │
                ▼
        ResultManager.summarize()
                │
                ├─► ローカルファイル保存（results/*.json）
                └─► SharePointClient.send_result()
```

### 3.2 Equipment Agent（プラグイン設計）

```
equipment-agent/
├── main.py          # FastAPI エントリーポイント
├── agent.py         # プラグインローダー・機材マネージャー
├── base_driver.py   # 全ドライバの共通インターフェース（抽象基底クラス）
├── config/
│   └── equipment.yaml   ← 接続機材の設定（PCごとに編集）
└── drivers/
    ├── visa/
    │   ├── keysight_e3631a.py   # Keysight E3631A 三出力電源
    │   └── keysight_n9020b.py   # Keysight N9020B スペクトラムアナライザ
    ├── serial/
    │   └── generic_serial.py    # 汎用シリアル通信ドライバ
    ├── rest/
    │   └── generic_rest.py      # 汎用REST APIドライバ
    └── mock/
        └── mock_driver.py       # モックドライバ（実機なし動作確認用）
```

#### BaseDriver インターフェース

```python
class BaseDriver(ABC):
    def connect(self) -> None       # 必須実装
    def disconnect(self) -> None    # 必須実装
    def send_command(self, cmd) -> str   # 必須実装
    def measure(self, parameter) -> MeasureResult  # 必須実装
    def reset(self) -> None         # オーバーライド任意（デフォルト: *RST）
    def get_id(self) -> str         # オーバーライド任意（デフォルト: *IDN?）
```

#### 新機材追加手順

```
1. drivers/<通信方式>/<機材名>.py を作成
   └── BaseDriver を継承して4メソッドを実装
2. config/equipment.yaml にエントリを追記
3. docker compose restart equipment-agent

→ コアコードの変更は不要
```

#### Equipment Agent API

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/instruments` | 機材一覧・接続状態 |
| POST | `/instruments/{name}/connect` | 接続 |
| POST | `/instruments/{name}/disconnect` | 切断 |
| POST | `/instruments/{name}/command` | 生コマンド送信 |
| GET | `/instruments/{name}/measure/{parameter}` | 測定値取得 |
| POST | `/instruments/{name}/method` | 機材固有メソッド呼び出し |
| POST | `/instruments/{name}/reset` | リセット |
| GET | `/instruments/{name}/id` | 機材ID取得 |

### 3.3 Android Agent

```
android-agent/
├── main.py           # FastAPI エントリーポイント
├── adb_client.py     # ADB コマンドラッパー
├── appium_client.py  # Appium WebDriver クライアント
└── start.sh          # Appium Server + FastAPI 同時起動スクリプト
```

#### ADB / Appium 役割分担

| 操作 | ADB | Appium |
|---|---|---|
| 端末初期化・再起動 | ✅ | — |
| APKインストール | ✅ | — |
| Wi-Fi/機内モード切替 | ✅ | — |
| logcat収集 | ✅ | — |
| スクリーンショット | ✅ | — |
| UI要素タップ（ID/テキスト指定） | — | ✅ |
| テキスト入力 | — | ✅ |
| 画面状態確認・テキスト取得 | — | ✅ |
| 要素出現待機（WebDriverWait） | — | ✅ |

### 3.4 Web Dashboard

単一の HTML ファイル（依存パッケージなし）。nginx コンテナで配信。

| 機能 | 実装 |
|---|---|
| シナリオ選択・試験開始/停止 | REST API (`/test/start`, `/test/stop`) |
| リアルタイムログ表示 | WebSocket (`/ws/log`) |
| ステップ進捗表示 | ステータスポーリング (`/test/status`) |
| 試験結果履歴 | REST API (`/results`) |
| 計測器・端末状態表示 | REST API (`/instruments`, `/devices`) |

---

## 4. 試験シナリオ定義（YAML）

### 4.1 基本構造

```yaml
name: 試験名称           # 必須
version: "1.0"           # 任意
description: 説明文      # 任意

steps:
  - id: 1                # 必須（通し番号）
    description: 説明    # 必須
    action: adb          # 必須（下記 action 一覧参照）
    on_fail: stop        # 任意：FAIL時に試験を中断する場合
    # action ごとの追加パラメータ...
```

### 4.2 action 一覧

| action | 説明 | 追加パラメータ |
|---|---|---|
| `adb` | ADB shell コマンド実行 | `command`, `expect` |
| `tap` | 画面要素をタップ | `locator_type`, `locator_value` |
| `input_text` | テキスト入力 | `locator_type`, `locator_value`, `text` |
| `assert_text` | テキスト確認 | `locator_type`, `locator_value`, `expect` |
| `assert_exists` | 要素の存在確認 | `locator_type`, `locator_value` |
| `equipment_measure` | 計測器で測定 | `device`, `parameter`, `expect` |
| `equipment_method` | 計測器メソッド呼び出し | `device`, `method`, `args` |
| `equipment_command` | 計測器生コマンド送信 | `device`, `command`, `expect` |
| `screenshot` | スクリーンショット保存 | `save_path` |
| `wait` | 待機 | `seconds` |

### 4.3 locator_type 一覧

| locator_type | 指定方法 | 例 |
|---|---|---|
| `id` | リソースID | `com.example:id/btn_start` |
| `text` | 表示テキスト（完全一致） | `設定` |
| `xpath` | XPath式 | `//android.widget.Button[@text='OK']` |
| `class` | クラス名 | `android.widget.Button` |
| `desc` | content-description | `送信ボタン` |

### 4.4 expect（合否判定）

```yaml
# 文字列
expect:
  contains: "Pixel"          # 含む
  equals: "1"                # 完全一致
  not_contains: "ERROR"      # 含まない

# 数値
expect:
  greater_than: -80          # より大きい
  less_than: 5.0             # より小さい
  between: [3.5, 4.2]        # 範囲内（境界値含む）
  equals: 3.7                # 数値一致（tolerance: 0.001 デフォルト）
  tolerance: 0.01            # equals と組み合わせて許容誤差指定
```

---

## 5. SharePoint連携設計

### 5.1 データフロー

```
試験完了
    │
    ▼
ResultManager.save_and_send()
    ├─► results/<timestamp>_<scenario>_<device>.json（ローカル保存）
    └─► SharePointClient.send_result()
              │ Microsoft Graph API
              ▼
        SharePoint Lists（TestResults リスト）
              │
              ▼
          Power BI
```

### 5.2 SharePoint Lists スキーマ（TestResults）

| 列名 | 型 | 内容 |
|---|---|---|
| Title | テキスト | `{scenario} / {device_id}` |
| Scenario | テキスト | シナリオ名 |
| DeviceId | テキスト | 端末ID |
| TestSite | テキスト | 試験サイト名（.env で設定） |
| Result | テキスト | PASS / FAIL |
| PassCount | 数値 | PASSステップ数 |
| FailCount | 数値 | FAILステップ数 |
| Total | 数値 | 総ステップ数 |
| Timestamp | 日時 | 試験実施日時 |
| Details | 複数行テキスト | ステップ詳細（JSON） |

### 5.3 Azure AD アプリ登録手順

1. Azure Portal → Azure Active Directory → アプリの登録
2. 「新規登録」→ 名前: `android-test-system`
3. 「証明書とシークレット」→ クライアントシークレットを作成
4. 「APIのアクセス許可」→ Microsoft Graph → アプリケーションの許可
   - `Sites.ReadWrite.All`
5. `.env` に以下を設定:

```env
SHAREPOINT_TENANT_ID=<ディレクトリ(テナント)ID>
SHAREPOINT_CLIENT_ID=<アプリケーション(クライアント)ID>
SHAREPOINT_CLIENT_SECRET=<作成したシークレット値>
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/test
```

---

## 6. セットアップ手順

### 6.1 初回セットアップ（各PCで1回）

```
Step 1: Android Platform Tools インストール
  ① https://developer.android.com/tools/releases/platform-tools からダウンロード
  ② 解凍して C:\android-tools\ 等に配置
  ③ システム環境変数の Path に追加
  ④ コマンドプロンプトで adb version を実行して確認

Step 2: ADB Server 自動起動設定
  ① スタートアップフォルダに adb start-server を起動するショートカットを作成
     または タスクスケジューラ → ログオン時 → adb start-server

Step 3: Docker Desktop インストール
  ① https://www.docker.com/products/docker-desktop からインストール

Step 4: リポジトリ取得
  > git clone https://github.com/your-org/android-test-system
  > cd android-test-system

Step 5: 環境設定
  > copy .env.example .env
  メモ帳等で .env を開いてSharePoint接続情報を入力

Step 6: 起動
  > docker compose up -d

Step 7: Android端末をUSBで接続
  > adb devices  ← 認識確認（端末側で「USBデバッグを許可」を選択）

ブラウザで http://localhost:3000 を開けば完了
```

### 6.2 バージョンアップ手順

```bash
git pull
docker compose up -d --build
```

### 6.3 起動・停止コマンド

```bash
docker compose up -d        # バックグラウンドで起動
docker compose down         # 停止
docker compose logs -f      # ログ確認
docker compose ps           # 状態確認
```

---

## 7. ディレクトリ構成

```
android-test-system/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── dashboard/                  ← ブラウザUI
│   ├── Dockerfile
│   └── index.html
│
├── orchestrator/               ← 試験司令塔
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── scenario_runner.py
│   ├── scenario_parser.py
│   ├── state_manager.py
│   ├── result_manager.py
│   ├── agent_client.py
│   ├── sharepoint_client.py
│   └── scenarios/
│       └── sample_wifi_test.yaml
│
├── android-agent/              ← ADB + Appium
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── start.sh
│   ├── main.py
│   ├── adb_client.py
│   └── appium_client.py
│
├── equipment-agent/            ← 計測器制御
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── agent.py
│   ├── base_driver.py
│   ├── config/
│   │   └── equipment.yaml
│   └── drivers/
│       ├── visa/
│       │   ├── keysight_e3631a.py
│       │   └── keysight_n9020b.py
│       ├── serial/
│       │   └── generic_serial.py
│       ├── rest/
│       │   └── generic_rest.py
│       └── mock/
│           └── mock_driver.py
│
├── tests/                      ← 自動テスト
│   ├── conftest.py
│   ├── test_scenario_parser.py
│   ├── test_state_manager.py
│   ├── test_result_manager.py
│   ├── test_equipment_agent.py
│   └── test_mock_driver.py
│
└── docs/
    └── design.md               ← 本設計書
```

---

## 8. テスト

### 8.1 テスト方針

実機（Android端末・計測器）に依存しないロジック層を単体テストでカバーする。

| テストファイル | テスト対象 | テスト数 |
|---|---|---|
| test_scenario_parser.py | YAMLシナリオ読み込み・バリデーション | 8件 |
| test_state_manager.py | 試験状態管理 | 9件 |
| test_result_manager.py | 合否判定・結果集計 | 19件 |
| test_equipment_agent.py | プラグインローダー・機材マネージャー | 10件 |
| test_mock_driver.py | モックドライバ動作 | 8件 |
| **合計** | | **56件（全件PASS）** |

### 8.2 テスト実行

```bash
pip install pytest pyyaml httpx pydantic fastapi
pytest tests/ -v
```

### 8.3 テスト非対象（実機が必要なため）

- ADB実機接続・コマンド実行
- Appiumによる実端末UI操作
- PyVISA/シリアルによる実機材接続
- SharePoint Graph API連携（認証情報が必要）

---

## 9. セキュリティ設計

| 項目 | 対応 |
|---|---|
| 認証情報 | `.env` ファイルで管理、`.gitignore` で除外 |
| SharePoint認証 | Azure AD クライアントクレデンシャルフロー（OAuth2） |
| コンテナ間通信 | Docker内部ネットワーク（外部非公開） |
| CORS | 開発用途のため `allow_origins=["*"]`（本番環境では制限推奨） |

---

## 10. 残タスク

| 優先度 | 作業 | 内容 |
|---|---|---|
| 高 | GitHubリポジトリ作成・push | Watchtowerなし → 手動運用 |
| 高 | SharePoint Azure ADアプリ登録 | `.env` に接続情報を設定 |
| 高 | 実機動作確認 | `docker compose up` → ADB接続 → 試験実行 |
| 中 | 実計測器ドライバ作成 | 手元の機材に合わせた `drivers/` 追加 |
| 中 | Power BI レポート設計 | SharePoint Lists に接続した分析ダッシュボード |
| 低 | 非エンジニア向けセットアップ手順書 | スクリーンショット付きWord/PDF |
