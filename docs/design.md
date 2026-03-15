# Android 自動試験システム 詳細設計書

| 項目 | 内容 |
|---|---|
| ドキュメント番号 | AND-TEST-DESIGN-001 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-15 |
| 対象リポジトリ | android-test-system |
| ステータス | 実装済み・テスト済み |

---

## 目次

1. [システム概要](#1-システム概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [コンポーネント詳細設計](#3-コンポーネント詳細設計)
4. [シーケンス図](#4-シーケンス図)
5. [状態遷移設計](#5-状態遷移設計)
6. [API仕様](#6-api仕様)
7. [試験シナリオ定義（YAML）](#7-試験シナリオ定義yaml)
8. [Equipment Agent プラグイン設計](#8-equipment-agent-プラグイン設計)
9. [SharePoint連携設計](#9-sharepoint連携設計)
10. [データ設計](#10-データ設計)
11. [Docker構成設計](#11-docker構成設計)
12. [セキュリティ設計](#12-セキュリティ設計)
13. [テスト設計](#13-テスト設計)
14. [エラーハンドリング設計](#14-エラーハンドリング設計)
15. [セットアップ手順](#15-セットアップ手順)
16. [運用手順](#16-運用手順)
17. [トラブルシューティング](#17-トラブルシューティング)
18. [残タスク・制約事項](#18-残タスク制約事項)

---

## 1. システム概要

### 1.1 目的

Android OS 搭載端末（DUT: Device Under Test）と各種試験機材を自動制御し、試験手順を標準化・自動化するシステムです。ブラウザから操作でき、試験結果はクラウドで一元管理します。

### 1.2 要件一覧

| # | 要件 | 対応方法 | 実装状態 |
|---|---|---|---|
| R01 | Android端末の自動試験 | ADB + Appium (UiAutomator2) | ✅ 実装済 |
| R02 | ブラウザからコントロール | Web Dashboard (localhost:3000) | ✅ 実装済 |
| R03 | 様々な試験機材の制御 | Equipment Agent プラグイン式 | ✅ 実装済 |
| R04 | 様々なPCで利用可能 | Docker Compose による環境統一 | ✅ 実装済 |
| R05 | 簡単な環境構築 | `docker compose up` 一発起動 | ✅ 実装済 |
| R06 | バージョンアップ容易性 | `git pull && docker compose up --build` | ✅ 手動運用 |
| R07 | クラウド結果管理 | SharePoint Lists + Power BI | ✅ 実装済 |
| R08 | 属人化防止 | YAML試験定義・Python標準構成 | ✅ 実装済 |

### 1.3 システムスコープ

```
【スコープ内】
  ・試験シナリオの定義・実行・管理
  ・Android端末のUI操作・状態確認（Appium）
  ・Android端末の低レベル制御（ADB）
  ・試験機材の制御（電源・計測器等）
  ・試験結果のローカル保存・SharePoint送信
  ・ブラウザによるリアルタイム監視

【スコープ外】
  ・試験機材のドライバ開発（枠組みのみ提供）
  ・Power BI レポートの設計・構築
  ・Android端末のOSバージョン管理
  ・ネットワーク環境の構築
```

---

## 2. システムアーキテクチャ

### 2.1 全体構成図

```
┌────────────────────────────────────────────────────────────────────┐
│  ホストPC（Windows / Mac / Linux）                                   │
│                                                                    │
│  試験員                                                             │
│   │ ブラウザ (Chrome / Edge 等)                                    │
│   └──► http://localhost:3000                                       │
│              │                                                     │
│  ┌───────────┼──────────────────────────────────────────────────┐ │
│  │  Docker Compose  (test-system-network)                        │ │
│  │           │                                                   │ │
│  │   ┌───────▼──────────────────────────────────┐               │ │
│  │   │  ① Dashboard (nginx) :3000               │               │ │
│  │   │    index.html                             │               │ │
│  │   │    REST GET/POST → :8000                  │               │ │
│  │   │    WebSocket ws://localhost:8000/ws/log   │               │ │
│  │   └───────────────────┬──────────────────────┘               │ │
│  │                       │ HTTP                                  │ │
│  │   ┌───────────────────▼──────────────────────┐               │ │
│  │   │  ② Orchestrator (FastAPI) :8000           │               │ │
│  │   │    main.py         ← REST + WebSocket      │               │ │
│  │   │    scenario_runner.py ← 試験実行エンジン   │               │ │
│  │   │    scenario_parser.py ← YAML読み込み      │               │ │
│  │   │    state_manager.py   ← 状態管理          │               │ │
│  │   │    result_manager.py  ← 結果集計・保存    │               │ │
│  │   │    agent_client.py    ← Agent HTTP通信    │               │ │
│  │   │    sharepoint_client.py ← Graph API      │               │ │
│  │   └──────────┬───────────────────┬────────────┘               │ │
│  │              │ HTTP              │ HTTP                        │ │
│  │   ┌──────────▼──────┐  ┌────────▼──────────────────────┐     │ │
│  │   │ ③ Android Agent │  │ ④ Equipment Agent              │     │ │
│  │   │   :5000 FastAPI │  │   :5001 FastAPI               │     │ │
│  │   │   :4723 Appium  │  │   agent.py（プラグインLoader）│     │ │
│  │   │   adb_client.py │  │   base_driver.py（I/F）        │     │ │
│  │   │   appium_client │  │   drivers/visa/               │     │ │
│  │   └──────┬──────────┘  │   drivers/serial/             │     │ │
│  └──────────┼─────────────│   drivers/rest/               │─────┘ │
│             │ TCP:5037    │   drivers/mock/               │       │
│  ADB Server ◄─────────   └───────────────┬───────────────┘       │
│  （ホスト常駐）                           │ VISA/Serial/REST/LAN   │
│             │ USB or Wi-Fi              試験機材                   │
│        Android端末 (DUT)               （電源・計測器等）           │
└────────────────────────────────────────────────────────────────────┘
                    │ HTTPS  Microsoft Graph API
                    ▼
         ┌──────────────────────────┐
         │  ☁️  Microsoft 365        │
         │  SharePoint Lists        │
         │  （TestResults リスト）   │
         │         │                │
         │         ▼                │
         │  Power BI ダッシュボード  │
         └──────────────────────────┘
```

### 2.2 コンポーネント一覧

| # | コンポーネント | 技術スタック | ポート | 役割 |
|---|---|---|---|---|
| ① | Web Dashboard | HTML/JS (Vanilla) + nginx | 3000 | 試験操作UI・リアルタイムログ・結果閲覧 |
| ② | Orchestrator | Python 3.11 + FastAPI + asyncio | 8000 | 試験司令塔・シナリオ実行・結果管理 |
| ③ | Android Agent | Python 3.11 + FastAPI + ADB + Appium | 5000 / 4723 | Android端末のUI操作・低レベル制御 |
| ④ | Equipment Agent | Python 3.11 + FastAPI + PyVISA/pyserial | 5001 | 計測器・試験機材制御（プラグイン式） |

### 2.3 ADB接続方式の選定理由

Dockerコンテナから Android 端末を制御するには以下3方式があります。

| 方式 | Windows対応 | ホストへの追加インストール | 採用 |
|---|---|---|---|
| ① Docker内USB直接パススルー | ❌ Linux限定 | なし | ✗ |
| **② ホストADB Server + TCP経由** | **✅** | **ADBのみ** | **✅ 採用** |
| ③ Wi-Fi ADB（Android 11以上） | ✅ | なし | △ 補助的に利用可 |

**採用方式②の仕組み:**
```
Android端末 ──USB──► ホストのADB Server（TCP:5037 でリッスン）
                              ▲
                              │ TCP接続（host.docker.internal:5037）
                    Docker: Android Agent コンテナ
```

---

## 3. コンポーネント詳細設計

### 3.1 Orchestrator

#### 3.1.1 モジュール構成

```
orchestrator/
├── main.py               # FastAPI app / WebSocket / エンドポイント定義
├── scenario_runner.py    # YAMLシナリオ実行エンジン（非同期）
├── scenario_parser.py    # YAML読み込み・バリデーション
├── state_manager.py      # 試験状態の一元管理・ログキュー
├── result_manager.py     # 合否判定・結果集計・ローカル保存・SP送信
├── agent_client.py       # Android Agent / Equipment Agent との非同期HTTP通信
├── sharepoint_client.py  # Microsoft Graph API クライアント（OAuth2）
└── scenarios/            # YAMLシナリオファイル置き場
    └── sample_wifi_test.yaml
```

#### 3.1.2 クラス・モジュール関係図

```
main.py
 ├── uses  StateManager（グローバルシングルトン）
 └── uses  ScenarioRunner
              ├── uses  ScenarioParser.load()
              ├── uses  AndroidAgentClient
              ├── uses  EquipmentAgentClient
              └── uses  ResultManager
                          └── uses  SharePointClient
```

#### 3.1.3 ScenarioRunner 実行フロー（詳細）

```
ScenarioRunner.run(scenario_name, device_id)
        │
        ├─ ScenarioParser.load("scenarios/{name}.yaml")
        │      └─ バリデーション失敗 → state.set_error() → return
        │
        ├─ state.set_running(scenario_name, device_id)
        │
        ├─ for step in scenario["steps"]:
        │      │
        │      ├─ state.stop_requested() == True → break（中断）
        │      │
        │      ├─ state.set_step({id, description})
        │      │
        │      ├─ _execute_step(step, device_id)
        │      │      │
        │      │      ├─ action == "adb"
        │      │      │    └─ AndroidAgentClient.adb_command(device_id, command)
        │      │      │         → 応答を evaluate(expect, response) で判定
        │      │      │
        │      │      ├─ action == "tap"
        │      │      │    └─ AndroidAgentClient.tap(device_id, locator_type, locator_value)
        │      │      │
        │      │      ├─ action == "input_text"
        │      │      │    └─ AndroidAgentClient.input_text(...)
        │      │      │
        │      │      ├─ action == "assert_text"
        │      │      │    └─ AndroidAgentClient.get_text(...)
        │      │      │         → evaluate(expect, text) で判定
        │      │      │
        │      │      ├─ action == "assert_exists"
        │      │      │    └─ AndroidAgentClient.assert_exists(...) → bool
        │      │      │
        │      │      ├─ action == "equipment_measure"
        │      │      │    └─ EquipmentAgentClient.measure(device, parameter)
        │      │      │         → evaluate_numeric(expect, value) で判定
        │      │      │
        │      │      ├─ action == "equipment_method"
        │      │      │    └─ EquipmentAgentClient.call_method(device, method, args)
        │      │      │
        │      │      ├─ action == "equipment_command"
        │      │      │    └─ EquipmentAgentClient.send_command(device, command)
        │      │      │
        │      │      ├─ action == "screenshot"
        │      │      │    └─ AndroidAgentClient.screenshot(device_id, save_path)
        │      │      │
        │      │      └─ action == "wait"
        │      │           └─ asyncio.sleep(seconds)
        │      │
        │      ├─ pass == False && on_fail == "stop" → break
        │      └─ step_results に結果を追記
        │
        ├─ ResultManager.summarize(scenario, device_id, step_results)
        ├─ ResultManager.save_and_send(summary)
        │      ├─ results/*.json にローカル保存
        │      └─ SharePointClient.send_result(summary)（失敗しても試験はエラーにしない）
        │
        └─ state.set_finished(summary)
```

#### 3.1.4 StateManager 管理データ

```python
class StateManager:
    status: str          # "idle" | "running" | "finished" | "error"
    current_scenario: str | None    # 実行中のシナリオ名
    current_device: str | None      # 実行中の端末ID
    start_time: datetime | None     # 試験開始時刻
    current_step: dict | None       # 現在実行中のステップ {id, description}
    _stop_requested: bool           # 中断フラグ
    log_queue: asyncio.Queue        # WebSocket送信用ログキュー
    _results: list[dict]            # 直近100件の試験結果
```

### 3.2 Android Agent

#### 3.2.1 モジュール構成

```
android-agent/
├── main.py           # FastAPI エントリーポイント・エンドポイント定義
├── adb_client.py     # ADB コマンドラッパー（subprocess経由）
├── appium_client.py  # Appium WebDriver クライアント（セッション管理）
└── start.sh          # Appium Server + FastAPI 同時起動スクリプト
```

#### 3.2.2 ADB/Appium 役割分担

| 操作カテゴリ | 操作内容 | 担当 | APIパス |
|---|---|---|---|
| 端末情報 | 機種名・OSバージョン取得 | ADB | `/adb/command` |
| 端末制御 | 再起動 | ADB | `/adb/reboot` |
| 端末制御 | Wi-Fi ON/OFF | ADB | `/adb/command` |
| 端末制御 | 機内モード ON/OFF | ADB | `/adb/command` |
| アプリ | APKインストール | ADB | `/adb/command` |
| ログ | logcat収集 | ADB | `/adb/logcat` |
| 画面 | スクリーンショット | ADB | `/adb/screenshot` |
| UI操作 | 要素タップ | Appium | `/appium/tap` |
| UI操作 | テキスト入力 | Appium | `/appium/input_text` |
| UI確認 | テキスト取得 | Appium | `/appium/get_text` |
| UI確認 | 要素存在確認 | Appium | `/appium/exists` |
| セッション | Appiumセッション開始 | Appium | `/appium/session/start` |
| セッション | Appiumセッション終了 | Appium | `/appium/session/close` |

#### 3.2.3 Appiumセッション管理

```python
# appium_client.py
_sessions: dict[str, WebDriver] = {}  # 端末ID → ドライバ のキャッシュ

# セッションの再利用ロジック
def _get_driver(device_id):
    if device_id in _sessions:
        return _sessions[device_id]   # 既存セッションを再利用
    # → 新規セッション作成・キャッシュ
```

Appium capabilities 設定:
```python
caps = {
    "platformName":   "Android",
    "udid":           device_id,        # 端末固有ID
    "automationName": "UiAutomator2",   # Android用ドライバ
    "adbHost":        "host.docker.internal",  # ホストのADB Server
    "adbPort":        5037,
    "noReset":        True,             # テスト後にアプリ状態をリセットしない
}
```

#### 3.2.4 起動シーケンス（start.sh）

```
コンテナ起動
    │
    ├─ appium --address 0.0.0.0 --port 4723 --base-path / &
    │      （バックグラウンドで Appium Server を起動）
    │
    └─ uvicorn main:app --host 0.0.0.0 --port 5000
           （フォアグラウンドで FastAPI を起動）
```

### 3.3 Equipment Agent

#### 3.3.1 モジュール構成

```
equipment-agent/
├── main.py          # FastAPI エントリーポイント・エンドポイント定義
├── agent.py         # EquipmentAgent: YAMLロード・プラグイン管理
├── base_driver.py   # BaseDriver: 全ドライバの抽象基底クラス
├── config/
│   └── equipment.yaml   # 接続機材設定（PCごとに編集）
└── drivers/
    ├── visa/            # VISA（GPIB/USB/LAN）通信
    │   ├── keysight_e3631a.py   # E3631A 三出力直流電源
    │   └── keysight_n9020b.py   # N9020B MXA スペクトラムアナライザ
    ├── serial/          # RS-232C / USB-Serial
    │   └── generic_serial.py    # 汎用シリアル通信ドライバ
    ├── rest/            # REST API
    │   └── generic_rest.py      # 汎用 REST API ドライバ
    └── mock/            # テスト・動作確認用
        └── mock_driver.py       # モックドライバ（ノイズ付き乱数値を返す）
```

#### 3.3.2 プラグインローディング仕組み

```python
# EquipmentAgent._load_config() の動作
#
# equipment.yaml:
#   instruments:
#     power_supply:
#       driver: visa.keysight_e3631a   ← "visa.keysight_e3631a"
#
# → importlib.import_module("drivers.visa.keysight_e3631a")
#   → module.Driver(name="power_supply", config={...})
#   → self._drivers["power_supply"] = <Driver instance>
```

ドライバのロード・エラー時の挙動:
- ロード失敗 → エラーログを出力してスキップ（他の機材への影響なし）
- 存在しない設定ファイル → 警告ログを出力して空マネージャーで起動
- 未知の機材名 → `KeyError` を送出（HTTP 404 として返る）

#### 3.3.3 BaseDriver インターフェース

```python
@dataclass
class MeasureResult:
    value: float      # 測定値
    unit:  str        # 単位（"V", "A", "dBm" 等）
    raw:   str = ""   # 生レスポンス文字列
    pass_: bool = True

class BaseDriver(ABC):
    # ── 必須実装（4メソッド）────────────────────────────────
    @abstractmethod
    def connect(self) -> None:
        """機材に接続する"""

    @abstractmethod
    def disconnect(self) -> None:
        """接続を切断する"""

    @abstractmethod
    def send_command(self, command: str) -> str:
        """生コマンド（SCPI等）を送信して応答を返す"""

    @abstractmethod
    def measure(self, parameter: str) -> MeasureResult:
        """指定パラメータを測定して結果を返す"""

    # ── オーバーライド任意（デフォルト実装あり）─────────────
    def reset(self) -> None:
        self.send_command("*RST")     # SCPI標準リセット

    def get_id(self) -> str:
        return self.send_command("*IDN?")   # SCPI標準ID取得

    def get_status(self) -> dict:
        return {"name": self.name, "connected": self._connected, ...}
```

#### 3.3.4 通信方式別ドライバ比較

| 通信方式 | ドライバ | 対象機材例 | 必要ライブラリ | 設定パラメータ |
|---|---|---|---|---|
| VISA (GPIB) | visa/*.py | Keysight電源・計測器 | pyvisa | address: "GPIB0::5::INSTR" |
| VISA (LAN) | visa/*.py | LAN対応計測器 | pyvisa | address: "TCPIP0::192.168.1.x::inst0::INSTR" |
| Serial | serial/generic_serial.py | RS-232C機材 | pyserial | port, baudrate, measure_commands |
| REST API | rest/generic_rest.py | HTTPで制御する機材 | requests | base_url, measure_endpoints |
| Mock | mock/mock_driver.py | テスト・デモ用 | なし | mock_values |

### 3.4 Web Dashboard

#### 3.4.1 画面構成

```
┌────────────────────────────────────────────────────────────┐
│ HEADER: [●ステータス] Android 自動試験システム    [経過時間] │
├─────────────────┬──────────────────────────────────────────┤
│  左パネル        │  右パネル（タブ）                        │
│                 │  [リアルタイムログ] [ステップ進捗] [結果]  │
│ ■ 試験シナリオ  │                                          │
│  [セレクトBox]  │  ログタブ:                               │
│                 │   10:23:01 === 試験開始: Wi-Fi試験 ===    │
│ ■ Android端末   │   10:23:02 [Step 1] 端末情報取得         │
│  [セレクトBox]  │   10:23:02   → ✅ PASS                   │
│  ● device-001  │   10:23:03 [Step 2] スクリーンショット     │
│                 │   10:23:04   → ✅ PASS                   │
│ [▶ 試験開始]    │                                          │
│ [⏹ 試験中断]    │  ステップタブ:                           │
│                 │   #1 端末情報取得       ✅               │
│ ■ 結果サマリー  │   #2 スクリーンショット ✅               │
│  総: 10 PASS: 9 │   #3 Wi-FiをOFFにする  ▶ ←現在         │
│  FAIL: 1  90%   │   #4 待機              —                │
│                 │                                          │
│ ■ 計測器        │  結果タブ:                               │
│  ● mock_power  │   日時         シナリオ  端末  結果       │
│  ● mock_rf     │   2026-03-15   wifi_test dev-1 ✅PASS    │
└─────────────────┴──────────────────────────────────────────┘
```

#### 3.4.2 フロントエンド通信設計

```
Dashboard (index.html)
    │
    ├─ 初期ロード (DOMContentLoaded)
    │    ├─ GET  /scenarios      → シナリオセレクト
    │    ├─ GET  /devices        → 端末セレクト
    │    ├─ GET  /instruments    → 計測器リスト
    │    └─ GET  /results        → 結果テーブル
    │
    ├─ 試験開始 ボタン押下
    │    └─ POST /test/start {scenario_name, device_id}
    │
    ├─ 試験中断 ボタン押下
    │    └─ POST /test/stop
    │
    ├─ ステータスポーリング（3秒間隔）
    │    └─ GET  /test/status    → ステータスドット・ボタン制御
    │
    └─ WebSocket 常時接続
         └─ ws://localhost:8000/ws/log
              → ログエントリを受信しリアルタイム表示
```

---

## 4. シーケンス図

### 4.1 試験実行シーケンス（正常系）

```
試験員       Dashboard      Orchestrator   Android Agent  Equip Agent   SharePoint
  │              │               │               │              │            │
  │ [試験開始]   │               │               │              │            │
  ├────────────►│               │               │              │            │
  │  POST /test/start           │               │              │            │
  │             ├──────────────►│               │              │            │
  │             │   202 started │               │              │            │
  │             │◄──────────────┤               │              │            │
  │             │               │               │              │            │
  │             │ ← WebSocket接続確立 ──────────────────────────────────── │
  │             │               │               │              │            │
  │             │               │ YAML読み込み   │              │            │
  │             │               ├──────────────►│              │            │
  │             │               │  Step1: ADB   │              │            │
  │             │               │  POST /adb/command           │            │
  │             │               ├──────────────►│              │            │
  │             │               │  {stdout}     │              │            │
  │             │               │◄──────────────┤              │            │
  │             │               │               │              │            │
  │  ログ送信  ◄─────────────── WebSocket                       │            │
  │             │               │               │              │            │
  │             │               │  Step5: equipment_measure    │            │
  │             │               │  GET /instruments/mock_power/measure/voltage_ch1
  │             │               ├──────────────────────────────►            │
  │             │               │  {value, unit}               │            │
  │             │               │◄─────────────────────────────┤            │
  │             │               │               │              │            │
  │             │               │  全ステップ完了              │            │
  │             │               │  ResultManager.save_and_send()            │
  │             │               ├────────────────────────────────────────►  │
  │             │               │  Graph API: POST /lists/{id}/items        │
  │             │               │◄────────────────────────────────────────  │
  │  ログ送信  ◄─────────────── WebSocket (=== 試験完了 ===)               │
  │             │               │               │              │            │
```

### 4.2 試験中断シーケンス

```
試験員       Dashboard      Orchestrator
  │              │               │
  │ [試験中断]   │               │
  ├────────────►│               │
  │  POST /test/stop             │
  │             ├──────────────►│
  │             │   200 ok      │  state._stop_requested = True
  │             │◄──────────────┤
  │             │               │
  │             │               │  次ステップ実行前に stop_requested() チェック
  │             │               │  ↓ True の場合
  │             │               │  break → summarize → save_and_send
  │ ログ受信   ◄─────────────── WebSocket ("⏹ 試験を中断しました")
```

### 4.3 SharePoint 認証・送信シーケンス

```
Orchestrator         Azure AD             SharePoint Graph API
    │                    │                       │
    │  POST /token        │                       │
    │  client_credentials │                       │
    ├───────────────────►│                       │
    │  access_token       │                       │
    │◄───────────────────┤                       │
    │  ※トークンをキャッシュ（有効期限-60秒まで再利用）
    │                    │                       │
    │  GET /sites/{host}:/{path}                 │
    ├───────────────────────────────────────────►│
    │  site_id           │                       │
    │◄───────────────────────────────────────────┤
    │                    │                       │
    │  GET /sites/{id}/lists/TestResults         │
    ├───────────────────────────────────────────►│
    │  list_id（404の場合は自動作成）              │
    │◄───────────────────────────────────────────┤
    │                    │                       │
    │  POST /sites/{id}/lists/{id}/items         │
    │  ← 試験結果1行                              │
    ├───────────────────────────────────────────►│
    │  201 Created        │                       │
    │◄───────────────────────────────────────────┤
```

---

## 5. 状態遷移設計

### 5.1 試験状態機械

```
                  ┌──────────────────────────────────────────┐
                  │                                          │
        起動時     ▼    POST /test/start                     │
       ────────► idle ──────────────────────────► running   │
                  ▲                                  │       │
                  │                                  │ POST /test/stop
                  │  set_finished()                  │ ↓
                  │◄─────────────────────────────── (中断フラグセット)
                  │                                  │
                  │  全ステップ完了                    │
                  │◄──────────────────────────────────┘
                  │
                  │  ※ エラー発生時
                  └──────────────────► error ──── POST /test/start ──►（再起動）
```

| 状態 | 説明 | 遷移条件 |
|---|---|---|
| `idle` | 待機中・試験受付可能 | 初期状態 / 試験完了後 / 中断後 |
| `running` | 試験実行中 | POST /test/start 受信後 |
| `error` | エラー停止 | シナリオ読み込み失敗等 |

### 5.2 ステップ実行結果

| pass | error | on_fail | 次の動作 |
|---|---|---|---|
| True | — | — | 次のステップへ |
| False | — | — | 次のステップへ（FAILを記録して継続） |
| False | — | "stop" | 試験を中断 |
| — | Exception | — | FAILを記録して次へ（on_fail: stop があれば中断） |

---

## 6. API仕様

### 6.1 Orchestrator API (`:8000`)

#### `GET /scenarios` — シナリオ一覧

**Response:**
```json
[
  {
    "name": "sample_wifi_test",
    "display_name": "Wi-Fi接続試験",
    "description": "Wi-FiのON/OFF切り替えと接続状態の確認",
    "version": "1.0",
    "step_count": 10
  }
]
```

#### `POST /test/start` — 試験開始

**Request:**
```json
{ "scenario_name": "sample_wifi_test", "device_id": "emulator-5554" }
```
**Response (200):**
```json
{ "status": "started", "scenario": "sample_wifi_test", "device_id": "emulator-5554" }
```
**Response (409):** 試験が既に実行中
```json
{ "detail": "試験が既に実行中です" }
```

#### `GET /test/status` — 試験状態

**Response:**
```json
{
  "status": "running",
  "scenario": "sample_wifi_test",
  "device": "emulator-5554",
  "start_time": "2026-03-15T10:23:01.234567",
  "elapsed": "0:01:23",
  "current_step": { "id": 5, "description": "電源電圧を測定（モック）" }
}
```

#### `GET /results` — 結果履歴

**Query:** `?limit=20`

**Response:**
```json
[
  {
    "scenario": "sample_wifi_test",
    "device_id": "emulator-5554",
    "test_site": "osaka-lab",
    "timestamp": "2026-03-15T10:25:01.234567",
    "total": 10,
    "pass_count": 9,
    "fail_count": 1,
    "result": "FAIL",
    "steps": [
      { "step_id": 1, "action": "adb", "pass": true, "response": "Pixel 6" },
      { "step_id": 5, "action": "equipment_measure", "pass": false,
        "value": 2.8, "unit": "mock", "expected": {"between": [3.0, 4.5]} }
    ]
  }
]
```

#### `WebSocket /ws/log` — リアルタイムログ

**送信メッセージ（JSON）:**
```json
{ "timestamp": "10:23:02", "level": "INFO", "message": "[Step 1] 端末情報を取得する" }
{ "timestamp": "10:23:02", "level": "INFO", "message": "  → ✅ PASS" }
{ "timestamp": "10:23:05", "level": "ERROR", "message": "  → ⚠️ ERROR: 接続タイムアウト" }
```

### 6.2 Equipment Agent API (`:5001`)

#### `GET /instruments/{name}/measure/{parameter}`

**Response:**
```json
{ "value": 3.712, "unit": "V", "raw": "3.712E+00" }
```

#### `POST /instruments/{name}/method`

**Request:**
```json
{ "method": "set_voltage", "kwargs": { "channel": 1, "voltage": 3.7 } }
```
**Response:**
```json
{ "result": null }
```

### 6.3 Android Agent API (`:5000`)

#### `POST /adb/command`

**Request:**
```json
{ "device_id": "emulator-5554", "command": "shell getprop ro.product.model" }
```
**Response:**
```json
{ "stdout": "sdk_gphone64_x86_64", "stderr": "", "returncode": 0 }
```

#### `POST /appium/tap`

**Request:**
```json
{ "device_id": "emulator-5554", "locator_type": "text", "locator_value": "設定" }
```
**Response:**
```json
{ "status": "tapped" }
```

---

## 7. 試験シナリオ定義（YAML）

### 7.1 完全な構文リファレンス

```yaml
name: 試験名称            # 必須・表示名
version: "1.0"            # 任意・バージョン管理用
description: 試験の説明   # 任意・一覧表示に使用

steps:
  # ── ADB コマンド ──────────────────────────────────────────
  - id: 1
    description: 端末情報を取得する
    action: adb
    command: shell getprop ro.product.model
    expect:                # 任意。なければ常にPASS
      contains: "Pixel"   # レスポンスに"Pixel"を含む
    on_fail: stop          # 任意。FAILしたら試験中断

  # ── Appium タップ ─────────────────────────────────────────
  - id: 2
    description: 設定ボタンをタップする
    action: tap
    locator_type: text     # id / text / xpath / class / desc
    locator_value: "設定"

  # ── テキスト入力 ─────────────────────────────────────────
  - id: 3
    description: 検索ボックスに文字を入力する
    action: input_text
    locator_type: id
    locator_value: com.example:id/search_input
    text: "テスト入力文字"

  # ── テキスト確認 ─────────────────────────────────────────
  - id: 4
    description: ステータスが"接続済み"であることを確認する
    action: assert_text
    locator_type: id
    locator_value: com.example:id/status_label
    expect:
      equals: "接続済み"

  # ── 要素存在確認 ─────────────────────────────────────────
  - id: 5
    description: エラーダイアログが表示されていないことを確認
    action: assert_exists
    locator_type: id
    locator_value: com.example:id/error_dialog
    # existsがFalseならFAIL（要素が存在することを期待する場合に使用）

  # ── 計測器 測定 ───────────────────────────────────────────
  - id: 6
    description: 電源電圧を測定する
    action: equipment_measure
    device: power_supply   # equipment.yaml の機材名
    parameter: voltage_ch1 # ドライバが対応するパラメータ名
    expect:
      between: [3.5, 4.2]  # 3.5V ≤ value ≤ 4.2V でPASS
    on_fail: stop

  # ── 計測器 メソッド呼び出し ──────────────────────────────
  - id: 7
    description: 電源電圧を3.7Vに設定する
    action: equipment_method
    device: power_supply
    method: set_voltage    # ドライバの固有メソッド名
    args:
      channel: 1
      voltage: 3.7

  # ── 計測器 生コマンド ────────────────────────────────────
  - id: 8
    description: スペアナの中心周波数を設定する
    action: equipment_command
    device: spectrum_analyzer
    command: ":SENS:FREQ:CENT 2400000000"
    # expect は任意

  # ── スクリーンショット ────────────────────────────────────
  - id: 9
    description: 試験結果画面をスクリーンショット保存
    action: screenshot
    save_path: /app/results/step9_result.png

  # ── 待機 ─────────────────────────────────────────────────
  - id: 10
    description: 5秒待機（接続安定待ち）
    action: wait
    seconds: 5
```

### 7.2 expect 合否判定ロジック

```
【文字列判定 (evaluate)】
  expect: {contains: "X"}      → "X" in response
  expect: {equals: "Y"}        → response.strip() == "Y"
  expect: {not_contains: "Z"}  → "Z" not in response
  expect: なし                  → 常に PASS

【数値判定 (evaluate_numeric)】
  expect: {greater_than: N}    → value > N
  expect: {less_than: N}       → value < N
  expect: {between: [lo, hi]}  → lo <= value <= hi（境界値含む）
  expect: {equals: N}          → |value - N| < 0.001（デフォルト許容誤差）
  expect: {equals: N, tolerance: T} → |value - N| < T
  expect: なし                  → 常に PASS
```

---

## 8. Equipment Agent プラグイン設計

### 8.1 新規ドライバ作成手順

**Step 1:** `drivers/<通信方式>/<機材名>.py` を作成

```python
# drivers/visa/my_new_instrument.py
import sys; sys.path.insert(0, "/app")
from base_driver import BaseDriver, MeasureResult

class Driver(BaseDriver):
    """
    クラス名は必ず "Driver" とすること（EquipmentAgent がこの名前でロードする）
    """

    def connect(self) -> None:
        # 機材への接続処理
        # self.config["address"] 等で equipment.yaml の設定値を参照できる
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def send_command(self, command: str) -> str:
        # コマンド送信処理
        # "?" を含む場合はクエリ（応答を返す）、含まない場合は設定コマンド
        return ""

    def measure(self, parameter: str) -> MeasureResult:
        # parameter に応じた測定処理
        # 未対応パラメータは ValueError を送出すること
        value = 0.0
        return MeasureResult(value=value, unit="V", raw=str(value))

    # ─── 機材固有メソッド（任意）───────────────────────────
    def set_output(self, voltage: float) -> None:
        self.send_command(f"VOLT {voltage:.4f}")
```

**Step 2:** `config/equipment.yaml` にエントリ追記

```yaml
instruments:
  my_new_instrument:
    driver: visa.my_new_instrument   # drivers/ 以下のパス（.py 不要）
    connection: visa
    address: "GPIB0::10::INSTR"
    description: "新規追加機材の説明"
    # ドライバが参照する任意の設定値を自由に追加可能
    timeout_ms: 5000
```

**Step 3:** コンテナ再起動

```bash
docker compose restart equipment-agent
```

**コアコードへの変更は不要です。**

### 8.2 通信方式別 config サンプル

```yaml
# ── VISA (GPIB) ─────────────────────────────────────────
power_supply_gpib:
  driver: visa.keysight_e3631a
  connection: visa
  address: "GPIB0::5::INSTR"
  timeout_ms: 5000

# ── VISA (LAN) ───────────────────────────────────────────
spectrum_analyzer_lan:
  driver: visa.keysight_n9020b
  connection: visa
  address: "TCPIP0::192.168.1.20::inst0::INSTR"
  timeout_ms: 10000

# ── シリアル通信 ─────────────────────────────────────────
serial_meter:
  driver: serial.generic_serial
  connection: serial
  port: "COM3"           # Linux: "/dev/ttyUSB0"
  baudrate: 9600
  timeout: 2
  terminator: "\r\n"
  measure_commands:
    voltage: "READ:VOLT?"
    temperature: "MEAS:TEMP?"
  units:
    voltage: "V"
    temperature: "degC"

# ── REST API ─────────────────────────────────────────────
web_tester:
  driver: rest.generic_rest
  connection: rest
  base_url: "http://192.168.1.30:8080"
  measure_endpoints:
    rssi: "/measure/rssi"
    power: "/measure/power"
  command_endpoint: "/command"
  value_key: "value"
  unit_key: "unit"

# ── モック（実機なし確認用）─────────────────────────────
mock_device:
  driver: mock.mock_driver
  connection: mock
  mock_values:
    voltage_ch1: 3.7
    current_ch1: 0.5
    peak_power: -30.0
```

---

## 9. SharePoint連携設計

### 9.1 認証方式

OAuth2 クライアントクレデンシャルフロー（アプリケーション権限）

```
Orchestrator
    │  POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
    │  Body: grant_type=client_credentials
    │        client_id={CLIENT_ID}
    │        client_secret={CLIENT_SECRET}
    │        scope=https://graph.microsoft.com/.default
    │
    ▼
Azure AD → アクセストークン（有効期限: 3600秒）
    │
    │  ※ expires_in - 60 秒でキャッシュ失効（次回呼び出し時に自動再取得）
    ▼
Microsoft Graph API（Bearer認証）
```

### 9.2 TestResults リスト自動作成

初回実行時、`TestResults` リストが存在しない場合は自動作成します。

```python
# sharepoint_client.py: _create_list()
columns = [
    {"name": "Scenario",  "text": {}},
    {"name": "DeviceId",  "text": {}},
    {"name": "TestSite",  "text": {}},
    {"name": "Result",    "text": {}},          # "PASS" / "FAIL"
    {"name": "PassCount", "number": {}},
    {"name": "FailCount", "number": {}},
    {"name": "Total",     "number": {}},
    {"name": "Timestamp", "dateTime": {}},
    {"name": "Details",   "text": {"allowMultipleLines": True}},
]
```

### 9.3 Azure AD アプリ登録手順（詳細）

```
1. Azure Portal (https://portal.azure.com) にサインイン

2. [Azure Active Directory] → [アプリの登録] → [新規登録]
   ・名前: android-test-system
   ・サポートされているアカウントの種類:
     「この組織ディレクトリのみのアカウント（シングルテナント）」
   ・リダイレクトURI: 空白でよい（クライアントクレデンシャルフローなので不要）
   → [登録]

3. [証明書とシークレット] → [新しいクライアントシークレット]
   ・説明: android-test-system-secret
   ・有効期限: 24ヶ月（組織ポリシーに従う）
   → [追加] → 生成された「値」をコピー（この画面を閉じると二度と見られない）

4. [APIのアクセス許可] → [アクセス許可の追加]
   → [Microsoft Graph] → [アプリケーションの許可]
   → 「Sites」で検索 → [Sites.ReadWrite.All] にチェック
   → [アクセス許可の追加]
   → [<テナント>に管理者の同意を与えます] → [はい]

5. [概要] で以下の値をコピーして .env に設定:
   ・アプリケーション（クライアント）ID → SHAREPOINT_CLIENT_ID
   ・ディレクトリ（テナント）ID        → SHAREPOINT_TENANT_ID
   ・作成したシークレット値            → SHAREPOINT_CLIENT_SECRET
```

### 9.4 .env 設定例

```env
SHAREPOINT_TENANT_ID=12345678-1234-1234-1234-123456789012
SHAREPOINT_CLIENT_ID=abcdefab-abcd-abcd-abcd-abcdefabcdef
SHAREPOINT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxx~Xxxxx
SHAREPOINT_SITE_URL=https://contoso.sharepoint.com/sites/test
TEST_SITE=osaka-lab
```

---

## 10. データ設計

### 10.1 試験結果ローカルファイル（JSON）

**保存パス:** `results/2026-03-15T10-23-01_sample_wifi_test_emulator-5554.json`

```json
{
  "scenario": "sample_wifi_test",
  "device_id": "emulator-5554",
  "test_site": "osaka-lab",
  "timestamp": "2026-03-15T10:23:01.234567",
  "total": 10,
  "pass_count": 9,
  "fail_count": 1,
  "result": "FAIL",
  "steps": [
    {
      "step_id": 1,
      "action": "adb",
      "pass": true,
      "response": "sdk_gphone64_x86_64"
    },
    {
      "step_id": 5,
      "action": "equipment_measure",
      "pass": false,
      "value": 2.8,
      "unit": "mock",
      "expected": { "between": [3.0, 4.5] }
    },
    {
      "step_id": 6,
      "action": "adb",
      "pass": true,
      "response": "0"
    }
  ]
}
```

### 10.2 環境変数一覧（.env）

| 変数名 | 必須 | 説明 | 例 |
|---|---|---|---|
| SHAREPOINT_SITE_URL | ✅ | SharePoint サイトURL | `https://contoso.sharepoint.com/sites/test` |
| SHAREPOINT_TENANT_ID | ✅ | Azure AD テナントID | UUID形式 |
| SHAREPOINT_CLIENT_ID | ✅ | Azure ADアプリのクライアントID | UUID形式 |
| SHAREPOINT_CLIENT_SECRET | ✅ | クライアントシークレット値 | 文字列 |
| TEST_SITE | — | 試験サイト識別子（結果に付与） | `osaka-lab` |

### 10.3 equipment.yaml スキーマ

```yaml
instruments:               # 必須: 機材定義のマップ
  <機材名>:                # キー: 試験シナリオから参照する名前
    driver: <パス>          # 必須: drivers/ 以下のモジュールパス
    connection: <種別>      # 任意: visa/serial/rest/mock
    description: <説明>    # 任意: 機材の説明
    # 以下はドライバ依存の任意パラメータ
    address: <VISA ADDR>
    port: <シリアルポート>
    baudrate: <ボーレート>
    base_url: <REST URL>
    mock_values: { ... }
```

---

## 11. Docker構成設計

### 11.1 docker-compose.yml 全体

```yaml
version: "3.9"

services:
  dashboard:                        # ① Web UI (nginx)
    build: ./dashboard
    ports: ["3000:3000"]
    depends_on: [orchestrator]
    restart: unless-stopped

  orchestrator:                     # ② 試験司令塔 (FastAPI)
    build: ./orchestrator
    ports: ["8000:8000"]
    volumes:
      - ./orchestrator/scenarios:/app/scenarios  # シナリオをホストから参照
      - ./results:/app/results                   # 結果をホストに保存
    environment:
      - ANDROID_AGENT_URL=http://android-agent:5000
      - EQUIPMENT_AGENT_URL=http://equipment-agent:5001
      - SHAREPOINT_SITE_URL=${SHAREPOINT_SITE_URL}
      - SHAREPOINT_TENANT_ID=${SHAREPOINT_TENANT_ID}
      - SHAREPOINT_CLIENT_ID=${SHAREPOINT_CLIENT_ID}
      - SHAREPOINT_CLIENT_SECRET=${SHAREPOINT_CLIENT_SECRET}
      - TEST_SITE=${TEST_SITE:-default}
    depends_on: [android-agent, equipment-agent]
    restart: unless-stopped

  android-agent:                    # ③ ADB + Appium (FastAPI)
    build: ./android-agent
    ports: ["5000:5000", "4723:4723"]
    environment:
      - ADB_SERVER_HOST=host.docker.internal
      - ADB_SERVER_PORT=5037
    extra_hosts:
      - "host.docker.internal:host-gateway"   # Linux でも動作するよう設定
    restart: unless-stopped

  equipment-agent:                  # ④ 計測器制御 (FastAPI)
    build: ./equipment-agent
    ports: ["5001:5001"]
    volumes:
      - ./equipment-agent/config:/app/config   # equipment.yaml をホストから参照
    restart: unless-stopped

networks:
  default:
    name: test-system-network       # コンテナ間の内部ネットワーク
```

### 11.2 コンテナ間ネットワーク

```
Docker network: test-system-network（bridge）

  dashboard      → orchestrator    HTTP http://orchestrator:8000
  orchestrator   → android-agent   HTTP http://android-agent:5000
  orchestrator   → equipment-agent HTTP http://equipment-agent:5001

  android-agent  → ホストOS         TCP  host.docker.internal:5037（ADB Server）
  equipment-agent→ 計測器            VISA/Serial/REST（ホスト経由）

外部公開ポート（ホスト）:
  :3000  → Dashboard
  :8000  → Orchestrator（ブラウザWebSocket用）
  :5000  → Android Agent（直接アクセス用）
  :5001  → Equipment Agent（直接アクセス用）
  :4723  → Appium Server（デバッグ用）
```

### 11.3 各コンテナの Dockerfile

#### Dashboard
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
RUN sed -i 's/listen\s*80/listen 3000/g' /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

#### Orchestrator / Equipment Agent
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000   # または 5001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Android Agent（マルチステージビルド）
```dockerfile
# Stage 1: Appium インストール
FROM node:20-slim AS appium-base
RUN npm install -g appium@2 && appium driver install uiautomator2

# Stage 2: Python + ADB + Appium コピー
FROM python:3.11-slim
COPY --from=appium-base /usr/local/bin/appium /usr/local/bin/
COPY --from=appium-base /root/.appium /root/.appium
RUN apt-get install -y android-tools-adb
RUN pip install -r requirements.txt
CMD ["/start.sh"]   # Appium をバックグラウンド起動後に FastAPI 起動
```

---

## 12. セキュリティ設計

### 12.1 認証情報の管理

| 情報 | 保存場所 | Git管理 | アクセス |
|---|---|---|---|
| SharePoint接続情報 | `.env` | `.gitignore` で除外 | コンテナ環境変数 |
| `.env.example` | リポジトリ管理 | ✅ 含む | キーの雛形のみ（値なし） |

### 12.2 通信セキュリティ

| 通信路 | プロトコル | 備考 |
|---|---|---|
| ブラウザ ↔ Dashboard | HTTP | ローカルのみ |
| Dashboard ↔ Orchestrator | HTTP / WS | Docker内部ネットワーク |
| Orchestrator ↔ Agents | HTTP | Docker内部ネットワーク |
| Orchestrator ↔ SharePoint | HTTPS | Microsoft Graph API |
| Android Agent ↔ ADB Server | TCP:5037 | ローカルホスト |

### 12.3 既知のセキュリティ上の注意事項

| 項目 | 内容 | 推奨対応 |
|---|---|---|
| CORS | `allow_origins=["*"]` | 本番導入時はオリジン制限 |
| ADB Server | TCP:5037 がローカルで公開 | 同一LAN内のみアクセス可能な環境で使用 |
| USB デバッグ | Android端末のUSBデバッグを有効化が必要 | 試験専用端末に限定 |

---

## 13. テスト設計

### 13.1 テスト戦略

実機（Android端末・計測器・SharePoint）に依存しないロジック層を自動テストでカバーします。

```
テスト対象範囲:
  ✅ scenario_parser.py    - YAML解析・バリデーション
  ✅ state_manager.py      - 状態遷移管理
  ✅ result_manager.py     - 合否判定・集計ロジック
  ✅ equipment/agent.py    - プラグインローダー
  ✅ drivers/mock/*.py     - モックドライバ動作

テスト非対象（実機依存）:
  ✗ ADB実機操作
  ✗ Appium実端末UI操作
  ✗ PyVISA/Serial実機材接続
  ✗ SharePoint Graph API（認証情報依存）
```

### 13.2 テストケース一覧

#### test_scenario_parser.py（8件）

| テストケース | 分類 | 確認内容 |
|---|---|---|
| test_load_valid_scenario | 正常 | 正常なYAMLが読み込め、name・stepsが正しく解析される |
| test_load_all_actions | 正常 | 全10種類のactionを含むシナリオが読み込める |
| test_load_missing_file | 異常 | 存在しないファイル → FileNotFoundError |
| test_load_missing_name | 異常 | nameフィールドなし → ValueError |
| test_load_missing_steps | 異常 | stepsフィールドなし → ValueError |
| test_load_missing_required_key | 異常 | descriptionなし → ValueError |
| test_load_invalid_action | 異常 | 未知のaction → ValueError |
| test_list_scenarios | 正常 | ディレクトリのYAML一覧とstep_countが正しく返る |

#### test_state_manager.py（9件）

| テストケース | 確認内容 |
|---|---|
| test_initial_state | 初期状態が idle・is_running=False |
| test_set_running | set_running() でstatus=running・各フィールドが設定される |
| test_request_stop | request_stop() → stop_requested()==True |
| test_set_finished | set_finished() → idle・results に追加 |
| test_results_limit | 110件登録 → 100件に制限される |
| test_list_results_limit | limit=10 で10件・limit=50 で実件数を返す |
| test_get_status_running | 実行中のstatusに elapsed・current_step が含まれる |
| test_set_error | set_error() → status=error・is_running=False |
| test_log_queue | asyncio.Queue に put した値が get で取り出せる |

#### test_result_manager.py（19件）

| グループ | テストケース数 | 確認内容 |
|---|---|---|
| evaluate（文字列）| 8件 | contains/equals/not_contains の正常・異常系 |
| evaluate_numeric | 8件 | greater_than/less_than/between/equals の正常・異常系・境界値 |
| summarize | 3件 | 全PASS・FAILあり・空リストの集計 |

#### test_equipment_agent.py（10件）

| テストケース | 確認内容 |
|---|---|
| test_load_mock_drivers | モックドライバが2件ロードされる |
| test_connect_mock | connect() → connected=True |
| test_measure_mock | measure() → 許容範囲内の値が返る |
| test_send_command_mock | send_command() → "MOCK"を含むレスポンス |
| test_get_id_mock | get_id() → "MOCK"と機材名を含むID |
| test_call_method_not_found | 存在しないメソッド → AttributeError |
| test_get_unknown_instrument | 未登録機材名 → KeyError |
| test_connect_all | 全機材に接続 → 全件"ok" |
| test_missing_config | 設定ファイルなし → 例外なし・空リスト |
| test_invalid_driver_path | 不正ドライバパス → スキップ・空リスト |

### 13.3 テスト実行コマンド

```bash
# 依存パッケージインストール
pip install pytest pyyaml httpx pydantic fastapi

# 全テスト実行
pytest tests/ -v

# 特定ファイルのみ
pytest tests/test_result_manager.py -v

# カバレッジ計測
pip install pytest-cov
pytest tests/ --cov=orchestrator --cov=equipment-agent --cov-report=term-missing
```

### 13.4 テスト結果（実施済み）

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2
collected 56 items

tests/test_equipment_agent.py  ..........  (10 passed)
tests/test_mock_driver.py      ........   ( 8 passed)
tests/test_result_manager.py   ...................  (19 passed)
tests/test_scenario_parser.py  ........   ( 8 passed)
tests/test_state_manager.py    .........  ( 9 passed)

============================= 56 passed in 0.39s ==============================
```

---

## 14. エラーハンドリング設計

### 14.1 各層でのエラー対処

| 発生箇所 | エラー種別 | 対処 |
|---|---|---|
| ScenarioParser | FileNotFoundError / ValueError | `state.set_error()` → 試験中断・ログ送信 |
| ScenarioRunner ステップ | Exception（任意） | FAILとして記録・`on_fail:stop` なら中断 |
| AndroidAgentClient | HTTP エラー / タイムアウト | Exception として上位に伝播 → ステップFAIL |
| EquipmentAgentClient | HTTP エラー / タイムアウト | Exception として上位に伝播 → ステップFAIL |
| SharePointClient | 認証エラー / API エラー | `logger.warning()` → ローカル保存は完了・試験結果には影響しない |
| EquipmentAgent._load_config | ドライバロード失敗 | `logger.error()` → 対象機材をスキップ・他機材に影響なし |

### 14.2 HTTP エラーコード

| コード | 状況 | エンドポイント例 |
|---|---|---|
| 200 | 正常 | すべて |
| 202 | 非同期処理開始 | POST /test/start |
| 400 | リクエスト不正（パラメータ誤り） | POST /instruments/{name}/method |
| 404 | リソースが存在しない | GET /instruments/{name}/measure |
| 409 | 競合（試験が既に実行中） | POST /test/start |
| 500 | サーバーエラー（機材接続失敗等） | POST /instruments/{name}/connect |
| 503 | 依存サービス接続不可 | GET /devices (Android Agent未起動) |

---

## 15. セットアップ手順

### 15.1 前提条件

| ソフトウェア | バージョン | 用途 |
|---|---|---|
| Docker Desktop | 4.x 以上 | コンテナ実行環境 |
| Android Platform Tools | 最新版 | ADB コマンド |
| Git | 2.x 以上 | リポジトリ管理 |

### 15.2 初回セットアップ手順（各PCで1回）

```
【Step 1】Android Platform Tools（ADB）のインストール

  ① 以下のURLからダウンロード:
     https://developer.android.com/tools/releases/platform-tools
  ② zipを解凍 → 例: C:\android-tools\
  ③ システム環境変数の「Path」に追加: C:\android-tools\
  ④ コマンドプロンプトを新規起動して確認:
     > adb version
     Android Debug Bridge version 1.0.41

【Step 2】ADB Server の自動起動設定（Windows）

  方法A: スタートアップフォルダへ登録
  ① Win+R → shell:startup → フォルダが開く
  ② 右クリック → 新規 → ショートカット
  ③ プログラム: adb start-server
  ④ 名前: ADB Server

  方法B: タスクスケジューラ
  ① スタート → タスクスケジューラ → 基本タスクの作成
  ② トリガー: ログオン時
  ③ 操作: プログラムの起動 → adb start-server

【Step 3】Docker Desktop のインストール

  ① https://www.docker.com/products/docker-desktop からダウンロード
  ② インストーラを実行（WSL2 バックエンドを推奨）
  ③ PCを再起動
  ④ タスクバーのDocker アイコンが緑になることを確認

【Step 4】リポジトリの取得

  > git clone https://github.com/your-org/android-test-system
  > cd android-test-system

【Step 5】環境設定ファイルの作成

  > copy .env.example .env

  メモ帳等で .env を開いて SharePoint 接続情報を入力:
    SHAREPOINT_TENANT_ID=<Azureテナント ID>
    SHAREPOINT_CLIENT_ID=<アプリのクライアント ID>
    SHAREPOINT_CLIENT_SECRET=<シークレット値>
    SHAREPOINT_SITE_URL=https://contoso.sharepoint.com/sites/test
    TEST_SITE=your-lab-name

【Step 6】計測器設定（必要な場合）

  equipment-agent/config/equipment.yaml を編集:
  ・実際に接続する機材の driver / address を設定
  ・使用しない機材のエントリはコメントアウトまたは削除

【Step 7】起動

  > docker compose up -d

  初回はDockerイメージのビルドが行われます（5〜10分程度）。
  次回からは数秒で起動します。

【Step 8】Android端末の接続

  ① Android端末の「開発者オプション」→「USBデバッグ」を有効化
  ② PCとUSBケーブルで接続
  ③ 端末に「USBデバッグを許可しますか？」と表示されたら「許可」
  ④ 確認:
     > adb devices
     List of devices attached
     emulator-5554   device      ← この行が表示されれば成功

【Step 9】動作確認

  ブラウザで http://localhost:3000 を開く
  → シナリオが表示され、端末が認識されていれば完了
```

---

## 16. 運用手順

### 16.1 日常運用

```bash
# システム起動
docker compose up -d

# システム停止
docker compose down

# 起動状態確認
docker compose ps

# ログ確認（全コンテナ）
docker compose logs -f

# 特定コンテナのログ確認
docker compose logs -f orchestrator
docker compose logs -f android-agent
```

### 16.2 バージョンアップ手順

```bash
# 1. コードを最新化
git pull

# 2. イメージを再ビルドして起動
docker compose up -d --build

# 3. 動作確認
docker compose ps
```

### 16.3 試験シナリオの追加・更新

```bash
# 1. シナリオファイルを追加（コンテナ再起動不要）
cp my_new_scenario.yaml orchestrator/scenarios/

# 2. ブラウザでリロード → シナリオ一覧に反映される
```

### 16.4 計測器設定の変更

```bash
# 1. equipment.yaml を編集
notepad equipment-agent/config/equipment.yaml

# 2. Equipment Agent を再起動（コンテナ全体の再起動は不要）
docker compose restart equipment-agent
```

---

## 17. トラブルシューティング

### 17.1 よくある問題と対処

#### ADB 端末が認識されない

```
症状: ブラウザの端末一覧が空 / adb devices に何も表示されない

確認コマンド:
  > adb devices
  List of devices attached
  （空の場合）

対処:
  1. ADB Server の確認・再起動
     > adb kill-server
     > adb start-server
  2. USBケーブルの抜き差し
  3. 端末の「USBデバッグを許可しますか？」に「許可」を選択したか確認
  4. 端末のUSB接続モード → 「ファイル転送」または「MTP」に変更
```

#### Docker コンテナが起動しない

```
症状: docker compose up -d 後に docker compose ps で Exited が表示される

確認コマンド:
  > docker compose logs orchestrator

よくある原因と対処:
  ・ポートが既に使用中
    → netstat -ano | findstr :8000 でプロセス確認 → 終了させる
  ・.env が存在しない
    → copy .env.example .env を実行して設定を入力
  ・メモリ不足
    → Docker Desktop の設定 → Resources → Memoryを増やす
```

#### SharePoint への送信が失敗する

```
症状: ログに "SharePoint送信に失敗" が表示される（試験結果はローカル保存される）

確認事項:
  1. .env の SHAREPOINT_* が正しく設定されているか
  2. Azure AD アプリに Sites.ReadWrite.All 権限が付与されているか
  3. 管理者同意が完了しているか（Azure Portal で確認）
  4. クライアントシークレットが期限切れでないか

ログ確認:
  > docker compose logs orchestrator | grep SharePoint
```

#### Appium セッションが開始できない

```
症状: tap / assert_text アクションで "session not started" エラー

対処:
  1. /appium/session/start を先に呼び出しているか確認
     → シナリオの最初に appium セッション開始ステップを追加
  2. Appium Server の確認
     > curl http://localhost:4723/status
  3. android-agent コンテナのログ確認
     > docker compose logs android-agent
```

---

## 18. 残タスク・制約事項

### 18.1 残タスク

| 優先度 | タスク | 内容 |
|---|---|---|
| 高 | GitHubリポジトリ作成・push | `git remote add origin <URL>` して push |
| 高 | SharePoint Azure ADアプリ登録 | セクション9.3の手順を実施して `.env` に設定 |
| 高 | 実機動作確認 | `docker compose up` → Android端末接続 → サンプルシナリオ実行 |
| 中 | 実計測器ドライバ作成 | 手元の機材に合わせた `drivers/` 追加 |
| 中 | Power BI レポート設計 | SharePoint Lists に接続した分析ダッシュボード構築 |
| 低 | 非エンジニア向けセットアップ手順書 | スクリーンショット付きWord/PDF資料 |

### 18.2 既知の制約事項

| 制約 | 詳細 |
|---|---|
| USB接続 | ADB Server はホストPCにインストールが必要（Docker内に閉じ込められない） |
| 同時実行 | 試験は1試験のみ同時実行可能（StateManager は1セッション管理） |
| Appium対応 | Android 8.0（API 26）以上が必要（UiAutomator2の要件） |
| Wi-Fi ADB | Android 11以上で`adb tcpip`によるワイヤレス接続が可能 |
| シリアル通信 | コンテナ内からシリアルポートを使う場合は docker-compose.yml の `devices:` 設定が別途必要 |
| SharePoint | `TestResults` リストの Details 列は4000文字に切り詰め（SharePoint Lists の制限） |
