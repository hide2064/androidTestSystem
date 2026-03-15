-- Android試験結果テーブル定義

USE testSystemDB;

CREATE TABLE IF NOT EXISTS android_test_results (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id        VARCHAR(64)  NOT NULL UNIQUE,
    scenario      VARCHAR(128) NOT NULL,
    device_id     VARCHAR(64)  NOT NULL,
    device_model  VARCHAR(128),
    test_site     VARCHAR(64)  DEFAULT 'unknown',
    operator_id   VARCHAR(64),
    started_at    DATETIME     NOT NULL,
    finished_at   DATETIME,
    total         INT          DEFAULT 0,
    pass_count    INT          DEFAULT 0,
    fail_count    INT          DEFAULT 0,
    result        ENUM('PASS','FAIL','RUNNING','ABORTED') DEFAULT 'RUNNING',
    note          TEXT,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS android_test_steps (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id         VARCHAR(64)  NOT NULL,
    step_id        INT          NOT NULL,
    action         VARCHAR(64)  NOT NULL,
    description    TEXT,
    response       TEXT,
    measured_value DOUBLE,
    unit           VARCHAR(32),
    upper_limit    DOUBLE,
    lower_limit    DOUBLE,
    pass           BOOLEAN      NOT NULL DEFAULT FALSE,
    error_msg      TEXT,
    executed_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id),
    FOREIGN KEY (run_id) REFERENCES android_test_results(run_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
