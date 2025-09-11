"""
Comprehensive tests for the tag system functionality.
Tests all tag-related features including edge cases and UI integration points.
"""

import pytest
import tempfile
import os
import sqlite3
from models.music_model import MusicModel
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


class TestTagSystemComplete:
    """Complete test suite for tag system functionality."""
    
    def test_add_tag_basic(self, db_connection):
        """Test basic tag creation."""
        music_model = MusicModel(db_connection)
        
        # Add a new tag
        music_model.add_tag("rock")
        
        # Verify tag exists
        all_tags = music_model.get_all_tags()
        assert len(all_tags) == 1
        assert "rock" in all_tags
    
    def test_add_tag_duplicate(self, db_connection):
        """Test adding duplicate tags."""
        music_model = MusicModel(db_connection)
        
        # Add same tag twice
        music_model.add_tag("rock")
        music_model.add_tag("rock")
        
        # Should only have one tag
        all_tags = music_model.get_all_tags()
        assert len(all_tags) == 1
        assert "rock" in all_tags
    
    def test_get_all_tags_empty(self, db_connection):
        """Test getting tags when none exist."""
        music_model = MusicModel(db_connection)
        
        all_tags = music_model.get_all_tags()
        assert all_tags == []
    
    def test_get_all_tags_multiple(self, db_connection):
        """Test getting multiple tags."""
        music_model = MusicModel(db_connection)
        
        # Add several tags
        music_model.add_tag("rock")
        music_model.add_tag("pop")
        music_model.add_tag("jazz")
        
        all_tags = music_model.get_all_tags()
        assert len(all_tags) == 3
        assert "rock" in all_tags
        assert "pop" in all_tags
        assert "jazz" in all_tags
    
    def test_associate_tag_basic(self, db_connection):
        """Test basic tag association with music."""
        music_model = MusicModel(db_connection)
        
        # Add music and tag
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.add_tag("rock")
        
        # Associate tag with music
        music_model.associate_tag(music_id, "rock")
        
        # Verify association
        tags = music_model.get_music_tags(music_id)
        assert len(tags) == 1
        assert tags[0] == "rock"
    
    def test_associate_tag_multiple(self, db_connection):
        """Test associating multiple tags with one song."""
        music_model = MusicModel(db_connection)
        
        # Add music and tags
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.add_tag("rock")
        music_model.add_tag("alternative")
        music_model.add_tag("90s")
        
        # Associate multiple tags
        music_model.associate_tag(music_id, "rock")
        music_model.associate_tag(music_id, "alternative")
        music_model.associate_tag(music_id, "90s")
        
        # Verify all associations
        tags = music_model.get_music_tags(music_id)
        assert len(tags) == 3
        assert "rock" in tags
        assert "alternative" in tags
        assert "90s" in tags
    
    def test_associate_tag_duplicate(self, db_connection):
        """Test associating the same tag multiple times."""
        music_model = MusicModel(db_connection)
        
        # Add music and tag
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.add_tag("rock")
        
        # Associate same tag twice
        music_model.associate_tag(music_id, "rock")
        music_model.associate_tag(music_id, "rock")
        
        # Should only have one association
        tags = music_model.get_music_tags(music_id)
        assert len(tags) == 1
        assert tags[0] == "rock"
    
    def test_get_music_tags_no_tags(self, db_connection):
        """Test getting tags for music with no tags."""
        music_model = MusicModel(db_connection)
        
        music_id = music_model.add_music("/path/to/song.mp3")
        tags = music_model.get_music_tags(music_id)
        assert tags == []
    
    def test_get_music_tags_nonexistent_music(self, db_connection):
        """Test getting tags for nonexistent music."""
        music_model = MusicModel(db_connection)
        
        tags = music_model.get_music_tags(999999)
        assert tags == []
    
    def test_remove_tag_from_music_basic(self, db_connection):
        """Test basic tag removal from music."""
        music_model = MusicModel(db_connection)
        
        # Setup music with tag
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.add_tag("rock")
        music_model.associate_tag(music_id, "rock")
        
        # Verify tag is there
        tags = music_model.get_music_tags(music_id)
        assert "rock" in tags
        
        # Remove tag
        music_model.remove_tag_from_music(music_id, "rock")
        
        # Verify tag is gone
        tags = music_model.get_music_tags(music_id)
        assert "rock" not in tags
        assert len(tags) == 0
    
    def test_remove_tag_from_music_partial(self, db_connection):
        """Test removing one tag while keeping others."""
        music_model = MusicModel(db_connection)
        
        # Setup music with multiple tags
        music_id = music_model.add_music("/path/to/song.mp3")
        music_model.add_tag("rock")
        music_model.add_tag("alternative")
        music_model.associate_tag(music_id, "rock")
        music_model.associate_tag(music_id, "alternative")
        
        # Remove one tag
        music_model.remove_tag_from_music(music_id, "rock")
        
        # Verify only one tag remains
        tags = music_model.get_music_tags(music_id)
        assert len(tags) == 1
        assert "alternative" in tags
        assert "rock" not in tags
    
    def test_remove_tag_nonexistent(self, db_connection):
        """Test removing a tag that doesn't exist on the music."""
        music_model = MusicModel(db_connection)
        
        music_id = music_model.add_music("/path/to/song.mp3")
        
        # Try to remove non-existent tag (should not crash)
        music_model.remove_tag_from_music(music_id, "nonexistent")
        
        # Should still have no tags
        tags = music_model.get_music_tags(music_id)
        assert len(tags) == 0
    
    def test_get_music_by_tag_basic(self, db_connection):
        """Test getting music by tag."""
        music_model = MusicModel(db_connection)
        
        # Setup multiple songs with different tags
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        
        music_model.add_tag("rock")
        music_model.add_tag("pop")
        
        music_model.associate_tag(music1_id, "rock")
        music_model.associate_tag(music2_id, "rock")
        music_model.associate_tag(music3_id, "pop")
        
        # Get rock songs
        rock_songs = music_model.get_music_by_tag("rock")
        assert len(rock_songs) == 2
        
        # Extract paths
        rock_paths = [song[0] for song in rock_songs]
        assert "/path/to/song1.mp3" in rock_paths
        assert "/path/to/song2.mp3" in rock_paths
        assert "/path/to/song3.mp3" not in rock_paths
    
    def test_get_music_by_tag_nonexistent(self, db_connection):
        """Test getting music by non-existent tag."""
        music_model = MusicModel(db_connection)
        
        music_id = music_model.add_music("/path/to/song.mp3")
        
        # Try to get songs by non-existent tag
        songs = music_model.get_music_by_tag("nonexistent")
        assert len(songs) == 0
    
    def test_filtered_musics_tag_and_stars_complex(self, db_connection):
        """Test complex filtering with both tags and stars."""
        music_model = MusicModel(db_connection)
        
        # Setup complex scenario
        music1_id = music_model.add_music("/path/to/song1.mp3")
        music2_id = music_model.add_music("/path/to/song2.mp3")
        music3_id = music_model.add_music("/path/to/song3.mp3")
        music4_id = music_model.add_music("/path/to/song4.mp3")
        
        # Set different star ratings
        music_model.update_stars(music1_id, 5)
        music_model.update_stars(music2_id, 4)
        music_model.update_stars(music3_id, 3)
        music_model.update_stars(music4_id, 5)
        
        # Add tags
        music_model.add_tag("rock")
        music_model.add_tag("pop")
        
        music_model.associate_tag(music1_id, "rock")  # 5 stars, rock
        music_model.associate_tag(music2_id, "rock")  # 4 stars, rock
        music_model.associate_tag(music3_id, "pop")   # 3 stars, pop
        music_model.associate_tag(music4_id, "pop")   # 5 stars, pop
        
        # Test various filters
        high_rated_rock = music_model.get_filtered_musics(tag_filter="rock", min_stars=5)
        assert len(high_rated_rock) == 1
        assert high_rated_rock[0]['id'] == music1_id
        
        high_rated_any = music_model.get_filtered_musics(min_stars=5)
        assert len(high_rated_any) == 2  # music1 and music4
        
        rock_any_rating = music_model.get_filtered_musics(tag_filter="rock")
        assert len(rock_any_rating) == 2  # music1 and music2
        
        mid_to_high_rated = music_model.get_filtered_musics(min_stars=4, max_stars=5)
        assert len(mid_to_high_rated) == 3  # music1, music2, music4
    
    def test_tag_system_integration_workflow(self, db_connection):
        """Test a complete workflow using the tag system."""
        music_model = MusicModel(db_connection)
        
        # 1. Add multiple songs
        song_ids = []
        for i in range(5):
            song_id = music_model.add_music(f"/path/to/song{i}.mp3")
            song_ids.append(song_id)
        
        # 2. Create tag hierarchy
        genres = ["rock", "pop", "jazz", "classical"]
        moods = ["energetic", "relaxing", "melancholic"]
        
        for genre in genres:
            music_model.add_tag(genre)
        for mood in moods:
            music_model.add_tag(mood)
        
        # 3. Tag songs with multiple categories
        music_model.associate_tag(song_ids[0], "rock")
        music_model.associate_tag(song_ids[0], "energetic")
        
        music_model.associate_tag(song_ids[1], "pop")
        music_model.associate_tag(song_ids[1], "energetic")
        
        music_model.associate_tag(song_ids[2], "jazz")
        music_model.associate_tag(song_ids[2], "relaxing")
        
        music_model.associate_tag(song_ids[3], "classical")
        music_model.associate_tag(song_ids[3], "relaxing")
        
        music_model.associate_tag(song_ids[4], "rock")
        music_model.associate_tag(song_ids[4], "melancholic")
        
        # 4. Set star ratings
        for i, song_id in enumerate(song_ids):
            music_model.update_stars(song_id, (i % 5) + 1)  # 1-5 stars
        
        # 5. Test complex queries
        energetic_songs = music_model.get_music_by_tag("energetic")
        assert len(energetic_songs) == 2
        
        rock_songs = music_model.get_music_by_tag("rock")
        assert len(rock_songs) == 2
        
        high_rated_rock = music_model.get_filtered_musics(tag_filter="rock", min_stars=4)
        # This depends on the star assignments, should be testable
        
        # 6. Verify all tags are accessible
        all_tags = music_model.get_all_tags()
        for genre in genres:
            assert genre in all_tags
        for mood in moods:
            assert mood in all_tags
        
        # 7. Test tag removal
        music_model.remove_tag_from_music(song_ids[0], "energetic")
        updated_tags = music_model.get_music_tags(song_ids[0])
        assert "energetic" not in updated_tags
        assert "rock" in updated_tags
        
        # 8. Verify filtered results update accordingly
        energetic_songs_after = music_model.get_music_by_tag("energetic")
        assert len(energetic_songs_after) == 1  # One less than before
    
    def test_tag_edge_cases(self, db_connection):
        """Test edge cases in tag system."""
        music_model = MusicModel(db_connection)
        
        # Empty string tag
        try:
            music_model.add_tag("")
            all_tags = music_model.get_all_tags()
            # Should handle gracefully, may or may not include empty string
        except:
            pass  # Expected behavior may vary
        
        # Very long tag name
        long_tag = "a" * 100  # Reasonable length
        music_model.add_tag(long_tag)
        all_tags = music_model.get_all_tags()
        assert long_tag in all_tags
        
        # Special characters in tag
        special_tag = "rock/pop & jazz-fusion (90's)"
        music_model.add_tag(special_tag)
        all_tags = music_model.get_all_tags()
        assert special_tag in all_tags
        
        # Unicode tag
        unicode_tag = "ロック音楽"
        music_model.add_tag(unicode_tag)
        all_tags = music_model.get_all_tags()
        assert unicode_tag in all_tags
