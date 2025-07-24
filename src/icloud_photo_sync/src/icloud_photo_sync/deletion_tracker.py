"""Local deletion tracking using SQLite database."""

import sqlite3
import shutil
import glob
from pathlib import Path
from datetime import datetime

from .logger import get_logger


class DeletionTracker:
    """Tracks locally deleted photos to prevent re-downloading."""

    def __init__(self, db_path: str = "deletion_tracker.db") -> None:
        """Initialize deletion tracker with database safety checks.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)

        # Ensure database safety before any operations
        if not self.ensure_database_safety():
            raise RuntimeError("Failed to ensure database safety")

    @property
    def logger(self):
        """Get the global logger instance."""
        return get_logger()

    def _init_database(self) -> None:
        """Initialize the SQLite database with album-aware schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check current schema version
                schema_version = self._get_schema_version(conn)

                if schema_version == 0:
                    # Initialize new database with album-aware schema
                    self._create_album_aware_schema(conn)
                elif schema_version == 1:
                    # Migrate from legacy schema to album-aware schema
                    self._migrate_to_album_aware_schema(conn)

                # Ensure we're at the latest schema version
                self._set_schema_version(conn, 2)
                conn.commit()

            self.logger.debug(f"Successfully initialized deletion tracker database: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize deletion tracker database: {e}")
            raise

    def _get_schema_version(self, conn) -> int:
        """Get current database schema version.

        Args:
            conn: SQLite database connection

        Returns:
            Schema version number (0 for new database, 1 for legacy, 2 for album-aware)
        """
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if cursor.fetchone():
                cursor.execute("SELECT version FROM schema_version LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else 0

            # Check if we have legacy tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='downloaded_photos'"
            )
            if cursor.fetchone():
                # Check if it's the old schema (no source_album_name column)
                cursor.execute("PRAGMA table_info(downloaded_photos)")
                columns = {row[1] for row in cursor.fetchall()}
                if 'source_album_name' not in columns:
                    return 1  # Legacy schema
                else:
                    return 2  # Already album-aware

            return 0  # New database
        except Exception as e:
            self.logger.error(f"Error checking schema version: {e}")
            return 0

    def _set_schema_version(self, conn, version: int) -> None:
        """Set database schema version.

        Args:
            conn: SQLite database connection
            version: Schema version to set
        """
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            conn.execute("DELETE FROM schema_version")
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            self.logger.debug(f"Set schema version to {version}")
        except Exception as e:
            self.logger.error(f"Error setting schema version: {e}")

    def _create_album_aware_schema(self, conn) -> None:
        """Create new album-aware database schema.

        Args:
            conn: SQLite database connection
        """
        try:
            # Table for tracking deleted photos (album-aware)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deleted_photos (
                    photo_name TEXT NOT NULL,
                    source_album_name TEXT NOT NULL,
                    photo_id TEXT,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    original_path TEXT,
                    PRIMARY KEY (photo_id, source_album_name)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_deleted_photo_name
                ON deleted_photos(photo_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_deleted_album_name
                ON deleted_photos(source_album_name)
            """)

            # Table for tracking downloaded photos (album-aware)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloaded_photos (
                    photo_name TEXT NOT NULL,
                    source_album_name TEXT NOT NULL,
                    photo_id TEXT,
                    local_path TEXT NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    PRIMARY KEY (photo_id, source_album_name)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloaded_path
                ON downloaded_photos(local_path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloaded_photo_name
                ON downloaded_photos(photo_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloaded_album_name
                ON downloaded_photos(source_album_name)
            """)

            self.logger.info("Created album-aware database schema")
        except Exception as e:
            self.logger.error(f"Error creating album-aware schema: {e}")
            raise

    def _migrate_to_album_aware_schema(self, conn) -> None:
        """Migrate from legacy schema to album-aware schema.

        Args:
            conn: SQLite database connection
        """
        try:
            self.logger.info("Migrating database to album-aware schema...")

            # First, backup existing data
            cursor = conn.cursor()

            # Backup deleted_photos
            cursor.execute("SELECT * FROM deleted_photos")
            legacy_deleted = cursor.fetchall()

            # Backup downloaded_photos
            cursor.execute("SELECT * FROM downloaded_photos")
            legacy_downloaded = cursor.fetchall()

            # Drop old tables
            conn.execute("DROP TABLE IF EXISTS deleted_photos")
            conn.execute("DROP TABLE IF EXISTS downloaded_photos")

            # Create new schema
            self._create_album_aware_schema(conn)

            # Migrate downloaded photos data
            for row in legacy_downloaded:
                photo_id, filename, local_path, downloaded_at, file_size, album_name = row
                # Use album name from the record, or 'Unknown' if None
                source_album = album_name if album_name else 'Unknown'

                conn.execute("""
                    INSERT OR IGNORE INTO downloaded_photos
                    (photo_name, source_album_name, photo_id, local_path, downloaded_at, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (filename, source_album, photo_id, local_path, downloaded_at, file_size))

            # Migrate deleted photos data
            for row in legacy_deleted:
                photo_id, filename, deleted_at, file_size, original_path = row
                # Extract album from original_path if possible, otherwise use 'Unknown'
                album_name = 'Unknown'
                if original_path and '/' in original_path:
                    # Try to extract album from path like "Album/photo.jpg"
                    parts = Path(original_path).parts
                    if len(parts) > 1:
                        album_name = parts[0]

                conn.execute("""
                    INSERT OR IGNORE INTO deleted_photos
                    (photo_name, source_album_name, photo_id, deleted_at, file_size, original_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (filename, album_name, photo_id, deleted_at, file_size, original_path))

            migrated_downloaded = len(legacy_downloaded)
            migrated_deleted = len(legacy_deleted)

            self.logger.info(
                f"Migration completed: {migrated_downloaded} downloaded photos, "
                f"{migrated_deleted} deleted photos migrated to album-aware schema"
            )

        except Exception as e:
            self.logger.error(f"Error migrating to album-aware schema: {e}")
            raise

    def create_backup(self, max_backups: int = 5) -> bool:
        """Create a backup copy of the database before sync operations.

        Args:
            max_backups: Maximum number of backup files to keep

        Returns:
            True if backup was created successfully, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.with_suffix(f".backup_{timestamp}.db")

            # Create backup directory if it doesn't exist
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the database file
            shutil.copy2(self.db_path, backup_path)

            # Clean up old backups
            self._cleanup_old_backups(max_backups)

            self.logger.info(f"Database backup created: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create database backup: {e}")
            return False

    def _cleanup_old_backups(self, max_backups: int):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_pattern = str(self.db_path.with_suffix(".backup_*.db"))
            backup_files = sorted(glob.glob(backup_pattern), reverse=True)

            # Remove excess backups
            for backup_file in backup_files[max_backups:]:
                Path(backup_file).unlink()
                self.logger.info(f"Removed old backup: {backup_file}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")

    def check_database_integrity(self) -> bool:
        """Check if the database is not corrupted.

        Returns:
            True if database is intact, False if corrupted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()

                if result and result[0] == "ok":
                    self.logger.debug("Database integrity check passed")
                    return True
                else:
                    self.logger.error(f"Database integrity check failed: {result}")
                    return False

        except Exception as e:
            self.logger.error(f"Database integrity check failed with exception: {e}")
            return False

    def recover_from_backup(self) -> bool:
        """Attempt to recover database from the most recent backup.

        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            backup_pattern = str(self.db_path.with_suffix(".backup_*.db"))
            backup_files = sorted(glob.glob(backup_pattern), reverse=True)

            if not backup_files:
                self.logger.error("No backup files found for recovery")
                return False

            latest_backup = backup_files[0]

            # Test backup integrity before restoring
            backup_path = Path(latest_backup)
            test_conn = None
            try:
                test_conn = sqlite3.connect(backup_path)
                cursor = test_conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()

                if not result or result[0] != "ok":
                    self.logger.error(f"Backup file is also corrupted: {latest_backup}")
                    return False

            except Exception as e:
                self.logger.error(f"Cannot validate backup file {latest_backup}: {e}")
                return False
            finally:
                if test_conn:
                    test_conn.close()

            # Create a backup of the corrupted database
            if self.db_path.exists():
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    corrupted_backup = self.db_path.with_suffix(f".corrupted_{timestamp}.db")

                    # Force close connections and wait for Windows file handles
                    import gc
                    gc.collect()
                    import time
                    time.sleep(0.1)

                    shutil.move(self.db_path, corrupted_backup)
                    self.logger.info(f"Moved corrupted database to: {corrupted_backup}")
                except Exception as move_error:
                    self.logger.warning(f"Could not move corrupted database: {move_error}")
                    # Try to delete instead
                    try:
                        self.db_path.unlink()
                        self.logger.info("Deleted corrupted database file")
                    except Exception as delete_error:
                        self.logger.error(f"Could not delete corrupted database: {delete_error}")
                        return False

            # Restore from backup
            shutil.copy2(latest_backup, self.db_path)
            self.logger.info(f"Database recovered from backup: {latest_backup}")

            # Verify the restored database
            if self.check_database_integrity():
                return True
            else:
                self.logger.error("Restored database failed integrity check")
                return False

        except Exception as e:
            self.logger.error(f"Database recovery failed: {e}")
            return False

    def ensure_database_safety(self) -> bool:
        """Ensure database is ready for operations with safety checks.

        Returns:
            True if database is safe to use, False otherwise
        """
        # Check if database exists
        if not self.db_path.exists():
            self.logger.info("Database does not exist, will be created")
            self._init_database()
            # Create initial backup after database creation
            self.create_backup()
            return True

        # Check database integrity
        if not self.check_database_integrity():
            self.logger.warning("Database corruption detected, attempting recovery")

            # Force close any open connections before recovery
            import gc
            gc.collect()

            if self.recover_from_backup():
                self.logger.info("Database successfully recovered from backup")
                return True
            else:
                self.logger.error("Database recovery failed, creating new database")
                # Move corrupted database and create new one
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    corrupted_backup = self.db_path.with_suffix(f".corrupted_{timestamp}.db")

                    # Force close connections and wait a bit for Windows file handles
                    gc.collect()
                    import time
                    time.sleep(0.1)

                    shutil.move(self.db_path, corrupted_backup)
                    self._init_database()
                    # Create backup after recreating database
                    self.create_backup()
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to move corrupted database: {e}")
                    # As last resort, just recreate the database
                    try:
                        self.db_path.unlink(missing_ok=True)
                        self._init_database()
                        # Create backup after recreating database as last resort
                        self.create_backup()
                        return True
                    except Exception as e2:
                        self.logger.error(f"Failed to recreate database: {e2}")
                        return False

        # Create backup before operations
        self.create_backup()
        return True

    def add_deleted_photo(
        self,
        photo_id: str,
        filename: str,
        file_size: int | None = None,
        original_path: str | None = None,
        album_name: str | None = None
    ) -> None:
        """Record a photo as deleted with album-aware tracking.

        Args:
            photo_id: Unique photo identifier
            filename: Photo filename
            file_size: File size in bytes
            original_path: Original local file path
            album_name: Album name where photo originated
        """
        # Extract album from original_path if not provided
        source_album = album_name
        if not source_album and original_path:
            # Try to extract album from path like "Album/photo.jpg"
            parts = Path(original_path).parts
            if len(parts) > 1:
                source_album = parts[0]

        # Use 'Unknown' if still no album
        if not source_album:
            source_album = 'Unknown'

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO deleted_photos
                (photo_name, source_album_name, photo_id, deleted_at, file_size, original_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (filename, source_album, photo_id, datetime.now(), file_size, original_path))
            conn.commit()
        self.logger.debug(f"📝 Recorded deleted photo: {filename} from {source_album}")

    def is_deleted(self, photo_id: str) -> bool:
        """Check if a photo is marked as deleted (legacy method for backward compatibility).

        Args:
            photo_id: Unique photo identifier

        Returns:
            True if photo is marked as deleted, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM deleted_photos WHERE photo_id = ? LIMIT 1",
                (photo_id,)
            )
            return cursor.fetchone() is not None

    def is_photo_deleted(self, photo_name: str, album_name: str | None = None) -> bool:
        """Check if a photo is marked as deleted (album-aware).

        Args:
            photo_name: Photo filename
            album_name: Album name (uses 'Unknown' if None)

        Returns:
            True if photo is marked as deleted in the specified album, False otherwise
        """
        source_album = album_name if album_name else 'Unknown'

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM deleted_photos
                WHERE photo_name = ? AND source_album_name = ?
                LIMIT 1
            """, (photo_name, source_album))
            return cursor.fetchone() is not None

    def is_photo_downloaded(self, photo_name: str, album_name: str | None = None) -> bool:
        """Check if a photo has already been downloaded from a specific album.

        Args:
            photo_name: Photo filename
            album_name: Album name (uses 'Unknown' if None)

        Returns:
            True if photo is already downloaded from the specified album, False otherwise
        """
        source_album = album_name if album_name else 'Unknown'

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM downloaded_photos
                WHERE photo_name = ? AND source_album_name = ?
                LIMIT 1
            """, (photo_name, source_album))
            return cursor.fetchone() is not None

    def is_filename_deleted(self, filename: str) -> bool:
        """Check if a filename is marked as deleted.

        Args:
            filename: Photo filename

        Returns:
            True if filename is marked as deleted, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM deleted_photos WHERE filename = ? LIMIT 1",
                    (filename,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"❌ Failed to check deletion status for filename {filename}: {e}")
            return False

    def get_deleted_photos(self) -> set[str]:
        """Get all deleted photo IDs.

        Returns:
            Set of deleted photo IDs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT photo_id FROM deleted_photos")
            return {row[0] for row in cursor.fetchall()}

    def remove_deleted_photo(self, photo_id: str) -> None:
        """Remove a photo from the deletion tracker.

        Args:
            photo_id: Unique photo identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM deleted_photos WHERE photo_id = ?",
                (photo_id,)
            )
            conn.commit()
        self.logger.debug(f"🗑️ Removed photo from deletion tracker: {photo_id}")

    def get_stats(self) -> dict:
        """Get deletion tracker statistics.

        Returns:
            Dictionary with tracker statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM deleted_photos")
            total_deleted = cursor.fetchone()[0]

            cursor = conn.execute("""
                    SELECT
                        MIN(deleted_at) as first_deletion,
                        MAX(deleted_at) as last_deletion
                    FROM deleted_photos
                """)
            times = cursor.fetchone()

            return {
                'total_deleted': total_deleted,
                'first_deletion': times[0],
                'last_deletion': times[1],
                'db_path': str(self.db_path)
            }

    def add_downloaded_photo(
        self,
        photo_id: str,
        filename: str,
        local_path: str,
        file_size: int | None = None,
        album_name: str | None = None
    ) -> None:
        """Record a photo as successfully downloaded with album-aware tracking.

        Args:
            photo_id: Unique photo identifier
            filename: Photo filename
            local_path: Local file path where photo was saved
            file_size: File size in bytes
            album_name: Album name where photo originated
        """
        try:
            # Use 'Unknown' if no album name provided
            source_album = album_name if album_name else 'Unknown'

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO downloaded_photos
                    (photo_name, source_album_name, photo_id, local_path, downloaded_at, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (filename, source_album, photo_id, local_path, datetime.now(), file_size))
                conn.commit()
            self.logger.debug(
                f"📝 Recorded downloaded photo: {filename} from {source_album} -> {local_path}"
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to record downloaded photo {filename}: {e}")

    def get_downloaded_photos(self) -> dict[str, dict]:
        """Get all downloaded photos with their metadata (album-aware).

        Returns:
            Dictionary mapping (photo_name, album_name) tuple to photo metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT photo_name, source_album_name, photo_id, local_path,
                           downloaded_at, file_size
                    FROM downloaded_photos
                """)
                result = {}
                for row in cursor.fetchall():
                    # Use composite key (photo_name, album_name)
                    key = (row[0], row[1])
                    result[key] = {
                        'photo_name': row[0],
                        'source_album_name': row[1],
                        'photo_id': row[2],
                        'local_path': row[3],
                        'downloaded_at': row[4],
                        'file_size': row[5]
                    }
                return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get downloaded photos: {e}")
            return {}

    def detect_locally_deleted_photos(self, sync_directory: Path) -> list[dict]:
        """Detect photos that were downloaded but are now missing locally.

        Args:
            sync_directory: Base sync directory path

        Returns:
            List of photo metadata dictionaries for detected deletions
        """
        deleted_photos = []
        try:
            downloaded_photos = self.get_downloaded_photos()

            for (photo_name, album_name), metadata in downloaded_photos.items():
                # Check if this photo is already marked as deleted
                if self.is_photo_deleted(photo_name, album_name):
                    continue

                # Check if the file still exists locally
                local_path = sync_directory / metadata['local_path']
                if not local_path.exists():
                    # Photo was deleted locally
                    deleted_photos.append({
                        'photo_id': metadata['photo_id'],
                        'filename': photo_name,
                        'local_path': metadata['local_path'],
                        'file_size': metadata['file_size'],
                        'album_name': album_name
                    })

            return deleted_photos

        except Exception as e:
            self.logger.error(f"❌ Error detecting locally deleted photos: {e}")
            return []

    def mark_photos_as_deleted(self, deleted_photos: list[dict]) -> None:
        """Mark multiple photos as deleted based on deletion detection.

        Args:
            deleted_photos: List of photo metadata from detect_locally_deleted_photos
        """
        for photo_data in deleted_photos:
            try:
                self.add_deleted_photo(
                    photo_id=photo_data['photo_id'],
                    filename=photo_data['filename'],
                    file_size=photo_data.get('file_size'),
                    original_path=photo_data['local_path'],
                    album_name=photo_data.get('album_name')
                )
                self.logger.info(f"🗑️ Marked as deleted: {photo_data['local_path']}")
            except Exception as e:
                self.logger.error(
                    f"❌ Failed to mark photo as deleted {photo_data['filename']}: {e}")

    def remove_downloaded_photo(self, photo_id: str) -> None:
        """Remove a photo from the downloaded photos tracking.

        Args:
            photo_id: Unique photo identifier
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM downloaded_photos WHERE photo_id = ?",
                    (photo_id,)
                )
                conn.commit()
            self.logger.debug(f"🗑️ Removed photo from download tracker: {photo_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to remove downloaded photo {photo_id}: {e}")

    def close(self) -> None:
        """Close any open database connections.

        This is useful for ensuring proper cleanup, especially on Windows
        where file handles may prevent directory cleanup.
        """
        # Force garbage collection to close any remaining connections
        import gc
        gc.collect()

        # Try to close any lingering connections by connecting and closing immediately
        try:
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                conn.close()
        except Exception:
            pass  # Ignore errors during cleanup
