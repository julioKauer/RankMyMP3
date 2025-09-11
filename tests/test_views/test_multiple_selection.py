"""
Testes para as funcionalidades de múltipla seleção na lista de ranking.
Testa menus contextuais adaptados e operações em lote.
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


class TestMultipleSelectionFeatures:
    """Testes para as funcionalidades de múltipla seleção."""
    
    def test_ranking_list_allows_multiple_selection(self, db_connection):
        """Testa que a lista de ranking permite múltipla seleção."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Verificar que a lista não tem wx.LC_SINGLE_SEL
            style = main_window.ranking_list.GetWindowStyle()
            has_single_sel = bool(style & wx.LC_SINGLE_SEL)
            
            assert not has_single_sel, "Lista de ranking deveria permitir múltipla seleção"
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    def test_get_selected_music_ids_from_ranking_multiple(self, db_connection):
        """Testa obtenção de IDs de múltiplas músicas selecionadas."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com várias músicas classificadas
            controller = MusicController(db_connection)
            
            # Adicionar e classificar algumas músicas
            music_ids = []
            for i in range(5):
                music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
                controller.music_model.update_stars(music_id, 5 - i)  # Diferentes rankings
                music_ids.append(music_id)
            
            main_window = MusicApp(controller)
            main_window.update_ranking_list()
            
            # Simular seleção múltipla (índices 0, 2, 4)
            main_window.ranking_list.Select(0)
            main_window.ranking_list.Select(2)
            main_window.ranking_list.Select(4)
            
            # Testar método de obtenção de IDs
            selected_ids = main_window._get_selected_music_ids_from_ranking()
            
            # Verificar que retornou 3 IDs
            assert len(selected_ids) == 3
            
            # Verificar que são IDs válidos
            for music_id in selected_ids:
                assert music_id in music_ids
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    def test_get_selected_music_ids_from_ranking_single(self, db_connection):
        """Testa obtenção de ID de uma única música selecionada."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com uma música classificada
            controller = MusicController(db_connection)
            music_id = controller.music_model.add_music("/test/song.mp3")
            controller.music_model.update_stars(music_id, 5)
            
            main_window = MusicApp(controller)
            main_window.update_ranking_list()
            
            # Simular seleção única
            main_window.ranking_list.Select(0)
            
            # Testar método de obtenção de IDs
            selected_ids = main_window._get_selected_music_ids_from_ranking()
            
            # Verificar que retornou 1 ID
            assert len(selected_ids) == 1
            assert selected_ids[0] == music_id
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    def test_get_selected_music_ids_from_ranking_empty(self, db_connection):
        """Testa obtenção de IDs quando nenhuma música está selecionada."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            controller = MusicController(db_connection)
            main_window = MusicApp(controller)
            
            # Testar sem seleção
            selected_ids = main_window._get_selected_music_ids_from_ranking()
            
            # Verificar que retornou lista vazia
            assert len(selected_ids) == 0
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    @patch('wx.MessageDialog')
    def test_remove_multiple_from_ranking_confirmed(self, mock_dialog, db_connection):
        """Testa remoção múltipla com confirmação do usuário."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com várias músicas classificadas
            controller = MusicController(db_connection)
            
            music_ids = []
            for i in range(3):
                music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
                controller.music_model.update_stars(music_id, 5)
                music_ids.append(music_id)
            
            main_window = MusicApp(controller)
            
            # Mock da confirmação do usuário (YES)
            mock_dialog_instance = MagicMock()
            mock_dialog_instance.ShowModal.return_value = wx.ID_YES
            mock_dialog.return_value = mock_dialog_instance
            
            # Mock do método para retornar os IDs das primeiras 2 músicas
            with patch.object(main_window, '_get_selected_music_ids_from_ranking', return_value=music_ids[:2]):
                with patch.object(wx, 'MessageBox') as mock_msgbox:
                    # Executar remoção múltipla
                    main_window.on_remove_multiple_from_ranking()
                    
                    # Verificar que o diálogo de confirmação foi mostrado
                    mock_dialog.assert_called_once()
                    
                    # Verificar que as músicas foram removidas do ranking (stars = 0)
                    for music_id in music_ids[:2]:
                        details = controller.music_model.get_music_details(music_id)
                        assert details['stars'] == 0
                    
                    # Verificar que a última música não foi afetada
                    details = controller.music_model.get_music_details(music_ids[2])
                    assert details['stars'] == 5
                    
                    # Verificar mensagem de sucesso
                    mock_msgbox.assert_called_once()
                    success_msg = mock_msgbox.call_args[0][0]
                    assert "2 música(s) removida(s)" in success_msg
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    @patch('wx.MessageDialog')
    def test_remove_multiple_from_ranking_cancelled(self, mock_dialog, db_connection):
        """Testa remoção múltipla cancelada pelo usuário."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com músicas classificadas
            controller = MusicController(db_connection)
            
            music_ids = []
            for i in range(2):
                music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
                controller.music_model.update_stars(music_id, 5)
                music_ids.append(music_id)
            
            main_window = MusicApp(controller)
            
            # Mock da confirmação do usuário (NO)
            mock_dialog_instance = MagicMock()
            mock_dialog_instance.ShowModal.return_value = wx.ID_NO
            mock_dialog.return_value = mock_dialog_instance
            
            # Mock do método para retornar todos os IDs
            with patch.object(main_window, '_get_selected_music_ids_from_ranking', return_value=music_ids):
                # Executar remoção múltipla
                main_window.on_remove_multiple_from_ranking()
                
                # Verificar que o diálogo de confirmação foi mostrado
                mock_dialog.assert_called_once()
                
                # Verificar que as músicas NÃO foram removidas (stars ainda = 5)
                for music_id in music_ids:
                    details = controller.music_model.get_music_details(music_id)
                    assert details['stars'] == 5
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    @patch('wx.MessageDialog')
    def test_ignore_multiple_from_ranking_confirmed(self, mock_dialog, db_connection):
        """Testa ignorar múltiplas músicas com confirmação."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com várias músicas classificadas
            controller = MusicController(db_connection)
            
            music_ids = []
            for i in range(3):
                music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
                controller.music_model.update_stars(music_id, 4)
                music_ids.append(music_id)
            
            main_window = MusicApp(controller)
            
            # Mock da confirmação do usuário (YES)
            mock_dialog_instance = MagicMock()
            mock_dialog_instance.ShowModal.return_value = wx.ID_YES
            mock_dialog.return_value = mock_dialog_instance
            
            # Mock do método para retornar os IDs das primeiras 2 músicas
            with patch.object(main_window, '_get_selected_music_ids_from_ranking', return_value=music_ids[:2]):
                with patch.object(wx, 'MessageBox') as mock_msgbox:
                    # Executar ignorar múltiplo
                    main_window.on_ignore_multiple_from_ranking()
                    
                    # Verificar que o diálogo de confirmação foi mostrado
                    mock_dialog.assert_called_once()
                    
                    # Verificar que as músicas foram ignoradas (stars = -1)
                    for music_id in music_ids[:2]:
                        details = controller.music_model.get_music_details(music_id)
                        assert details['stars'] == -1
                    
                    # Verificar que a última música não foi afetada
                    details = controller.music_model.get_music_details(music_ids[2])
                    assert details['stars'] == 4
                    
                    # Verificar mensagem de sucesso
                    mock_msgbox.assert_called_once()
                    success_msg = mock_msgbox.call_args[0][0]
                    assert "2 música(s) ignorada(s)" in success_msg
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    def test_context_menu_multiple_selection_detection(self, db_connection):
        """Testa detecção de múltipla seleção no menu contextual."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com músicas classificadas
            controller = MusicController(db_connection)
            
            for i in range(3):
                music_id = controller.music_model.add_music(f"/test/song{i}.mp3")
                controller.music_model.update_stars(music_id, 5)
            
            main_window = MusicApp(controller)
            main_window.update_ranking_list()
            
            # Verificar que GetSelectedItemCount retorna contagem correta
            main_window.ranking_list.Select(0)
            assert main_window.ranking_list.GetSelectedItemCount() == 1
            
            main_window.ranking_list.Select(1)
            assert main_window.ranking_list.GetSelectedItemCount() == 2
            
            main_window.ranking_list.Select(2)
            assert main_window.ranking_list.GetSelectedItemCount() == 3
                        
        finally:
            main_window.Destroy()
            app.Destroy()

    def test_create_and_play_playlist_simple_method(self, db_connection):
        """Testa o método simplificado de criar e reproduzir playlist."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com múltiplas músicas classificadas
            controller = MusicController(db_connection)
            
            music_paths = ["/test/song1.mp3", "/test/song2.mp3"]
            for path in music_paths:
                music_id = controller.music_model.add_music(path)
                controller.music_model.update_stars(music_id, 5)
            
            main_window = MusicApp(controller)
            main_window.update_ranking_list()
            
            # Simular seleção múltipla
            main_window.ranking_list.Select(0)
            main_window.ranking_list.Select(1)
            
            # Mock do método _create_and_play_playlist
            with patch.object(main_window, '_create_and_play_playlist') as mock_create_play:
                # Executar criação de playlist
                main_window.on_create_and_play_playlist_simple()
                
                # Verificar que método foi chamado com caminhos corretos
                mock_create_play.assert_called_once()
                called_paths = mock_create_play.call_args[0][0]
                assert len(called_paths) == 2
                assert all(path in music_paths for path in called_paths)
        

    @patch('shutil.copy2')
    @patch('wx.MessageBox')
    @patch('wx.DirDialog')
    def test_copy_multiple_music_files(self, mock_dir_dialog, mock_msgbox, mock_copy, db_connection):
        """Testa cópia de múltiplas músicas selecionadas."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com múltiplas músicas classificadas
            controller = MusicController(db_connection)
            
            music_paths = ["/test/song1.mp3", "/test/song2.mp3"]
            for path in music_paths:
                music_id = controller.music_model.add_music(path)
                controller.music_model.update_stars(music_id, 5)
            
            main_window = MusicApp(controller)
            main_window.update_ranking_list()
            
            # Simular seleção de múltiplas músicas
            main_window.ranking_list.Select(0)
            main_window.ranking_list.Select(1)
            
            # Mock dialog de seleção de pasta
            mock_dir_dialog_instance = MagicMock()
            mock_dir_dialog_instance.ShowModal.return_value = wx.ID_OK
            mock_dir_dialog_instance.GetPath.return_value = "/dest/folder"
            mock_dir_dialog.return_value = mock_dir_dialog_instance
            
            # Mock dialog de confirmação
            mock_msgbox.side_effect = [wx.ID_YES, None]  # Confirmação + resultado
            
            # Mock verificação se arquivos existem
            with patch('os.path.exists', return_value=True):
                # Executar cópia
                main_window.on_copy_multiple_music_files()
                
                # Verificar que shutil.copy2 foi chamado para cada música
                assert mock_copy.call_count == 2
                
                # Verificar chamadas de cópia
                expected_calls = [
                    (("/test/song1.mp3", "/dest/folder/song1.mp3"),),
                    (("/test/song2.mp3", "/dest/folder/song2.mp3"),)
                ]
                for call in expected_calls:
                    assert call in [c.args for c in mock_copy.call_args_list]
                
                # Verificar mensagem de sucesso
                success_call = [call for call in mock_msgbox.call_args_list if call[0][0] and "copiada(s)" in call[0][0]]
                assert len(success_call) == 1
                assert "2 música(s) copiada(s)" in success_call[0][0][0]
        
        finally:
            main_window.Destroy()
            app.Destroy()

    @patch('tempfile.gettempdir')
    @patch('subprocess.run')
    @patch('wx.MessageBox')
    @patch('wx.MessageDialog')
    def test_create_and_play_playlist(self, mock_msg_dialog, mock_msgbox, mock_subprocess, mock_tempdir, db_connection):
        """Testa criação e reprodução de playlist temporária."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup
            mock_tempdir.return_value = "/tmp"
            main_window = MusicApp(MusicController(db_connection))
            
            music_paths = ["/test/song1.mp3", "/test/song2.mp3"]
            
            # Mock verificação de arquivos
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    with patch('platform.system', return_value='Linux'):
                        # Executar criação de playlist
                        main_window._create_and_play_playlist(music_paths)
                        
                        # Verificar que arquivo foi aberto para escrita
                        mock_open.assert_called_once()
                        
                        # Verificar que subprocess foi chamado com xdg-open
                        mock_subprocess.assert_called_once()
                        call_args = mock_subprocess.call_args[0][0]
                        assert call_args[0] == 'xdg-open'
                        assert '.m3u' in call_args[1]
                        
                        # Verificar mensagem de sucesso
                        mock_msgbox.assert_called_once()
                        success_msg = mock_msgbox.call_args[0][0]
                        assert "Playlist criada com 2 música(s)" in success_msg
        
        finally:
            main_window.Destroy()
            app.Destroy()

    @patch('wx.FileDialog')
    def test_export_playlist_m3u(self, mock_file_dialog, db_connection):
        """Testa exportação de playlist no formato M3U."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup
            main_window = MusicApp(MusicController(db_connection))
            
            music_paths = ["/test/song1.mp3", "/test/song2.mp3"]
            
            # Mock dialog de arquivo
            mock_dialog_instance = MagicMock()
            mock_dialog_instance.ShowModal.return_value = wx.ID_OK
            mock_dialog_instance.GetPath.return_value = "/export/playlist.m3u"
            mock_file_dialog.return_value = mock_dialog_instance
            
            # Mock verificação de arquivos
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    with patch('wx.MessageBox') as mock_msgbox:
                        # Executar exportação
                        main_window._export_playlist_m3u(music_paths)
                        
                        # Verificar que arquivo foi aberto
                        mock_open.assert_called_once_with("/export/playlist.m3u", 'w', encoding='utf-8')
                        
                        # Verificar que conteúdo M3U foi escrito
                        handle = mock_open.return_value.__enter__.return_value
                        write_calls = [call.args[0] for call in handle.write.call_args_list]
                        
                        # Verificar cabeçalho M3U
                        assert any("#EXTM3U" in call for call in write_calls)
                        assert any("2 música(s)" in call for call in write_calls)
                        
                        # Verificar entradas das músicas
                        assert any("/test/song1.mp3" in call for call in write_calls)
                        assert any("/test/song2.mp3" in call for call in write_calls)
                        
                        # Verificar mensagem de sucesso
                        mock_msgbox.assert_called_once()
                        success_msg = mock_msgbox.call_args[0][0]
                        assert "M3U salva com sucesso" in success_msg
        
        finally:
            main_window.Destroy()
            app.Destroy()

    @patch('wx.FileDialog')
    def test_export_playlist_pls(self, mock_file_dialog, db_connection):
        """Testa exportação de playlist no formato PLS."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup
            main_window = MusicApp(MusicController(db_connection))
            
            music_paths = ["/test/song1.mp3", "/test/song2.mp3"]
            
            # Mock dialog de arquivo
            mock_dialog_instance = MagicMock()
            mock_dialog_instance.ShowModal.return_value = wx.ID_OK
            mock_dialog_instance.GetPath.return_value = "/export/playlist.pls"
            mock_file_dialog.return_value = mock_dialog_instance
            
            # Mock verificação de arquivos
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    with patch('wx.MessageBox') as mock_msgbox:
                        # Executar exportação
                        main_window._export_playlist_pls(music_paths)
                        
                        # Verificar que arquivo foi aberto
                        mock_open.assert_called_once_with("/export/playlist.pls", 'w', encoding='utf-8')
                        
                        # Verificar que conteúdo PLS foi escrito
                        handle = mock_open.return_value.__enter__.return_value
                        write_calls = [call.args[0] for call in handle.write.call_args_list]
                        
                        # Verificar cabeçalho PLS
                        assert any("[playlist]" in call for call in write_calls)
                        assert any("NumberOfEntries=2" in call for call in write_calls)
                        
                        # Verificar entradas das músicas
                        assert any("File1=/test/song1.mp3" in call for call in write_calls)
                        assert any("Title1=song1.mp3" in call for call in write_calls)
                        assert any("File2=/test/song2.mp3" in call for call in write_calls)
                        assert any("Title2=song2.mp3" in call for call in write_calls)
                        
                        # Verificar mensagem de sucesso
                        mock_msgbox.assert_called_once()
                        success_msg = mock_msgbox.call_args[0][0]
                        assert "PLS salva com sucesso" in success_msg
        
        finally:
            main_window.Destroy()
            app.Destroy()

    def test_export_selected_playlist_method(self, db_connection):
        """Testa método de exportar playlist de músicas selecionadas."""
        from views.music_app import MusicApp
        
        import wx
        app = wx.App(False)
        
        try:
            # Setup com múltiplas músicas classificadas
            controller = MusicController(db_connection)
            
            music_paths = ["/test/song1.mp3", "/test/song2.mp3"]
            for path in music_paths:
                music_id = controller.music_model.add_music(path)
                controller.music_model.update_stars(music_id, 5)
            
            main_window = MusicApp(controller)
            main_window.update_ranking_list()
            
            # Simular seleção múltipla
            main_window.ranking_list.Select(0)
            main_window.ranking_list.Select(1)
            
            # Mock do método _show_export_playlist_options
            with patch.object(main_window, '_show_export_playlist_options') as mock_show_export:
                # Executar exportação
                main_window.on_export_selected_playlist()
                
                # Verificar que método foi chamado com caminhos corretos
                mock_show_export.assert_called_once()
                called_paths = mock_show_export.call_args[0][0]
                assert len(called_paths) == 2
                assert all(path in music_paths for path in called_paths)
        
        finally:
            main_window.Destroy()
            app.Destroy()
