import os
import discord

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
    # 受け取ったメッセージをそのまま返す
    await message.channel.send(message.content)

if __name__ == '__main__':
    if TOKEN is None:
        print("DISCORD_TOKEN環境変数が設定されていません。")
    else:
        client.run(TOKEN)