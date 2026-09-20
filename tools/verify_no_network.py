#!/usr/bin/env python3
"""Run the end-to-end offline suite with Python outbound sockets blocked."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.errors import NetworkBlockedError
from src.offline import network_blocked


def guard_self_test() -> None:
    with network_blocked() as guard:
        try:
            socket.create_connection(("example.invalid", 443), timeout=0.01)
        except NetworkBlockedError:
            pass
        else:
            raise AssertionError("Network guard did not block socket.create_connection")
        if guard is None or len(guard.attempts) != 1:
            raise AssertionError("Network guard did not count its self-test attempt")
    print("NETWORK GUARD SELF-TEST: PASS")


def run_suite() -> None:
    from tests.test_offline import run_offline_suite

    with network_blocked() as guard:
        run_offline_suite()
        attempts = 0 if guard is None else len(guard.attempts)
    if attempts:
        raise AssertionError(f"Blocked network attempts were observed: {attempts}")
    print("NETWORK ATTEMPTS: 0")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-suite", action="store_true")
    args = parser.parse_args()
    if not args.self_test and not args.run_suite:
        parser.error("select --self-test or --run-suite")
    if args.self_test:
        guard_self_test()
    if args.run_suite:
        run_suite()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

