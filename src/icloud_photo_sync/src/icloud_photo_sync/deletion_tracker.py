"""Local deletion tracking using SQLite database."""

import sqlite3
from pathlib import Path
from datetime import datetime

from .logger import get_logger


class DeletionTracker:
    """Tracks locally deleted photos to prevent re-downloading."""

    def __init__(self, db_path: str = "deletion_tracker.db") -> None:
        """Initialize deletion tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()

    @property
    def logger(self):
        """Get the global logger instance."""
        return get_logger()

    def _init_database(self) -> None:
        """Initialize the SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS deleted_photos (
                        photo_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER,
                        original_path TEXT
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_filename 
                    ON deleted_photos(filename)
                """)
                conn.commit()
            self.logger.debug(f"Successfully initialized deletion tracker database: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize deletion tracker database: {e}")
            raise

    def add_deleted_photo(
        self,
        photo_id: str,
        filename: str,
        file_size: int | None = None,
        original_path: str | None = None
    ) -> None:
        """Record a photo as deleted.

        Args:
            photo_id: Unique photo identifier
            filename: Photo filename
            file_size: File size in bytes
            original_path: Original local file path
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO deleted_photos 
                (photo_id, filename, deleted_at, file_size, original_path)
                VALUES (?, ?, ?, ?, ?)
            """, (photo_id, filename, datetime.now(), file_size, original_path))
            conn.commit()
        self.logger.debug(f"📝 Recorded deleted photo: {filename}")

    def is_deleted(self, photo_id: str) -> bool:
        """Check if a photo is marked as deleted.

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

    def close(self) -> None:
        """Close any open database connections.

        This is useful for ensuring proper cleanup, especially on Windows
        where file handles may prevent directory cleanup.
        """
        # Since we use context managers (with statements) throughout the class,
        # connections are automatically closed. This method is here for
        # explicit cleanup if needed.
        pass
