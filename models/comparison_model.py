from sqlite3 import Connection

class ComparisonModel:
    def __init__(self, conn : Connection):
        self.conn = conn

    def save_comparison(self, music_a_id, music_b_id, winner_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO comparisons (music_a_id, music_b_id, winner_id)
            VALUES (?, ?, ?)
        ''', (music_a_id, music_b_id, winner_id))
        self.conn.commit()

    def get_comparisons(self):
        """
        Retorna todas as comparações registradas.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT music_a_id, music_b_id, winner_id FROM comparisons')
        return cursor.fetchall()