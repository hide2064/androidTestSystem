@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================================
echo  Android 自動試験システム - デバッグモード起動
echo ============================================================
echo.
echo  debugpy ポート一覧:
echo    🎯 orchestrator    : localhost:5678
echo    📱 android-agent   : localhost:5679
echo    🔧 equipment-agent : localhost:5680
echo    📈 analysis-service: localhost:5681
echo.
echo  ホットリロード: ソースファイルを保存すると自動再起動します
echo ============================================================
echo.

:: ── 前提確認 ─────────────────────────────────────────────────

docker info > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop が起動していません。起動してから再実行してください。
    pause
    exit /b 1
)

if not exist .env (
    echo [ERROR] .env が見つかりません。先に setup.bat を実行してください。
    pause
    exit /b 1
)

if not exist docker-compose.debug.yml (
    echo [ERROR] docker-compose.debug.yml が見つかりません。
    pause
    exit /b 1
)

:: ── デバッグモードで起動 ──────────────────────────────────────

echo  デバッグモードで起動しています...
echo  (初回はサービスイメージのビルドに数分かかる場合があります)
echo.

docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d
if errorlevel 1 (
    echo.
    echo [ERROR] 起動に失敗しました。
    echo         docker compose logs でエラー内容を確認してください。
    pause
    exit /b 1
)

:: ── debugpy 待機 ──────────────────────────────────────────────

echo.
echo  サービスの起動を待機しています...

set RETRY=0
set MAX_RETRY=24

:wait_loop
set /a RETRY+=1
if !RETRY! gtr !MAX_RETRY! (
    echo.
    echo [WARN] タイムアウト。サービスがまだ起動中の可能性があります。
    goto :show_instructions
)

curl -sf http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    <nul set /p "=."
    timeout /t 5 /nobreak > nul
    goto :wait_loop
)

echo.

:show_instructions

:: ── 操作案内 ─────────────────────────────────────────────────

echo.
echo ============================================================
echo  デバッグモード起動完了
echo ============================================================
echo.
echo  【VS Code でのデバッグ手順】
echo.
echo  1. VS Code で Run ^& Debug パネルを開く (Ctrl+Shift+D)
echo.
echo  2. デバッグ設定を選択して F5 でアタッチ:
echo       "Attach: All Services"  ... 全サービス一括アタッチ
echo       "Attach: orchestrator"  ... orchestrator のみ
echo       "Attach: android-agent" ... android-agent のみ
echo       (他のサービスも同様)
echo.
echo  3. デバッグしたいファイルにブレークポイントを設置
echo       例: orchestrator/scenario_runner.py の任意の行
echo.
echo  4. ブラウザから操作すると該当箇所で停止します
echo       http://localhost:3000
echo.
echo  【ホットリロードについて】
echo    ソースファイルを保存 → サービスが自動再起動 → デバッガを再アタッチ
echo.
echo  【ログ確認】
echo    docker compose logs -f orchestrator
echo    docker compose logs -f android-agent
echo.
echo  【通常モードに戻す】
echo    docker compose down
echo    docker compose up -d   または  start.bat
echo.

start http://localhost:3000
pause
