"""
Testes para classificação forçada de músicas.
"""

import pytest
import tempfile
import os
import shutil
import sqlite3
from controllers.music_controller import MusicController
from utils.database_initializer import DatabaseInitializer


class TestForceClassification:
    
    def setup_method(self):
        """Setup para cada teste."""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db.close()
        
        # Inicializar banco de dados
        conn = sqlite3.connect(self.test_db.name)
        initializer = DatabaseInitializer(conn)
        initializer.create_tables()
        conn.close()
        
        # Criar controller
        self.controller = MusicController(self.test_db.name)
        
        # Criar pasta temporária para música
        self.temp_folder = tempfile.mkdtemp()
        
        # Criar arquivos de música simulados
        self.music_files = [
            os.path.join(self.temp_folder, "song_1.mp3"),
            os.path.join(self.temp_folder, "song_2.mp3"),
            os.path.join(self.temp_folder, "song_3.mp3"),
        ]
        
        for music_file in self.music_files:
            with open(music_file, 'w') as f:
                f.write("fake mp3 content")
        
        # Adicionar músicas ao banco
        self.controller.add_music_folder(self.temp_folder)
        
        # Obter IDs das músicas
        all_musics = self.controller.music_model.get_unrated_musics()
        self.music_ids = [music['id'] for music in all_musics]
    
    def teardown_method(self):
        """Cleanup após cada teste."""
        # Fechar conexão
        if hasattr(self.controller, 'conn'):
            self.controller.conn.close()
        
        # Remover arquivo de banco temporário
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
        
        # Remover pasta temporária
        if os.path.exists(self.temp_folder):
            shutil.rmtree(self.temp_folder)
    
    def test_force_classification_valid_music(self):
        """Testa forçar classificação de uma música válida."""
        music_id = self.music_ids[0]
        
        # Verificar que não há comparação ativa
        assert self.controller.get_comparison_state() is None
        
        # Forçar classificação
        success = self.controller.force_next_comparison(music_id)
        assert success is True
        
        # Verificar que agora há uma comparação ativa com esta música
        state = self.controller.get_comparison_state()
        assert state is not None
        assert state['unrated_music_id'] == music_id
    
    def test_force_classification_nonexistent_music(self):
        """Testa forçar classificação de música que não existe."""
        nonexistent_id = 99999
        
        success = self.controller.force_next_comparison(nonexistent_id)
        assert success is False
        
        # Não deve haver comparação ativa
        assert self.controller.get_comparison_state() is None
    
    def test_force_classification_already_classified(self):
        """Testa forçar classificação de música já classificada."""
        music_id = self.music_ids[0]
        
        # Classificar a música primeiro
        self.controller.music_model.update_stars(music_id, 5)
        
        # Tentar forçar classificação
        success = self.controller.force_next_comparison(music_id)
        assert success is False
        
        # Não deve haver comparação ativa
        assert self.controller.get_comparison_state() is None
    
    def test_force_classification_ignored_music(self):
        """Testa forçar classificação de música ignorada."""
        music_id = self.music_ids[0]
        
        # Ignorar a música primeiro
        self.controller.music_model.update_stars(music_id, -1)
        
        # Tentar forçar classificação
        success = self.controller.force_next_comparison(music_id)
        assert success is False
        
        # Não deve haver comparação ativa
        assert self.controller.get_comparison_state() is None
    
    def test_force_classification_clears_previous_state(self):
        """Testa que forçar classificação limpa estado anterior."""
        music_id_1 = self.music_ids[0]
        music_id_2 = self.music_ids[1]
        
        # Forçar primeira música
        success1 = self.controller.force_next_comparison(music_id_1)
        assert success1 is True
        
        state1 = self.controller.get_comparison_state()
        assert state1['unrated_music_id'] == music_id_1
        
        # Forçar segunda música (deve limpar estado anterior)
        success2 = self.controller.force_next_comparison(music_id_2)
        assert success2 is True
        
        state2 = self.controller.get_comparison_state()
        assert state2['unrated_music_id'] == music_id_2
        assert state2['unrated_music_id'] != music_id_1
    
    def test_force_classification_with_no_classified_musics(self):
        """Testa forçar classificação quando não há músicas classificadas."""
        music_id = self.music_ids[0]
        
        # Verificar que não há músicas classificadas
        classified = self.controller.music_model.get_all_classified_musics()
        assert len(classified) == 0
        
        # Forçar classificação deve ainda funcionar (vai comparar com uma música aleatória)
        success = self.controller.force_next_comparison(music_id)
        assert success is True
        
        # Deve haver uma comparação ativa
        state = self.controller.get_comparison_state()
        assert state is not None
        assert state['unrated_music_id'] == music_id
    
    def test_get_music_details_for_forced_music(self):
        """Testa que podemos obter detalhes da música forçada."""
        music_id = self.music_ids[0]
        
        # Forçar classificação
        success = self.controller.force_next_comparison(music_id)
        assert success is True
        
        # Obter detalhes da música
        details = self.controller.get_music_details(music_id)
        assert details is not None
        assert details['id'] == music_id
        assert details['stars'] == 0  # Ainda não classificada
        assert details['path'].endswith('.mp3')
