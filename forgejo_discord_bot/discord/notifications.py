import os
import discord
from ..database.models import (
    get_channel_id_for_repository,
    get_thread_id_from_db,
    set_thread_id_to_db
)


# 設定
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')


async def send_issue_notification(bot, action, issue, repository=None):
    """Issue状態変更をDiscordに通知（同じissueは同じスレッドに返信）"""
    try:
        # リポジトリが指定されている場合は、対応するチャンネルを取得
        if repository:
            channel_id = get_channel_id_for_repository(repository)
            if not channel_id:
                print(f"リポジトリ '{repository}' に対応するチャンネルが設定されていません")
                # フォールバック: デフォルトチャンネルを使用
                channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        else:
            # リポジトリが指定されていない場合はデフォルトチャンネルを使用
            channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"チャンネルが見つかりません: {channel_id}")
            return
        
        action_emoji = {
            'opened': '🆕',
            'closed': '✅',
            'reopened': '🔄'
        }
        action_text = {
            'opened': '作成されました',
            'closed': 'クローズされました',
            'reopened': '再オープンされました'
        }
        
        embed = discord.Embed(
            title=f"{action_emoji.get(action, '📋')} Issue {action_text.get(action, action)}",
            description=f"**#{issue['number']}** {issue['title']}",
            color=0x00ff00 if action == 'opened' else 0xff9900 if action == 'closed' else 0x0099ff,
            url=issue['html_url']
        )
        # リポジトリ名を表示（リポジトリが指定されている場合は使用、そうでなければデフォルト）
        repo_display = repository if repository else f"{REPO_OWNER}/{REPO_NAME}"
        embed.add_field(name="リポジトリ", value=repo_display, inline=True)
        embed.add_field(name="作成者", value=issue['user']['login'], inline=True)

        issue_number = issue['number']
        thread = None

        # "opened"または"reopened"時は新規スレッド作成
        if action in ['opened', 'reopened']:
            # 既存スレッドがあればそれを使う（再オープン時など）
            thread_id = get_thread_id_from_db(issue_number)
            if thread_id:
                try:
                    thread = await bot.fetch_channel(thread_id)
                except Exception:
                    thread = None
            if not thread:
                # 新規スレッド作成
                thread_name = f"Issue #{issue_number}: {issue['title'][:80]}"
                msg = await channel.send(embed=embed)
                thread = await msg.create_thread(name=thread_name, auto_archive_duration=1440)
                set_thread_id_to_db(issue_number, thread.id, repository)
            else:
                await thread.send(embed=embed)
        else:
            # "closed"などは既存スレッドに返信、なければ新規作成
            thread_id = get_thread_id_from_db(issue_number)
            if thread_id:
                try:
                    thread = await bot.fetch_channel(thread_id)
                except Exception:
                    thread = None
            if not thread:
                # 新規スレッド作成
                thread_name = f"Issue #{issue_number}: {issue['title'][:80]}"
                msg = await channel.send(embed=embed)
                thread = await msg.create_thread(name=thread_name, auto_archive_duration=1440)
                set_thread_id_to_db(issue_number, thread.id, repository)
            else:
                await thread.send(embed=embed)
    except Exception as e:
        print(f"Discord通知エラー: {e}")


async def send_comment_notification(bot, issue, comment, repository=None):
    """コメント追加をDiscordに通知（同じissueは同じスレッドに返信）"""
    try:
        # Discord由来のコメントは通知しない
        import re
        body = comment.get('body', '').strip()
        if re.search(r"\*Posted from Discord by .+（Discord）\*$", body):
            return

        # リポジトリが指定されている場合は、対応するチャンネルを取得
        if repository:
            channel_id = get_channel_id_for_repository(repository)
            if not channel_id:
                print(f"リポジトリ '{repository}' に対応するチャンネルが設定されていません")
                # フォールバック: デフォルトチャンネルを使用
                channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        else:
            # リポジトリが指定されていない場合はデフォルトチャンネルを使用
            channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        
        channel = bot.get_channel(channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title=f"💬 新しいコメント",
            description=f"**Issue #{issue['number']}:** {issue['title']}",
            color=0x9966cc,
            url=comment['html_url']
        )
        embed.add_field(name="コメント者", value=comment['user']['login'], inline=True)
        embed.add_field(name="内容", value=comment['body'][:500] + ('...' if len(comment['body']) > 500 else ''), inline=False)

        issue_number = issue['number']
        thread = None
        thread_id = get_thread_id_from_db(issue_number)
        if thread_id:
            try:
                thread = await bot.fetch_channel(thread_id)
            except Exception:
                thread = None
        if not thread:
            # 新規スレッド作成
            thread_name = f"Issue #{issue_number}: {issue['title'][:80]}"
            msg = await channel.send(embed=embed)
            thread = await msg.create_thread(name=thread_name, auto_archive_duration=1440)
            set_thread_id_to_db(issue_number, thread.id, repository)
        else:
            await thread.send(embed=embed)
    except Exception as e:
        print(f"コメント通知エラー: {e}")
