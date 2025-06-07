import os
import asyncio
from flask import Flask, request, jsonify
import threading

from .bot import bot, send_issue_notification, send_comment_notification

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

app = Flask(__name__)

def verify_signature(data, signature, secret):
    # TODO: 実装（現状は常にTrueを返すダミー）
    return True

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
            asyncio.run_coroutine_threadsafe(
                send_issue_notification(action, issue),
                bot.loop
            )
        elif action == 'created' and 'comment' in data:
            print("コメント通知分岐")
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

def run_flask():
    """Flaskアプリを別スレッドで実行"""
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Flask webhook server starting on {host}:{port}")
    print(f"📡 Webhook URL: http://192.168.0.131:{port}/webhook/forgejo")
    
    app.run(host=host, port=port, debug=debug)