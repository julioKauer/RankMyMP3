import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from controllers.music_controller import MusicController
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


class TestMusicControllerExtended:
    """Extended tests for MusicController to improve coverage."""

    def test_init_with_string_path(self):
        """Test initialization with string path."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_db_path = temp_file.name
        
        try:
            controller = MusicController(temp_db_path)
            assert controller.owns_connection is True
            assert controller.db_path == temp_db_path
            controller.conn.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_init_with_connection_object(self, db_connection):
        """Test initialization with connection object."""
        controller = MusicController(db_connection)
        assert controller.owns_connection is False
        assert controller.db_path == "data/music_ranking.db"  # default

    def test_add_music_folder_new_folder(self, db_connection):
        """Test adding a new folder that doesn't exist in database."""
        controller = MusicController(db_connection)
        
        # Create temporary directory with MP3 files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create fake MP3 files
            mp3_file1 = os.path.join(temp_dir, "song1.mp3")
            mp3_file2 = os.path.join(temp_dir, "song2.mp3")
            
            with open(mp3_file1, 'w') as f:
                f.write("fake mp3 content")
            with open(mp3_file2, 'w') as f:
                f.write("fake mp3 content")
            
            # Mock folder_exists to return False (new folder)
            with patch.object(controller.folder_model, 'folder_exists', return_value=False), \
                 patch.object(controller.folder_model, 'add_folder') as mock_add_folder:
                
                result = controller.add_music_folder(temp_dir)
                
                # Verify folder was added
                mock_add_folder.assert_called_once_with(temp_dir)
                assert result == 2  # 2 MP3 files added

    def test_add_music_folder_existing_folder(self, db_connection):
        """Test adding a folder that already exists in database."""
        controller = MusicController(db_connection)
        
        # Create temporary directory with MP3 files
        with tempfile.TemporaryDirectory() as temp_dir:
            mp3_file = os.path.join(temp_dir, "song.mp3")
            with open(mp3_file, 'w') as f:
                f.write("fake mp3 content")
            
            # Mock folder_exists to return True (existing folder)
            with patch.object(controller.folder_model, 'folder_exists', return_value=True), \
                 patch.object(controller.folder_model, 'add_folder') as mock_add_folder:
                
                result = controller.add_music_folder(temp_dir)
                
                # Verify folder was not added again
                mock_add_folder.assert_not_called()
                assert result == 1  # 1 MP3 file still processed

    def test_validate_consistency_with_errors(self, db_connection):
        """Test consistency validation when there are errors."""
        controller = MusicController(db_connection)
        
        # Add some test data
        music1_id = controller.music_model.add_music("/path/to/song1.mp3")
        music2_id = controller.music_model.add_music("/path/to/song2.mp3")
        
        # Create inconsistent comparisons
        controller.comparison_model.save_comparison(music1_id, music2_id, music1_id)
        controller.comparison_model.save_comparison(music2_id, music1_id, music2_id)
        
        # This should detect and fix the inconsistency
        with patch('builtins.print') as mock_print:
            controller._validate_consistency()
            
            # Verify that inconsistency was detected and logged
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("Removed inconsistent comparisons" in call for call in print_calls)

    def test_validate_consistency_normal_flow(self, db_connection):
        """Test consistency validation normal flow."""
        controller = MusicController(db_connection)
        
        # Add some test data
        music1_id = controller.music_model.add_music("/path/to/song1.mp3")
        music2_id = controller.music_model.add_music("/path/to/song2.mp3")
        
        # Test normal flow - no inconsistencies
        controller._validate_consistency()
        
        # Should complete without error
        assert True

    def test_process_binary_search_step_no_state(self, db_connection):
        """Test binary search step when no state exists."""
        controller = MusicController(db_connection)
        
        # Mock get_comparison_state to return None
        with patch.object(controller.comparison_state_model, 'get_comparison_state', return_value=None):
            result = controller._process_binary_search_step(1)
            assert result is True

    def test_process_binary_search_step_initial_comparison_winner_wins(self, db_connection):
        """Test initial comparison where winner_id wins."""
        controller = MusicController(db_connection)
        
        # Add test music
        music1_id = controller.music_model.add_music("/path/to/song1.mp3")
        music2_id = controller.music_model.add_music("/path/to/song2.mp3")
        
        # Mock comparison state for initial comparison
        mock_state = {
            'unrated_music_id': music1_id,
            'compared_music_id': music2_id,
            'context': 'initial_comparison_test'
        }
        
        with patch.object(controller.comparison_state_model, 'get_comparison_state', return_value=mock_state), \
             patch.object(controller, '_insert_music_at_position') as mock_insert, \
             patch.object(controller.comparison_state_model, 'clear_comparison_state') as mock_clear, \
             patch('builtins.print'):
            
            result = controller._process_binary_search_step(music1_id)
            
            # Verify correct positioning
            assert mock_insert.call_count == 2
            mock_insert.assert_any_call(music1_id, 0)  # winner at position 0
            mock_insert.assert_any_call(music2_id, 1)  # loser at position 1
            mock_clear.assert_called_once()
            assert result is True

    def test_process_binary_search_step_initial_comparison_winner_loses(self, db_connection):
        """Test initial comparison where winner_id loses."""
        controller = MusicController(db_connection)
        
        # Add test music
        music1_id = controller.music_model.add_music("/path/to/song1.mp3")
        music2_id = controller.music_model.add_music("/path/to/song2.mp3")
        
        # Mock comparison state for initial comparison
        mock_state = {
            'unrated_music_id': music1_id,
            'compared_music_id': music2_id,
            'context': 'initial_comparison_test'
        }
        
        with patch.object(controller.comparison_state_model, 'get_comparison_state', return_value=mock_state), \
             patch.object(controller, '_insert_music_at_position') as mock_insert, \
             patch.object(controller.comparison_state_model, 'clear_comparison_state') as mock_clear, \
             patch('builtins.print'):
            
            result = controller._process_binary_search_step(music2_id)  # compared_music wins
            
            # Verify correct positioning (compared_music wins)
            assert mock_insert.call_count == 2
            mock_insert.assert_any_call(music2_id, 0)  # winner at position 0
            mock_insert.assert_any_call(music1_id, 1)  # loser at position 1
            mock_clear.assert_called_once()
            assert result is True

    def test_process_binary_search_step_with_proper_context(self, db_connection):
        """Test binary search step with proper context format."""
        controller = MusicController(db_connection)
        
        # Add test music
        music1_id = controller.music_model.add_music("/path/to/song1.mp3")
        music2_id = controller.music_model.add_music("/path/to/song2.mp3")
        
        # Mock comparison state with proper binary search context
        mock_state = {
            'unrated_music_id': music1_id,
            'compared_music_id': music2_id,
            'context': 'binary_search_0_5_2'  # low=0, high=5, comparisons=2
        }
        
        with patch.object(controller.comparison_state_model, 'get_comparison_state', return_value=mock_state), \
             patch('builtins.print') as mock_print:
            
            # This should continue binary search rather than finish
            result = controller._process_binary_search_step(music1_id)
            
            # Verify debug prints were called
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("Binary search step" in call for call in print_calls)

    def test_process_binary_search_step_fallback_context(self, db_connection):
        """Test binary search step with fallback context parsing."""
        controller = MusicController(db_connection)
        
        # Add test music
        music1_id = controller.music_model.add_music("/path/to/song1.mp3")
        music2_id = controller.music_model.add_music("/path/to/song2.mp3")
        
        # Mock comparison state with incomplete context (triggers fallback)
        mock_state = {
            'unrated_music_id': music1_id,
            'compared_music_id': music2_id,
            'context': 'invalid_format'  # Should trigger fallback
        }
        
        with patch.object(controller.comparison_state_model, 'get_comparison_state', return_value=mock_state), \
             patch.object(controller, '_build_ranking_from_comparisons', return_value=[music2_id]), \
             patch('builtins.print') as mock_print:
            
            result = controller._process_binary_search_step(music1_id)
            
            # Verify fallback was used
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("Binary search step" in call for call in print_calls)

    def test_get_next_comparison_normal_flow(self, db_connection):
        """Test get_next_comparison normal flow."""
        controller = MusicController(db_connection)
        
        # Add test music
        music_id = controller.music_model.add_music("/path/to/song.mp3")
        
        # Test normal flow
        result = controller.get_next_comparison()
        assert result is None  # Only one music, should auto-classify

    def test_start_binary_search_normal_flow(self, db_connection):
        """Test _start_binary_search normal flow."""
        controller = MusicController(db_connection)
        
        music_id = controller.music_model.add_music("/path/to/song.mp3")
        
        # Test normal flow - should auto-classify single music
        result = controller._start_binary_search(music_id)
        assert result is None

    def test_build_ranking_from_comparisons_normal_flow(self, db_connection):
        """Test _build_ranking_from_comparisons normal flow."""
        controller = MusicController(db_connection)
        
        # Test normal flow - empty ranking
        result = controller._build_ranking_from_comparisons()
        assert result == []

    def test_get_existing_comparison_normal_flow(self, db_connection):
        """Test _get_existing_comparison normal flow."""
        controller = MusicController(db_connection)
        
        # Test normal flow - no existing comparison
        result = controller._get_existing_comparison(1, 2)
        assert result is None

    def test_insert_music_at_position_normal_flow(self, db_connection):
        """Test _insert_music_at_position normal flow."""
        controller = MusicController(db_connection)
        
        music_id = controller.music_model.add_music("/path/to/song.mp3")
        
        # Test normal flow
        controller._insert_music_at_position(music_id, 0)
        
        # Verify music was updated
        details = controller.music_model.get_music_details(music_id)
        assert details['stars'] > 0

    def test_create_positioning_comparisons_normal_flow(self, db_connection):
        """Test _create_positioning_comparisons normal flow."""
        controller = MusicController(db_connection)
        
        music_id = controller.music_model.add_music("/path/to/song.mp3")
        other_id = controller.music_model.add_music("/path/to/other.mp3")
        
        # Test normal flow
        controller._create_positioning_comparisons(music_id, [other_id], 0)
        
        # Should complete without error
        assert True

    def test_redistribute_all_stars_normal_flow(self, db_connection):
        """Test _redistribute_all_stars normal flow."""
        controller = MusicController(db_connection)
        
        music_id = controller.music_model.add_music("/path/to/song.mp3")
        
        # Test normal flow
        controller._redistribute_all_stars([music_id])
        
        # Verify music was updated
        details = controller.music_model.get_music_details(music_id)
        assert details['stars'] > 0
