import sqlite3
import wx
from controllers.music_controller import MusicController
from views.music_app import MusicApp
from utils.database_initializer import DatabaseInitializer  # Importa o inicializador do banco de dados

if __name__ == '__main__':
    app = wx.App()
    conn = sqlite3.connect("data/music_ranking.db")

    # Inicializar o banco de dados
    db_initializer = DatabaseInitializer(conn)
    db_initializer.create_tables()

    # Criar o controlador
    controller = MusicController(conn)

    # Iniciar a aplicação (exemplo)
    main_frame = MusicApp(controller)
    main_frame.Show()
    app.MainLoop()