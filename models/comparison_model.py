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

    def get_comparison_result(self, music_a_id, music_b_id):
        """
        Retorna o resultado de uma comparação específica.
        Retorna None se não houver comparação entre as músicas.
        """
        # Normalizar ordem
        if music_a_id > music_b_id:
            music_a_id, music_b_id = music_b_id, music_a_id
            
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT winner_id FROM comparisons 
            WHERE music_a_id = ? AND music_b_id = ?
        ''', (music_a_id, music_b_id))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_all_comparisons_for_music(self, music_id):
        """
        Retorna todas as comparações que envolvem uma música específica.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT music_a_id, music_b_id, winner_id FROM comparisons 
            WHERE music_a_id = ? OR music_b_id = ?
        ''', (music_id, music_id))
        return cursor.fetchall()

    def get_defeated_by_music(self, music_id):
        """
        Retorna lista de IDs de músicas derrotadas por uma música específica.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT CASE 
                WHEN music_a_id = ? THEN music_b_id 
                ELSE music_a_id 
            END as defeated_id
            FROM comparisons 
            WHERE (music_a_id = ? OR music_b_id = ?) AND winner_id = ?
        ''', (music_id, music_id, music_id, music_id))
        return [row[0] for row in cursor.fetchall()]

    def get_winners_against_music(self, music_id):
        """
        Retorna lista de IDs de músicas que derrotaram uma música específica.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT winner_id FROM comparisons 
            WHERE (music_a_id = ? OR music_b_id = ?) AND winner_id != ?
        ''', (music_id, music_id, music_id))
        return [row[0] for row in cursor.fetchall()]

    def remove_comparisons_for_music(self, music_id):
        """
        Remove todas as comparações que envolvem uma música específica.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM comparisons 
            WHERE music_a_id = ? OR music_b_id = ?
        ''', (music_id, music_id))
        self.conn.commit()