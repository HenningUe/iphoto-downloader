"""Delivery Artifacts Management for iCloud Photo Sync Tool."""

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .config import BaseConfig, get_settings_folder_path

from .logger import get_logger


class DeliveryArtifactsManager:
    """Manages delivery artifacts for 'Delivered' operating mode."""
    
    ARTEFACT_FILES = [
        {'src': 'README.md'},
        {'src': '.env.example',
         'dest': [
             {'operation_mode': 'delivered',
              'file': 'settings.ini',
              'template': 'settings.ini.template',
              }]},
    ]
    
    def __init__(self, config: 'BaseConfig') -> None:
        """Initialize the delivery artifacts manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger()
        self.settings_folder = get_settings_folder_path()
        
    def handle_delivered_mode_startup(self) -> bool:
        """Handle startup operations for 'Delivered' mode.
        
        Returns:
            True if startup completed successfully, False if app should terminate
        """
        if self.config.operating_mode != 'Delivered':
            return True  # Nothing to do for InDevelopment mode

        self.logger.info(f"Running in '{self.config.operating_mode}' mode - "
                         f"checking delivery artifacts")

        # Ensure settings folder exists
        self._ensure_settings_folder_exists()
            
        # Update template files on every startup
        required_template_file_defs = self._check_required_files("template")
        self._update_template_files(required_template_file_defs)
        
        # Check if required files exist
        missing_file_defs = self._check_required_files("operation")
        if missing_file_defs:
            # Copy missing files and terminate
            self._copy_missing_files(missing_file_defs)
            self._notify_user_about_copied_files(missing_file_defs)
            return False  # Signal that app should terminate

        return True  # Continue with normal operation
        
    def _ensure_settings_folder_exists(self) -> None:
        """Create settings folder if it doesn't exist."""
        try:
            self.settings_folder.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Settings folder ready: {self.settings_folder}")
        except Exception as e:
            self.logger.error(f"Failed to create settings folder {self.settings_folder}: {e}")
            raise
            
    def _check_required_files(
        self,
        dst_file_type: str) -> list[dict[str, Path]]:
        """Check which required files are missing.
        
        Returns:
            List of missing file definitions
        """
        
        assert dst_file_type in ['operation', 'template'], \
            "dst_file_type must be 'operation' or 'template'"

        required_files = []
        
        cfg = self.config
        cfg.operating_mode  #Operating mode: "InDevelopment" or "Delivered"
        
        for file_def in self.ARTEFACT_FILES:
            dst_file = None
            for dst_def in file_def.get('dest', []):
                if isinstance(dst_def, dict) \
                        and dst_def.get('operation_mode') == cfg.operating_mode:
                    if dst_file_type == 'operation':
                        dst_file = dst_def.get('file', file_def['src'])
                    elif dst_file_type == 'template' and 'template' in dst_def:
                        dst_file = dst_def['template']
                    break
                else:
                    raise ValueError(f"Unsupported delivery file: {dst_def}")
            if dst_file is None and dst_file_type == 'operation':
                dst_file = file_def['src']
            elif dst_file is None:
                continue
            dst_file_path = self.settings_folder / dst_file
            if not dst_file_path.exists():
                missing_file_def = {
                    'src': Path(file_def['src']),
                    'dest': dst_file_path
                }
                required_files.append(missing_file_def)
                self.logger.debug(f"Required file missing: {dst_file_path}")
                
        return required_files

    def _copy_missing_files(self, missing_files: list[dict[str, Path]]) -> None:
        """Copy missing required files to settings folder.
        
        Args:
            missing_files: List of file definitions to copy
        """
        for file_def in missing_files:
            try:
                self._copy_file_from_resources(file_def['src'], file_def['dest'])
                self.logger.info(f"Copied required file: {file_def['src'].name}")

            except Exception as e:
                self.logger.error(f"Failed to copy file {file_def['src']}: {e}")
                raise
                
    def _update_template_files(
        self,
        required_template_file_defs: list[dict[str, Path]]) -> None:
        """Update template files on every startup (overwrite existing)."""
        for file_def in required_template_file_defs:
            try:
                self._copy_file_from_resources(file_def['src'], file_def['dest'])
                self.logger.debug(f"Updated template file: {file_def['dest'].name}")
            except Exception as e:
                self.logger.warning(f"Failed to update template file {file_def['dest'].name}: {e}")

    def _copy_file_from_resources(
        self,
        src_file_name: str | Path,
        dst_file_path: Path) -> None:
        """Copy a file from repository sources to settings folder.
        
        Args:
            file_name: Name of the file to copy
        """
        
        # Determine source file location from repository
        src_file_name = str(src_file_name)
        if src_file_name == 'README.md':
            source_file = self._get_repository_readme_path()
        elif src_file_name == '.env.example':
            source_file = self._get_repository_env_example_path()
        else:
            self.logger.error(f"Unknown file type for delivery: {src_file_name}")
            raise ValueError(f"Unsupported delivery file: {src_file_name}")
            
        if not source_file.exists():
            self.logger.error(f"Repository source file not found: {source_file}")
            raise FileNotFoundError(f"Required repository file missing: {source_file}")

        shutil.copy2(source_file, dst_file_path)
        self.logger.debug(f"Copied repository file {src_file_name} from {source_file}")
        
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
        
    def _notify_user_about_copied_files(
        self,
        copied_files: list[dict[str, Path]]) -> None:
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

        for file_def in copied_files:
            print(f"   ✅ {file_def['dest'].name}")
            
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Edit 'settings.ini' to configure your sync preferences")
        print(f"2. Review 'settings.ini.template' for all available options") 
        print(f"3. Run the application again to start syncing")
        print(f"\n💡 TIP: Your iCloud and Pushover credentials will be")
        print(f"   stored securely when you run the application.")
        print(f"\n🔧 Settings folder: {self.settings_folder}")
        print("="*60)
        