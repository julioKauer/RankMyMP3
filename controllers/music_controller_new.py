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

    def classify_music(self, music_id, stars):
        """Classifica uma música com um número de estrelas e reorganiza todo o ranking."""
        self.music_model.update_stars(music_id, stars)
        self._update_all_rankings()

    def _update_all_rankings(self):
        """
        Atualiza o ranking de todas as músicas baseado em porcentagens.
        20% das músicas = 5 estrelas
        20% das músicas = 4 estrelas  
        20% das músicas = 3 estrelas
        20% das músicas = 2 estrelas
        20% das músicas = 1 estrela
        """
        # Obter todas as músicas classificadas (stars > 0), ordenadas por estrelas e depois por ID
        classified_musics = self.music_model.get_all_classified_musics()
        
        if not classified_musics:
            return
            
        total = len(classified_musics)
        
        # Calcular as faixas de 20% cada
        for i, music in enumerate(classified_musics):
            # Calcula em qual quintil (20%) a música está
            quintil = int(i * 5 / total)  # 0, 1, 2, 3, ou 4
            new_stars = 5 - quintil  # 5, 4, 3, 2, ou 1
            
            # Atualiza apenas se mudou
            if music['stars'] != new_stars:
                self.music_model.update_stars(music['id'], new_stars)

    def skip_music(self, music_id):
        """Marca uma música como pulada (-1 estrelas)."""
        self.music_model.update_stars(music_id, -1)

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
