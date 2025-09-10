import os
from sqlite3 import Connection
from collections import defaultdict
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

    def force_redistribute_all_stars(self):
        """
        Força a redistribuição de estrelas para todas as músicas classificadas
        baseado na ordem topológica atual.
        """
        ranking = self._build_ranking_from_comparisons()
        if ranking:
            print(f"DEBUG: Force redistributing stars for {len(ranking)} musics")
            self._redistribute_all_stars(ranking)
            print("DEBUG: Star redistribution completed")
        else:
            print("DEBUG: No musics to redistribute")

    def get_classified_musics_topological(self):
        """
        Retorna músicas classificadas ordenadas por ordenação topológica baseada nas comparações.
        """
        # Usar o mesmo algoritmo de _build_ranking_from_comparisons para consistência
        topological_order = self._build_ranking_from_comparisons()
        
        if not topological_order:
            # Fallback para ordem por estrelas se não há comparações
            return self.music_model.get_all_classified_musics()
        
        # Obter dados completos das músicas classificadas
        classified_musics = self.music_model.get_all_classified_musics()
        music_dict = {music['id']: music for music in classified_musics}
        
        # Criar lista ordenada mantendo apenas músicas classificadas
        ordered_musics = []
        for music_id in topological_order:
            if music_id in music_dict:
                ordered_musics.append(music_dict[music_id])
        
        return ordered_musics

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
            result = self._process_binary_search_step(winner_id)
            # Validar consistência após processamento
            self._validate_consistency()
            return result
        
        return True
    
    def _validate_consistency(self):
        """
        Valida e corrige inconsistências entre comparações e estrelas.
        """
        try:
            # Buscar músicas que aparecem em comparações mas têm stars = 0
            cursor = self.music_model.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT music_a_id FROM comparisons 
                UNION 
                SELECT DISTINCT music_b_id FROM comparisons
            ''')
            musics_in_comparisons = set(row[0] for row in cursor.fetchall())
            
            cursor.execute('SELECT id FROM music WHERE stars = 0')
            unrated_ids = set(row[0] for row in cursor.fetchall())
            
            inconsistent = musics_in_comparisons & unrated_ids
            
            if inconsistent:
                print(f"DEBUG: Detected inconsistent musics: {inconsistent}")
                for music_id in inconsistent:
                    # Remover comparações inconsistentes
                    cursor.execute('DELETE FROM comparisons WHERE music_a_id = ? OR music_b_id = ?', 
                                 (music_id, music_id))
                    print(f"DEBUG: Removed inconsistent comparisons for music {music_id}")
                
                self.music_model.conn.commit()
        except Exception as e:
            print(f"DEBUG: Error in consistency validation: {e}")

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
        
        # Parsear contexto: "binary_search_low_high_comparisons" ou "initial_comparison_..."
        parts = context.split('_')
        if parts[0] == "initial" and parts[1] == "comparison":
            # Comparação inicial entre duas primeiras músicas
            print(f"DEBUG: Processing initial comparison between {new_music_id} and {compared_music_id}")
            
            # Classificar ambas as músicas baseado no resultado
            if winner_id == new_music_id:
                # new_music_id vence - fica na posição 0, compared_music_id na posição 1
                self._insert_music_at_position(new_music_id, 0)
                self._insert_music_at_position(compared_music_id, 1)
                print(f"DEBUG: Initial comparison complete - {new_music_id} wins")
            else:
                # compared_music_id vence - fica na posição 0, new_music_id na posição 1
                self._insert_music_at_position(compared_music_id, 0)
                self._insert_music_at_position(new_music_id, 1)
                print(f"DEBUG: Initial comparison complete - {compared_music_id} wins")
            
            self.comparison_state_model.clear_comparison_state()
            return True
        elif len(parts) >= 4:
            low = int(parts[2])
            high = int(parts[3])
            comparisons = int(parts[4]) if len(parts) > 4 else 0
        else:
            # Fallback para formato antigo
            low = 0
            high = len(self._build_ranking_from_comparisons(exclude_music_id=new_music_id)) - 1
            comparisons = 0
            
        print(f"DEBUG: Binary search step - low={low}, high={high}, comparisons={comparisons}")
        print(f"DEBUG: Compared music {new_music_id} vs {compared_music_id}, winner: {winner_id}")
        
        # Calcular posição atual mid para referência
        current_mid = (low + high) // 2
        
        # Determinar nova posição baseada no resultado
        ranking = self._build_ranking_from_comparisons(exclude_music_id=new_music_id)
        
        if winner_id == new_music_id:
            # Nova música é melhor - buscar na metade ANTES (posições menores)
            new_high = current_mid - 1
            print(f"DEBUG: New music wins - searching before, new range [{low}, {new_high}]")
        else:
            # Música existente é melhor - buscar na metade DEPOIS (posições maiores)
            new_low = current_mid + 1
            print(f"DEBUG: Existing music wins - searching after, new range [{new_low}, {high}]")
            low = new_low
            
        if winner_id == new_music_id:
            high = new_high
            
        comparisons += 1
        
        # Verificar se encontrou a posição ou precisa continuar
        if low > high or comparisons >= 5:  # Máximo 5 comparações ou intervalo inválido
            # Finalizar busca - inserir na posição encontrada
            final_position = low
            self._insert_music_at_position(new_music_id, final_position)
            self.comparison_state_model.clear_comparison_state()
            print(f"DEBUG: Binary search complete - inserted at position {final_position} after {comparisons} comparisons")
            return True
        else:
            # Continuar busca - próxima comparação
            ranking = self._build_ranking_from_comparisons(exclude_music_id=new_music_id)
            mid = (low + high) // 2
            
            if mid < len(ranking):
                next_compare_id = ranking[mid]
                
                # Verificar se já fizemos esta comparação antes (prevenir loops)
                existing_result = self._get_existing_comparison(new_music_id, next_compare_id)
                if existing_result is not None:
                    print(f"DEBUG: Using existing comparison result between {new_music_id} and {next_compare_id}: winner={existing_result}")
                    # Usar resultado existente diretamente
                    return self._process_binary_search_step(existing_result)
                
                new_context = f"binary_search_{low}_{high}_{comparisons}"
                self.comparison_state_model.save_comparison_state(new_music_id, next_compare_id, new_context)
                print(f"DEBUG: Next comparison needed - mid position {mid}, comparing with music {next_compare_id}")
                return False  # Precisa de mais comparações
            else:
                # Inserir no final
                self._insert_music_at_position(new_music_id, len(ranking))
                self.comparison_state_model.clear_comparison_state()
                print(f"DEBUG: Inserting at end - position {len(ranking)}")
                return True

    def _insert_music_at_position(self, music_id, position):
        """
        Insere uma música em uma posição específica do ranking e redistribui estrelas.
        """
        ranking = self._build_ranking_from_comparisons(exclude_music_id=music_id)
        
        # Inserir na posição correta
        ranking.insert(position, music_id)
        
        print(f"DEBUG: Final ranking after insertion: {ranking}")
        
        # Criar comparações artificiais para garantir a ordem topológica correta
        self._create_positioning_comparisons(music_id, ranking, position)
        
        # SEMPRE redistribuir TODAS as músicas do ranking
        self._redistribute_all_stars(ranking)

    def _create_positioning_comparisons(self, music_id, ranking, position):
        """
        Cria comparações artificiais para garantir que a música fique na posição correta.
        """
        print(f"DEBUG: Creating positioning comparisons for music {music_id} at position {position}")
        
        # Criar comparações para garantir ordem correta:
        # 1. Nova música vence todas as que vêm depois dela
        for i in range(position + 1, len(ranking)):
            next_music_id = ranking[i]
            self.comparison_model.save_comparison(music_id, next_music_id, music_id)
            print(f"DEBUG: {music_id} beats {next_music_id}")
        
        # 2. Todas as que vêm antes vencem a nova música  
        for i in range(position):
            prev_music_id = ranking[i]
            self.comparison_model.save_comparison(prev_music_id, music_id, prev_music_id)
            print(f"DEBUG: {prev_music_id} beats {music_id}")
        
        print(f"DEBUG: Positioning comparisons completed for music {music_id}")

    def _redistribute_all_stars(self, ranking):
        """
        Redistribui estrelas para todas as músicas do ranking baseado na posição.
        """
        total_musics = len(ranking)
        if total_musics == 0:
            return
            
        musics_per_level = total_musics // 5
        remainder = total_musics % 5
        
        # Calcular quantas músicas em cada nível (5 a 1 estrelas)
        level_counts = [musics_per_level] * 5
        for i in range(remainder):
            level_counts[i] += 1
            
        print(f"DEBUG: Redistributing {total_musics} musics")
        print(f"DEBUG: Distribution: 5⭐={level_counts[0]}, 4⭐={level_counts[1]}, 3⭐={level_counts[2]}, 2⭐={level_counts[3]}, 1⭐={level_counts[4]}")
        
        # Atribuir estrelas baseado na posição no ranking
        current_pos = 0
        for level in range(5, 0, -1):  # 5 estrelas para 1 estrela
            count = level_counts[5 - level]
            for _ in range(count):
                if current_pos < total_musics:
                    music_id_at_pos = ranking[current_pos]
                    old_stars = self.music_model.get_music_details(music_id_at_pos)['stars']
                    self.music_model.update_stars(music_id_at_pos, level)
                    print(f"DEBUG: Music {music_id_at_pos} at position {current_pos+1}: {old_stars}⭐ -> {level}⭐")
                    current_pos += 1

    def get_next_comparison(self):
        """
        Obtém a próxima comparação necessária.
        """
        # Primeiro verificar se ainda há músicas não classificadas
        unrated_music = self.music_model.get_unrated_musics()
        if not unrated_music:
            # Não há mais músicas para classificar - limpar estado salvo se existir
            self.comparison_state_model.clear_comparison_state()
            return None
            
        # Verificar se há busca binária em andamento para uma música não classificada
        current_state = self.comparison_state_model.get_comparison_state()
        if current_state:
            # Verificar se AMBAS as músicas do estado atual ainda são válidas
            unrated_music_id = current_state['unrated_music_id']
            compared_music_id = current_state['compared_music_id']
            
            unrated_data = self.music_model.get_music_details(unrated_music_id)
            compared_data = self.music_model.get_music_details(compared_music_id)
            
            # Ambas as músicas devem existir e nenhuma deve estar pulada (-1)
            unrated_valid = unrated_data and unrated_data.get('stars', 0) == 0
            compared_valid = compared_data and compared_data.get('stars', 0) != -1
            
            if unrated_valid and compared_valid:
                # Ambas as músicas são válidas, continuar com o estado salvo
                return current_state
            else:
                # Estado inválido - uma das músicas foi pulada ou classificada
                print(f"DEBUG: Clearing invalid state - unrated_id={unrated_music_id}({unrated_data.get('stars', 'N/A') if unrated_data else 'None'}), compared_id={compared_music_id}({compared_data.get('stars', 'N/A') if compared_data else 'None'})")
                self.comparison_state_model.clear_comparison_state()
            
        # Iniciar nova busca binária para próxima música não classificada
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
        # Verificar músicas já classificadas (com estrelas > 0)
        classified_music = self.music_model.get_all_classified_musics()
        current_ranking = self._build_ranking_from_comparisons()
        
        # Se não há músicas classificadas, precisamos de pelo menos 2 para comparar
        if not classified_music:
            # Verificar se há pelo menos 2 músicas não classificadas
            unrated_music = self.music_model.get_unrated_musics()
            if len(unrated_music) < 2:
                # Só há 1 música - classificar automaticamente como 3⭐
                self._insert_music_at_position(new_music_id, 0)
                print(f"DEBUG: Only one music - auto-classified with 3 stars")
                return None
            else:
                # Há pelo menos 2 músicas - fazer comparação entre as duas primeiras
                first_music = unrated_music[0]
                second_music = unrated_music[1]
                
                # Se a música atual é uma das duas primeiras, fazer comparação inicial
                if new_music_id in [first_music['id'], second_music['id']]:
                    other_music_id = second_music['id'] if new_music_id == first_music['id'] else first_music['id']
                    
                    # Verificar se já existe um estado idêntico salvo para evitar loop
                    current_state = self.comparison_state_model.get_comparison_state()
                    if (current_state and 
                        current_state['unrated_music_id'] == new_music_id and 
                        current_state['compared_music_id'] == other_music_id):
                        print(f"DEBUG: Identical state already exists, skipping save")
                        return current_state
                    
                    # Iniciar comparação entre as duas primeiras músicas
                    context = f"initial_comparison_0_0_0"
                    self.comparison_state_model.save_comparison_state(new_music_id, other_music_id, context)
                    print(f"DEBUG: Initial comparison between first two musics")
                    return {
                        'unrated_music_id': new_music_id,
                        'compared_music_id': other_music_id,
                        'context': context
                    }
                else:
                    # Música não é uma das duas primeiras - isso não deveria acontecer
                    print(f"DEBUG: Unexpected case - music {new_music_id} is not in first two")
                    return None
        
        # Se há músicas classificadas, mas ranking vazio, reconstruir
        if not current_ranking:
            current_ranking = [music['id'] for music in classified_music]
            print(f"DEBUG: Rebuilt ranking from classified music: {current_ranking}")
        
        if not current_ranking:
            print(f"DEBUG: No ranking available, treating as first music")
            # Usar _insert_music_at_position para garantir consistência
            self._insert_music_at_position(new_music_id, 0)
            
            # Buscar próxima música não classificada
            unrated_music = self.music_model.get_unrated_musics()
            if unrated_music:
                next_unrated = unrated_music[0]
                next_music_id = next_unrated['id']
                print(f"DEBUG: Starting binary search for next music {next_music_id}")
                return self._start_binary_search(next_music_id)
            else:
                print(f"DEBUG: No more unrated music")
                return None
            
        # Iniciar busca binária
        low = 0
        high = len(current_ranking) - 1
        mid = (low + high) // 2
        mid_music_id = current_ranking[mid]
        
        # Verificar se não é autocomparação
        if new_music_id == mid_music_id:
            print(f"DEBUG: Autocomparação detectada! Música {new_music_id} já está no ranking na posição {mid}")
            # Música já está classificada, não deve acontecer
            return None
        
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

    def _build_ranking_from_comparisons(self, exclude_music_id=None):
        """Constrói ranking baseado nas comparações diretas usando ordenação topológica."""
        comparisons = self.comparison_model.get_comparisons()
        
        if not comparisons:
            return []
            
        # Construir grafo direcionado: vencedor -> perdedor
        graph = {}
        in_degree = {}
        all_musics = set()
        
        for music_a_id, music_b_id, winner_id in comparisons:
            # Excluir música específica se solicitado
            if exclude_music_id and (music_a_id == exclude_music_id or music_b_id == exclude_music_id):
                continue
                
            all_musics.add(music_a_id)
            all_musics.add(music_b_id)
            
            # Inicializar nós se não existem
            if music_a_id not in graph:
                graph[music_a_id] = []
            if music_b_id not in graph:
                graph[music_b_id] = []
            if music_a_id not in in_degree:
                in_degree[music_a_id] = 0
            if music_b_id not in in_degree:
                in_degree[music_b_id] = 0
            
            # Adicionar aresta: vencedor aponta para perdedor
            loser_id = music_b_id if winner_id == music_a_id else music_a_id
            
            # Evitar arestas duplicadas
            if loser_id not in graph[winner_id]:
                graph[winner_id].append(loser_id)
                in_degree[loser_id] += 1
        
        # Incluir todas as músicas que já têm estrelas (efetivamente classificadas)
        classified_music = self.music_model.get_all_classified_musics()
        for music in classified_music:
            # Excluir música específica se solicitado
            if exclude_music_id and music['id'] == exclude_music_id:
                continue
            if music['stars'] > 0:
                # Incluir sempre músicas com estrelas, mesmo se não têm comparações diretas ainda
                if music['id'] not in all_musics:
                    all_musics.add(music['id'])
                if music['id'] not in graph:
                    graph[music['id']] = []
                if music['id'] not in in_degree:
                    in_degree[music['id']] = 0
        
        # Ordenação topológica usando algoritmo de Kahn
        queue = []
        for music_id in all_musics:
            if in_degree[music_id] == 0:
                queue.append(music_id)
        
        # Ordenar música sem grau de entrada por ID para ordem determinística
        queue.sort()
        
        result = []
        while queue:
            # Para música com mesmo grau, usar ID para ordem determinística
            current = queue.pop(0)
            result.append(current)
            
            # Remover arestas e atualizar graus
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            
            # Manter ordem determinística
            queue.sort()
        
        # Verificar se há ciclos (não deveria haver)
        if len(result) != len(all_musics):
            print(f"WARNING: Possible cycle detected in comparisons. Expected {len(all_musics)}, got {len(result)}")
            # Fallback: adicionar músicas restantes ordenadas por ID
            remaining = all_musics - set(result)
            result.extend(sorted(remaining))
        
        return result

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
        """Retorna o ranking usando ordenação topológica (mais preciso que por estrelas)."""
        return self.get_classified_musics_topological()

    def get_filtered_musics(self, tag_filter=None, max_stars=None):
        return self.music_model.get_filtered_musics(tag_filter, min_stars=1, max_stars=max_stars)

    def clear_comparison_state(self):
        """
        Limpa o estado de comparação. Este método deve ser usado apenas
        quando queremos realmente cancelar toda a busca binária de uma música,
        não apenas parar temporariamente.
        """
        self.comparison_state_model.clear_comparison_state()
        
    def pause_comparison(self):
        """
        Pausa a comparação atual, mantendo o progresso da busca binária.
        O estado fica salvo e pode ser retomado com get_next_comparison().
        """
        # Não fazer nada - apenas deixar o estado salvo
        current_state = self.comparison_state_model.get_comparison_state()
        if current_state:
            print(f"DEBUG: Comparison paused - progress saved for music {current_state['unrated_music_id']}")
        else:
            print(f"DEBUG: No comparison to pause")
    
    def cancel_current_music_classification(self):
        """
        Cancela completamente a classificação da música atual e limpa o progresso.
        """
        current_state = self.comparison_state_model.get_comparison_state()
        if current_state:
            print(f"DEBUG: Cancelling classification for music {current_state['unrated_music_id']}")
            self.comparison_state_model.clear_comparison_state()
        else:
            print(f"DEBUG: No classification to cancel")

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

    def get_unrated_musics_by_folder(self):
        """Retorna músicas não classificadas organizadas por pasta."""
        unrated_musics = self.music_model.get_unrated_musics()
        
        # Organizar por pasta
        folders_dict = {}
        for music in unrated_musics:
            folder_path = os.path.dirname(music['path'])
            if folder_path not in folders_dict:
                folders_dict[folder_path] = []
            folders_dict[folder_path].append(music)
        
        return folders_dict

    def get_ignored_musics(self):
        """Retorna músicas ignoradas (stars = -1)."""
        return self.music_model.get_ignored_musics()
