import os

class MusicController:
    def __init__(self, model):
        self.model = model

    def add_music_folder(self, folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.mp3'):
                    self.model.add_music(os.path.join(root, file))

    def classify_music(self, music_id, stars):
        self.model.update_stars(music_id, stars)

    def delete_music(self, music_id):
        self.model.delete_music(music_id)

    def get_next_comparison(self):
        musics = self.model.get_unrated_musics()
        if len(musics) >= 2:
            return musics[0], musics[1]
        return None, None

    def get_ranking(self, tag_filter=None):
        return self.model.get_ranking(tag_filter)

    def add_tag_to_music(self, music_id, tag_name):
        tag_id = self.model.add_tag(tag_name)
        self.model.associate_music_tag(music_id, tag_id)

    def get_music_by_tag(self, tag_name):
        return self.model.get_music_by_tag(tag_name)