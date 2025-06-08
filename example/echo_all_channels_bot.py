import os
import discord

from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

# Botのトークンは環境変数から取得
TOKEN = os.getenv('DISCORD_TOKEN')

# メッセージ内容を取得するためのIntentを有効化
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'ログインしました: {client.user}')

@client.event
async def on_message(message):
    # Bot自身のメッセージには反応しない
    if message.author == client.user:
        return
    # Embedでメッセージを作成し、フッターにチャンネル名を記載
    embed = discord.Embed(description=message.content)
    embed.set_footer(text=f"チャンネル: {message.channel.name}")
    await message.channel.send(embed=embed)

if __name__ == '__main__':
    if TOKEN is None:
        print("DISCORD_TOKEN環境変数が設定されていません。")
    else:
        client.run(TOKEN)