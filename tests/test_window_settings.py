"""
Testes para o utilitário de persistência de configurações da aplicação.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch
from utils.window_settings import AppSettings


class TestAppSettings:
    """Testes para a classe AppSettings."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        # Usar arquivo temporário para testes
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.settings = AppSettings(config_file=self.temp_file.name)
    
    def teardown_method(self):
        """Limpeza após cada teste."""
        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass
    
    def test_save_window_settings_basic(self):
        """Testa salvamento básico de configurações."""
        # Mock do frame wxPython
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=100, y=200)
        mock_frame.GetSize.return_value = Mock(width=800, height=600)
        mock_frame.IsMaximized.return_value = False
        
        # Salvar configurações
        self.settings.save_window_settings(mock_frame)
        
        # Verificar se arquivo foi criado
        assert os.path.exists(self.temp_file.name)
        
        # Verificar conteúdo (novo formato)
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        assert 'window' in data
        assert data['window']['position'] == [100, 200]
        assert data['window']['size'] == [800, 600]
        assert data['window']['maximized'] == False
    
    def test_save_window_settings_maximized(self):
        """Testa salvamento com janela maximizada."""
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=50, y=75)
        mock_frame.GetSize.return_value = Mock(width=1920, height=1080)
        mock_frame.IsMaximized.return_value = True
        
        self.settings.save_window_settings(mock_frame)
        
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        assert 'window' in data
        assert data['window']['maximized'] == True
    
    def test_load_window_settings_nonexistent(self):
        """Testa carregamento quando arquivo não existe."""
        # Remover arquivo temporário
        os.unlink(self.temp_file.name)
        
        result = self.settings.load_window_settings()
        assert result is None
    
    def test_load_window_settings_valid(self):
        """Testa carregamento de configurações válidas."""
        # Criar arquivo de configuração válido
        test_data = {
            'position': [150, 250],
            'size': [900, 700],
            'maximized': False
        }
        
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)
        
        result = self.settings.load_window_settings()
        assert result == test_data
    
    def test_load_window_settings_invalid_json(self):
        """Testa carregamento com JSON inválido."""
        # Criar arquivo com JSON inválido
        with open(self.temp_file.name, 'w') as f:
            f.write("invalid json content")
        
        result = self.settings.load_window_settings()
        assert result is None
    
    def test_validate_settings_valid(self):
        """Testa validação de configurações válidas."""
        valid_settings = {
            'position': [100, 200],
            'size': [800, 600],
            'maximized': False
        }
        
        assert self.settings._validate_settings(valid_settings) == True
    
    def test_validate_settings_invalid_structure(self):
        """Testa validação com estruturas inválidas."""
        # Não é dict
        assert self.settings._validate_settings("not a dict") == False
        
        # Falta position
        assert self.settings._validate_settings({'size': [800, 600]}) == False
        
        # Falta size
        assert self.settings._validate_settings({'position': [100, 200]}) == False
        
        # Position não é lista
        assert self.settings._validate_settings({
            'position': 'not a list',
            'size': [800, 600]
        }) == False
        
        # Size com tamanho errado
        assert self.settings._validate_settings({
            'position': [100, 200],
            'size': [800]  # Só um elemento
        }) == False
        
        # Size com valores negativos
        assert self.settings._validate_settings({
            'position': [100, 200],
            'size': [-800, 600]
        }) == False
    
    def test_validate_settings_invalid_types(self):
        """Testa validação com tipos inválidos."""
        # Valores não numéricos
        assert self.settings._validate_settings({
            'position': ['not', 'numbers'],
            'size': [800, 600]
        }) == False
        
        assert self.settings._validate_settings({
            'position': [100, 200],
            'size': ['not', 'numbers']
        }) == False
    
    @patch('wx.Display')
    def test_is_position_valid_within_screen(self, mock_display):
        """Testa validação de posição dentro da tela."""
        # Mock da tela
        mock_geometry = Mock()
        mock_geometry.width = 1920
        mock_geometry.height = 1080
        
        mock_display_instance = Mock()
        mock_display_instance.GetGeometry.return_value = mock_geometry
        mock_display.return_value = mock_display_instance
        
        # Posição válida (bem dentro da tela)
        assert self.settings._is_position_valid(100, 100, 800, 600) == True
        
        # Posição no limite (ainda válida)
        assert self.settings._is_position_valid(1820, 980, 100, 100) == True
    
    @patch('wx.Display')
    def test_is_position_valid_outside_screen(self, mock_display):
        """Testa validação de posição fora da tela."""
        mock_geometry = Mock()
        mock_geometry.width = 1920
        mock_geometry.height = 1080
        
        mock_display_instance = Mock()
        mock_display_instance.GetGeometry.return_value = mock_geometry
        mock_display.return_value = mock_display_instance
        
        # Muito longe à direita
        assert self.settings._is_position_valid(2000, 100, 800, 600) == False
        
        # Muito longe para baixo
        assert self.settings._is_position_valid(100, 1200, 800, 600) == False
        
        # Muito longe à esquerda
        assert self.settings._is_position_valid(-900, 100, 800, 600) == False
        
        # Muito longe para cima
        assert self.settings._is_position_valid(100, -700, 800, 600) == False
    
    def test_get_default_settings(self):
        """Testa configurações padrão."""
        defaults = self.settings.get_default_window_settings()
        
        assert defaults['position'] == [100, 100]
        assert defaults['size'] == [1200, 700]
        assert defaults['maximized'] == False
    
    def test_apply_window_settings_none(self):
        """Testa aplicação de configurações quando settings é None."""
        mock_frame = Mock()
        
        # Não deve fazer nada
        self.settings.apply_window_settings(mock_frame, None)
        
        # Verificar que métodos não foram chamados
        mock_frame.SetPosition.assert_not_called()
        mock_frame.SetSize.assert_not_called()
        mock_frame.Maximize.assert_not_called()
    
    @patch.object(AppSettings, '_is_position_valid', return_value=True)
    def test_apply_window_settings_valid(self, mock_valid):
        """Testa aplicação de configurações válidas."""
        mock_frame = Mock()
        
        settings = {
            'position': [150, 250],
            'size': [900, 700],
            'maximized': True
        }
        
        self.settings.apply_window_settings(mock_frame, settings)
        
        mock_frame.SetPosition.assert_called_once_with((150, 250))
        mock_frame.SetSize.assert_called_once_with((900, 700))
        mock_frame.Maximize.assert_called_once()
    
    @patch.object(AppSettings, '_is_position_valid', return_value=False)
    def test_apply_window_settings_invalid_position(self, mock_valid):
        """Testa aplicação quando posição é inválida."""
        mock_frame = Mock()
        
        settings = {
            'position': [2000, 2000],  # Fora da tela
            'size': [900, 700],
            'maximized': False
        }
        
        self.settings.apply_window_settings(mock_frame, settings)
        
        # Posição e tamanho não devem ser aplicados
        mock_frame.SetPosition.assert_not_called()
        mock_frame.SetSize.assert_not_called()
        mock_frame.Maximize.assert_not_called()
    
    def test_save_load_roundtrip(self):
        """Testa ciclo completo de salvar e carregar."""
        # Mock do frame
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=300, y=400)
        mock_frame.GetSize.return_value = Mock(width=1000, height=800)
        mock_frame.IsMaximized.return_value = True
        
        # Salvar
        self.settings.save_window_settings(mock_frame)
        
        # Carregar
        loaded = self.settings.load_window_settings()
        
        # Verificar
        assert loaded['position'] == [300, 400]
        assert loaded['size'] == [1000, 800]
        assert loaded['maximized'] == True
    
    def test_error_handling_save(self):
        """Testa tratamento de erro durante salvamento."""
        # Remover arquivo temporário primeiro
        os.unlink(self.temp_file.name)
        
        # Mock que lança exceção
        mock_frame = Mock()
        mock_frame.GetPosition.side_effect = Exception("Test error")
        
        # Não deve lançar exceção
        self.settings.save_window_settings(mock_frame)
        
        # Arquivo não deve ter sido criado
        assert not os.path.exists(self.temp_file.name)
    
    def test_error_handling_load_permission(self):
        """Testa tratamento de erro de permissão durante carregamento."""
        # Criar arquivo e remover permissão de leitura
        with open(self.temp_file.name, 'w') as f:
            json.dump({'position': [100, 200], 'size': [800, 600]}, f)
        
        os.chmod(self.temp_file.name, 0o000)  # Remove todas as permissões
        
        try:
            result = self.settings.load_window_settings()
            assert result is None
        finally:
            # Restaurar permissões para limpeza
            os.chmod(self.temp_file.name, 0o644)
    
    # ===================== NOVOS TESTES PARA LAYOUT =====================
    
    def test_save_layout_settings_basic(self):
        """Testa salvamento básico de configurações de layout."""
        column_widths = [80, 400, 120, 250]
        splitter_pos = 600
        tags_expanded = True
        
        # Salvar configurações de layout
        self.settings.save_layout_settings(column_widths, splitter_pos, tags_expanded)
        
        # Verificar se arquivo foi criado
        assert os.path.exists(self.temp_file.name)
        
        # Verificar conteúdo
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        assert 'layout' in data
        assert data['layout']['column_widths'] == column_widths
        assert data['layout']['splitter_position'] == splitter_pos
        assert data['layout']['tags_panel_expanded'] == tags_expanded
    
    def test_save_all_settings_complete(self):
        """Testa salvamento de todas as configurações de uma vez."""
        # Mock do frame
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=150, y=250)
        mock_frame.GetSize.return_value = Mock(width=1000, height=800)
        mock_frame.IsMaximized.return_value = False
        
        column_widths = [70, 350, 100, 200]
        splitter_pos = 500
        tags_expanded = False
        
        # Salvar todas as configurações
        self.settings.save_all_settings(mock_frame, column_widths, splitter_pos, tags_expanded)
        
        # Verificar estrutura completa
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        # Verificar seção window
        assert 'window' in data
        assert data['window']['position'] == [150, 250]
        assert data['window']['size'] == [1000, 800]
        assert data['window']['maximized'] == False
        
        # Verificar seção layout
        assert 'layout' in data
        assert data['layout']['column_widths'] == column_widths
        assert data['layout']['splitter_position'] == splitter_pos
        assert data['layout']['tags_panel_expanded'] == tags_expanded
    
    def test_load_layout_settings_valid(self):
        """Testa carregamento de configurações de layout válidas."""
        test_data = {
            'window': {
                'position': [100, 200],
                'size': [800, 600],
                'maximized': False
            },
            'layout': {
                'column_widths': [75, 375, 125, 225],
                'splitter_position': 550,
                'tags_panel_expanded': True
            }
        }
        
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)
        
        layout_result = self.settings.load_layout_settings()
        assert layout_result == test_data['layout']
    
    def test_load_layout_settings_nonexistent(self):
        """Testa carregamento quando não há configurações de layout."""
        # Remover arquivo
        os.unlink(self.temp_file.name)
        
        result = self.settings.load_layout_settings()
        assert result is None
    
    def test_get_tags_panel_state(self):
        """Testa obtenção do estado do painel de tags."""
        # Criar arquivo com estado expandido
        test_data = {
            'layout': {
                'column_widths': [70, 350, 100, 200],
                'splitter_position': 500,
                'tags_panel_expanded': True
            }
        }
        
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)
        
        assert self.settings.get_tags_panel_state() == True
        
        # Testar estado recolhido
        test_data['layout']['tags_panel_expanded'] = False
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)
        
        assert self.settings.get_tags_panel_state() == False
        
        # Testar sem arquivo
        os.unlink(self.temp_file.name)
        assert self.settings.get_tags_panel_state() == False
    
    def test_validate_layout_settings_valid(self):
        """Testa validação de configurações de layout válidas."""
        valid_layouts = [
            {
                'column_widths': [70, 350, 100, 200],
                'splitter_position': 500,
                'tags_panel_expanded': False
            },
            {
                'column_widths': [100, 400, 150, 250],
                'splitter_position': 600,
                'tags_panel_expanded': True
            },
            # Só com alguns campos
            {
                'column_widths': [70, 350, 100, 200]
            },
            {
                'splitter_position': 500
            },
            {
                'tags_panel_expanded': True
            }
        ]
        
        for layout in valid_layouts:
            assert self.settings._validate_layout_settings(layout) == True
    
    def test_validate_layout_settings_invalid(self):
        """Testa validação de configurações de layout inválidas."""
        invalid_layouts = [
            # column_widths inválidos
            {'column_widths': [70, 350, 100]},  # Lista muito curta
            {'column_widths': [70, 350, 100, 200, 50]},  # Lista muito longa
            {'column_widths': [-70, 350, 100, 200]},  # Valor negativo
            {'column_widths': [0, 350, 100, 200]},  # Valor zero
            {'column_widths': "not a list"},  # Não é lista
            
            # splitter_position inválidos
            {'splitter_position': -100},  # Negativo
            {'splitter_position': 0},  # Zero
            {'splitter_position': "not a number"},  # Não é número
            
            # tags_panel_expanded inválidos
            {'tags_panel_expanded': "not a bool"},  # Não é boolean
            {'tags_panel_expanded': 1},  # Número em vez de boolean
            
            # Não é dict
            "not a dict",
            None,
            []
        ]
        
        for layout in invalid_layouts:
            assert self.settings._validate_layout_settings(layout) == False
    
    def test_get_default_settings_complete(self):
        """Testa configurações padrão completas."""
        defaults = self.settings.get_default_settings()
        
        # Verificar estrutura
        assert 'window' in defaults
        assert 'layout' in defaults
        
        # Verificar valores padrão da janela
        assert defaults['window']['position'] == [100, 100]
        assert defaults['window']['size'] == [1200, 700]
        assert defaults['window']['maximized'] == False
        
        # Verificar valores padrão do layout
        assert defaults['layout']['column_widths'] == [70, 350, 100, 200]
        assert defaults['layout']['splitter_position'] == 500
        assert defaults['layout']['tags_panel_expanded'] == False
    
    def test_backward_compatibility_window_settings(self):
        """Testa compatibilidade com formato antigo de configurações."""
        # Criar arquivo no formato antigo (só janela)
        old_format = {
            'position': [200, 300],
            'size': [900, 700],
            'maximized': True
        }
        
        with open(self.temp_file.name, 'w') as f:
            json.dump(old_format, f)
        
        # Deve carregar configurações da janela corretamente
        window_settings = self.settings.load_window_settings()
        assert window_settings == old_format
        
        # Layout deve retornar None
        layout_settings = self.settings.load_layout_settings()
        assert layout_settings is None
    
    def test_incremental_settings_update(self):
        """Testa atualização incremental de configurações."""
        # Salvar configurações de janela primeiro
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=100, y=200)
        mock_frame.GetSize.return_value = Mock(width=800, height=600)
        mock_frame.IsMaximized.return_value = False
        
        self.settings.save_window_settings(mock_frame)
        
        # Verificar que só tem seção window
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        assert 'window' in data
        assert 'layout' not in data
        
        # Agora salvar configurações de layout
        self.settings.save_layout_settings([70, 350, 100, 200], 500, False)
        
        # Verificar que tem ambas as seções
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        assert 'window' in data
        assert 'layout' in data
        
        # Configurações da janela devem ter sido preservadas
        assert data['window']['position'] == [100, 200]
        assert data['layout']['column_widths'] == [70, 350, 100, 200]
