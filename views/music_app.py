import wx
import os
from controllers.music_controller import MusicController


class MusicApp(wx.Frame):
    def __init__(self, music_controller: MusicController):
        super().__init__(parent=None, title='RankMyMP3', size=(1000, 600))

        self.controller = music_controller

        # Criar o painel principal
        self.panel = wx.Panel(self)

        # Criar o layout principal (divisão horizontal)
        self.main_splitter = wx.SplitterWindow(self.panel)

        # Painel esquerdo (músicas não classificadas)
        self.left_panel = wx.Panel(self.main_splitter)
        self.unrated_list = wx.ListCtrl(
            self.left_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.unrated_list.InsertColumn(0, "Músicas Não Classificadas")
        self.unrated_list.SetColumnWidth(0, 500)

        # Painel direito (ranking)
        self.right_panel = wx.Panel(self.main_splitter)
        self.ranking_list = wx.ListCtrl(
            self.right_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.ranking_list.InsertColumn(0, "Posição")
        self.ranking_list.InsertColumn(1, "Música")
        self.ranking_list.InsertColumn(2, "Estrelas")
        self.ranking_list.SetColumnWidth(0, 70)
        self.ranking_list.SetColumnWidth(1, 500)
        self.ranking_list.SetColumnWidth(2, 200)

        # Área de comparação (inicialmente escondida)
        self.comparison_panel = wx.Panel(self.panel)
        self.comparison_panel.Hide()

        # Configurar layouts
        self._setup_menu()
        self._setup_layouts()
        self._setup_comparison_panel()
        self._setup_toolbar()
        self._setup_statusbar()

        # Atualizar as listas
        self.update_lists()

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

        # Layout do painel esquerdo
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self.left_panel, label="Músicas Não Classificadas:"), 0, wx.ALL, 5)
        left_sizer.Add(self.unrated_list, 1, wx.EXPAND | wx.ALL, 5)
        self.left_panel.SetSizer(left_sizer)

        # Layout do painel direito
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer.Add(wx.StaticText(self.right_panel, label="Ranking Atual:"), 0, wx.ALL, 5)
        right_sizer.Add(self.ranking_list, 1, wx.EXPAND | wx.ALL, 5)
        self.right_panel.SetSizer(right_sizer)

        # Adicionar splitter e painel de comparação ao layout principal
        main_sizer.Add(self.main_splitter, 1, wx.EXPAND)
        main_sizer.Add(self.comparison_panel, 0, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

    def _setup_comparison_panel(self):
        """Configura o painel de comparação."""
        # Definir um tamanho mínimo para o painel de comparação
        self.comparison_panel.SetMinSize((900, 400))  # Altura aumentada
        
        comparison_sizer = wx.BoxSizer(wx.VERTICAL)

        # Container para o título para garantir espaço adequado
        title_container = wx.Panel(self.comparison_panel)
        title_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Título da comparação
        self.comparison_title = wx.StaticText(
            title_container,
            label="Comparação em Andamento",
            style=wx.ALIGN_CENTER_HORIZONTAL
        )
        title_font = self.comparison_title.GetFont()
        title_font.SetPointSize(14)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.comparison_title.SetFont(title_font)
        
        # Adiciona espaço extra acima e abaixo do texto
        title_sizer.Add((-1, 5))  # Espaço superior
        title_sizer.Add(self.comparison_title, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        title_sizer.Add((-1, 10))  # Espaço inferior maior para a cedilha
        
        title_container.SetSizer(title_sizer)
        comparison_sizer.Add(title_container, 0, wx.EXPAND)

        # Área das músicas sendo comparadas com tamanho mínimo
        songs_sizer = wx.BoxSizer(wx.HORIZONTAL)
        songs_sizer.SetMinSize((780, 200))  # Altura reduzida

        # Música A
        self.song_a_panel = wx.Panel(self.comparison_panel)
        song_a_sizer = wx.BoxSizer(wx.VERTICAL)
        
                # Container para o nome da música A
        name_container_a = wx.Panel(self.song_a_panel)
        name_container_sizer_a = wx.BoxSizer(wx.VERTICAL)
        
        # Nome da música A com fonte maior
        self.song_a_name = wx.StaticText(name_container_a, label="", style=wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTER)
        font = self.song_a_name.GetFont()
        font.SetPointSize(12)  # Fonte maior
        font.SetWeight(wx.FONTWEIGHT_BOLD)  # Texto em negrito
        self.song_a_name.SetFont(font)
        self.song_a_name.Wrap(300)  # Largura máxima para wrap do texto
        name_container_sizer_a.Add(self.song_a_name, 1, wx.EXPAND | wx.ALL, 5)
        name_container_a.SetSizer(name_container_sizer_a)
        
        # Adiciona o container do nome com altura mínima
        song_a_sizer.Add(name_container_a, 0, wx.EXPAND | wx.ALL, 10)
        name_container_a.SetMinSize((-1, 60))  # Altura mínima para o nome
        
        # Botões da música A em um painel separado
        buttons_panel_a = wx.Panel(self.song_a_panel)
        song_a_buttons = wx.BoxSizer(wx.VERTICAL)
        
        self.song_a_button = wx.Button(buttons_panel_a, label="Prefiro Esta")
        self.song_a_button.SetMinSize((200, 40))  # Botões mais largos
        self.skip_a_button = wx.Button(buttons_panel_a, label="Pular Esta")
        self.skip_a_button.SetMinSize((200, 40))
        
        song_a_buttons.Add(self.song_a_button, 0, wx.EXPAND | wx.ALL, 5)
        song_a_buttons.Add(self.skip_a_button, 0, wx.EXPAND | wx.ALL, 5)
        buttons_panel_a.SetSizer(song_a_buttons)
        
        song_a_sizer.Add(buttons_panel_a, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.song_a_panel.SetSizer(song_a_sizer)

        # VS simplificado e menor
        vs_panel = wx.Panel(self.comparison_panel)
        vs_panel.SetMinSize((80, 80))  # Tamanho reduzido
        vs_sizer = wx.BoxSizer(wx.VERTICAL)
        
        vs_label = wx.StaticText(vs_panel, label="VS", style=wx.ALIGN_CENTER_HORIZONTAL)
        font = vs_label.GetFont()
        font.SetPointSize(12)  # Fonte um pouco menor
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        vs_label.SetFont(font)
        
        # Centraliza o VS diretamente no painel
        vs_sizer.AddStretchSpacer(1)
        vs_sizer.Add(vs_label, 0, wx.CENTER | wx.ALL, 5)
        vs_sizer.AddStretchSpacer(1)
        
        vs_panel.SetSizer(vs_sizer)

        # Música B
        self.song_b_panel = wx.Panel(self.comparison_panel)
        song_b_sizer = wx.BoxSizer(wx.VERTICAL)
        
                # Container para o nome da música B
        name_container_b = wx.Panel(self.song_b_panel)
        name_container_sizer_b = wx.BoxSizer(wx.VERTICAL)
        
        # Nome da música B com fonte maior
        self.song_b_name = wx.StaticText(name_container_b, label="", style=wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTER)
        font = self.song_b_name.GetFont()
        font.SetPointSize(12)  # Fonte maior
        font.SetWeight(wx.FONTWEIGHT_BOLD)  # Texto em negrito
        self.song_b_name.SetFont(font)
        self.song_b_name.Wrap(300)  # Largura máxima para wrap do texto
        name_container_sizer_b.Add(self.song_b_name, 1, wx.EXPAND | wx.ALL, 5)
        name_container_b.SetSizer(name_container_sizer_b)
        
        # Adiciona o container do nome com altura mínima
        song_b_sizer.Add(name_container_b, 0, wx.EXPAND | wx.ALL, 10)
        name_container_b.SetMinSize((-1, 60))  # Altura mínima para o nome
        
        # Botões da música B em um painel separado
        buttons_panel_b = wx.Panel(self.song_b_panel)
        song_b_buttons = wx.BoxSizer(wx.VERTICAL)
        
        self.song_b_button = wx.Button(buttons_panel_b, label="Prefiro Esta")
        self.song_b_button.SetMinSize((200, 40))  # Botões mais largos
        self.skip_b_button = wx.Button(buttons_panel_b, label="Pular Esta")
        self.skip_b_button.SetMinSize((200, 40))
        
        song_b_buttons.Add(self.song_b_button, 0, wx.EXPAND | wx.ALL, 5)
        song_b_buttons.Add(self.skip_b_button, 0, wx.EXPAND | wx.ALL, 5)
        buttons_panel_b.SetSizer(song_b_buttons)
        
        song_b_sizer.Add(buttons_panel_b, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.song_b_panel.SetSizer(song_b_sizer)

        # Adicionar elementos ao sizer horizontal com mais espaçamento e proporções fixas
        songs_sizer.Add(self.song_a_panel, 1, wx.EXPAND | wx.ALL, 20)
        songs_sizer.Add(vs_panel, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 30)
        songs_sizer.Add(self.song_b_panel, 1, wx.EXPAND | wx.ALL, 20)

        # Adicionar ao sizer principal do painel de comparação
        comparison_sizer.Add(songs_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # Progresso da comparação
        self.comparison_progress = wx.Gauge(self.comparison_panel, range=100)
        comparison_sizer.Add(self.comparison_progress, 0, wx.EXPAND | wx.ALL, 5)  # Padding reduzido

        # Botão para parar a comparação centralizado
        self.stop_comparison_button = wx.Button(self.comparison_panel, label="Parar Comparação")
        comparison_sizer.Add(self.stop_comparison_button, 0, wx.ALL | wx.CENTER, 5)  # Padding reduzido

        self.comparison_panel.SetSizer(comparison_sizer)

        # Bind eventos
        self.song_a_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_comparison_choice(0))
        self.song_b_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_comparison_choice(1))
        self.skip_a_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_skip_music(0))
        self.skip_b_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_skip_music(1))
        self.stop_comparison_button.Bind(wx.EVT_BUTTON, self.on_stop_comparison)

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

        # Botão de classificação (busca binária)
        start_comparison_tool = toolbar.AddTool(
            wx.ID_ANY,
            "Classificar Músicas",
            wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR),
            "Classificar próxima música usando busca binária inteligente"
        )

        toolbar.Realize()

        # Bind eventos
        self.Bind(wx.EVT_TOOL, self.on_add_folder, add_folder_tool)
        self.Bind(wx.EVT_TOOL, self.on_start_comparison, start_comparison_tool)

    def _setup_statusbar(self):
        """Configura a barra de status."""
        self.statusbar = self.CreateStatusBar(3)  # 3 seções: músicas, classificadas, pastas
        self.update_status()

    def update_lists(self):
        """Atualiza as listas de músicas não classificadas e ranking."""
        # Atualizar lista de músicas não classificadas
        self.unrated_list.DeleteAllItems()
        unrated_musics = self.controller.get_unrated_musics()
        for music in unrated_musics:
            index = self.unrated_list.GetItemCount()
            self.unrated_list.InsertItem(index, os.path.basename(music['path']))

        # Atualizar ranking usando ordenação topológica
        self.ranking_list.DeleteAllItems()
        ranked_musics = self.controller.get_classified_musics_topological()
        for position, music in enumerate(ranked_musics, 1):
            if music['stars'] is not None and music['stars'] > 0:  # Apenas músicas efetivamente classificadas
                index = self.ranking_list.GetItemCount()
                self.ranking_list.InsertItem(index, str(position))
                self.ranking_list.SetItem(index, 1, os.path.basename(music['path']))
                self.ranking_list.SetItem(index, 2, "★" * music['stars'])

    def update_status(self):
        """Atualiza a barra de status."""
        total_musics = self.controller.get_total_musics_count()
        rated_musics = self.controller.get_rated_musics_count()
        folder_count = self.controller.get_folder_count()
        self.statusbar.SetStatusText(f"Total de músicas: {total_musics}", 0)
        self.statusbar.SetStatusText(f"Classificadas: {rated_musics}", 1)
        self.statusbar.SetStatusText(f"Pastas: {folder_count}", 2)

    def start_comparison(self):
        """Inicia uma nova comparação."""
        print("DEBUG: start_comparison method called")
        try:
            print("DEBUG: About to call get_next_comparison")
            print(f"DEBUG: Controller exists: {self.controller is not None}")
            if not hasattr(self.controller, 'get_next_comparison'):
                print("DEBUG: Controller missing get_next_comparison method")
                return
            
            try:
                state = self.controller.get_next_comparison()
                print(f"DEBUG: get_next_comparison returned: {state}")
            except Exception as e:
                print(f"DEBUG: Exception in get_next_comparison: {e}")
                import traceback
                traceback.print_exc()
                wx.MessageBox(
                    f'Erro interno: {str(e)}',
                    'Erro',
                    wx.OK | wx.ICON_ERROR
                )
                return
            if not state:
                print("DEBUG: No valid state returned, showing message")
                self.comparison_panel.Hide()
                self.panel.Layout()
                wx.MessageBox(
                    'Não há mais músicas para comparar!',
                    'Finalizado',
                    wx.OK | wx.ICON_INFORMATION
                )
                return

            print("DEBUG: Valid state found, proceeding with comparison")
            music_a_id = state['unrated_music_id']
            music_b_id = state['compared_music_id'] 
            context = state['context']
            print(f"DEBUG: Getting details for music_a_id={music_a_id}, music_b_id={music_b_id}")
            music_a = self.controller.get_music_details(music_a_id)
            music_b = self.controller.get_music_details(music_b_id)
            print(f"DEBUG: music_a={music_a}, music_b={music_b}")
            
            if not music_a or not music_b:
                print("DEBUG: One or both music details are None")
                self.comparison_panel.Hide()
                self.panel.Layout()
                wx.MessageBox(
                    'Erro ao obter detalhes das músicas para comparação.',
                    'Erro',
                    wx.OK | wx.ICON_ERROR
                )
                return

            print("DEBUG: About to call _update_comparison_ui")
            self._update_comparison_ui(music_a, music_b, context)
        except Exception as e:
            print(f"DEBUG: Exception caught in start_comparison: {e}")
            import traceback
            traceback.print_exc()
            self.comparison_panel.Hide()
            self.panel.Layout()
            wx.MessageBox(
                f'Erro na comparação: {str(e)}',
                'Erro',
                wx.OK | wx.ICON_ERROR
            )

    def _update_comparison_ui(self, music_a, music_b, context):
        """Atualiza a interface de comparação."""
        print(f"DEBUG: _update_comparison_ui called with context={context}")
        try:
            # Atualizar nomes das músicas
            self.song_a_name.SetLabel(os.path.basename(music_a['path']))
            self.song_b_name.SetLabel(os.path.basename(music_b['path']))
            
            # Mostrar contexto da comparação
            if context == 'initial':
                context_text = "Comparação inicial - Qual música você prefere?"
            elif context == 'refinement':
                context_text = f"Refinamento - A: {music_a['stars']}⭐ vs B: {music_b['stars']}⭐"
            else:
                context_text = "Qual música você prefere?"
                
            # Se existe um label de contexto, atualizar (senão criar depois)
            if hasattr(self, 'context_label'):
                self.context_label.SetLabel(context_text)
            
            # Mostrar botão de skip apenas para músicas não classificadas (stars = 0)
            # Música A - mostrar skip se não foi classificada
            self.skip_a_button.Show(music_a['stars'] == 0)
            buttons_panel_a = self.skip_a_button.GetParent()
            buttons_panel_a.Layout()
            
            # Música B - mostrar skip apenas se não foi classificada
            self.skip_b_button.Show(music_b['stars'] == 0)
            buttons_panel_b = self.skip_b_button.GetParent()
            buttons_panel_b.Layout()
            
            print("DEBUG: About to show comparison panel")
            # Mostrar o painel de comparação
            self.comparison_panel.Show()
            self.panel.Layout()
            self.comparison_panel.Layout()
            self.comparison_panel.Refresh()
            self.panel.Layout()
            self.Layout()
            print("DEBUG: Comparison panel should be visible now")
        except Exception as e:
            print(f"DEBUG: Exception in _update_comparison_ui: {e}")
            import traceback
            traceback.print_exc()



    def on_comparison_choice(self, choice):
        """Lida com a escolha do usuário na comparação."""
        state = self.controller.get_current_comparison_state()
        if not state:
            return

        music_a_id = state['unrated_music_id']
        music_b_id = state['compared_music_id']
        context = state['context']
        
        # Determinar o vencedor baseado na escolha
        winner_id = music_a_id if choice == 0 else music_b_id
        
        # Registrar a comparação no sistema
        classification_finished = self.controller.make_comparison(music_a_id, music_b_id, winner_id)
        
        # Finalizar esta comparação (só limpa estado se foi finalizada)
        self._finalize_comparison(classification_finished)

    def _finalize_comparison(self, classification_finished=True):
        """Finaliza o processo de comparação."""
        self.comparison_panel.Hide()
        self.update_lists()
        self.update_status()
        
        # Só limpa o estado se a classificação foi finalizada
        if classification_finished:
            self.controller.clear_comparison_state()
        
        self.panel.Layout()
        
        # Verificar se há mais músicas para classificar apenas se a classificação foi finalizada
        if classification_finished:
            try:
                next_state = self.controller.get_next_comparison()
                if next_state:
                    wx.CallAfter(self.start_comparison)  # Inicia automaticamente a próxima comparação
                else:
                    wx.MessageBox('Todas as músicas foram classificadas!', 'Parabéns!', wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                # Se houver erro, assumir que acabaram as músicas
                wx.MessageBox('Todas as músicas foram classificadas!', 'Parabéns!', wx.OK | wx.ICON_INFORMATION)
        else:
            # Se a classificação não foi finalizada (skip), apenas inicia a próxima comparação
            wx.CallAfter(self.start_comparison)

    def on_add_folder(self, event):
        """Abre o diálogo para adicionar uma pasta de músicas."""
        with wx.DirDialog(self, "Selecione uma pasta de músicas") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.controller.add_music_folder(dlg.GetPath())
                self.update_lists()
                self.update_status()

    def on_start_comparison(self, event):
        """Inicia o processo de classificação por busca binária."""
        print("DEBUG: on_start_comparison button clicked")
        self.start_comparison()

    def on_stop_comparison(self, event):
        """Para o processo de comparação atual, mas mantém o progresso."""
        self.comparison_panel.Hide()
        self.update_lists()
        self.update_status()
        # Pausar comparação (manter progresso) em vez de limpar completamente
        self.controller.pause_comparison()
        self.panel.Layout()
        self.main_splitter.Layout()

    def on_skip_music(self, index):
        """
        Pula uma das músicas em comparação e avança para a próxima.
        :param index: 0 para música A, 1 para música B
        """
        state = self.controller.get_current_comparison_state()
        if not state:
            return

        music_a_id = state['unrated_music_id']
        music_b_id = state['compared_music_id'] 
        context = state['context']
        music_id = music_a_id if index == 0 else music_b_id
            
        # Marcar a música como pulada (-1 estrelas)
        self.controller.skip_music(music_id)
            
        # Limpar o estado atual de comparação para permitir nova busca
        self.controller.clear_comparison_state()
        
        # Avançar para próxima comparação (não limpar estado novamente)
        self._finalize_comparison(classification_finished=False)

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