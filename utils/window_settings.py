"""
Utilitário para gerenciar persistência de configurações da aplicação.
Salva e carrega tamanho, posição da janela e configurações de layout.
"""
import json
import os
from typing import Dict, Tuple, Optional, List


class AppSettings:
    """Gerencia persistência de configurações da aplicação (janela + layout)."""
    
    def __init__(self, config_file: str = "app_config.json"):
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
            # Carregar configurações existentes ou criar novas
            existing_settings = self.load_settings() or {}
            
            # Obter posição e tamanho da janela
            position = frame.GetPosition()
            size = frame.GetSize()
            is_maximized = frame.IsMaximized()
            
            # Atualizar seção de janela
            existing_settings['window'] = {
                'position': [position.x, position.y],
                'size': [size.width, size.height],
                'maximized': is_maximized
            }
            
            # Salvar no arquivo JSON
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar configurações da janela: {e}")
    
    def save_layout_settings(self, column_widths: List[int], splitter_pos: int, tags_expanded: bool, tags_splitter_pos: int = -150) -> None:
        """
        Salva configurações de layout.
        
        Args:
            column_widths: Lista com larguras das colunas [posição, música, estrelas, tags]
            splitter_pos: Posição do divisor entre árvore e ranking
            tags_expanded: Se o painel de tags está expandido
            tags_splitter_pos: Posição do divisor do painel de tags
        """
        try:
            # Carregar configurações existentes ou criar novas
            existing_settings = self.load_settings() or {}
            
            # Atualizar seção de layout
            existing_settings['layout'] = {
                'column_widths': column_widths,
                'splitter_position': splitter_pos,
                'tags_panel_expanded': tags_expanded,
                'tags_splitter_position': tags_splitter_pos
            }
            
            # Salvar no arquivo JSON
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar configurações de layout: {e}")
    
    def save_all_settings(self, frame, column_widths: List[int], splitter_pos: int, tags_expanded: bool, tags_splitter_pos: int = -150) -> None:
        """
        Salva todas as configurações de uma vez.
        
        Args:
            frame: Frame wxPython da janela principal
            column_widths: Lista com larguras das colunas
            splitter_pos: Posição do divisor
            tags_expanded: Se o painel de tags está expandido
            tags_splitter_pos: Posição do divisor do painel de tags
        """
        try:
            # Obter dados da janela
            position = frame.GetPosition()
            size = frame.GetSize()
            is_maximized = frame.IsMaximized()
            
            settings = {
                'window': {
                    'position': [position.x, position.y],
                    'size': [size.width, size.height],
                    'maximized': is_maximized
                },
                'layout': {
                    'column_widths': column_widths,
                    'splitter_position': splitter_pos,
                    'tags_panel_expanded': tags_expanded,
                    'tags_splitter_position': tags_splitter_pos
                }
            }
            
            # Salvar no arquivo JSON
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar todas as configurações: {e}")
    
    def load_settings(self) -> Optional[Dict]:
        """
        Carrega todas as configurações.
        
        Returns:
            Dict com todas as configurações ou None se não existir
        """
        try:
            if not os.path.exists(self.config_path):
                return None
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # Validar se as configurações são válidas
            if self._validate_all_settings(settings):
                return settings
            else:
                return None
                
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return None
    
    def load_window_settings(self) -> Optional[Dict]:
        """
        Carrega apenas configurações da janela.
        
        Returns:
            Dict com configurações da janela ou None se não existir
        """
        settings = self.load_settings()
        if settings and 'window' in settings:
            return settings['window']
        
        # Fallback para formato antigo (compatibilidade)
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    old_settings = json.load(f)
                
                # Se é formato antigo (sem seção 'window')
                if 'position' in old_settings and 'window' not in old_settings:
                    return old_settings
        except Exception:
            pass
            
        return None
    
    def load_layout_settings(self) -> Optional[Dict]:
        """
        Carrega apenas configurações de layout.
        
        Returns:
            Dict com configurações de layout ou None se não existir
        """
        settings = self.load_settings()
        if settings and 'layout' in settings:
            return settings['layout']
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
    
    def apply_layout_settings(self, ranking_list, main_splitter, layout_settings: Dict) -> bool:
        """
        Aplica configurações de layout.
        
        Args:
            ranking_list: ListCtrl do ranking para aplicar larguras das colunas
            main_splitter: SplitterWindow para aplicar posição do divisor
            layout_settings: Dict com configurações de layout
            
        Returns:
            True se aplicou com sucesso, False caso contrário
        """
        try:
            if layout_settings is None:
                return False
            
            # Aplicar larguras das colunas
            if 'column_widths' in layout_settings:
                widths = layout_settings['column_widths']
                if len(widths) == 4:  # [posição, música, estrelas, tags]
                    for i, width in enumerate(widths):
                        if width > 0:  # Validar largura positiva
                            ranking_list.SetColumnWidth(i, width)
            
            # Aplicar posição do splitter
            if 'splitter_position' in layout_settings:
                splitter_pos = layout_settings['splitter_position']
                if splitter_pos > 0:
                    # Usar CallAfter para garantir que o splitter já foi inicializado
                    import wx
                    wx.CallAfter(main_splitter.SetSashPosition, splitter_pos)
            
            return True
            
        except Exception as e:
            print(f"Erro ao aplicar configurações de layout: {e}")
            return False
    
    def get_tags_panel_state(self) -> bool:
        """
        Retorna o estado salvo do painel de tags.
        
        Returns:
            True se deve estar expandido, False caso contrário
        """
        layout_settings = self.load_layout_settings()
        if layout_settings and 'tags_panel_expanded' in layout_settings:
            return layout_settings['tags_panel_expanded']
        return False  # Padrão: recolhido
    
    def _validate_all_settings(self, settings: Dict) -> bool:
        """
        Valida se todas as configurações são válidas.
        
        Args:
            settings: Dict com todas as configurações
            
        Returns:
            True se válidas, False caso contrário
        """
        try:
            if not isinstance(settings, dict):
                return False
            
            # Validar seção de janela se existir
            if 'window' in settings:
                if not self._validate_window_settings(settings['window']):
                    return False
            
            # Validar seção de layout se existir
            if 'layout' in settings:
                if not self._validate_layout_settings(settings['layout']):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_window_settings(self, window_settings: Dict) -> bool:
        """
        Valida configurações da janela.
        
        Args:
            window_settings: Dict com configurações da janela
            
        Returns:
            True se válidas, False caso contrário
        """
        return self._validate_settings(window_settings)  # Usar método existente
    
    def _validate_layout_settings(self, layout_settings: Dict) -> bool:
        """
        Valida configurações de layout.
        
        Args:
            layout_settings: Dict com configurações de layout
            
        Returns:
            True se válidas, False caso contrário
        """
        try:
            if not isinstance(layout_settings, dict):
                return False
            
            # Validar larguras das colunas
            if 'column_widths' in layout_settings:
                widths = layout_settings['column_widths']
                if not isinstance(widths, list) or len(widths) != 4:
                    return False
                if not all(isinstance(w, (int, float)) and w > 0 for w in widths):
                    return False
            
            # Validar posição do splitter
            if 'splitter_position' in layout_settings:
                pos = layout_settings['splitter_position']
                if not isinstance(pos, (int, float)) or pos <= 0:
                    return False
            
            # Validar estado do painel de tags
            if 'tags_panel_expanded' in layout_settings:
                expanded = layout_settings['tags_panel_expanded']
                if not isinstance(expanded, bool):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_settings(self, settings: Dict) -> bool:
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
        Retorna configurações padrão completas.
        
        Returns:
            Dict com todas as configurações padrão
        """
        return {
            'window': {
                'position': [100, 100],
                'size': [1200, 700],
                'maximized': False
            },
            'layout': {
                'column_widths': [70, 350, 100, 200],  # posição, música, estrelas, tags
                'splitter_position': 500,
                'tags_panel_expanded': False
            }
        }
    
    def get_default_window_settings(self) -> Dict:
        """
        Retorna configurações padrão apenas da janela.
        
        Returns:
            Dict com configurações padrão da janela
        """
        return self.get_default_settings()['window']
    
    def get_default_layout_settings(self) -> Dict:
        """
        Retorna configurações padrão apenas do layout.
        
        Returns:
            Dict com configurações padrão do layout
        """
        return self.get_default_settings()['layout']
