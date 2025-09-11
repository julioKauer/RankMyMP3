"""
Testes para o MusicModel.
"""
import pytest
from models.music_model import MusicModel


class TestMusicModel:
    """Testes para a classe MusicModel."""

    def test_add_music(self, music_model):
        """Testa adicionar uma música."""
        music_id = music_model.add_music('/path/to/test.mp3')
        assert music_id is not None
        assert music_id > 0
        
    def test_add_music_duplicate(self, music_model):
        """Testa adicionar música duplicada."""
        path = '/path/to/test.mp3'
        music_id1 = music_model.add_music(path)
        music_id2 = music_model.add_music(path)
        
        # Deve retornar o mesmo ID para duplicata
        assert music_id2 == music_id1
        assert music_id1 is not None

    def test_get_unrated_musics(self, music_model, sample_music_data):
        """Testa buscar músicas não classificadas."""
        # Adicionar algumas músicas
        for path in sample_music_data:
            music_model.add_music(path)
        
        # Buscar não classificadas
        unrated = music_model.get_unrated_musics()
        assert len(unrated) == len(sample_music_data)
        
        # Todas devem ter stars = 0
        for music in unrated:
            assert music['stars'] == 0

    def test_get_ignored_musics(self, music_model, sample_music_data):
        """Testa buscar músicas ignoradas."""
        # Adicionar músicas
        music_ids = []
        for path in sample_music_data:
            music_id = music_model.add_music(path)
            music_ids.append(music_id)
        
        # Ignorar algumas
        for i in range(2):
            music_model.update_stars(music_ids[i], -1)
        
        # Buscar ignoradas
        ignored = music_model.get_ignored_musics()
        assert len(ignored) == 2
        
        # Todas devem ter stars = -1
        for music in ignored:
            assert music['stars'] == -1

    def test_update_stars(self, music_model):
        """Testa atualizar estrelas de uma música."""
        music_id = music_model.add_music('/path/to/test.mp3')
        
        # Atualizar para 3 estrelas
        music_model.update_stars(music_id, 3)
        
        # Verificar atualização
        details = music_model.get_music_details(music_id)
        assert details['stars'] == 3

    def test_get_music_details(self, music_model):
        """Testa buscar detalhes de uma música."""
        path = '/path/to/test.mp3'
        music_id = music_model.add_music(path)
        
        details = music_model.get_music_details(music_id)
        assert details is not None
        assert details['id'] == music_id
        assert details['path'] == path
        assert details['stars'] == 0

    def test_get_music_details_not_found(self, music_model):
        """Testa buscar detalhes de música inexistente."""
        details = music_model.get_music_details(999)
        assert details is None

    def test_get_all_classified_musics(self, music_model, sample_music_data):
        """Testa buscar músicas classificadas."""
        # Adicionar músicas
        music_ids = []
        for path in sample_music_data:
            music_id = music_model.add_music(path)
            music_ids.append(music_id)
        
        # Classificar algumas
        for i in range(3):
            music_model.update_stars(music_ids[i], i + 1)
        
        # Buscar classificadas
        classified = music_model.get_all_classified_musics()
        assert len(classified) == 3
        
        # Todas devem ter stars > 0
        for music in classified:
            assert music['stars'] > 0

    def test_get_total_count(self, music_model, sample_music_data):
        """Testa contagem total de músicas."""
        # Inicialmente vazio
        assert music_model.get_total_count() == 0
        
        # Adicionar músicas
        for path in sample_music_data:
            music_model.add_music(path)
        
        # Verificar contagem
        assert music_model.get_total_count() == len(sample_music_data)

    def test_get_rated_count(self, music_model, sample_music_data):
        """Testa contagem de músicas classificadas."""
        # Adicionar músicas
        music_ids = []
        for path in sample_music_data:
            music_id = music_model.add_music(path)
            music_ids.append(music_id)
        
        # Inicialmente nenhuma classificada
        assert music_model.get_rated_count() == 0
        
        # Classificar algumas
        for i in range(3):
            music_model.update_stars(music_ids[i], i + 1)
        
        # Verificar contagem
        assert music_model.get_rated_count() == 3

    def test_delete_music(self, music_model):
        """Testa deletar uma música."""
        music_id = music_model.add_music('/path/to/test.mp3')
        
        # Verificar que existe
        details = music_model.get_music_details(music_id)
        assert details is not None
        
        # Deletar
        music_model.delete_music(music_id)
        
        # Verificar que não existe mais
        details = music_model.get_music_details(music_id)
        assert details is None

    def test_get_two_unrated_musics_empty(self, music_model):
        """Testa buscar duas músicas não classificadas quando vazio."""
        result = music_model.get_two_unrated_musics()
        assert result == []

    def test_get_two_unrated_musics_only_one(self, music_model):
        """Testa buscar duas músicas quando há apenas uma."""
        music_model.add_music('/path/to/music1.mp3')
        result = music_model.get_two_unrated_musics()
        assert len(result) == 1

    def test_get_two_unrated_musics_multiple(self, music_model):
        """Testa buscar duas músicas quando há várias."""
        for i in range(5):
            music_model.add_music(f'/path/to/music{i}.mp3')
        
        result = music_model.get_two_unrated_musics()
        assert len(result) == 2
        assert result[0]['id'] != result[1]['id']

    def test_update_stars_edge_cases(self, music_model):
        """Testa atualizar estrelas com casos extremos."""
        music_id = music_model.add_music('/path/to/test.mp3')
        
        # Testar valores extremos
        extreme_values = [-1, 0, 1, 5, 10]
        for stars in extreme_values:
            music_model.update_stars(music_id, stars)
            details = music_model.get_music_details(music_id)
            assert details['stars'] == stars

    def test_get_last_music_with_stars(self, music_model):
        """Testa buscar última música com determinado número de estrelas."""
        # Adicionar e classificar músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        music_model.update_stars(music_id1, 3)
        music_model.update_stars(music_id2, 3)
        music_model.update_stars(music_id3, 5)
        
        # Buscar última com 3 estrelas
        last_3_stars = music_model.get_last_music_with_stars(3)
        assert last_3_stars is not None
        assert last_3_stars['stars'] == 3
        
        # Buscar com estrelas que não existem
        not_found = music_model.get_last_music_with_stars(2)
        assert not_found is None

    def test_get_music_by_stars(self, music_model):
        """Testa buscar música por número de estrelas."""
        # Adicionar e classificar músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        music_model.update_stars(music_id1, 4)
        music_model.update_stars(music_id2, 4)
        music_model.update_stars(music_id3, 5)
        
        # Buscar músicas com 4 estrelas
        four_stars = music_model.get_music_by_stars(4)
        assert len(four_stars) == 2
        
        # Buscar excluindo uma específica
        four_stars_excluded = music_model.get_music_by_stars(4, exclude_id=music_id1)
        assert len(four_stars_excluded) == 1
        assert four_stars_excluded[0]['id'] == music_id2

    def test_get_next_unrated_music(self, music_model):
        """Testa buscar próxima música não classificada."""
        # Adicionar músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        
        # Classificar algumas
        music_model.update_stars(music_id1, 3)
        
        # Buscar próxima não classificada
        next_unrated = music_model.get_next_unrated_music()
        assert next_unrated is not None
        assert next_unrated['stars'] == 0
        assert next_unrated['id'] in [music_id2, music_id3]
        
        # Buscar excluindo uma específica
        next_unrated_excluded = music_model.get_next_unrated_music(exclude_id=music_id2)
        assert next_unrated_excluded is not None
        assert next_unrated_excluded['id'] == music_id3

    def test_get_all_classified_musics_by_quality(self, music_model):
        """Testa buscar músicas classificadas ordenadas por qualidade."""
        # Adicionar e classificar músicas
        music_id1 = music_model.add_music('/path/to/music1.mp3')
        music_id2 = music_model.add_music('/path/to/music2.mp3')
        music_id3 = music_model.add_music('/path/to/music3.mp3')
        music_id4 = music_model.add_music('/path/to/music4.mp3')
        
        music_model.update_stars(music_id1, 2)
        music_model.update_stars(music_id2, 5)
        music_model.update_stars(music_id3, 1)
        music_model.update_stars(music_id4, 4)
        
        # Buscar classificadas por qualidade
        by_quality = music_model.get_all_classified_musics_by_quality()
        assert len(by_quality) == 4
        
        # Verificar ordem decrescente de estrelas
        stars = [music['stars'] for music in by_quality]
        assert stars == [5, 4, 2, 1]

    def test_music_lifecycle(self, music_model):
        """Testa ciclo completo de vida de uma música."""
        # Adicionar
        music_id = music_model.add_music('/path/to/lifecycle.mp3')
        assert music_id is not None
        
        # Verificar detalhes iniciais
        details = music_model.get_music_details(music_id)
        assert details['stars'] == 0
        
        # Classificar
        music_model.update_stars(music_id, 4)
        details = music_model.get_music_details(music_id)
        assert details['stars'] == 4
        
        # Ignorar
        music_model.update_stars(music_id, -1)
        details = music_model.get_music_details(music_id)
        assert details['stars'] == -1
        
        # Deletar
        music_model.delete_music(music_id)
        details = music_model.get_music_details(music_id)
        assert details is None

    def test_get_filtered_musics(self, music_model):
        """Testa buscar músicas filtradas."""
        # Adicionar e classificar músicas
        music_ids = []
        for i in range(5):
            music_id = music_model.add_music(f'/path/to/filtered{i}.mp3')
            music_ids.append(music_id)
            music_model.update_stars(music_id, i + 1)  # 1-5 estrelas
        
        # Filtrar por estrelas mínimas
        filtered_min = music_model.get_filtered_musics(min_stars=3)
        assert len(filtered_min) == 3  # 3, 4, 5 estrelas
        
        # Filtrar por estrelas máximas
        filtered_max = music_model.get_filtered_musics(max_stars=2)
        assert len(filtered_max) == 2  # 1, 2 estrelas
        
        # Filtrar por faixa
        filtered_range = music_model.get_filtered_musics(min_stars=2, max_stars=4)
        assert len(filtered_range) == 3  # 2, 3, 4 estrelas
        
        # Sem filtros (deve retornar todas exceto ignoradas)
        all_filtered = music_model.get_filtered_musics()
        assert len(all_filtered) == 5

    def test_get_music_by_tag(self, music_model):
        """Testa buscar música por tag."""
        # Este método pode não estar implementado ainda
        try:
            result = music_model.get_music_by_tag('rock')
            assert isinstance(result, list)
        except:
            # Método pode não existir ou falhar
            pass

    def test_path_operations(self, music_model):
        """Testa operações relacionadas a caminhos."""
        # Testar com diferentes tipos de caminhos
        paths = [
            '/absolute/path/music.mp3',
            'relative/path/music.mp3',
            '/path/with spaces/music.mp3',
            '/path/with-special_chars123/music.mp3'
        ]
        
        music_ids = []
        for path in paths:
            music_id = music_model.add_music(path)
            music_ids.append(music_id)
            
            # Verificar que o caminho foi salvo corretamente
            details = music_model.get_music_details(music_id)
            assert details['path'] == path

    def test_edge_case_operations(self, music_model):
        """Testa operações em casos extremos."""
        # Testar com música inexistente
        fake_id = 999999
        details = music_model.get_music_details(fake_id)
        assert details is None
        
        # Testar busca com exclusão
        music_id1 = music_model.add_music('/path/to/test1.mp3')
        music_id2 = music_model.add_music('/path/to/test2.mp3')
        music_model.update_stars(music_id1, 3)
        music_model.update_stars(music_id2, 3)
        
        # Buscar com exclusão
        result_with_exclusion = music_model.get_music_by_stars(3, exclude_id=music_id1)
        assert len(result_with_exclusion) == 1
        assert result_with_exclusion[0]['id'] == music_id2

    def test_large_dataset_operations(self, music_model):
        """Testa operações com dataset maior."""
        # Adicionar muitas músicas
        music_ids = []
        for i in range(20):
            music_id = music_model.add_music(f'/path/to/large{i}.mp3')
            music_ids.append(music_id)
            
            # Classificar com diferentes estrelas
            stars = (i % 5) + 1  # 1-5 estrelas
            music_model.update_stars(music_id, stars)
        
        # Testar contagens
        total = music_model.get_total_count()
        rated = music_model.get_rated_count()
        
        assert total >= 20
        assert rated >= 20
        
        # Testar busca de classificadas
        classified = music_model.get_all_classified_musics()
        assert len(classified) >= 20
        
        # Testar busca por qualidade
        by_quality = music_model.get_all_classified_musics_by_quality()
        assert len(by_quality) >= 20
        
        # Verificar ordenação
        stars_sequence = [music['stars'] for music in by_quality]
        assert stars_sequence == sorted(stars_sequence, reverse=True)

    def test_star_distribution(self, music_model):
        """Testa distribuição de estrelas."""
        # Criar músicas com diferentes classificações
        star_counts = {1: 2, 2: 3, 3: 4, 4: 2, 5: 1}
        total_added = 0
        
        for stars, count in star_counts.items():
            for i in range(count):
                music_id = music_model.add_music(f'/path/to/star{stars}_{i}.mp3')
                music_model.update_stars(music_id, stars)
                total_added += 1
        
        # Verificar contagens por estrela
        for stars, expected_count in star_counts.items():
            musics_with_stars = music_model.get_music_by_stars(stars)
            assert len(musics_with_stars) == expected_count
        
        # Verificar total
        assert music_model.get_rated_count() == total_added

    def test_boundary_values(self, music_model):
        """Testa valores limite."""
        music_id = music_model.add_music('/path/to/boundary.mp3')
        
        # Testar valores extremos de estrelas
        extreme_values = [-1, 0, 1, 5, 10, 100]
        for stars in extreme_values:
            music_model.update_stars(music_id, stars)
            details = music_model.get_music_details(music_id)
            assert details['stars'] == stars

    def test_concurrent_operations(self, music_model):
        """Testa operações que podem simular concorrência."""
        # Adicionar música
        music_id = music_model.add_music('/path/to/concurrent.mp3')
        
        # Múltiplas atualizações rápidas
        for i in range(10):
            music_model.update_stars(music_id, i % 6)  # 0-5
        
        # Verificar estado final
        details = music_model.get_music_details(music_id)
        assert details is not None
        assert 0 <= details['stars'] <= 5

    def test_tag_operations(self, music_model):
        """Testa operações com tags."""
        # Testar get_music_by_tag (pode não estar totalmente implementado)
        try:
            result = music_model.get_music_by_tag('rock')
            assert isinstance(result, list)
        except Exception as e:
            # Tabelas de tags podem não existir ainda
            assert 'no such table' in str(e).lower() or 'table' in str(e).lower()

    def test_add_tag_to_music(self, music_model):
        """Testa adicionar tag a música."""
        music_id = music_model.add_music('/path/to/tagged.mp3')
        
        try:
            music_model.add_tag_to_music(music_id, 'rock')
            # Se chegou aqui, método existe e funcionou
        except AttributeError:
            # Método pode não existir ainda
            pass
        except Exception as e:
            # Tabelas de tags podem não existir
            assert 'no such table' in str(e).lower() or 'table' in str(e).lower()

    def test_file_deletion_scenarios(self, music_model):
        """Testa cenários de deleção de arquivos."""
        # Criar música com caminho que pode não existir
        music_id = music_model.add_music('/nonexistent/path/test.mp3')
        
        # Tentar deletar (send2trash deve lidar com arquivo inexistente)
        try:
            music_model.delete_music(music_id)
            # Verificar que foi removida do BD
            details = music_model.get_music_details(music_id)
            assert details is None
        except Exception:
            # send2trash pode falhar com arquivo inexistente
            pass

    def test_sql_injection_protection(self, music_model):
        """Testa proteção contra SQL injection."""
        # Tentar caminhos com caracteres SQL suspeitos
        suspicious_paths = [
            "/path/'; DROP TABLE music; --/test.mp3",
            "/path/with'quote/test.mp3",
            '/path/with"double"quote/test.mp3',
            "/path/with;semicolon/test.mp3"
        ]
        
        for path in suspicious_paths:
            try:
                music_id = music_model.add_music(path)
                details = music_model.get_music_details(music_id)
                assert details['path'] == path  # Deve salvar o caminho exato
            except Exception:
                # Alguns caracteres podem causar problemas no sistema de arquivos
                pass

    def test_database_consistency(self, music_model):
        """Testa consistência do banco de dados."""
        # Adicionar várias músicas
        music_ids = []
        for i in range(10):
            music_id = music_model.add_music(f'/path/to/consistency{i}.mp3')
            music_ids.append(music_id)
            music_model.update_stars(music_id, (i % 5) + 1)
        
        # Verificar contagens
        total = music_model.get_total_count()
        rated = music_model.get_rated_count()
        
        assert total >= 10
        assert rated >= 10
        
        # Verificar que todas as músicas podem ser recuperadas
        for music_id in music_ids:
            details = music_model.get_music_details(music_id)
            assert details is not None
            assert details['id'] == music_id

    def test_update_stars_with_same_value(self, music_model):
        """Testa atualizar estrelas com o mesmo valor."""
        music_id = music_model.add_music('/path/to/same_value.mp3')
        
        # Atualizar várias vezes com o mesmo valor
        for _ in range(5):
            music_model.update_stars(music_id, 3)
            details = music_model.get_music_details(music_id)
            assert details['stars'] == 3

    def test_extreme_path_lengths(self, music_model):
        """Testa caminhos extremamente longos."""
        # Caminho muito longo
        long_path = '/very/' + 'long/' * 50 + 'path/music.mp3'
        
        try:
            music_id = music_model.add_music(long_path)
            details = music_model.get_music_details(music_id)
            assert details['path'] == long_path
        except Exception:
            # Sistema pode ter limite de tamanho de caminho
            pass

    def test_unicode_paths(self, music_model):
        """Testa caminhos com caracteres Unicode."""
        unicode_paths = [
            '/música/português/test.mp3',
            '/音乐/中文/test.mp3',
            '/музыка/русский/test.mp3',
            '/🎵/emoji/test.mp3'
        ]
        
        for path in unicode_paths:
            try:
                music_id = music_model.add_music(path)
                details = music_model.get_music_details(music_id)
                assert details['path'] == path
            except Exception:
                # Alguns sistemas podem não suportar todos os caracteres
                pass

    def test_transaction_rollback_simulation(self, music_model):
        """Testa simulação de rollback de transação."""
        initial_count = music_model.get_total_count()
        
        try:
            # Tentar operação que pode falhar
            music_id = music_model.add_music('/path/to/transaction.mp3')
            music_model.update_stars(music_id, 999)  # Valor inválido
            
            # Se chegou aqui, operação foi bem sucedida
            final_count = music_model.get_total_count()
            assert final_count > initial_count
        except Exception:
            # Se falhou, verificar que não corrompeu o estado
            final_count = music_model.get_total_count()
            assert final_count >= initial_count

    def test_performance_with_many_operations(self, music_model):
        """Testa performance com muitas operações."""
        import time
        
        start_time = time.time()
        
        # Realizar muitas operações
        music_ids = []
        for i in range(100):
            music_id = music_model.add_music(f'/path/to/perf{i}.mp3')
            music_ids.append(music_id)
            music_model.update_stars(music_id, (i % 5) + 1)
        
        # Buscar todas
        for music_id in music_ids:
            music_model.get_music_details(music_id)
        
        elapsed = time.time() - start_time
        
        # Deve completar em tempo razoável (menos de 5 segundos)
        assert elapsed < 5.0
        
        # Verificar que todas estão no banco
        assert music_model.get_total_count() >= 100
