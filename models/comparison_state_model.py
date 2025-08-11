from sqlite3 import Connection

class ComparisonStateModel:
    def __init__(self, conn : Connection):
        self.conn = conn

    def save_comparison_state(self, unrated_music_id, compared_music_id, range_index):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO comparison_state (unrated_music_id, compared_music_id, range_index)
            VALUES (?, ?, ?)
        ''', (unrated_music_id, compared_music_id, range_index))
        self.conn.commit()

    def get_comparison_state(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT unrated_music_id, compared_music_id, range_index FROM comparison_state LIMIT 1')
        return cursor.fetchone()

    def clear_comparison_state(self, unrated_music_id=None):
        cursor = self.conn.cursor()
        if unrated_music_id is not None:
            cursor.execute('DELETE FROM comparison_state WHERE unrated_music_id = ?', (unrated_music_id,))
        else:
            cursor.execute('DELETE FROM comparison_state')
        self.conn.commit()