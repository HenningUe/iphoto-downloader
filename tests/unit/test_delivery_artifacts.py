"""Tests for delivery artifacts management functionality."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from icloud_photo_sync.config import BaseConfig
from icloud_photo_sync.delivery_artifacts import DeliveryArtifactsManager


class TestDeliveryArtifactsManager(unittest.TestCase):
    """Test cases for DeliveryArtifactsManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_folder = Path(self.temp_dir) / 'test_settings'
        
        # Mock config
        self.mock_config = Mock(spec=BaseConfig)
        self.mock_config.operating_mode = 'Delivered'
        self.mock_config.get_settings_folder_path.return_value = self.settings_folder
        
        # Create manager
        with patch('icloud_photo_sync.delivery_artifacts.get_logger'):
            self.manager = DeliveryArtifactsManager(self.mock_config)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_operating_mode_detection_development(self):
        """Test operating mode detection in development environment."""
        with patch.dict(os.environ, {'OPERATING_MODE': 'InDevelopment'}):
            with patch('sys.frozen', False, create=True):
                config = Mock(spec=BaseConfig)
                config.operating_mode = 'InDevelopment'
                
                with patch('icloud_photo_sync.delivery_artifacts.get_logger'):
                    manager = DeliveryArtifactsManager(config)
                    result = manager.handle_delivered_mode_startup()
                    
                    # Should return True for InDevelopment mode
                    self.assertTrue(result)

    def test_operating_mode_detection_delivered(self):
        """Test operating mode detection in delivered environment."""
        with patch.dict(os.environ, {'OPERATING_MODE': 'Delivered'}):
            with patch('sys.frozen', True, create=True):
                with patch('sys._MEIPASS', '/tmp/test', create=True):
                    # Test with all files missing
                    self.mock_config.operating_mode = 'Delivered'
                    
                    with patch.object(self.manager, '_notify_user_about_copied_files'):
                        result = self.manager.handle_delivered_mode_startup()
                        
                        # Should return False when files need to be copied
                        self.assertFalse(result)

    def test_settings_folder_detection_windows(self):
        """Test settings folder detection on Windows."""
        with patch('os.name', 'nt'):
            with patch('os.path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = 'C:\\Users\\TestUser'
                
                from icloud_photo_sync.config import BaseConfig
                config = Mock(spec=BaseConfig)
                
                # Create a real config instance to test the method
                with patch('icloud_photo_sync.config.load_dotenv'):
                    with patch('icloud_photo_sync.config.os.getenv') as mock_getenv:
                        mock_getenv.side_effect = lambda key, default=None: {
                            'SYNC_DIRECTORY': './photos',
                            'DRY_RUN': 'false',
                            'LOG_LEVEL': 'INFO',
                            'MAX_DOWNLOADS': '0',
                            'MAX_FILE_SIZE_MB': '0',
                            'PUSHOVER_DEVICE': '',
                            'ENABLE_PUSHOVER': 'true',
                            'INCLUDE_PERSONAL_ALBUMS': 'true',
                            'INCLUDE_SHARED_ALBUMS': 'true',
                            'PERSONAL_ALBUM_NAMES_TO_INCLUDE': '',
                            'SHARED_ALBUM_NAMES_TO_INCLUDE': '',
                            'EXECUTION_MODE': 'single',
                            'SYNC_INTERVAL_MINUTES': '2',
                            'MAINTENANCE_INTERVAL_HOURS': '1',
                            'DATABASE_PARENT_DIRECTORY': '.data',
                            'OPERATING_MODE': 'Delivered'
                        }.get(key, default)
                        
                        from icloud_photo_sync.config import KeyringConfig
                        real_config = KeyringConfig(Path('.env'))
                        
                        settings_path = real_config.get_settings_folder_path()
                        expected_path = Path('C:\\Users\\TestUser') / 'icloud_photo_sync_settings'
                        self.assertEqual(settings_path, expected_path)

    def test_settings_folder_detection_linux(self):
        """Test settings folder detection on Linux."""
        with patch('os.name', 'posix'):
            with patch('os.path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = '/home/testuser/.config'
                
                from icloud_photo_sync.config import BaseConfig
                config = Mock(spec=BaseConfig)
                
                # Create a real config instance to test the method
                with patch('icloud_photo_sync.config.load_dotenv'):
                    with patch('icloud_photo_sync.config.os.getenv') as mock_getenv:
                        mock_getenv.side_effect = lambda key, default=None: {
                            'SYNC_DIRECTORY': './photos',
                            'DRY_RUN': 'false',
                            'LOG_LEVEL': 'INFO',
                            'MAX_DOWNLOADS': '0',
                            'MAX_FILE_SIZE_MB': '0',
                            'PUSHOVER_DEVICE': '',
                            'ENABLE_PUSHOVER': 'true',
                            'INCLUDE_PERSONAL_ALBUMS': 'true',
                            'INCLUDE_SHARED_ALBUMS': 'true',
                            'PERSONAL_ALBUM_NAMES_TO_INCLUDE': '',
                            'SHARED_ALBUM_NAMES_TO_INCLUDE': '',
                            'EXECUTION_MODE': 'single',
                            'SYNC_INTERVAL_MINUTES': '2',
                            'MAINTENANCE_INTERVAL_HOURS': '1',
                            'DATABASE_PARENT_DIRECTORY': '.data',
                            'OPERATING_MODE': 'Delivered'
                        }.get(key, default)
                        
                        from icloud_photo_sync.config import KeyringConfig
                        real_config = KeyringConfig(Path('.env'))
                        
                        settings_path = real_config.get_settings_folder_path()
                        expected_path = Path('/home/testuser/.config') / 'icloud_photo_sync_settings'
                        self.assertEqual(settings_path, expected_path)

    def test_required_files_existence_checking(self):
        """Test required files existence checking."""
        # No files exist initially
        missing_files = self.manager._check_required_files()
        expected_files = ['README.md', 'settings.ini.template', 'settings.ini']
        self.assertEqual(set(missing_files), set(expected_files))
        
        # Create some files
        self.settings_folder.mkdir(parents=True, exist_ok=True)
        (self.settings_folder / 'README.md').touch()
        (self.settings_folder / 'settings.ini').touch()
        
        missing_files = self.manager._check_required_files()
        self.assertEqual(missing_files, ['settings.ini.template'])

    def test_file_copying_mechanism(self):
        """Test file copying mechanism for missing artifacts."""
        self.settings_folder.mkdir(parents=True, exist_ok=True)
        
        # Test copying missing files
        missing_files = ['README.md', 'settings.ini.template']
        self.manager._copy_missing_files(missing_files)
        
        # Check that files were created
        self.assertTrue((self.settings_folder / 'README.md').exists())
        self.assertTrue((self.settings_folder / 'settings.ini.template').exists())
        
        # Check content of README.md (should contain repository content or fallback)
        readme_content = (self.settings_folder / 'README.md').read_text()
        self.assertIn('iCloud Photo Sync', readme_content)
        
        # Check content of settings.ini.template (should contain env content or fallback)
        template_content = (self.settings_folder / 'settings.ini.template').read_text()
        self.assertIn('SYNC_DIRECTORY', template_content)

    def test_settings_ini_creation_from_template(self):
        """Test settings.ini creation from template."""
        self.settings_folder.mkdir(parents=True, exist_ok=True)
        
        # Test creating settings.ini
        self.manager._create_settings_ini_from_template()
        
        settings_ini_path = self.settings_folder / 'settings.ini'
        self.assertTrue(settings_ini_path.exists())
        
        content = settings_ini_path.read_text()
        self.assertIn('SYNC_DIRECTORY=./photos', content)
        self.assertIn('OPERATING_MODE=Delivered', content)

    def test_settings_ini_preservation(self):
        """Test that existing settings.ini is never overwritten."""
        self.settings_folder.mkdir(parents=True, exist_ok=True)
        
        # Create existing settings.ini with custom content
        existing_content = "# Custom user settings\nSYNC_DIRECTORY=/my/custom/path\n"
        settings_ini_path = self.settings_folder / 'settings.ini'
        settings_ini_path.write_text(existing_content)
        
        # Try to create settings.ini from template
        self.manager._create_settings_ini_from_template()
        
        # Check that content is preserved
        content = settings_ini_path.read_text()
        self.assertEqual(content, existing_content)

    def test_user_notification_system(self):
        """Test user notification system for copied files."""
        copied_files = ['README.md', 'settings.ini.template', 'settings.ini']
        
        with patch('builtins.print') as mock_print:
            self.manager._notify_user_about_copied_files(copied_files)
            
            # Check that notification was printed
            mock_print.assert_called()
            print_calls = [str(call) for call in mock_print.call_args_list]
            notification_text = ''.join(print_calls)
            
            self.assertIn('FIRST TIME SETUP COMPLETE', notification_text)
            self.assertIn('README.md', notification_text)
            self.assertIn('settings.ini', notification_text)
            self.assertIn(str(self.settings_folder), notification_text)

    def test_graceful_program_termination(self):
        """Test graceful program termination after file copying."""
        # Mock all required files as missing
        with patch.object(self.manager, '_check_required_files') as mock_check:
            mock_check.return_value = ['README.md', 'settings.ini.template', 'settings.ini']
            
            with patch.object(self.manager, '_copy_missing_files'):
                with patch.object(self.manager, '_notify_user_about_copied_files'):
                    result = self.manager.handle_delivered_mode_startup()
                    
                    # Should return False to signal termination
                    self.assertFalse(result)

    def test_automatic_file_updates_in_delivered_mode(self):
        """Test automatic file updates in 'Delivered' mode."""
        self.settings_folder.mkdir(parents=True, exist_ok=True)
        
        # Create existing template files with old content
        old_readme_content = "Old README content"
        old_template_content = "Old template content"
        
        (self.settings_folder / 'README.md').write_text(old_readme_content)
        (self.settings_folder / 'settings.ini.template').write_text(old_template_content)
        
        # Update template files
        self.manager._update_template_files()
        
        # Check that files were updated
        new_readme_content = (self.settings_folder / 'README.md').read_text()
        new_template_content = (self.settings_folder / 'settings.ini.template').read_text()
        
        self.assertNotEqual(new_readme_content, old_readme_content)
        self.assertNotEqual(new_template_content, old_template_content)
        
        # Check that new content contains expected information
        self.assertIn('iCloud Photo Sync Tool', new_readme_content)
        self.assertIn('SYNC_DIRECTORY', new_template_content)

    def test_executable_default_mode_behavior(self):
        """Test that executable defaults to 'Delivered' mode."""
        with patch('sys.frozen', True, create=True):
            with patch('sys._MEIPASS', '/tmp/test', create=True):
                with patch('icloud_photo_sync.config.load_dotenv'):
                    with patch('icloud_photo_sync.config.os.getenv') as mock_getenv:
                        # Don't set OPERATING_MODE env var to test default behavior
                        mock_getenv.side_effect = lambda key, default=None: {
                            'SYNC_DIRECTORY': './photos',
                            'DRY_RUN': 'false',
                            'LOG_LEVEL': 'INFO',
                            'MAX_DOWNLOADS': '0',
                            'MAX_FILE_SIZE_MB': '0',
                            'PUSHOVER_DEVICE': '',
                            'ENABLE_PUSHOVER': 'true',
                            'INCLUDE_PERSONAL_ALBUMS': 'true',
                            'INCLUDE_SHARED_ALBUMS': 'true',
                            'PERSONAL_ALBUM_NAMES_TO_INCLUDE': '',
                            'SHARED_ALBUM_NAMES_TO_INCLUDE': '',
                            'EXECUTION_MODE': 'single',
                            'SYNC_INTERVAL_MINUTES': '2',
                            'MAINTENANCE_INTERVAL_HOURS': '1',
                            'DATABASE_PARENT_DIRECTORY': '.data'
                        }.get(key, default)
                        
                        from icloud_photo_sync.config import KeyringConfig
                        config = KeyringConfig(Path('.env'))
                        
                        # Should default to 'Delivered' mode when running from executable
                        self.assertEqual(config.operating_mode, 'Delivered')

    def test_development_default_mode_behavior(self):
        """Test that development environment defaults to 'InDevelopment' mode."""
        with patch('sys.frozen', False, create=True):
            with patch('icloud_photo_sync.config.load_dotenv'):
                with patch('icloud_photo_sync.config.os.getenv') as mock_getenv:
                    # Don't set OPERATING_MODE env var to test default behavior
                    mock_getenv.side_effect = lambda key, default=None: {
                        'SYNC_DIRECTORY': './photos',
                        'DRY_RUN': 'false',
                        'LOG_LEVEL': 'INFO',
                        'MAX_DOWNLOADS': '0',
                        'MAX_FILE_SIZE_MB': '0',
                        'PUSHOVER_DEVICE': '',
                        'ENABLE_PUSHOVER': 'true',
                        'INCLUDE_PERSONAL_ALBUMS': 'true',
                        'INCLUDE_SHARED_ALBUMS': 'true',
                        'PERSONAL_ALBUM_NAMES_TO_INCLUDE': '',
                        'SHARED_ALBUM_NAMES_TO_INCLUDE': '',
                        'EXECUTION_MODE': 'single',
                        'SYNC_INTERVAL_MINUTES': '2',
                        'MAINTENANCE_INTERVAL_HOURS': '1',
                        'DATABASE_PARENT_DIRECTORY': '.data'
                    }.get(key, default)
                    
                    from icloud_photo_sync.config import KeyringConfig
                    config = KeyringConfig(Path('.env'))
                    
                    # Should default to 'InDevelopment' mode when running from source
                    self.assertEqual(config.operating_mode, 'InDevelopment')

    def test_integration_with_packaging(self):
        """Test integration with PyInstaller packaging."""
        # This test verifies that the delivery artifacts system works
        # properly when running from a packaged executable
        
        with patch('sys.frozen', True, create=True):
            with patch('sys._MEIPASS', '/tmp/test_app', create=True):
                # Test that executable mode is detected
                config = Mock(spec=BaseConfig)
                config.operating_mode = 'Delivered'
                config.get_settings_folder_path.return_value = self.settings_folder
                
                with patch('icloud_photo_sync.delivery_artifacts.get_logger'):
                    manager = DeliveryArtifactsManager(config)
                    
                    # Should handle delivered mode properly
                    with patch.object(manager, '_notify_user_about_copied_files'):
                        result = manager.handle_delivered_mode_startup()
                        
                        # Files should be created in settings folder
                        self.assertTrue(self.settings_folder.exists())


if __name__ == '__main__':
    unittest.main()
