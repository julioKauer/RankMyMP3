import os
from sqlite3 import Connection
from models.music_model import MusicModel
from models.comparison_model import ComparisonModel
from models.comparison_state_model import ComparisonStateModel
from models.folder_model import FolderModel

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
        self.folder_model = FolderModel()

    def add_music_folder(self, folder_path):
        """Adiciona todas as músicas MP3 de uma pasta e salva a pasta no banco."""
        # 1. Salvar a pasta no FolderModel (evita duplicatas)
        if not self.folder_model.folder_exists(folder_path):
            self.folder_model.add_folder(folder_path)
            print(f"Pasta adicionada ao banco: {folder_path}")
        else:
            print(f"Pasta já existe no banco: {folder_path}")
        
        # 2. Processar arquivos MP3 da pasta
        added_count = 0
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.mp3'):
                    file_path = os.path.join(root, file)
                    if self.music_model.add_music(file_path):
                        added_count += 1
        
        print(f"Adicionadas {added_count} músicas da pasta: {folder_path}")
        return added_count

    def get_folders(self):
        """Recupera todas as pastas salvas."""
        return self.folder_model.get_folders()

    def remove_folder(self, folder_path):
        """Remove uma pasta do banco de dados."""
        self.folder_model.remove_folder(folder_path)
        print(f"Pasta removida: {folder_path}")

    def get_folder_count(self):
        """Retorna o número total de pastas."""
        return self.folder_model.get_folder_count()

    def clear_all_folders(self):
        """Remove todas as pastas do banco de dados."""
        self.folder_model.clear_all_folders()
        print("Todas as pastas foram removidas")

    def make_comparison(self, music_a_id, music_b_id, winner_id):
        """
        Registra uma comparação e continua a busca binária.
        """
        # Salvar a comparação
        self.comparison_model.save_comparison(music_a_id, music_b_id, winner_id)
        
        # Obter estado da busca binária
        current_state = self.comparison_state_model.get_comparison_state()
        if current_state:
            return self._process_binary_search_step(winner_id)
        
        return True

    def _process_binary_search_step(self, winner_id):
        """
        Processa um passo da busca binária e determina próxima comparação ou finaliza.
        """
        current_state = self.comparison_state_model.get_comparison_state()
        if not current_state:
            return True
            
        # Parsear contexto da busca binária
        new_music_id = current_state['unrated_music_id']
        compared_music_id = current_state['compared_music_id']
        context = current_state['context']
        
        # Parsear contexto: "binary_search_low_high_comparisons"
        parts = context.split('_')
        if len(parts) >= 4:
            low = int(parts[2])
            high = int(parts[3])
            comparisons = int(parts[4]) if len(parts) > 4 else 0
        else:
            # Fallback para formato antigo
            low = 0
            high = len(self._build_ranking_from_comparisons()) - 1
            comparisons = 0
            
        print(f"DEBUG: Binary search step - low={low}, high={high}, comparisons={comparisons}")
        
        # Determinar nova posição baseada no resultado
        if winner_id == new_music_id:
            # Nova música é melhor - buscar na metade superior
            high = (low + high) // 2
        else:
            # Música existente é melhor - buscar na metade inferior  
            low = (low + high) // 2 + 1
            
        comparisons += 1
        
        # Verificar se encontrou a posição ou precisa continuar
        if low >= high or comparisons >= 5:  # Máximo 5 comparações
            # Finalizar busca - inserir na posição encontrada
            final_position = low
            self._insert_music_at_position(new_music_id, final_position)
            self.comparison_state_model.clear_comparison_state()
            print(f"DEBUG: Binary search complete - inserted at position {final_position} after {comparisons} comparisons")
            return True
        else:
            # Continuar busca - próxima comparação
            ranking = self._build_ranking_from_comparisons()
            if low < len(ranking):
                mid = (low + high) // 2
                next_compare_id = ranking[mid] if mid < len(ranking) else ranking[-1]
                
                new_context = f"binary_search_{low}_{high}_{comparisons}"
                self.comparison_state_model.save_comparison_state(new_music_id, next_compare_id, new_context)
                print(f"DEBUG: Next comparison needed - position {mid}, comparisons so far: {comparisons}")
                return False  # Precisa de mais comparações
            else:
                # Inserir no final
                self._insert_music_at_position(new_music_id, len(ranking))
                self.comparison_state_model.clear_comparison_state()
                return True

    def _insert_music_at_position(self, music_id, position):
        """
        Insere uma música em uma posição específica do ranking e redistribui estrelas.
        """
        ranking = self._build_ranking_from_comparisons()
        
        # Inserir na posição correta
        ranking.insert(position, music_id)
        
        # Redistribuir estrelas baseado na nova ordem
        total_musics = len(ranking)
        musics_per_level = total_musics // 5
        remainder = total_musics % 5
        
        # Calcular quantas músicas em cada nível (5 a 1 estrelas)
        level_counts = [musics_per_level] * 5
        for i in range(remainder):
            level_counts[i] += 1
            
        print(f"DEBUG: Inserting music {music_id} at position {position}/{total_musics}")
        print(f"DEBUG: Redistributing: 5⭐={level_counts[0]}, 4⭐={level_counts[1]}, 3⭐={level_counts[2]}, 2⭐={level_counts[3]}, 1⭐={level_counts[4]}")
        
        # Atribuir estrelas baseado na posição no ranking
        current_pos = 0
        for level in range(5, 0, -1):  # 5 estrelas para 1 estrela
            count = level_counts[5 - level]
            for _ in range(count):
                if current_pos < total_musics:
                    music_id_at_pos = ranking[current_pos]
                    self.music_model.update_stars(music_id_at_pos, level)
                    print(f"DEBUG: Music {music_id_at_pos} at position {current_pos+1} -> {level} stars")
                    current_pos += 1

    def get_next_comparison(self):
        """
        Obtém a próxima comparação necessária.
        """
        # Verificar se há busca binária em andamento
        current_state = self.comparison_state_model.get_comparison_state()
        if current_state:
            return current_state
            
        # Iniciar nova busca binária para próxima música não classificada
        unrated_music = self.music_model.get_unrated_musics()
        if unrated_music:
            first_unrated = unrated_music[0]
            new_music_id = first_unrated['id']
            
            print(f"DEBUG: Starting binary search for music {new_music_id}")
            comparison = self._start_binary_search(new_music_id)
            return comparison
            
        return None

    def _start_binary_search(self, new_music_id):
        """
        Inicia busca binária para uma nova música.
        """
        current_ranking = self._build_ranking_from_comparisons()
        
        if not current_ranking:
            # Primeira música - dar 3 estrelas e buscar próxima
            self.music_model.update_stars(new_music_id, 3)
            print(f"DEBUG: First music, assigned 3 stars")
            
            # Buscar próxima música não classificada
            unrated_music = self.music_model.get_unrated_musics()
            if unrated_music:
                next_unrated = unrated_music[0]
                next_music_id = next_unrated['id']
                print(f"DEBUG: Starting binary search for next music {next_music_id}")
                return self._start_binary_search(next_music_id)
            else:
                print(f"DEBUG: No more unrated music after first")
                return None
            
        # Iniciar busca binária
        low = 0
        high = len(current_ranking) - 1
        mid = (low + high) // 2
        mid_music_id = current_ranking[mid]
        
        # Verificar se já existe comparação
        existing_result = self._get_existing_comparison(new_music_id, mid_music_id)
        if existing_result is not None:
            # Usar resultado existente para posicionar
            if existing_result == new_music_id:
                position = mid  # Música nova é melhor, inserir antes
            else:
                position = mid + 1  # Música nova é pior, inserir depois
            self._insert_music_at_position(new_music_id, position)
            return None
            
        # Salvar estado inicial da busca binária
        context = f"binary_search_{low}_{high}_0"
        self.comparison_state_model.save_comparison_state(new_music_id, mid_music_id, context)
        
        print(f"DEBUG: Binary search started - comparing with position {mid}")
        return {
            'unrated_music_id': new_music_id,
            'compared_music_id': mid_music_id,
            'context': context
        }

    def _build_ranking_from_comparisons(self):
        """Constrói ranking baseado nas comparações diretas."""
        comparisons = self.comparison_model.get_comparisons()
        scores = {}
        music_ids = set()
        
        for music_a_id, music_b_id, winner_id in comparisons:
            music_ids.add(music_a_id)
            music_ids.add(music_b_id)
            
            if music_a_id not in scores:
                scores[music_a_id] = 0
            if music_b_id not in scores:
                scores[music_b_id] = 0
            
            if winner_id == music_a_id:
                scores[music_a_id] += 1
            elif winner_id == music_b_id:
                scores[music_b_id] += 1

        # Incluir músicas classificadas mas sem comparações
        classified_music = self.music_model.get_all_classified_musics()
        for music in classified_music:
            music_ids.add(music['id'])
            if music['id'] not in scores:
                scores[music['id']] = 0

        return sorted(music_ids, key=lambda x: scores.get(x, 0), reverse=True)

    def _get_existing_comparison(self, music_a_id, music_b_id):
        """
        Verifica se já existe comparação entre duas músicas.
        Como as comparações são normalizadas (menor ID primeiro),
        precisamos normalizar nossa busca também.
        """
        # Normalizar a ordem para busca
        if music_a_id > music_b_id:
            music_a_id, music_b_id = music_b_id, music_a_id
            
        comparisons = self.comparison_model.get_comparisons()
        
        for comp_a, comp_b, winner in comparisons:
            if comp_a == music_a_id and comp_b == music_b_id:
                return winner
        return None

    # Métodos auxiliares necessários para a interface
    def skip_music(self, music_id):
        self.music_model.update_stars(music_id, -1)

    def classify_music(self, music_id, stars):
        self.music_model.update_stars(music_id, stars)
        
    def delete_music(self, music_id):
        self.music_model.delete_music(music_id)

    def get_total_musics_count(self):
        return self.music_model.get_total_count()

    def get_unrated_musics_count(self):
        total = self.music_model.get_total_count()
        rated = self.music_model.get_rated_count()
        return total - rated

    def get_rated_musics_count(self):
        return self.music_model.get_rated_count()

    def get_unrated_musics(self):
        return self.music_model.get_unrated_musics()

    def get_rated_musics(self):
        return self.music_model.get_all_classified_musics()

    def get_ranking(self):
        return self.music_model.get_all_classified_musics_by_quality()

    def get_filtered_musics(self, tag_filter=None, max_stars=None):
        return self.music_model.get_filtered_musics(tag_filter, min_stars=1, max_stars=max_stars)

    def clear_comparison_state(self):
        self.comparison_state_model.clear_comparison_state()

    def get_comparison_state(self):
        return self.comparison_state_model.get_comparison_state()

    def get_current_comparison_state(self):
        return self.get_comparison_state()

    def get_music_details(self, music_id):
        return self.music_model.get_music_details(music_id)

    def start_classification_for_unrated(self):
        """Inicia classificação da próxima música não classificada."""
        return self.get_next_comparison() is not None

    def get_all_music(self):
        return self.music_model.get_all_classified_musics()
