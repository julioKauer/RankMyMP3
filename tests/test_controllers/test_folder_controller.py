"""
Testes para FolderController.
"""
import pytest
from controllers.folder_controller import FolderController


class TestFolderController:
    """Testes para a classe FolderController."""

    def test_folder_controller_initialization(self, folder_controller):
        """Testa inicialização do controller."""
        assert folder_controller is not None
        assert hasattr(folder_controller, 'model')

    def test_add_folder(self, folder_controller):
        """Testa adicionar uma pasta."""
        folder_controller.add_folder('/path/to/folder1')
        folders = folder_controller.get_folders()
        assert '/path/to/folder1' in folders

    def test_get_folders_empty(self, folder_controller):
        """Testa buscar todas as pastas quando vazio."""
        folders = folder_controller.get_folders()
        assert folders == []

    def test_get_folders_with_data(self, folder_controller):
        """Testa buscar todas as pastas com dados."""
        # Adicionar pastas
        paths = ['/path/to/folder1', '/path/to/folder2', '/path/to/folder3']
        for path in paths:
            folder_controller.add_folder(path)
        
        # Buscar pastas
        folders = folder_controller.get_folders()
        assert len(folders) == 3
        for path in paths:
            assert path in folders

    def test_remove_folder(self, folder_controller):
        """Testa remover uma pasta."""
        # Adicionar pastas
        paths = ['/path/to/folder1', '/path/to/folder2']
        for path in paths:
            folder_controller.add_folder(path)
        
        # Remover uma pasta
        folder_controller.remove_folder('/path/to/folder1')
        
        # Verificar
        folders = folder_controller.get_folders()
        assert len(folders) == 1
        assert '/path/to/folder2' in folders
        assert '/path/to/folder1' not in folders
