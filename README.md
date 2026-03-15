# Android 自動試験システム

ブラウザから操作できる Android 端末自動試験システムです。

## 構成

```
ブラウザ (localhost:3000)
    │
    ▼
Orchestrator (localhost:8000) ← 試験司令塔
    ├── Android Agent (localhost:5000) ← ADB + Appium
    └── Equipment Agent (localhost:5001) ← 計測器制御
                                        ↓
                              SharePoint / Power BI
```

## セットアップ（各PCで初回のみ）

### 1. 前提ソフトウェアのインストール

| ソフトウェア | 説明 | 入手先 |
|---|---|---|
| Docker Desktop | コンテナ実行環境 | https://www.docker.com/products/docker-desktop |
| Android Platform Tools | ADB コマンド | https://developer.android.com/tools/releases/platform-tools |

ADB を PATH に追加して、`adb version` が通ることを確認してください。

### 2. ADB Server の自動起動設定（Windows）

タスクスケジューラまたはスタートアップフォルダに以下を登録:
```
adb start-server
```

### 3. リポジトリの取得

```bash
git clone https://github.com/your-org/android-test-system
cd android-test-system
```

### 4. 環境設定ファイルの作成

```bash
cp .env.example .env
# .env を編集して SharePoint 接続情報を入力
```

### 5. 起動

```bash
docker compose up -d
```

ブラウザで http://localhost:3000 を開けば完了です。

### 6. Android 端末の接続

```bash
adb devices  # 端末が認識されていることを確認
```

---

## バージョンアップ

```bash
git pull
docker compose pull
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
    device: power_supply          # equipment.yaml に定義した機材名
    parameter: voltage_ch1
    expect:
      between: [3.5, 4.2]        # 範囲外なら FAIL
    on_fail: stop                 # FAIL 時に試験を中断する場合

  - id: 4
    description: 画面のボタンをタップ
    action: tap
    locator_type: text            # id / text / xpath / desc
    locator_value: "設定"

  - id: 5
    description: 画面に "完了" と表示されることを確認
    action: assert_text
    locator_type: id
    locator_value: com.example:id/result
    expect:
      equals: "完了"
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
android-test-system/
├── docker-compose.yml
├── .env.example
├── dashboard/              ← ブラウザUI (nginx)
│   └── index.html
├── orchestrator/           ← 試験司令塔 (FastAPI)
│   ├── main.py
│   ├── scenario_runner.py
│   ├── scenario_parser.py
│   ├── state_manager.py
│   ├── result_manager.py
│   ├── agent_client.py
│   ├── sharepoint_client.py
│   └── scenarios/          ← ← YAMLシナリオを置く場所
├── android-agent/          ← ADB + Appium (FastAPI)
│   ├── main.py
│   ├── adb_client.py
│   └── appium_client.py
└── equipment-agent/        ← 計測器制御 (FastAPI)
    ├── main.py
    ├── agent.py
    ├── base_driver.py
    ├── drivers/            ← ← ドライバを置く場所
    │   ├── visa/
    │   ├── serial/
    │   ├── rest/
    │   └── mock/
    └── config/
        └── equipment.yaml  ← ← 接続機材の設定
```
