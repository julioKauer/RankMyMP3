"""
Testes para file_operations.
"""
import pytest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from utils.file_operations import move_file_to_trash, move_file, copy_file, delete_file


class TestFileOperations:
    """Testes para operações de arquivo."""

    def setup_method(self):
        """Setup para cada teste."""
        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test_file.txt')
        
        # Criar arquivo de teste
        with open(self.test_file, 'w') as f:
            f.write('Test content')

    def teardown_method(self):
        """Cleanup após cada teste."""
        # Remover diretório temporário
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('utils.file_operations.send2trash')
    def test_move_file_to_trash_existing_file(self, mock_send2trash):
        """Testa mover arquivo existente para lixeira."""
        move_file_to_trash(self.test_file)
        mock_send2trash.assert_called_once_with(self.test_file)

    @patch('utils.file_operations.send2trash')
    def test_move_file_to_trash_nonexistent_file(self, mock_send2trash):
        """Testa mover arquivo inexistente para lixeira."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        move_file_to_trash(nonexistent_file)
        mock_send2trash.assert_not_called()

    def test_move_file_existing(self):
        """Testa mover arquivo existente."""
        destination = os.path.join(self.temp_dir, 'subdir', 'moved_file.txt')
        
        move_file(self.test_file, destination)
        
        # Verificar se arquivo foi movido
        assert not os.path.exists(self.test_file)
        assert os.path.exists(destination)
        
        # Verificar conteúdo
        with open(destination, 'r') as f:
            assert f.read() == 'Test content'

    def test_move_file_nonexistent(self):
        """Testa mover arquivo inexistente."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        destination = os.path.join(self.temp_dir, 'moved_file.txt')
        
        # Não deve dar erro
        move_file(nonexistent_file, destination)
        
        # Destino não deve existir
        assert not os.path.exists(destination)

    def test_copy_file_existing(self):
        """Testa copiar arquivo existente."""
        destination = os.path.join(self.temp_dir, 'subdir', 'copied_file.txt')
        
        copy_file(self.test_file, destination)
        
        # Verificar se ambos existem
        assert os.path.exists(self.test_file)
        assert os.path.exists(destination)
        
        # Verificar conteúdo
        with open(destination, 'r') as f:
            assert f.read() == 'Test content'

    def test_copy_file_nonexistent(self):
        """Testa copiar arquivo inexistente."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        destination = os.path.join(self.temp_dir, 'copied_file.txt')
        
        # Não deve dar erro
        copy_file(nonexistent_file, destination)
        
        # Destino não deve existir
        assert not os.path.exists(destination)

    def test_delete_file_existing(self):
        """Testa deletar arquivo existente."""
        delete_file(self.test_file)
        
        # Verificar se foi deletado
        assert not os.path.exists(self.test_file)

    def test_delete_file_nonexistent(self):
        """Testa deletar arquivo inexistente."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        
        # Não deve dar erro
        delete_file(nonexistent_file)

    def test_move_file_creates_directory(self):
        """Testa se move_file cria diretórios necessários."""
        nested_destination = os.path.join(self.temp_dir, 'level1', 'level2', 'moved_file.txt')
        
        move_file(self.test_file, nested_destination)
        
        # Verificar se arquivo foi movido e diretórios criados
        assert not os.path.exists(self.test_file)
        assert os.path.exists(nested_destination)
        assert os.path.exists(os.path.dirname(nested_destination))

    def test_copy_file_creates_directory(self):
        """Testa se copy_file cria diretórios necessários."""
        nested_destination = os.path.join(self.temp_dir, 'level1', 'level2', 'copied_file.txt')
        
        copy_file(self.test_file, nested_destination)
        
        # Verificar se arquivo foi copiado e diretórios criados
        assert os.path.exists(self.test_file)
        assert os.path.exists(nested_destination)
        assert os.path.exists(os.path.dirname(nested_destination))
