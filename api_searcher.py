#!/usr/bin/env python3
"""TikHub API Searcher - search / inspect endpoints in the local OpenAPI spec.

Data source: ``openapi.json`` (OpenAPI 3.0.1) next to this script.
Spec lookup order: --spec / TIKHUB_OPENAPI_PATH, script directory, parents.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}
TOKEN_RE = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def find_spec(explicit: Optional[str] = None) -> Path:
    """Locate openapi.json without hard-coding a machine-specific path."""
    candidates: List[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env = os.environ.get("TIKHUB_OPENAPI_PATH")
    if env:
        candidates.append(Path(env).expanduser())
    # Self-contained: the spec normally sits right next to this script.
    # Parent lookup is only a convenience for development checkouts.
    for root in [SCRIPT_DIR, *list(SCRIPT_DIR.parents)[:5]]:
        candidates.append(root / "openapi.json")

    seen = set()
    for candidate in candidates:
        try:
            key = candidate.resolve()
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "openapi.json not found. Set TIKHUB_OPENAPI_PATH or pass --spec <path>.\n"
        "Checked: this skill folder and its parent directories."
    )


def tokenize(query: str) -> List[tuple]:
    """Split into (token, weight). Chinese runs also produce bigrams.

    Bigrams get a lower weight so that partial Chinese matches help recall
    without outranking exact keyword hits.
    """
    tokens: List[tuple] = []
    for raw in TOKEN_RE.findall(query.lower().strip()):
        tokens.append((raw, 1.0))
        if CJK_RE.search(raw) and len(raw) > 2:
            tokens.extend((raw[i : i + 2], 0.4) for i in range(len(raw) - 1))
    # dedupe, keeping the highest weight
    best: Dict[str, float] = {}
    for token, weight in tokens:
        best[token] = max(best.get(token, 0.0), weight)
    return list(best.items())


class TikHubAPISearcher:
    """Search and filter TikHub APIs from the OpenAPI specification."""

    def __init__(self, openapi_path: str | None = None):
        self.openapi_path = Path(openapi_path) if openapi_path else find_spec()
        with open(self.openapi_path, "r", encoding="utf-8") as fh:
            self.data: Dict[str, Any] = json.load(fh)
        self.operations = self._index()
        self.last_total = 0  # total match count from the most recent search

    def _index(self) -> List[Dict[str, Any]]:
        ops: List[Dict[str, Any]] = []
        for path, item in self.data.get("paths", {}).items():
            if not isinstance(item, dict):
                continue
            for method, det in item.items():
                # Path Item objects may contain non-operation keys
                # (parameters/summary/servers/$ref). Skip them explicitly.
                if method.lower() not in HTTP_METHODS or not isinstance(det, dict):
                    continue
                ops.append({
                    "method": method.upper(),
                    "path": path,
                    "operation_id": det.get("operationId", "") or "",
                    "summary": det.get("summary", "") or "",
                    "description": det.get("description", "") or "",
                    "tags": det.get("tags", []) or [],
                    "parameters": det.get("parameters", []) or [],
                    "request_body": det.get("requestBody", {}) or {},
                    "responses": det.get("responses", {}) or {},
                    "raw": det,
                })
        return ops

    # ------------------------------------------------------------------ queries

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Tag list with endpoint counts (the spec's tag descriptions are empty)."""
        counts: Dict[str, int] = {}
        for op in self.operations:
            for tag in op["tags"]:
                counts[tag] = counts.get(tag, 0) + 1
        declared = {t.get("name"): t.get("description", "") for t in self.data.get("tags", [])}
        return [
            {"name": name, "count": count, "description": declared.get(name, "")}
            for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

    def search_by_keyword(self, keyword: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Relevance-ranked token search across path/summary/opId/tags/description.

        The old implementation required the *whole* query string to appear
        verbatim, so 'tiktok user profile' matched nothing useful.
        """
        tokens = tokenize(keyword)
        if not tokens:
            return []
        phrase = keyword.lower().strip()
        weights = {
            "path": 3.0,
            "summary": 4.0,
            "operation_id": 2.5,
            "tags": 2.0,
            "description": 1.0,
        }
        primary = [t for t, w in tokens if w == 1.0]
        # Ordered-token match on the path, e.g. tiktok ... user ... profile
        seq_re = re.compile(".*".join(re.escape(t) for t in primary)) if primary else None
        scored: List[tuple] = []
        for op in self.operations:
            fields = {
                "path": op["path"].lower(),
                "summary": op["summary"].lower(),
                "operation_id": op["operation_id"].lower(),
                "tags": " ".join(op["tags"]).lower(),
                # Long descriptions can otherwise dominate the score.
                "description": op["description"][:1500].lower(),
            }
            score = 0.0
            primary_hits = 0
            for token, weight in tokens:
                for field, field_weight in weights.items():
                    if token in fields[field]:
                        score += weight * field_weight
                if weight == 1.0 and any(token in f for f in fields.values()):
                    primary_hits += 1
            if score <= 0:
                continue
            if primary and primary_hits == len(primary):
                score += 6.0
            if phrase and phrase in fields["summary"]:
                score += 8.0
            if phrase and phrase in fields["path"]:
                score += 8.0
            if seq_re and seq_re.search(op["path"].lower()):
                score += 8.0
            # TikHub names real data endpoints fetch_*/get_*; open_/generate_*
            # are link builders or helpers. Small tie-breaker, not a filter.
            if op["path"].rsplit("/", 1)[-1].startswith(("fetch_", "get_")):
                score += 6.0
            # Demo endpoints return fixed cached data, not live results.
            if "/demo/" in op["path"] or "Demo-API" in op["tags"]:
                score -= 20.0
            scored.append((score, len(op["path"]), op["path"], op))
        scored.sort(key=lambda x: (-x[0], x[1], x[2]))
        self.last_total = len(scored)
        return [item[3] for item in scored[:limit]]

    def search_by_tag(self, tag: str, limit: int = 0) -> List[Dict[str, Any]]:
        """All endpoints for a tag. limit=0 means no truncation.

        The old default limit=50 silently dropped endpoints from tags with
        50+ members (TikTok-Web-API has 58).
        """
        matches = [op for op in self.operations if tag in op["tags"]]
        matches.sort(key=lambda op: op["path"])
        return matches[:limit] if limit else matches

    def get_api_detail(self, key: str) -> Optional[Dict[str, Any]]:
        """Detail by operationId OR by exact/partial path."""
        op = None
        for candidate in self.operations:
            if candidate["operation_id"] == key or candidate["path"] == key:
                op = candidate
                break
        if op is None and key.startswith("/"):
            hits = [o for o in self.operations if key in o["path"]]
            if len(hits) == 1:
                op = hits[0]
        return self._compact_detail(op) if op else None

    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        node: Any = self.data
        for part in ref.lstrip("#/").split("/"):
            if not isinstance(node, dict):
                return {}
            node = node.get(part.replace("~1", "/").replace("~0", "~"), {})
        return node if isinstance(node, dict) else {}

    def _compact_detail(self, op: Dict[str, Any], full: bool = False) -> Dict[str, Any]:
        """Agent-friendly detail: parameters + example call, not a 100 KB schema dump."""
        params = []
        for p in op["parameters"]:
            if "$ref" in p:
                p = self._resolve_ref(p["$ref"])
            schema = p.get("schema", {}) or {}
            params.append({
                "name": p.get("name"),
                "in": p.get("in"),
                "required": bool(p.get("required")),
                "type": schema.get("type") or ("enum" if schema.get("enum") else "any"),
                "default": schema.get("default"),
                "description": (p.get("description") or "")[:300],
            })

        body: Dict[str, Any] = {}
        rb = op["request_body"]
        if rb:
            body["required"] = bool(rb.get("required"))
            for ctype, media in (rb.get("content", {}) or {}).items():
                schema = media.get("schema", {}) or {}
                if "$ref" in schema:
                    schema = self._resolve_ref(schema["$ref"])
                body["content_type"] = ctype
                body["properties"] = list((schema.get("properties", {}) or {}).keys())

        responses: Dict[str, Any] = {}
        for code, resp in op["responses"].items():
            if not isinstance(resp, dict):
                continue
            hint = None
            for ctype, media in (resp.get("content", {}) or {}).items():
                schema = media.get("schema", {}) or {}
                hint = schema.get("$ref") or f"inline {schema.get('type', 'schema')}"
                break
            responses[str(code)] = {
                "description": (resp.get("description") or "")[:200],
                "schema": hint,
            }

        required = [p["name"] for p in params if p["required"]]
        # Many TikHub endpoints mark everything optional but require at least
        # one of them (documented in description). Show them as hints anyway.
        hinted = (required or [p["name"] for p in params])[:6]
        call = f'python api_client.py {op["method"]} "{op["path"]}"'
        if hinted:
            call += " " + " ".join(f'"{n}=<{n}>"' for n in hinted)

        detail: Dict[str, Any] = {
            "method": op["method"],
            "path": op["path"],
            "operation_id": op["operation_id"],
            "summary": op["summary"],
            "tags": op["tags"],
            "description": op["description"] if full else op["description"][:1500],
            "parameters": params,
            "request_body": body,
            "responses": responses,
            "example_call": call,
        }
        if full:
            detail["raw"] = op["raw"]
        return detail

    def suggest_api(self, user_query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Backward-compatible alias for ranked search."""
        return self.search_by_keyword(user_query, limit=limit)

    def list_popular_apis(self, limit: int = 20) -> List[Dict[str, Any]]:
        keywords = ["fetch_user_profile", "fetch_post_detail", "fetch_search",
                    "fetch_video_comment", "trending", "fetch_user_post"]
        seen, out = set(), []
        for kw in keywords:
            for op in self.search_by_keyword(kw, limit=8):
                key = f'{op["method"]}:{op["path"]}'
                if key not in seen and "/demo/" not in op["path"]:
                    seen.add(key)
                    out.append(op)
                    if len(out) >= limit:
                        return out
        return out


# ---------------------------------------------------------------------- output

def _print_ops(ops: Iterable[Dict[str, Any]], title: str, total: Optional[int] = None) -> None:
    ops = list(ops)
    suffix = f" (showing {len(ops)} of {total} matches)" if total else f" ({len(ops)})"
    print(f"\n=== {title}{suffix} ===\n")
    for i, op in enumerate(ops, 1):
        tags = ",".join(op["tags"]) or "-"
        print(f'{i:3}. {op["method"]:5} {op["path"]}')
        print(f'       [{tags}] {op["summary"][:120]}')
        print(f'       opId: {op["operation_id"]}')
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search the TikHub OpenAPI spec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  api_searcher.py "tiktok user profile"
  api_searcher.py "视频评论" --limit 10
  api_searcher.py tag:TikTok-Web-API
  api_searcher.py detail:fetch_user_profile_api_v1_tiktok_web_fetch_user_profile_get
  api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile
  api_searcher.py tags
  api_searcher.py popular
  api_searcher.py "douyin search" --json
""",
    )
    parser.add_argument("query", nargs="?", help="keywords | tag:X | detail:X | tags | popular")
    parser.add_argument("--spec", help="path to openapi.json")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    parser.add_argument("--limit", type=int, default=15, help="max results (default 15)")
    parser.add_argument("--full", action="store_true", help="include raw operation in detail")
    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        return 1

    try:
        searcher = TikHubAPISearcher(args.spec)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    q = args.query.strip()

    if q == "tags":
        tags = searcher.get_all_tags()
        if args.as_json:
            print(json.dumps(tags, ensure_ascii=False, indent=2))
        else:
            print(f"\n=== {len(tags)} API tags ===\n")
            for t in tags:
                print(f'  {t["count"]:4d}  {t["name"]}')
        return 0

    if q == "popular":
        ops = searcher.list_popular_apis(args.limit)
        if args.as_json:
            print(json.dumps([{k: v for k, v in o.items() if k != "raw"} for o in ops],
                             ensure_ascii=False, indent=2))
        else:
            _print_ops(ops, "Popular TikHub APIs")
        return 0

    if q.startswith("tag:"):
        tag = q[4:].strip()
        ops = searcher.search_by_tag(tag)
        if not ops:
            print(f"No endpoints for tag '{tag}'. Run `api_searcher.py tags` to list tags.",
                  file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps([{k: v for k, v in o.items() if k != "raw"} for o in ops],
                             ensure_ascii=False, indent=2))
        else:
            _print_ops(ops, f"Tag: {tag}")
        return 0

    if q.startswith("detail:") or q.startswith("path:"):
        key = q.split(":", 1)[1].strip()
        detail = searcher.get_api_detail(key)
        if not detail:
            print(f"No API found for: {key}", file=sys.stderr)
            print("Hint: use `api_searcher.py tags` or a keyword search first.", file=sys.stderr)
            return 1
        print(json.dumps(detail, ensure_ascii=False, indent=2))
        return 0

    if q.startswith("search:"):
        q = q[7:].strip()

    found = searcher.search_by_keyword(q, limit=args.limit)
    total = searcher.last_total
    if args.as_json:
        print(json.dumps([{k: v for k, v in o.items() if k != "raw"} for o in found],
                         ensure_ascii=False, indent=2))
    else:
        _print_ops(found, f"Search: {q!r}", total=total)
        if not found:
            print("No match. Try fewer words, a path keyword, or `tags` to browse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
