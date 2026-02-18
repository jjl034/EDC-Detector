import sqlite3
from pathlib import Path

DB_FILE = Path.home() / "EDC-Detector" / "data" / "edc.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Users table
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
        """)
        # Items table
        c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            desc TEXT,
            mac TEXT
        )
        """)
        # Events table
        c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            timestamp TEXT
        )
        """)
        self.conn.commit()

    # --- User methods ---
    def create_user(self, email, password):
        try:
            self.conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            self.conn.commit()
            return True
        except:
            return False

    def verify_user(self, email, password):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        return c.fetchone() is not None

    # --- Items methods ---
    def add_item(self, name, desc, mac):
        self.conn.execute("INSERT INTO items (name, desc, mac) VALUES (?, ?, ?)", (name, desc, mac.lower()))
        self.conn.commit()

    def update_item(self, item_id, name, desc, mac):
        self.conn.execute("UPDATE items SET name=?, desc=?, mac=? WHERE id=?", (name, desc, mac.lower(), item_id))
        self.conn.commit()

    def delete_item(self, item_id):
        self.conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def get_items(self):
        c = self.conn.cursor()
        c.execute("SELECT id, name, desc, mac FROM items ORDER BY id")
        return c.fetchall()

    # --- Events methods ---
    def add_event(self, level, event, timestamp):
        self.conn.execute("INSERT INTO events (level, event, timestamp) VALUES (?, ?, ?)", (level, event, timestamp))
        self.conn.commit()

    def GetEvents(self):
        c = self.conn.cursor()
        c.execute("SELECT level, event, timestamp FROM events ORDER BY id")
        return c.fetchall()
