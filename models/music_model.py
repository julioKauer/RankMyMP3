import sqlite3
from pathlib import Path
from send2trash import send2trash

class MusicModel:
    def __init__(self, db_path="data/music_ranking.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                stars INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_tags (
                music_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY(music_id) REFERENCES music(id),
                FOREIGN KEY(tag_id) REFERENCES tags(id),
                UNIQUE(music_id, tag_id)
            )
        ''')
        self.conn.commit()

    def add_music(self, path):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO music (path) VALUES (?)', (path,))
        self.conn.commit()

    def get_unrated_musics(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path FROM music WHERE stars = 0')
        return cursor.fetchall()

    def update_stars(self, music_id, stars):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE music SET stars = ? WHERE id = ?', (stars, music_id))
        self.conn.commit()

    def delete_music(self, music_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT path FROM music WHERE id = ?', (music_id,))
        path = cursor.fetchone()[0]
        if path and Path(path).exists():
            send2trash(path)
        cursor.execute('DELETE FROM music WHERE id = ?', (music_id,))
        self.conn.commit()

    def get_ranking(self, tag_filter=None):
        cursor = self.conn.cursor()
        if tag_filter:
            cursor.execute('''
                SELECT m.path, m.stars FROM music m
                JOIN music_tags mt ON m.id = mt.music_id
                JOIN tags t ON t.id = mt.tag_id
                WHERE t.name = ?
                ORDER BY m.stars DESC
            ''', (tag_filter,))
        else:
            cursor.execute('SELECT path, stars FROM music ORDER BY stars DESC')
        return cursor.fetchall()

    def add_tag(self, tag_name):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
        self.conn.commit()

    def associate_tag(self, music_id, tag_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
        tag_id = cursor.fetchone()
        if tag_id:
            cursor.execute('INSERT OR IGNORE INTO music_tags (music_id, tag_id) VALUES (?, ?)', (music_id, tag_id[0]))
            self.conn.commit()

    def get_music_by_tag(self, tag_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.path, m.stars FROM music m
            JOIN music_tags mt ON m.id = mt.music_id
            JOIN tags t ON t.id = mt.tag_id
            WHERE t.name = ?
        ''', (tag_name,))
        return cursor.fetchall()