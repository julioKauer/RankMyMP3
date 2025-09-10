"""
Testes para o ComparisonModel.
"""
import pytest
from models.comparison_model import ComparisonModel
from models.music_model import MusicModel


class TestComparisonModel:
    """Testes para a classe ComparisonModel."""
    
    def test_save_comparison(self, comparison_model, music_model):
        """Testa salvar uma comparação."""
        # Adicionar duas músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        
        # Salvar comparação
        comparison_model.save_comparison(music_id1, music_id2, music_id1)
        
        # Verificar se foi salva
        result = comparison_model.get_comparison_result(music_id1, music_id2)
        assert result == music_id1
        
    def test_get_comparison_result(self, comparison_model, music_model):
        """Testa buscar resultado de comparação."""
        # Adicionar duas músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        
        # Sem comparação deve retornar None
        result = comparison_model.get_comparison_result(music_id1, music_id2)
        assert result is None
        
        # Salvar comparação
        comparison_model.save_comparison(music_id1, music_id2, music_id2)
        
        # Agora deve retornar o vencedor
        result = comparison_model.get_comparison_result(music_id1, music_id2)
        assert result == music_id2
        
    def test_get_comparison_result_symmetric(self, comparison_model, music_model):
        """Testa que comparação é simétrica (A vs B = B vs A)."""
        # Adicionar duas músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        
        # Salvar comparação A vs B
        comparison_model.save_comparison(music_id1, music_id2, music_id1)
        
        # Buscar B vs A deve retornar o mesmo resultado
        result1 = comparison_model.get_comparison_result(music_id1, music_id2)
        result2 = comparison_model.get_comparison_result(music_id2, music_id1)
        
        assert result1 == result2 == music_id1
        
    def test_get_all_comparisons_for_music(self, comparison_model, music_model):
        """Testa buscar todas as comparações de uma música."""
        # Adicionar três músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        # Criar comparações envolvendo music_id1
        comparison_model.save_comparison(music_id1, music_id2, music_id1)
        comparison_model.save_comparison(music_id1, music_id3, music_id3)
        comparison_model.save_comparison(music_id2, music_id3, music_id2)  # Não envolve music_id1
        
        # Buscar comparações de music_id1
        comparisons = comparison_model.get_all_comparisons_for_music(music_id1)
        
        # Deve retornar 2 comparações
        assert len(comparisons) == 2
        
        # Verificar se music_id1 está em todas
        for comp in comparisons:
            assert music_id1 in [comp[0], comp[1]]  # comp é uma tupla (music_a_id, music_b_id, winner_id)
            
    def test_remove_comparisons_for_music(self, comparison_model, music_model):
        """Testa remover todas as comparações de uma música."""
        # Adicionar três músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        # Criar comparações
        comparison_model.save_comparison(music_id1, music_id2, music_id1)
        comparison_model.save_comparison(music_id1, music_id3, music_id3)
        comparison_model.save_comparison(music_id2, music_id3, music_id2)
        
        # Verificar que existem comparações para music_id1
        comparisons = comparison_model.get_all_comparisons_for_music(music_id1)
        assert len(comparisons) == 2
        
        # Remover comparações de music_id1
        comparison_model.remove_comparisons_for_music(music_id1)
        
        # Verificar que não existem mais comparações para music_id1
        comparisons = comparison_model.get_all_comparisons_for_music(music_id1)
        assert len(comparisons) == 0
        
        # Verificar que comparação entre music_id2 e music_id3 ainda existe
        result = comparison_model.get_comparison_result(music_id2, music_id3)
        assert result == music_id2
        
    def test_get_defeated_by_music(self, comparison_model, music_model):
        """Testa buscar músicas derrotadas por uma música específica."""
        # Adicionar três músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        # music_id1 derrota music_id2 e music_id3
        comparison_model.save_comparison(music_id1, music_id2, music_id1)
        comparison_model.save_comparison(music_id1, music_id3, music_id1)
        comparison_model.save_comparison(music_id2, music_id3, music_id2)
        
        # Buscar derrotadas por music_id1
        defeated = comparison_model.get_defeated_by_music(music_id1)
        defeated_ids = defeated  # defeated já é uma lista de IDs
        
        assert len(defeated) == 2
        assert music_id2 in defeated_ids
        assert music_id3 in defeated_ids
        assert music_id1 not in defeated_ids
        
    def test_get_winners_against_music(self, comparison_model, music_model):
        """Testa buscar músicas que derrotaram uma música específica."""
        # Adicionar três músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        # music_id1 e music_id2 derrotam music_id3
        comparison_model.save_comparison(music_id1, music_id3, music_id1)
        comparison_model.save_comparison(music_id2, music_id3, music_id2)
        comparison_model.save_comparison(music_id1, music_id2, music_id1)
        
        # Buscar vencedores contra music_id3
        winners = comparison_model.get_winners_against_music(music_id3)
        winner_ids = winners  # winners já é uma lista de IDs
        
        assert len(winners) == 2
        assert music_id1 in winner_ids
        assert music_id2 in winner_ids
        assert music_id3 not in winner_ids
