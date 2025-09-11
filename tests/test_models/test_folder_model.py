"""
Testes para o FolderModel.
"""
import pytest
from models.folder_model import FolderModel


class TestFolderModel:
    """Testes para a classe FolderModel."""

    def test_add_folder(self, folder_model):
        """Testa adicionar uma pasta."""
        folder_model.add_folder('/path/to/folder1')
        folders = folder_model.get_folders()
        assert '/path/to/folder1' in folders

    def test_add_folder_duplicate(self, folder_model):
        """Testa adicionar pasta duplicada."""
        path = '/path/to/folder1'
        folder_model.add_folder(path)
        folder_model.add_folder(path)  # Duplicata deve ser ignorada
        
        folders = folder_model.get_folders()
        assert folders.count(path) == 1

    def test_get_all_folders_empty(self, folder_model):
        """Testa buscar todas as pastas quando vazio."""
        folders = folder_model.get_all_folders()
        assert folders == []

    def test_get_all_folders_with_data(self, folder_model):
        """Testa buscar todas as pastas com dados."""
        # Adicionar pastas
        paths = ['/path/to/folder1', '/path/to/folder2', '/path/to/folder3']
        for path in paths:
            folder_model.add_folder(path)
        
        # Buscar pastas
        folders = folder_model.get_all_folders()
        assert len(folders) == 3
        for path in paths:
            assert path in folders

    def test_get_folder_count_empty(self, folder_model):
        """Testa contagem de pastas quando vazio."""
        count = folder_model.get_folder_count()
        assert count == 0

    def test_get_folder_count_with_data(self, folder_model):
        """Testa contagem de pastas com dados."""
        # Adicionar pastas
        paths = ['/path/to/folder1', '/path/to/folder2', '/path/to/folder3']
        for path in paths:
            folder_model.add_folder(path)
        
        # Verificar contagem
        count = folder_model.get_folder_count()
        assert count == 3

    def test_clear_all_folders_empty(self, folder_model):
        """Testa limpar pastas quando vazio."""
        # Não deve dar erro
        folder_model.clear_all_folders()
        assert folder_model.get_folder_count() == 0

    def test_clear_all_folders_with_data(self, folder_model):
        """Testa limpar pastas com dados."""
        # Adicionar pastas
        paths = ['/path/to/folder1', '/path/to/folder2', '/path/to/folder3']
        for path in paths:
            folder_model.add_folder(path)
        
        # Verificar que foram adicionadas
        assert folder_model.get_folder_count() == 3
        
        # Limpar
        folder_model.clear_all_folders()
        
        # Verificar que foram removidas
        assert folder_model.get_folder_count() == 0
        assert folder_model.get_all_folders() == []

    def test_folder_model_initialization(self, folder_model):
        """Testa inicialização do modelo."""
        assert folder_model is not None
        assert hasattr(folder_model, 'db_path')

    def test_add_multiple_folders_different_paths(self, folder_model):
        """Testa adicionar múltiplas pastas com caminhos diferentes."""
        paths = [
            '/home/user/Music/Rock',
            '/home/user/Music/Pop',
            '/home/user/Music/Jazz',
            '/media/external/Music'
        ]
        
        for path in paths:
            folder_model.add_folder(path)
        
        folders = folder_model.get_all_folders()
        assert len(folders) == len(paths)
        for path in paths:
            assert path in folders

    def test_folder_operations_sequence(self, folder_model):
        """Testa sequência de operações com pastas."""
        # Começar vazio
        assert folder_model.get_folder_count() == 0
        
        # Adicionar algumas pastas
        paths = ['/path1', '/path2', '/path3']
        for path in paths:
            folder_model.add_folder(path)
        
        # Verificar contagem
        assert folder_model.get_folder_count() == 3
        
        # Verificar existência
        for path in paths:
            assert folder_model.folder_exists(path)
        
        # Remover uma pasta
        folder_model.remove_folder('/path2')
        assert folder_model.get_folder_count() == 2
        assert not folder_model.folder_exists('/path2')
        
        # Limpar todas
        folder_model.clear_all_folders()
        assert folder_model.get_folder_count() == 0

    def test_folder_exists(self, folder_model):
        """Testa verificação de existência de pasta."""
        path = '/test/folder'
        
        # Inicialmente não existe
        assert not folder_model.folder_exists(path)
        
        # Adicionar e verificar que existe
        folder_model.add_folder(path)
        assert folder_model.folder_exists(path)
        
        # Remover e verificar que não existe mais
        folder_model.remove_folder(path)
        assert not folder_model.folder_exists(path)

    def test_remove_folder(self, folder_model):
        """Testa remover uma pasta."""
        # Adicionar pastas
        paths = ['/path/to/folder1', '/path/to/folder2']
        for path in paths:
            folder_model.add_folder(path)
        
        # Verificar que foram adicionadas
        assert folder_model.get_folder_count() == 2
        
        # Remover uma pasta
        folder_model.remove_folder('/path/to/folder1')
        
        # Verificar
        folders = folder_model.get_folders()
        assert len(folders) == 1
        assert '/path/to/folder2' in folders
        assert '/path/to/folder1' not in folders
