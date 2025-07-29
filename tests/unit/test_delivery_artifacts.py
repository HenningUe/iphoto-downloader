"""Tests for delivery artifacts management functionality."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from iphoto_downloader.delivery_artifacts import DeliveryArtifactsManager


class TestDeliveryArtifactsManager(unittest.TestCase):
    """Test cases for DeliveryArtifactsManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_folder = Path(self.temp_dir) / 'test_settings'
        
        # Create manager with mocked dependencies
        with patch('iphoto_downloader.delivery_artifacts.get_logger'), \
             patch('iphoto_downloader.delivery_artifacts.get_settings_folder_path', return_value=self.settings_folder):
            self.manager = DeliveryArtifactsManager()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test that DeliveryArtifactsManager initializes correctly."""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.settings_folder, self.settings_folder)

    @patch('iphoto_downloader.delivery_artifacts.get_operating_mode')
    def test_development_default_mode_behavior(self, mock_get_mode):
        """Test behavior in development mode (default)."""
        mock_get_mode.return_value = 'development'
        
        # Should return True (no operations needed) for development mode
        result = self.manager.handle_delivered_mode_startup()
        self.assertTrue(result)

    @patch('iphoto_downloader.delivery_artifacts.get_operating_mode')
    def test_executable_default_mode_behavior(self, mock_get_mode):
        """Test behavior in executable mode."""
        mock_get_mode.return_value = 'executable'
        
        # Should return True (no operations needed) for non-delivered modes
        result = self.manager.handle_delivered_mode_startup()
        self.assertTrue(result)

    @patch('iphoto_downloader.delivery_artifacts.get_operating_mode')
    def test_automatic_file_updates_in_delivered_mode(self, mock_get_mode):
        """Test automatic file updates in delivered mode."""
        mock_get_mode.return_value = 'delivered'
        
        # Mock the required methods
        with patch.object(self.manager, '_ensure_settings_folder_exists'), \
             patch.object(self.manager, '_check_required_files') as mock_check, \
             patch.object(self.manager, '_copy_missing_files'), \
             patch.object(self.manager, '_update_template_files'), \
             patch.object(self.manager, '_notify_user_about_copied_files'):
            
            mock_check.return_value = []  # No missing files
            
            result = self.manager.handle_delivered_mode_startup()
            self.assertTrue(result)

    def test_settings_folder_creation(self):
        """Test settings folder creation."""
        # Ensure folder doesn't exist
        if self.settings_folder.exists():
            import shutil
            shutil.rmtree(self.settings_folder)
        
        self.manager._ensure_settings_folder_exists()
        self.assertTrue(self.settings_folder.exists())

    def test_required_files_existence_checking(self):
        """Test checking for required files existence."""
        # Test operation files checking
        with patch('iphoto_downloader.delivery_artifacts.get_operating_mode') as mock_mode, \
             patch.object(self.manager, '_get_repository_readme_path') as mock_readme, \
             patch.object(self.manager, '_get_repository_env_example_path') as mock_env:
            
            mock_mode.return_value = 'delivered'
            mock_readme.return_value = Path('fake_readme.md')
            mock_env.return_value = Path('fake_env.example')
            
            missing_files = self.manager._check_required_files('operation')
            self.assertIsInstance(missing_files, list)

    def test_file_copying_mechanism(self):
        """Test file copying mechanism."""
        # Ensure settings folder exists
        self.settings_folder.mkdir(parents=True, exist_ok=True)
        
        # Use actual supported file names as Path objects (like the real implementation)
        missing_files = [
            {
                'src': Path('README.md'),
                'dest': self.settings_folder / 'README.md'
            }
        ]
        
        # Mock the repository path methods to return actual files
        with patch.object(self.manager, '_get_repository_readme_path') as mock_readme:
            readme_file = Path(self.temp_dir) / 'README.md'
            readme_file.write_text('# Test README')
            mock_readme.return_value = readme_file
            
            self.manager._copy_missing_files(missing_files)
            
            # Check if file was copied
            dst_file = self.settings_folder / 'README.md'
            self.assertTrue(dst_file.exists())

    def test_graceful_program_termination(self):
        """Test graceful program termination on critical errors."""
        with patch('iphoto_downloader.delivery_artifacts.get_operating_mode') as mock_mode, \
             patch.object(self.manager, '_ensure_settings_folder_exists') as mock_ensure:
            
            mock_mode.return_value = 'delivered'
            mock_ensure.side_effect = PermissionError("Access denied")
            
            # Should handle errors gracefully and return False
            result = self.manager.handle_delivered_mode_startup()
            self.assertFalse(result)

    def test_integration_with_packaging(self):
        """Test integration with packaging system."""
        # Test that manager can find resource files
        readme_path = self.manager._get_repository_readme_path()
        self.assertIsInstance(readme_path, Path)
        
        env_path = self.manager._get_repository_env_example_path()
        self.assertIsInstance(env_path, Path)

    @patch('iphoto_downloader.delivery_artifacts.get_operating_mode')
    def test_operating_mode_detection_delivered(self, mock_get_mode):
        """Test operating mode detection for delivered mode."""
        mock_get_mode.return_value = 'delivered'
        
        with patch.object(self.manager, '_ensure_settings_folder_exists'), \
             patch.object(self.manager, '_check_required_files', return_value=[]), \
             patch.object(self.manager, '_update_template_files'):
            
            result = self.manager.handle_delivered_mode_startup()
            self.assertTrue(result)

    @patch('iphoto_downloader.delivery_artifacts.get_operating_mode')
    def test_operating_mode_detection_development(self, mock_get_mode):
        """Test operating mode detection for development mode."""
        mock_get_mode.return_value = 'development'
        
        result = self.manager.handle_delivered_mode_startup()
        self.assertTrue(result)

    def test_settings_folder_detection_windows(self):
        """Test settings folder detection on Windows."""
        with patch('platform.system', return_value='Windows'), \
             patch('iphoto_downloader.delivery_artifacts.get_settings_folder_path') as mock_path:
            
            mock_path.return_value = Path('C:/Users/Test/AppData/Local/icloud-photo-sync/settings')
            
            # Create new manager to test folder detection
            with patch('iphoto_downloader.delivery_artifacts.get_logger'):
                manager = DeliveryArtifactsManager()
                self.assertIsInstance(manager.settings_folder, Path)

    def test_settings_folder_detection_linux(self):
        """Test settings folder detection on Linux."""
        with patch('platform.system', return_value='Linux'), \
             patch('iphoto_downloader.delivery_artifacts.get_settings_folder_path') as mock_path:
            
            mock_path.return_value = Path('/home/test/.config/icloud-photo-sync/settings')
            
            # Create new manager to test folder detection
            with patch('iphoto_downloader.delivery_artifacts.get_logger'):
                manager = DeliveryArtifactsManager()
                self.assertIsInstance(manager.settings_folder, Path)

    def test_settings_ini_creation_from_template(self):
        """Test settings.ini creation from template."""
        # Mock the _copy_file_from_resources method since it has specific logic
        with patch.object(self.manager, '_copy_file_from_resources') as mock_copy:
            template_defs = [
                {
                    'src': 'settings.ini.template',
                    'dest': self.settings_folder / 'settings.ini'
                }
            ]
            
            self.manager._update_template_files(template_defs)
            
            # Check that copy was attempted
            mock_copy.assert_called_once()

    def test_settings_ini_preservation(self):
        """Test preservation of existing settings.ini."""
        # Create existing settings.ini
        settings_file = self.settings_folder / 'settings.ini'
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        original_content = '[settings]\nexisting_key=existing_value'
        settings_file.write_text(original_content)
        
        # Try to update with template
        template_defs = [
            {
                'src': Path(self.temp_dir) / 'template.ini',
                'dest': settings_file
            }
        ]
        template_defs[0]['src'].write_text('[settings]\ntemplate_key=template_value')
        
        self.manager._update_template_files(template_defs)
        
        # Original content should be preserved if file exists
        content = settings_file.read_text()
        self.assertEqual(content, original_content)

    def test_user_notification_system(self):
        """Test user notification system."""
        copied_files = [
            {
                'src': Path('src.txt'),
                'dest': Path('dst.txt')
            }
        ]
        
        # Mock input to avoid stdin reading during tests
        with patch('builtins.input', return_value='n'):
            self.manager._notify_user_about_copied_files(copied_files)
