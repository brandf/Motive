class MotiveConfigError(Exception):
    """Base exception for configuration-related errors in Motive."""
    pass

class ConfigNotFoundError(MotiveConfigError):
    """Raised when a configuration file is not found."""
    pass

class ConfigParseError(MotiveConfigError):
    """Raised when there is an error parsing a configuration file (e.g., YAML syntax error)."""
    pass

class ConfigValidationError(MotiveConfigError):
    """Raised when a configuration fails Pydantic validation."""
    pass
