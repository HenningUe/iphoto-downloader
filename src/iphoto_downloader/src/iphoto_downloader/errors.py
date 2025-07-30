class PhotoSyncError(Exception):
    """Base class for all exceptions raised by the photo sync module."""

    pass


class UserInteractionRequiredErrorMixin:
    """Exception raised when user interaction is required."""


class ConfigFileMissingError(PhotoSyncError, UserInteractionRequiredErrorMixin):
    """Raised when the configuration file is missing."""

    def __init__(self, message="Configuration file is missing. Please create one."):
        super().__init__(message)
