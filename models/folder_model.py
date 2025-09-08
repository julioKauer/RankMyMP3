import sqlite3

class FolderModel:
    def __init__(self, db_path="data/music_ranking.db"):
        self.db_path = db_path

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

    def folder_exists(self, folder_path):
        """Check if a folder already exists in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM folders WHERE path = ?", (folder_path,))
            return cursor.fetchone()[0] > 0

    def get_folder_count(self):
        """Get the total number of folders."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM folders")
            return cursor.fetchone()[0]

    def clear_all_folders(self):
        """Remove all folders from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM folders")
            conn.commit()