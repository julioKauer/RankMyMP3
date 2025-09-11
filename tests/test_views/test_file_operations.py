"""
Testes para operações de arquivo - foco na cobertura da funcionalidade de mover músicas.
"""

import pytest
import os
import tempfile
import shutil
import sqlite3
from pathlib import Path

from models.music_model import MusicModel
from utils.database_initializer import DatabaseInitializer


class TestMusicModelUpdatePath:
    """Testa o método update_music_path no modelo com cobertura completa."""
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para banco de dados temporário."""
        import tempfile
        import sqlite3
        from utils.database_initializer import DatabaseInitializer
        
        # Criar banco temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Conectar e inicializar estrutura
        conn = sqlite3.connect(temp_file.name)
        initializer = DatabaseInitializer(conn)
        initializer.create_tables()
        conn.close()
        
        yield temp_file.name
        
        # Limpar
        os.unlink(temp_file.name)

    def test_update_music_path_success(self, temp_db):
        """Testa a atualização bem-sucedida do caminho."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        music_model = MusicModel(conn)
        
        # Adicionar música de teste
        music_id = music_model.add_music("/old/path/song.mp3")
        
        # Atualizar caminho
        result = music_model.update_music_path(music_id, "/new/path/song.mp3")
        
        # Verificar resultado
        assert result is True
        
        # Verificar se foi atualizado no banco
        details = music_model.get_music_details(music_id)
        assert details['path'] == "/new/path/song.mp3"
        
        conn.close()
        
    def test_update_music_path_nonexistent_id(self, temp_db):
        """Testa a atualização com ID inexistente."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        music_model = MusicModel(conn)
        
        # Tentar atualizar música inexistente
        result = music_model.update_music_path(999, "/new/path/song.mp3")
        
        # Verificar que retorna False (rowcount = 0)
        assert result is False
        
        conn.close()
        
    def test_update_music_path_database_error(self, temp_db):
        """Testa o comportamento com erro no banco de dados."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        music_model = MusicModel(conn)
        
        # Fechar conexão para simular erro
        music_model.conn.close()
        
        # Tentar atualizar (irá capturar exceção)
        result = music_model.update_music_path(1, "/new/path/song.mp3")
        
        # Verificar que retorna False
        assert result is False

    def test_update_music_path_invalid_parameters(self, temp_db):
        """Testa comportamento com parâmetros inválidos."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        music_model = MusicModel(conn)
        
        # Testar com ID None
        result = music_model.update_music_path(None, "/new/path/song.mp3")
        assert result is False
        
        # Testar com caminho None
        result = music_model.update_music_path(1, None)
        assert result is False
        
        conn.close()

    def test_update_music_path_multiple_updates(self, temp_db):
        """Testa múltiplas atualizações de caminho."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        music_model = MusicModel(conn)
        
        # Adicionar música de teste
        music_id = music_model.add_music("/original/path/song.mp3")
        
        # Primeira atualização
        result1 = music_model.update_music_path(music_id, "/first/new/path/song.mp3")
        assert result1 is True
        
        # Verificar primeira atualização
        details1 = music_model.get_music_details(music_id)
        assert details1['path'] == "/first/new/path/song.mp3"
        
        # Segunda atualização
        result2 = music_model.update_music_path(music_id, "/second/new/path/song.mp3")
        assert result2 is True
        
        # Verificar segunda atualização
        details2 = music_model.get_music_details(music_id)
        assert details2['path'] == "/second/new/path/song.mp3"
        
        conn.close()


class TestFileMovementIntegration:
    """Testes de integração para movimento de arquivo + atualização no banco."""
    
    @pytest.fixture
    def temp_environment(self):
        """Fixture para ambiente completo de teste."""
        # Criar estrutura temporária
        temp_dir = tempfile.mkdtemp()
        source_folder = os.path.join(temp_dir, "source")
        dest_folder = os.path.join(temp_dir, "destination")
        os.makedirs(source_folder)
        os.makedirs(dest_folder)
        
        # Criar arquivo de música de teste
        music_file = os.path.join(source_folder, "test_song.mp3")
        with open(music_file, 'w') as f:
            f.write("fake music content")
        
        # Criar banco de dados temporário
        db_file = os.path.join(temp_dir, "test.db")
        conn = sqlite3.connect(db_file)
        
        # Inicializar banco
        initializer = DatabaseInitializer(conn)
        initializer.create_tables()
        
        yield {
            'temp_dir': temp_dir,
            'source_folder': source_folder,
            'dest_folder': dest_folder,
            'music_file': music_file,
            'db_file': db_file,
            'conn': conn
        }
        
        # Limpar
        conn.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_complete_file_move_workflow(self, temp_environment):
        """Testa o workflow completo de mover arquivo e atualizar banco."""
        env = temp_environment
        music_model = MusicModel(env['conn'])
        
        # 1. Adicionar música no banco
        music_id = music_model.add_music(env['music_file'])
        assert music_id is not None
        
        # 2. Verificar estado inicial
        initial_details = music_model.get_music_details(music_id)
        assert initial_details['path'] == env['music_file']
        assert os.path.exists(env['music_file'])
        
        # 3. Simular movimento do arquivo
        new_path = os.path.join(env['dest_folder'], "test_song.mp3")
        shutil.move(env['music_file'], new_path)
        
        # 4. Verificar que arquivo foi movido fisicamente
        assert os.path.exists(new_path)
        assert not os.path.exists(env['music_file'])
        
        # 5. Atualizar caminho no banco
        update_result = music_model.update_music_path(music_id, new_path)
        assert update_result is True
        
        # 6. Verificar que banco foi atualizado
        updated_details = music_model.get_music_details(music_id)
        assert updated_details['path'] == new_path
        assert updated_details['id'] == music_id
        
        # 7. Verificar que outros dados permaneceram intactos
        assert updated_details['stars'] == initial_details['stars']

    def test_file_move_with_existing_destination(self, temp_environment):
        """Testa movimento quando arquivo de destino já existe."""
        env = temp_environment
        music_model = MusicModel(env['conn'])
        
        # Criar arquivo de destino que já existe
        dest_file = os.path.join(env['dest_folder'], "test_song.mp3")
        with open(dest_file, 'w') as f:
            f.write("existing content")
            
        # Adicionar música no banco
        music_id = music_model.add_music(env['music_file'])
        
        # Tentar mover (irá substituir o arquivo existente)
        shutil.move(env['music_file'], dest_file)
        
        # Atualizar no banco
        result = music_model.update_music_path(music_id, dest_file)
        assert result is True
        
        # Verificar resultado
        details = music_model.get_music_details(music_id)
        assert details['path'] == dest_file