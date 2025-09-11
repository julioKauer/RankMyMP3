import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from models.music_model import MusicModel
from models.comparison_model import ComparisonModel
from utils.database_initializer import DatabaseInitializer


@pytest.fixture
def db_connection():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
        temp_db_path = temp_file.name
    
    conn = sqlite3.connect(temp_db_path)
    db_init = DatabaseInitializer(conn)
    db_init.create_tables()
    
    yield conn
    
    conn.close()
    os.unlink(temp_db_path)


class TestMusicModelExtended:
    """Extended tests for MusicModel to improve coverage."""

    def test_delete_music_with_existing_file(self, db_connection):
        """Test deleting music with existing file."""
        music_model = MusicModel(db_connection)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"dummy audio data")
        
        try:
            # Add music to database
            music_id = music_model.add_music(temp_path)
            
            # Mock send2trash to avoid actual file deletion
            with patch('models.music_model.send2trash') as mock_send2trash:
                music_model.delete_music(music_id)
                mock_send2trash.assert_called_once_with(temp_path)
            
            # Verify music is deleted from database
            cursor = db_connection.cursor()
            cursor.execute('SELECT * FROM music WHERE id = ?', (music_id,))
            assert cursor.fetchone() is None
            
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_delete_music_with_nonexistent_file(self, db_connection):
        """Test deleting music when file doesn't exist."""
        music_model = MusicModel(db_connection)
        
        # Add music with non-existent path
        fake_path = "/nonexistent/path/to/music.mp3"
        cursor = db_connection.cursor()
        cursor.execute('INSERT INTO music (path, stars) VALUES (?, ?)', (fake_path, 0))
        db_connection.commit()
        music_id = cursor.lastrowid
        
        # Mock send2trash - should not be called for non-existent files
        with patch('models.music_model.send2trash') as mock_send2trash:
            music_model.delete_music(music_id)
            mock_send2trash.assert_not_called()
        
        # Verify music is deleted from database
        cursor.execute('SELECT * FROM music WHERE id = ?', (music_id,))
        assert cursor.fetchone() is None

    def test_get_filtered_musics_by_tag_only(self, db_connection):
        """Test filtering music by tag only."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Set different star ratings
        music_model.update_stars(music1_id, 3)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 5)
        
        # Add tags
        music_model.add_tag("rock")
        music_model.add_tag("pop")
        music_model.associate_tag(music1_id, "rock")
        music_model.associate_tag(music2_id, "rock")
        music_model.associate_tag(music3_id, "pop")
        
        # Filter by tag only
        rock_songs = music_model.get_filtered_musics(tag_filter="rock")
        assert len(rock_songs) == 2
        assert any(song['id'] == music1_id for song in rock_songs)
        assert any(song['id'] == music2_id for song in rock_songs)

    def test_get_filtered_musics_with_tag_and_stars(self, db_connection):
        """Test filtering music by both tag and stars."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Set different star ratings
        music_model.update_stars(music1_id, 3)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 5)
        
        # Add tags
        music_model.add_tag("rock")
        music_model.associate_tag(music1_id, "rock")
        music_model.associate_tag(music2_id, "rock")
        music_model.associate_tag(music3_id, "rock")
        
        # Filter by tag and minimum stars
        filtered_songs = music_model.get_filtered_musics(tag_filter="rock", min_stars=4)
        assert len(filtered_songs) == 2
        assert any(song['id'] == music2_id for song in filtered_songs)
        assert any(song['id'] == music3_id for song in filtered_songs)

    def test_get_filtered_musics_no_tag_with_stars(self, db_connection):
        """Test filtering music by stars only (no tag filter)."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        music4_id = music_model.add_music("/path/to/song4.mp3")
        
        # Set different star ratings (including skipped)
        music_model.update_stars(music1_id, 3)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 5)
        music_model.update_stars(music4_id, -1)  # Skipped
        
        # Filter by stars only (no tag)
        filtered_songs = music_model.get_filtered_musics(min_stars=4)
        assert len(filtered_songs) == 2
        assert any(song['id'] == music2_id for song in filtered_songs)
        assert any(song['id'] == music3_id for song in filtered_songs)
        # Skipped song should not be included
        assert not any(song['id'] == music4_id for song in filtered_songs)

    def test_associate_tag_with_nonexistent_tag(self, db_connection):
        """Test associating a tag that doesn't exist."""
        music_model = MusicModel(db_connection)
        
        music_id = music_model.add_music("/path/to/song.mp3")
        
        # Try to associate non-existent tag
        music_model.associate_tag(music_id, "nonexistent_tag")
        
        # Verify no association was created
        tags = music_model.get_music_tags(music_id)
        assert len(tags) == 0

    def test_get_music_by_tag(self, db_connection):
        """Test getting music by tag."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Set star ratings
        music_model.update_stars(music1_id, 3)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 5)
        
        # Add tags
        music_model.add_tag("rock")
        music_model.add_tag("pop")
        music_model.associate_tag(music1_id, "rock")
        music_model.associate_tag(music2_id, "rock")
        music_model.associate_tag(music3_id, "pop")
        
        # Get music by tag
        rock_songs = music_model.get_music_by_tag("rock")
        assert len(rock_songs) == 2
        
        pop_songs = music_model.get_music_by_tag("pop")
        assert len(pop_songs) == 1

    def test_get_music_by_stars_with_exclude(self, db_connection):
        """Test getting music by stars with exclusion."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Set same star ratings
        music_model.update_stars(music1_id, 4)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 5)
        
        # Get music by stars excluding one
        result = music_model.get_music_by_stars(4, exclude_id=music1_id)
        assert len(result) == 1
        assert result[0]['id'] == music2_id

    def test_get_music_by_stars_without_exclude(self, db_connection):
        """Test getting music by stars without exclusion."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        
        # Set same star ratings
        music_model.update_stars(music1_id, 4)
        music_model.update_stars(music2_id, 4)
        
        # Get music by stars without exclusion
        result = music_model.get_music_by_stars(4)
        assert len(result) == 2

    def test_get_next_unrated_music_with_exclude(self, db_connection):
        """Test getting unrated music with exclusion."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Keep all unrated (stars = 0)
        # update_stars would change stars, so we skip it
        
        # Get unrated music excluding one
        result = music_model.get_next_unrated_music(exclude_id=music1_id)
        assert result is not None
        assert result['id'] != music1_id
        assert result['stars'] == 0

    def test_get_next_unrated_music_without_exclude(self, db_connection):
        """Test getting unrated music without exclusion."""
        music_model = MusicModel(db_connection)
        
        # Add test data
        music_id = music_model.add_music("/path/to/song.mp3")
        
        # Get unrated music without exclusion
        result = music_model.get_next_unrated_music()
        assert result is not None
        assert result['id'] == music_id
        assert result['stars'] == 0

    def test_get_next_unrated_music_when_none_exists(self, db_connection):
        """Test getting unrated music when none exists."""
        music_model = MusicModel(db_connection)
        
        # Add music and rate it
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.update_stars(music_id, 3)
        
        # Try to get unrated music
        result = music_model.get_next_unrated_music()
        assert result is None

    def test_get_all_classified_musics_with_comparisons(self, db_connection):
        """Test getting classified musics when comparisons exist."""
        music_model = MusicModel(db_connection)
        comparison_model = ComparisonModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Set star ratings
        music_model.update_stars(music1_id, 5)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 3)
        
        # Add comparisons to create ranking
        comparison_model.save_comparison(music1_id, music2_id, music1_id)
        comparison_model.save_comparison(music2_id, music3_id, music2_id)
        
        # Get classified musics
        classified = music_model.get_all_classified_musics()
        assert len(classified) == 3

    def test_build_ranking_from_comparisons_empty(self, db_connection):
        """Test building ranking when no comparisons exist."""
        music_model = MusicModel(db_connection)
        comparison_model = ComparisonModel(db_connection)
        
        # Test with no comparisons
        ranking = music_model._build_ranking_from_comparisons(comparison_model)
        assert ranking == []

    def test_build_ranking_from_comparisons_with_data(self, db_connection):
        """Test building ranking from existing comparisons."""
        music_model = MusicModel(db_connection)
        comparison_model = ComparisonModel(db_connection)
        
        # Add test data
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        # Add comparisons: 1 > 2 > 3
        comparison_model.save_comparison(music1_id, music2_id, music1_id)
        comparison_model.save_comparison(music2_id, music3_id, music2_id)
        comparison_model.save_comparison(music1_id, music3_id, music1_id)
        
        # Build ranking
        ranking = music_model._build_ranking_from_comparisons(comparison_model)
        
        # Verify order (music1 should be first)
        assert music1_id in ranking
        assert music2_id in ranking
        assert music3_id in ranking
        assert ranking.index(music1_id) < ranking.index(music2_id)
        assert ranking.index(music2_id) < ranking.index(music3_id)

    def test_get_music_by_id_existing(self, db_connection):
        """Test getting music by existing ID."""
        music_model = MusicModel(db_connection)
        
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.update_stars(music_id, 4)
        
        result = music_model.get_music_by_id(music_id)
        assert result is not None
        assert result['id'] == music_id
        assert result['path'] == "/path/to/song.mp3"
        assert result['stars'] == 4

    def test_get_music_by_id_nonexistent(self, db_connection):
        """Test getting music by non-existent ID."""
        music_model = MusicModel(db_connection)
        
        result = music_model.get_music_by_id(99999)
        assert result is None
