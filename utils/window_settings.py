"""
Utilitário para gerenciar persistência de configurações da janela.
Salva e carrega tamanho, posição e estado da janela.
"""
import json
import os
from typing import Dict, Tuple, Optional


class WindowSettings:
    """Gerencia persistência de configurações da janela principal."""
    
    def __init__(self, config_file: str = "window_config.json"):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_file: Nome do arquivo de configuração
        """
        self.config_file = config_file
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
        
    def save_window_settings(self, frame) -> None:
        """
        Salva configurações da janela.
        
        Args:
            frame: Frame wxPython da janela principal
        """
        try:
            # Obter posição e tamanho da janela
            position = frame.GetPosition()
            size = frame.GetSize()
            is_maximized = frame.IsMaximized()
            
            settings = {
                'position': [position.x, position.y],
                'size': [size.width, size.height],
                'maximized': is_maximized
            }
            
            # Salvar no arquivo JSON
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar configurações da janela: {e}")
    
    def load_window_settings(self) -> Optional[Dict]:
        """
        Carrega configurações da janela.
        
        Returns:
            Dict com configurações ou None se não existir
        """
        try:
            if not os.path.exists(self.config_path):
                return None
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # Validar se as configurações são válidas
            if self._validate_settings(settings):
                return settings
            else:
                return None
                
        except Exception as e:
            print(f"Erro ao carregar configurações da janela: {e}")
            return None
    
    def apply_window_settings(self, frame, settings: Dict) -> None:
        """
        Aplica configurações à janela.
        
        Args:
            frame: Frame wxPython da janela principal
            settings: Dict com configurações da janela
        """
        try:
            if settings is None:
                return
                
            # Aplicar posição e tamanho
            if 'position' in settings and 'size' in settings:
                x, y = settings['position']
                width, height = settings['size']
                
                # Verificar se a posição está dentro dos limites da tela
                if self._is_position_valid(x, y, width, height):
                    frame.SetPosition((x, y))
                    frame.SetSize((width, height))
                
            # Aplicar estado maximizado
            if settings.get('maximized', False):
                frame.Maximize()
                
        except Exception as e:
            print(f"Erro ao aplicar configurações da janela: {e}")
    
    def _validate_settings(self, settings: Dict) -> bool:
        """
        Valida se as configurações são válidas.
        
        Args:
            settings: Dict com configurações
            
        Returns:
            True se válidas, False caso contrário
        """
        try:
            if not isinstance(settings, dict):
                return False
                
            # Verificar se tem os campos necessários
            if 'position' not in settings or 'size' not in settings:
                return False
                
            # Verificar tipos
            position = settings['position']
            size = settings['size']
            
            if not (isinstance(position, list) and len(position) == 2):
                return False
                
            if not (isinstance(size, list) and len(size) == 2):
                return False
                
            # Verificar se são números válidos
            if not all(isinstance(x, (int, float)) for x in position + size):
                return False
                
            # Verificar se o tamanho é positivo
            if size[0] <= 0 or size[1] <= 0:
                return False
                
            return True
            
        except Exception:
            return False
    
    def _is_position_valid(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Verifica se a posição da janela está dentro dos limites da tela.
        
        Args:
            x, y: Posição da janela
            width, height: Tamanho da janela
            
        Returns:
            True se a posição é válida
        """
        try:
            import wx
            
            # Obter informações da tela
            display = wx.Display()
            screen_geometry = display.GetGeometry()
            
            # Verificar se pelo menos parte da janela está visível
            window_right = x + width
            window_bottom = y + height
            
            # A janela deve ter pelo menos 100px visíveis em cada direção
            min_visible = 100
            
            if (window_right < min_visible or 
                x > screen_geometry.width - min_visible or
                window_bottom < min_visible or 
                y > screen_geometry.height - min_visible):
                return False
                
            return True
            
        except Exception:
            # Em caso de erro, considerar posição como inválida
            return False
    
    def get_default_settings(self) -> Dict:
        """
        Retorna configurações padrão da janela.
        
        Returns:
            Dict com configurações padrão
        """
        return {
            'position': [100, 100],
            'size': [1200, 700],
            'maximized': False
        }
