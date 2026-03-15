"""
pytest 共通設定
"""
import sys, os

# 各モジュールのルートを sys.path に追加
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ["orchestrator", "equipment-agent", "android-agent"]:
    p = os.path.join(ROOT, d)
    if p not in sys.path:
        sys.path.insert(0, p)
