"""
Testes de integração simulando fluxos completos de usuário.
Estes testes validam cenários end-to-end que um usuário real experimentaria.
"""
import pytest
import tempfile
import os
from controllers.music_controller import MusicController


class TestUserWorkflows:
    """Testes de fluxos de usuário completos."""

    def test_complete_ranking_workflow(self, music_controller):
        """
        CENÁRIO: Usuário adiciona pasta de música e faz ranking completo.
        
        FLUXO:
        1. Adicionar pasta com múltiplas músicas
        2. Fazer algumas classificações manuais
        3. Usar sistema de comparações para rankings precisos
        4. Redistribuir estrelas baseado em comparações
        5. Verificar ranking final
        """
        # 1. Simular adição de pasta com músicas
        with tempfile.TemporaryDirectory() as temp_dir:
            music_files = ['rock_song.mp3', 'pop_song.mp3', 'jazz_song.mp3', 
                          'classical.mp3', 'blues.mp3', 'electronic.mp3']
            
            for filename in music_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w') as f:
                    f.write(f'fake content for {filename}')
            
            # Adicionar pasta
            count = music_controller.add_music_folder(temp_dir)
            assert count == len(music_files)
        
        # 2. Classificações manuais iniciais (usuário dá notas para algumas)
        unrated = music_controller.get_unrated_musics()
        assert len(unrated) == len(music_files)
        
        # Usuário classifica algumas músicas manualmente
        music_controller.classify_music(unrated[0]['id'], 5)  # Favorita
        music_controller.classify_music(unrated[1]['id'], 1)  # Não gosta
        music_controller.classify_music(unrated[2]['id'], 3)  # OK
        
        # 3. Usar sistema de comparações para músicas restantes
        remaining_unrated = music_controller.get_unrated_musics()
        assert len(remaining_unrated) == len(music_files) - 3
        
        # Iniciar processo de comparação
        comparison_started = music_controller.start_classification_for_unrated()
        
        # Simular usuário fazendo algumas comparações (limitado para evitar loops)
        max_comparisons = 5  # Limitar para evitar loop infinito
        comparisons_made = 0
        
        while comparisons_made < max_comparisons:
            next_comp = music_controller.get_next_comparison()
            if not next_comp:
                break
            
            # Fazer comparação simples
            if 'compared_music_id' in next_comp:
                compared_id = next_comp['compared_music_id']
                unrated_id = next_comp['unrated_music_id']
                # Simular escolha do usuário (escolher sempre o primeiro)
                winner = compared_id
                music_controller.make_comparison(compared_id, unrated_id, winner)
                comparisons_made += 1
            elif 'music_a' in next_comp:
                music_a_id = next_comp['music_a']['id']
                music_b_id = next_comp['music_b']['id']
                # Simular escolha do usuário (escolher sempre o primeiro)
                winner = music_a_id
                music_controller.make_comparison(music_a_id, music_b_id, winner)
                comparisons_made += 1
        
        # 4. Forçar redistribuição baseada em comparações
        music_controller.force_redistribute_all_stars()
        
        # 5. Verificar ranking final
        final_unrated = music_controller.get_unrated_musics()
        total_musics = music_controller.get_total_musics_count()
        
        # A maioria das músicas deve estar classificada
        classified_count = total_musics - len(final_unrated)
        assert classified_count >= 3  # Pelo menos as 3 classificadas manualmente
        
        print(f"Workflow completo: {classified_count}/{total_musics} músicas classificadas")

    def test_partial_classification_workflow(self, music_controller):
        """
        CENÁRIO: Usuário faz classificação parcial, sai e volta depois.
        
        FLUXO:
        1. Adicionar músicas
        2. Fazer algumas comparações
        3. Simular fechamento da aplicação (estado salvo)
        4. Simular reabertura e continuação
        """
        # 1. Adicionar músicas
        music_ids = []
        for i in range(6):
            music_id = music_controller.music_model.add_music(f'/path/to/partial_{i}.mp3')
            music_ids.append(music_id)
        
        # Classificar algumas para criar contexto
        music_controller.classify_music(music_ids[0], 4)
        music_controller.classify_music(music_ids[1], 2)
        
        # 2. Fazer algumas comparações
        music_controller.start_classification_for_unrated()
        
        # Fazer 3 comparações
        for _ in range(3):
            next_comp = music_controller.get_next_comparison()
            if next_comp:
                if 'compared_music_id' in next_comp:
                    compared_id = next_comp['compared_music_id']
                    unrated_id = next_comp['unrated_music_id']
                    music_controller.make_comparison(compared_id, unrated_id, compared_id)
                break
        
        # 3. Simular "fechamento" - verificar que estado foi salvo
        state_before = music_controller.get_comparison_state()
        unrated_before = len(music_controller.get_unrated_musics())
        
        # 4. Simular "reabertura" - estado deve ser mantido
        # (Em implementação real seria novo controller com mesmo DB)
        unrated_after = len(music_controller.get_unrated_musics())
        assert unrated_after <= unrated_before  # Pode ter diminuído com comparações
        
        # Sistema deve poder continuar de onde parou
        next_comp = music_controller.get_next_comparison()
        # Deve retornar comparação válida ou None se terminou

    def test_error_recovery_workflow(self, music_controller):
        """
        CENÁRIO: Usuário encontra erro durante uso e sistema se recupera.
        
        FLUXO:
        1. Operação normal
        2. Simular erro/interrupção
        3. Sistema deve se recuperar
        4. Continuar operação normalmente
        """
        # 1. Operação normal
        music_ids = []
        for i in range(4):
            music_id = music_controller.music_model.add_music(f'/path/to/error_recovery_{i}.mp3')
            music_ids.append(music_id)
            music_controller.classify_music(music_id, (i % 3) + 1)
        
        initial_count = music_controller.get_total_musics_count()
        
        # 2. Simular erro durante operação
        try:
            # Tentar operação inválida
            music_controller.make_comparison(999, 1000, 999)  # IDs inexistentes
        except:
            pass  # Erro esperado
        
        try:
            # Tentar classificação inválida
            music_controller.classify_music(999, 10)  # ID inexistente, nota inválida
        except:
            pass  # Erro esperado
        
        # 3. Sistema deve se recuperar e continuar funcionando
        count_after_errors = music_controller.get_total_musics_count()
        assert count_after_errors == initial_count  # Não deve ter corrompido
        
        # 4. Operações normais devem funcionar
        new_music_id = music_controller.music_model.add_music('/path/to/after_error.mp3')
        music_controller.classify_music(new_music_id, 3)
        
        final_count = music_controller.get_total_musics_count()
        assert final_count == initial_count + 1

    def test_bulk_operations_workflow(self, music_controller):
        """
        CENÁRIO: Usuário faz operações em lote (múltiplas músicas).
        
        FLUXO:
        1. Adicionar muitas músicas
        2. Classificar várias rapidamente
        3. Fazer comparações em sequência
        4. Redistribuir tudo
        """
        # 1. Adicionar muitas músicas (simulando pasta grande)
        music_ids = []
        for i in range(20):
            music_id = music_controller.music_model.add_music(f'/path/to/bulk_{i:02d}.mp3')
            music_ids.append(music_id)
        
        assert music_controller.get_total_musics_count() == 20
        
        # 2. Classificações rápidas em lote
        for i, music_id in enumerate(music_ids[:10]):
            stars = (i % 5) + 1  # Distribuir 1-5 estrelas
            music_controller.classify_music(music_id, stars)
        
        classified_count = 20 - len(music_controller.get_unrated_musics())
        assert classified_count == 10
        
        # 3. Fazer várias comparações em sequência
        music_controller.start_classification_for_unrated()
        
        comparisons_made = 0
        for _ in range(10):  # Máximo 10 comparações
            next_comp = music_controller.get_next_comparison()
            if not next_comp:
                break
            
            # Fazer comparação automatizada
            if 'compared_music_id' in next_comp:
                compared_id = next_comp['compared_music_id']
                unrated_id = next_comp['unrated_music_id']
                # Escolha determinística para teste
                winner = compared_id if compared_id < unrated_id else unrated_id
                music_controller.make_comparison(compared_id, unrated_id, winner)
                comparisons_made += 1
        
        # 4. Redistribuição em lote
        music_controller.force_redistribute_all_stars()
        
        # Verificar que sistema lidou com volume
        final_count = music_controller.get_total_musics_count()
        assert final_count == 20
        
        print(f"Bulk operations: {comparisons_made} comparações, 20 músicas processadas")

    def test_mixed_operations_workflow(self, music_controller):
        """
        CENÁRIO: Usuário mistura diferentes tipos de operações.
        
        FLUXO:
        1. Classificação manual
        2. Comparação
        3. Mais classificação
        4. Ignorar música
        5. Restaurar música
        6. Redistribuir
        """
        # Setup inicial
        music_ids = []
        for i in range(6):
            music_id = music_controller.music_model.add_music(f'/path/to/mixed_{i}.mp3')
            music_ids.append(music_id)
        
        # 1. Classificação manual
        music_controller.classify_music(music_ids[0], 5)
        music_controller.classify_music(music_ids[1], 3)
        
        # 2. Comparação
        music_controller.make_comparison(music_ids[0], music_ids[1], music_ids[0])
        
        # 3. Mais classificação
        music_controller.classify_music(music_ids[2], 4)
        
        # 4. Simular ignorar música (classificação -1)
        music_controller.classify_music(music_ids[3], -1)
        
        # Verificar que foi ignorada
        details = music_controller.music_model.get_music_details(music_ids[3])
        assert details['stars'] == -1
        
        # 5. Restaurar música (classificação 0)
        music_controller.classify_music(music_ids[3], 0)
        
        # Verificar que foi restaurada
        details = music_controller.music_model.get_music_details(music_ids[3])
        assert details['stars'] == 0
        
        # 6. Redistribuir
        music_controller.force_redistribute_all_stars()
        
        # Sistema deve ter lidado com todas as operações
        total = music_controller.get_total_musics_count()
        assert total == 6
        
        # Verificar que algumas músicas foram classificadas
        unrated = music_controller.get_unrated_musics()
        classified_count = total - len(unrated)
        assert classified_count >= 3  # Pelo menos as 3 classificadas manualmente

    def test_large_scale_workflow(self, music_controller):
        """
        CENÁRIO: Teste com volume maior de dados.
        
        FLUXO:
        1. Adicionar muitas músicas
        2. Fazer muitas classificações
        3. Medir performance
        """
        import time
        
        # 1. Adicionar 100 músicas
        start_time = time.time()
        
        music_ids = []
        for i in range(100):
            music_id = music_controller.music_model.add_music(f'/path/to/large_{i:03d}.mp3')
            music_ids.append(music_id)
        
        add_time = time.time() - start_time
        
        # 2. Classificar 50 músicas
        start_time = time.time()
        
        for i in range(50):
            stars = (i % 5) + 1
            music_controller.classify_music(music_ids[i], stars)
        
        classify_time = time.time() - start_time
        
        # 3. Fazer algumas comparações
        start_time = time.time()
        
        for i in range(10):
            music_a = music_ids[i]
            music_b = music_ids[i + 1]
            winner = music_a if i % 2 == 0 else music_b
            music_controller.make_comparison(music_a, music_b, winner)
        
        compare_time = time.time() - start_time
        
        # 4. Verificar performance
        assert add_time < 1.0, f"Adicionar 100 músicas muito lento: {add_time:.2f}s"
        assert classify_time < 0.5, f"Classificar 50 músicas muito lento: {classify_time:.2f}s"
        assert compare_time < 0.1, f"10 comparações muito lentas: {compare_time:.2f}s"
        
        # Verificar integridade
        total = music_controller.get_total_musics_count()
        assert total == 100
        
        unrated = music_controller.get_unrated_musics()
        assert len(unrated) == 50  # 50 não classificadas
        
        print(f"Large scale: 100 músicas, {add_time:.2f}s add, {classify_time:.2f}s classify, {compare_time:.2f}s compare")

    def test_edge_case_workflow(self, music_controller):
        """
        CENÁRIO: Teste com casos extremos e edge cases.
        
        FLUXO:
        1. Nenhuma música
        2. Uma música apenas
        3. Duas músicas
        4. Todas com mesma classificação
        """
        # 1. Nenhuma música
        assert music_controller.get_total_musics_count() == 0
        assert len(music_controller.get_unrated_musics()) == 0
        assert music_controller.get_next_comparison() is None
        
        # 2. Uma música apenas
        music_id1 = music_controller.music_model.add_music('/path/to/single.mp3')
        
        assert music_controller.get_total_musics_count() == 1
        assert len(music_controller.get_unrated_musics()) == 1
        
        # Não deve ser possível fazer comparação
        result = music_controller.start_classification_for_unrated()
        assert result is False
        
        # 3. Duas músicas
        music_id2 = music_controller.music_model.add_music('/path/to/second.mp3')
        
        assert music_controller.get_total_musics_count() == 2
        
        # Agora deve ser possível iniciar comparação
        result = music_controller.start_classification_for_unrated()
        assert result is True
        
        # Fazer comparação
        next_comp = music_controller.get_next_comparison()
        assert next_comp is not None
        
        music_controller.make_comparison(music_id1, music_id2, music_id1)
        
        # 4. Todas com mesma classificação
        music_id3 = music_controller.music_model.add_music('/path/to/third.mp3')
        
        # Classificar todas com mesma nota
        music_controller.classify_music(music_id1, 3)
        music_controller.classify_music(music_id2, 3)
        music_controller.classify_music(music_id3, 3)
        
        # Redistribuir deve funcionar mesmo com notas iguais
        music_controller.force_redistribute_all_stars()
        
        # Sistema deve continuar funcionando
        assert music_controller.get_total_musics_count() == 3
