import time
from typing import Dict, Optional, Any
import requests

class TorHttpClient:
    """Lightweight HTTP client that routes requests through a Tor SOCKS proxy."""

    def __init__(self, proxy_url: str = "socks5h://127.0.0.1:9050", timeout: int = 20):
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, max_bytes: int = 4096) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            response = requests.get(
                url,
                headers=headers,
                proxies=self.proxies,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Tor-routed request failed: {exc}") from exc

        elapsed_ms = (time.perf_counter() - start) * 1000
        body_bytes = response.content or b""
        truncated = len(body_bytes) > max_bytes
        preview = body_bytes[:max_bytes]

        return {
            "url": url,
            "status_code": response.status_code,
            "elapsed_ms": round(elapsed_ms, 2),
            "headers": dict(response.headers),
            "text_preview": preview.decode(errors="replace"),
            "preview_truncated": truncated,
        }
