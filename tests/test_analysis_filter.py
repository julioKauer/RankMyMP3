"""
Testes para o filtro de análise por nome de música.
"""

import pytest
import tempfile
import os
import shutil
import sqlite3
from controllers.music_controller import MusicController
from utils.database_initializer import DatabaseInitializer


class TestAnalysisFilter:
    
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
            os.path.join(self.temp_folder, "rock_song_1.mp3"),
            os.path.join(self.temp_folder, "pop_music_2.mp3"),
            os.path.join(self.temp_folder, "jazz_classic.mp3"),
            os.path.join(self.temp_folder, "rock_anthem.mp3"),
        ]
        
        for music_file in self.music_files:
            with open(music_file, 'w') as f:
                f.write("fake mp3 content")
        
        # Adicionar músicas ao banco
        self.controller.add_music_folder(self.temp_folder)
    
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
    
    def test_get_unrated_musics_by_folder_no_filter(self):
        """Testa que todas as músicas aparecem sem filtro."""
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        all_musics = []
        for musics in folders_dict.values():
            all_musics.extend(musics)
        
        assert len(all_musics) == 4
        music_names = [os.path.basename(music['path']) for music in all_musics]
        assert "rock_song_1.mp3" in music_names
        assert "pop_music_2.mp3" in music_names
        assert "jazz_classic.mp3" in music_names
        assert "rock_anthem.mp3" in music_names
    
    def test_filter_by_rock(self):
        """Testa filtro por 'rock'."""
        # Simular filtro no frontend: buscar músicas com 'rock' no nome
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        filtered_musics = []
        for musics in folders_dict.values():
            for music in musics:
                if 'rock' in os.path.basename(music['path']).lower():
                    filtered_musics.append(music)
        
        assert len(filtered_musics) == 2
        music_names = [os.path.basename(music['path']) for music in filtered_musics]
        assert "rock_song_1.mp3" in music_names
        assert "rock_anthem.mp3" in music_names
    
    def test_filter_by_jazz(self):
        """Testa filtro por 'jazz'."""
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        filtered_musics = []
        for musics in folders_dict.values():
            for music in musics:
                if 'jazz' in os.path.basename(music['path']).lower():
                    filtered_musics.append(music)
        
        assert len(filtered_musics) == 1
        assert os.path.basename(filtered_musics[0]['path']) == "jazz_classic.mp3"
    
    def test_filter_nonexistent(self):
        """Testa filtro que não corresponde a nenhuma música."""
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        filtered_musics = []
        for musics in folders_dict.values():
            for music in musics:
                if 'metal' in os.path.basename(music['path']).lower():
                    filtered_musics.append(music)
        
        assert len(filtered_musics) == 0
    
    def test_filter_case_insensitive(self):
        """Testa que o filtro é case-insensitive."""
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        # Filtrar por "ROCK" em maiúsculo
        filtered_musics = []
        for musics in folders_dict.values():
            for music in musics:
                if 'ROCK'.lower() in os.path.basename(music['path']).lower():
                    filtered_musics.append(music)
        
        assert len(filtered_musics) == 2
        music_names = [os.path.basename(music['path']) for music in filtered_musics]
        assert "rock_song_1.mp3" in music_names
        assert "rock_anthem.mp3" in music_names
