<div align="center">
  <img src="header.png" alt="header" width="600"/>
  <h1>discord-forgejo-bot</h1>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10-blue?logo=python">
    <img src="https://img.shields.io/badge/Docker-enabled-blue?logo=docker">
    <img src="https://img.shields.io/badge/Discord-Bot-5865F2?logo=discord">
  </p>
</div>

## 🚀 概要
ForgejoとDiscordを連携するBotです。プルリクやIssueの通知をDiscordに送信します。  
さらに、**Discordのスラッシュコマンド（`/issue`）でForgejoにIssueを作成することも可能です。**

## 📦 インストール

```sh
git clone https://github.com/yourname/discord-forgejo-bot.git
cd discord-forgejo-bot
cp .env.example .env
# 必要に応じて.envを編集
docker-compose up -d
```

## 📝 使い方

1. Discord Developer PortalでBotを作成し、トークンを取得
2. .envファイルに各種トークンやURLを設定
3. DockerまたはローカルでBotを起動
4. ForgejoのWebhookを設定し、Discord通知を受け取る

### 💡 DiscordからForgejoにIssueを作成する

Discordのスラッシュコマンド `/issue` を使って、ForgejoにIssueを作成できます。

例:
```
/issue タイトル: バグ報告 本文: ボタンが動作しません
```
（実際のコマンドの引数形式はBotの実装に従ってください）

## 📁 サンプル
サンプルBotや設定例は [example/README.md](./example/README.md) を参照してください。

## 🖼️ スクリーンショット
<!-- 必要に応じて動作例の画像をここに追加 -->

## 📝 ライセンス
本プロジェクトはMITライセンスです。