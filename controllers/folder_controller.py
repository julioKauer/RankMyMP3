class FolderController:
    def __init__(self, model):
        self.model = model

    def get_folders(self):
        """Retrieve the list of folders from the model."""
        return self.model.get_folders()

    def add_folder(self, folder_path):
        """Add a folder through the model."""
        self.model.add_folder(folder_path)

    def remove_folder(self, folder_path):
        """Remove a folder through the model."""
        self.model.remove_folder(folder_path)