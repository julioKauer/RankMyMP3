from sqlite3 import Connection
from pathlib import Path
from send2trash import send2trash

class MusicModel:
    def __init__(self, conn: Connection):
        self.conn = conn

    def add_music(self, path):
        cursor = self.conn.cursor()
        # Verificar se a música já existe
        cursor.execute('SELECT id FROM music WHERE path = ?', (path,))
        existing = cursor.fetchone()
        
        if existing:
            return existing[0]  # Retornar ID da música existente
        else:
            cursor.execute('INSERT INTO music (path) VALUES (?)', (path,))
            self.conn.commit()
            return cursor.lastrowid  # Retornar ID da música recém-criada

    def get_unrated_musics(self):
        """
        Retorna músicas que ainda não foram classificadas.
        Músicas com stars = -1 são consideradas puladas e não são retornadas.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE stars = 0')
        results = cursor.fetchall()
        
        music_list = [{'id': row[0], 'path': row[1], 'stars': row[2]} for row in results]
        
        return music_list

    def get_ignored_musics(self):
        """
        Retorna músicas ignoradas (stars = -1).
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE stars = -1')
        results = cursor.fetchall()
        
        music_list = [{'id': row[0], 'path': row[1], 'stars': row[2]} for row in results]
        
        return music_list

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
        elif len(results) == 1:
            return [{'id': results[0][0], 'path': results[0][1], 'stars': results[0][2]}]
        return []

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

    def update_music_path(self, music_id, new_path):
        """
        Atualiza o caminho de uma música no banco de dados.
        :param music_id: ID da música.
        :param new_path: Novo caminho completo do arquivo.
        :return: True se a atualização foi bem-sucedida, False caso contrário.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE music SET path = ? WHERE id = ?', (new_path, music_id))
            self.conn.commit()
            
            # Verificar se a linha foi realmente atualizada
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar caminho da música: {e}")
            return False

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

        # Ordenar por estrelas em ordem decrescente
        query += ' ORDER BY m.stars DESC'

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

    def get_all_classified_musics(self):
        """
        Retorna todas as músicas classificadas (stars > 0) ordenadas por estrelas descendente e depois por ID.
        Isso garante que músicas de mesmo nível mantenham ordem de classificação.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE stars > 0 ORDER BY stars DESC, id ASC')
        results = cursor.fetchall()
        return [{'id': row[0], 'path': row[1], 'stars': row[2]} for row in results]

    def get_all_classified_musics_by_quality(self):
        """
        Retorna todas as músicas classificadas ordenadas por qualidade real.
        Para preservar a ordem real do ranking baseado nas comparações,
        precisamos reconstruir o ranking a partir das comparações, não apenas ordenar por estrelas.
        """
        from models.comparison_model import ComparisonModel
        comparison_model = ComparisonModel(self.conn)
        
        # Reconstruir o ranking real baseado nas comparações
        ranking = self._build_ranking_from_comparisons(comparison_model)
        
        if not ranking:
            # Fallback: ordenar por estrelas e ID se não há comparações
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, path, stars FROM music WHERE stars > 0 ORDER BY stars DESC, id ASC')
            results = cursor.fetchall()
            return [{'id': row[0], 'path': row[1], 'stars': row[2]} for row in results]
        
        # Obter detalhes das músicas na ordem real do ranking
        result = []
        for music_id in ranking:
            details = self.get_music_details(music_id)
            if details and details['stars'] > 0:  # Apenas músicas classificadas
                result.append(details)
        
        return result
    
    def _build_ranking_from_comparisons(self, comparison_model):
        """
        Reconstrói o ranking baseado nas comparações existentes.
        """
        from collections import defaultdict, deque
        
        # Obter todas as comparações
        comparisons = comparison_model.get_comparisons()
        if not comparisons:
            return []
        
        # Construir grafo direcionado baseado nas comparações
        graph = defaultdict(list)  # vencedor -> [perdedores]
        in_degree = defaultdict(int)  # quantas músicas são melhores que esta
        all_musics = set()
        
        for music_a, music_b, winner in comparisons:
            loser = music_b if winner == music_a else music_a
            all_musics.add(music_a)
            all_musics.add(music_b)
            
            # Evitar duplicatas
            if loser not in graph[winner]:
                graph[winner].append(loser)
                in_degree[loser] += 1
            
            # Inicializar in_degree para vencedores
            if winner not in in_degree:
                in_degree[winner] = 0
        
        # Ordenação topológica para encontrar a ordem
        queue = deque([music for music in all_musics if in_degree[music] == 0])
        ranking = []
        
        while queue:
            current = queue.popleft()
            ranking.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return ranking

    def get_music_tags(self, music_id):
        """Retorna as tags de uma música."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.name 
            FROM tags t
            JOIN music_tags mt ON t.id = mt.tag_id
            WHERE mt.music_id = ?
            ORDER BY t.name
        ''', (music_id,))
        
        return [row[0] for row in cursor.fetchall()]

    def remove_tag_from_music(self, music_id, tag_name):
        """Remove uma tag específica de uma música."""
        cursor = self.conn.cursor()
        
        # Primeiro, obter o ID da tag
        cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
        tag_result = cursor.fetchone()
        
        if tag_result:
            tag_id = tag_result[0]
            # Remover associação
            cursor.execute('DELETE FROM music_tags WHERE music_id = ? AND tag_id = ?', (music_id, tag_id))
            self.conn.commit()

    def get_music_by_id(self, music_id):
        """Retorna informações de uma música pelo ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, stars FROM music WHERE id = ?', (music_id,))
        result = cursor.fetchone()
        
        if result:
            return {'id': result[0], 'path': result[1], 'stars': result[2]}
        return None

    def get_all_tags(self):
        """Retorna todas as tags disponíveis."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM tags ORDER BY name')
        return [row[0] for row in cursor.fetchall()]
