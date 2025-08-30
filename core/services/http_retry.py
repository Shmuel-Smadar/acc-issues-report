import time
import random
import datetime as dt
import email.utils
import requests


def _parse_retry_after(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(int(value))
    except Exception:
        try:
            d = email.utils.parsedate_to_datetime(value)
            if not d:
                return None
            if d.tzinfo is None:
                d = d.replace(tzinfo=dt.timezone.utc)
            now = dt.datetime.now(dt.timezone.utc)
            secs = (d - now).total_seconds()
            return max(0.0, secs)
        except Exception:
            return None


def _sleep_backoff(attempt: int, retry_after_header: str | None, backoff_base: float, backoff_max: float):
    ra = _parse_retry_after(retry_after_header) if retry_after_header else None
    if ra is not None:
        delay = ra
    else:
        delay = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, backoff_base)
    delay = min(delay, backoff_max)
    if delay > 0:
        time.sleep(delay)


def request_with_retries(make_request, get_headers, refresh_on_401, *, max_retries: int, backoff_base: float, backoff_max: float) -> requests.Response:
    attempt = 1
    did_refresh = False
    while True:
        headers = get_headers()
        try:
            resp = make_request(headers)
        except requests.RequestException:
            if attempt >= max_retries:
                raise
            _sleep_backoff(attempt, None, backoff_base, backoff_max)
            attempt += 1
            continue
        if resp.status_code == 401:
            if did_refresh:
                return resp
            refresh_on_401()
            did_refresh = True
            headers = get_headers()
            resp = make_request(headers)
            if resp.status_code == 401:
                return resp
        if resp.status_code == 429 or (500 <= resp.status_code < 600):
            if attempt >= max_retries:
                return resp
            retry_after = resp.headers.get("Retry-After") if isinstance(resp.headers, dict) else None
            _sleep_backoff(attempt, retry_after, backoff_base, backoff_max)
            attempt += 1
            continue
        return resp
