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
    
    def test_show_music_path_functionality(self, db_connection):
        """Testa a funcionalidade de mostrar caminho da música."""
        from views.music_app import MusicApp
        
        # Criar a aplicação (sem mostrar GUI)
        import wx
        app = wx.App(False)
        
        try:
            # Criar controller e adicionar música
            controller = MusicController(db_connection)
            music_id = controller.music_model.add_music("/home/user/Music/test.mp3")
            
            # Criar a janela principal
            main_window = MusicApp(controller)
            
            # Mock do MessageDialog
            with patch('wx.MessageDialog') as mock_dialog:
                mock_dialog_instance = MagicMock()
                mock_dialog.return_value = mock_dialog_instance
                
                # Chamar a função
                main_window.on_show_music_path("/home/user/Music/test.mp3")
                
                # Verificar se o dialog foi criado corretamente
                mock_dialog.assert_called_once()
                call_args = mock_dialog.call_args[0]
                
                # Verificar se o caminho está na mensagem
                assert "/home/user/Music/test.mp3" in call_args[1]
                assert "📁 Caminho completo da música" in call_args[1]
                
                # Verificar se ShowModal foi chamado
                mock_dialog_instance.ShowModal.assert_called_once()
                mock_dialog_instance.Destroy.assert_called_once()
                
        finally:
            app.Destroy()
    
    def test_open_folder_linux_success(self, db_connection):
        """Testa abertura de pasta no Linux com sucesso."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Mock do sistema e subprocess
            with patch('platform.system', return_value='Linux'), \
                 patch('os.path.exists', return_value=True), \
                 patch('subprocess.run') as mock_run:
                
                # Configurar subprocess para sucesso
                mock_run.return_value = None
                
                # Chamar a função
                main_window.on_open_music_folder("/home/user/Music/test.mp3")
                
                # Verificar se foi chamado com xdg-open
                mock_run.assert_called_once_with(['xdg-open', '/home/user/Music'], check=True)
                
        finally:
            app.Destroy()
    
    def test_open_folder_windows_success(self, db_connection):
        """Testa abertura de pasta no Windows com sucesso."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Mock do sistema, os.path.dirname e subprocess
            with patch('platform.system', return_value='Windows'), \
                 patch('os.path.exists', return_value=True), \
                 patch('os.path.dirname', return_value='C:\\Users\\User\\Music'), \
                 patch('subprocess.run') as mock_run:
                
                # Configurar subprocess para sucesso
                mock_run.return_value = None
                
                # Chamar a função
                main_window.on_open_music_folder("C:\\Users\\User\\Music\\test.mp3")
                
                # Verificar se foi chamado com explorer
                mock_run.assert_called_once_with(['explorer', 'C:\\Users\\User\\Music'], check=True)
                
        finally:
            app.Destroy()
    
    def test_open_folder_macos_success(self, db_connection):
        """Testa abertura de pasta no macOS com sucesso."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Mock do sistema e subprocess
            with patch('platform.system', return_value='Darwin'), \
                 patch('os.path.exists', return_value=True), \
                 patch('subprocess.run') as mock_run:
                
                # Configurar subprocess para sucesso
                mock_run.return_value = None
                
                # Chamar a função
                main_window.on_open_music_folder("/Users/user/Music/test.mp3")
                
                # Verificar se foi chamado com open
                mock_run.assert_called_once_with(['open', '/Users/user/Music'], check=True)
                
        finally:
            app.Destroy()
    
    def test_open_folder_nonexistent_path(self, db_connection):
        """Testa abertura de pasta com caminho inexistente."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Mock do sistema e wx.MessageBox
            with patch('platform.system', return_value='Linux'), \
                 patch('os.path.exists', return_value=False), \
                 patch('wx.MessageBox') as mock_messagebox:
                
                # Chamar a função
                main_window.on_open_music_folder("/nonexistent/path/test.mp3")
                
                # Verificar se o MessageBox de erro foi mostrado
                mock_messagebox.assert_called_once()
                call_args = mock_messagebox.call_args[0]
                assert "não foi encontrada" in call_args[0]
                assert "/nonexistent/path" in call_args[0]
                
        finally:
            app.Destroy()
    
    def test_open_folder_command_failure(self, db_connection):
        """Testa falha no comando de abertura da pasta."""
        from views.music_app import MusicApp
        import subprocess  # Importar aqui para usar na exceção
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Mock do sistema e subprocess que falha
            with patch('platform.system', return_value='Linux'), \
                 patch('os.path.exists', return_value=True), \
                 patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'xdg-open')), \
                 patch('wx.MessageBox') as mock_messagebox:
                
                # Chamar a função
                main_window.on_open_music_folder("/home/user/Music/test.mp3")
                
                # Verificar se o MessageBox de erro foi mostrado
                mock_messagebox.assert_called_once()
                call_args = mock_messagebox.call_args[0]
                assert "Não foi possível abrir a pasta" in call_args[0]
                assert "/home/user/Music" in call_args[0]
                
        finally:
            app.Destroy()
    
    def test_open_folder_linux_fallback_success(self, db_connection):
        """Testa fallback para outros gerenciadores de arquivo no Linux."""
        from views.music_app import MusicApp
        import subprocess  # Importar aqui para usar na exceção
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Mock do sistema e subprocess
            with patch('platform.system', return_value='Linux'), \
                 patch('os.path.exists', return_value=True), \
                 patch('subprocess.run') as mock_run:
                
                # Configurar para falhar no xdg-open mas ter sucesso no nautilus
                def side_effect(cmd, **kwargs):
                    if cmd[0] == 'xdg-open':
                        raise subprocess.CalledProcessError(1, 'xdg-open')
                    elif cmd[0] == 'nautilus':
                        return None
                    else:
                        raise FileNotFoundError()
                
                mock_run.side_effect = side_effect
                
                # Chamar a função
                main_window.on_open_music_folder("/home/user/Music/test.mp3")
                
                # Verificar se tentou xdg-open primeiro e depois nautilus
                assert mock_run.call_count >= 2
                
        finally:
            app.Destroy()
    
    def test_integration_context_menu_path_functions(self, db_connection):
        """Testa integração das funções de caminho no menu contextual."""
        controller = MusicController(db_connection)
        
        # Adicionar música de teste
        music_id = controller.music_model.add_music("/home/user/Music/rock/song.mp3")
        controller.music_model.update_stars(music_id, 4)
        
        # Verificar se a música está no ranking
        ranked_musics = controller.get_classified_musics_topological()
        assert len(ranked_musics) > 0
        
        # Verificar se podemos obter os detalhes da música
        music_details = controller.music_model.get_music_details(music_id)
        assert music_details is not None
        assert music_details['path'] == "/home/user/Music/rock/song.mp3"
        
        # Testar que o diretório é extraído corretamente
        folder_path = os.path.dirname(music_details['path'])
        assert folder_path == "/home/user/Music/rock"
    
    def test_path_extraction_edge_cases(self, db_connection):
        """Testa casos extremos de extração de caminho."""
        controller = MusicController(db_connection)
        
        # Casos de teste
        test_cases = [
            "/home/user/file.mp3",          # Arquivo na raiz de user
            "/file.mp3",                    # Arquivo na raiz do sistema  
            "C:\\Users\\User\\song.mp3",    # Windows
            "/home/user/folder with spaces/song.mp3",  # Espaços
            "/home/user/música_çãos/song.mp3",         # Unicode
        ]
        
        for path in test_cases:
            music_id = controller.music_model.add_music(path)
            music_details = controller.music_model.get_music_details(music_id)
            
            assert music_details['path'] == path
            
            # Verificar extração do diretório
            expected_dir = os.path.dirname(path)
            actual_dir = os.path.dirname(music_details['path'])
            assert actual_dir == expected_dir
