"""Small source fixture; the indexer must never execute this module."""

from .errors import TimeoutError as RequestTimeout

DEFAULT_TIMEOUT = 10


def trace(function):
    return function


class Client:
    """A client with a configurable timeout."""

    @trace
    async def send_request(
        self,
        url: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Send a request and enforce the connection timeout."""
        if timeout <= 0:
            raise RequestTimeout("connection timeout")
        return url


def calculate_checksum(payload: bytes) -> int:
    """Calculate a checksum for payload bytes."""
    return sum(payload)


raise RuntimeError("This fixture must only be parsed, never imported")
