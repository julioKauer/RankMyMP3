"""
Configuração do pytest e fixtures globais.
"""
import pytest
import tempfile
import os
import sqlite3
import sys
from pathlib import Path

# Adicionar o diretório raiz ao Python path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.music_model import MusicModel
from models.comparison_model import ComparisonModel
from models.comparison_state_model import ComparisonStateModel
from models.folder_model import FolderModel
from controllers.music_controller import MusicController
from controllers.folder_controller import FolderController


@pytest.fixture 
def temp_db_path():
    """
    Cria um banco de dados temporário e retorna o caminho.
    """
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    # Conectar e criar tabelas
    conn = sqlite3.connect(temp_file.name)
    
    # Criar tabela music
    conn.execute('''
        CREATE TABLE music (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            stars INTEGER DEFAULT 0
        )
    ''')
    
    # Criar tabela comparisons
    conn.execute('''
        CREATE TABLE comparisons (
            music_a_id INTEGER,
            music_b_id INTEGER,
            winner_id INTEGER,
            PRIMARY KEY (music_a_id, music_b_id),
            FOREIGN KEY (music_a_id) REFERENCES music (id),
            FOREIGN KEY (music_b_id) REFERENCES music (id),
            FOREIGN KEY (winner_id) REFERENCES music (id)
        )
    ''')
    
    # Criar tabela comparison_state
    conn.execute('''
        CREATE TABLE comparison_state (
            id INTEGER PRIMARY KEY,
            unrated_music_id INTEGER,
            compared_music_id INTEGER,
            context TEXT,
            FOREIGN KEY (unrated_music_id) REFERENCES music (id),
            FOREIGN KEY (compared_music_id) REFERENCES music (id)
        )
    ''')
    
    # Criar tabela folders
    conn.execute('''
        CREATE TABLE folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield temp_file.name
    
    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def temp_db(temp_db_path):
    """
    Retorna uma conexão para o banco temporário.
    """
    conn = sqlite3.connect(temp_db_path)
    yield conn
    conn.close()


@pytest.fixture
def music_model(temp_db):
    """
    Fixture para MusicModel com banco temporário.
    """
    return MusicModel(temp_db)


@pytest.fixture
def comparison_model(temp_db):
    """
    Fixture para ComparisonModel com banco temporário.
    """
    return ComparisonModel(temp_db)


@pytest.fixture
def comparison_state_model(temp_db):
    """
    Fixture para ComparisonStateModel com banco temporário.
    """
    return ComparisonStateModel(temp_db)


@pytest.fixture
def folder_model(temp_db_path):
    """
    Fixture para FolderModel com banco temporário.
    """
    return FolderModel(temp_db_path)


@pytest.fixture
def music_controller(temp_db_path):
    """
    Fixture para MusicController com banco temporário.
    """
    return MusicController(temp_db_path)


@pytest.fixture
def folder_controller(folder_model):
    """
    Fixture para FolderController com FolderModel.
    """
    return FolderController(folder_model)


@pytest.fixture
def sample_music_data():
    """
    Dados de músicas para testes.
    """
    return [
        '/path/to/music1.mp3',
        '/path/to/music2.mp3',
        '/path/to/music3.mp3',
        '/path/to/music4.mp3',
        '/path/to/music5.mp3'
    ]


@pytest.fixture
def sample_folder_data():
    """
    Dados de pastas para testes.
    """
    return [
        '/path/to/folder1',
        '/path/to/folder2',
        '/path/to/folder3'
    ]
