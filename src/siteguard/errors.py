"""Domain-specific exceptions with messages suitable for CLI and dashboard users."""


class SiteGuardError(Exception):
    """Base exception for expected SiteGuard failures."""


class VideoInputError(SiteGuardError):
    """The source video is missing, unsupported, or cannot be opened."""


class VideoDecodeError(SiteGuardError):
    """No usable frames could be decoded from the source video."""


class VideoWriterError(SiteGuardError):
    """An annotated MP4 writer could not be initialized."""


class ModelLoadError(SiteGuardError):
    """A required inference model could not be loaded."""
