"""A re-entrant Python socket guard used in normal offline operation and tests."""

from __future__ import annotations

import socket
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from src.errors import NetworkBlockedError


@dataclass(frozen=True)
class NetworkAttempt:
    operation: str
    target: str


class NetworkGuard:
    """Patch outbound Python socket entry points and count blocked attempts."""

    _lock = threading.RLock()
    _depth = 0
    _attempts: list[NetworkAttempt] = []
    _originals: dict[str, object] = {}

    def __enter__(self) -> "NetworkGuard":
        with self._lock:
            if self.__class__._depth == 0:
                self.__class__._attempts = []
                self.__class__._originals = {
                    "create_connection": socket.create_connection,
                    "socket_connect": socket.socket.connect,
                    "socket_connect_ex": socket.socket.connect_ex,
                    "getaddrinfo": socket.getaddrinfo,
                }
                socket.create_connection = _blocked_create_connection
                socket.socket.connect = _blocked_socket_connect
                socket.socket.connect_ex = _blocked_socket_connect_ex
                socket.getaddrinfo = _blocked_getaddrinfo
            self.__class__._depth += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        with self._lock:
            self.__class__._depth -= 1
            if self.__class__._depth == 0:
                socket.create_connection = self.__class__._originals["create_connection"]  # type: ignore[assignment]
                socket.socket.connect = self.__class__._originals["socket_connect"]  # type: ignore[assignment]
                socket.socket.connect_ex = self.__class__._originals["socket_connect_ex"]  # type: ignore[assignment]
                socket.getaddrinfo = self.__class__._originals["getaddrinfo"]  # type: ignore[assignment]
                self.__class__._originals = {}

    @property
    def attempts(self) -> tuple[NetworkAttempt, ...]:
        return tuple(self.__class__._attempts)

    @classmethod
    def _deny(cls, operation: str, target: object) -> None:
        attempt = NetworkAttempt(operation=operation, target=repr(target))
        cls._attempts.append(attempt)
        raise NetworkBlockedError(
            f"Outbound networking is disabled (operation={operation}, target={target!r})."
        )

@contextmanager
def network_blocked(enabled: bool = True) -> Iterator[NetworkGuard | None]:
    """Block outbound Python networking for the duration of the context."""

    if not enabled:
        yield None
        return
    with NetworkGuard() as guard:
        yield guard


def _blocked_create_connection(address, *args, **kwargs):
    NetworkGuard._deny("socket.create_connection", address)


def _blocked_socket_connect(sock, address):
    NetworkGuard._deny("socket.socket.connect", address)


def _blocked_socket_connect_ex(sock, address):
    NetworkGuard._deny("socket.socket.connect_ex", address)


def _blocked_getaddrinfo(host, port, *args, **kwargs):
    NetworkGuard._deny("socket.getaddrinfo", (host, port))
