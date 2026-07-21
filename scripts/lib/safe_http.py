#!/usr/bin/env python3
"""Safe HTTP helpers shared by network-facing SEO scripts."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse, urlunparse

try:
    import requests
except ImportError as exc:  # pragma: no cover - import-time environment guard
    raise SystemExit("Error: requests library required. Install with: pip install requests") from exc


AGENTIC_SEO_USER_AGENT = (
    "Mozilla/5.0 (compatible; AgenticSEOSkill/1.0; "
    "+https://github.com/Bhanunamikaze/Agentic-SEO-Skill)"
)
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_REDIRECTS = 5
DEFAULT_MAX_RESPONSE_BYTES = 5 * 1024 * 1024

DEFAULT_HEADERS = {
    "User-Agent": AGENTIC_SEO_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class SafeHTTPError(requests.exceptions.RequestException):
    """Raised when a request is blocked by safe HTTP policy."""


def default_headers(extra: dict | None = None) -> dict:
    """Return request headers with the shared Agentic SEO User-Agent."""
    headers = dict(DEFAULT_HEADERS)
    if extra:
        headers.update(extra)
    headers["User-Agent"] = AGENTIC_SEO_USER_AGENT
    return headers


def normalize_url(url: str, default_scheme: str = "https") -> str:
    """Normalize a user-supplied URL, adding https:// when no scheme exists."""
    if not url:
        raise SafeHTTPError("URL is required")
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"{default_scheme}://{url}"
        parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SafeHTTPError(f"Invalid URL scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise SafeHTTPError("URL must include a hostname")
    return urlunparse(parsed)


def _port_for(parsed) -> int:
    if parsed.port:
        return parsed.port
    return 443 if parsed.scheme == "https" else 80


def _is_blocked_ip(ip_text: str) -> bool:
    ip = ipaddress.ip_address(ip_text)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_reserved
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_safe_url(url: str) -> str:
    """Validate URL scheme and reject hosts resolving to private/internal IPs."""
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    hostname = parsed.hostname

    try:
        if _is_blocked_ip(hostname):
            raise SafeHTTPError(f"Blocked: URL resolves to private/internal IP ({hostname})")
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(hostname, _port_for(parsed), type=socket.SOCK_STREAM)
    except socket.gaierror:
        return normalized

    resolved_ips = sorted({info[4][0] for info in infos})
    for ip_text in resolved_ips:
        try:
            if _is_blocked_ip(ip_text):
                raise SafeHTTPError(f"Blocked: URL resolves to private/internal IP ({ip_text})")
        except ValueError as exc:
            raise SafeHTTPError(f"Blocked: could not validate resolved IP ({ip_text})") from exc

    return normalized


def _consume_capped(response, max_response_bytes: int | None):
    if max_response_bytes is None:
        response._content = response.content
        return response

    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_response_bytes:
            response.close()
            raise SafeHTTPError(f"Response exceeded {max_response_bytes} byte safety limit")
        chunks.append(chunk)
    response._content = b"".join(chunks)
    response._content_consumed = True
    return response


def safe_request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    timeout: int | float = DEFAULT_TIMEOUT,
    allow_redirects: bool = True,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    max_response_bytes: int | None = DEFAULT_MAX_RESPONSE_BYTES,
    stream: bool = False,
    session=None,
    **kwargs,
):
    """
    Execute an HTTP request with SSRF guards, redirect checks, TLS verification,
    timeouts, and a response-size cap.
    """
    current = assert_safe_url(url)
    request_headers = default_headers(headers)
    requester = session or requests.Session()
    history = []
    method = method.upper()
    kwargs["verify"] = True

    for _ in range(max_redirects + 1):
        response = requester.request(
            method,
            current,
            headers=request_headers,
            timeout=timeout,
            allow_redirects=False,
            stream=True,
            **kwargs,
        )

        if not (allow_redirects and response.is_redirect):
            response.history = history
            if method == "HEAD":
                response.close()
                return response
            if stream:
                return response
            return _consume_capped(response, max_response_bytes)

        location = response.headers.get("Location")
        if not location:
            response.history = history
            if method == "HEAD":
                response.close()
                return response
            if stream:
                return response
            return _consume_capped(response, max_response_bytes)

        response.close()
        history.append(response)
        if len(history) > max_redirects:
            raise requests.exceptions.TooManyRedirects(f"Too many redirects (max {max_redirects})")

        next_url = assert_safe_url(urljoin(current, location))
        if response.status_code == 303 and method not in ("GET", "HEAD"):
            method = "GET"
            kwargs.pop("data", None)
            kwargs.pop("json", None)
        current = next_url

    raise requests.exceptions.TooManyRedirects(f"Too many redirects (max {max_redirects})")


def safe_get(url: str, **kwargs):
    return safe_request("GET", url, **kwargs)


def safe_head(url: str, **kwargs):
    return safe_request("HEAD", url, **kwargs)


def safe_post(url: str, **kwargs):
    return safe_request("POST", url, **kwargs)
