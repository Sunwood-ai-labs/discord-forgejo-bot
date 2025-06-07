import os
import discord
from discord.ext import commands
from .forgejo_api import ForgejoAPI

import asyncio

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
        synced = await bot.tree.sync()
        print(f'{len(synced)} 個のスラッシュコマンドを同期しました')
    except Exception as e:
        print(f'コマンド同期に失敗: {e}')

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
    """Issue状態変更をDiscordに通知"""
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
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Discord通知エラー: {e}")

async def send_comment_notification(issue, comment):
    """コメント追加をDiscordに通知"""
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
        await channel.send(embed=embed)
    except Exception as e:
        print(f"コメント通知エラー: {e}")