import sqlite3
from typing import Optional


class Database:
    def __init__(self):
        self.con = sqlite3.connect('tweets.db')
        self.create_db()

    def create_db(self):
        cur = self.con.cursor()
        cur.execute(f'''
        CREATE TABLE IF NOT EXISTS Tweets
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            tweet_timestamp DATETIME,
            sender_id TEXT,
            sender_display_name TEXT,
            message BLOB,
            message_lang TEXT,
            screenshot BLOB,
            likes INTEGER DEFAULT 0,
            comments INTEGER,
            tweet_href TEXT
            verified_account INTEGER DEFAULT 0
        );
        ''')
        self.con.commit()

    def insert_tweet(self, timestamp: Optional[str], tweet_timestamp: Optional[str], sender_id: Optional, message: Optional,
                     message_lang: Optional, sender_display_name: Optional, tweet_href: Optional,
                     screenshot_img_path: Optional, likes: Optional[str], verified_account: Optional[bool]):
        sql = '''
        INSERT INTO Tweets 
        (
            timestamp, 
            tweet_timestamp, 
            sender_id, 
            message, 
            screenshot, 
            message_lang, 
            sender_display_name, 
            tweet_href,
            likes,
            verified_account
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''
        if screenshot_img_path:
            with open(screenshot_img_path, "rb") as file:
                _screenshot_binary = sqlite3.Binary(file.read())
        else:
            _screenshot_binary = None

        cur = self.con.cursor()
        cur.execute(sql, [timestamp, tweet_timestamp, sender_id, message, _screenshot_binary, message_lang,
                          sender_display_name, tweet_href, likes, verified_account])
        self.con.commit()
