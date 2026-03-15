from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request


class HTTPError(RuntimeError):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"HTTP {status}: {detail[:200]}")
        self.status = status
        self.detail = detail


def parse_jsonp(payload: str) -> dict:
    payload = payload.strip()
    if payload.startswith("{"):
        return json.loads(payload)
    start = payload.find("(")
    end = payload.rfind(")")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Unable to parse JSONP.")
    return json.loads(payload[start + 1 : end].strip())


def http_get_bytes(url: str, params: dict[str, str | int], headers: dict[str, str], timeout_s: int) -> bytes:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPError(exc.code, detail) from exc


def http_get_json(
    url: str,
    params: dict[str, str | int],
    headers: dict[str, str],
    timeout_s: int,
) -> dict:
    body = http_get_bytes(url, params, headers, timeout_s).decode("utf-8", errors="replace")
    return parse_jsonp(body)


def try_get_json(
    urls: list[str],
    params: dict[str, str | int],
    headers: dict[str, str],
    *,
    timeout_s: int,
    retries: int,
    rate_limit_ms: int,
) -> dict:
    last_error: Exception | None = None
    for url in urls:
        attempt = 0
        while True:
            if rate_limit_ms > 0:
                time.sleep(rate_limit_ms / 1000.0)
            try:
                return http_get_json(url, params, headers, timeout_s)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                attempt += 1
                if attempt > retries:
                    break
                time.sleep(0.4 + random.random() * 0.6)
    raise RuntimeError(f"All JSON endpoints failed: {last_error}")


def try_get_bytes(
    urls: list[str],
    params: dict[str, str | int],
    headers: dict[str, str],
    *,
    timeout_s: int,
    retries: int,
    rate_limit_ms: int,
) -> bytes:
    last_error: Exception | None = None
    for url in urls:
        attempt = 0
        while True:
            if rate_limit_ms > 0:
                time.sleep(rate_limit_ms / 1000.0)
            try:
                return http_get_bytes(url, params, headers, timeout_s)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                attempt += 1
                if attempt > retries:
                    break
                time.sleep(0.4 + random.random() * 0.6)
    raise RuntimeError(f"All content endpoints failed: {last_error}")

