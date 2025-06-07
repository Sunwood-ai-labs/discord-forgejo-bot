import os
import discord
from discord.ext import commands
from .forgejo_api import ForgejoAPI

import asyncio
import psycopg2

# PostgreSQL接続情報
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'forgejo_discord')
DB_USER = os.getenv('DB_USER', 'forgejo_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'forgejo_pass')

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def ensure_issue_threads_table():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS issue_threads (
                issue_number INTEGER PRIMARY KEY,
                thread_id BIGINT NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DBテーブル作成エラー: {e}")

def get_thread_id_from_db(issue_number):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT thread_id FROM issue_threads WHERE issue_number = %s;", (issue_number,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"DB取得エラー: {e}")
        return None

def get_issue_number_from_thread_id(thread_id):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT issue_number FROM issue_threads WHERE thread_id = %s;", (thread_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"DB取得エラー: {e}")
        return None

def set_thread_id_to_db(issue_number, thread_id):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO issue_threads (issue_number, thread_id)
            VALUES (%s, %s)
            ON CONFLICT (issue_number) DO UPDATE SET thread_id = EXCLUDED.thread_id;
        """, (issue_number, thread_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB保存エラー: {e}")

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
    print(f'{bot.user} がログインしました！')
    try:
        # DBテーブル作成
        ensure_issue_threads_table()
        synced = await bot.tree.sync()
        print(f'{len(synced)} 個のスラッシュコマンドを同期しました')
    except Exception as e:
        print(f'コマンド同期に失敗: {e}')

@bot.event
async def on_message(message):
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
                comment_body = f"{message.author.display_name}（Discord）:\n{message.content}"
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

@bot.tree.command(name="issue", description="Forgejoにissueを作成します")
async def create_issue_command(interaction: discord.Interaction, title: str, description: str, assignee: str = None):
    """Discord slash commandでissue作成"""
    await interaction.response.defer()
    try:
        author_info = f"\n\n---\n**作成者:** {interaction.user.mention} ({interaction.user.name})\n**Discord ID:** {interaction.user.id}"
        full_description = description + author_info
        issue = await forgejo.create_issue(
            owner=REPO_OWNER,
            repo=REPO_NAME,
            title=title,
            body=full_description,
            assignee=assignee
        )
        embed = discord.Embed(
            title="✅ Issue作成完了",
            description=f"**#{issue['number']}** {title}",
            color=0x00ff00,
            url=issue['html_url']
        )
        embed.add_field(name="リポジトリ", value=f"{REPO_OWNER}/{REPO_NAME}", inline=True)
        embed.add_field(name="作成者", value=issue['user']['login'], inline=True)
        embed.add_field(name="状態", value=issue['state'], inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ エラー",
            description=f"Issue作成に失敗しました: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(name="issue_status", description="指定したissueの状態を確認します")
async def check_issue_command(interaction: discord.Interaction, issue_number: int):
    """Issue状態確認コマンド"""
    await interaction.response.defer()
    try:
        issue = await forgejo.get_issue(REPO_OWNER, REPO_NAME, issue_number)
        if not issue:
            await interaction.followup.send("指定されたissueが見つかりませんでした。")
            return
        embed = discord.Embed(
            title=f"Issue #{issue['number']}: {issue['title']}",
            description=issue.get('body', '説明なし')[:1000] + ('...' if len(issue.get('body', '')) > 1000 else ''),
            color=0x0099ff,
            url=issue['html_url']
        )
        embed.add_field(name="状態", value=issue['state'], inline=True)
        embed.add_field(name="作成者", value=issue['user']['login'], inline=True)
        embed.add_field(name="作成日", value=issue['created_at'][:10], inline=True)
        if issue.get('assignee'):
            embed.add_field(name="担当者", value=issue['assignee']['login'], inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ エラー",
            description=f"Issue取得に失敗しました: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

async def send_issue_notification(action, issue):
    """Issue状態変更をDiscordに通知（同じissueは同じスレッドに返信）"""
    try:
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
        embed.add_field(name="リポジトリ", value=f"{REPO_OWNER}/{REPO_NAME}", inline=True)
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
                set_thread_id_to_db(issue_number, thread.id)
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
                set_thread_id_to_db(issue_number, thread.id)
            else:
                await thread.send(embed=embed)
    except Exception as e:
        print(f"Discord通知エラー: {e}")

async def send_comment_notification(issue, comment):
    """コメント追加をDiscordに通知（同じissueは同じスレッドに返信）"""
    try:
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
            set_thread_id_to_db(issue_number, thread.id)
        else:
            await thread.send(embed=embed)
    except Exception as e:
        print(f"コメント通知エラー: {e}")