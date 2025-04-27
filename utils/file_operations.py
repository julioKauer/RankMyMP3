import os
import shutil
from send2trash import send2trash

def move_file_to_trash(file_path):
    """Move a file to the trash."""
    if os.path.exists(file_path):
        send2trash(file_path)

def move_file(source_path, destination_path):
    """Move a file from source to destination."""
    if os.path.exists(source_path):
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        os.rename(source_path, destination_path)

def copy_file(source_path, destination_path):
    """Copy a file from source to destination."""
    if os.path.exists(source_path):
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.copy2(source_path, destination_path)

def delete_file(file_path):
    """Delete a file permanently."""
    if os.path.exists(file_path):
        os.remove(file_path)