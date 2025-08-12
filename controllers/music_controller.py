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
        # Salvar a comparação
        self.comparison_model.save_comparison(music_a_id, music_b_id, winner_id)
        
        # Recalcular o ranking baseado em todas as comparações
        self._update_ranking_from_comparisons()

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
            
            # Inicializar scores se necessário
            if music_a_id not in scores:
                scores[music_a_id] = 0
            if music_b_id not in scores:
                scores[music_b_id] = 0
                
            # Vencedor ganha 1 ponto, perdedor perde 1 ponto
            if winner_id == music_a_id:
                scores[music_a_id] += 1
                scores[music_b_id] -= 1
            elif winner_id == music_b_id:
                scores[music_b_id] += 1
                scores[music_a_id] -= 1

        # Ordenar músicas por pontuação (maior pontuação = melhor)
        if scores:
            ranked_music_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            
            # Distribuir estrelas baseado na posição no ranking
            total = len(ranked_music_ids)
            for i, music_id in enumerate(ranked_music_ids):
                # Calcular estrelas baseado na posição (20% para cada nível)
                position_ratio = i / total if total > 1 else 0
                if position_ratio <= 0.2:
                    stars = 5
                elif position_ratio <= 0.4:
                    stars = 4
                elif position_ratio <= 0.6:
                    stars = 3
                elif position_ratio <= 0.8:
                    stars = 2
                else:
                    stars = 1
                    
                self.music_model.update_stars(music_id, stars)

    def skip_music(self, music_id):
        """Marca uma música como pulada (-1 estrelas)."""
        self.music_model.update_stars(music_id, -1)

    def classify_music(self, music_id, stars):
        """Classifica uma música diretamente com um número de estrelas."""
        self.music_model.update_stars(music_id, stars)

    def delete_music(self, music_id):
        """Remove uma música do banco."""
        self.music_model.delete_music(music_id)

    def get_next_comparison(self):
        """
        Obtém a próxima comparação mais útil para refinar o ranking.
        Prioriza comparações entre músicas próximas no ranking atual.
        :return: (music_a_id, music_b_id, context_info) ou None se não houver comparações úteis.
        """
        print("DEBUG: get_next_comparison called")
        
        try:
            # Verificar se há um estado de comparação salvo
            state = self.comparison_state_model.get_comparison_state()
            if state:
                print(f"DEBUG: Found saved state: {state}")
                unrated_music_id, compared_music_id, context = state
                return unrated_music_id, compared_music_id, context

            # Buscar duas músicas não classificadas para comparação inicial
            unrated_musics = self.music_model.get_unrated_musics()
            print(f"DEBUG: Found {len(unrated_musics)} unrated musics")
            
            if len(unrated_musics) >= 2:
                music_a = unrated_musics[0]
                music_b = unrated_musics[1]
                print(f"DEBUG: Starting comparison between music {music_a['id']} and {music_b['id']}")
                self.comparison_state_model.save_comparison_state(music_a['id'], music_b['id'], 'initial')
                return music_a['id'], music_b['id'], 'initial'

            # Se todas estão classificadas, buscar comparações para refinar o ranking
            print("DEBUG: Looking for refinement comparisons")
            return self._find_refinement_comparison()
            
        except Exception as e:
            print(f"DEBUG: Exception in get_next_comparison: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _find_refinement_comparison(self):
        """
        Encontra duas músicas classificadas que se beneficiariam de uma comparação direta.
        Prioriza músicas com estrelas adjacentes ou que nunca foram comparadas.
        """
        # Obter músicas classificadas por estrelas
        classified_musics = self.music_model.get_all_classified_musics()
        
        if len(classified_musics) < 2:
            return None

        # Buscar por músicas de níveis adjacentes que não foram comparadas
        comparisons = self.comparison_model.get_comparisons()
        compared_pairs = set()
        for music_a_id, music_b_id, _ in comparisons:
            compared_pairs.add((min(music_a_id, music_b_id), max(music_a_id, music_b_id)))

        # Procurar músicas de estrelas adjacentes não comparadas
        for i in range(len(classified_musics) - 1):
            for j in range(i + 1, len(classified_musics)):
                music_a = classified_musics[i]
                music_b = classified_musics[j]
                
                # Só compara se as estrelas são adjacentes ou iguais
                star_diff = abs(music_a['stars'] - music_b['stars'])
                if star_diff <= 1:
                    pair = (min(music_a['id'], music_b['id']), max(music_a['id'], music_b['id']))
                    if pair not in compared_pairs:
                        self.comparison_state_model.save_comparison_state(music_a['id'], music_b['id'], 'refinement')
                        return music_a['id'], music_b['id'], 'refinement'

        return None

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

    def clear_comparison_state(self):
        """Limpa o estado atual da comparação."""
        self.comparison_state_model.clear_comparison_state()

    def get_ranking(self, tag_filter=None, max_stars=None):
        """
        Retorna o ranking das músicas baseado nas estrelas.
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
