@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================================
echo  Android 自動試験システム - 起動
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
    echo [ERROR] .env が見つかりません。初回は setup.bat を実行してください。
    pause
    exit /b 1
)

:: ── サービス起動 ──────────────────────────────────────────────

echo  サービスを起動しています...
echo.

docker compose up -d
if errorlevel 1 (
    echo [ERROR] 起動に失敗しました。docker compose logs でログを確認してください。
    pause
    exit /b 1
)

:: ── 起動完了待機 ──────────────────────────────────────────────

echo.
echo  起動完了を待機しています...

set RETRY=0
set MAX_RETRY=36

:wait_loop
set /a RETRY+=1
if !RETRY! gtr !MAX_RETRY! (
    echo.
    echo [WARN]  タイムアウト。docker compose logs で状態を確認してください。
    goto :done
)

curl -sf http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    <nul set /p "=."
    timeout /t 5 /nobreak > nul
    goto :wait_loop
)

curl -sf http://localhost:8001/health > nul 2>&1
if errorlevel 1 (
    <nul set /p "=."
    timeout /t 5 /nobreak > nul
    goto :wait_loop
)

echo.

:done

:: ── 完了 ─────────────────────────────────────────────────────

echo.
echo  起動完了: http://localhost:3000
echo.

start http://localhost:3000
