import wx
import os
from controllers.music_controller import MusicController


class MusicApp(wx.Frame):
    def __init__(self, music_controller: MusicController):
        super().__init__(parent=None, title='RankMyMP3', size=(1200, 700))

        self.controller = music_controller

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
        self.ranking_list = wx.ListCtrl(
            self.right_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.ranking_list.InsertColumn(0, "Posição")
        self.ranking_list.InsertColumn(1, "Música")
        self.ranking_list.InsertColumn(2, "Estrelas")
        self.ranking_list.InsertColumn(3, "Tags")
        self.ranking_list.SetColumnWidth(0, 70)
        self.ranking_list.SetColumnWidth(1, 350)
        self.ranking_list.SetColumnWidth(2, 100)
        self.ranking_list.SetColumnWidth(3, 200)

        # Área de comparação (sempre visível, mas compacta)
        self.comparison_panel = wx.Panel(self.panel)

        # Configurar layouts
        self._setup_menu()
        self._setup_layouts()
        self._setup_comparison_panel()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_tree_events()

        # Atualizar as listas
        self.update_analysis_tree()
        self.update_ranking_list()
        
        # Popular o filtro de tags
        if hasattr(self, 'tags_filter'):
            self.populate_tags_filter()

        # Iniciar primeira comparação automaticamente
        wx.CallAfter(self.start_auto_comparison)

        self.Centre()
        self.Show()

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
        left_sizer.Add(self.analysis_tree, 1, wx.EXPAND | wx.ALL, 5)
        self.left_panel.SetSizer(left_sizer)

        # Layout do painel direito (ranking)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer.Add(wx.StaticText(self.right_panel, label="🏆 Ranking Atual:"), 0, wx.ALL, 5)
        
        # Adicionar barra de filtros
        self._setup_filter_panel()
        right_sizer.Add(self.filter_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        right_sizer.Add(self.ranking_list, 1, wx.EXPAND | wx.ALL, 5)
        self.right_panel.SetSizer(right_sizer)

        # Adicionar splitter e painel de comparação ao layout principal
        main_sizer.Add(self.main_splitter, 1, wx.EXPAND)
        main_sizer.Add(self.comparison_panel, 0, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

    def _setup_filter_panel(self):
        """Configura o painel de filtros para estrelas e tags."""
        self.filter_panel = wx.Panel(self.right_panel)
        
        # Layout horizontal para filtros
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Filtro por estrelas
        filter_sizer.Add(wx.StaticText(self.filter_panel, label="⭐ Estrelas:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        self.stars_filter = wx.Choice(self.filter_panel, choices=[
            "Todas", "⭐⭐⭐⭐⭐ (5)", "⭐⭐⭐⭐☆ (4)", "⭐⭐⭐☆☆ (3)", "⭐⭐☆☆☆ (2)", "⭐☆☆☆☆ (1)"
        ])
        self.stars_filter.SetSelection(0)  # "Todas" por padrão
        filter_sizer.Add(self.stars_filter, 0, wx.ALL, 5)
        
        # Espaçador
        filter_sizer.Add(wx.StaticLine(self.filter_panel, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 5)
        
        # Filtro por tags
        filter_sizer.Add(wx.StaticText(self.filter_panel, label="🏷️ Tags:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        # Usar ComboBox com dropdown para tags
        self.tags_filter = wx.ComboBox(self.filter_panel, style=wx.CB_READONLY)
        self.tags_filter.Append("Todas as Tags")
        self.tags_filter.SetSelection(0)  # "Todas as Tags" por padrão
        self.populate_tags_filter()  # Carregar tags disponíveis
        filter_sizer.Add(self.tags_filter, 0, wx.ALL, 5)
        
        # Botão limpar filtros
        self.clear_filters_btn = wx.Button(self.filter_panel, label="❌ Limpar")
        self.clear_filters_btn.SetMinSize((80, -1))
        filter_sizer.Add(self.clear_filters_btn, 0, wx.ALL, 5)
        
        self.filter_panel.SetSizer(filter_sizer)
        
        # Bind eventos dos filtros
        self.stars_filter.Bind(wx.EVT_CHOICE, self.on_filter_changed)
        self.tags_filter.Bind(wx.EVT_COMBOBOX, self.on_filter_changed)
        self.clear_filters_btn.Bind(wx.EVT_BUTTON, self.on_clear_filters)

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

    def update_analysis_tree(self):
        """Atualiza a árvore de análise com músicas organizadas por pasta."""
        # Salvar estado de expansão das pastas
        expanded_folders = set()
        root = self.analysis_tree.GetRootItem()
        if root.IsOk():
            analysis_root = self.analysis_tree.GetFirstChild(root)[0]
            if analysis_root.IsOk():
                folder_item = self.analysis_tree.GetFirstChild(analysis_root)[0]
                while folder_item.IsOk():
                    if self.analysis_tree.IsExpanded(folder_item):
                        folder_name = self.analysis_tree.GetItemText(folder_item)
                        expanded_folders.add(folder_name)
                    folder_item = self.analysis_tree.GetNextSibling(folder_item)
        
        # Reconstruir árvore
        self.analysis_tree.DeleteAllItems()
        
        # Criar raiz invisível
        root = self.analysis_tree.AddRoot("Root")
        
        # Buscar músicas não classificadas organizadas por pasta
        folders_dict = self.controller.get_unrated_musics_by_folder()
        
        # Adicionar seções principais
        analysis_root = self.analysis_tree.AppendItem(root, "🎵 Em Análise")
        self.analysis_tree.SetItemBold(analysis_root, True)
        
        # Adicionar pastas e músicas
        for folder_path, musics in folders_dict.items():
            folder_name = os.path.basename(folder_path) or folder_path
            folder_display_name = f"📁 {folder_name} ({len(musics)} músicas)"
            folder_item = self.analysis_tree.AppendItem(analysis_root, folder_display_name)
            
            # Adicionar músicas da pasta
            for music in musics:
                music_name = os.path.basename(music['path'])
                music_item = self.analysis_tree.AppendItem(folder_item, f"🎵 {music_name}")
                # Guardar o ID da música no item
                self.analysis_tree.SetItemData(music_item, music['id'])
            
            # Restaurar estado de expansão
            if folder_display_name in expanded_folders:
                self.analysis_tree.Expand(folder_item)
        
        # Adicionar seção de ignoradas (colapsada por padrão)
        ignored_musics = self.controller.get_ignored_musics()
        if ignored_musics:
            ignored_root = self.analysis_tree.AppendItem(root, f"❌ Ignoradas ({len(ignored_musics)})")
            self.analysis_tree.SetItemBold(ignored_root, True)
            
            for music in ignored_musics:
                music_name = os.path.basename(music['path'])
                music_item = self.analysis_tree.AppendItem(ignored_root, f"❌ {music_name}")
                self.analysis_tree.SetItemData(music_item, music['id'])
        
        # Expandir apenas a seção "Em Análise"
        self.analysis_tree.Expand(analysis_root)

    def update_ranking_list(self):
        """Atualiza a lista de ranking com filtros aplicados."""
        self.ranking_list.DeleteAllItems()
        
        # Verificar se há filtros ativos
        has_filters = (
            hasattr(self, 'stars_filter') and self.stars_filter.GetSelection() > 0 or
            hasattr(self, 'tags_filter') and self.tags_filter.GetSelection() > 0
        )
        
        if has_filters:
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
                self.ranking_list.SetItem(index, 2, "★" * music['stars'])
                
                # Adicionar tags na coluna 3
                tags = self.controller.music_model.get_music_tags(music['id'])
                tags_text = ", ".join(tags) if tags else ""
                self.ranking_list.SetItem(index, 3, tags_text)

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
        
        # Clique direito na lista de ranking para menu contextual
        self.ranking_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_ranking_right_click)

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
                
                move_item = menu.Append(wx.ID_ANY, "📦 Mover para Pasta...")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_move_music_file(music_id), move_item)
                
                menu.AppendSeparator()
            
            if item_text.startswith("❌"):
                # Música ignorada - opção para restaurar
                restore_item = menu.Append(wx.ID_ANY, "Restaurar para Análise")
                self.Bind(wx.EVT_MENU, lambda evt: self.on_restore_music(music_items[0][1]), restore_item)
            else:
                # Música em análise - opção para ignorar
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
        
        # Buscar a música classificada correspondente ao índice
        ranked_musics = self.controller.get_classified_musics_topological()
        classified_musics = [music for music in ranked_musics if music['stars'] is not None and music['stars'] > 0]
        
        if item_index >= len(classified_musics):
            return
        
        selected_music = classified_musics[item_index]
        music_id = selected_music['id']
        music_name = os.path.basename(selected_music['path'])
        
        # Criar menu contextual
        menu = wx.Menu()
        
        # Opção para gerenciar tags
        tags_item = menu.Append(wx.ID_ANY, f"🏷️ Gerenciar Tags")
        self.Bind(wx.EVT_MENU, lambda evt: self.on_manage_tags(music_id, music_name), tags_item)
        
        menu.AppendSeparator()
        
        # Opção para mostrar caminho da música
        show_path_item = menu.Append(wx.ID_ANY, f"📁 Mostrar Caminho")
        self.Bind(wx.EVT_MENU, lambda evt: self.on_show_music_path(selected_music['path']), show_path_item)
        
        # Opção para abrir pasta no sistema
        open_folder_item = menu.Append(wx.ID_ANY, f"🗂️ Abrir Pasta")
        self.Bind(wx.EVT_MENU, lambda evt: self.on_open_music_folder(selected_music['path']), open_folder_item)
        
        # Opção para mover arquivo
        move_item = menu.Append(wx.ID_ANY, f"📦 Mover para Pasta...")
        self.Bind(wx.EVT_MENU, lambda evt: self.on_move_music_file(music_id), move_item)
        
        menu.AppendSeparator()
        
        # Opção para remover da classificação
        remove_item = menu.Append(wx.ID_ANY, f"Remover da Classificação")
        self.Bind(wx.EVT_MENU, lambda evt: self.on_remove_from_ranking(music_id), remove_item)
        
        # Opção para ignorar permanentemente
        ignore_item = menu.Append(wx.ID_ANY, f"Ignorar Permanentemente")
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

    # ===================== NOVOS MÉTODOS PARA TAGS E FILTROS =====================

    def on_filter_changed(self, event):
        """Atualiza a lista quando os filtros mudam."""
        self.update_ranking_list()

    def on_clear_filters(self, event):
        """Limpa todos os filtros."""
        self.stars_filter.SetSelection(0)  # "Todas"
        self.tags_filter.SetSelection(0)   # "Todas as Tags"
        self.update_ranking_list()

    def populate_tags_filter(self):
        """Popula o filtro de tags com as tags disponíveis no banco."""
        try:
            # Limpar itens existentes (exceto "Todas as Tags")
            while self.tags_filter.GetCount() > 1:
                self.tags_filter.Delete(1)
            
            # Obter todas as tags do banco
            all_tags = self.controller.music_model.get_all_tags()
            
            # Adicionar cada tag ao filtro
            for tag in sorted(all_tags):
                self.tags_filter.Append(tag)
                
        except Exception as e:
            print(f"Erro ao carregar tags: {e}")

    def refresh_tags_filter(self):
        """Atualiza o filtro de tags (chamado após mudanças nas tags)."""
        current_selection = self.tags_filter.GetSelection()
        current_value = self.tags_filter.GetStringSelection() if current_selection >= 0 else ""
        
        # Repopular
        self.populate_tags_filter()
        
        # Tentar restaurar seleção
        if current_value:
            new_index = self.tags_filter.FindString(current_value)
            if new_index != wx.NOT_FOUND:
                self.tags_filter.SetSelection(new_index)
            else:
                self.tags_filter.SetSelection(0)  # "Todas as Tags"

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
        # Obter critérios de filtro
        stars_selection = self.stars_filter.GetSelection()
        tags_selection = self.tags_filter.GetSelection()
        
        # Determinar filtro de estrelas
        stars_filter = None
        if stars_selection > 0:  # Não é "Todas"
            # Mapear índice para número de estrelas (5, 4, 3, 2, 1)
            stars_filter = 6 - stars_selection
        
        # Determinar filtro de tags
        tags_filter = None
        if tags_selection > 0:  # Não é "Todas as Tags"
            tags_filter = self.tags_filter.GetStringSelection()
        
        # Usar o método do modelo para filtrar
        return self.controller.music_model.get_filtered_musics(
            tag_filter=tags_filter,
            min_stars=stars_filter,
            max_stars=stars_filter
        )


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