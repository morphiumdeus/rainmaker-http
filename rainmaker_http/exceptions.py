class RainmakerError(Exception):
    """Base error for rainmaker-http"""


class RainmakerAuthError(RainmakerError):
    """Authentication / login failures"""


class RainmakerConnectionError(RainmakerError, RuntimeError):
    """Raised for transport / network problems"""


class RainmakerSetError(RainmakerError):
    """Raised when a parameter set action fails"""
