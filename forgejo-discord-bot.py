import discord
from discord.ext import commands
import aiohttp
import asyncio
from flask import Flask, request, jsonify
import threading
import json
import os

# 設定
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
FORGEJO_URL = os.getenv('FORGEJO_URL')  # https://git.example.com
FORGEJO_TOKEN = os.getenv('FORGEJO_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

# Discord bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Flask app for webhooks
app = Flask(__name__)

class ForgejoAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
    
    async def create_issue(self, owner, repo, title, body, assignee=None, labels=None):
        """Forgejoにissueを作成"""
        url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues"
        
        data = {
            'title': title,
            'body': body
        }
        
        if assignee:
            data['assignee'] = assignee
        if labels:
            data['labels'] = labels
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Failed to create issue: {response.status} - {text}")
    
    async def get_issue(self, owner, repo, issue_number):
        """指定したissueの詳細を取得"""
        url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues/{issue_number}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

# Forgejo API インスタンス
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
        # Discordユーザー情報を含める
        author_info = f"\n\n---\n**作成者:** {interaction.user.mention} ({interaction.user.name})\n**Discord ID:** {interaction.user.id}"
        full_description = description + author_info
        
        # Forgejoにissue作成
        issue = await forgejo.create_issue(
            owner=REPO_OWNER,
            repo=REPO_NAME,
            title=title,
            body=full_description,
            assignee=assignee
        )
        
        # 成功時のEmbed作成
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

# Forgejo Webhook受信用のFlask route
@app.route('/webhook/forgejo', methods=['POST'])
def forgejo_webhook():
    """Forgejoからのwebhookを処理"""
    try:
        print("=== Webhook受信 ===")
        print(f"Headers: {dict(request.headers)}")
        print(f"Raw data: {request.data}")

        # Secret検証（設定されている場合）
        if WEBHOOK_SECRET:
            signature = request.headers.get('X-Gitea-Signature')
            if not verify_signature(request.data, signature, WEBHOOK_SECRET):
                print("シグネチャ検証失敗")
                return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        print(f"受信データ: {data}")
        
        if not data:
            print("JSONデータなし")
            return jsonify({'error': 'No JSON data'}), 400
        
        # webhook typeを確認
        action = data.get('action')
        issue = data.get('issue', {})
        print(f"action: {action}")
        
        if action in ['opened', 'closed', 'reopened']:
            print("issue通知分岐")
            # 非同期でDiscordに通知
            asyncio.run_coroutine_threadsafe(
                send_issue_notification(action, issue),
                bot.loop
            )
        elif action == 'created' and 'comment' in data:
            print("コメント通知分岐")
            # コメント通知
            comment = data.get('comment', {})
            asyncio.run_coroutine_threadsafe(
                send_comment_notification(issue, comment),
                bot.loop
            )
        else:
            print("通知対象外のactionまたは不明なaction")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook処理エラー: {e}")
        return jsonify({'error': str(e)}), 500

async def send_issue_notification(action, issue):
    """Issue状態変更をDiscordに通知"""
    try:
        channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))  # 通知チャンネルID
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

def run_flask():
    """Flaskアプリを別スレッドで実行"""
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Flask webhook server starting on {host}:{port}")
    print(f"📡 Webhook URL: http://192.168.0.131:{port}/webhook/forgejo")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # 環境変数チェック
    required_vars = ['DISCORD_TOKEN', 'FORGEJO_URL', 'FORGEJO_TOKEN', 'REPO_OWNER', 'REPO_NAME', 'DISCORD_CHANNEL_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        exit(1)
    
    # Flaskを別スレッドで起動
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Discord botを起動
    bot.run(DISCORD_TOKEN)