import os
import threading
from .bot import bot
from .webhook import run_flask

def main():
    # 環境変数チェック
    required_vars = [
        'DISCORD_TOKEN', 'FORGEJO_URL', 'FORGEJO_TOKEN',
        'REPO_OWNER', 'REPO_NAME', 'DISCORD_CHANNEL_ID'
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        exit(1)

    # Flaskを別スレッドで起動
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Discord botを起動
    bot.run(os.getenv('DISCORD_TOKEN'))
if __name__ == "__main__":
    main()