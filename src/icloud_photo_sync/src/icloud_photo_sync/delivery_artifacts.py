"""Delivery Artifacts Management for iCloud Photo Sync Tool."""

import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import BaseConfig

from .logger import get_logger


class DeliveryArtifactsManager:
    """Manages delivery artifacts for 'Delivered' operating mode."""
    
    REQUIRED_FILES = [
        'README.md',
        'settings.ini.template',
        'settings.ini'
    ]
    
    TEMPLATE_FILES = [
        'README.md',
        'settings.ini.template'
    ]
    
    def __init__(self, config: 'BaseConfig') -> None:
        """Initialize the delivery artifacts manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger()
        self.settings_folder = config.get_settings_folder_path()
        
    def handle_delivered_mode_startup(self) -> bool:
        """Handle startup operations for 'Delivered' mode.
        
        Returns:
            True if startup completed successfully, False if app should terminate
        """
        if self.config.operating_mode != 'Delivered':
            return True  # Nothing to do for InDevelopment mode
            
        self.logger.info("Running in 'Delivered' mode - checking delivery artifacts")
        
        # Ensure settings folder exists
        self._ensure_settings_folder_exists()
        
        # Check if required files exist
        missing_files = self._check_required_files()
        
        if missing_files:
            # Copy missing files and terminate
            self._copy_missing_files(missing_files)
            self._notify_user_about_copied_files(missing_files)
            return False  # Signal that app should terminate
            
        # Update template files on every startup
        self._update_template_files()
        
        return True  # Continue with normal operation
        
    def _ensure_settings_folder_exists(self) -> None:
        """Create settings folder if it doesn't exist."""
        try:
            self.settings_folder.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Settings folder ready: {self.settings_folder}")
        except Exception as e:
            self.logger.error(f"Failed to create settings folder {self.settings_folder}: {e}")
            raise
            
    def _check_required_files(self) -> list[str]:
        """Check which required files are missing.
        
        Returns:
            List of missing file names
        """
        missing_files = []
        
        for file_name in self.REQUIRED_FILES:
            file_path = self.settings_folder / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                self.logger.debug(f"Required file missing: {file_path}")
                
        return missing_files
        
    def _copy_missing_files(self, missing_files: list[str]) -> None:
        """Copy missing required files to settings folder.
        
        Args:
            missing_files: List of file names to copy
        """
        for file_name in missing_files:
            try:
                if file_name == 'settings.ini':
                    # Create empty settings.ini from template
                    self._create_settings_ini_from_template()
                else:
                    # Copy from embedded resources
                    self._copy_file_from_resources(file_name)
                    
                self.logger.info(f"Copied required file: {file_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to copy file {file_name}: {e}")
                raise
                
    def _update_template_files(self) -> None:
        """Update template files on every startup (overwrite existing)."""
        for file_name in self.TEMPLATE_FILES:
            try:
                self._copy_file_from_resources(file_name)
                self.logger.debug(f"Updated template file: {file_name}")
            except Exception as e:
                self.logger.warning(f"Failed to update template file {file_name}: {e}")
                
    def _copy_file_from_resources(self, file_name: str) -> None:
        """Copy a file from repository sources to settings folder.
        
        Args:
            file_name: Name of the file to copy
        """
        destination = self.settings_folder / file_name
        
        # Determine source file location from repository
        if file_name == 'README.md':
            source_file = self._get_repository_readme_path()
        elif file_name == 'settings.ini.template':
            source_file = self._get_repository_env_example_path()
        else:
            self.logger.error(f"Unknown file type for delivery: {file_name}")
            raise ValueError(f"Unsupported delivery file: {file_name}")
            
        if not source_file.exists():
            self.logger.error(f"Repository source file not found: {source_file}")
            raise FileNotFoundError(f"Required repository file missing: {source_file}")
            
        shutil.copy2(source_file, destination)
        self.logger.debug(f"Copied repository file {file_name} from {source_file}")
        
    def _get_repository_readme_path(self) -> Path:
        """Get path to repository README.md file.
        
        Returns:
            Path to the repository README.md
        """
        # Check if we're running from PyInstaller executable
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # In PyInstaller executable, files are embedded in _MEIPASS
            return Path(sys._MEIPASS) / 'README.md'  # type: ignore
        else:
            # In development, navigate to repository root
            current_dir = Path(__file__).parent
            # Navigate up from src/icloud_photo_sync/src/icloud_photo_sync/ to repository root
            repo_root = current_dir.parent.parent.parent.parent
            return repo_root / 'README.md'
            
    def _get_repository_env_example_path(self) -> Path:
        """Get path to repository .env.example file.
        
        Returns:
            Path to the repository .env.example
        """
        # Check if we're running from PyInstaller executable
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # In PyInstaller executable, files are embedded in _MEIPASS
            return Path(sys._MEIPASS) / '.env.example'  # type: ignore
        else:
            # In development, navigate to repository root
            current_dir = Path(__file__).parent
            # Navigate up from src/icloud_photo_sync/src/icloud_photo_sync/ to repository root
            repo_root = current_dir.parent.parent.parent.parent
            return repo_root / '.env.example'
    
    def _create_settings_ini_from_template(self) -> None:
        """Create initial settings.ini file with minimal settings."""
        settings_ini_path = self.settings_folder / 'settings.ini'
        
        # Only create if it doesn't exist (never overwrite existing settings)
        if settings_ini_path.exists():
            self.logger.debug("settings.ini already exists, preserving user settings")
            return
            
        initial_content = """# iCloud Photo Sync Tool - Personal Configuration
# Edit this file to customize your settings
# See settings.ini.template for all available options

SYNC_DIRECTORY=./photos
DRY_RUN=false
LOG_LEVEL=INFO
EXECUTION_MODE=single
OPERATING_MODE=Delivered
ENABLE_PUSHOVER=true
"""

        settings_ini_path.write_text(initial_content, encoding='utf-8')
        self.logger.info(f"Created initial settings.ini file: {settings_ini_path}")
        
    def _notify_user_about_copied_files(self, copied_files: list[str]) -> None:
        """Notify user about copied files and provide guidance.
        
        Args:
            copied_files: List of file names that were copied
        """
        print("\n" + "="*60)
        print("🚀 FIRST TIME SETUP COMPLETE")
        print("="*60)
        print(f"\nRequired configuration files have been created in:")
        print(f"📁 {self.settings_folder}")
        print(f"\nFiles created:")
        
        for file_name in copied_files:
            print(f"   ✅ {file_name}")
            
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Edit 'settings.ini' to configure your sync preferences")
        print(f"2. Review 'settings.ini.template' for all available options") 
        print(f"3. Run the application again to start syncing")
        print(f"\n💡 TIP: Your iCloud and Pushover credentials will be")
        print(f"   stored securely when you run the application.")
        print(f"\n🔧 Settings folder: {self.settings_folder}")
        print("="*60)
        
    def get_env_file_path(self) -> Path:
        """Get the path to the .env file based on operating mode.
        
        Returns:
            Path to the .env file to use
        """
        if self.config.operating_mode == 'Delivered':
            # In delivered mode, use settings.ini from settings folder
            return self.settings_folder / 'settings.ini'
        else:
            # In development mode, use .env from project root
            return Path('.env')
