from sqlite3 import Connection
from pathlib import Path
from send2trash import send2trash

class MusicModel:
    def __init__(self, conn: Connection):
        self.conn = conn

    def add_music(self, path):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO music (path) VALUES (?)', (path,))
        self.conn.commit()

    def get_unrated_musics(self):
        """
        Retorna músicas que ainda não foram classificadas.
        Músicas com stars = -1 são consideradas puladas e não são retornadas.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path FROM music WHERE stars = 0')  # Apenas músicas não classificadas
        return cursor.fetchall()

    def get_two_unrated_musics(self):
        """
        Retorna duas músicas não classificadas diferentes para comparação inicial.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE stars = 0 LIMIT 2')
        results = cursor.fetchall()
        if len(results) >= 2:
            return [
                {'id': results[0][0], 'path': results[0][1], 'stars': results[0][2]},
                {'id': results[1][0], 'path': results[1][1], 'stars': results[1][2]}
            ]
        return None

    def get_last_music_with_stars(self, star_level):
        """
        Retorna a última música classificada com o nível de estrelas especificado.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE stars = ? ORDER BY id DESC LIMIT 1', (star_level,))
        result = cursor.fetchone()
        if result:
            return {'id': result[0], 'path': result[1], 'stars': result[2]}
        return None

    def update_stars(self, music_id, stars):
        """
        Atualiza a quantidade de estrelas de uma música.
        :param music_id: ID da música.
        :param stars: Quantidade de estrelas (1 a 5).
        """
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

    def get_filtered_musics(self, tag_filter=None, min_stars=None, max_stars=None):
        """
        Retorna músicas filtradas por tags e quantidade de estrelas.
        """
        cursor = self.conn.cursor()

        # Construir a consulta SQL dinamicamente
        query = '''
            SELECT m.id, m.path, m.stars FROM music m
        '''
        params = []

        # Adicionar filtro por tags, se necessário
        if tag_filter:
            query += '''
                JOIN music_tags mt ON m.id = mt.music_id
                JOIN tags t ON t.id = mt.tag_id
                WHERE t.name = ?
            '''
            params.append(tag_filter)
        else:
            query += 'WHERE stars > -1'  # Exclui músicas puladas (-1)

        # Adicionar filtro por estrelas, se necessário
        if min_stars is not None:
            query += ' AND m.stars >= ?'
            params.append(min_stars)
        if max_stars is not None:
            query += ' AND m.stars <= ?'
            params.append(max_stars)

        # Executar a consulta
        cursor.execute(query, params)
        results = cursor.fetchall()

        # Retornar como uma lista de dicionários
        return [{'id': row[0], 'path': row[1], 'stars': row[2]} for row in results]

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

    def get_music_by_stars(self, stars, exclude_id=None):
        cursor = self.conn.cursor()
        if exclude_id:
            cursor.execute('SELECT id, path, stars FROM music WHERE stars = ? AND id != ?', (stars, exclude_id))
        else:
            cursor.execute('SELECT id, path, stars FROM music WHERE stars = ?', (stars,))
        results = cursor.fetchall()
        return [{'id': row[0], 'path': row[1], 'stars': row[2]} for row in results]

    def get_music_details(self, music_id):
        """
        Retorna os detalhes de uma música com base no ID.
        :param music_id: ID da música.
        :return: Um dicionário com os detalhes da música (id, path, stars).
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE id = ?', (music_id,))
        result = cursor.fetchone()
        if result:
            return {'id': result[0], 'path': result[1], 'stars': result[2]}
        return None

    def get_next_unrated_music(self, exclude_id=None):
        """
        Retorna a próxima música não classificada, excluindo uma música específica.
        Músicas com stars = -1 são consideradas puladas e não são retornadas.
        """
        cursor = self.conn.cursor()
        if exclude_id is not None:
            cursor.execute('SELECT id, path, stars FROM music WHERE stars = 0 AND id != ? LIMIT 1', (exclude_id,))
        else:
            cursor.execute('SELECT id, path, stars FROM music WHERE stars = 0 LIMIT 1')
        result = cursor.fetchone()
        if result:
            return {'id': result[0], 'path': result[1], 'stars': result[2]}
        return None

    def get_total_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM music')
        return cursor.fetchone()[0]

    def get_rated_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM music WHERE stars > 0')
        return cursor.fetchone()[0]
