import os
import discord
from discord.ext import commands
from ..forgejo.api import ForgejoAPI
from ..database.models import (
    ensure_issue_threads_table,
    get_issue_number_from_thread_id
)
from ..discord.commands import setup_commands


# 設定
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
FORGEJO_URL = os.getenv('FORGEJO_URL')
FORGEJO_TOKEN = os.getenv('FORGEJO_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

forgejo = ForgejoAPI(FORGEJO_URL, FORGEJO_TOKEN)


@bot.event
async def on_ready():
    """Bot起動時のイベント"""
    print(f'{bot.user} がログインしました！')
    try:
        # DBテーブル作成
        ensure_issue_threads_table()
        
        # スラッシュコマンドを設定
        setup_commands(bot)
        
        # コマンドを同期
        synced = await bot.tree.sync()
        print(f'{len(synced)} 個のスラッシュコマンドを同期しました')

        # 除外チャンネルリストを.envから取得
        excluded_channels = os.getenv("EXCLUDED_CHANNELS", "")
        excluded_channels = [name.strip() for name in excluded_channels.split(",") if name.strip()]

        # 参加している全ギルドの全テキストチャンネルにBotを「追加」
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.name not in excluded_channels:
                    try:
                        # ここでBotがチャンネルに「追加」されていることを通知（または初期化処理）
                        await channel.send(f"Botがこのチャンネル（{channel.name}）で有効になりました。")
                    except Exception as e:
                        print(f"チャンネル {channel.name} への通知失敗: {e}")

    except Exception as e:
        print(f'コマンド同期に失敗: {e}')


@bot.event
async def on_message(message):
    """メッセージ受信時のイベント"""
    # Bot自身の発言は無視
    if message.author.bot:
        return

    # スレッド内のメッセージのみ対象
    if isinstance(message.channel, discord.Thread):
        issue_number = get_issue_number_from_thread_id(message.channel.id)
        if issue_number is not None:
            # Forgejoにコメント投稿
            try:
                # コメント本文
                comment_body = (
                    f"{message.content}"
                    f"\n\n---\n*Posted from Discord by {message.author.display_name}（Discord）*"
                )
                await forgejo.create_comment(
                    owner=REPO_OWNER,
                    repo=REPO_NAME,
                    issue_number=issue_number,
                    body=comment_body
                )
            except Exception as e:
                print(f"Forgejoコメント投稿エラー: {e}")

    # 他のコマンドも通す
    await bot.process_commands(message)
