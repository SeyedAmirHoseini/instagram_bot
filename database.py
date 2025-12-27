import sqlite3
from config import *

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS items 
                     (pk INTEGER PRIMARY KEY, category TEXT, name TEXT, link TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings 
                     (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS processed_ids 
                     (item_id TEXT PRIMARY KEY)''')

        defaults = [
            ('check_interval', str(CHECK_INTERVAL_COMMENTS)),
            ('posts_count', str(POSTS_TO_CHECK)),
            ('min_delay_dm', str(DELAY_RANGE_DM[0])),
            ('max_delay_dm', str(DELAY_RANGE_DM[1])),
        ]
        c.executemany("INSERT OR IGNORE INTO settings VALUES (?, ?)", defaults)
        conn.commit()

def get_setting(key, default=None):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone()
        return row[0] if row else default

def update_setting(key, value):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

def get_item(pk):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT category, name, link FROM items WHERE pk=?", (pk,))
        return c.fetchone()

def add_item(pk, category, name, link):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO items VALUES (?, ?, ?, ?)", (pk, category, name, link))
        conn.commit()

def is_processed(item_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM processed_ids WHERE item_id=?", (item_id,))
        return c.fetchone() is not None

def mark_processed(item_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO processed_ids VALUES (?)", (item_id,))
        conn.commit()