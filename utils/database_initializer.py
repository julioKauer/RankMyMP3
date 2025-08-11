from sqlite3 import Connection

class DatabaseInitializer:
    def __init__(self, conn : Connection):
        self.conn = conn

    def create_tables(self):
        cursor = self.conn.cursor()

        # Tabela de músicas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                stars INTEGER DEFAULT 0
            )
        ''')

        # Tabela de tags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')

        # Tabela de associação música-tags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_tags (
                music_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY(music_id) REFERENCES music(id),
                FOREIGN KEY(tag_id) REFERENCES tags(id),
                UNIQUE(music_id, tag_id)
            )
        ''')

        # Tabela de comparações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparisons (
                music_a_id INTEGER,
                music_b_id INTEGER,
                winner_id INTEGER,
                PRIMARY KEY (music_a_id, music_b_id),
                FOREIGN KEY(music_a_id) REFERENCES music(id),
                FOREIGN KEY(music_b_id) REFERENCES music(id),
                FOREIGN KEY(winner_id) REFERENCES music(id)
            )
        ''')

        # Tabela de estado de comparação
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparison_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unrated_music_id INTEGER,
                compared_music_id INTEGER,
                range_index INTEGER,
                FOREIGN KEY(unrated_music_id) REFERENCES music(id),
                FOREIGN KEY(compared_music_id) REFERENCES music(id)
            )
        ''')

        self.conn.commit()