"""Confirm HTTP health and the exact revision of a running release."""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def check(port, revision):
    base = f"http://127.0.0.1:{port}"
    passed = True
    expected = {"/health": {"status": "available"}, "/version": {"commit": revision}}
    for path, body in expected.items():
        try:
            with urlopen(base + path, timeout=3) as response:
                code = response.status
                content = response.read().decode()
        except HTTPError as error:
            with error:
                code = error.code
                content = error.read().decode()
        except (URLError, TimeoutError) as error:
            print(f"{path}: {error}")
            passed = False
            continue
        print(f"{path} -> HTTP {code} {content}")
        try:
            passed = (code == 200 and json.loads(content) == body) and passed
        except ValueError:
            passed = False
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(check(int(sys.argv[1]), sys.argv[2]))
