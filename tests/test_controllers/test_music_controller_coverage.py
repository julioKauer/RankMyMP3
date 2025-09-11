"""
Testes simples para aumentar a cobertura do music_controller.py
Foca nas linhas específicas não cobertas.
"""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch
from models.music_model import MusicModel
from controllers.music_controller import MusicController
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


class TestMusicControllerCoverage:
    """Testes simples para aumentar cobertura do MusicController."""
    
    def test_force_redistribute_all_stars_with_debug_output(self, db_connection):
        """Testa force_redistribute_all_stars com output de debug."""
        controller = MusicController(db_connection)
        
        # Adicionar músicas e fazer comparações
        music_ids = []
        for i in range(3):
            music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
            music_ids.append(music_id)
        
        # Fazer comparações para criar ranking
        controller.comparison_model.save_comparison(music_ids[0], music_ids[1], music_ids[0])
        controller.comparison_model.save_comparison(music_ids[1], music_ids[2], music_ids[1])
        
        # Classificar as músicas
        for music_id in music_ids:
            controller.music_model.update_stars(music_id, 3)
        
        with patch('builtins.print') as mock_print:
            controller.force_redistribute_all_stars()
            
            # Verificar que mensagens de debug foram impressas
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("Force redistributing stars for" in call for call in print_calls)
            assert any("Star redistribution completed" in call for call in print_calls)

    def test_force_redistribute_all_stars_empty_ranking(self, db_connection):
        """Testa force_redistribute_all_stars com ranking vazio."""
        controller = MusicController(db_connection)
        
        with patch('builtins.print') as mock_print:
            controller.force_redistribute_all_stars()
            
            # Verificar mensagem de debug para caso vazio
            mock_print.assert_called_with("DEBUG: No musics to redistribute")

    def test_get_classified_musics_topological_complex_scenario(self, db_connection):
        """Testa get_classified_musics_topological com cenário complexo."""
        controller = MusicController(db_connection)
        
        # Criar múltiplas músicas classificadas
        music_ids = []
        for i in range(5):
            music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
            controller.music_model.update_stars(music_id, 4)  # Classificar todas
            music_ids.append(music_id)
        
        # Criar comparações formando uma cadeia de vitórias
        for i in range(len(music_ids) - 1):
            controller.comparison_model.save_comparison(
                music_ids[i], music_ids[i + 1], music_ids[i]
            )
        
        results = controller.get_classified_musics_topological()
        
        # Verificar que retorna todas as músicas classificadas
        assert len(results) == 5
        
        # Verificar que estão em ordem (primeiro deveria ser o que venceu mais)
        assert results[0]['id'] == music_ids[0]

    def test_skip_music_basic(self, db_connection):
        """Testa skip_music básico."""
        controller = MusicController(db_connection)
        
        # Adicionar música
        music_id = controller.music_model.add_music("/test/song.mp3")
        
        # Pular música
        controller.skip_music(music_id)
        
        # Verificar que música foi marcada como pulada (-1)
        details = controller.music_model.get_music_details(music_id)
        assert details['stars'] == -1

    def test_classify_music_with_stars_parameter(self, db_connection):
        """Testa classify_music com parâmetro de estrelas."""
        controller = MusicController(db_connection)
        
        # Adicionar música
        music_id = controller.music_model.add_music("/test/song.mp3")
        
        with patch('builtins.print') as mock_print:
            controller.classify_music(music_id, 4)
            
            # Verificar que música foi classificada
            details = controller.music_model.get_music_details(music_id)
            assert details['stars'] == 4

    def test_get_next_comparison_with_many_unrated(self, db_connection):
        """Testa get_next_comparison com muitas músicas não classificadas."""
        controller = MusicController(db_connection)
        
        # Criar muitas músicas não classificadas
        music_ids = []
        for i in range(10):
            music_id = controller.music_model.add_music(f"/test/unrated{i}.mp3")
            music_ids.append(music_id)
        
        comparison = controller.get_next_comparison()
        assert comparison is not None
        
        # Verificar estrutura básica do retorno
        assert 'unrated_music_id' in comparison
        assert 'compared_music_id' in comparison
        assert comparison['unrated_music_id'] in music_ids

    def test_make_comparison_basic(self, db_connection):
        """Testa make_comparison básico."""
        controller = MusicController(db_connection)
        
        # Adicionar duas músicas
        music_id1 = controller.music_model.add_music("/test/song1.mp3")
        music_id2 = controller.music_model.add_music("/test/song2.mp3")
        
        # Fazer comparação
        result = controller.make_comparison(music_id1, music_id2, music_id1)
        
        # Verificar que comparação foi salva
        comparison_result = controller.comparison_model.get_comparison_result(music_id1, music_id2)
        assert comparison_result == music_id1
