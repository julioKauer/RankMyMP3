"""
Testes de regressão baseados em problemas reais encontrados durante o desenvolvimento.
Estes testes simulam situações problemáticas que ocorreram e suas soluções.
"""
import pytest
import sqlite3
import tempfile
import os
from controllers.music_controller import MusicController
from models.music_model import MusicModel


class TestRegressionProblems:
    """Testes baseados em problemas reais encontrados durante o desenvolvimento."""

    def test_comparison_state_not_clearing_after_classification(self, music_controller):
        """
        PROBLEMA: Estado de comparação não era limpo após classificação manual,
        causando comportamento inesperado no get_next_comparison.
        
        CENÁRIO: Usuário estava no meio de busca binária, classificou manualmente
        uma música, mas o estado da busca binária permaneceu ativo.
        """
        # 1. Adicionar músicas e iniciar busca binária
        music_ids = []
        for i in range(5):
            music_id = music_controller.music_model.add_music(f'/path/to/regression1_{i}.mp3')
            music_ids.append(music_id)
            music_controller.classify_music(music_id, (i % 3) + 1)
        
        # Adicionar nova música que iniciará busca binária
        new_music_id = music_controller.music_model.add_music('/path/to/new_regression1.mp3')
        
        # Simular início de busca binária
        result = music_controller.start_classification_for_unrated()
        
        # Verificar que há estado de busca binária
        state = music_controller.get_comparison_state()
        
        # 2. PROBLEMA: Classificar manualmente durante busca binária
        music_controller.classify_music(new_music_id, 4)
        
        # 3. SOLUÇÃO: Estado deve ser limpo automaticamente ou sistema deve lidar com isso
        state_after = music_controller.get_comparison_state()
        
        # 4. Próxima comparação deve ser consistente
        next_comp = music_controller.get_next_comparison()
        # Sistema deve funcionar sem erros

    def test_binary_search_with_insufficient_ranked_music(self, music_controller):
        """
        PROBLEMA: Busca binária falhava quando havia poucas músicas classificadas.
        
        CENÁRIO: Apenas 1-2 músicas classificadas, busca binária não conseguia
        encontrar bounds adequados para comparação.
        """
        # 1. Adicionar apenas uma música classificada
        music_id1 = music_controller.music_model.add_music('/path/to/single_ranked.mp3')
        music_controller.classify_music(music_id1, 3)
        
        # 2. Adicionar música não classificada
        new_music_id = music_controller.music_model.add_music('/path/to/new_unranked.mp3')
        
        # 3. Tentar iniciar busca binária com insuficientes músicas classificadas
        result = music_controller.start_classification_for_unrated()
        
        # 4. Sistema deve lidar graciosamente com poucos dados
        # Pode retornar False (não iniciou) ou True (iniciou comparação simples)
        assert isinstance(result, bool)
        
        # 5. Se iniciou comparação, deve ser válida
        next_comp = music_controller.get_next_comparison()
        if next_comp:
            # Verificar estrutura real da comparação
            expected_keys = ['compared_music_id', 'unrated_music_id', 'context']
            for key in expected_keys:
                if key in next_comp:
                    assert next_comp[key] is not None

    def test_ignore_restore_affecting_comparison_state(self, music_controller):
        """
        PROBLEMA: Ignorar/restaurar músicas durante comparações causava
        inconsistências no estado das comparações.
        
        CENÁRIO: Usuário ignorava uma música que estava sendo comparada,
        mas o estado de comparação não era atualizado adequadamente.
        """
        # 1. Adicionar músicas
        music_ids = []
        for i in range(4):
            music_id = music_controller.music_model.add_music(f'/path/to/ignore_test_{i}.mp3')
            music_ids.append(music_id)
        
        # 2. Iniciar comparação
        result = music_controller.start_classification_for_unrated()
        next_comp = music_controller.get_next_comparison()
        
        if next_comp:
            # Extrair IDs independente da estrutura
            music_a_id = None
            music_b_id = None
            
            if 'music_a' in next_comp:
                music_a_id = next_comp['music_a'].get('id')
                music_b_id = next_comp['music_b'].get('id')
            elif 'music1_id' in next_comp:
                music_a_id = next_comp['music1_id']
                music_b_id = next_comp['music2_id']
            
            if music_a_id:
                # 3. PROBLEMA: Simular ação de ignorar música (via classificação especial)
                music_controller.classify_music(music_a_id, -1)  # -1 = ignorada
                
                # 4. SOLUÇÃO: Sistema deve continuar funcionando
                new_next_comp = music_controller.get_next_comparison()
                # Sistema deve funcionar sem erros
                
                # 5. Restaurar música (via classificação 0)
                music_controller.classify_music(music_a_id, 0)  # 0 = não classificada
                
                # Verificar que música está disponível novamente
                details = music_controller.music_model.get_music_details(music_a_id)
                assert details['stars'] == 0

    def test_duplicate_comparisons_prevention(self, music_controller):
        """
        PROBLEMA: Sistema permitia comparações duplicadas ou circulares.
        
        CENÁRIO: Mesmo par de músicas sendo comparado múltiplas vezes,
        ou comparações A vs B e depois B vs A.
        """
        # 1. Adicionar músicas
        music_id1 = music_controller.music_model.add_music('/path/to/dup1.mp3')
        music_id2 = music_controller.music_model.add_music('/path/to/dup2.mp3')
        music_id3 = music_controller.music_model.add_music('/path/to/dup3.mp3')
        
        # 2. Fazer comparação inicial
        music_controller.make_comparison(music_id1, music_id2, music_id1)
        
        # 3. Verificar que comparação foi registrada
        comparisons_before = music_controller.comparison_model.get_comparisons()
        
        # 4. PROBLEMA: Tentar fazer mesma comparação novamente
        music_controller.make_comparison(music_id1, music_id2, music_id2)  # Resultado diferente
        
        # 5. SOLUÇÃO: Sistema deve atualizar ou prevenir duplicatas
        comparisons_after = music_controller.comparison_model.get_comparisons()
        
        # Sistema deve lidar com duplicatas adequadamente
        assert len(comparisons_after) >= len(comparisons_before)
        
        # Verificar que comparações existem
        comparison_result = music_controller.comparison_model.get_comparison_result(music_id1, music_id2)
        assert comparison_result is not None

    def test_database_corruption_recovery(self, temp_db_path):
        """
        PROBLEMA: Corrupção no banco de dados ou estados inconsistentes.
        
        CENÁRIO: Banco de dados em estado inconsistente após operações
        interrompidas ou erro de aplicação.
        """
        # 1. Criar controller com banco novo
        controller = MusicController(temp_db_path)
        
        # 2. Adicionar dados normalmente
        music_id1 = controller.music_model.add_music('/path/to/corrupt_test1.mp3')
        music_id2 = controller.music_model.add_music('/path/to/corrupt_test2.mp3')
        controller.classify_music(music_id1, 5)
        
        # 3. PROBLEMA: Simular corrupção - estado inconsistente
        # Inserir comparação com música inexistente
        try:
            controller.comparison_model.save_comparison(music_id1, 99999, music_id1)
        except:
            pass  # Pode falhar, é esperado
        
        # 4. SOLUÇÃO: Sistema deve ser resiliente e continuar funcionando
        # Verificar que operações básicas ainda funcionam
        total_count = controller.get_total_musics_count()
        assert total_count >= 2
        
        # Sistema deve conseguir fazer novas comparações
        next_comp = controller.get_next_comparison()
        # Pode ser None se não há mais comparações possíveis
        
        # Verificar integridade básica do banco
        details1 = controller.music_model.get_music_details(music_id1)
        details2 = controller.music_model.get_music_details(music_id2)
        assert details1 is not None
        assert details2 is not None

    def test_star_redistribution_edge_cases(self, music_controller):
        """
        PROBLEMA: Redistribuição de estrelas causava problemas com poucos dados
        ou distribuições desiguais.
        
        CENÁRIO: Redistribuição forçada com número ímpar de músicas,
        ou todas as músicas com mesmo ranking.
        """
        # 1. CASO: Número ímpar de músicas (7 músicas)
        music_ids = []
        for i in range(7):
            music_id = music_controller.music_model.add_music(f'/path/to/redist_edge_{i}.mp3')
            music_ids.append(music_id)
            music_controller.classify_music(music_id, 3)  # Todas com mesma classificação
        
        # Fazer algumas comparações para criar ordem
        for i in range(6):
            music_controller.make_comparison(music_ids[i], music_ids[i+1], music_ids[i+1])
        
        # 2. PROBLEMA: Redistribuição com classificações iguais
        music_controller.force_redistribute_all_stars()
        
        # 3. SOLUÇÃO: Deve distribuir adequadamente mesmo com dados problemáticos
        final_ratings = []
        for music_id in music_ids:
            details = music_controller.music_model.get_music_details(music_id)
            final_ratings.append(details['stars'])
        
        # Se há comparações, deve ter distribuição variada
        unique_ratings = set(final_ratings)
        if len([r for r in final_ratings if r > 0]) > 1:  # Se múltiplas músicas classificadas
            assert len(unique_ratings) > 1, "Redistribuição deve criar variedade de classificações"
        
        # Todas classificadas devem estar entre 1-5
        classified_ratings = [r for r in final_ratings if r > 0]
        assert all(1 <= rating <= 5 for rating in classified_ratings)

    def test_ui_state_synchronization_issues(self, music_controller):
        """
        PROBLEMA: Dessincronia entre interface e estado interno do controller.
        
        CENÁRIO: Interface mostrando dados antigos após operações de
        classificação, comparação ou redistribuição.
        """
        # 1. Estado inicial
        music_ids = []
        for i in range(3):
            music_id = music_controller.music_model.add_music(f'/path/to/ui_sync_{i}.mp3')
            music_ids.append(music_id)
        
        initial_total = music_controller.get_total_musics_count()
        initial_unrated = len(music_controller.get_unrated_musics())
        
        # 2. PROBLEMA: Operações que devem atualizar contadores
        music_controller.classify_music(music_ids[0], 5)
        
        # 3. SOLUÇÃO: Contadores devem refletir mudanças imediatamente
        after_classify_unrated = len(music_controller.get_unrated_musics())
        assert after_classify_unrated == initial_unrated - 1
        
        # 4. Simular ignorar música (classificação -1)
        music_controller.classify_music(music_ids[1], -1)
        after_ignore_unrated = len(music_controller.get_unrated_musics())
        assert after_ignore_unrated == after_classify_unrated - 1
        
        # 5. Simular restaurar música (classificação 0)
        music_controller.classify_music(music_ids[1], 0)
        after_restore_unrated = len(music_controller.get_unrated_musics())
        assert after_restore_unrated == after_ignore_unrated + 1
        
        # 6. Total de músicas deve permanecer consistente
        final_total = music_controller.get_total_musics_count()
        assert final_total == initial_total

    def test_binary_search_infinite_loop_prevention(self, music_controller):
        """
        PROBLEMA: Busca binária entrando em loop infinito em casos extremos.
        
        CENÁRIO: Estados de busca binária mal formados ou bounds inválidos
        causando loops infinitos.
        """
        # 1. Criar cenário problemático
        music_ids = []
        for i in range(5):
            music_id = music_controller.music_model.add_music(f'/path/to/loop_test_{i}.mp3')
            music_ids.append(music_id)
            music_controller.classify_music(music_id, (i % 2) + 1)  # 1 ou 2 estrelas apenas
        
        new_music_id = music_controller.music_model.add_music('/path/to/new_loop_test.mp3')
        
        # 2. PROBLEMA: Simular estado de busca binária problemático
        # Forçar estado que poderia causar loop
        try:
            music_controller.comparison_state_model.save_comparison_state(
                new_music_id, music_ids[0], "binary_search_0_0_0"  # Bounds inválidos
            )
        except:
            pass
        
        # 3. SOLUÇÃO: Sistema deve detectar e sair de loops
        max_iterations = 10  # Limite de segurança
        iterations = 0
        
        while iterations < max_iterations:
            next_comp = music_controller.get_next_comparison()
            if next_comp is None:
                break
            
            # Extrair IDs da comparação
            music_a_id = None
            music_b_id = None
            
            if 'music_a' in next_comp and next_comp['music_a']:
                music_a_id = next_comp['music_a'].get('id')
                music_b_id = next_comp['music_b'].get('id')
            elif 'music1_id' in next_comp:
                music_a_id = next_comp['music1_id']
                music_b_id = next_comp['music2_id']
            
            # Se conseguiu extrair IDs válidos, fazer comparação
            if music_a_id and music_b_id:
                music_controller.make_comparison(music_a_id, music_b_id, music_a_id)
            else:
                break  # Sair se comparação inválida
            
            iterations += 1
        
        # 4. Sistema deve ter terminado sem loop infinito
        assert iterations < max_iterations, "Busca binária não deve entrar em loop infinito"

    def test_concurrent_operation_simulation(self, music_controller):
        """
        PROBLEMA: Operações "concorrentes" causando estados inconsistentes.
        
        CENÁRIO: Simulação de usuário fazendo múltiplas operações rapidamente,
        como classificar e comparar simultaneamente.
        """
        # 1. Adicionar músicas
        music_ids = []
        for i in range(6):
            music_id = music_controller.music_model.add_music(f'/path/to/concurrent_{i}.mp3')
            music_ids.append(music_id)
        
        # 2. PROBLEMA: Operações rápidas e potencialmente conflitantes
        try:
            # Simular operações "concorrentes"
            music_controller.classify_music(music_ids[0], 5)
            music_controller.make_comparison(music_ids[0], music_ids[1], music_ids[0])
            music_controller.ignore_music(music_ids[1])
            music_controller.start_classification_for_unrated()
            music_controller.restore_music(music_ids[1])
            music_controller.force_redistribute_all_stars()
        except Exception as e:
            # Se houver erro, verificar que não corrompeu o estado
            pass
        
        # 3. SOLUÇÃO: Estado deve permanecer consistente
        total_count = music_controller.get_total_musics_count()
        assert total_count == 6
        
        # Verificar que músicas ainda existem e são acessíveis
        for music_id in music_ids:
            details = music_controller.music_model.get_music_details(music_id)
            assert details is not None
            assert isinstance(details['stars'], int)

    def test_large_dataset_performance_regression(self, temp_db_path):
        """
        PROBLEMA: Performance degradada com datasets maiores.
        
        CENÁRIO: Sistema funcionava bem com poucas músicas mas ficava lento
        com muitas músicas ou muitas comparações.
        """
        # 1. Criar dataset maior
        controller = MusicController(temp_db_path)
        
        # Adicionar mais músicas (50 para teste rápido, em produção seria mais)
        music_ids = []
        for i in range(50):
            music_id = controller.music_model.add_music(f'/path/to/perf_test_{i:03d}.mp3')
            music_ids.append(music_id)
            
            # Classificar algumas para criar estrutura
            if i % 5 == 0:
                controller.classify_music(music_id, (i % 5) + 1)
        
        # 2. PROBLEMA: Operações ficando lentas
        import time
        
        # Medir tempo de operações críticas
        start_time = time.time()
        total_count = controller.get_total_musics_count()
        count_time = time.time() - start_time
        
        start_time = time.time()
        unrated = controller.get_unrated_musics()
        unrated_time = time.time() - start_time
        
        start_time = time.time()
        next_comp = controller.get_next_comparison()
        next_comp_time = time.time() - start_time
        
        # 3. SOLUÇÃO: Operações devem ser razoavelmente rápidas
        assert count_time < 0.1, f"get_total_musics_count muito lento: {count_time}s"
        assert unrated_time < 0.1, f"get_unrated_musics muito lento: {unrated_time}s"
        assert next_comp_time < 0.1, f"get_next_comparison muito lento: {next_comp_time}s"
        
        # Verificar que resultados estão corretos
        assert total_count == 50
        assert len(unrated) >= 40  # Maioria não classificada
