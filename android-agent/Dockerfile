FROM node:20-slim AS appium-base

# Appium Server インストール
RUN npm install -g appium@latest && \
    appium driver install uiautomator2

FROM python:3.11-slim

# Node.js と Appium をコピー
COPY --from=appium-base /usr/local/bin/node /usr/local/bin/
COPY --from=appium-base /usr/local/bin/npm /usr/local/bin/
COPY --from=appium-base /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=appium-base /usr/local/bin/appium /usr/local/bin/
COPY --from=appium-base /root/.appium /root/.appium

# ADB インストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Appium をバックグラウンドで起動してから FastAPI を起動するスクリプト
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 5000 4723

CMD ["/start.sh"]
