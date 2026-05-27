from __future__ import annotations

import json
from urllib import request


def send_webhook_text(webhook_url: str, text: str) -> None:
    if not webhook_url:
        raise ValueError("webhook_url is required")

    payload = json.dumps({"msgtype": "text", "text": {"content": text}}).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=15) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"webhook request failed: HTTP {resp.status}")

