import os
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

    def add_music_folder(self, folder_path):
        """Adiciona todas as músicas MP3 de uma pasta."""
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.mp3'):
                    self.music_model.add_music(os.path.join(root, file))

    def make_comparison(self, music_a_id, music_b_id, winner_id):
        """
        Registra uma comparação entre duas músicas e atualiza o ranking.
        :param music_a_id: ID da primeira música
        :param music_b_id: ID da segunda música  
        :param winner_id: ID da música vencedora
        """
        # Obter o contexto da comparação
        state = self.comparison_state_model.get_comparison_state()
        context = state[2] if state else 'unknown'
        
        # Usar a nova lógica de processamento
        self.process_comparison_result(music_a_id, music_b_id, winner_id, context)

    def _update_ranking_from_comparisons(self):
        """
        Constrói um ranking baseado nas comparações feitas e distribui as estrelas.
        Usa um algoritmo simples de pontuação para ordenar as músicas.
        """
        # Obter todas as comparações
        comparisons = self.comparison_model.get_comparisons()
        
        # Calcular pontuações para cada música
        scores = {}
        music_ids = set()
        
        for music_a_id, music_b_id, winner_id in comparisons:
            music_ids.add(music_a_id)
            music_ids.add(music_b_id)
            
            # Inicializar pontuações se não existirem
            if music_a_id not in scores:
                scores[music_a_id] = 0
            if music_b_id not in scores:
                scores[music_b_id] = 0
            
            # Dar pontos ao vencedor
            if winner_id == music_a_id:
                scores[music_a_id] += 1
            elif winner_id == music_b_id:
                scores[music_b_id] += 1

        # Ordenar por pontuação
        sorted_musics = sorted(music_ids, key=lambda x: scores.get(x, 0), reverse=True)
        
        # Distribuir estrelas baseado na posição no ranking
        total_musics = len(sorted_musics)
        if total_musics == 0:
            return

        for i, music_id in enumerate(sorted_musics):
            # Calcular estrelas baseado na posição (1-5)
            position_percentage = i / max(1, total_musics - 1)
            
            if position_percentage <= 0.1:  # Top 10%
                stars = 5
            elif position_percentage <= 0.3:  # Top 30%
                stars = 4
            elif position_percentage <= 0.6:  # Top 60%
                stars = 3
            elif position_percentage <= 0.8:  # Top 80%
                stars = 2
            else:  # Bottom 20%
                stars = 1
            
            self.music_model.update_stars(music_id, stars)

    def skip_music(self, music_id):
        """Pula uma música (marca com -1 estrelas para não aparecer mais)."""
        self.music_model.update_stars(music_id, -1)

    def classify_music(self, music_id, stars):
        """Classifica uma música diretamente com um número de estrelas."""
        self.music_model.update_stars(music_id, stars)

    def delete_music(self, music_id):
        """Remove uma música do banco."""
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
        # Verificar se há músicas classificadas
        classified_musics = self.music_model.get_all_classified_musics()
            
        if not classified_musics:
            # Se não há músicas classificadas, buscar duas músicas não classificadas
            two_unrated = self.music_model.get_two_unrated_musics()
            if not two_unrated or len(two_unrated) < 2:
                return None  # Não há músicas suficientes para comparar
            
            # Para a primeira comparação, usar nível 3 (neutro)
            unrated_music_id = two_unrated[0]['id']
            compared_music_id = two_unrated[1]['id']
            self.comparison_state_model.save_comparison_state(unrated_music_id, compared_music_id, 'initial')
            return unrated_music_id, compared_music_id, 'initial'

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

    def clear_comparison_state(self):
        """Limpa o estado atual da comparação."""
        self.comparison_state_model.clear_comparison_state()

    def get_ranking(self, tag_filter=None, max_stars=None):
        """
        Retorna o ranking das músicas baseado nas comparações.
        Retorna apenas músicas efetivamente classificadas (stars > 0).
        """
        return self.music_model.get_filtered_musics(tag_filter, min_stars=1, max_stars=max_stars)

    def get_music_details(self, music_id):
        """
        Obtém os detalhes de uma música específica.
        :param music_id: ID da música.
        :return: Um dicionário com os detalhes da música (id, path, stars) ou None se não encontrada.
        """
        return self.music_model.get_music_details(music_id)

    def get_total_musics_count(self):
        """Retorna o número total de músicas."""
        return self.music_model.get_total_count()

    def get_rated_musics_count(self):
        """Retorna o número de músicas classificadas."""
        return self.music_model.get_rated_count()

    def get_unrated_musics(self):
        """Retorna as músicas não classificadas."""
        return self.music_model.get_unrated_musics()

    def get_current_comparison_state(self):
        """Retorna o estado atual da comparação."""
        return self.comparison_state_model.get_comparison_state()

    def process_comparison_result(self, music_a_id, music_b_id, winner_id, context):
        """
        Processa o resultado de uma comparação usando a estratégia descendente.
        :param music_a_id: ID da primeira música
        :param music_b_id: ID da segunda música  
        :param winner_id: ID da música vencedora
        :param context: Contexto da comparação (nível de estrelas ou 'initial')
        """
        # Salvar a comparação
        self.comparison_model.save_comparison(music_a_id, music_b_id, winner_id)
        
        if context == 'initial':
            # Comparação inicial entre duas músicas não classificadas
            # Classifica o vencedor com 3 estrelas e o perdedor com 2 estrelas
            loser_id = music_b_id if winner_id == music_a_id else music_a_id
            self.classify_music(winner_id, 3)
            self.classify_music(loser_id, 2)
            print(f"DEBUG: Initial comparison - winner {winner_id} gets 3 stars, loser {loser_id} gets 2 stars")
        elif isinstance(context, int):
            # Comparação com estratégia descendente
            star_level = context
            
            # Determinar qual música está sendo classificada (a não classificada)
            music_a_details = self.get_music_details(music_a_id)
            music_b_details = self.get_music_details(music_b_id)
            
            if music_a_details['stars'] == 0:
                # música A está sendo classificada
                unrated_music_id = music_a_id
                classified_music_id = music_b_id
                unrated_won = (winner_id == music_a_id)
            else:
                # música B está sendo classificada  
                unrated_music_id = music_b_id
                classified_music_id = music_a_id
                unrated_won = (winner_id == music_b_id)
            
            if unrated_won:
                # A música não classificada venceu - ela é melhor que o nível atual
                # Classifica com o nível atual de estrelas
                self.classify_music(unrated_music_id, star_level)
                print(f"DEBUG: Unrated music {unrated_music_id} won against {star_level}-star music, classified as {star_level} stars")
            else:
                # A música não classificada perdeu - ela é pior que o nível atual
                # Continua descendo de nível
                next_level = star_level - 1
                if next_level >= 1:
                    # Tenta o próximo nível inferior
                    representative_music = self.music_model.get_last_music_with_stars(next_level)
                    if representative_music:
                        self.comparison_state_model.save_comparison_state(unrated_music_id, representative_music['id'], next_level)
                        print(f"DEBUG: Unrated music {unrated_music_id} lost against {star_level}-star music, trying level {next_level}")
                    else:
                        # Não há música representativa no próximo nível, desce mais
                        self._continue_classification(unrated_music_id, next_level - 1)
                else:
                    # Chegou ao nível mínimo, classifica como 1 estrela
                    self.classify_music(unrated_music_id, 1)
                    print(f"DEBUG: Unrated music {unrated_music_id} reached minimum level, classified as 1 star")
        else:
            # Comparação de refinamento - usa a lógica antiga
            self._update_ranking_from_comparisons()

    def _continue_classification(self, unrated_music_id, star_level):
        """Continua a classificação descendo pelos níveis de estrelas."""
        if star_level < 1:
            # Se chegou abaixo de 1 estrela, classifica como 1 estrela
            self.classify_music(unrated_music_id, 1)
            print(f"DEBUG: Music {unrated_music_id} classified as 1 star (bottom level)")
            return
        
        # Procura uma música representativa neste nível
        representative_music = self.music_model.get_last_music_with_stars(star_level)
        if representative_music:
            self.comparison_state_model.save_comparison_state(unrated_music_id, representative_music['id'], star_level)
            print(f"DEBUG: Continuing classification for music {unrated_music_id} at level {star_level}")
        else:
            # Se não há música representativa neste nível, desce mais um
            self._continue_classification(unrated_music_id, star_level - 1)
