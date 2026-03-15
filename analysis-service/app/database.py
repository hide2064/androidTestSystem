"""
analysis-service データベース接続
RF DB と Android試験結果 DB の2エンジン管理
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.config import settings, android_cfg

_rf_engine:      Engine | None = None
_android_engine: Engine | None = None


def get_engine() -> Engine:
    """RF DB (cellularAnylyze) エンジンを返す（opeAnyalyze互換）"""
    global _rf_engine
    if _rf_engine is None:
        _rf_engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _rf_engine


def get_android_engine() -> Engine:
    """Android試験結果 DB (testSystemDB) エンジンを返す"""
    global _android_engine
    if _android_engine is None:
        _android_engine = create_engine(
            android_cfg.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _android_engine


@contextmanager
def get_connection() -> Generator:
    """RF DB 接続（opeAnyalyze 既存コードとの互換性維持）"""
    with get_engine().connect() as conn:
        yield conn


@contextmanager
def get_android_connection() -> Generator:
    """Android試験結果 DB 接続"""
    with get_android_engine().connect() as conn:
        yield conn


def get_inspector():
    return inspect(get_engine())
