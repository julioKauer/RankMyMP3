"""
Testes para o ComparisonStateModel.
"""
import pytest
from models.comparison_state_model import ComparisonStateModel
from models.music_model import MusicModel


class TestComparisonStateModel:
    """Testes para a classe ComparisonStateModel."""
    
    def test_save_comparison_state(self, comparison_state_model, music_model):
        """Testa salvar estado de comparação."""
        # Adicionar duas músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        
        # Salvar estado
        context = "binary_search_3_5_4"
        comparison_state_model.save_comparison_state(music_id1, music_id2, context)
        
        # Verificar se foi salvo
        state = comparison_state_model.get_comparison_state()
        assert state is not None
        assert state['unrated_music_id'] == music_id1
        assert state['compared_music_id'] == music_id2
        assert state['context'] == context
        
    def test_get_comparison_state_empty(self, comparison_state_model):
        """Testa buscar estado quando não há nenhum salvo."""
        state = comparison_state_model.get_comparison_state()
        assert state is None
        
    def test_clear_comparison_state(self, comparison_state_model, music_model):
        """Testa limpar estado de comparação."""
        # Adicionar duas músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        
        # Salvar estado
        comparison_state_model.save_comparison_state(music_id1, music_id2, "test_context")
        
        # Verificar que foi salvo
        state = comparison_state_model.get_comparison_state()
        assert state is not None
        
        # Limpar estado
        comparison_state_model.clear_comparison_state()
        
        # Verificar que foi limpo
        state = comparison_state_model.get_comparison_state()
        assert state is None
        
    def test_update_comparison_state(self, comparison_state_model, music_model):
        """Testa atualizar estado existente."""
        # Adicionar três músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        # Salvar estado inicial
        comparison_state_model.save_comparison_state(music_id1, music_id2, "context1")
        
        # Atualizar estado (deve substituir o anterior)
        comparison_state_model.save_comparison_state(music_id1, music_id3, "context2")
        
        # Verificar estado atualizado
        state = comparison_state_model.get_comparison_state()
        assert state is not None
        assert state['unrated_music_id'] == music_id1
        assert state['compared_music_id'] == music_id3
        assert state['context'] == "context2"
        
    def test_context_parsing(self, comparison_state_model, music_model):
        """Testa diferentes formatos de contexto."""
        # Adicionar duas músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        
        contexts = [
            "binary_search_0_10_5",
            "initial_comparison_0_0_0",
            "final_position_check",
            ""
        ]
        
        for context in contexts:
            # Limpar estado anterior
            comparison_state_model.clear_comparison_state()
            
            # Salvar com contexto específico
            comparison_state_model.save_comparison_state(music_id1, music_id2, context)
            
            # Verificar se foi salvo corretamente
            state = comparison_state_model.get_comparison_state()
            assert state is not None
            assert state['context'] == context
