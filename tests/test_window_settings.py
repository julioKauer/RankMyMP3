"""
Testes para o utilitário de persistência de configurações da janela.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch
from utils.window_settings import WindowSettings


class TestWindowSettings:
    """Testes para a classe WindowSettings."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        # Usar arquivo temporário para testes
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.settings = WindowSettings(config_file=self.temp_file.name)
    
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
        
        # Verificar conteúdo
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        assert data['position'] == [100, 200]
        assert data['size'] == [800, 600]
        assert data['maximized'] == False
    
    def test_save_window_settings_maximized(self):
        """Testa salvamento com janela maximizada."""
        mock_frame = Mock()
        mock_frame.GetPosition.return_value = Mock(x=50, y=75)
        mock_frame.GetSize.return_value = Mock(width=1920, height=1080)
        mock_frame.IsMaximized.return_value = True
        
        self.settings.save_window_settings(mock_frame)
        
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        assert data['maximized'] == True
    
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
        defaults = self.settings.get_default_settings()
        
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
    
    @patch.object(WindowSettings, '_is_position_valid', return_value=True)
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
    
    @patch.object(WindowSettings, '_is_position_valid', return_value=False)
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
