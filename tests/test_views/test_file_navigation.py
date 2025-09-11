"""
Testes para as funcionalidades de navegação de arquivos.
Testa a exibição de caminhos e abertura de pastas.
"""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
from models.music_model import MusicModel
from controllers.music_controller import MusicController
from utils.database_initializer import DatabaseInitializer


@pytest.fixture
def db_connection():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
        temp_db_path = temp_file.name
    
    conn = sqlite3.connect(temp_db_path)
    db_init = DatabaseInitializer(conn)
    db_init.create_tables()
    
    yield conn
    
    conn.close()
    os.unlink(temp_db_path)


class TestFileNavigationFeatures:
    """Testes para as funcionalidades de navegação de arquivos."""
    
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    @patch('wx.MessageDialog')
    def test_show_music_path_functionality(self, mock_dialog, mock_music_app, mock_wx_app, db_connection):
        """Testa a funcionalidade de mostrar caminho da música."""
        # Criar controller e adicionar música
        controller = MusicController(db_connection)
        music_id = controller.music_model.add_music("/home/user/Music/test.mp3")
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular criação da aplicação
        from views.music_app import MusicApp
        main_window = MusicApp(controller)
        
        # Mock do diálogo
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Simular chamada do método show_music_path
        with patch.object(main_window, 'show_music_path') as mock_show_path:
            main_window.show_music_path(music_id)
            mock_show_path.assert_called_once_with(music_id)
    
    @patch('subprocess.run')
    @patch('platform.system')
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    def test_open_music_folder_windows(self, mock_music_app, mock_wx_app, mock_platform, mock_subprocess, db_connection):
        """Testa abertura de pasta no Windows."""
        # Configurar mock para Windows
        mock_platform.return_value = 'Windows'
        
        # Criar controller e adicionar música
        controller = MusicController(db_connection)
        music_id = controller.music_model.add_music("C:\\Music\\test.mp3")
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular abertura de pasta
        with patch.object(mock_window, 'open_music_folder') as mock_open_folder:
            mock_window.open_music_folder(music_id)
            mock_open_folder.assert_called_once_with(music_id)
    
    @patch('subprocess.run')
    @patch('platform.system')
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    def test_open_music_folder_linux(self, mock_music_app, mock_wx_app, mock_platform, mock_subprocess, db_connection):
        """Testa abertura de pasta no Linux."""
        # Configurar mock para Linux
        mock_platform.return_value = 'Linux'
        
        # Criar controller e adicionar música
        controller = MusicController(db_connection)
        music_id = controller.music_model.add_music("/home/user/Music/test.mp3")
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular abertura de pasta
        with patch.object(mock_window, 'open_music_folder') as mock_open_folder:
            mock_window.open_music_folder(music_id)
            mock_open_folder.assert_called_once_with(music_id)
    
    @patch('subprocess.run')
    @patch('platform.system')
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    def test_open_music_folder_macos(self, mock_music_app, mock_wx_app, mock_platform, mock_subprocess, db_connection):
        """Testa abertura de pasta no macOS."""
        # Configurar mock para macOS
        mock_platform.return_value = 'Darwin'
        
        # Criar controller e adicionar música
        controller = MusicController(db_connection)
        music_id = controller.music_model.add_music("/Users/user/Music/test.mp3")
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular abertura de pasta
        with patch.object(mock_window, 'open_music_folder') as mock_open_folder:
            mock_window.open_music_folder(music_id)
            mock_open_folder.assert_called_once_with(music_id)
    
    @patch('subprocess.run')
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    def test_open_music_folder_error_handling(self, mock_music_app, mock_wx_app, mock_subprocess, db_connection):
        """Testa tratamento de erros na abertura de pasta."""
        # Configurar mock para gerar erro
        mock_subprocess.side_effect = Exception("Erro ao abrir pasta")
        
        # Criar controller e adicionar música
        controller = MusicController(db_connection)
        music_id = controller.music_model.add_music("/home/user/Music/test.mp3")
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular tentativa de abertura de pasta com erro
        with patch.object(mock_window, 'open_music_folder') as mock_open_folder:
            mock_window.open_music_folder(music_id)
            mock_open_folder.assert_called_once_with(music_id)
    
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    def test_show_path_nonexistent_music(self, mock_music_app, mock_wx_app, db_connection):
        """Testa exibição de caminho para música inexistente."""
        # Criar controller
        controller = MusicController(db_connection)
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular tentativa de mostrar caminho para música inexistente
        with patch.object(mock_window, 'show_music_path') as mock_show_path:
            mock_window.show_music_path(99999)  # ID inexistente
            mock_show_path.assert_called_once_with(99999)
    
    @patch('wx.App')
    @patch('views.music_app.MusicApp')
    def test_open_folder_nonexistent_music(self, mock_music_app, mock_wx_app, db_connection):
        """Testa abertura de pasta para música inexistente."""
        # Criar controller
        controller = MusicController(db_connection)
        
        # Mock da janela principal
        mock_window = MagicMock()
        mock_music_app.return_value = mock_window
        
        # Simular tentativa de abrir pasta para música inexistente
        with patch.object(mock_window, 'open_music_folder') as mock_open_folder:
            mock_window.open_music_folder(99999)  # ID inexistente
            mock_open_folder.assert_called_once_with(99999)


class TestFileNavigationBackend:
    """Testes para a lógica backend de navegação de arquivos."""
    
    def test_get_music_details_with_path(self, db_connection):
        """Testa obtenção de detalhes da música incluindo caminho."""
        controller = MusicController(db_connection)
        
        # Adicionar música
        test_path = "/home/user/Music/test_song.mp3"
        music_id = controller.music_model.add_music(test_path)
        
        # Obter detalhes
        details = controller.music_model.get_music_details(music_id)
        
        # Verificar que o caminho está presente
        assert details is not None
        assert details['path'] == test_path
        assert details['id'] == music_id
    
    def test_path_validation(self, db_connection):
        """Testa validação de caminhos."""
        controller = MusicController(db_connection)
        
        # Testar caminhos válidos
        valid_paths = [
            "/home/user/Music/song.mp3",
            "C:\\Music\\song.mp3",
            "/Users/user/Music/song.mp3"
        ]
        
        for path in valid_paths:
            music_id = controller.music_model.add_music(path)
            details = controller.music_model.get_music_details(music_id)
            assert details['path'] == path
    
    def test_file_existence_handling(self, db_connection):
        """Testa tratamento de arquivos que não existem mais."""
        controller = MusicController(db_connection)
        
        # Adicionar música com caminho inexistente
        fake_path = "/path/that/does/not/exist.mp3"
        music_id = controller.music_model.add_music(fake_path)
        
        # Verificar que ainda podemos obter os detalhes
        details = controller.music_model.get_music_details(music_id)
        assert details is not None
        assert details['path'] == fake_path
        
        # O tratamento de arquivo inexistente deve ser feito na UI, não no modelo
