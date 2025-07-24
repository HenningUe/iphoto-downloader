"""Continuous execution mode implementation for iCloud Photo Sync Tool."""

import signal
import time
import threading
from datetime import datetime, timedelta
from typing import Optional

from .config import BaseConfig
from .sync import PhotoSyncer
from .deletion_tracker import DeletionTracker
from .logger import get_logger


class ContinuousRunner:
    """Handles continuous execution mode with sync intervals and maintenance scheduling."""

    def __init__(self, config: BaseConfig) -> None:
        """Initialize continuous runner.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger()
        self.running = False
        self.shutdown_requested = False
        self.last_maintenance_time: Optional[datetime] = None

        # Synchronization for maintenance operations
        self.maintenance_lock = threading.Lock()
        self.maintenance_in_progress = threading.Event()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        self.logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def run_single_sync(self) -> bool:
        """Run a single synchronization cycle.

        Returns:
            True if sync completed successfully, False otherwise
        """
        # Wait for any maintenance operations to complete before starting sync
        if self.maintenance_in_progress.is_set():
            self.logger.info(
                "Waiting for database maintenance to complete before starting single sync..."
            )
            self.maintenance_in_progress.wait()
            self.logger.info("Database maintenance completed, proceeding with single sync")

        self.logger.info("Starting single synchronization run")
        syncer = PhotoSyncer(self.config)

        try:
            success = syncer.sync()

            if success:
                self.logger.info("✅ Single sync completed successfully")
            else:
                self.logger.error("❌ Single sync failed")

            return success
        finally:
            # Ensure proper cleanup
            syncer.cleanup()

    def run_continuous_sync(self) -> None:
        """Run continuous synchronization with scheduled maintenance."""
        self.logger.info("Starting continuous execution mode")
        self.logger.info(f"Sync interval: {self.config.sync_interval_minutes} minutes")
        self.logger.info(f"Maintenance interval: {self.config.maintenance_interval_hours} hours")

        self.running = True
        self.last_maintenance_time = datetime.now()

        # Start maintenance thread
        maintenance_thread = threading.Thread(
            target=self._maintenance_worker,
            daemon=True,
            name="MaintenanceWorker"
        )
        maintenance_thread.start()

        try:
            while self.running and not self.shutdown_requested:
                # Run sync cycle
                self._run_sync_cycle()

                if self.shutdown_requested:
                    break

                # Wait for next sync interval
                self._wait_for_next_sync()

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.running = False
            self.logger.info("Continuous execution mode stopped")

    def _run_sync_cycle(self) -> None:
        """Run a single sync cycle with error handling."""
        try:
            # Wait for any maintenance operations to complete before starting sync
            if self.maintenance_in_progress.is_set():
                self.logger.info(
                    "Waiting for database maintenance to complete before starting sync..."
                )
                self.maintenance_in_progress.wait()
                self.logger.info("Database maintenance completed, proceeding with sync")

            cycle_start = datetime.now()
            self.logger.info(f"Starting sync cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")

            syncer = PhotoSyncer(self.config)

            try:
                success = syncer.sync()

                cycle_end = datetime.now()
                duration = cycle_end - cycle_start

                if success:
                    duration_seconds = duration.total_seconds()
                    self.logger.info(
                        f"✅ Sync cycle completed successfully in {duration_seconds:.1f} seconds"
                    )
                else:
                    duration_seconds = duration.total_seconds()
                    self.logger.error(
                        f"❌ Sync cycle failed after {duration_seconds:.1f} seconds"
                    )

            finally:
                # Ensure proper cleanup
                syncer.cleanup()

        except Exception as e:
            self.logger.error(f"Sync cycle failed with error: {e}", exc_info=True)

    def _wait_for_next_sync(self) -> None:
        """Wait for the next sync interval, checking for shutdown periodically."""
        wait_seconds = int(self.config.sync_interval_minutes * 60)
        self.logger.info(f"Waiting {self.config.sync_interval_minutes} minutes until next sync...")

        # Check for shutdown every 5 seconds while waiting
        check_interval = 5
        elapsed = 0

        while elapsed < wait_seconds and not self.shutdown_requested:
            time.sleep(min(check_interval, wait_seconds - elapsed))
            elapsed += check_interval

    def _maintenance_worker(self) -> None:
        """Background worker thread for database maintenance."""
        self.logger.info("Database maintenance worker started")

        while self.running and not self.shutdown_requested:
            try:
                # Check if maintenance is due
                if self._is_maintenance_due():
                    self._perform_maintenance()

                # Check every minute for maintenance schedule
                time.sleep(60)

            except Exception as e:
                self.logger.error(f"Maintenance worker error: {e}", exc_info=True)
                # Sleep a bit before retrying to avoid tight error loops
                time.sleep(300)  # 5 minutes

        self.logger.info("Database maintenance worker stopped")

    def _is_maintenance_due(self) -> bool:
        """Check if database maintenance is due.

        Returns:
            True if maintenance should be performed now
        """
        if not self.last_maintenance_time:
            return True
        maintenance_interval = timedelta(seconds=int(self.config.maintenance_interval_hours * 3600))
        return datetime.now() - self.last_maintenance_time >= maintenance_interval

    def _perform_maintenance(self) -> None:
        """Perform scheduled database maintenance."""
        # Acquire maintenance lock to ensure exclusive access
        with self.maintenance_lock:
            try:
                self.logger.info("Starting scheduled database maintenance")

                # Signal that maintenance is in progress to pause sync operations
                self.maintenance_in_progress.set()

                # Create deletion tracker for maintenance operations
                deletion_tracker = DeletionTracker(
                    str(self.config.sync_directory / "deletion_tracker.db")
                )

                try:
                    # Perform integrity check
                    if deletion_tracker.check_database_integrity():
                        self.logger.info("Database integrity check passed")
                    else:
                        self.logger.warning("Database integrity check failed, attempting recovery")
                        if deletion_tracker.recover_from_backup():
                            self.logger.info("Database recovered from backup successfully")
                        else:
                            self.logger.error("Database recovery failed")

                    # Create backup
                    if deletion_tracker.create_backup():
                        self.logger.info("Database backup created successfully")
                    else:
                        self.logger.warning("Database backup creation failed")

                    # Update last maintenance time
                    self.last_maintenance_time = datetime.now()
                    self.logger.info("Scheduled database maintenance completed")

                finally:
                    deletion_tracker.close()

            except Exception as e:
                self.logger.error(f"Database maintenance failed: {e}", exc_info=True)
            finally:
                # Clear maintenance flag to allow sync operations to resume
                self.maintenance_in_progress.clear()
                self.logger.info("Database maintenance finished, sync operations can resume")

    def stop(self) -> None:
        """Stop the continuous runner gracefully."""
        self.logger.info("Stopping continuous runner...")
        self.shutdown_requested = True
        self.running = False


def run_execution_mode(config: BaseConfig) -> bool:
    """Run the application in the configured execution mode.

    Args:
        config: Application configuration

    Returns:
        True if execution completed successfully, False otherwise
    """
    logger = get_logger()
    runner = ContinuousRunner(config)

    if config.execution_mode == 'single':
        logger.info("Running in single execution mode")
        return runner.run_single_sync()

    elif config.execution_mode == 'continuous':
        logger.info("Running in continuous execution mode")
        try:
            runner.run_continuous_sync()
            return True
        except Exception as e:
            logger.error(f"Continuous execution failed: {e}", exc_info=True)
            return False
    else:
        logger.error(f"Unknown execution mode: {config.execution_mode}")
        return False
