"""
後方互換性のためのエントリーポイント
新しい構造では core.bot を使用してください
"""
from .core.bot import bot

# 後方互換性のため、主要な関数をエクスポート
__all__ = ['bot']
