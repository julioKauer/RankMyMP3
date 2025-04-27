import wx
from wx.lib.agw.genericmessagedialog import GenericMessageDialog
from controllers.music_controller import MusicController
from models.music_model import MusicModel


class FolderConfigPanel(wx.Panel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Layout components
        self.folder_list = wx.ListBox(self, style=wx.LB_SINGLE)
        self.add_button = wx.Button(self, label="Adicionar Pasta")
        self.remove_button = wx.Button(self, label="Remover Pasta")
        self.save_button = wx.Button(self, label="Salvar Alterações")

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label="Pastas Selecionadas:"), 0, wx.ALL, 5)
        sizer.Add(self.folder_list, 1, wx.EXPAND | wx.ALL, 5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.add_button, 0, wx.ALL, 5)
        button_sizer.Add(self.remove_button, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.CENTER)
        sizer.Add(self.save_button, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(sizer)

        # Bind events
        self.add_button.Bind(wx.EVT_BUTTON, self.on_add_folder)
        self.remove_button.Bind(wx.EVT_BUTTON, self.on_remove_folder)
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save_folders)

        # Load initial data
        self.load_folders()

    def load_folders(self):
        """Load folders from the controller and display them."""
        self.folder_list.Clear()
        folders = self.controller.get_folders()
        self.folder_list.AppendItems(folders)

    def on_add_folder(self, event):
        """Handle adding a new folder."""
        with wx.DirDialog(self, "Selecione uma pasta", style=wx.DD_DEFAULT_STYLE) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                folder_path = dialog.GetPath()
                self.controller.add_folder(folder_path)  # Adiciona a pasta ao banco de dados

                # Adiciona os arquivos .mp3 da pasta ao banco de dados de músicas
                music_model = MusicModel()  # Inicializa o modelo de músicas
                music_controller = MusicController(music_model)
                music_controller.add_music_folder(folder_path)

                self.load_folders()

    def on_remove_folder(self, event):
        """Handle removing the selected folder."""
        selection = self.folder_list.GetSelection()
        if selection != wx.NOT_FOUND:
            folder_path = self.folder_list.GetString(selection)
            self.controller.remove_folder(folder_path)
            self.load_folders()
        else:
            dlg = GenericMessageDialog(self, "Nenhuma pasta selecionada para remover.", "Erro", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_save_folders(self, event):
        """Handle saving changes (folders are saved automatically)."""
        dlg = GenericMessageDialog(self, "Alterações salvas com sucesso!", "Sucesso", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()