import os
import psycopg2


# PostgreSQL接続情報
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'forgejo_discord')
DB_USER = os.getenv('DB_USER', 'forgejo_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'forgejo_pass')


def get_db_conn():
    """PostgreSQL接続を取得"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def ensure_issue_threads_table():
    """データベーステーブルを作成"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS issue_threads (
                issue_number INTEGER PRIMARY KEY,
                thread_id BIGINT NOT NULL,
                repository VARCHAR(255) NOT NULL DEFAULT ''
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS repository_channels (
                repository VARCHAR(255) PRIMARY KEY,
                channel_id BIGINT NOT NULL,
                guild_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DBテーブル作成エラー: {e}")


def get_thread_id_from_db(issue_number):
    """Issue番号からスレッドIDを取得"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT thread_id FROM issue_threads WHERE issue_number = %s;", (issue_number,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"DB取得エラー: {e}")
        return None


def get_issue_number_from_thread_id(thread_id):
    """スレッドIDからIssue番号を取得"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT issue_number FROM issue_threads WHERE thread_id = %s;", (thread_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"DB取得エラー: {e}")
        return None


def set_thread_id_to_db(issue_number, thread_id, repository=None):
    """Issue番号とスレッドIDの対応を保存"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        if repository:
            cur.execute("""
                INSERT INTO issue_threads (issue_number, thread_id, repository)
                VALUES (%s, %s, %s)
                ON CONFLICT (issue_number) DO UPDATE SET 
                    thread_id = EXCLUDED.thread_id,
                    repository = EXCLUDED.repository;
            """, (issue_number, thread_id, repository))
        else:
            cur.execute("""
                INSERT INTO issue_threads (issue_number, thread_id)
                VALUES (%s, %s)
                ON CONFLICT (issue_number) DO UPDATE SET thread_id = EXCLUDED.thread_id;
            """, (issue_number, thread_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB保存エラー: {e}")


def get_channel_id_for_repository(repository):
    """リポジトリに対応するチャンネルIDを取得"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT channel_id FROM repository_channels WHERE repository = %s;", (repository,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"チャンネルID取得エラー: {e}")
        return None


def set_repository_channel(repository, channel_id, guild_id):
    """リポジトリとチャンネルの対応を設定"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO repository_channels (repository, channel_id, guild_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (repository) DO UPDATE SET 
                channel_id = EXCLUDED.channel_id,
                guild_id = EXCLUDED.guild_id;
        """, (repository, channel_id, guild_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"リポジトリチャンネル設定エラー: {e}")
        return False


def get_repository_channels():
    """すべてのリポジトリチャンネルマッピングを取得"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT repository, channel_id, guild_id FROM repository_channels;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"リポジトリチャンネル一覧取得エラー: {e}")
        return []
