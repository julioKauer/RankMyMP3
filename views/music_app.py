import wx
import os
from views.folder_config_panel import FolderConfigPanel
from models.folder_model import FolderModel
from controllers.folder_controller import FolderController


class MusicApp(wx.Frame):
    def __init__(self, music_controller):
        super().__init__(None, title="Music Classifier", size=(800, 600))
        self.controller = music_controller

        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.compare_btn = wx.Button(self.panel, label="Começar a Comparar")
        self.compare_btn.Bind(wx.EVT_BUTTON, self.on_compare)
        vbox.Add(self.compare_btn, 0, wx.ALL | wx.CENTER, 10)

        self.ranking_btn = wx.Button(self.panel, label="Ver Ranking")
        self.ranking_btn.Bind(wx.EVT_BUTTON, self.on_ranking)
        vbox.Add(self.ranking_btn, 0, wx.ALL | wx.CENTER, 10)

        self.config_btn = wx.Button(self.panel, label="Configurações")
        self.config_btn.Bind(wx.EVT_BUTTON, self.on_open_folder_config)
        vbox.Add(self.config_btn, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(vbox)

        self.Centre()
        self.Show()

    def on_compare(self, event):
        music1, music2 = self.controller.get_next_comparison()
        if not music1 or not music2:
            wx.MessageBox('Não há músicas suficientes para comparar!', 'Info', wx.OK | wx.ICON_INFORMATION)
            return

        dlg = wx.SingleChoiceDialog(
            self, 'Qual preferes?',
            'Comparar', [os.path.basename(music1[1]), os.path.basename(music2[1])]
        )
        if dlg.ShowModal() == wx.ID_OK:
            choice = dlg.GetSelection()
            if choice == 0:
                self.controller.classify_music(music1[0], 5)
                self.controller.classify_music(music2[0], 4)
            else:
                self.controller.classify_music(music2[0], 5)
                self.controller.classify_music(music1[0], 4)
        dlg.Destroy()

    def on_ranking(self, event):
        ranking = self.controller.get_ranking()
        ranking_text = "\n".join([f"{stars} ★ - {os.path.basename(path)}" for path, stars in ranking])

        dlg = wx.MessageDialog(self, ranking_text, "Ranking", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_open_folder_config(self, event):
        """Open the folder configuration window."""
        folder_model = FolderModel()
        folder_controller = FolderController(folder_model)
        folder_config_frame = wx.Frame(self, title="Configuração de Pastas", size=(600, 400))
        FolderConfigPanel(folder_config_frame, folder_controller)
        folder_config_frame.Show()