import os
import requests
import secrets
import string

from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

FORGEJO_URL = os.getenv("FORGEJO_URL")
FORGEJO_TOKEN = os.getenv("FORGEJO_TOKEN")

# 作成するユーザー情報
USERNAME = "forgejo-discord-bot"
EMAIL = "forgejo-discord-bot@example.com"
# 一時パスワードをランダム生成
PASSWORD = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

def create_user():
    url = f"{FORGEJO_URL}/api/v1/admin/users"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {FORGEJO_TOKEN}"
    }
    data = {
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD,
        "must_change_password": True,
        "send_notify": False,
        "active": True,
        "visibility": "public"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"ユーザー '{USERNAME}' を作成しました。")
        print(f"一時パスワード: {PASSWORD}")
    else:
        print("ユーザー作成に失敗しました。")
        print("Status:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    create_user()