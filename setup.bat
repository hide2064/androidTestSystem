@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================================
echo  Android 自動試験システム - 初回セットアップ
echo ============================================================
echo.

:: ── 前提ソフトウェアチェック ─────────────────────────────────

echo [1/5] 前提ソフトウェアを確認しています...

docker --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker が見つかりません。Docker Desktop をインストールしてください。
    echo         https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

docker info > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop が起動していません。起動してから再実行してください。
    pause
    exit /b 1
)

adb --version > nul 2>&1
if errorlevel 1 (
    echo [WARN]  ADB が見つかりません。Android 端末を使う場合は Android Platform Tools をインストールしてください。
    echo         https://developer.android.com/tools/releases/platform-tools
    echo.
) else (
    echo        ADB: OK
)

echo        Docker: OK
echo.

:: ── .env ファイル設定 ─────────────────────────────────────────

echo [2/5] 環境変数を設定しています...

if exist .env (
    echo        .env が既に存在します。スキップします。
    echo        変更したい場合は .env を直接編集してください。
    echo.
    goto :env_done
)

echo.
echo  .env を作成します。各項目を入力してください。
echo  ※ 空のままEnterで括弧内のデフォルト値が使われます。
echo.

:: MySQL root パスワード
set /p "INPUT_ROOT_PW=  MySQL root パスワード (TestSystem2024!) : "
if "!INPUT_ROOT_PW!"=="" set INPUT_ROOT_PW=TestSystem2024!

:: MySQL ユーザーパスワード
set /p "INPUT_USER_PW=  MySQL ユーザーパスワード (TestUser2024!) : "
if "!INPUT_USER_PW!"=="" set INPUT_USER_PW=TestUser2024!

:: 試験サイト名
set /p "INPUT_TEST_SITE=  試験サイト名 (local-dev) : "
if "!INPUT_TEST_SITE!"=="" set INPUT_TEST_SITE=local-dev

:: SharePoint（省略可）
echo.
echo  SharePoint 連携を設定しますか？ (使わない場合はEnterでスキップ)
set /p "INPUT_SP_URL=  SharePoint サイトURL (空=スキップ) : "

if "!INPUT_SP_URL!"=="" (
    set INPUT_SP_TENANT=
    set INPUT_SP_CLIENT_ID=
    set INPUT_SP_CLIENT_SECRET=
) else (
    set /p "INPUT_SP_TENANT=  Tenant ID : "
    set /p "INPUT_SP_CLIENT_ID=  Client ID : "
    set /p "INPUT_SP_CLIENT_SECRET=  Client Secret : "
)

:: .env 書き出し
(
    echo # MySQL
    echo MYSQL_ROOT_PASSWORD=!INPUT_ROOT_PW!
    echo DB_PASSWORD=!INPUT_USER_PW!
    echo.
    echo # SharePoint / Microsoft 365
    echo SHAREPOINT_SITE_URL=!INPUT_SP_URL!
    echo SHAREPOINT_TENANT_ID=!INPUT_SP_TENANT!
    echo SHAREPOINT_CLIENT_ID=!INPUT_SP_CLIENT_ID!
    echo SHAREPOINT_CLIENT_SECRET=!INPUT_SP_CLIENT_SECRET!
    echo.
    echo # 試験サイト識別子
    echo TEST_SITE=!INPUT_TEST_SITE!
) > .env

echo.
echo        .env を作成しました。
echo.

:env_done

:: ── Docker イメージのビルドと起動 ────────────────────────────

echo [3/5] Docker イメージをビルドしています... (初回は数分かかります)
echo.

docker compose build
if errorlevel 1 (
    echo [ERROR] ビルドに失敗しました。エラーを確認してください。
    pause
    exit /b 1
)

echo.
echo [4/5] サービスを起動しています...
echo.

docker compose up -d
if errorlevel 1 (
    echo [ERROR] 起動に失敗しました。エラーを確認してください。
    pause
    exit /b 1
)

:: ── 起動完了待機 ──────────────────────────────────────────────

echo.
echo [5/5] サービスの起動完了を待機しています...
echo        (初回はAppiumのダウンロード等で2〜3分かかる場合があります)
echo.

set RETRY=0
set MAX_RETRY=36

:wait_loop
set /a RETRY+=1
if !RETRY! gtr !MAX_RETRY! (
    echo [WARN]  タイムアウト。サービスがまだ起動中の可能性があります。
    echo         docker compose logs でログを確認してください。
    goto :open_browser
)

:: orchestratorのヘルスチェック
curl -sf http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    <nul set /p "=."
    timeout /t 5 /nobreak > nul
    goto :wait_loop
)

:: analysis-serviceのヘルスチェック
curl -sf http://localhost:8001/health > nul 2>&1
if errorlevel 1 (
    <nul set /p "=."
    timeout /t 5 /nobreak > nul
    goto :wait_loop
)

echo.
echo.

:open_browser

:: ── 完了メッセージ ────────────────────────────────────────────

echo ============================================================
echo  セットアップ完了！
echo ============================================================
echo.
echo  ダッシュボード : http://localhost:3000
echo  Orchestrator  : http://localhost:8000/docs
echo  Analysis API  : http://localhost:8001/docs
echo.

:: Android 端末の確認
adb --version > nul 2>&1
if not errorlevel 1 (
    echo  接続済み Android 端末:
    adb devices
    echo.
)

echo  ブラウザを開いています...
start http://localhost:3000

echo.
echo  ※ 次回以降は以下のコマンドだけで起動できます:
echo       docker compose up -d
echo.
pause
