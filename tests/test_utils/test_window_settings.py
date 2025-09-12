"""
Testes para utils.window_settings
"""
import os
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from utils.window_settings import AppSettings


class TestAppSettings(unittest.TestCase):
    """Testes para a classe AppSettings."""
    
    def setUp(self):
        """Configuração para cada teste."""
        # Usar arquivo temporário para não afetar configurações reais
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.app_settings = AppSettings(self.config_file)
        self.app_settings.config_path = self.config_file
    
    def tearDown(self):
        """Limpeza após cada teste."""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_init(self):
        """Testa inicialização da classe."""
        settings = AppSettings("custom_config.json")
        self.assertEqual(settings.config_file, "custom_config.json")
        self.assertIn("custom_config.json", settings.config_path)
    
    def test_save_window_settings(self):
        """Testa salvamento de configurações da janela."""
        # Mock do frame wxPython
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=100, y=150)
        mock_frame.GetSize.return_value = Mock(width=800, height=600)
        mock_frame.IsMaximized.return_value = False
        
        # Salvar configurações
        self.app_settings.save_window_settings(mock_frame)
        
        # Verificar se foi salvo corretamente
        self.assertTrue(os.path.exists(self.config_file))
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('window', data)
        self.assertEqual(data['window']['position'], [100, 150])
        self.assertEqual(data['window']['size'], [800, 600])
        self.assertEqual(data['window']['maximized'], False)
    
    def test_save_window_settings_error(self):
        """Testa erro ao salvar configurações da janela."""
        # Mock do frame que causa erro
        mock_frame = Mock()
        mock_frame.GetPosition.side_effect = Exception("Erro de teste")
        
        # Capturar print de erro
        with patch('builtins.print') as mock_print:
            self.app_settings.save_window_settings(mock_frame)
            mock_print.assert_called_once()
            self.assertIn("Erro ao salvar configurações da janela", str(mock_print.call_args))
    
    def test_save_layout_settings(self):
        """Testa salvamento de configurações de layout."""
        column_widths = [70, 350, 100, 200]
        splitter_pos = 500
        tags_expanded = True
        tags_splitter_pos = -200
        
        self.app_settings.save_layout_settings(column_widths, splitter_pos, tags_expanded, tags_splitter_pos)
        
        # Verificar se foi salvo corretamente
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('layout', data)
        self.assertEqual(data['layout']['column_widths'], column_widths)
        self.assertEqual(data['layout']['splitter_position'], splitter_pos)
        self.assertEqual(data['layout']['tags_panel_expanded'], tags_expanded)
        self.assertEqual(data['layout']['tags_splitter_position'], tags_splitter_pos)
    
    def test_save_layout_settings_with_existing_data(self):
        """Testa salvamento de layout preservando dados existentes."""
        # Criar dados existentes de janela
        existing_data = {
            'window': {
                'position': [50, 50],
                'size': [1000, 800],
                'maximized': True
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(existing_data, f)
        
        # Salvar layout
        self.app_settings.save_layout_settings([80, 400, 120, 250], 600, False)
        
        # Verificar se preservou dados da janela
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('window', data)
        self.assertIn('layout', data)
        self.assertEqual(data['window']['position'], [50, 50])
    
    def test_save_all_settings(self):
        """Testa salvamento de todas as configurações."""
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=200, y=300)
        mock_frame.GetSize.return_value = Mock(width=1200, height=700)
        mock_frame.IsMaximized.return_value = True
        
        column_widths = [60, 300, 90, 180]
        splitter_pos = 450
        tags_expanded = False
        
        self.app_settings.save_all_settings(mock_frame, column_widths, splitter_pos, tags_expanded)
        
        # Verificar se salvou tudo corretamente
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('window', data)
        self.assertIn('layout', data)
        self.assertEqual(data['window']['position'], [200, 300])
        self.assertEqual(data['layout']['column_widths'], column_widths)
    
    def test_load_settings_file_not_exists(self):
        """Testa carregamento quando arquivo não existe."""
        result = self.app_settings.load_settings()
        self.assertIsNone(result)
    
    def test_load_settings_success(self):
        """Testa carregamento bem-sucedido."""
        test_data = {
            'window': {
                'position': [100, 100],
                'size': [800, 600],
                'maximized': False
            },
            'layout': {
                'column_widths': [70, 350, 100, 200],
                'splitter_position': 500,
                'tags_panel_expanded': True
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.app_settings.load_settings()
        self.assertEqual(result, test_data)
    
    def test_load_settings_invalid_json(self):
        """Testa carregamento com JSON inválido."""
        with open(self.config_file, 'w') as f:
            f.write("invalid json content")
        
        with patch('builtins.print') as mock_print:
            result = self.app_settings.load_settings()
            self.assertIsNone(result)
            mock_print.assert_called_once()
    
    def test_load_window_settings(self):
        """Testa carregamento de configurações da janela."""
        test_data = {
            'window': {
                'position': [50, 75],
                'size': [900, 650],
                'maximized': True
            },
            'layout': {
                'column_widths': [80, 400, 120, 250]
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.app_settings.load_window_settings()
        self.assertEqual(result, test_data['window'])
    
    def test_load_window_settings_old_format(self):
        """Testa carregamento de formato antigo de configurações."""
        old_format_data = {
            'position': [100, 200],
            'size': [1000, 700],
            'maximized': False
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(old_format_data, f)
        
        result = self.app_settings.load_window_settings()
        self.assertEqual(result, old_format_data)
    
    def test_load_layout_settings(self):
        """Testa carregamento de configurações de layout."""
        test_data = {
            'window': {
                'position': [100, 100],
                'size': [800, 600]
            },
            'layout': {
                'column_widths': [70, 350, 100, 200],
                'splitter_position': 500,
                'tags_panel_expanded': False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.app_settings.load_layout_settings()
        self.assertEqual(result, test_data['layout'])
    
    def test_apply_window_settings(self):
        """Testa aplicação de configurações da janela."""
        mock_frame = Mock()
        settings = {
            'position': [150, 200],
            'size': [900, 700],
            'maximized': True
        }
        
        with patch.object(self.app_settings, '_is_position_valid', return_value=True):
            self.app_settings.apply_window_settings(mock_frame, settings)
        
        mock_frame.SetPosition.assert_called_once_with((150, 200))
        mock_frame.SetSize.assert_called_once_with((900, 700))
        mock_frame.Maximize.assert_called_once()
    
    def test_apply_window_settings_invalid_position(self):
        """Testa aplicação com posição inválida."""
        mock_frame = Mock()
        settings = {
            'position': [-5000, -5000],
            'size': [900, 700],
            'maximized': False
        }
        
        with patch.object(self.app_settings, '_is_position_valid', return_value=False):
            self.app_settings.apply_window_settings(mock_frame, settings)
        
        # Não deve aplicar posição/tamanho se posição é inválida
        mock_frame.SetPosition.assert_not_called()
        mock_frame.SetSize.assert_not_called()
        mock_frame.Maximize.assert_not_called()
    
    def test_apply_window_settings_none(self):
        """Testa aplicação com settings None."""
        mock_frame = Mock()
        self.app_settings.apply_window_settings(mock_frame, None)
        
        # Não deve chamar nenhum método do frame
        mock_frame.SetPosition.assert_not_called()
        mock_frame.SetSize.assert_not_called()
        mock_frame.Maximize.assert_not_called()
    
    def test_apply_layout_settings(self):
        """Testa aplicação de configurações de layout - apenas larguras."""
        mock_ranking_list = Mock()
        mock_splitter = Mock()
        layout_settings = {
            'column_widths': [80, 400, 120, 250]
            # Não incluir splitter_position para evitar wx.CallAfter
        }
        
        result = self.app_settings.apply_layout_settings(mock_ranking_list, mock_splitter, layout_settings)
        
        self.assertTrue(result)
        # Verificar se aplicou larguras das colunas
        self.assertEqual(mock_ranking_list.SetColumnWidth.call_count, 4)
        mock_ranking_list.SetColumnWidth.assert_any_call(0, 80)
        mock_ranking_list.SetColumnWidth.assert_any_call(1, 400)
    
    def test_apply_layout_settings_invalid_widths(self):
        """Testa aplicação com larguras inválidas."""
        mock_ranking_list = Mock()
        mock_splitter = Mock()
        layout_settings = {
            'column_widths': [80, 400, 0, -50]  # Larguras inválidas
            # Não incluir splitter_position para evitar wx.CallAfter
        }
        
        result = self.app_settings.apply_layout_settings(mock_ranking_list, mock_splitter, layout_settings)
        
        self.assertTrue(result)
        # Deve aplicar apenas larguras válidas (> 0)
        mock_ranking_list.SetColumnWidth.assert_any_call(0, 80)
        mock_ranking_list.SetColumnWidth.assert_any_call(1, 400)
        # Não deve aplicar larguras <= 0
        self.assertEqual(mock_ranking_list.SetColumnWidth.call_count, 2)
    
    def test_apply_layout_settings_with_splitter_error(self):
        """Testa aplicação que falha por causa do wx."""
        mock_ranking_list = Mock()
        mock_splitter = Mock()
        layout_settings = {
            'column_widths': [80, 400, 120, 250],
            'splitter_position': 600  # Isso vai causar erro no wx.CallAfter
        }
        
        # Deve retornar False por causa do erro do wx
        result = self.app_settings.apply_layout_settings(mock_ranking_list, mock_splitter, layout_settings)
        self.assertFalse(result)
    
    def test_apply_layout_settings_none(self):
        """Testa aplicação com layout_settings None."""
        mock_ranking_list = Mock()
        mock_splitter = Mock()
        
        result = self.app_settings.apply_layout_settings(mock_ranking_list, mock_splitter, None)
        
        self.assertFalse(result)
        mock_ranking_list.SetColumnWidth.assert_not_called()
    
    def test_get_tags_panel_state(self):
        """Testa obtenção do estado do painel de tags."""
        # Sem configurações salvas
        result = self.app_settings.get_tags_panel_state()
        self.assertFalse(result)  # Padrão: recolhido
        
        # Com configurações salvas
        test_data = {
            'layout': {
                'tags_panel_expanded': True
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.app_settings.get_tags_panel_state()
        self.assertTrue(result)
    
    def test_validate_settings_valid(self):
        """Testa validação com configurações válidas."""
        valid_settings = {
            'position': [100, 150],
            'size': [800, 600],
            'maximized': False
        }
        
        result = self.app_settings._validate_settings(valid_settings)
        self.assertTrue(result)
    
    def test_validate_settings_invalid(self):
        """Testa validação com configurações inválidas."""
        # Sem campos obrigatórios
        invalid1 = {'position': [100, 150]}
        self.assertFalse(self.app_settings._validate_settings(invalid1))
        
        # Tipo inválido
        invalid2 = {
            'position': "invalid",
            'size': [800, 600]
        }
        self.assertFalse(self.app_settings._validate_settings(invalid2))
        
        # Tamanho negativo
        invalid3 = {
            'position': [100, 150],
            'size': [-800, 600]
        }
        self.assertFalse(self.app_settings._validate_settings(invalid3))
    
    def test_validate_layout_settings_valid(self):
        """Testa validação de configurações de layout válidas."""
        valid_layout = {
            'column_widths': [70, 350, 100, 200],
            'splitter_position': 500,
            'tags_panel_expanded': True
        }
        
        result = self.app_settings._validate_layout_settings(valid_layout)
        self.assertTrue(result)
    
    def test_validate_layout_settings_invalid(self):
        """Testa validação de configurações de layout inválidas."""
        # Larguras inválidas
        invalid1 = {
            'column_widths': [70, 350, -100],  # Muito poucas colunas
            'splitter_position': 500
        }
        self.assertFalse(self.app_settings._validate_layout_settings(invalid1))
        
        # Posição de splitter inválida
        invalid2 = {
            'column_widths': [70, 350, 100, 200],
            'splitter_position': -500
        }
        self.assertFalse(self.app_settings._validate_layout_settings(invalid2))
        
        # Tipo inválido para estado do painel
        invalid3 = {
            'tags_panel_expanded': "true"  # String ao invés de bool
        }
        self.assertFalse(self.app_settings._validate_layout_settings(invalid3))
    
    def test_is_position_valid_no_wx(self):
        """Testa validação de posição quando wx não está disponível."""
        # Quando wx não está disponível, deve retornar False
        result = self.app_settings._is_position_valid(100, 100, 800, 600)
        self.assertFalse(result)  # Deve retornar False quando não consegue importar wx
    
    def test_get_default_settings(self):
        """Testa obtenção de configurações padrão."""
        defaults = self.app_settings.get_default_settings()
        
        self.assertIn('window', defaults)
        self.assertIn('layout', defaults)
        self.assertEqual(defaults['window']['position'], [100, 100])
        self.assertEqual(defaults['layout']['column_widths'], [70, 350, 100, 200])
    
    def test_get_default_window_settings(self):
        """Testa obtenção de configurações padrão da janela."""
        window_defaults = self.app_settings.get_default_window_settings()
        
        self.assertEqual(window_defaults['position'], [100, 100])
        self.assertEqual(window_defaults['size'], [1200, 700])
        self.assertEqual(window_defaults['maximized'], False)
    
    def test_get_default_layout_settings(self):
        """Testa obtenção de configurações padrão do layout."""
        layout_defaults = self.app_settings.get_default_layout_settings()
        
        self.assertEqual(layout_defaults['column_widths'], [70, 350, 100, 200])
        self.assertEqual(layout_defaults['splitter_position'], 500)
        self.assertEqual(layout_defaults['tags_panel_expanded'], False)


if __name__ == '__main__':
    unittest.main()
