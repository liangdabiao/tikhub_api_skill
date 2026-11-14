#!/usr/bin/env python3
"""TikHub API Client - authenticated HTTP calls to TikHub REST endpoints.

No API token is baked into this file. Token resolution order:
  1. --token
  2. TIKHUB_API_TOKEN
  3. TIKHUB_TOKEN
  4. .env in this directory or a parent (never commit credentials)

Every call that needs auth fails fast with an actionable message instead of
silently sending "Bearer " and returning a confusing 403.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_URL_CHINA = "https://api.tikhub.dev"
BASE_URL_INTERNATIONAL = "https://api.tikhub.io"
# Cloudflare blocks urllib's default "Python-urllib/x.y" signature (error 1010).
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
# Git Bash / MSYS2 rewrites a leading /api/v1/... argument into
# e.g. D:/WorkBuddy/resources/vendor/PortableGit/api/v1/...
# This captures the real API path from either form.
API_PATH_RE = re.compile(r"(?:^|/)(api/v\d+/.*)$", re.IGNORECASE)


class TokenMissingError(RuntimeError):
    pass


def normalize_path(path: str) -> str:
    """Return a clean '/api/v1/...' path even after MSYS2 mangling."""
    path = path.strip()
    if path.startswith(("http://", "https://")):
        return path
    normalized = path.replace("\\", "/")
    match = API_PATH_RE.search(normalized)
    if match:
        return "/" + match.group(1)
    if not path.startswith("/"):
        path = "/" + path
    return path


def read_env_token() -> Optional[str]:
    for key in ("TIKHUB_API_TOKEN", "TIKHUB_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return None


def read_dotenv_token() -> Optional[str]:
    for root in [SCRIPT_DIR, *list(SCRIPT_DIR.parents)[:5]]:
        env_file = root / ".env"
        if not env_file.is_file():
            continue
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[7:].strip()
            value = value.strip().strip('"').strip("'")
            if key in ("TIKHUB_API_TOKEN", "TIKHUB_TOKEN") and value:
                if "Your_API_Token" not in value:
                    return value
    return None


def restore_msys_value(value: str) -> str:
    """MSYS2 also rewrites '/api/v1/...' inside a 'k=v' value into a drive path."""
    if re.match(r"^[A-Za-z]:/", value):
        match = API_PATH_RE.search(value.replace("\\", "/"))
        if match:
            return "/" + match.group(1)
    return value


def parse_kv(items: list[str]) -> Dict[str, str]:
    """Parse 'k=v' and 'a=1&b=2' without decoding (urlencode does that later)."""
    params: Dict[str, str] = {}
    for item in items:
        for pair in item.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key.strip()] = restore_msys_value(value)
    return params


def summarize(obj: Any) -> Any:
    """Compact shape of a large response, so it does not flood the context."""
    if not isinstance(obj, dict):
        return {"type": type(obj).__name__}
    out: Dict[str, Any] = {}
    for key, value in obj.items():
        if isinstance(value, dict):
            out[key] = {"type": "dict", "keys": list(value.keys())[:20]}
        elif isinstance(value, list):
            first = value[0] if value else None
            out[key] = {
                "type": "list",
                "count": len(value),
                "first_item_keys": list(first.keys())[:20] if isinstance(first, dict) else None,
            }
        elif isinstance(value, str) and len(value) > 200:
            out[key] = value[:200] + "...(truncated)"
        else:
            out[key] = value
    return out


def error_hint(result: Dict[str, Any]) -> str:
    """Pull TikHub's human-readable reason out of an HTTP error body.

    The 400 body carries message_zh / message / docs / router, which is far
    more useful for diagnosis than "HTTP 400: Bad Request" alone.
    """
    if not isinstance(result, dict):
        return ""
    details = result.get("details")
    node = details.get("detail") if isinstance(details, dict) else None
    if not isinstance(node, dict):
        node = details if isinstance(details, dict) else None
    if isinstance(node, dict):
        parts = []
        for key in ("message_zh", "message", "msg", "detail"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
                break
        for key in ("router", "docs"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(key + ": " + value.strip())
        if parts:
            return " | ".join(parts)[:600]
    if isinstance(details, str) and details.strip():
        return details.strip()[:600]
    return ""


class TikHubAPIClient:
    """Client for making requests to TikHub APIs."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        use_china_domain: bool = False,
        timeout: float = 30.0,
        max_retries: int = 0,
        require_token: bool = True,
    ):
        self.api_token = api_token or read_env_token() or read_dotenv_token() or ""
        if require_token and not self.api_token:
            raise TokenMissingError(
                "No TikHub API token found.\n"
                "  export TIKHUB_API_TOKEN=<your token>   (Git Bash / macOS / Linux)\n"
                "  set TIKHUB_API_TOKEN=<your token>      (Windows CMD)\n"
                "  or put TIKHUB_API_TOKEN=<your token> in a .env outside the repo\n"
                "  or pass --token <your token>\n"
                "  (use --no-auth only for public endpoints such as health check)"
            )

        env_url = os.environ.get("TIKHUB_BASE_URL", "").strip()
        if base_url or env_url:
            self.base_url = (base_url or env_url).rstrip("/")
        elif use_china_domain or os.environ.get("TIKHUB_CHINA_DOMAIN", "").strip() == "1":
            self.base_url = BASE_URL_CHINA
        else:
            self.base_url = BASE_URL_INTERNATIONAL

        self.timeout = timeout
        # Default 0: TikHub bills per request, so retrying automatically can
        # silently spend credits twice. Opt in with --retries N.
        self.max_retries = max(0, max_retries)

    def _build_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        path = normalize_path(path)
        url = path if path.startswith(("http://", "https://")) else f"{self.base_url}{path}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}{'&' if '?' in url else '?'}{query}"
        return url

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": os.environ.get("TIKHUB_USER_AGENT", "").strip() or DEFAULT_USER_AGENT,
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make one HTTP request (with optional retry on 429 / 5xx / network)."""
        url = self._build_url(path, params)
        req_headers = self._build_headers()
        if headers:
            req_headers.update(headers)

        data = None
        if body is not None:
            if isinstance(body, (dict, list)):
                data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            else:
                data = str(body).encode("utf-8")

        attempt = 0
        while True:
            req = urllib.request.Request(
                url, data=data, headers=req_headers, method=method.upper()
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    text = response.read().decode("utf-8", errors="replace")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"_raw_text": text, "_note": "response is not JSON"}

            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                try:
                    details: Any = json.loads(error_body)
                except json.JSONDecodeError:
                    details = error_body[:1000]
                retryable = exc.code == 429 or exc.code >= 500
                if retryable and attempt < self.max_retries:
                    attempt += 1
                    time.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                return {"error": f"HTTP {exc.code}: {exc.reason}",
                        "status_code": exc.code, "details": details}

            except urllib.error.URLError as exc:
                if attempt < self.max_retries:
                    attempt += 1
                    time.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                return {"error": f"Connection error: {exc.reason}"}

            except Exception as exc:  # noqa: BLE001 - CLI must always return JSON
                return {"error": f"Request failed: {exc}"}

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.request("POST", path, params=params, body=body)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Call a TikHub API endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  api_client.py GET /api/v1/health/check --no-auth
  api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"
  api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming" "count=10"
  api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"lego"}'
  api_client.py GET /api/v1/xiaohongshu/app_v2/search_notes "keyword=food" --china --output result.json
""",
    )
    parser.add_argument("method", help="GET or POST")
    parser.add_argument("path", help="endpoint path, e.g. /api/v1/tiktok/web/fetch_user_profile")
    parser.add_argument("args", nargs="*", help="k=v query params; a leading {...} is a POST body")
    parser.add_argument("--body", help='JSON body for POST, \'{"key":"value"}\'')
    parser.add_argument("--token", help="TikHub API token (overrides env/.env)")
    parser.add_argument("--base-url", help="override base URL")
    parser.add_argument("--china", action="store_true", help="use https://api.tikhub.dev")
    parser.add_argument("--no-auth", action="store_true", help="skip token requirement (public endpoints)")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=0, help="retries on 429/5xx (default 0, billed per call)")
    parser.add_argument("--output", help="write full JSON to a file instead of stdout")
    parser.add_argument("--compact", action="store_true", help="minified JSON output")
    parser.add_argument("--summary", action="store_true", help="print only response shape + scalars")
    args = parser.parse_args()

    method = args.method.upper()
    if method not in ("GET", "POST"):
        print(f"ERROR: unsupported method {method} (only GET / POST)", file=sys.stderr)
        return 2

    params: Dict[str, str] = {}
    body: Optional[Any] = None
    kv_items = []
    for item in args.args:
        if item.lstrip().startswith("{"):
            try:
                body = json.loads(item)
            except json.JSONDecodeError as exc:
                print(f"ERROR: invalid JSON body: {exc}", file=sys.stderr)
                return 2
        else:
            kv_items.append(item)
    if args.body:
        try:
            body = json.loads(args.body)
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid --body JSON: {exc}", file=sys.stderr)
            return 2
    params = parse_kv(kv_items)

    if body is not None and method == "GET":
        print("ERROR: a JSON body was supplied for GET; use POST or k=v params",
              file=sys.stderr)
        return 2

    try:
        client = TikHubAPIClient(
            api_token=args.token,
            base_url=args.base_url,
            use_china_domain=args.china,
            timeout=args.timeout,
            max_retries=args.retries,
            require_token=not args.no_auth,
        )
    except TokenMissingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if method == "GET":
        result = client.get(args.path, params)
    else:
        result = client.post(args.path, body=body, params=params)

    rendered = json.dumps(
        summarize(result) if args.summary else result,
        ensure_ascii=False,
        indent=None if args.compact else 2,
        separators=(",", ":") if args.compact else None,
    )
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Wrote {out.resolve()} ({out.stat().st_size} bytes)")
        if isinstance(result, dict) and "error" in result:
            print(f"API returned an error: {result['error']}")
    else:
        print(rendered)
        if len(rendered) > 30000 and not args.summary:
            print("\n[note] large response - consider --summary or --output result.json",
                  file=sys.stderr)

    if isinstance(result, dict) and "error" in result:
        hint = error_hint(result)
        print("API error: %s%s" % (result["error"], " | " + hint if hint else ""),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
