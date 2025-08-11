import wx
import os
from views.folder_config_panel import FolderConfigPanel
from models.folder_model import FolderModel
from controllers.folder_controller import FolderController
from controllers.music_controller import MusicController


class MusicApp(wx.Frame):
    def __init__(self, music_controller: MusicController):
        super().__init__(None, title="Music Classifier", size=(800, 600))
        self.controller = music_controller

        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.add_button(vbox, "Começar a Comparar", self.on_compare)
        self.add_button(vbox, "Ver Ranking", self.on_ranking)
        self.add_button(vbox, "Configurações", self.on_open_folder_config)

        self.panel.SetSizer(vbox)

        self.Centre()
        self.Show()

    def add_button(self, sizer, label, handler):
        button = wx.Button(self.panel, label=label)
        button.Bind(wx.EVT_BUTTON, handler)
        sizer.Add(button, 0, wx.ALL | wx.CENTER, 10)

    def on_compare(self, event):
        # Obter o estado atual da comparação ou iniciar uma nova comparação
        state = self.controller.get_next_comparison()
        if not state:
            wx.MessageBox('Não há músicas suficientes para comparar!', 'Info', wx.OK | wx.ICON_INFORMATION)
            return

        unrated_music_id, compared_music_id, range_index = state

        # Obter os detalhes das músicas
        unrated_music = self.controller.get_music_details(unrated_music_id)
        compared_music = self.controller.get_music_details(compared_music_id)

        # Exibir o diálogo de comparação
        dlg = wx.SingleChoiceDialog(
            self, 'Qual preferes?',
            'Comparar', [os.path.basename(unrated_music['path']), os.path.basename(compared_music['path'])]
        )
        if dlg.ShowModal() == wx.ID_OK:
            choice = dlg.GetSelection()
            if choice == 0:
                self.controller.add_comparison(unrated_music_id, compared_music_id, unrated_music_id)
            else:
                self.controller.add_comparison(unrated_music_id, compared_music_id, compared_music_id)
        dlg.Destroy()

        # Atualizar o estado ou finalizar a classificação
        if self.controller.is_last_range(range_index):
            # Finalizar a classificação da música
            self.controller.finalize_classification(unrated_music_id)
            wx.MessageBox(f'A música "{os.path.basename(unrated_music["path"])}" foi classificada!', 'Info', wx.OK | wx.ICON_INFORMATION)
        else:
            # Avançar para o próximo range
            self.controller.update_comparison_state(unrated_music_id, range_index + 1)

    def on_open_folder_config(self, event):
        """Open the folder configuration window."""
        folder_model = FolderModel()
        folder_controller = FolderController(folder_model)
        folder_config_frame = wx.Frame(self, title="Configuração de Pastas", size=(600, 400))
        FolderConfigPanel(folder_config_frame, folder_controller)
        folder_config_frame.Show()

    def on_ranking(self, event):
        ranking = self.controller.get_ranking()
        ranking_text = "\n".join([f"{stars} ★ - {os.path.basename(path)}" for path, stars in ranking])

        dlg = wx.MessageDialog(self, ranking_text, "Ranking", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_reset_ranking(self, event):
        """Confirma e reseta o ranking."""
        confirm = wx.MessageBox(
            "Tem certeza que deseja resetar o ranking?",
            "Confirmação",
            wx.YES_NO | wx.ICON_WARNING
        )
        if confirm == wx.YES:
            self.controller.reset_ranking()