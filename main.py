import wx
from controllers.music_controller import MusicController
from models.music_model import MusicModel  # Importa o modelo correto
from views.music_app import MusicApp

if __name__ == '__main__':
    app = wx.App()
    music_model = MusicModel()  # Inicializa o modelo
    music_controller = MusicController(model=music_model)  # Passa o modelo para o controlador
    main_frame = MusicApp(music_controller)
    main_frame.Show()
    app.MainLoop()