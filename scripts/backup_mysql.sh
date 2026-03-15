#!/usr/bin/env bash
# MySQL バックアップスクリプト
# Docker コンテナ内の mysqldump を使って全DBをダンプする
#
# 使い方:
#   bash scripts/backup_mysql.sh [backup_dir]
#
# デフォルト保存先: ./backups/
# cron 例 (毎日 2:00 AM):
#   0 2 * * * cd /path/to/androidTestSystem && bash scripts/backup_mysql.sh >> logs/backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
CONTAINER="androidtestsystem-mysql-1"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-TestSystem2024!}"
TIMESTAMP=$(date +"%Y%m%dT%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/mysql_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -Iseconds)] バックアップ開始: ${BACKUP_FILE}"

docker exec "${CONTAINER}" \
  mysqldump \
    -uroot \
    "-p${MYSQL_ROOT_PASSWORD}" \
    --all-databases \
    --single-transaction \
    --routines \
    --triggers \
  | gzip > "${BACKUP_FILE}"

SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[$(date -Iseconds)] 完了: ${BACKUP_FILE} (${SIZE})"

# 30日以上前のバックアップを削除
find "${BACKUP_DIR}" -name "mysql_backup_*.sql.gz" -mtime +30 -delete
echo "[$(date -Iseconds)] 古いバックアップを削除しました (30日以上前)"
