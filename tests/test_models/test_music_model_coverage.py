"""
Testes simples para aumentar a cobertura do music_model.py
Foca nas linhas específicas não cobertas.
"""

import pytest
import tempfile
import os
import sqlite3
from models.music_model import MusicModel
from utils.database_initializer import DatabaseInitializer


@pytest.fixture
def db_connection():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
        temp_db_path = temp_file.name
    
    conn = sqlite3.connect(temp_db_path)
    db_init = DatabaseInitializer(conn)
    db_init.create_tables()
    
    yield conn
    
    conn.close()
    os.unlink(temp_db_path)


class TestMusicModelCoverage:
    """Testes simples para aumentar cobertura do MusicModel."""
    
    def test_update_music_path_success(self, db_connection):
        """Testa atualização bem-sucedida de caminho de música."""
        music_model = MusicModel(db_connection)
        
        # Adicionar música
        music_id = music_model.add_music("/original/path.mp3")
        
        # Atualizar caminho
        result = music_model.update_music_path(music_id, "/new/path.mp3")
        
        assert result is True
        
        # Verificar se foi realmente atualizado
        details = music_model.get_music_details(music_id)
        assert details['path'] == "/new/path.mp3"

    def test_update_music_path_nonexistent_id(self, db_connection):
        """Testa atualização de música que não existe."""
        music_model = MusicModel(db_connection)
        
        # Tentar atualizar música inexistente
        result = music_model.update_music_path(99999, "/new/path.mp3")
        
        assert result is False

    def test_delete_music_with_file_removal(self, db_connection):
        """Testa remoção de música com tentativa de deletar arquivo."""
        music_model = MusicModel(db_connection)
        
        # Adicionar música
        music_id = music_model.add_music("/test/song.mp3")
        
        # Deletar música (sem arquivo real, só testa o código)
        result = music_model.delete_music(music_id)
        
        # Verificar que música foi removida do banco
        details = music_model.get_music_details(music_id)
        assert details is None

    def test_get_filtered_musics_with_min_max_stars(self, db_connection):
        """Testa filtro por faixa de estrelas."""
        music_model = MusicModel(db_connection)
        
        # Adicionar músicas com diferentes estrelas
        for i in range(5):
            music_id = music_model.add_music(f"/test/song{i}.mp3")
            music_model.update_stars(music_id, i + 1)  # 1-5 estrelas
        
        # Testar filtro por faixa (3-4 estrelas)
        results = music_model.get_filtered_musics(min_stars=3, max_stars=4)
        assert len(results) == 2
        
        # Verificar que são as músicas corretas
        star_values = [r['stars'] for r in results]
        assert 3 in star_values
        assert 4 in star_values

    def test_get_all_tags_with_data(self, db_connection):
        """Testa get_all_tags com dados no banco."""
        music_model = MusicModel(db_connection)
        
        # Adicionar algumas tags
        music_model.add_tag("rock")
        music_model.add_tag("metal")
        music_model.add_tag("jazz")
        
        tags = music_model.get_all_tags()
        assert len(tags) == 3
        assert "rock" in tags
        assert "metal" in tags
        assert "jazz" in tags
