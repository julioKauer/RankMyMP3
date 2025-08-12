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
        self._setup_layouts()
        self._setup_comparison_panel()
        self._setup_toolbar()
        self._setup_statusbar()

        # Atualizar as listas
        self.update_lists()

        self.Centre()
        self.Show()

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

        # Botão de iniciar comparações
        start_comparison_tool = toolbar.AddTool(
            wx.ID_ANY,
            "Iniciar Comparações",
            wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR),
            "Iniciar comparações"
        )

        toolbar.Realize()

        # Bind eventos
        self.Bind(wx.EVT_TOOL, self.on_add_folder, add_folder_tool)
        self.Bind(wx.EVT_TOOL, self.on_start_comparison, start_comparison_tool)

    def _setup_statusbar(self):
        """Configura a barra de status."""
        self.statusbar = self.CreateStatusBar(2)
        self.update_status()

    def update_lists(self):
        """Atualiza as listas de músicas não classificadas e ranking."""
        # Atualizar lista de músicas não classificadas
        self.unrated_list.DeleteAllItems()
        unrated_musics = self.controller.get_unrated_musics()
        for music in unrated_musics:
            index = self.unrated_list.GetItemCount()
            self.unrated_list.InsertItem(index, os.path.basename(music[1]))

        # Atualizar ranking (apenas músicas classificadas com stars > 0)
        self.ranking_list.DeleteAllItems()
        ranked_musics = self.controller.get_ranking()
        ranked_index = 1  # Contador para posição no ranking
        for music in ranked_musics:
            if music['stars'] is not None and music['stars'] > 0:  # Apenas músicas efetivamente classificadas
                index = self.ranking_list.GetItemCount()
                self.ranking_list.InsertItem(index, str(ranked_index))
                self.ranking_list.SetItem(index, 1, os.path.basename(music['path']))
                self.ranking_list.SetItem(index, 2, "★" * music['stars'])
                ranked_index += 1  # Incrementa apenas quando uma música é adicionada ao ranking

    def update_status(self):
        """Atualiza a barra de status."""
        total_musics = self.controller.get_total_musics_count()
        rated_musics = self.controller.get_rated_musics_count()
        self.statusbar.SetStatusText(f"Total de músicas: {total_musics}", 0)
        self.statusbar.SetStatusText(f"Músicas classificadas: {rated_musics}", 1)

    def start_comparison(self):
        """Inicia uma nova comparação usando estratégia descendente."""
        try:
            state = self.controller.get_next_comparison()
            if not state or len(state) != 3:
                self.comparison_panel.Hide()
                self.panel.Layout()
                wx.MessageBox(
                    'Não há mais músicas para comparar!',
                    'Finalizado',
                    wx.OK | wx.ICON_INFORMATION
                )
                return

            unrated_music_id, compared_music_id, star_level = state
            unrated_music = self.controller.get_music_details(unrated_music_id)
            compared_music = self.controller.get_music_details(compared_music_id)
            
            if not unrated_music or not compared_music:
                self.comparison_panel.Hide()
                self.panel.Layout()
                wx.MessageBox(
                    'Erro ao obter detalhes das músicas para comparação.',
                    'Erro',
                    wx.OK | wx.ICON_ERROR
                )
                return

            self._update_comparison_ui(unrated_music, compared_music, star_level)
        except Exception as e:
            self.comparison_panel.Hide()
            self.panel.Layout()
            wx.MessageBox(
                'Todas as músicas foram classificadas!',
                'Finalizado',
                wx.OK | wx.ICON_INFORMATION
            )

    def _update_comparison_ui(self, unrated_music, compared_music, star_level):
        """Atualiza a interface de comparação."""
        # Atualizar nomes das músicas
        self.song_a_name.SetLabel(os.path.basename(unrated_music['path']))
        
        # Se é uma comparação inicial (duas músicas não classificadas), não mostrar estrelas
        if compared_music['stars'] == 0:
            self.song_b_name.SetLabel(os.path.basename(compared_music['path']))
            self.comparison_title.SetLabel("Qual música você prefere?")
        else:
            # Comparação com música já classificada - mostrar nível de estrelas
            stars_text = "★" * compared_music['stars']
            self.song_b_name.SetLabel(f"{os.path.basename(compared_music['path'])} ({stars_text})")
            self.comparison_title.SetLabel(f"É melhor que uma música {compared_music['stars']} estrela{'s' if compared_music['stars'] > 1 else ''}?")
        
        self.song_a_name.GetParent().Layout()
        self.song_b_name.GetParent().Layout()

        # Verificar se a música B já foi classificada
        is_compared_music_rated = self.controller.is_music_rated(compared_music['id'])
        self.skip_b_button.Show(not is_compared_music_rated)
        buttons_panel_b = self.skip_b_button.GetParent()
        buttons_panel_b.Layout()
        
        # Calcular progresso baseado no nível atual (5→1)
        if compared_music['stars'] == 0:
            progress = 10  # Comparação inicial
        else:
            progress = (6 - star_level) * 20  # 20% por nível
        self.comparison_progress.SetValue(progress)
        
        self.comparison_panel.Show()
        self.song_a_panel.Layout()
        self.song_b_panel.Layout()
        self.comparison_panel.Layout()
        self.comparison_panel.Refresh()
        self.panel.Layout()
        self.Layout()

    def on_comparison_choice(self, choice):
        """Lida com a escolha do usuário na comparação descendente."""
        state = self.controller.get_current_comparison_state()
        if not state:
            return

        unrated_music_id, compared_music_id, star_level = state
        compared_music = self.controller.get_music_details(compared_music_id)

        # Se é uma comparação inicial (duas músicas não classificadas)
        if compared_music['stars'] == 0:
            if choice == 0:  # Escolheu a primeira música
                # Primeira música ganha, classifica como 3 estrelas e a segunda como 2
                self.controller.classify_music(unrated_music_id, 3)
                self.controller.classify_music(compared_music_id, 2)
            else:  # Escolheu a segunda música
                # Segunda música ganha, classifica como 3 estrelas e a primeira como 2
                self.controller.classify_music(compared_music_id, 3)
                self.controller.classify_music(unrated_music_id, 2)
            
            self._finalize_comparison()
            return

        # Comparação com música já classificada (estratégia descendente)
        if choice == 0:  # Escolheu a música não classificada
            # A música não classificada é melhor que a de X estrelas
            final_stars = min(star_level + 1, 5) if star_level < 5 else 5
            self.controller.classify_music(unrated_music_id, final_stars)
            self._finalize_comparison()
        else:  # Escolheu a música já classificada
            # A música não classificada não é melhor que a de X estrelas
            # Continua testando o próximo nível (X-1)
            next_state = self.controller.try_next_star_level(unrated_music_id, star_level - 1)
            if next_state:
                self.start_comparison()
            else:
                # Não há mais níveis, finaliza
                self._finalize_comparison()

    def _finalize_comparison(self):
        """Finaliza o processo de comparação."""
        self.comparison_panel.Hide()
        self.update_lists()
        self.update_status()
        self.controller.clear_comparison_state()
        self.panel.Layout()
        # Verificar se há mais músicas para classificar
        try:
            next_state = self.controller.get_next_comparison()
            if next_state and len(next_state) == 3:
                wx.CallAfter(self.start_comparison)  # Inicia automaticamente a próxima comparação
            else:
                wx.MessageBox('Todas as músicas foram classificadas!', 'Parabéns!', wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            # Se houver erro, assumir que acabaram as músicas
            wx.MessageBox('Todas as músicas foram classificadas!', 'Parabéns!', wx.OK | wx.ICON_INFORMATION)

    def on_add_folder(self, event):
        """Abre o diálogo para adicionar uma pasta de músicas."""
        with wx.DirDialog(self, "Selecione uma pasta de músicas") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.controller.add_music_folder(dlg.GetPath())
                self.update_lists()
                self.update_status()

    def on_start_comparison(self, event):
        """Inicia o processo de comparação."""
        self.start_comparison()

    def on_stop_comparison(self, event):
        """Para o processo de comparação atual."""
        self.comparison_panel.Hide()
        self.update_lists()
        self.update_status()
        self.controller.clear_comparison_state()
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

        unrated_music_id, compared_music_id, range_index = state
        music_id = unrated_music_id if index == 0 else compared_music_id
            
        # Atribuir -1 estrelas indica que a música foi pulada
        self.controller.classify_music(music_id, -1)
            
        if index == 0:  # Se pulou a música não classificada, vai para a próxima música não classificada
            self.update_lists()
            self.update_status()
            self.controller.clear_comparison_state()
            self.start_comparison()  # Inicia nova comparação com próxima música não classificada
        else:  # Se pulou a música de comparação, busca outra música no mesmo range
            try:
                next_compared_id = self.controller.get_representative_music(range_index, exclude_id=unrated_music_id)
                if next_compared_id:
                    self.controller.comparison_state_model.save_comparison_state(unrated_music_id, next_compared_id, range_index)
                    self.update_lists()  # Atualiza as listas antes de iniciar nova comparação
                    self.start_comparison()
                    # Força atualização do texto e layout dos botões da música B
                    self.song_b_name.GetParent().Layout()
                    self.song_b_panel.Layout()
                else:
                    # Se não há mais músicas neste range, avança para o próximo
                    if not self.controller.is_last_range(range_index):
                        self.controller.update_comparison_state(unrated_music_id, range_index + 1)
                        self.update_lists()  # Atualiza as listas antes de iniciar nova comparação
                        self.start_comparison()
                        self.song_b_name.GetParent().Layout()
                        self.song_b_panel.Layout()
                    else:
                        # Se não houver mais ranges, limpa o estado e atualiza a interface
                        self.controller.clear_comparison_state()
                        self.update_lists()
                        self.update_status()
                        self.comparison_panel.Hide()
                        self.panel.Layout()
                        # Finaliza a classificação desta música
                        self.controller.finalize_classification(unrated_music_id)
                        self.comparison_panel.Hide()
                        self.update_lists()
                        self.update_status()
                        self.controller.clear_comparison_state()
                        self.panel.Layout()
                        self.main_splitter.Layout()
            except ValueError:
                # Se não conseguir encontrar uma próxima música, trata como finalização
                self.controller.finalize_classification(unrated_music_id)
                self.comparison_panel.Hide()
                self.update_lists()
                self.update_status()
                self.controller.clear_comparison_state()
                self.panel.Layout()
                self.main_splitter.Layout()