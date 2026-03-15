"""
analysis-service 設定
RF DB (cellularAnylyze) と Android試験DB (testSystemDB) の2DB対応
"""
import os
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RfSettings(BaseSettings):
    """RF試験データ DB (cellularAnylyze) 接続設定"""
    DB_HOST:     str = os.getenv("DB_HOST", "mysql")
    DB_PORT:     int = int(os.getenv("DB_PORT", "3306"))
    DB_USER:     str = os.getenv("DB_USER", "testuser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME:     str = os.getenv("DB_NAME", "cellularAnylyze")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


class AndroidSettings(BaseSettings):
    """Android試験結果 DB (testSystemDB) 接続設定"""
    ANDROID_DB_HOST:     str = os.getenv("ANDROID_DB_HOST", "mysql")
    ANDROID_DB_PORT:     int = int(os.getenv("ANDROID_DB_PORT", "3306"))
    ANDROID_DB_USER:     str = os.getenv("ANDROID_DB_USER", "testuser")
    ANDROID_DB_PASSWORD: str = os.getenv("ANDROID_DB_PASSWORD", "")
    ANDROID_DB_NAME:     str = os.getenv("ANDROID_DB_NAME", "testSystemDB")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.ANDROID_DB_USER}:{self.ANDROID_DB_PASSWORD}"
            f"@{self.ANDROID_DB_HOST}:{self.ANDROID_DB_PORT}/{self.ANDROID_DB_NAME}"
        )


settings    = RfSettings()
android_cfg = AndroidSettings()
