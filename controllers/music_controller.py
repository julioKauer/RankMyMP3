import os
import networkx as nx
from sqlite3 import Connection
from models.music_model import MusicModel
from models.comparison_model import ComparisonModel
from models.comparison_state_model import ComparisonStateModel

class MusicController:
    def __init__(self, conn: Connection):
        """
        Inicializa o controlador de música.
        :param conn: Conexão com o banco de dados.
        """
        self.conn = conn
        # Inicializar os modelos
        self.music_model = MusicModel(conn)
        self.comparison_model = ComparisonModel(conn)
        self.comparison_state_model = ComparisonStateModel(conn)

        self.graph = nx.DiGraph()  # Grafo direcionado para representar as relações de preferência
        self.load_comparisons_into_graph()

    def load_comparisons_into_graph(self):
        """
        Carrega as comparações do banco de dados para o grafo.
        """
        self.graph.clear()  # Limpa o grafo atual
        comparisons = self.comparison_model.get_comparisons()
        for music_a_id, music_b_id, winner_id in comparisons:
            if winner_id == music_a_id:
                self.graph.add_edge(music_a_id, music_b_id)  # A > B
            elif winner_id == music_b_id:
                self.graph.add_edge(music_b_id, music_a_id)  # B > A

    def update_ranking(self):
        """Atualiza o ranking baseado na ordenação topológica do grafo."""
        try:
            # Ordenação topológica
            ordered_music_ids = list(nx.topological_sort(self.graph))

            # Atualiza as estrelas no banco de dados
            total = len(ordered_music_ids)
            for index, music_id in enumerate(ordered_music_ids):
                # Calcula estrelas com base na posição (20% por faixa)
                stars = 5 - (index * 5 // total)
                self.music_model.update_stars(music_id, stars)
        except nx.NetworkXUnfeasible:
            raise ValueError("O grafo de comparações não é um DAG válido!")

    def is_music_rated(self, music_id):
        """
        Verifica se uma música já foi classificada.
        :param music_id: ID da música a verificar
        :return: True se a música já foi classificada, False caso contrário
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT stars FROM music WHERE id = ?', (music_id,))
        result = cursor.fetchone()
        if result is None:
            return False
        stars = result[0]
        return stars is not None and stars > 0  # Não classificada = 0, Pulada = -1, Classificada > 0

    def get_representative_music(self, range_index, exclude_id=None):
        """
        Obtém uma música representativa para um determinado range.
        :param range_index: Índice do range (1 a 5)
        :param exclude_id: ID da música a ser excluída da seleção
        :return: ID da música representativa ou None se não houver música disponível
        """
        # Obtém músicas com o número de estrelas correspondente ao range
        musics = self.music_model.get_music_by_stars(range_index, exclude_id)
        if not musics:
            return None
        
        # Por enquanto, retorna a primeira música do range
        # Pode ser melhorado para escolher uma música mais representativa
        return musics[0]['id']

    def add_music_folder(self, folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.mp3'):
                    self.music_model.add_music(os.path.join(root, file))

    def classify_music(self, music_id, stars):
        self.music_model.update_stars(music_id, stars)

    def delete_music(self, music_id):
        self.music_model.delete_music(music_id)

    def get_ranking(self, tag_filter=None, max_stars=None):
        """
        Retorna o ranking das músicas baseado nas comparações registradas.
        Permite filtrar por tags e por quantidade de estrelas.
        Retorna apenas músicas efetivamente classificadas (stars > 0).
        """
        # Obter músicas filtradas, apenas classificadas (stars > 0)
        musics = self.music_model.get_filtered_musics(tag_filter, min_stars=1, max_stars=max_stars)

        # Construir o grafo de comparações
        graph = nx.DiGraph()
        for music in musics:
            graph.add_node(music['id'])

        comparisons = self.comparison_model.get_comparisons()
        for music_a_id, music_b_id, winner_id in comparisons:
            if winner_id == music_a_id:
                graph.add_edge(music_a_id, music_b_id)  # A > B
            elif winner_id == music_b_id:
                graph.add_edge(music_b_id, music_a_id)  # B > A

        # Ordenar as músicas usando ordenação topológica
        try:
            sorted_music_ids = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("O grafo contém ciclos, o que indica inconsistências nas comparações.")

        # Mapear IDs para informações das músicas
        music_map = {m['id']: m for m in musics}
        ranked_musics = [music_map[music_id] for music_id in sorted_music_ids if music_id in music_map]

        return ranked_musics

    def add_music_folder(self, folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.mp3'):
                    self.music_model.add_music(os.path.join(root, file))

    def classify_music(self, music_id, stars):
        self.music_model.update_stars(music_id, stars)

    def delete_music(self, music_id):
        self.music_model.delete_music(music_id)

    def get_next_comparison(self):
        """
        Obtém a próxima comparação a ser realizada usando estratégia descendente.
        Retorna os IDs das músicas a serem comparadas e o nível de estrelas atual (5 para 1).
        :return: (unrated_music_id, compared_music_id, star_level) ou None se não houver músicas.
        """
        # Verificar se há um estado de comparação salvo
        state = self.comparison_state_model.get_comparison_state()
        if state:
            unrated_music_id, compared_music_id, star_level = state
            # Buscar música representativa para o nível atual
            representative_music = self.music_model.get_last_music_with_stars(star_level)
            if representative_music:
                return unrated_music_id, representative_music['id'], star_level
            else:
                # Se não há música representativa neste nível, desce um nível
                if star_level > 1:
                    self.comparison_state_model.save_comparison_state(unrated_music_id, None, star_level - 1)
                    return self.get_next_comparison()
                else:
                    # Se chegou ao nível 1 sem representativo, classifica como 1 estrela
                    self.classify_music(unrated_music_id, 1)
                    self.comparison_state_model.clear_comparison_state()
                    # Buscar a próxima música após classificar esta
                    return self._get_new_comparison()
        else:
            # Iniciar uma nova comparação
            return self._get_new_comparison()

    def _get_new_comparison(self):
        """Método auxiliar para buscar uma nova comparação."""
        try:
            # Verificar se há músicas classificadas
            ranked_musics = self.get_ranking()
        except:
            # Se der erro no ranking, assumir que não há músicas classificadas
            ranked_musics = []
            
        if not ranked_musics:
            # Se não há músicas classificadas, buscar duas músicas não classificadas
            two_unrated = self.music_model.get_two_unrated_musics()
            if not two_unrated or len(two_unrated) < 2:
                return None  # Não há músicas suficientes para comparar
            
            # Para a primeira comparação, usar nível 3 (neutro)
            unrated_music_id = two_unrated[0]['id']
            compared_music_id = two_unrated[1]['id']
            self.comparison_state_model.save_comparison_state(unrated_music_id, compared_music_id, 3)
            return unrated_music_id, compared_music_id, 3

        # Se há músicas classificadas, buscar uma música não classificada
        unrated_music = self.music_model.get_next_unrated_music()
        if not unrated_music:
            return None  # Não há músicas não classificadas

        unrated_music_id = unrated_music['id']
        # Começar sempre do nível 5 estrelas (estratégia descendente)
        star_level = 5
        representative_music = self.music_model.get_last_music_with_stars(star_level)
        
        if representative_music:
            self.comparison_state_model.save_comparison_state(unrated_music_id, representative_music['id'], star_level)
            return unrated_music_id, representative_music['id'], star_level
        else:
            # Se não há música de 5 estrelas, desce para 4, etc.
            for level in range(4, 0, -1):
                representative_music = self.music_model.get_last_music_with_stars(level)
                if representative_music:
                    self.comparison_state_model.save_comparison_state(unrated_music_id, representative_music['id'], level)
                    return unrated_music_id, representative_music['id'], level
            
            # Se não há músicas classificadas em nenhum nível, classificar como 1 estrela
            self.classify_music(unrated_music_id, 1)
            return None

    def get_last_music_with_stars(self, star_level):
        """Retorna a última música classificada com o nível de estrelas especificado."""
        return self.music_model.get_last_music_with_stars(star_level)

    def try_next_star_level(self, unrated_music_id, star_level):
        """Tenta o próximo nível de estrelas ou finaliza se chegou ao fim."""
        if star_level < 1:
            # Se chegou abaixo de 1 estrela, classifica como 1 estrela
            self.classify_music(unrated_music_id, 1)
            self.comparison_state_model.clear_comparison_state()
            return None
        else:
            # Continua com o próximo nível
            representative_music = self.music_model.get_last_music_with_stars(star_level)
            
            if representative_music:
                self.comparison_state_model.save_comparison_state(unrated_music_id, representative_music['id'], star_level)
                return unrated_music_id, representative_music['id'], star_level
            else:
                # Se não há música representativa neste nível, desce mais um
                return self.try_next_star_level(unrated_music_id, star_level - 1)

    def finalize_classification(self, unrated_music_id):
        """
        Finaliza a classificação de uma música não classificada.
        Recalcula a ordenação topológica do grafo e atualiza as estrelas de todas as músicas classificadas.
        :param unrated_music_id: ID da música não classificada.
        """
        # Atualizar o grafo com as comparações mais recentes
        self.load_comparisons_into_graph()

        # Recalcular a ordenação topológica
        try:
            ordered_music_ids = list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("O grafo contém ciclos, o que indica inconsistências nas comparações.")

        # Atualizar as estrelas no banco de dados com base na nova ordenação
        total = len(ordered_music_ids)
        for index, music_id in enumerate(ordered_music_ids):
            # Calcula estrelas com base na posição (20% por faixa)
            stars = 5 - (index * 5 // total)
            self.music_model.update_stars(music_id, stars)

        # Limpar o estado da comparação para a música não classificada
        self.comparison_state_model.clear_comparison_state(unrated_music_id)

    def add_comparison(self, music_a_id, music_b_id, winner_id):
        """
        Salva uma comparação após verificar se ela não cria ciclos no grafo.
        Ajusta a lógica para lidar com menos de 5 ranges.
        :param music_a_id: ID da primeira música.
        :param music_b_id: ID da segunda música.
        :param winner_id: ID da música vencedora.
        """
        # Construir o grafo atual
        graph = nx.DiGraph()
        comparisons = self.comparison_model.get_comparisons()
        for a_id, b_id, w_id in comparisons:
            if w_id == a_id:
                graph.add_edge(a_id, b_id)
            elif w_id == b_id:
                graph.add_edge(b_id, a_id)

        # Adicionar a nova comparação ao grafo
        loser_id = music_b_id if winner_id == music_a_id else music_a_id
        graph.add_edge(winner_id, loser_id)

        # Verificar se o grafo ainda é acíclico
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("A comparação criaria um ciclo no grafo.")

        # Salvar a comparação no banco de dados
        self.comparison_model.save_comparison(music_a_id, music_b_id, winner_id)

        # Atualizar o ranking
        self.update_ranking()

    def update_comparison_state(self, unrated_music_id, range_index):
        """
        Atualiza o estado de comparação para o próximo range.
        :param unrated_music_id: ID da música não classificada.
        :param range_index: Índice do próximo range.
        """
        # Tenta obter uma música representativa do range atual
        compared_music_id = self.get_representative_music(range_index, exclude_id=unrated_music_id)
        
        if not compared_music_id:
            # Se não encontrou no range atual, tenta o próximo range
            if not self.is_last_range(range_index):
                compared_music_id = self.get_representative_music(range_index + 1, exclude_id=unrated_music_id)
                if compared_music_id:
                    range_index += 1
            
            if not compared_music_id:
                raise ValueError("Não há músicas classificadas suficientes para continuar a comparação.")

        # Atualizar o estado no banco de dados
        self.comparison_state_model.save_comparison_state(unrated_music_id, compared_music_id, range_index)

    def clear_comparison_state(self):
        """
        Limpa o estado atual da comparação.
        """
        self.comparison_state_model.clear_comparison_state()

    def is_last_range(self, range_index):
        """
        Verifica se o range atual é o último.
        O número de ranges depende do número de músicas classificadas.
        :param range_index: Índice do range atual.
        :return: True se for o último range, False caso contrário.
        """
        ranked_musics = self.get_ranking()
        num_ranges = min(4, len(ranked_musics) - 1)  # Determina o número de ranges disponíveis
        return range_index >= num_ranges

    def get_representative_music(self, range_index, exclude_id=None):
        """
        Retorna uma música representativa de um range de classificação.
        :param range_index: Índice do range (1 a 5).
        :param exclude_id: ID da música a ser excluída da seleção
        :return: O ID da música representativa ou None se não houver músicas no range.
        """
        ranked_musics = self.get_ranking()
        total = len(ranked_musics)
        if total == 0:
            return None  # Nenhuma música classificada

        # Determinar o número de ranges disponíveis
        num_ranges = min(5, total)

        # Calcula o intervalo do range
        start = (range_index - 1) * total // num_ranges
        end = range_index * total // num_ranges

        # Cria uma lista de músicas válidas no range atual
        valid_musics = []
        if start < total:
            for i in range(start, min(end, total)):
                music = ranked_musics[i]
                # Verifica se a música é válida para comparação
                if (music['id'] != exclude_id and  # Não é a música sendo excluída
                    music['stars'] >= 0 and        # Não foi pulada
                    music['id'] not in [s[1] for s in self.comparison_model.get_comparisons() if s[0] == exclude_id]):  # Não foi comparada antes
                    valid_musics.append(music)

        # Se encontrou músicas válidas, retorna uma delas
        if valid_musics:
            # Por enquanto, retorna a primeira música válida encontrada
            return valid_musics[0]['id']
            
        return None

    def update_stars_based_on_ranking(self):
        """
        Atualiza as estrelas das músicas com base no ranking calculado.
        """
        ranking = self.get_ranking()
        total = len(ranking)

        for index, music in enumerate(ranking):
            # Calcula estrelas com base na posição no ranking
            stars = 5 - (index * 5 // total)
            self.music_model.update_stars(music['id'], stars)

    def get_music_details(self, music_id):
        """
        Obtém os detalhes de uma música específica.
        :param music_id: ID da música.
        :return: Um dicionário com os detalhes da música (id, path, stars) ou None se não encontrada.
        """
        return self.music_model.get_music_details(music_id)

    def get_total_musics_count(self):
        return self.music_model.get_total_count()

    def get_rated_musics_count(self):
        return self.music_model.get_rated_count()

    def get_unrated_musics(self):
        return self.music_model.get_unrated_musics()

    def get_current_comparison_state(self):
        return self.comparison_state_model.get_comparison_state()