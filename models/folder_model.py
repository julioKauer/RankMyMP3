import sqlite3

class FolderModel:
    def __init__(self, db_path="data/music_ranking.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Create the folders table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL
                )
            """)
            conn.commit()

    def get_folders(self):
        """Retrieve all saved folders."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM folders")
            return [row[0] for row in cursor.fetchall()]

    def add_folder(self, folder_path):
        """Add a new folder to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO folders (path) VALUES (?)", (folder_path,))
            conn.commit()

    def remove_folder(self, folder_path):
        """Remove a folder from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM folders WHERE path = ?", (folder_path,))
            conn.commit()