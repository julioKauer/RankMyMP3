from sqlite3 import Connection

class ComparisonModel:
    def __init__(self, conn : Connection):
        self.conn = conn

    def save_comparison(self, music_a_id, music_b_id, winner_id):
        """
        Salva uma comparação entre duas músicas.
        Normaliza a ordem para sempre salvar o menor ID primeiro,
        evitando duplicatas como (1,2) e (2,1).
        """
        # Normalizar: sempre colocar o menor ID primeiro
        if music_a_id > music_b_id:
            music_a_id, music_b_id = music_b_id, music_a_id
            
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