"""Local deletion tracking using SQLite database."""

import gc
import glob
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

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
                if "source_album_name" not in columns:
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        self.logger.debug(f"Set schema version to {version}")

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

            # Table for enhanced photo tracking with composite keys
            # First check if table exists and has old format
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='photo_tracking'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Check if it has the new schema with album_name column
                cursor.execute("PRAGMA table_info(photo_tracking)")
                columns = [col[1] for col in cursor.fetchall()]
                if "album_name" not in columns:
                    # Old format table exists, need to migrate
                    self.logger.info("Migrating old photo_tracking table to enhanced format")

                    # Backup old data
                    cursor.execute("SELECT * FROM photo_tracking")
                    old_data = cursor.fetchall()

                    # Drop old table
                    conn.execute("DROP TABLE photo_tracking")

                    # Create new table
                    conn.execute("""
                        CREATE TABLE photo_tracking (
                            photo_id TEXT NOT NULL,
                            album_name TEXT NOT NULL,
                            filename TEXT NOT NULL,
                            local_path TEXT,
                            file_size INTEGER,
                            modified_date TEXT,
                            checksum TEXT,
                            sync_status TEXT DEFAULT 'pending',
                            last_sync_attempt TEXT,
                            error_count INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (photo_id, album_name)
                        )
                    """)

                    # Migrate old data with 'Unknown' album
                    for row in old_data:
                        try:
                            # Old format: (photo_id, filename, local_path, file_size, modified_date, checksum, sync_status)
                            photo_id = row[0]
                            filename = row[1] if len(row) > 1 else "unknown.jpg"
                            local_path = row[2] if len(row) > 2 else None  # noqa
                            file_size = row[3] if len(row) > 3 else None  # noqa
                            checksum = row[5] if len(row) > 5 else None  # noqa
                            sync_status = row[6] if len(row) > 6 else "pending"  # noqa

                            conn.execute(
                                """
                                INSERT INTO photo_tracking
                                (photo_id, album_name, filename, local_path, file_size,
                                 checksum, sync_status, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """,
                                (
                                    photo_id,
                                    "Unknown",
                                    filename,
                                    local_path,
                                    file_size,
                                    checksum,
                                    sync_status,
                                ),
                            )
                        except Exception as e:
                            self.logger.warning(f"Failed to migrate photo record {row}: {e}")

                    self.logger.info(f"Migrated {len(old_data)} photos to enhanced tracking format")
            else:
                # Create new table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS photo_tracking (
                        photo_id TEXT NOT NULL,
                        album_name TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        local_path TEXT,
                        file_size INTEGER,
                        modified_date TEXT,
                        checksum TEXT,
                        sync_status TEXT DEFAULT 'pending',
                        last_sync_attempt TEXT,
                        error_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (photo_id, album_name)
                    )
                """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_photo_tracking_album
                ON photo_tracking(album_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_photo_tracking_status
                ON photo_tracking(sync_status)
            """)

            # Table for album tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS album_tracking (
                    album_name TEXT PRIMARY KEY,
                    is_shared BOOLEAN DEFAULT FALSE,
                    total_photos INTEGER DEFAULT 0,
                    synced_photos INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_sync TEXT,
                    sync_status TEXT DEFAULT 'pending'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_album_tracking_status
                ON album_tracking(sync_status)
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
                source_album = album_name if album_name else "Unknown"

                conn.execute(
                    """
                    INSERT OR IGNORE INTO downloaded_photos
                    (photo_name, source_album_name, photo_id, local_path, downloaded_at, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (filename, source_album, photo_id, local_path, downloaded_at, file_size),
                )

            # Migrate deleted photos data
            for row in legacy_deleted:
                photo_id, filename, deleted_at, file_size, original_path = row
                # Extract album from original_path if possible, otherwise use 'Unknown'
                album_name = "Unknown"
                if original_path and "/" in original_path:
                    # Try to extract album from path like "Album/photo.jpg"
                    parts = Path(original_path).parts
                    if len(parts) > 1:
                        album_name = parts[0]

                conn.execute(
                    """
                    INSERT OR IGNORE INTO deleted_photos
                    (photo_name, source_album_name, photo_id, deleted_at, file_size, original_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (filename, album_name, photo_id, deleted_at, file_size, original_path),
                )

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

    def recover_from_backup(self) -> bool:  # noqa
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
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    corrupted_backup = self.db_path.with_suffix(f".corrupted_{timestamp}.db")

                    # Force close connections and wait for Windows file handles
                    gc.collect()
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
            gc.collect()

            if self.recover_from_backup():
                self.logger.info("Database successfully recovered from backup")
                return True
            else:
                self.logger.error("Database recovery failed, creating new database")
                # Move corrupted database and create new one
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

        # Check if database has proper schema (even if integrity is OK)
        if not self._has_required_tables():
            self.logger.info("Database exists but missing required tables, initializing schema")
            self._init_database()

        # Create backup before operations
        self.create_backup()
        return True

    def _has_required_tables(self) -> bool:
        """Check if database has the required tables.

        Returns:
            True if all required tables exist, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='deleted_photos'"
                )
                if not cursor.fetchone():
                    return False

                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='downloaded_photos'"
                )
                return bool(cursor.fetchone())
        except Exception as e:
            self.logger.error(f"Error checking database tables: {e}")
            return False

    def add_deleted_photo(
        self,
        photo_id: str,
        filename: str,
        file_size: int | None = None,
        original_path: str | None = None,
        album_name: str | None = None,
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
            source_album = "Unknown"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO deleted_photos
                (photo_name, source_album_name, photo_id, deleted_at, file_size, original_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (filename, source_album, photo_id, datetime.now(), file_size, original_path),
            )
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
                "SELECT 1 FROM deleted_photos WHERE photo_id = ? LIMIT 1", (photo_id,)
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
        source_album = album_name if album_name else "Unknown"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 1 FROM deleted_photos
                WHERE photo_name = ? AND source_album_name = ?
                LIMIT 1
            """,
                (photo_name, source_album),
            )
            return cursor.fetchone() is not None

    def is_photo_downloaded(self, photo_name: str, album_name: str | None = None) -> bool:
        """Check if a photo has already been downloaded from a specific album.

        Args:
            photo_name: Photo filename
            album_name: Album name (uses 'Unknown' if None)

        Returns:
            True if photo is already downloaded from the specified album, False otherwise
        """
        source_album = album_name if album_name else "Unknown"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 1 FROM downloaded_photos
                WHERE photo_name = ? AND source_album_name = ?
                LIMIT 1
            """,
                (photo_name, source_album),
            )
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
                    "SELECT 1 FROM deleted_photos WHERE photo_name = ? LIMIT 1", (filename,)
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
            conn.execute("DELETE FROM deleted_photos WHERE photo_id = ?", (photo_id,))
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
                "total_deleted": total_deleted,
                "first_deletion": times[0],
                "last_deletion": times[1],
                "db_path": str(self.db_path),
            }

    def add_downloaded_photo(
        self,
        photo_id: str,
        filename: str,
        local_path: str,
        file_size: int | None = None,
        album_name: str | None = None,
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
            source_album = album_name if album_name else "Unknown"

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO downloaded_photos
                    (photo_name, source_album_name, photo_id, local_path, downloaded_at, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (filename, source_album, photo_id, local_path, datetime.now(), file_size),
                )
                conn.commit()
            self.logger.debug(
                f"📝 Recorded downloaded photo: {filename} from {source_album} -> {local_path}"
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to record downloaded photo {filename}: {e}")

    def get_downloaded_photos(self) -> dict[str, dict]:
        """Get all downloaded photos with their metadata (album-aware).

        Returns:
            Dictionary mapping photo_id to photo metadata
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
                    # Use photo_id as key for simpler access
                    photo_id = row[2]
                    result[photo_id] = {
                        "filename": row[0],  # Map photo_name to filename for test compatibility
                        "album_name": row[
                            1
                        ],  # Map source_album_name to album_name for test compatibility
                        "photo_id": row[2],
                        "local_path": row[3],
                        "downloaded_at": row[4],
                        "file_size": row[5],
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

            for _, metadata in downloaded_photos.items():
                # Check if this photo is already marked as deleted
                if self.is_photo_deleted(metadata["filename"], metadata["album_name"]):
                    continue

                # Check if the file still exists locally
                local_path = sync_directory / metadata["local_path"]
                if not local_path.exists():
                    # Photo was deleted locally
                    deleted_photos.append(
                        {
                            "photo_id": metadata["photo_id"],
                            "filename": metadata["filename"],
                            "local_path": metadata["local_path"],
                            "file_size": metadata["file_size"],
                            "album_name": metadata["album_name"],
                        }
                    )

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
                    photo_id=photo_data["photo_id"],
                    filename=photo_data["filename"],
                    file_size=photo_data.get("file_size"),
                    original_path=photo_data["local_path"],
                    album_name=photo_data.get("album_name"),
                )
                self.logger.info(f"🗑️ Marked as deleted: {photo_data['local_path']}")
            except Exception as e:
                self.logger.error(
                    f"❌ Failed to mark photo as deleted {photo_data['filename']}: {e}"
                )

    def remove_downloaded_photo(self, photo_id: str) -> None:
        """Remove a photo from the downloaded photos tracking.

        Args:
            photo_id: Unique photo identifier
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM downloaded_photos WHERE photo_id = ?", (photo_id,))
                conn.commit()
            self.logger.debug(f"🗑️ Removed photo from download tracker: {photo_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to remove downloaded photo {photo_id}: {e}")

    def track_photo(
        self,
        photo_id: str,
        album_name: str,
        filename: str,
        local_path: str,
        file_size: int,
        checksum: str,
        **kwargs,
    ) -> None:
        """Track a photo with album-aware composite key identification.

        Args:
            photo_id: Unique photo identifier
            album_name: Album name where photo belongs
            filename: Photo filename
            local_path: Local file path
            file_size: File size in bytes
            checksum: Photo checksum
            **kwargs: Additional optional parameters
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO photo_tracking
                    (photo_id, album_name, filename, local_path, file_size, checksum,
                     sync_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                    (photo_id, album_name, filename, local_path, file_size, checksum),
                )
                conn.commit()
            self.logger.debug(f"📸 Tracked photo {photo_id} in album {album_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to track photo {photo_id}: {e}")

    def track_album(self, album_name: str, is_shared: bool, total_photos: int) -> None:
        """Track an album with metadata.

        Args:
            album_name: Album name
            is_shared: Whether album is shared
            total_photos: Total number of photos in album
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO album_tracking
                    (album_name, is_shared, total_photos, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (album_name, is_shared, total_photos),
                )
                conn.commit()
            self.logger.debug(f"📁 Tracked album {album_name} with {total_photos} photos")
        except Exception as e:
            self.logger.error(f"❌ Failed to track album {album_name}: {e}")

    def get_all_tracked_photos(self) -> list[dict]:
        """Get all tracked photos with their metadata.

        Returns:
            List of dictionaries containing photo data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT photo_id, album_name, filename, local_path, file_size,
                           checksum, sync_status, created_at
                    FROM photo_tracking
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()

                columns = [
                    "photo_id",
                    "album_name",
                    "filename",
                    "local_path",
                    "file_size",
                    "checksum",
                    "sync_status",
                    "created_at",
                ]
                return [dict(zip(columns, row, strict=False)) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ Failed to get tracked photos: {e}")
            return []

    def get_photos_in_album(self, album_name: str) -> list[dict]:
        """Get all photos in a specific album.

        Args:
            album_name: Album name to query

        Returns:
            List of dictionaries containing photo data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT photo_id, album_name, filename, local_path, file_size,
                           checksum, sync_status, created_at
                    FROM photo_tracking
                    WHERE album_name = ?
                    ORDER BY created_at DESC
                """,
                    (album_name,),
                )
                rows = cursor.fetchall()

                columns = [
                    "photo_id",
                    "album_name",
                    "filename",
                    "local_path",
                    "file_size",
                    "checksum",
                    "sync_status",
                    "created_at",
                ]
                return [dict(zip(columns, row, strict=False)) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ Failed to get photos in album {album_name}: {e}")
            return []

    def update_photo_sync_status(self, photo_id: str, album_name: str, status: str) -> None:
        """Update sync status for a specific photo in an album.

        Args:
            photo_id: Photo identifier
            album_name: Album name
            status: New sync status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE photo_tracking
                    SET sync_status = ?, last_sync_attempt = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE photo_id = ? AND album_name = ?
                """,
                    (status, photo_id, album_name),
                )
                conn.commit()
            self.logger.debug(f"📸 Updated photo {photo_id} status to {status}")
        except Exception as e:
            self.logger.error(f"❌ Failed to update photo status: {e}")

    def get_photo_sync_status(self, photo_id: str, album_name: str) -> str:
        """Get sync status for a specific photo in an album.

        Args:
            photo_id: Photo identifier
            album_name: Album name

        Returns:
            Sync status string
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT sync_status FROM photo_tracking
                    WHERE photo_id = ? AND album_name = ?
                """,
                    (photo_id, album_name),
                )
                result = cursor.fetchone()
                return result[0] if result else "unknown"
        except Exception as e:
            self.logger.error(f"❌ Failed to get photo status: {e}")
            return "error"

    def update_album_sync_progress(self, album_name: str, synced_photos: int) -> None:
        """Update sync progress for an album.

        Args:
            album_name: Album name
            synced_photos: Number of photos synced
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE album_tracking
                    SET synced_photos = ?, last_sync = CURRENT_TIMESTAMP
                    WHERE album_name = ?
                """,
                    (synced_photos, album_name),
                )
                conn.commit()
            self.logger.debug(f"📁 Updated album {album_name} progress: {synced_photos} photos")
        except Exception as e:
            self.logger.error(f"❌ Failed to update album progress: {e}")

    def get_album_statistics(self, album_name: str) -> dict:
        """Get statistics for a specific album.

        Args:
            album_name: Album name

        Returns:
            Dictionary with album statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT is_shared, total_photos, synced_photos, created_at, last_sync
                    FROM album_tracking
                    WHERE album_name = ?
                """,
                    (album_name,),
                )
                row = cursor.fetchone()

                if row:
                    return {
                        "album_name": album_name,
                        "is_shared": bool(row[0]),
                        "total_photos": row[1],
                        "synced_photos": row[2] or 0,
                        "created_at": row[3],
                        "last_sync": row[4],
                    }
                else:
                    return {
                        "album_name": album_name,
                        "is_shared": False,
                        "total_photos": 0,
                        "synced_photos": 0,
                        "created_at": None,
                        "last_sync": None,
                    }
        except Exception as e:
            self.logger.error(f"❌ Failed to get album statistics: {e}")
            return {}

    def update_album_sync_status(self, album_name: str, status: str) -> None:
        """Update sync status for an album.

        Args:
            album_name: Album name
            status: New sync status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE album_tracking
                    SET sync_status = ?, last_sync = CURRENT_TIMESTAMP
                    WHERE album_name = ?
                """,
                    (status, album_name),
                )
                conn.commit()
            self.logger.debug(f"📁 Updated album {album_name} status to {status}")
        except Exception as e:
            self.logger.error(f"❌ Failed to update album status: {e}")

    def bulk_track_photos(self, photos_data: list[dict]) -> None:
        """Bulk track multiple photos for performance.

        Args:
            photos_data: List of photo dictionaries with required fields
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO photo_tracking
                    (photo_id, album_name, filename, local_path, file_size, checksum,
                     sync_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                    [
                        (
                            photo["photo_id"],
                            photo["album_name"],
                            photo["filename"],
                            photo["local_path"],
                            photo["file_size"],
                            photo["checksum"],
                        )
                        for photo in photos_data
                    ],
                )
                conn.commit()
            self.logger.debug(f"📸 Bulk tracked {len(photos_data)} photos")
        except Exception as e:
            self.logger.error(f"❌ Failed to bulk track photos: {e}")

    def cleanup_old_completed_entries(self, days_old: int = 30) -> int:
        """Clean up old completed photo tracking entries.

        Args:
            days_old: Number of days old entries to clean up

        Returns:
            Number of entries cleaned up
        """
        try:
            cutoff_timestamp = time.time() - (days_old * 24 * 60 * 60)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM photo_tracking
                    WHERE sync_status = 'completed'
                    AND updated_at < ?
                """,
                    (cutoff_timestamp,),
                )
                deleted_count = cursor.rowcount
                conn.commit()

            self.logger.debug(f"🧹 Cleaned up {deleted_count} old completed entries")
            return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup old entries: {e}")
            return 0

    def find_cross_album_duplicates(self) -> list[dict]:
        """Find photos that exist in multiple albums (same checksum).

        Returns:
            List of duplicate groups
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT checksum, GROUP_CONCAT(photo_id || ':' || album_name) as locations,
                           COUNT(*) as duplicate_count
                    FROM photo_tracking
                    WHERE checksum IS NOT NULL
                    GROUP BY checksum
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                """)

                duplicates = []
                for row in cursor.fetchall():
                    checksum, locations_str, count = row
                    locations = []
                    albums = []
                    for loc in locations_str.split(","):
                        if ":" in loc:
                            photo_id, album_name = loc.split(":", 1)
                            locations.append({"photo_id": photo_id, "album_name": album_name})
                            albums.append(album_name)

                    duplicates.append(
                        {
                            "checksum": checksum,
                            "locations": locations,
                            "albums": albums,  # Add albums key for test compatibility
                            "duplicate_count": count,
                        }
                    )

                return duplicates
        except Exception as e:
            self.logger.error(f"❌ Failed to find duplicates: {e}")
            return []

    def record_sync_error(self, photo_id: str, album_name: str, error_message: str) -> None:
        """Record a sync error for a photo.

        Args:
            photo_id: Photo identifier
            album_name: Album name
            error_message: Error message
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE photo_tracking
                    SET sync_status = 'failed',
                        error_count = error_count + 1,
                        last_sync_attempt = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE photo_id = ? AND album_name = ?
                """,
                    (photo_id, album_name),
                )
                conn.commit()
            self.logger.debug(f"🚫 Recorded sync error for {photo_id}: {error_message}")
        except Exception as e:
            self.logger.error(f"❌ Failed to record sync error: {e}")

    def get_album_sync_progress(self, album_name: str) -> dict:
        """Get detailed sync progress for an album.

        Args:
            album_name: Album name

        Returns:
            Dictionary with progress information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get album metadata
                cursor = conn.execute(
                    """
                    SELECT total_photos FROM album_tracking WHERE album_name = ?
                """,
                    (album_name,),
                )
                album_row = cursor.fetchone()
                total_photos_from_album = album_row[0] if album_row else 0

                # Get actual tracked photos stats
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as tracked_photos,
                        SUM(CASE WHEN sync_status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN sync_status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
                    FROM photo_tracking
                    WHERE album_name = ?
                """,
                    (album_name,),
                )

                row = cursor.fetchone()
                if row:
                    tracked, completed, failed, pending, in_progress = row
                    return {
                        "album_name": album_name,
                        "total_photos": total_photos_from_album,  # From album metadata
                        "tracked_photos": tracked or 0,  # Actual photos tracked
                        "completed": completed or 0,
                        "completed_photos": completed or 0,  # Alternative field name
                        "failed": failed or 0,
                        "failed_photos": failed or 0,  # Alternative field name
                        "pending": pending or 0,
                        "pending_photos": pending or 0,  # Alternative field name
                        "in_progress": in_progress or 0,
                        "in_progress_photos": in_progress or 0,  # Alternative field name
                        "completion_percentage": (completed or 0) / max(tracked or 1, 1) * 100,
                    }
                else:
                    return {
                        "album_name": album_name,
                        "total_photos": total_photos_from_album,
                        "tracked_photos": 0,
                        "completed": 0,
                        "completed_photos": 0,
                        "failed": 0,
                        "failed_photos": 0,
                        "pending": 0,
                        "pending_photos": 0,
                        "in_progress": 0,
                        "in_progress_photos": 0,
                        "completion_percentage": 0.0,
                    }
        except Exception as e:
            self.logger.error(f"❌ Failed to get album sync progress: {e}")
            return {}

    def get_albums_by_status(self, status: str) -> list[dict]:
        """Get list of albums with specific sync status.

        Args:
            status: Sync status to filter by

        Returns:
            List of album dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT album_name, is_shared, total_photos, synced_photos,
                           created_at, last_sync, sync_status
                    FROM album_tracking
                    WHERE sync_status = ?
                    ORDER BY album_name
                """,
                    (status,),
                )

                columns = [
                    "album_name",
                    "is_shared",
                    "total_photos",
                    "synced_photos",
                    "created_at",
                    "last_sync",
                    "sync_status",
                ]
                return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"❌ Failed to get albums by status: {e}")
            return []

    def get_photo_info(self, photo_id: str, album_name: str) -> dict:
        """Get detailed information for a specific photo.

        Args:
            photo_id: Photo identifier
            album_name: Album name

        Returns:
            Dictionary with photo information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT photo_id, album_name, filename, local_path, file_size,
                           checksum, sync_status, last_sync_attempt, error_count, created_at
                    FROM photo_tracking
                    WHERE photo_id = ? AND album_name = ?
                """,
                    (photo_id, album_name),
                )

                row = cursor.fetchone()
                if row:
                    columns = [
                        "photo_id",
                        "album_name",
                        "filename",
                        "local_path",
                        "file_size",
                        "checksum",
                        "sync_status",
                        "last_sync_attempt",
                        "error_count",
                        "created_at",
                    ]
                    return dict(zip(columns, row, strict=False))
                else:
                    return {}
        except Exception as e:
            self.logger.error(f"❌ Failed to get photo info: {e}")
            return {}

    def get_photos_for_retry(self, max_errors: int = 3) -> list[dict]:
        """Get photos that are eligible for retry based on error count.

        Args:
            max_errors: Maximum error count for retry eligibility

        Returns:
            List of photo dictionaries eligible for retry
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT photo_id, album_name, filename, local_path, file_size,
                           checksum, sync_status, last_sync_attempt, error_count, created_at
                    FROM photo_tracking
                    WHERE sync_status = 'failed' AND error_count < ?
                    ORDER BY last_sync_attempt ASC
                """,
                    (max_errors,),
                )

                columns = [
                    "photo_id",
                    "album_name",
                    "filename",
                    "local_path",
                    "file_size",
                    "checksum",
                    "sync_status",
                    "last_sync_attempt",
                    "error_count",
                    "created_at",
                ]
                return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"❌ Failed to get photos for retry: {e}")
            return []

    def close(self) -> None:
        """Close any open database connections.

        This is useful for ensuring proper cleanup, especially on Windows
        where file handles may prevent directory cleanup.
        """
        # Force garbage collection to close any remaining connections
        gc.collect()

        # Try to close any lingering connections by connecting and closing immediately
        try:
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                conn.close()
        except Exception:
            pass  # Ignore errors during cleanup

        # Also close connections to any backup files
        try:
            backup_pattern = str(self.db_path.with_suffix(".backup_*.db"))
            backup_files = glob.glob(backup_pattern)
            for backup_file in backup_files:
                try:
                    backup_path = Path(backup_file)
                    if backup_path.exists():
                        conn = sqlite3.connect(backup_path)
                        conn.close()
                except Exception:
                    pass  # Ignore errors during cleanup
        except Exception:
            pass  # Ignore errors during cleanup
