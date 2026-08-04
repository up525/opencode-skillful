#!/usr/bin/env python3
"""Small, dependency-free GLM-4.6V-Flash image-analysis client.

Designed as a fallback for a text-only agent model. It accepts one or more
local image paths or HTTP(S) image URLs and prints GLM's final textual
observation to stdout.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.6v-flash"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze images with Zhipu GLM-4.6V-Flash."
    )
    parser.add_argument(
        "--image",
        action="append",
        required=True,
        help="Local image path or HTTP(S) URL. Repeat for multiple images.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Task-specific instruction for the visual model.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("GLM_VISION_MODEL", DEFAULT_MODEL),
        help=f"Model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("ZHIPU_API_ENDPOINT", DEFAULT_ENDPOINT),
        help="Chat completions endpoint.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP timeout in seconds (default: 120).",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Disable GLM thinking mode for faster/simple visual tasks.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the complete API JSON response instead of only content.",
    )
    return parser.parse_args()


def api_key() -> str:
    value = os.getenv("ZHIPU_API_KEY") or os.getenv("Z_AI_API_KEY")
    if not value:
        raise RuntimeError(
            "Missing API key. Set ZHIPU_API_KEY (preferred) or Z_AI_API_KEY."
        )
    return value


def image_value(source: str) -> str:
    if source.startswith(("http://", "https://")):
        return source

    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Image does not exist or is not a file: {path}")

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise OSError(f"Unable to read image {path}: {exc}") from exc

    # Zhipu's official GLM-4.6V-Flash examples pass raw Base64 in image_url.url.
    return base64.b64encode(data).decode("ascii")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    for source in args.image:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_value(source)},
            }
        )
    content.append({"type": "text", "text": args.prompt})

    return {
        "model": args.model,
        "messages": [{"role": "user", "content": content}],
        "thinking": {"type": "disabled" if args.no_thinking else "enabled"},
        "stream": False,
    }


def call_api(
    endpoint: str,
    key: str,
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "deepseek-glm-vision-skill/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Zhipu API returned HTTP {exc.code}: {details}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Zhipu API: {exc.reason}") from exc

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Zhipu API returned invalid JSON: {raw[:500]}") from exc

    if not isinstance(result, dict):
        raise RuntimeError("Zhipu API returned an unexpected response shape.")
    return result


def extract_content(result: dict[str, Any]) -> str:
    try:
        message = result["choices"][0]["message"]
        content = message["content"]
    except (KeyError, IndexError, TypeError) as exc:
        error = result.get("error") or result
        raise RuntimeError(f"No assistant content in API response: {error}") from exc

    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    try:
        result = call_api(
            endpoint=args.endpoint,
            key=api_key(),
            payload=build_payload(args),
            timeout=args.timeout,
        )
        if args.raw:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(extract_content(result))
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"glm_vision error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
