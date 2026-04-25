from __future__ import annotations

import argparse
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def wait_for_http(url: str, *, timeout: float = 60.0, interval: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=min(interval, 5.0)) as response:
                if 200 <= response.status < 500:
                    return
        except HTTPError as error:
            if 200 <= error.code < 500:
                return
            last_error = error
        except URLError as error:
            last_error = error
        except OSError as error:
            last_error = error

        time.sleep(interval)

    raise TimeoutError(f"Timed out waiting for {url}: {last_error}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    command = list(args.command)

    if command[:1] == ["--"]:
        command = command[1:]

    wait_for_http(args.url, timeout=args.timeout, interval=args.interval)

    if not command:
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
