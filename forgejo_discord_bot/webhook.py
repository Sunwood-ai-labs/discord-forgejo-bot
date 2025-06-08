"""
後方互換性のためのエントリーポイント
新しい構造では web.webhook を使用してください
"""
from .web.webhook import app, run_flask

# 後方互換性のため、主要な関数をエクスポート
__all__ = ['app', 'run_flask']
