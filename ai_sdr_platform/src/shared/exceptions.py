class SDRDomainError(Exception):
    """Base domain exception for the SDR platform."""


class ICPValidationError(SDRDomainError):
    """Raised when an ICP payload fails business validation."""


class ValidationError(SDRDomainError):
    """Raised when input validation fails."""
