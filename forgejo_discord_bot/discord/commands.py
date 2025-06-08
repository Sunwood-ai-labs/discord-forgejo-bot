import os
import discord
from discord.ext import commands
from ..forgejo.api import ForgejoAPI
from ..database.models import (
    set_repository_channel,
    get_repository_channels
)


# 設定
FORGEJO_URL = os.getenv('FORGEJO_URL')
FORGEJO_TOKEN = os.getenv('FORGEJO_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')

forgejo = ForgejoAPI(FORGEJO_URL, FORGEJO_TOKEN)


def setup_commands(bot):
    """スラッシュコマンドを設定"""
    
    @bot.tree.command(name="issue", description="Forgejoにissueを作成します")
    async def create_issue_command(
        interaction: discord.Interaction,
        title: str,
        description: str,
        assignee: str = None,
        repo: str = None
    ):
        """Discord slash commandでissue作成"""
        await interaction.response.defer()
        try:
            # デフォルトrepo名はチャンネル名
            repo_name = repo if repo else interaction.channel.name
            author_info = f"\n\n---\n**作成者:** {interaction.user.mention} ({interaction.user.name})\n**Discord ID:** {interaction.user.id}"
            full_description = description + author_info
            issue = await forgejo.create_issue(
                owner=REPO_OWNER,
                repo=repo_name,
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
            embed.add_field(name="リポジトリ", value=f"{REPO_OWNER}/{repo_name}", inline=True)
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

    @bot.tree.command(name="set_repo_channel", description="リポジトリの通知チャンネルを設定します")
    async def set_repo_channel_command(
        interaction: discord.Interaction,
        repository: str,
        channel: discord.TextChannel = None
    ):
        """リポジトリの通知チャンネルを設定"""
        await interaction.response.defer()
        try:
            # チャンネルが指定されていない場合は現在のチャンネルを使用
            target_channel = channel if channel else interaction.channel
            
            # 設定を保存
            success = set_repository_channel(repository, target_channel.id, interaction.guild.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ リポジトリチャンネル設定完了",
                    description=f"リポジトリ `{repository}` の通知が {target_channel.mention} に送信されるようになりました。",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ エラー",
                    description="リポジトリチャンネル設定に失敗しました。",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ エラー",
                description=f"リポジトリチャンネル設定に失敗しました: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)

    @bot.tree.command(name="list_repo_channels", description="リポジトリチャンネルのマッピング一覧を表示します")
    async def list_repo_channels_command(interaction: discord.Interaction):
        """リポジトリチャンネルマッピング一覧を表示"""
        await interaction.response.defer()
        try:
            mappings = get_repository_channels()
            
            if not mappings:
                embed = discord.Embed(
                    title="📋 リポジトリチャンネルマッピング",
                    description="設定されているマッピングがありません。",
                    color=0xffa500
                )
            else:
                embed = discord.Embed(
                    title="📋 リポジトリチャンネルマッピング",
                    color=0x0099ff
                )
                
                for repository, channel_id, guild_id in mappings:
                    try:
                        channel = bot.get_channel(channel_id)
                        channel_name = channel.mention if channel else f"<#{channel_id}> (チャンネルが見つかりません)"
                        embed.add_field(
                            name=f"🔗 {repository}",
                            value=channel_name,
                            inline=False
                        )
                    except Exception:
                        embed.add_field(
                            name=f"🔗 {repository}",
                            value=f"<#{channel_id}> (エラー)",
                            inline=False
                        )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ エラー",
                description=f"リポジトリチャンネル一覧取得に失敗しました: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
