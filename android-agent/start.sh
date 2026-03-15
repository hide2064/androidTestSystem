#!/bin/bash
# Appium Server をバックグラウンドで起動
appium --address 0.0.0.0 --port 4723 --base-path / &

# FastAPI を起動
uvicorn main:app --host 0.0.0.0 --port 5000
