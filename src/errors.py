"""Project-specific errors with actionable offline diagnostics."""


class OfflineModelMissingError(FileNotFoundError):
    """Raised when an artifact required for offline inference is absent."""


class OfflineConfigurationError(RuntimeError):
    """Raised when configuration could permit an online lookup."""


class NetworkBlockedError(ConnectionError):
    """Raised when code attempts networking while the offline guard is active."""

