import wx
import os
import subprocess
import platform
import shutil
import tempfile
import time
from controllers.music_controller import MusicController
from utils.window_settings import AppSettings


class MusicApp(wx.Frame):
    def __init__(self, music_controller: MusicController):
        # Inicializar gerenciador de configurações da aplicação
        self.app_settings = AppSettings()
        
        # Carregar configurações salvas ou usar padrão
        saved_window_settings = self.app_settings.load_window_settings()
        if saved_window_settings:
            size = tuple(saved_window_settings['size'])
            pos = tuple(saved_window_settings['position'])
        else:
            size = (1200, 700)
            pos = (100, 100)
        
        super().__init__(parent=None, title='RankMyMP3', size=size, pos=pos)

        self.controller = music_controller

        # Aplicar configurações da janela (incluindo maximização)
        if saved_window_settings:
            self.app_settings.apply_window_settings(self, saved_window_settings)

        # Criar o painel principal
        self.panel = wx.Panel(self)

        # Criar o layout principal (divisão horizontal)
        self.main_splitter = wx.SplitterWindow(self.panel)

        # Painel esquerdo (árvore de análise)
        self.left_panel = wx.Panel(self.main_splitter)
        
        # Substituir ListCtrl por TreeCtrl para estrutura hierárquica
        self.analysis_tree = wx.TreeCtrl(
            self.left_panel,
            style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_MULTIPLE
        )

        # Painel direito (ranking)
        self.right_panel = wx.Panel(self.main_splitter)

        # Configurar cores personalizadas para melhor legibilidade
        self._setup_list_colors()

        # Área de comparação (sempre visível, mas compacta)
        self.comparison_panel = wx.Panel(self.panel)

        # Variáveis para manter estado de expansão da árvore
        self.tree_expanded_folders = set()
        self.tree_expanded_sections = set()

        # Timer para reaplicar cores de seleção (temporariamente desabilitado)
        # self.color_timer = wx.Timer(self)
        # self.Bind(wx.EVT_TIMER, self.on_color_timer, self.color_timer)
        # self.color_timer.Start(500)  # Reaplicar a cada 500ms

        # Configurar layouts
        self._setup_menu()
        self._setup_layouts()
        self._setup_comparison_panel()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_tree_events()
        self._setup_window_events()

        # Atualizar as listas
        self.update_analysis_tree()
        self.update_ranking_list()
        
        # Inicializar checkboxes de tags
        self.populate_tags_checkboxes()

        # Aplicar configurações de layout salvas
        self._apply_saved_layout_settings()
        
        # Garantir que o botão tenha o estado correto após aplicar configurações
        wx.CallAfter(self._ensure_button_state)

        # Iniciar primeira comparação automaticamente
        wx.CallAfter(self.start_auto_comparison)

        self.Centre()
        self.Show()

    def _setup_list_colors(self):
        """Configura cores personalizadas para melhor legibilidade das listas."""
        # Detectar tema do sistema uma vez e cachear
        self.is_dark_theme = self._detect_dark_theme()
        
        # Usar cores do sistema quando possível para melhor integração
        try:
            system_highlight_bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
            system_highlight_text = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        except:
            # Fallback se não conseguir obter cores do sistema
            system_highlight_bg = wx.Colour(0, 120, 215)
            system_highlight_text = wx.Colour(255, 255, 255)
        
        # Configurar ranking_list e analysis_tree (usar cores 100% padrão do sistema)
        # Não modificar cores para manter aparência nativa

    def _detect_dark_theme(self):
        """Detecta se o sistema está usando tema escuro."""
        try:
            # Método 1: Verificar cor de fundo padrão do sistema
            system_bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            # Se a cor de fundo é escura (soma RGB baixa), provavelmente é tema escuro
            brightness = system_bg.Red() + system_bg.Green() + system_bg.Blue()
            if brightness < 384:  # 128 * 3 = 384 (meio termo)
                return True
            
            # Método 2: Verificar cor do texto do sistema
            system_text = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
            text_brightness = system_text.Red() + system_text.Green() + system_text.Blue()
            # Se o texto é claro, provavelmente é tema escuro
            if text_brightness > 384:
                return True
                
            return False
        except:
            # Se falhar na detecção, assumir tema claro como padrão
            return False

    def refresh_theme(self):
        """Força a atualização do tema da interface."""
        # Re-detectar tema
        self._setup_list_colors()
        self._apply_theme_to_panels()
        # Atualizar listas
        self.update_ranking_list()
        self.update_analysis_tree()
        # Forçar refresh visual
        self.Refresh()

    def _setup_menu(self):
        """Configura o menu da aplicação."""
        menubar = wx.MenuBar()
        
        # Menu Arquivo
        file_menu = wx.Menu()
        view_folders_item = file_menu.Append(wx.ID_ANY, "Ver Pastas\tCtrl+F", "Visualizar pastas adicionadas")
        clear_folders_item = file_menu.Append(wx.ID_ANY, "Limpar Pastas\tCtrl+Shift+F", "Remover todas as pastas")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "Sair\tCtrl+Q", "Sair da aplicação")
        
        menubar.Append(file_menu, "&Arquivo")
        self.SetMenuBar(menubar)
        
        # Bind eventos do menu
        self.Bind(wx.EVT_MENU, self.on_view_folders, view_folders_item)
        self.Bind(wx.EVT_MENU, self.on_clear_folders, clear_folders_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

    def _setup_layouts(self):
        """Configura os layouts da interface."""
        # Layout principal
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Layout do splitter
        self.main_splitter.SplitVertically(self.left_panel, self.right_panel)
        self.main_splitter.SetMinimumPaneSize(500)

        # Layout do painel esquerdo (árvore de análise)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self.left_panel, label="🎵 Em Análise:"), 0, wx.ALL, 5)
        
        # Adicionar filtro de texto para músicas em análise
        self._setup_analysis_filter()
        left_sizer.Add(self.analysis_filter_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        left_sizer.Add(self.analysis_tree, 1, wx.EXPAND | wx.ALL, 5)
        self.left_panel.SetSizer(left_sizer)

        # Layout do painel direito com splitter para redimensionar área de filtros/tags
        self.right_splitter = wx.SplitterWindow(self.right_panel, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.right_splitter.SetMinimumPaneSize(50)  # Tamanho mínimo para cada painel
        
        # Painel superior: título + filtros + tags (redimensionável)
        self.right_top_panel = wx.Panel(self.right_splitter)
        
        # Painel inferior: lista de ranking
        self.right_bottom_panel = wx.Panel(self.right_splitter)
        
        # === CONFIGURAR PAINEL SUPERIOR (FILTROS + TAGS) ===
        right_top_sizer = wx.BoxSizer(wx.VERTICAL)
        right_top_sizer.Add(wx.StaticText(self.right_top_panel, label="🏆 Ranking Atual:"), 0, wx.ALL, 5)
        
        # Adicionar filtros básicos
        self._setup_filter_panel()
        right_top_sizer.Add(self.filter_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Área de tags redimensionável (sempre visível)
        self._setup_tags_resizable_panel()
        right_top_sizer.Add(self.tags_resizable_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        self.right_top_panel.SetSizer(right_top_sizer)
        
        # === CONFIGURAR PAINEL INFERIOR (LISTA) ===
        # Criar ranking_list no painel inferior
        # === CONFIGURAR PAINEL INFERIOR (LISTA) ===
        # Criar ranking_list no painel inferior
        self.ranking_list = wx.ListCtrl(
            self.right_bottom_panel,
            style=wx.LC_REPORT  # Voltando com múltipla seleção
        )
        self.ranking_list.InsertColumn(0, "Posição")
        self.ranking_list.InsertColumn(1, "Música")
        self.ranking_list.InsertColumn(2, "Estrelas")
        self.ranking_list.InsertColumn(3, "Tags")
        self.ranking_list.SetColumnWidth(0, 70)
        self.ranking_list.SetColumnWidth(1, 350)
        self.ranking_list.SetColumnWidth(2, 100)
        self.ranking_list.SetColumnWidth(3, 200)
        
        right_bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        right_bottom_sizer.Add(self.ranking_list, 1, wx.EXPAND | wx.ALL, 5)
        self.right_bottom_panel.SetSizer(right_bottom_sizer)
        
        # Configurar splitter direito (começando com painel de tags oculto)
        self.right_splitter.SplitHorizontally(self.right_top_panel, self.right_bottom_panel, 80)
        
        # Layout do painel direito principal
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer.Add(self.right_splitter, 1, wx.EXPAND)
        self.right_panel.SetSizer(right_sizer)

        # Adicionar splitter e painel de comparação ao layout principal
        main_sizer.Add(self.main_splitter, 1, wx.EXPAND)
        main_sizer.Add(self.comparison_panel, 0, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

    def _setup_filter_panel(self):
        """Configura o painel de filtros para estrelas e tags."""
        self.filter_panel = wx.Panel(self.right_top_panel)
        
        # Layout vertical principal para filtros
        main_filter_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === LINHA 1: Filtros básicos (horizontal) ===
        basic_filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Filtro por estrelas
        basic_filter_sizer.Add(wx.StaticText(self.filter_panel, label="⭐ Estrelas:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        self.stars_filter = wx.Choice(self.filter_panel, choices=[
            "Todas", "⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"
        ])
        self.stars_filter.SetSelection(0)  # "Todas" por padrão
        basic_filter_sizer.Add(self.stars_filter, 0, wx.ALL, 5)
        
        # Espaçador
        basic_filter_sizer.Add(wx.StaticLine(self.filter_panel, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 5)
        
        # Botão para expandir/recolher filtro de tags
        self.expand_tags_btn = wx.Button(self.filter_panel, label="🔽 Filtrar por Tags")
        self.expand_tags_btn.SetMinSize((150, -1))
        basic_filter_sizer.Add(self.expand_tags_btn, 0, wx.ALL, 5)
        
        # Contador de filtros ativos (quando recolhido)
        self.filter_summary_label = wx.StaticText(self.filter_panel, label="")
        basic_filter_sizer.Add(self.filter_summary_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        # Botão limpar filtros
        self.clear_filters_btn = wx.Button(self.filter_panel, label="❌ Limpar")
        self.clear_filters_btn.SetMinSize((100, -1))
        basic_filter_sizer.Add(self.clear_filters_btn, 0, wx.ALL, 5)
        
        main_filter_sizer.Add(basic_filter_sizer, 0, wx.EXPAND)
        
        self.filter_panel.SetSizer(main_filter_sizer)
        
        # Bind eventos dos filtros básicos
        self.stars_filter.Bind(wx.EVT_CHOICE, self.on_filter_changed)
        self.clear_filters_btn.Bind(wx.EVT_BUTTON, self.on_clear_filters)
        self.expand_tags_btn.Bind(wx.EVT_BUTTON, self.on_toggle_tags_panel)

    def _setup_tags_resizable_panel(self):
        """Configura o painel de tags redimensionável."""
        # Criar o painel de tags dentro do painel superior
        self.tags_resizable_panel = wx.Panel(self.right_top_panel)
        
        # Layout para o painel de tags
        tags_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Cabeçalho do painel de tags
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer.Add(wx.StaticText(self.tags_resizable_panel, label="🏷️ Filtrar por Tags (AND - música deve ter TODAS):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        # Botão de controle
        self.clear_all_tags_btn = wx.Button(self.tags_resizable_panel, label="❌ Nenhuma", size=(120, -1))
        header_sizer.Add(self.clear_all_tags_btn, 0, wx.ALL, 3)
        
        # Contador de músicas filtradas
        self.filtered_count_label = wx.StaticText(self.tags_resizable_panel, label="")
        header_sizer.Add(self.filtered_count_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        tags_sizer.Add(header_sizer, 0, wx.EXPAND)
        
        # Painel scrollável para checkboxes das tags (agora redimensionável!)
        self.tags_scroll_panel = wx.ScrolledWindow(self.tags_resizable_panel, style=wx.BORDER_SUNKEN)
        self.tags_scroll_panel.SetScrollRate(5, 5)
        # Removido SetMinSize e SetMaxSize para permitir redimensionamento livre
        
        # Sizer para os checkboxes em colunas (será populado dinamicamente)
        # Começar com 3 colunas, será ajustado dinamicamente baseado no número de tags
        self.tags_checkboxes_sizer = wx.FlexGridSizer(0, 3, 5, 10)
        self.tags_scroll_panel.SetSizer(self.tags_checkboxes_sizer)
        
        tags_sizer.Add(self.tags_scroll_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        self.tags_resizable_panel.SetSizer(tags_sizer)
        
        # Inicializar variáveis
        self.tag_checkboxes = []
        self.tags_expanded = False  # Começar oculto
        self._saved_tags_splitter_pos = 200  # Posição padrão do splitter
        
        # Inicialmente ocultar o painel
        self.tags_resizable_panel.Hide()
        
        # Bind eventos dos controles de tags
        self.clear_all_tags_btn.Bind(wx.EVT_BUTTON, self.on_clear_all_tags)
        
        # Bind evento do splitter para salvar posição
        self.right_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_tags_splitter_move)

    def _setup_analysis_filter(self):
        """Configura o filtro de texto para músicas em análise."""
        self.analysis_filter_panel = wx.Panel(self.left_panel)
        
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Label e campo de texto
        filter_sizer.Add(wx.StaticText(self.analysis_filter_panel, label="🔍"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 3)
        
        self.analysis_filter_text = wx.TextCtrl(self.analysis_filter_panel, style=wx.TE_PROCESS_ENTER)
        self.analysis_filter_text.SetHint("Filtrar por nome da música...")
        filter_sizer.Add(self.analysis_filter_text, 1, wx.EXPAND | wx.ALL, 3)
        
        # Botão para limpar filtro
        self.clear_analysis_filter_btn = wx.Button(self.analysis_filter_panel, label="❌ Limpar", size=(100, -1))
        filter_sizer.Add(self.clear_analysis_filter_btn, 0, wx.ALL, 3)
        
        self.analysis_filter_panel.SetSizer(filter_sizer)
        
        # Inicializar variável de filtro
        self.analysis_filter_active = ""
        
        # Bind eventos
        self.analysis_filter_text.Bind(wx.EVT_TEXT, self.on_analysis_filter_changed)
        self.analysis_filter_text.Bind(wx.EVT_TEXT_ENTER, self.on_analysis_filter_changed)
        self.analysis_filter_text.Bind(wx.EVT_KILL_FOCUS, self.on_analysis_filter_changed)
        self.clear_analysis_filter_btn.Bind(wx.EVT_BUTTON, self.on_clear_analysis_filter)

    def _setup_comparison_panel(self):
        """Configura o painel de comparação - sempre visível e compacto."""
        # Definir um tamanho fixo menor para o painel de comparação
        self.comparison_panel.SetMinSize((900, 180))  # Mais compacto
        
        comparison_sizer = wx.BoxSizer(wx.VERTICAL)

        # Título da comparação mais compacto
        self.comparison_title = wx.StaticText(
            self.comparison_panel,
            label="🆚 Comparação Ativa",
            style=wx.ALIGN_CENTER_HORIZONTAL
        )
        title_font = self.comparison_title.GetFont()
        title_font.SetPointSize(12)  # Menor
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.comparison_title.SetFont(title_font)
        
        comparison_sizer.Add(self.comparison_title, 0, wx.EXPAND | wx.ALL, 5)

        # Área das músicas sendo comparadas - mais compacta
        songs_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Música A
        self.song_a_panel = wx.Panel(self.comparison_panel)
        song_a_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Nome da música A compacto
        self.song_a_name = wx.StaticText(self.song_a_panel, label="", style=wx.ALIGN_CENTER)
        font = self.song_a_name.GetFont()
        font.SetPointSize(10)  # Fonte menor para compacto
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.song_a_name.SetFont(font)
        
        song_a_sizer.Add(self.song_a_name, 0, wx.EXPAND | wx.ALL, 5)
        
        # Botões da música A mais compactos
        buttons_panel_a = wx.Panel(self.song_a_panel)
        song_a_buttons = wx.BoxSizer(wx.HORIZONTAL)  # Horizontal para compactar
        
        self.song_a_button = wx.Button(buttons_panel_a, label="Prefiro")
        self.song_a_button.SetMinSize((80, 30))  # Botões menores
        self.skip_a_button = wx.Button(buttons_panel_a, label="Ignorar")
        self.skip_a_button.SetMinSize((80, 30))
        
        song_a_buttons.Add(self.song_a_button, 0, wx.ALL, 2)
        song_a_buttons.Add(self.skip_a_button, 0, wx.ALL, 2)
        buttons_panel_a.SetSizer(song_a_buttons)
        
        song_a_sizer.Add(buttons_panel_a, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.song_a_panel.SetSizer(song_a_sizer)

        # VS simplificado
        vs_panel = wx.Panel(self.comparison_panel)
        vs_panel.SetMinSize((60, 60))  # Ainda menor
        vs_sizer = wx.BoxSizer(wx.VERTICAL)
        
        vs_label = wx.StaticText(vs_panel, label="VS", style=wx.ALIGN_CENTER_HORIZONTAL)
        font = vs_label.GetFont()
        font.SetPointSize(10)  # Fonte menor
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        vs_label.SetFont(font)
        
        vs_sizer.AddStretchSpacer(1)
        vs_sizer.Add(vs_label, 0, wx.CENTER)
        vs_sizer.AddStretchSpacer(1)
        vs_panel.SetSizer(vs_sizer)

        # Música B - espelho da A
        self.song_b_panel = wx.Panel(self.comparison_panel)
        song_b_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Nome da música B compacto
        self.song_b_name = wx.StaticText(self.song_b_panel, label="", style=wx.ALIGN_CENTER)
        font = self.song_b_name.GetFont()
        font.SetPointSize(10)  # Fonte menor para compacto
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.song_b_name.SetFont(font)
        
        song_b_sizer.Add(self.song_b_name, 0, wx.EXPAND | wx.ALL, 5)
        
        # Botões da música B mais compactos
        buttons_panel_b = wx.Panel(self.song_b_panel)
        song_b_buttons = wx.BoxSizer(wx.HORIZONTAL)  # Horizontal para compactar
        
        self.song_b_button = wx.Button(buttons_panel_b, label="Prefiro")
        self.song_b_button.SetMinSize((80, 30))  # Botões menores
        self.skip_b_button = wx.Button(buttons_panel_b, label="Ignorar")
        self.skip_b_button.SetMinSize((80, 30))
        
        song_b_buttons.Add(self.song_b_button, 0, wx.ALL, 2)
        song_b_buttons.Add(self.skip_b_button, 0, wx.ALL, 2)
        buttons_panel_b.SetSizer(song_b_buttons)
        
        song_b_sizer.Add(buttons_panel_b, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.song_b_panel.SetSizer(song_b_sizer)

        # Montar o layout horizontal das músicas
        songs_sizer.Add(self.song_a_panel, 1, wx.EXPAND | wx.ALL, 10)
        songs_sizer.Add(vs_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        songs_sizer.Add(self.song_b_panel, 1, wx.EXPAND | wx.ALL, 10)

        # Adicionar ao sizer principal
        comparison_sizer.Add(songs_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.comparison_panel.SetSizer(comparison_sizer)

        # Bind eventos dos botões
        self.song_a_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_comparison_choice(0))
        self.song_b_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_comparison_choice(1))
        self.skip_a_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_skip_music(0))
        self.skip_b_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_skip_music(1))

    def _setup_toolbar(self):
        """Configura a barra de ferramentas."""
        toolbar = self.CreateToolBar()

        # Botão de adicionar pasta
        add_folder_tool = toolbar.AddTool(
            wx.ID_ANY,
            "Adicionar Pasta",
            wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_TOOLBAR),
            "Adicionar pasta de músicas"
        )

        toolbar.Realize()

        # Bind eventos
        self.Bind(wx.EVT_TOOL, self.on_add_folder, add_folder_tool)

    def _setup_statusbar(self):
        """Configura a barra de status."""
        self.statusbar = self.CreateStatusBar(3)  # 3 seções: músicas, classificadas, pastas
        self.update_status()

    def _save_tree_expansion_state(self):
        """Salva o estado atual de expansão da árvore nas variáveis de instância."""
        root = self.analysis_tree.GetRootItem()
        if root.IsOk():
            # Verificar seções principais (Em Análise, Ignoradas)
            main_section = self.analysis_tree.GetFirstChild(root)[0]
            while main_section.IsOk():
                if self.analysis_tree.IsExpanded(main_section):
                    section_text = self.analysis_tree.GetItemText(main_section)
                    if section_text.startswith("❌ Ignoradas"):
                        self.tree_expanded_sections.add("Ignoradas")
                    elif section_text.startswith("🎵 Em Análise"):
                        self.tree_expanded_sections.add("Em Análise")
                        
                        # Verificar pastas dentro da seção "Em Análise"
                        folder_item = self.analysis_tree.GetFirstChild(main_section)[0]
                        while folder_item.IsOk():
                            if self.analysis_tree.IsExpanded(folder_item):
                                folder_text = self.analysis_tree.GetItemText(folder_item)
                                # Extrair apenas o nome da pasta (remover emoji e contagem)
                                if folder_text.startswith("📁 "):
                                    folder_name = folder_text[2:].split(" (")[0]  # Remove "📁 " e tudo após " ("
                                    self.tree_expanded_folders.add(folder_name)
                            folder_item = self.analysis_tree.GetNextSibling(folder_item)
                else:
                    # Se não está expandida, remover do conjunto
                    section_text = self.analysis_tree.GetItemText(main_section)
                    if section_text.startswith("❌ Ignoradas"):
                        self.tree_expanded_sections.discard("Ignoradas")
                    elif section_text.startswith("🎵 Em Análise"):
                        self.tree_expanded_sections.discard("Em Análise")
                
                main_section = self.analysis_tree.GetNextSibling(main_section)

    def update_analysis_tree(self):
        """Atualiza a árvore de análise com músicas organizadas por pasta."""
        # Salvar estado de expansão atual nas variáveis de instância
        self._save_tree_expansion_state()
        
        # Reconstruir árvore
        self.analysis_tree.DeleteAllItems()
        
        # Criar raiz invisível
        root = self.analysis_tree.AddRoot("Root")
        
        # Buscar músicas não classificadas organizadas por pasta
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        # Obter filtro de texto atual
        filter_text = getattr(self, 'analysis_filter_active', '').lower().strip()
        
        # Adicionar seções principais
        analysis_root = self.analysis_tree.AppendItem(root, "🎵 Em Análise")
        self.analysis_tree.SetItemBold(analysis_root, True)
        
        # Adicionar pastas e músicas
        for folder_path, musics in folders_dict.items():
            # Filtrar músicas se há filtro ativo
            if filter_text:
                musics = [m for m in musics if filter_text in os.path.basename(m['path']).lower()]
            
            # Só adicionar pasta se tem músicas (após filtro)
            if musics:
                folder_name = os.path.basename(folder_path) or folder_path
                folder_display_name = f"📁 {folder_name} ({len(musics)} músicas)"
                folder_item = self.analysis_tree.AppendItem(analysis_root, folder_display_name)
                
                # Adicionar músicas da pasta
                for music in musics:
                    music_name = os.path.basename(music['path'])
                    music_item = self.analysis_tree.AppendItem(folder_item, f"🎵 {music_name}")
                    # Guardar o ID da música no item
                    self.analysis_tree.SetItemData(music_item, music['id'])
                
                # Restaurar estado de expansão usando apenas o nome da pasta
                if folder_name in self.tree_expanded_folders:
                    self.analysis_tree.Expand(folder_item)
        
        # Adicionar seção de ignoradas
        ignored_musics = self.controller.get_ignored_musics()
        ignored_root = None
        if ignored_musics:
            # Filtrar ignoradas também se há filtro ativo
            if filter_text:
                ignored_musics = [m for m in ignored_musics if filter_text in os.path.basename(m['path']).lower()]
            
            if ignored_musics:  # Só mostrar se há músicas ignoradas (após filtro)
                ignored_root = self.analysis_tree.AppendItem(root, f"❌ Ignoradas ({len(ignored_musics)})")
                self.analysis_tree.SetItemBold(ignored_root, True)
                
                for music in ignored_musics:
                    music_name = os.path.basename(music['path'])
                    music_item = self.analysis_tree.AppendItem(ignored_root, f"❌ {music_name}")
                    self.analysis_tree.SetItemData(music_item, music['id'])
        
        # Restaurar estado de expansão das seções
        if "Em Análise" in self.tree_expanded_sections:
            self.analysis_tree.Expand(analysis_root)
        else:
            # Por padrão, expandir "Em Análise" se não havia estado anterior
            if not self.tree_expanded_sections:  # Primeira vez
                self.analysis_tree.Expand(analysis_root)
                self.tree_expanded_sections.add("Em Análise")
        
        if ignored_root and "Ignoradas" in self.tree_expanded_sections:
            self.analysis_tree.Expand(ignored_root)

    def update_ranking_list(self):
        """Atualiza a lista de ranking com filtros aplicados."""
        self.ranking_list.DeleteAllItems()
        
        # Verificar se há filtros ativos
        has_star_filter = hasattr(self, 'stars_filter') and self.stars_filter.GetSelection() > 0
        has_tag_filter = len(self.get_selected_tags()) > 0
        
        if has_star_filter or has_tag_filter:
            # Usar músicas filtradas
            filtered_musics = self.get_filtered_musics()
            musics_to_show = filtered_musics
        else:
            # Mostrar todas as músicas classificadas
            ranked_musics = self.controller.get_classified_musics_topological()
            musics_to_show = [music for music in ranked_musics if music['stars'] is not None and music['stars'] > 0]
        
        # Adicionar músicas à lista
        for position, music in enumerate(musics_to_show, 1):
            if music['stars'] is not None and music['stars'] > 0:  # Apenas músicas efetivamente classificadas
                index = self.ranking_list.GetItemCount()
                self.ranking_list.InsertItem(index, str(position))
                self.ranking_list.SetItem(index, 1, os.path.basename(music['path']))
                
                # Usar estrelas coloridas como no filtro
                stars_display = self._get_colored_stars(music['stars'])
                self.ranking_list.SetItem(index, 2, stars_display)
                
                # Adicionar tags na coluna 3
                tags = self.controller.music_model.get_music_tags(music['id'])
                tags_text = ", ".join(tags) if tags else ""
                self.ranking_list.SetItem(index, 3, tags_text)
                
                # Usar cores padrão do sistema - sem aplicação manual de cores

    def _get_colored_stars(self, stars_count):
        """Retorna representação visual das estrelas usando emojis coloridos."""
        if stars_count is None or stars_count <= 0:
            return ""
        
        # Usar apenas estrelas preenchidas para melhor alinhamento
        filled_stars = "⭐" * stars_count
        return filled_stars

    def update_lists(self):
        """Atualiza todas as listas - método de compatibilidade."""
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()

    def update_status(self):
        """Atualiza a barra de status."""
        total_musics = self.controller.get_total_musics_count()
        rated_musics = self.controller.get_rated_musics_count()
        folder_count = self.controller.get_folder_count()
        self.statusbar.SetStatusText(f"Total de músicas: {total_musics}", 0)
        self.statusbar.SetStatusText(f"Classificadas: {rated_musics}", 1)
        self.statusbar.SetStatusText(f"Pastas: {folder_count}", 2)

    def _setup_tree_events(self):
        """Configura eventos da árvore."""
        # Clique direito na árvore para menu contextual
        self.analysis_tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_tree_right_click)
        
        # Eventos de seleção da árvore para forçar fonte legível
        self.analysis_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_sel_changed)
        
        # Clique direito na lista de ranking para menu contextual
        self.ranking_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_ranking_right_click)
        
        # Apenas evento para forçar fonte legível durante seleção
        self.ranking_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_ranking_item_selected)
        self.ranking_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_ranking_item_deselected)

    def on_ranking_item_selected(self, event):
        """Força apenas cor de fonte legível quando selecionado, mantém fundo nativo."""
        item_index = event.GetIndex()
        
        # Deixar o sistema aplicar suas cores primeiro
        event.Skip()
        
        # Depois forçar apenas cor de fonte preta para legibilidade
        wx.CallAfter(self._force_readable_text, item_index)

    def _force_readable_text(self, item_index):
        """Força cor de texto contrastante para garantir legibilidade na seleção."""
        try:
            # Se tema escuro, usar branco; se claro, usar preto
            if self.is_dark_theme:
                text_color = wx.Colour(255, 255, 255)  # Branco para tema escuro
            else:
                text_color = wx.Colour(0, 0, 0)        # Preto para tema claro
            
            # Aplicar cor múltiplas vezes para garantir que seja aplicada
            for _ in range(3):
                self.ranking_list.SetItemTextColour(item_index, text_color)
                self.ranking_list.RefreshItem(item_index)
                wx.SafeYield()
        except:
            pass

    def on_ranking_item_deselected(self, event):
        """Remove cor de fonte forçada quando desselecionado."""
        item_index = event.GetIndex()
        
        # Usar cor de texto padrão do sistema explicitamente
        default_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        self.ranking_list.SetItemTextColour(item_index, default_color)
        self.ranking_list.RefreshItem(item_index)
        event.Skip()

    def on_tree_sel_changed(self, event):
        """Gerencia seleção da árvore para aplicar fonte legível."""
        # Restaurar cor padrão do item anteriormente selecionado se disponível
        try:
            old_item = event.GetOldItem()
            if old_item and old_item.IsOk():
                default_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
                self.analysis_tree.SetItemTextColour(old_item, default_color)
        except AttributeError:
            # GetOldItem pode não estar disponível em todas as versões
            pass
        
        # Aplicar cor legível ao novo item selecionado
        new_item = event.GetItem()
        if new_item and new_item.IsOk():
            # Deixar o sistema aplicar suas cores primeiro
            event.Skip()
            
            # Depois forçar apenas cor de fonte para legibilidade
            wx.CallAfter(self._force_readable_text_tree, new_item)
        else:
            event.Skip()

    def _force_readable_text_tree(self, tree_item):
        """Força cor de texto contrastante na árvore para garantir legibilidade na seleção."""
        try:
            # Se tema escuro, usar branco; se claro, usar preto
            if self.is_dark_theme:
                text_color = wx.Colour(255, 255, 255)  # Branco para tema escuro
            else:
                text_color = wx.Colour(0, 0, 0)        # Preto para tema claro
            
            # Aplicar cor múltiplas vezes para garantir que seja aplicada
            for _ in range(3):
                self.analysis_tree.SetItemTextColour(tree_item, text_color)
                self.analysis_tree.Refresh()
                wx.SafeYield()
        except:
            pass

    def _setup_window_events(self):
        """Configura eventos da janela."""
        # Evento de fechamento para salvar configurações
        self.Bind(wx.EVT_CLOSE, self.on_window_close)
        
        # Eventos para salvar configurações de layout em tempo real
        self.ranking_list.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_column_resize)
        self.main_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_splitter_move)

    def _apply_saved_layout_settings(self):
        """Aplica configurações de layout salvas."""
        try:
            layout_settings = self.app_settings.load_layout_settings()
            if layout_settings:
                # Aplicar configurações ao ranking_list e main_splitter
                self.app_settings.apply_layout_settings(
                    self.ranking_list, 
                    self.main_splitter, 
                    layout_settings
                )
                
                # Salvar posição do splitter de tags para uso posterior
                self._saved_tags_splitter_pos = layout_settings.get('tags_splitter_position', 200)
                
                # Aplicar estado do painel de tags - SEMPRE começar colapsado na inicialização
                # Ignorar configuração salva e sempre começar colapsado
                self.tags_expanded = False
                self.expand_tags_btn.SetLabel("🔽 Filtrar por Tags")
        except Exception as e:
            print(f"Erro ao aplicar configurações de layout: {e}")
    
    def _restore_tags_panel_state(self):
        """Restaura o estado expandido do painel de tags."""
        try:
            # Expandir painel de tags com posição salva
            self.tags_expanded = False  # Começar como falso para que o toggle funcione
            self.tags_resizable_panel.Show()
            self.tags_expanded = True
            self.expand_tags_btn.SetLabel("🔼 Ocultar Tags")
            self.right_splitter.SetSashPosition(self._saved_tags_splitter_pos)
            self.populate_tags_checkboxes()
            self.update_filter_summary()
            self.right_top_panel.Layout()
        except Exception as e:
            print(f"Erro ao restaurar estado do painel de tags: {e}")

    def _ensure_button_state(self):
        """Garante que o botão tenha o estado correto após todas as inicializações."""
        # Sempre forçar colapsado na inicialização
        self.tags_expanded = False
        self.expand_tags_btn.SetLabel("🔽 Filtrar por Tags")

    def start_auto_comparison(self):
        """Inicia comparação automática - chamado na inicialização."""
        # Verificar se há músicas para classificar antes de tentar iniciar
        unrated_count = self.controller.get_unrated_musics_count()
        if unrated_count > 0:
            self.start_comparison()
        else:
            # Atualizar interface para mostrar que não há músicas
            self.comparison_title.SetLabel("🎵 Adicione músicas para começar a classificar")
            self.song_a_name.SetLabel("")
            self.song_b_name.SetLabel("")
            self.song_a_button.Enable(False)
            self.song_b_button.Enable(False)
            self.skip_a_button.Enable(False)
            self.skip_b_button.Enable(False)

    def on_tree_right_click(self, event):
        """Handle right-click no item da árvore."""
        item = event.GetItem()
        if not item.IsOk():
            return
        
        # Verificar seleções múltiplas
        selected_items = self.analysis_tree.GetSelections()
        if not selected_items:
            selected_items = [item]
        
        # Filtrar apenas itens que são músicas (têm ID)
        music_items = []
        for sel_item in selected_items:
            music_id = self.analysis_tree.GetItemData(sel_item)
            if music_id:
                music_items.append((sel_item, music_id))
        
        if not music_items:
            return
        
        # Criar menu contextual
        menu = wx.Menu()
        
        if len(music_items) == 1:
            # Menu para uma música
            item_text = self.analysis_tree.GetItemText(music_items[0][0])
            music_id = music_items[0][1]
            
            # Obter informações da música para mostrar o caminho
            music_details = self.controller.music_model.get_music_details(music_id)
            if music_details:
                music_path = music_details['path']
                
                # Opções de caminho
                show_path_item = menu.Append(wx.ID_ANY, "📁 Mostrar Caminho")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_show_music_path(music_path), show_path_item)
                
                open_folder_item = menu.Append(wx.ID_ANY, "🗂️ Abrir Pasta")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_open_music_folder(music_path), open_folder_item)
                
                play_item = menu.Append(wx.ID_ANY, "🎵 Reproduzir Música")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_play_music(music_path), play_item)
                
                move_item = menu.Append(wx.ID_ANY, "📦 Mover para Pasta...")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_move_music_file(music_id), move_item)
                
                menu.AppendSeparator()
            
            if item_text.startswith("❌"):
                # Música ignorada - opção para restaurar
                restore_item = menu.Append(wx.ID_ANY, "Restaurar para Análise")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_restore_music(music_items[0][1]), restore_item)
            else:
                # Música em análise - opções para classificar e ignorar
                classify_item = menu.Append(wx.ID_ANY, "🎯 Classificar Esta Música Agora")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_force_classify_music(music_items[0][1]), classify_item)
                
                menu.AppendSeparator()
                
                ignore_item = menu.Append(wx.ID_ANY, "Ignorar Permanentemente")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_ignore_music_from_tree(music_items[0][1]), ignore_item)
        else:
            # Menu para múltiplas músicas
            # Verificar se todas são ignoradas ou em análise
            all_ignored = all(self.analysis_tree.GetItemText(item).startswith("❌") for item, _ in music_items)
            all_in_analysis = all(not self.analysis_tree.GetItemText(item).startswith("❌") for item, _ in music_items)
            
            if all_ignored:
                restore_item = menu.Append(wx.ID_ANY, f"Restaurar {len(music_items)} Músicas")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_restore_multiple_musics([music_id for _, music_id in music_items]), restore_item)
            elif all_in_analysis:
                ignore_item = menu.Append(wx.ID_ANY, f"Ignorar {len(music_items)} Músicas")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_ignore_multiple_musics([music_id for _, music_id in music_items]), ignore_item)
            else:
                # Mista - oferecer ambas opções
                ignore_analysis = [music_id for item, music_id in music_items if not self.analysis_tree.GetItemText(item).startswith("❌")]
                restore_ignored = [music_id for item, music_id in music_items if self.analysis_tree.GetItemText(item).startswith("❌")]
                
                if ignore_analysis:
                    ignore_item = menu.Append(wx.ID_ANY, f"Ignorar {len(ignore_analysis)} em Análise")
                    self.Bind(wx.EVT_MENU, lambda evt: self.on_ignore_multiple_musics(ignore_analysis), ignore_item)
                
                if restore_ignored:
                    restore_item = menu.Append(wx.ID_ANY, f"Restaurar {len(restore_ignored)} Ignoradas")
                    self.Bind(wx.EVT_MENU, lambda evt: self.on_restore_multiple_musics(restore_ignored), restore_item)
        
        # Mostrar menu
        self.PopupMenu(menu)
        menu.Destroy()

    def on_ignore_music_from_tree(self, music_id):
        """Ignora uma música selecionada da árvore."""
        # Verificar se esta música está em comparação ativa
        current_state = self.controller.get_comparison_state()
        music_in_active_comparison = False
        
        if current_state:
            unrated_id = current_state.get('unrated_music_id')
            compared_id = current_state.get('compared_music_id')
            
            if music_id == unrated_id or music_id == compared_id:
                music_in_active_comparison = True
                print(f"DEBUG: Música {music_id} está em comparação ativa - limpando estado")
        
        self.controller.skip_music(music_id)
        
        # Remover todas as comparações relacionadas a esta música
        self.controller.comparison_model.remove_comparisons_for_music(music_id)
        
        # Se estava em comparação ativa, limpar estado e ir para próxima
        if music_in_active_comparison:
            self.controller.comparison_state_model.clear_comparison_state()
            print(f"DEBUG: Estado de comparação limpo - procurando próxima")
        
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Se estava em comparação ativa, iniciar próxima automaticamente
        if music_in_active_comparison:
            wx.CallAfter(self.start_comparison)

    def on_ignore_multiple_musics(self, music_ids):
        """Ignora múltiplas músicas selecionadas."""
        # Verificar se alguma música está em comparação ativa
        current_state = self.controller.get_comparison_state()
        comparison_affected = False
        
        if current_state:
            unrated_id = current_state.get('unrated_music_id')
            compared_id = current_state.get('compared_music_id')
            
            if unrated_id in music_ids or compared_id in music_ids:
                comparison_affected = True
                print(f"DEBUG: Uma das músicas ignoradas estava em comparação ativa - limpando estado")
        
        for music_id in music_ids:
            self.controller.skip_music(music_id)
            # Remover todas as comparações relacionadas a esta música
            self.controller.comparison_model.remove_comparisons_for_music(music_id)
        
        # Se alguma música estava em comparação ativa, limpar estado
        if comparison_affected:
            self.controller.comparison_state_model.clear_comparison_state()
            print(f"DEBUG: Estado de comparação limpo após ignorar múltiplas músicas")
        
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Se comparação foi afetada, iniciar próxima automaticamente
        if comparison_affected:
            wx.CallAfter(self.start_comparison)

    def on_restore_music(self, music_id):
        """Restaura uma música ignorada de volta para análise."""
        # Restaurar música (setar stars = 0)
        self.controller.music_model.update_stars(music_id, 0)
        
        # Remover todas as comparações dessa música para evitar inconsistências
        self.controller.comparison_model.remove_comparisons_for_music(music_id)
        
        # Limpar estado de comparação para forçar nova busca
        self.controller.comparison_state_model.clear_comparison_state()
        
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Sempre iniciar comparações automaticamente após restaurar
        wx.CallAfter(self.start_comparison)

    def on_restore_multiple_musics(self, music_ids):
        """Restaura múltiplas músicas ignoradas de volta para análise."""
        for music_id in music_ids:
            # Restaurar música (setar stars = 0)
            self.controller.music_model.update_stars(music_id, 0)
            # Remover todas as comparações dessa música para evitar inconsistências
            self.controller.comparison_model.remove_comparisons_for_music(music_id)
        
        # Limpar estado de comparação para forçar nova busca
        self.controller.comparison_state_model.clear_comparison_state()
        
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Sempre iniciar comparações automaticamente após restaurar
        wx.CallAfter(self.start_comparison)

    def on_ranking_right_click(self, event):
        """Handle right-click na lista de ranking."""
        item_index = event.GetIndex()
        if item_index == -1:
            return
        
        # Verificar se há múltipla seleção
        selected_count = self.ranking_list.GetSelectedItemCount()
        is_multiple_selection = selected_count > 1
        
        # Buscar a música classificada correspondente ao índice clicado
        ranked_musics = self.controller.get_classified_musics_topological()
        classified_musics = [music for music in ranked_musics if music['stars'] is not None and music['stars'] > 0]
        
        if item_index >= len(classified_musics):
            return
        
        selected_music = classified_musics[item_index]
        music_id = selected_music['id']
        music_name = os.path.basename(selected_music['path'])
        
        # Criar menu contextual
        menu = wx.Menu()
        
        if is_multiple_selection:
            # Menu para múltipla seleção - apenas ações em lote
            selection_item = menu.Append(wx.ID_ANY, f"🔢 {selected_count} músicas selecionadas")
            selection_item.Enable(False)  # Item informativo, não clicável
            menu.AppendSeparator()
            
            # Ações de arquivo que fazem sentido para múltipla seleção
            play_multiple_item = menu.Append(wx.ID_ANY, f"🎵 Reproduzir Músicas")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_create_and_play_playlist_simple(), play_multiple_item)
            
            export_playlist_item = menu.Append(wx.ID_ANY, f"💾 Exportar Playlist...")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_export_selected_playlist(), export_playlist_item)
            
            menu.AppendSeparator()
            
            copy_multiple_item = menu.Append(wx.ID_ANY, f"📋 Copiar {selected_count} para Pasta...")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_copy_multiple_music_files(), copy_multiple_item)
            
            move_multiple_item = menu.Append(wx.ID_ANY, f"📦 Mover {selected_count} para Pasta...")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_move_multiple_music_files(), move_multiple_item)
            
            menu.AppendSeparator()
            
            # Ações de classificação para múltipla seleção
            remove_item = menu.Append(wx.ID_ANY, f"🗑️ Remover {selected_count} da Classificação")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_remove_multiple_from_ranking(), remove_item)
            
            ignore_item = menu.Append(wx.ID_ANY, f"❌ Ignorar {selected_count} Permanentemente")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_ignore_multiple_from_ranking(), ignore_item)
            
        else:
            # Menu para seleção única - todas as opções disponíveis
            # Opção para gerenciar tags
            tags_item = menu.Append(wx.ID_ANY, f"🏷️ Gerenciar Tags")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_manage_tags(music_id, music_name), tags_item)
            
            menu.AppendSeparator()
            
            # Opções de arquivo (só para seleção única)
            show_path_item = menu.Append(wx.ID_ANY, f"📁 Mostrar Caminho")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_show_music_path(selected_music['path']), show_path_item)
            
            open_folder_item = menu.Append(wx.ID_ANY, f"🗂️ Abrir Pasta")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_open_music_folder(selected_music['path']), open_folder_item)
            
            play_item = menu.Append(wx.ID_ANY, f"🎵 Reproduzir Música")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_play_music(selected_music['path']), play_item)
            
            move_item = menu.Append(wx.ID_ANY, f"📦 Mover para Pasta...")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_move_music_file(music_id), move_item)
            
            menu.AppendSeparator()
            
            # Opções de classificação
            remove_item = menu.Append(wx.ID_ANY, f"🗑️ Remover da Classificação")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_remove_from_ranking(music_id), remove_item)
            
            ignore_item = menu.Append(wx.ID_ANY, f"❌ Ignorar Permanentemente")
            self.Bind(wx.EVT_MENU, lambda evt: self.on_ignore_from_ranking(music_id), ignore_item)
        
        # Mostrar menu
        self.PopupMenu(menu)
        menu.Destroy()

    def on_remove_from_ranking(self, music_id):
        """Remove uma música do ranking, voltando ela para análise."""
        # Zerar as estrelas da música (volta para análise)
        self.controller.music_model.update_stars(music_id, 0)
        
        # Remover todas as comparações relacionadas a esta música
        self.controller.comparison_model.remove_comparisons_for_music(music_id)
        
        # Atualizar interface
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Iniciar comparações automaticamente se não há comparação ativa
        current_state = self.controller.get_current_comparison_state()
        if not current_state:
            wx.CallAfter(self.start_comparison)

    def on_ignore_from_ranking(self, music_id):
        """Ignora uma música do ranking permanentemente."""
        # Verificar se esta música está em comparação ativa
        current_state = self.controller.get_comparison_state()
        music_in_active_comparison = False
        
        if current_state:
            unrated_id = current_state.get('unrated_music_id')
            compared_id = current_state.get('compared_music_id')
            
            if music_id == unrated_id or music_id == compared_id:
                music_in_active_comparison = True
                print(f"DEBUG: Música {music_id} ignorada do ranking estava em comparação ativa")
        
        # Marcar como ignorada (-1)
        self.controller.skip_music(music_id)
        
        # Remover todas as comparações relacionadas a esta música
        self.controller.comparison_model.remove_comparisons_for_music(music_id)
        
        # Se estava em comparação ativa, limpar estado
        if music_in_active_comparison:
            self.controller.comparison_state_model.clear_comparison_state()
            print(f"DEBUG: Estado de comparação limpo após ignorar do ranking")
        
        # Atualizar interface
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Se estava em comparação ativa, iniciar próxima automaticamente
        if music_in_active_comparison:
            wx.CallAfter(self.start_comparison)

    def start_comparison(self):
        """Inicia uma nova comparação automaticamente."""
        try:
            state = self.controller.get_next_comparison()
            
            if not state:
                # Não há mais músicas para comparar
                self.comparison_title.SetLabel("🎉 Todas as músicas foram classificadas!")
                self.song_a_name.SetLabel("")
                self.song_b_name.SetLabel("")
                # Desabilitar botões
                self.song_a_button.Enable(False)
                self.song_b_button.Enable(False)
                self.skip_a_button.Enable(False)
                self.skip_b_button.Enable(False)
                return

            # Buscar detalhes das músicas
            music_a_id = state['unrated_music_id']
            music_b_id = state['compared_music_id'] 
            
            music_a = self.controller.get_music_details(music_a_id)
            music_b = self.controller.get_music_details(music_b_id)
            
            if not music_a or not music_b:
                wx.MessageBox(
                    'Erro ao obter detalhes das músicas para comparação.',
                    'Erro',
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Atualizar interface de comparação
            music_a_name = os.path.basename(music_a['path'])
            music_b_name = os.path.basename(music_b['path'])
            
            self.comparison_title.SetLabel("🆚 Qual música você prefere?")
            self.song_a_name.SetLabel(music_a_name)
            self.song_b_name.SetLabel(music_b_name)
            
            # Habilitar botões de preferência
            self.song_a_button.Enable(True)
            self.song_b_button.Enable(True)
            
            # Mostrar botões "Ignorar" apenas se ambas as músicas não têm classificação
            music_a_unrated = music_a.get('stars', 0) == 0
            music_b_unrated = music_b.get('stars', 0) == 0
            
            self.skip_a_button.Show(music_a_unrated)
            self.skip_b_button.Show(music_b_unrated)
            
            # Habilitar botões "Ignorar" apenas para músicas não classificadas
            self.skip_a_button.Enable(music_a_unrated)
            self.skip_b_button.Enable(music_b_unrated)
            
            # Força atualização da interface
            self.comparison_panel.Layout()
            self.panel.Layout()
            
        except Exception as e:
            wx.MessageBox(
                f'Erro ao iniciar comparação: {str(e)}',
                'Erro',
                wx.OK | wx.ICON_ERROR
            )

    def on_remove_multiple_from_ranking(self):
        """Remove múltiplas músicas selecionadas do ranking."""
        # Obter IDs das músicas selecionadas
        selected_music_ids = self._get_selected_music_ids_from_ranking()
        
        if not selected_music_ids:
            return
        
        # Confirmar ação
        count = len(selected_music_ids)
        dlg = wx.MessageDialog(
            self,
            f"Tem certeza que deseja remover {count} música(s) da classificação?\n\nElas voltarão para análise.",
            "Confirmar Remoção",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if dlg.ShowModal() == wx.ID_YES:
            # Processar cada música selecionada
            for music_id in selected_music_ids:
                # Zerar as estrelas da música (volta para análise)
                self.controller.music_model.update_stars(music_id, 0)
                
                # Remover todas as comparações relacionadas a esta música
                self.controller.comparison_model.remove_comparisons_for_music(music_id)
            
            # Limpar estado de comparação se alguma música removida estava sendo comparada
            self.controller.comparison_state_model.clear_comparison_state()
            
            # Atualizar interface
            self.update_analysis_tree()
            self.update_ranking_list()
            self.update_status()
            
            wx.MessageBox(
                f"{count} música(s) removida(s) da classificação com sucesso!",
                "Remoção Concluída",
                wx.OK | wx.ICON_INFORMATION
            )
        
        dlg.Destroy()

    def on_ignore_multiple_from_ranking(self):
        """Ignora múltiplas músicas selecionadas permanentemente."""
        # Obter IDs das músicas selecionadas
        selected_music_ids = self._get_selected_music_ids_from_ranking()
        
        if not selected_music_ids:
            return
        
        # Confirmar ação
        count = len(selected_music_ids)
        dlg = wx.MessageDialog(
            self,
            f"Tem certeza que deseja IGNORAR PERMANENTEMENTE {count} música(s)?\n\nElas não aparecerão mais nas comparações.",
            "Confirmar Ignorar",
            wx.YES_NO | wx.ICON_WARNING
        )
        
        if dlg.ShowModal() == wx.ID_YES:
            # Processar cada música selecionada
            for music_id in selected_music_ids:
                # Marcar como ignorada (-1)
                self.controller.skip_music(music_id)
                
                # Remover todas as comparações relacionadas a esta música
                self.controller.comparison_model.remove_comparisons_for_music(music_id)
            
            # Limpar estado de comparação se alguma música ignorada estava sendo comparada
            self.controller.comparison_state_model.clear_comparison_state()
            
            # Atualizar interface
            self.update_analysis_tree()
            self.update_ranking_list()
            self.update_status()
            
            wx.MessageBox(
                f"{count} música(s) ignorada(s) permanentemente!",
                "Ignorar Concluído",
                wx.OK | wx.ICON_INFORMATION
            )
        
        dlg.Destroy()

    def _get_selected_music_ids_from_ranking(self):
        """Obtém os IDs das músicas selecionadas na lista de ranking."""
        selected_ids = []
        
        # Obter lista de músicas classificadas
        ranked_musics = self.controller.get_classified_musics_topological()
        classified_musics = [music for music in ranked_musics if music['stars'] is not None and music['stars'] > 0]
        
        # Iterar pelos itens selecionados
        item = self.ranking_list.GetFirstSelected()
        while item != -1:
            if item < len(classified_musics):
                selected_ids.append(classified_musics[item]['id'])
            item = self.ranking_list.GetNextSelected(item)
        
        return selected_ids

    def on_create_and_play_playlist_simple(self):
        """Cria uma playlist temporária e reproduz no player padrão."""
        # Obter caminhos das músicas selecionadas
        selected_music_paths = self._get_selected_music_paths_from_ranking()
        
        if not selected_music_paths:
            return
        
        # Criar e reproduzir playlist diretamente
        self._create_and_play_playlist(selected_music_paths)

    def on_play_multiple_musics(self):
        """Método mantido para compatibilidade - redireciona para criação simples de playlist."""
        self.on_create_and_play_playlist_simple()

    def _create_and_play_playlist(self, music_paths):
        """Cria uma playlist temporária e abre no player padrão."""
        try:
            # Criar arquivo de playlist temporário
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            playlist_path = os.path.join(temp_dir, f"RankMyMP3_playlist_{timestamp}.m3u")
            
            # Escrever playlist no formato M3U
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"# Playlist criada pelo RankMyMP3\n")
                f.write(f"# {len(music_paths)} música(s)\n\n")
                
                for music_path in music_paths:
                    if os.path.exists(music_path):
                        # Adicionar entrada da música com título
                        music_name = os.path.basename(music_path)
                        f.write(f"#EXTINF:-1,{music_name}\n")
                        f.write(f"{music_path}\n")
            
            # Abrir playlist no player padrão
            system = platform.system()
            
            if system == "Windows":
                os.startfile(playlist_path)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', playlist_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', playlist_path], check=True)
            
        except Exception as e:
            wx.MessageBox(
                f"Erro ao criar playlist:\n{str(e)}\n\n" +
                "Tente exportar a playlist manualmente.",
                "Erro na Playlist",
                wx.OK | wx.ICON_ERROR
            )

    def _show_export_playlist_options(self, music_paths):
        """Mostra opções para exportar playlist."""
        dlg = wx.MessageDialog(
            self,
            f"Exportar playlist com {len(music_paths)} música(s)?\n\n" +
            "Escolha o formato:",
            "Exportar Playlist",
            wx.YES_NO | wx.ICON_QUESTION
        )
        dlg.SetYesNoLabels("M3U (Padrão)", "PLS (Winamp)")
        
        if dlg.ShowModal() == wx.ID_YES:
            self._export_playlist_m3u(music_paths)
        else:
            self._export_playlist_pls(music_paths)
        
        dlg.Destroy()

    def _export_playlist_m3u(self, music_paths):
        """Exporta playlist no formato M3U."""
        dlg = wx.FileDialog(
            self,
            "Salvar Playlist M3U",
            wildcard="Playlist M3U (*.m3u)|*.m3u",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            playlist_path = dlg.GetPath()
            try:
                with open(playlist_path, 'w', encoding='utf-8') as f:
                    f.write("#EXTM3U\n")
                    f.write(f"# Playlist criada pelo RankMyMP3\n")
                    f.write(f"# {len(music_paths)} música(s)\n\n")
                    
                    for music_path in music_paths:
                        if os.path.exists(music_path):
                            music_name = os.path.basename(music_path)
                            f.write(f"#EXTINF:-1,{music_name}\n")
                            f.write(f"{music_path}\n")
                
                wx.MessageBox(
                    f"Playlist M3U salva com sucesso!\n\n{playlist_path}",
                    "Exportação Concluída",
                    wx.OK | wx.ICON_INFORMATION
                )
            except Exception as e:
                wx.MessageBox(
                    f"Erro ao salvar playlist:\n{str(e)}",
                    "Erro na Exportação",
                    wx.OK | wx.ICON_ERROR
                )
        
        dlg.Destroy()

    def _export_playlist_pls(self, music_paths):
        """Exporta playlist no formato PLS."""
        dlg = wx.FileDialog(
            self,
            "Salvar Playlist PLS",
            wildcard="Playlist PLS (*.pls)|*.pls",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            playlist_path = dlg.GetPath()
            try:
                with open(playlist_path, 'w', encoding='utf-8') as f:
                    f.write("[playlist]\n")
                    f.write(f"NumberOfEntries={len(music_paths)}\n\n")
                    
                    valid_count = 0
                    for i, music_path in enumerate(music_paths, 1):
                        if os.path.exists(music_path):
                            valid_count += 1
                            music_name = os.path.basename(music_path)
                            f.write(f"File{valid_count}={music_path}\n")
                            f.write(f"Title{valid_count}={music_name}\n")
                            f.write(f"Length{valid_count}=-1\n\n")
                
                wx.MessageBox(
                    f"Playlist PLS salva com sucesso!\n\n{playlist_path}",
                    "Exportação Concluída",
                    wx.OK | wx.ICON_INFORMATION
                )
            except Exception as e:
                wx.MessageBox(
                    f"Erro ao salvar playlist:\n{str(e)}",
                    "Erro na Exportação",
                    wx.OK | wx.ICON_ERROR
                )
        
        dlg.Destroy()

    def on_move_multiple_music_files(self):
        """Move múltiplas músicas selecionadas para uma nova pasta."""
        # Obter IDs das músicas selecionadas
        selected_music_ids = self._get_selected_music_ids_from_ranking()
        
        if not selected_music_ids:
            return
        
        count = len(selected_music_ids)
        
        # Escolher pasta de destino
        dlg = wx.DirDialog(
            self,
            f"Escolha a pasta de destino para {count} música(s):",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            destination_folder = dlg.GetPath()
            
            # Confirmar operação
            confirm_dlg = wx.MessageDialog(
                self,
                f"Mover {count} música(s) para:\n{destination_folder}\n\nEsta operação atualizará os caminhos no banco de dados.",
                "Confirmar Movimentação",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if confirm_dlg.ShowModal() == wx.ID_YES:
                success_count = 0
                failed_files = []
                
                # Processar cada música selecionada
                for music_id in selected_music_ids:
                    music_details = self.controller.music_model.get_music_details(music_id)
                    if not music_details:
                        failed_files.append(f"ID {music_id}: Música não encontrada no banco")
                        continue
                    
                    current_path = music_details['path']
                    filename = os.path.basename(current_path)
                    new_path = os.path.join(destination_folder, filename)
                    
                    try:
                        # Verificar se arquivo fonte existe
                        if not os.path.exists(current_path):
                            failed_files.append(f"{filename}: Arquivo fonte não encontrado")
                            continue
                        
                        # Verificar se destino já existe
                        if os.path.exists(new_path):
                            # Gerar nome único
                            base, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(new_path):
                                new_filename = f"{base}_{counter}{ext}"
                                new_path = os.path.join(destination_folder, new_filename)
                                counter += 1
                        
                        # Mover arquivo
                        import shutil
                        shutil.move(current_path, new_path)
                        
                        # Atualizar banco de dados
                        success = self.controller.music_model.update_music_path(music_id, new_path)
                        
                        if success:
                            success_count += 1
                        else:
                            # Tentar reverter movimento do arquivo
                            try:
                                shutil.move(new_path, current_path)
                            except:
                                pass
                            failed_files.append(f"{filename}: Erro ao atualizar banco de dados")
                            
                    except Exception as e:
                        failed_files.append(f"{filename}: {str(e)}")
                
                # Atualizar interface se houve sucesso
                if success_count > 0:
                    self.update_analysis_tree()
                    self.update_ranking_list()
                
                # Mostrar resultado
                if success_count > 0:
                    message = f"{success_count} música(s) movida(s) com sucesso!"
                    if failed_files:
                        message += f"\n\n{len(failed_files)} arquivo(s) falharam:\n" + "\n".join(failed_files[:3])
                        if len(failed_files) > 3:
                            message += f"\n... e mais {len(failed_files) - 3}"
                    
                    wx.MessageBox(
                        message,
                        "Movimentação Concluída" if not failed_files else "Movimentação Parcial",
                        wx.OK | (wx.ICON_INFORMATION if not failed_files else wx.ICON_WARNING)
                    )
                else:
                    wx.MessageBox(
                        f"Não foi possível mover nenhuma das {count} música(s) selecionada(s).\n\nDetalhes:\n" + "\n".join(failed_files[:5]),
                        "Erro na Movimentação",
                        wx.OK | wx.ICON_ERROR
                    )
            
            confirm_dlg.Destroy()
        
        dlg.Destroy()

    def on_copy_multiple_music_files(self):
        """Copia múltiplas músicas selecionadas para uma nova pasta."""
        # Obter caminhos das músicas selecionadas
        selected_music_paths = self._get_selected_music_paths_from_ranking()
        
        if not selected_music_paths:
            return
        
        count = len(selected_music_paths)
        
        # Escolher pasta de destino
        dlg = wx.DirDialog(
            self,
            f"Escolha a pasta de destino para copiar {count} música(s):",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            destination_folder = dlg.GetPath()
            
            # Confirmar operação
            confirm_dlg = wx.MessageDialog(
                self,
                f"Copiar {count} música(s) para:\n{destination_folder}\n\nOs arquivos originais permanecerão inalterados.",
                "Confirmar Cópia",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if confirm_dlg.ShowModal() == wx.ID_YES:
                success_count = 0
                failed_files = []
                
                # Processar cada música selecionada
                for music_path in selected_music_paths:
                    filename = os.path.basename(music_path)
                    new_path = os.path.join(destination_folder, filename)
                    
                    try:
                        # Verificar se arquivo fonte existe
                        if not os.path.exists(music_path):
                            failed_files.append(f"{filename}: Arquivo fonte não encontrado")
                            continue
                        
                        # Verificar se destino já existe e gerar nome único se necessário
                        if os.path.exists(new_path):
                            base, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(new_path):
                                new_filename = f"{base}_{counter}{ext}"
                                new_path = os.path.join(destination_folder, new_filename)
                                counter += 1
                        
                        # Copiar arquivo
                        import shutil
                        shutil.copy2(music_path, new_path)
                        success_count += 1
                            
                    except Exception as e:
                        failed_files.append(f"{filename}: {str(e)}")
                
                # Mostrar resultado
                if success_count > 0:
                    message = f"{success_count} música(s) copiada(s) com sucesso para:\n{destination_folder}"
                    if failed_files:
                        message += f"\n\n{len(failed_files)} arquivo(s) falharam:\n" + "\n".join(failed_files[:3])
                        if len(failed_files) > 3:
                            message += f"\n... e mais {len(failed_files) - 3}"
                    
                    wx.MessageBox(
                        message,
                        "Cópia Concluída" if not failed_files else "Cópia Parcial",
                        wx.OK | (wx.ICON_INFORMATION if not failed_files else wx.ICON_WARNING)
                    )
                else:
                    wx.MessageBox(
                        f"Não foi possível copiar nenhuma das {count} música(s) selecionada(s).\n\nDetalhes:\n" + "\n".join(failed_files[:5]),
                        "Erro na Cópia",
                        wx.OK | wx.ICON_ERROR
                    )
            
            confirm_dlg.Destroy()
        
        dlg.Destroy()

    def on_export_selected_playlist(self):
        """Exporta playlist das músicas selecionadas."""
        # Obter caminhos das músicas selecionadas
        selected_music_paths = self._get_selected_music_paths_from_ranking()
        
        if not selected_music_paths:
            return
        
        # Mostrar opções de exportação
        self._show_export_playlist_options(selected_music_paths)

    def _get_selected_music_paths_from_ranking(self):
        """Obtém os caminhos das músicas selecionadas na lista de ranking."""
        selected_paths = []
        
        # Obter lista de músicas classificadas
        ranked_musics = self.controller.get_classified_musics_topological()
        classified_musics = [music for music in ranked_musics if music['stars'] is not None and music['stars'] > 0]
        
        # Iterar pelos itens selecionados
        item = self.ranking_list.GetFirstSelected()
        while item != -1:
            if item < len(classified_musics):
                selected_paths.append(classified_musics[item]['path'])
            item = self.ranking_list.GetNextSelected(item)
        
        return selected_paths

    def on_comparison_choice(self, choice):
        """Lida com a escolha do usuário na comparação."""
        state = self.controller.get_current_comparison_state()
        if not state:
            return

        music_a_id = state['unrated_music_id']
        music_b_id = state['compared_music_id']
        
        # Determinar o vencedor baseado na escolha
        winner_id = music_a_id if choice == 0 else music_b_id
        
        # Registrar a comparação no sistema
        classification_finished = self.controller.make_comparison(music_a_id, music_b_id, winner_id)
        
        # Finalizar esta comparação e iniciar próxima automaticamente
        self._finalize_comparison_and_continue()

    def _finalize_comparison_and_continue(self):
        """Finaliza comparação atual e inicia próxima automaticamente."""
        # Atualizar listas e status
        self.update_analysis_tree()
        self.update_ranking_list()
        self.update_status()
        
        # Nota: NÃO limpar o estado aqui, pois a busca binária pode continuar
        # com a mesma música. O controller gerencia o estado internamente.
        
        # Iniciar próxima comparação automaticamente
        wx.CallAfter(self.start_comparison)

    def on_add_folder(self, event):
        """Abre o diálogo para adicionar uma pasta de músicas."""
        with wx.DirDialog(self, "Selecione uma pasta de músicas") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                added_count = self.controller.add_music_folder(dlg.GetPath())
                self.update_analysis_tree()
                self.update_ranking_list()
                self.update_status()
                
                # Se foram adicionadas músicas, iniciar comparações automaticamente
                if added_count > 0:
                    wx.CallAfter(self.start_comparison)

    def on_skip_music(self, index):
        """
        Pula uma das músicas em comparação e avança para a próxima automaticamente.
        :param index: 0 para música A, 1 para música B
        """
        state = self.controller.get_current_comparison_state()
        if not state:
            return

        music_a_id = state['unrated_music_id']
        music_b_id = state['compared_music_id'] 
        music_id = music_a_id if index == 0 else music_b_id
            
        # Marcar a música como ignorada (-1 estrelas)
        self.controller.skip_music(music_id)
            
        # Limpar o estado atual e avançar automaticamente
        self._finalize_comparison_and_continue()

    def on_view_folders(self, event):
        """Mostra um diálogo com as pastas adicionadas."""
        folders = self.controller.get_folders()
        if not folders:
            wx.MessageBox("Nenhuma pasta foi adicionada ainda.", "Pastas", wx.OK | wx.ICON_INFORMATION)
            return
        
        folder_text = "\n".join([f"• {folder}" for folder in folders])
        message = f"Pastas adicionadas ({len(folders)}):\n\n{folder_text}"
        
        dlg = wx.MessageDialog(self, message, "Pastas Adicionadas", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def on_clear_folders(self, event):
        """Remove todas as pastas (com confirmação)."""
        folder_count = self.controller.get_folder_count()
        if folder_count == 0:
            wx.MessageBox("Não há pastas para remover.", "Limpar Pastas", wx.OK | wx.ICON_INFORMATION)
            return
        
        result = wx.MessageBox(
            f"Tem certeza que deseja remover todas as {folder_count} pastas?\n\n"
            "Isso não afetará as músicas já adicionadas ao banco.",
            "Confirmar Limpeza", 
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if result == wx.YES:
            self.controller.clear_all_folders()
            self.update_status()
            wx.MessageBox("Todas as pastas foram removidas.", "Sucesso", wx.OK | wx.ICON_INFORMATION)

    def on_exit(self, event):
        """Sai da aplicação."""
        self.Close()

    def on_window_close(self, event):
        """Salva todas as configurações antes de fechar."""
        try:
            # Coletar configurações de layout atuais
            column_widths = [
                self.ranking_list.GetColumnWidth(0),  # Posição
                self.ranking_list.GetColumnWidth(1),  # Música
                self.ranking_list.GetColumnWidth(2),  # Estrelas
                self.ranking_list.GetColumnWidth(3)   # Tags
            ]
            
            splitter_pos = self.main_splitter.GetSashPosition()
            tags_splitter_pos = self.right_splitter.GetSashPosition()
            tags_expanded = not self.right_splitter.IsSplit() or self.right_bottom_panel.IsShown()
            
            # Salvar todas as configurações de uma vez
            self.app_settings.save_all_settings(
                self, 
                column_widths, 
                splitter_pos, 
                tags_expanded,
                tags_splitter_pos
            )
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
        finally:
            # Permitir que a janela feche normalmente
            event.Skip()

    def on_column_resize(self, event):
        """Salva larguras das colunas quando redimensionadas."""
        try:
            # Usar CallAfter para garantir que a largura já foi atualizada
            wx.CallAfter(self._save_layout_settings)
        except Exception as e:
            print(f"Erro ao salvar largura das colunas: {e}")
        finally:
            event.Skip()
    
    def on_splitter_move(self, event):
        """Salva posição do splitter quando movido."""
        try:
            # Usar CallAfter para garantir que a posição já foi atualizada
            wx.CallAfter(self._save_layout_settings)
        except Exception as e:
            print(f"Erro ao salvar posição do splitter: {e}")
        finally:
            event.Skip()
    
    def on_tags_splitter_move(self, event):
        """Salva posição do splitter de tags quando movido."""
        try:
            # Usar CallAfter para garantir que a posição já foi atualizada
            wx.CallAfter(self._save_layout_settings)
        except Exception as e:
            print(f"Erro ao salvar posição do splitter de tags: {e}")
        finally:
            event.Skip()
    
    def _save_layout_settings(self):
        """Salva apenas as configurações de layout."""
        try:
            column_widths = [
                self.ranking_list.GetColumnWidth(0),
                self.ranking_list.GetColumnWidth(1),
                self.ranking_list.GetColumnWidth(2),
                self.ranking_list.GetColumnWidth(3)
            ]
            
            splitter_pos = self.main_splitter.GetSashPosition()
            tags_splitter_pos = self.right_splitter.GetSashPosition()
            tags_expanded = self.tags_expanded  # Usar o estado real da variável
            
            self.app_settings.save_layout_settings(
                column_widths, 
                splitter_pos, 
                tags_expanded,
                tags_splitter_pos  # Nova configuração
            )
        except Exception as e:
            print(f"Erro ao salvar configurações de layout: {e}")

    # ===================== NOVOS MÉTODOS PARA TAGS E FILTROS =====================

    def on_filter_changed(self, event):
        """Atualiza a lista quando os filtros mudam."""
        self.update_filter_summary()
        self.update_ranking_list()

    def on_clear_filters(self, event):
        """Limpa todos os filtros."""
        self.stars_filter.SetSelection(0)  # "Todas"
        
        # Limpar checkboxes de tags se existirem
        if hasattr(self, 'tag_checkboxes'):
            for checkbox in self.tag_checkboxes:
                checkbox.SetValue(False)
            self.update_filtered_count()
            self.update_filter_summary()
        
        self.update_ranking_list()

    def populate_tags_checkboxes(self):
        """Popula os checkboxes de tags em layout de colunas otimizado."""
        try:
            # Limpar checkboxes existentes
            for checkbox in self.tag_checkboxes:
                checkbox.Destroy()
            self.tag_checkboxes.clear()
            
            # Recriar o sizer para evitar problemas com growable columns
            self.tags_checkboxes_sizer.Clear()
            
            # Obter todas as tags do banco
            all_tags = self.controller.music_model.get_all_tags()
            num_tags = len(all_tags)
            
            # Ajustar número de colunas baseado na quantidade de tags
            if num_tags <= 6:
                cols = 2  # Poucas tags: 2 colunas
            elif num_tags <= 15:
                cols = 3  # Quantidade média: 3 colunas  
            else:
                cols = 4  # Muitas tags: 4 colunas
            
            # Recriar sizer com número de colunas otimizado
            self.tags_checkboxes_sizer.SetCols(cols)
            
            # Criar checkbox para cada tag
            for tag in sorted(all_tags):
                checkbox = wx.CheckBox(self.tags_scroll_panel, label=tag)
                checkbox.Bind(wx.EVT_CHECKBOX, self.on_tag_checkbox_changed)
                self.tag_checkboxes.append(checkbox)
                # Adicionar com alinhamento à esquerda e menos padding
                self.tags_checkboxes_sizer.Add(checkbox, 0, wx.ALIGN_LEFT | wx.ALL, 2)
            
            # Atualizar layout
            self.tags_scroll_panel.FitInside()
            self.tags_scroll_panel.Layout()
            
        except Exception as e:
            print(f"Erro ao carregar checkboxes de tags: {e}")

    def on_toggle_tags_panel(self, event):
        """Mostra/oculta o painel de tags."""
        if self.tags_expanded:
            # Ocultar painel de tags
            # Salvar a posição atual antes de ocultar
            self._saved_tags_splitter_pos = self.right_splitter.GetSashPosition()
            
            self.tags_expanded = False
            self.tags_resizable_panel.Hide()
            self.expand_tags_btn.SetLabel("🔽 Filtrar por Tags")
            
            # Limpar seleções de tags
            for checkbox in self.tag_checkboxes:
                checkbox.SetValue(False)
            self.update_filter_summary()
            
            # Reduzir o painel superior para dar mais espaço à lista
            self.right_splitter.SetSashPosition(80)  # Tamanho mínimo só para filtros
        else:
            # Mostrar painel de tags
            self.tags_expanded = True
            self.tags_resizable_panel.Show()
            self.expand_tags_btn.SetLabel("🔼 Ocultar Tags")
            self.populate_tags_checkboxes()
            self.update_filter_summary()
            
            # Restaurar tamanho salvo do painel superior
            saved_pos = getattr(self, '_saved_tags_splitter_pos', 200)
            self.right_splitter.SetSashPosition(saved_pos)
        
        # Atualizar layout
        self.right_top_panel.Layout()
        self.on_filter_changed(event)
        
        # Salvar estado do painel de tags
        wx.CallAfter(self._save_layout_settings)


    def on_clear_all_tags(self, event):
        """Limpa todas as seleções de tags nos checkboxes."""
        for checkbox in self.tag_checkboxes:
            checkbox.SetValue(False)
        self.update_filtered_count()
        self.update_filter_summary()
        self.on_filter_changed(event)

    def on_tag_checkbox_changed(self, event):
        """Chamado quando um checkbox de tag é alterado."""
        self.update_filtered_count()
        self.update_filter_summary()
        self.on_filter_changed(event)

    def get_selected_tags(self):
        """Retorna lista de tags selecionadas nos checkboxes."""
        if not hasattr(self, 'tags_expanded') or not self.tags_expanded:
            return []
        
        selected_tags = []
        for checkbox in self.tag_checkboxes:
            if checkbox.GetValue():
                selected_tags.append(checkbox.GetLabel())
        return selected_tags

    def update_filtered_count(self):
        """Atualiza o contador de músicas filtradas."""
        if not hasattr(self, 'tags_expanded') or not self.tags_expanded:
            self.filtered_count_label.SetLabel("")
            return
            
        try:
            # Obter filtros ativos
            selected_tags = self.get_selected_tags()
            min_stars, max_stars = self._get_stars_filter_range()
            
            # Contar músicas que correspondem aos filtros
            if selected_tags:
                filtered_musics = self.controller.music_model.get_filtered_musics_multi_tags(
                    tags_list=selected_tags,
                    min_stars=min_stars,
                    max_stars=max_stars
                )
                count = len(filtered_musics)
                tags_text = f"{len(selected_tags)} tag{'s' if len(selected_tags) != 1 else ''}"
                self.filtered_count_label.SetLabel(f"📊 {count} música{'s' if count != 1 else ''} com {tags_text}")
            else:
                self.filtered_count_label.SetLabel("📊 Selecione tags para filtrar")
                
        except Exception as e:
            print(f"Erro ao contar músicas filtradas: {e}")
            self.filtered_count_label.SetLabel("")

    def update_filter_summary(self):
        """Atualiza o resumo dos filtros quando o painel está recolhido."""
        if hasattr(self, 'tags_expanded') and self.tags_expanded:
            # Se expandido, não mostrar resumo
            self.filter_summary_label.SetLabel("")
            return
            
        # Contar filtros ativos
        selected_tags = self.get_selected_tags()
        has_star_filter = hasattr(self, 'stars_filter') and self.stars_filter.GetSelection() > 0
        
        summary_parts = []
        
        if has_star_filter:
            stars_text = self.stars_filter.GetStringSelection()
            summary_parts.append(f"⭐ {stars_text}")
        
        if selected_tags:
            summary_parts.append(f"🏷️ {len(selected_tags)} tag{'s' if len(selected_tags) != 1 else ''}")
        
        if summary_parts:
            self.filter_summary_label.SetLabel(f"Filtros: {' + '.join(summary_parts)}")
        else:
            self.filter_summary_label.SetLabel("")

    def refresh_tags_filter(self):
        """Atualiza os checkboxes de tags (chamado após mudanças nas tags)."""
        if hasattr(self, 'tags_expanded') and self.tags_expanded:
            # Se o painel de tags estiver expandido, repopular
            selected_tags_before = self.get_selected_tags()
            self.populate_tags_checkboxes()
            
            # Tentar restaurar seleções anteriores
            for checkbox in self.tag_checkboxes:
                if checkbox.GetLabel() in selected_tags_before:
                    checkbox.SetValue(True)
            
            self.update_filtered_count()
            self.update_filter_summary()

    def on_manage_tags(self, music_id, music_name):
        """Abre dialog para gerenciar tags de uma música."""
        dialog = TagsDialog(self, music_id, music_name, self.controller.music_model)
        if dialog.ShowModal() == wx.ID_OK:
            # Atualizar a lista de ranking para mostrar as novas tags
            self.update_ranking_list()
            # Atualizar o filtro de tags
            self.refresh_tags_filter()
        dialog.Destroy()

    def on_show_music_path(self, music_path):
        """Mostra o caminho completo da música em um dialog."""
        dialog = wx.MessageDialog(
            self,
            f"📁 Caminho completo da música:\n\n{music_path}",
            "Localização da Música",
            wx.OK | wx.ICON_INFORMATION
        )
        dialog.ShowModal()
        dialog.Destroy()

    def on_open_music_folder(self, music_path):
        """Abre a pasta que contém a música no explorador de arquivos do sistema."""
        import subprocess
        import platform
        
        # Obter o diretório da música
        folder_path = os.path.dirname(music_path)
        
        # Verificar se a pasta existe
        if not os.path.exists(folder_path):
            wx.MessageBox(
                f"A pasta não foi encontrada:\n{folder_path}",
                "Pasta não encontrada",
                wx.OK | wx.ICON_ERROR
            )
            return
        
        try:
            # Detectar o sistema operacional e usar o comando apropriado
            system = platform.system()
            
            if system == "Windows":
                # Windows - usar explorer
                subprocess.run(['explorer', folder_path], check=True)
            elif system == "Darwin":  # macOS
                # macOS - usar open
                subprocess.run(['open', folder_path], check=True)
            else:  # Linux e outros Unix-like
                # Linux - usar xdg-open (funciona na maioria das distribuições)
                subprocess.run(['xdg-open', folder_path], check=True)
                
        except subprocess.CalledProcessError:
            # Se falhar, tentar métodos alternativos
            try:
                if system == "Linux":
                    # Tentar outros gerenciadores de arquivo comuns no Linux
                    for file_manager in ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo']:
                        try:
                            subprocess.run([file_manager, folder_path], check=True)
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
                    else:
                        raise subprocess.CalledProcessError(1, "No file manager found")
                else:
                    raise
            except subprocess.CalledProcessError:
                # Se nada funcionar, mostrar erro com o caminho
                wx.MessageBox(
                    f"Não foi possível abrir a pasta automaticamente.\n\nCaminho da pasta:\n{folder_path}",
                    "Erro ao abrir pasta",
                    wx.OK | wx.ICON_WARNING
                )
            except FileNotFoundError:
                wx.MessageBox(
                    f"Comando não encontrado para abrir pastas no seu sistema.\n\nCaminho da pasta:\n{folder_path}",
                    "Comando não disponível",
                    wx.OK | wx.ICON_WARNING
                )

    def on_play_music(self, music_path):
        """Abre a música no player padrão do sistema."""
        # Verificar se o arquivo existe
        if not os.path.exists(music_path):
            wx.MessageBox(
                f"O arquivo de música não foi encontrado:\n{music_path}",
                "Arquivo não encontrado",
                wx.OK | wx.ICON_ERROR
            )
            return
        
        try:
            # Detectar o sistema operacional e usar o comando apropriado
            system = platform.system()
            
            if system == "Windows":
                # Windows - usar start para abrir com programa padrão
                os.startfile(music_path)
            elif system == "Darwin":  # macOS
                # macOS - usar open
                subprocess.run(['open', music_path], check=True)
            else:  # Linux e outros Unix-like
                # Linux - usar xdg-open (funciona na maioria das distribuições)
                subprocess.run(['xdg-open', music_path], check=True)
                
        except subprocess.CalledProcessError:
            # Se falhar, mostrar erro informativo
            wx.MessageBox(
                f"Não foi possível abrir a música no player padrão.\n\nArquivo:\n{music_path}\n\nTente abrir manualmente com seu player preferido.",
                "Erro ao abrir música",
                wx.OK | wx.ICON_WARNING
            )
        except (FileNotFoundError, OSError) as e:
            wx.MessageBox(
                f"Comando não encontrado para abrir arquivos de música no seu sistema.\n\nArquivo:\n{music_path}\n\nDetalhes: {str(e)}",
                "Player não disponível",
                wx.OK | wx.ICON_WARNING
            )

    def on_move_music_file(self, music_id):
        """Move uma música para outra pasta e atualiza o caminho no banco."""
        # Obter informações atuais da música
        music_details = self.controller.music_model.get_music_details(music_id)
        if not music_details:
            wx.MessageBox("Música não encontrada no banco de dados.", "Erro", wx.OK | wx.ICON_ERROR)
            return
            
        current_path = music_details['path']
        current_folder = os.path.dirname(current_path)
        filename = os.path.basename(current_path)
        
        # Verificar se o arquivo atual existe
        if not os.path.exists(current_path):
            wx.MessageBox(
                f"O arquivo da música não foi encontrado:\n{current_path}\n\nNão é possível mover.",
                "Arquivo não encontrado",
                wx.OK | wx.ICON_ERROR
            )
            return
        
        # Dialog para selecionar nova pasta
        with wx.DirDialog(
            self,
            "Selecione a pasta de destino:",
            defaultPath=current_folder,
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        ) as dialog:
            
            if dialog.ShowModal() != wx.ID_OK:
                return  # Usuário cancelou
                
            new_folder = dialog.GetPath()
            new_path = os.path.join(new_folder, filename)
            
            # Verificar se o arquivo de destino já existe
            if os.path.exists(new_path):
                response = wx.MessageBox(
                    f"Já existe um arquivo com o mesmo nome na pasta de destino:\n{new_path}\n\nDeseja substituir?",
                    "Arquivo já existe",
                    wx.YES_NO | wx.ICON_QUESTION
                )
                if response != wx.YES:
                    return
            
            # Tentar mover o arquivo
            try:
                import shutil
                shutil.move(current_path, new_path)
                
                # Atualizar o caminho no banco de dados
                success = self.controller.music_model.update_music_path(music_id, new_path)
                
                if success:
                    wx.MessageBox(
                        f"Música movida com sucesso!\n\nDe: {current_path}\nPara: {new_path}",
                        "Movimento realizado",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    
                    # Atualizar as interfaces
                    self.update_analysis_tree()
                    self.update_ranking_list()
                    
                else:
                    # Se falhou ao atualizar o banco, tentar voltar o arquivo
                    try:
                        shutil.move(new_path, current_path)
                        wx.MessageBox(
                            "Erro ao atualizar o banco de dados. O arquivo foi restaurado para a posição original.",
                            "Erro no banco de dados",
                            wx.OK | wx.ICON_ERROR
                        )
                    except Exception as e:
                        wx.MessageBox(
                            f"ERRO CRÍTICO: Arquivo foi movido mas não foi possível atualizar o banco nem restaurar!\n\nArquivo atual: {new_path}\nDeveria estar em: {current_path}\nErro: {str(e)}",
                            "Erro crítico",
                            wx.OK | wx.ICON_ERROR
                        )
                        
            except Exception as e:
                wx.MessageBox(
                    f"Erro ao mover o arquivo:\n{str(e)}",
                    "Erro de movimento",
                    wx.OK | wx.ICON_ERROR
                )

    def get_filtered_musics(self):
        """Retorna músicas filtradas pelos critérios atuais."""
        # Obter tags selecionadas e filtro de estrelas
        selected_tags = self.get_selected_tags()
        min_stars, max_stars = self._get_stars_filter_range()
        
        # Se há tags selecionadas, usar filtro de múltiplas tags
        if selected_tags:
            return self.controller.music_model.get_filtered_musics_multi_tags(
                tags_list=selected_tags,
                min_stars=min_stars,
                max_stars=max_stars
            )
        else:
            # Se não há tags, usar filtro tradicional apenas por estrelas
            return self.controller.music_model.get_filtered_musics(
                tag_filter=None,
                min_stars=min_stars,
                max_stars=max_stars
            )

    def _get_stars_filter_range(self):
        """Retorna o range de estrelas baseado na seleção atual."""
        stars_selection = self.stars_filter.GetSelection()
        
        if stars_selection == 0:  # "Todas"
            return None, None
        else:
            # Mapear índice para número de estrelas (5, 4, 3, 2, 1)
            stars_value = 6 - stars_selection
            return stars_value, stars_value

    # ===================== MÉTODOS PARA FILTRO DE ANÁLISE =====================

    def on_analysis_filter_changed(self, event):
        """Chamado quando o filtro de análise muda."""
        # Obter valor diretamente e aplicar imediatamente
        filter_value = self.analysis_filter_text.GetValue()
        
        if hasattr(self, 'analysis_filter_active') and self.analysis_filter_active == filter_value:
            return  # Evitar atualizações desnecessárias
        
        self.analysis_filter_active = filter_value
        self.update_analysis_tree()

    def on_clear_analysis_filter(self, event):
        """Limpa o filtro de análise."""
        self.analysis_filter_text.SetValue("")
        self.analysis_filter_active = ""
        self.update_analysis_tree()

    # ===================== MÉTODOS PARA CLASSIFICAÇÃO FORÇADA =====================

    def on_force_classify_music(self, music_id):
        """Força a classificação de uma música específica como próxima comparação."""
        try:
            # Obter detalhes da música
            music_details = self.controller.music_model.get_music_details(music_id)
            if not music_details:
                wx.MessageBox("Música não encontrada.", "Erro", wx.OK | wx.ICON_ERROR)
                return
            
            # Verificar se a música já está classificada
            if music_details.get('stars', 0) > 0:
                wx.MessageBox("Esta música já está classificada.", "Informação", wx.OK | wx.ICON_INFORMATION)
                return
            
            # Verificar se a música está ignorada
            if music_details.get('stars', 0) == -1:
                wx.MessageBox("Esta música está ignorada. Restaure-a primeiro.", "Informação", wx.OK | wx.ICON_INFORMATION)
                return
            
            # Forçar comparação com esta música
            success = self.controller.force_next_comparison(music_id)
            
            if success:
                # Iniciar comparação imediatamente
                wx.CallAfter(self.start_comparison)
                wx.MessageBox(
                    f"Música '{os.path.basename(music_details['path'])}' será a próxima a ser classificada.",
                    "Classificação Forçada",
                    wx.OK | wx.ICON_INFORMATION
                )
            else:
                wx.MessageBox("Não foi possível forçar a classificação desta música.", "Erro", wx.OK | wx.ICON_ERROR)
                
        except Exception as e:
            wx.MessageBox(f"Erro ao forçar classificação: {str(e)}", "Erro", wx.OK | wx.ICON_ERROR)


class TagsDialog(wx.Dialog):
    """Dialog para gerenciar tags de uma música."""
    
    def __init__(self, parent, music_id, music_name, music_model):
        super().__init__(parent, title=f"🏷️ Gerenciar Tags - {music_name}", size=(500, 400))
        
        self.music_id = music_id
        self.music_model = music_model
        
        # Layout principal
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Título
        title_label = wx.StaticText(self, label=f"Tags para: {music_name}")
        title_font = title_label.GetFont()
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title_label.SetFont(title_font)
        main_sizer.Add(title_label, 0, wx.ALL, 10)
        
        # Tags atuais
        main_sizer.Add(wx.StaticText(self, label="Tags Atuais:"), 0, wx.ALL, 5)
        
        self.current_tags_panel = wx.Panel(self)
        self.current_tags_sizer = wx.WrapSizer(wx.HORIZONTAL)
        self.current_tags_panel.SetSizer(self.current_tags_sizer)
        main_sizer.Add(self.current_tags_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Campo para nova tag
        main_sizer.Add(wx.StaticText(self, label="Adicionar Nova Tag:"), 0, wx.ALL, 5)
        
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.new_tag_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.add_btn = wx.Button(self, label="Adicionar")
        add_sizer.Add(self.new_tag_ctrl, 1, wx.ALL, 5)
        add_sizer.Add(self.add_btn, 0, wx.ALL, 5)
        main_sizer.Add(add_sizer, 0, wx.EXPAND)
        
        # Tags populares
        main_sizer.Add(wx.StaticText(self, label="Tags Populares:"), 0, wx.ALL, 5)
        
        self.popular_tags_panel = wx.Panel(self)
        self.popular_tags_sizer = wx.WrapSizer(wx.HORIZONTAL)
        self.popular_tags_panel.SetSizer(self.popular_tags_sizer)
        main_sizer.Add(self.popular_tags_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # Botões de controle
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        
        save_btn = wx.Button(self, wx.ID_OK, "Salvar")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancelar")
        
        btn_sizer.Add(save_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        
        # Bind eventos
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_tag)
        self.new_tag_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_add_tag)
        
        # Carregar dados
        self.load_current_tags()
        self.load_popular_tags()
        
        self.Center()
    
    def load_current_tags(self):
        """Carrega as tags atuais da música."""
        # Limpar tags atuais
        self.current_tags_sizer.Clear(True)
        
        tags = self.music_model.get_music_tags(self.music_id)
        
        if not tags:
            no_tags_label = wx.StaticText(self.current_tags_panel, label="(Nenhuma tag)")
            no_tags_label.SetForegroundColour(wx.Colour(128, 128, 128))
            self.current_tags_sizer.Add(no_tags_label, 0, wx.ALL, 2)
        else:
            for tag in tags:
                self.add_tag_button(tag, self.current_tags_sizer, self.current_tags_panel, removable=True)
        
        self.current_tags_panel.Layout()
    
    def load_popular_tags(self):
        """Carrega tags populares do banco (mais usadas) e algumas sugeridas."""
        # Limpar tags populares
        self.popular_tags_sizer.Clear(True)
        
        # Primeiro, tentar obter tags mais usadas do banco
        try:
            # Buscar tags mais populares (com mais associações)
            cursor = self.music_model.conn.cursor()
            cursor.execute('''
                SELECT t.name, COUNT(mt.music_id) as usage_count
                FROM tags t
                LEFT JOIN music_tags mt ON t.id = mt.tag_id
                GROUP BY t.id, t.name
                HAVING usage_count > 0
                ORDER BY usage_count DESC, t.name
                LIMIT 10
            ''')
            popular_from_db = [row[0] for row in cursor.fetchall()]
        except:
            popular_from_db = []
        
        # Tags sugeridas básicas (apenas se não houver muitas no banco)
        basic_suggestions = [
            "rock", "pop", "jazz", "classical", "metal", "electronic",
            "instrumental", "acoustic", "live", "cover"
        ]
        
        # Combinar: populares do banco + sugestões que ainda não estão no banco
        current_tags = self.music_model.get_music_tags(self.music_id)
        tags_to_show = popular_from_db.copy()
        
        # Adicionar sugestões básicas que não estão nas populares e não estão já na música
        for suggestion in basic_suggestions:
            if (suggestion not in tags_to_show and 
                suggestion not in current_tags and 
                len(tags_to_show) < 15):
                tags_to_show.append(suggestion)
        
        # Mostrar as tags
        for tag in tags_to_show:
            if tag not in current_tags:  # Não mostrar tags já adicionadas
                self.add_tag_button(tag, self.popular_tags_sizer, self.popular_tags_panel, clickable=True)
        
        # Se não houver nenhuma tag para mostrar
        if not any(tag not in current_tags for tag in tags_to_show):
            no_tags_label = wx.StaticText(self.popular_tags_panel, label="(Todas as tags sugeridas já foram adicionadas)")
            no_tags_label.SetForegroundColour(wx.Colour(128, 128, 128))
            self.popular_tags_sizer.Add(no_tags_label, 0, wx.ALL, 2)
        
        self.popular_tags_panel.Layout()
    
    def add_tag_button(self, tag_name, sizer, parent, removable=False, clickable=False):
        """Adiciona um botão de tag."""
        if removable:
            # Tag removível (com X)
            tag_btn = wx.Button(parent, label=f"{tag_name} ❌", size=(100, 25))
            tag_btn.Bind(wx.EVT_BUTTON, lambda evt: self.remove_tag(tag_name))
        elif clickable:
            # Tag clicável para adicionar
            tag_btn = wx.Button(parent, label=tag_name, size=(80, 25))
            tag_btn.Bind(wx.EVT_BUTTON, lambda evt: self.quick_add_tag(tag_name))
        else:
            # Tag apenas visual
            tag_btn = wx.StaticText(parent, label=tag_name)
        
        sizer.Add(tag_btn, 0, wx.ALL, 2)
    
    def on_add_tag(self, event):
        """Adiciona uma nova tag."""
        tag_name = self.new_tag_ctrl.GetValue().strip().lower()
        
        if not tag_name:
            return
        
        # Verificar se já existe
        current_tags = self.music_model.get_music_tags(self.music_id)
        if tag_name in current_tags:
            wx.MessageBox(f"A tag '{tag_name}' já foi adicionada.", "Tag Duplicada", wx.OK | wx.ICON_INFORMATION)
            return
        
        # Adicionar tag
        self.music_model.add_tag(tag_name)
        self.music_model.associate_tag(self.music_id, tag_name)
        
        # Limpar campo
        self.new_tag_ctrl.SetValue("")
        
        # Recarregar listas
        self.load_current_tags()
        self.load_popular_tags()
    
    def quick_add_tag(self, tag_name):
        """Adiciona uma tag rapidamente (do painel de populares)."""
        # Adicionar tag
        self.music_model.add_tag(tag_name)
        self.music_model.associate_tag(self.music_id, tag_name)
        
        # Recarregar listas
        self.load_current_tags()
        self.load_popular_tags()
    
    def remove_tag(self, tag_name):
        """Remove uma tag da música."""
        # Implementar remoção (você precisará adicionar este método ao modelo)
        self.music_model.remove_tag_from_music(self.music_id, tag_name)
        
        # Recarregar listas
        self.load_current_tags()
        self.load_popular_tags()