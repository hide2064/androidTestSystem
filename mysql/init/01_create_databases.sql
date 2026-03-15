-- Android試験システム + opeAnyalyze 共通DB初期化
-- MySQL 起動時に自動実行される

CREATE DATABASE IF NOT EXISTS testSystemDB
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS cellularAnylyze
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON testSystemDB.*    TO 'testuser'@'%';
GRANT ALL PRIVILEGES ON cellularAnylyze.* TO 'testuser'@'%';
FLUSH PRIVILEGES;
