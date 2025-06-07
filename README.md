<div align="center">
  <img src="header.png" alt="header" width="100%"/>
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

## 📦 Dockerでの起動

```sh
git clone https://github.com/yourname/discord-forgejo-bot.git
cd discord-forgejo-bot
cp .env.example .env
# .envを編集して各種トークンやURLを設定
docker-compose up -d
```

- Flaskサーバはデフォルトでポート5000で待ち受けます（`.env`で変更可）。
- ForgejoのWebhookに `http://<サーバーIP>:5000/webhook/forgejo` を設定してください。

## ⚙️ 必要な環境変数

`.env.example` を参照してください。主な変数は以下の通りです。

- `DISCORD_TOKEN` ... Discord Botのトークン
- `FORGEJO_URL` ... ForgejoのURL（例: https://git.example.com）
- `FORGEJO_TOKEN` ... Forgejo APIトークン
- `REPO_OWNER` ... リポジトリオーナー
- `REPO_NAME` ... リポジトリ名
- `DISCORD_CHANNEL_ID` ... 通知を送るDiscordチャンネルID
- `WEBHOOK_SECRET` ... Webhookシークレット（任意）

## 📝 使い方

1. Discord Developer PortalでBotを作成し、トークンを取得
2. `.env` ファイルに各種トークンやURLを設定
3. DockerでBotを起動
4. ForgejoのWebhookを設定し、Discord通知を受け取る

### 💡 DiscordからForgejoにIssueを作成する

Discordのスラッシュコマンド `/issue` を使って、ForgejoにIssueを作成できます。

例:
```
/issue タイトル: バグ報告 本文: ボタンが動作しません
```
（実際のコマンドの引数形式はBotの実装に従ってください）

## 🗂️ ディレクトリ構成（主要部分）

```
forgejo_discord_bot/
  ├── __init__.py
  ├── __main__.py
  ├── bot.py
  ├── cli.py
  ├── forgejo_api.py
  └── webhook.py
docker-compose.yml
Dockerfile
.env.example
README.md
```

## 📁 サンプル
サンプルBotや設定例は [example/README.md](./example/README.md) を参照してください。

## 🖼️ スクリーンショット
<!-- 必要に応じて動作例の画像をここに追加 -->

## 📝 ライセンス
本プロジェクトはMITライセンスです。
## インストール

依存パッケージはすべて `pyproject.toml` で管理されています。
以下のコマンドでパッケージと依存関係をまとめてインストールできます。

```sh
pip install .
```