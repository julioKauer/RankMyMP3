import pytest
import tempfile
import os
import sqlite3
from models.music_model import MusicModel
from utils.database_initializer import DatabaseInitializer


class TestMultiTagsFilterBasic:
    """Testes básicos para o filtro de múltiplas tags."""
    
    @pytest.fixture
    def test_db(self):
        """Cria um banco temporário para testes."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Criar conexão e inicializar estrutura
        conn = sqlite3.connect(temp_file.name)
        initializer = DatabaseInitializer(conn)
        initializer.create_tables()
        
        yield conn
        
        # Cleanup
        conn.close()
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    @pytest.fixture
    def music_model_with_data(self, test_db):
        """Cria um modelo com dados de teste."""
        model = MusicModel(test_db)
        
        # Adicionar músicas de teste
        model.add_music("/test/song1.mp3")
        model.add_music("/test/song2.mp3") 
        model.add_music("/test/song3.mp3")
        model.add_music("/test/song4.mp3")
        
        # Definir algumas estrelas
        model.update_stars(1, 5)
        model.update_stars(2, 4)
        model.update_stars(3, 3)
        model.update_stars(4, 2)
        
        # Adicionar tags
        model.add_tag("rock")
        model.add_tag("pop")
        model.add_tag("metal")
        model.add_tag("acoustic")
        
        # Associar tags às músicas
        model.associate_tag(1, "rock")
        model.associate_tag(1, "metal")
        model.associate_tag(2, "rock")
        model.associate_tag(2, "pop")
        model.associate_tag(3, "pop")
        model.associate_tag(3, "acoustic")
        model.associate_tag(4, "acoustic")
        
        return model
    
    def test_get_filtered_musics_multi_tags_basic(self, music_model_with_data):
        """Testa filtro básico com múltiplas tags."""
        model = music_model_with_data
        
        # Teste com tag única
        result = model.get_filtered_musics_multi_tags(tags_list=["rock"])
        assert len(result) == 2  # Songs 1 and 2
        
        # Teste com múltiplas tags (AND)
        result = model.get_filtered_musics_multi_tags(tags_list=["rock", "metal"])
        assert len(result) == 1  # Only song 1
        
        # Teste com tags que não existem juntas
        result = model.get_filtered_musics_multi_tags(tags_list=["metal", "acoustic"])
        assert len(result) == 0  # No song has both
    
    def test_get_filtered_musics_multi_tags_with_stars(self, music_model_with_data):
        """Testa filtro de múltiplas tags combinado com estrelas."""
        model = music_model_with_data
        
        # Filtro por tag + estrelas
        result = model.get_filtered_musics_multi_tags(
            tags_list=["rock"], 
            min_stars=4
        )
        assert len(result) == 2  # Songs 1 (5 stars) and 2 (4 stars)
        
        # Filtro mais restritivo
        result = model.get_filtered_musics_multi_tags(
            tags_list=["rock"], 
            min_stars=5
        )
        assert len(result) == 1  # Only song 1 (5 stars)
    
    def test_get_filtered_musics_multi_tags_empty_list(self, music_model_with_data):
        """Testa comportamento com lista vazia de tags."""
        model = music_model_with_data
        
        result = model.get_filtered_musics_multi_tags(tags_list=[])
        assert len(result) == 4  # Should return all songs
        
        result = model.get_filtered_musics_multi_tags(tags_list=None)
        assert len(result) == 4  # Should return all songs
    
    def test_get_filtered_musics_multi_tags_nonexistent_tags(self, music_model_with_data):
        """Testa filtro com tags que não existem."""
        model = music_model_with_data
        
        result = model.get_filtered_musics_multi_tags(tags_list=["nonexistent"])
        assert len(result) == 0
        
        result = model.get_filtered_musics_multi_tags(tags_list=["rock", "nonexistent"])
        assert len(result) == 0
    
    def test_get_filtered_musics_multi_tags_order(self, music_model_with_data):
        """Testa se o resultado está ordenado por estrelas descendente."""
        model = music_model_with_data
        
        result = model.get_filtered_musics_multi_tags(tags_list=["rock"])
        
        # Deve retornar songs 1 (5 stars) e 2 (4 stars) em ordem
        assert len(result) == 2
        assert result[0]['stars'] == 5  # Song 1
        assert result[1]['stars'] == 4  # Song 2
