"""
Testes para database_initializer.
"""
import pytest
import tempfile
import os
import sqlite3
from utils.database_initializer import DatabaseInitializer


class TestDatabaseInitializer:
    """Testes para inicialização do banco de dados."""

    def test_create_tables(self):
        """Testa se as tabelas são criadas corretamente."""
        # Usar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        temp_path = temp_file.name
        
        try:
            # Conectar ao banco
            conn = sqlite3.connect(temp_path)
            
            # Inicializar com DatabaseInitializer
            db_init = DatabaseInitializer(conn)
            db_init.create_tables()
            
            # Verificar se as tabelas foram criadas
            cursor = conn.cursor()
            
            # Verificar tabela music
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='music'")
            assert cursor.fetchone() is not None
            
            # Verificar tabela tags
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
            assert cursor.fetchone() is not None
            
            # Verificar tabela music_tags
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='music_tags'")
            assert cursor.fetchone() is not None
            
            # Verificar tabela comparisons
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comparisons'")
            assert cursor.fetchone() is not None
            
            # Verificar tabela comparison_state
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comparison_state'")
            assert cursor.fetchone() is not None
            
            # Verificar tabela folders
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
            assert cursor.fetchone() is not None
            
            conn.close()
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_database_initializer_with_existing_tables(self):
        """Testa inicialização com tabelas já existentes."""
        # Usar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        temp_path = temp_file.name
        
        try:
            # Conectar ao banco
            conn = sqlite3.connect(temp_path)
            
            # Primeira inicialização
            db_init = DatabaseInitializer(conn)
            db_init.create_tables()
            
            # Segunda inicialização não deve dar erro
            db_init2 = DatabaseInitializer(conn)
            db_init2.create_tables()
            
            # Verificar se tabelas ainda existem
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            # Deve ter pelo menos as 6 tabelas principais
            assert len(tables) >= 6
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
