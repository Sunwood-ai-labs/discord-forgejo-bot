import os
import asyncio
from loguru import logger
from dotenv import load_dotenv

import discord
from discord.ext import commands

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from forgejo_discord_bot.forgejo_api import ForgejoAPI

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FORGEJO_URL = os.getenv("FORGEJO_URL")
FORGEJO_TOKEN = os.getenv("FORGEJO_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")

if not all([DISCORD_TOKEN, FORGEJO_URL, FORGEJO_TOKEN, REPO_OWNER]):
    logger.error("必要な環境変数が不足しています。")
    exit(1)

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def get_repos():
    api = ForgejoAPI(FORGEJO_URL, FORGEJO_TOKEN)
    # org or user
    url_org = f"{FORGEJO_URL}/api/v1/orgs/{REPO_OWNER}/repos"
    url_user = f"{FORGEJO_URL}/api/v1/users/{REPO_OWNER}/repos"
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url_org, headers=api.headers) as resp:
            if resp.status == 200:
                return [repo["name"] for repo in await resp.json()]
        async with session.get(url_user, headers=api.headers) as resp:
            if resp.status == 200:
                return [repo["name"] for repo in await resp.json()]
    logger.error("リポジトリ一覧の取得に失敗しました。")
    return []

@bot.event
async def on_ready():
    logger.info(f"Botログイン: {bot.user}")
    if not bot.guilds:
        logger.error("Botが参加しているサーバーがありません。")
        await bot.close()
        return
    guild = bot.guilds[0]
    logger.info(f"対象ギルド: {guild.name} ({guild.id})")

    repo_names = await get_repos()
    logger.info(f"Forgejoリポジトリ一覧: {repo_names}")

    existing_channels = {ch.name for ch in guild.text_channels}
    logger.info(f"既存チャンネル: {existing_channels}")

    # REPO_OWNER名のカテゴリを取得または作成
    category = discord.utils.get(guild.categories, name=REPO_OWNER)
    if category:
        logger.info(f"既存カテゴリを使用: {category.name}")
    else:
        try:
            category = await guild.create_category(REPO_OWNER)
            logger.success(f"カテゴリ作成: {REPO_OWNER}")
        except Exception as e:
            logger.error(f"カテゴリ作成失敗: {REPO_OWNER} - {e}")
            await bot.close()
            return

    # カテゴリ内の既存チャンネル名
    category_channel_names = {ch.name for ch in category.text_channels}
    logger.info(f"カテゴリ内既存チャンネル: {category_channel_names}")

    # 新規チャンネル作成
    for repo_name in repo_names:
        if repo_name in category_channel_names:
            logger.info(f"既存チャンネルのためスキップ: {repo_name}")
            continue
        try:
            await guild.create_text_channel(repo_name, category=category)
            logger.success(f"チャンネル作成: {repo_name}")
        except Exception as e:
            logger.error(f"チャンネル作成失敗: {repo_name} - {e}")

    await bot.close()

if __name__ == "__main__":
    asyncio.run(bot.start(DISCORD_TOKEN))
