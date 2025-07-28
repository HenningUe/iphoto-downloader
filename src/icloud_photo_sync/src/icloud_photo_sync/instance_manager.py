"""Multi-instance control management for iCloud Photo Sync Tool."""

import os
import sys
import time
import platform
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager

# Cross-platform imports
_fcntl: Optional[Any] = None
_msvcrt: Optional[Any] = None

if platform.system() != "Windows":
    try:
        import fcntl as _fcntl
    except ImportError:
        pass
else:
    try:
        import msvcrt as _msvcrt
    except ImportError:
        pass

from .logger import get_logger
from .config import get_app_data_folder_path


class InstanceManager:
    """Manages single/multi-instance control for the application."""
    
    LOCK_FILE_NAME = "icloud_photo_sync.lock"
    
    def __init__(self, allow_multi_instance: bool = False):
        """Initialize the instance manager.
        
        Args:
            allow_multi_instance: Whether to allow multiple instances
        """
        self.allow_multi_instance = allow_multi_instance
        self.lock_file_path = self._get_lock_file_path()
        self.lock_file_handle: Optional[int] = None
        self.logger = get_logger()
        
    def _get_lock_file_path(self) -> Path:
        """Get the path to the lock file.
        
        Returns:
            Path to the lock file
        """
        # Use app data folder if available, otherwise current directory
        app_data_path = get_app_data_folder_path()
        if app_data_path:
            lock_dir = app_data_path / "locks"
            lock_dir.mkdir(parents=True, exist_ok=True)
            return lock_dir / self.LOCK_FILE_NAME
        else:
            return Path(self.LOCK_FILE_NAME)
    
    def _acquire_lock_windows(self) -> bool:
        """Acquire lock on Windows using msvcrt.
        
        Returns:
            True if lock was acquired, False otherwise
        """
        if _msvcrt is None:
            self.logger.warning("msvcrt not available on this system")
            return False
            
        try:
            self.lock_file_handle = os.open(
                str(self.lock_file_path), 
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC
            )
            
            # Try to lock the file (Windows)
            _msvcrt.locking(self.lock_file_handle, _msvcrt.LK_NBLCK, 1)
            
            # Write current process ID to lock file
            os.write(self.lock_file_handle, str(os.getpid()).encode())
            os.fsync(self.lock_file_handle)
            
            return True
            
        except (OSError, IOError):
            if self.lock_file_handle is not None:
                try:
                    os.close(self.lock_file_handle)
                except:
                    pass
                self.lock_file_handle = None
            return False
    
    def _acquire_lock_unix(self) -> bool:
        """Acquire lock on Unix-like systems using fcntl.
        
        Returns:
            True if lock was acquired, False otherwise
        """
        if _fcntl is None:
            self.logger.warning("fcntl not available on this system")
            return False
            
        try:
            self.lock_file_handle = os.open(
                str(self.lock_file_path), 
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC
            )
            
            # Try to acquire exclusive lock (non-blocking)
            _fcntl.flock(self.lock_file_handle, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            
            # Write current process ID to lock file
            os.write(self.lock_file_handle, str(os.getpid()).encode())
            os.fsync(self.lock_file_handle)
            
            return True
            
        except (OSError, IOError):
            if self.lock_file_handle is not None:
                try:
                    os.close(self.lock_file_handle)
                except:
                    pass
                self.lock_file_handle = None
            return False
    
    def check_and_acquire_lock(self) -> bool:
        """Check if another instance is running and acquire lock if allowed.
        
        Returns:
            True if lock was acquired or multi-instance is allowed
            False if another instance is running and multi-instance is disabled
        """
        if self.allow_multi_instance:
            self.logger.info("Multi-instance mode enabled - not checking for existing instances")
            return True
            
        # Use platform-specific locking mechanism
        if platform.system() == "Windows":
            success = self._acquire_lock_windows()
        else:
            success = self._acquire_lock_unix()
            
        if success:
            self.logger.info(f"Successfully acquired instance lock: {self.lock_file_path}")
        else:
            self.logger.warning("Could not acquire instance lock - another instance may be running")
            
        return success
    
    def release_lock(self) -> None:
        """Release the instance lock."""
        if self.lock_file_handle is not None:
            try:
                if platform.system() == "Windows" and _msvcrt is not None:
                    # Unlock on Windows
                    _msvcrt.locking(self.lock_file_handle, _msvcrt.LK_UNLCK, 1)
                elif _fcntl is not None:
                    # Unlock on Unix-like systems
                    _fcntl.flock(self.lock_file_handle, _fcntl.LOCK_UN)
                
                os.close(self.lock_file_handle)
                self.lock_file_handle = None
                
                # Remove lock file
                if self.lock_file_path.exists():
                    self.lock_file_path.unlink()
                    
                self.logger.info("Released instance lock")
            except Exception as e:
                self.logger.error(f"Error releasing instance lock: {e}")
    
    def get_running_instance_info(self) -> Optional[str]:
        """Get information about the currently running instance.
        
        Returns:
            Process ID of running instance if available
        """
        if not self.lock_file_path.exists():
            return None
            
        try:
            with open(self.lock_file_path, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    return f"Process ID: {pid_str}"
        except Exception:
            pass
            
        return "Unknown process"
    
    @contextmanager
    def instance_context(self):
        """Context manager for instance lock management.
        
        Yields:
            None
            
        Raises:
            SystemExit: If another instance is running and multi-instance is disabled
        """
        if not self.check_and_acquire_lock():
            # Another instance is running and multi-instance is disabled
            running_info = self.get_running_instance_info()
            print("❌ Another instance of iCloud Photo Sync Tool is already running.")
            if running_info:
                print(f"   Running instance: {running_info}")
            print("   To allow multiple instances, set ALLOW_MULTI_INSTANCE=true in your configuration.")
            print("   Application will now exit.")
            sys.exit(1)
        
        try:
            yield
        finally:
            self.release_lock()


def validate_multi_instance_config(allow_multi_instance: bool) -> bool:
    """Validate the multi-instance configuration parameter.
    
    Args:
        allow_multi_instance: The configuration value to validate
        
    Returns:
        True if valid (always returns True for boolean values)
        
    Raises:
        ValueError: If the configuration is invalid
    """
    if not isinstance(allow_multi_instance, bool):
        raise ValueError(f"allow_multi_instance must be a boolean, got {type(allow_multi_instance)}")
    
    return True


def enforce_single_instance(allow_multi_instance: bool) -> InstanceManager:
    """Enforce single instance if required and return instance manager.
    
    Args:
        allow_multi_instance: Whether to allow multiple instances
        
    Returns:
        InstanceManager instance
        
    Raises:
        SystemExit: If another instance is running and multi-instance is disabled
    """
    # Validate configuration
    validate_multi_instance_config(allow_multi_instance)
    
    # Create instance manager
    instance_manager = InstanceManager(allow_multi_instance)
    
    # Check and acquire lock (will exit if needed)
    with instance_manager.instance_context():
        pass
        
    return instance_manager
