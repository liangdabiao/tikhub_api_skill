#!/usr/bin/env python3
"""One-off spec explorer: sample endpoints + tag counts.

Reuses api_searcher.find_spec() so it works from any checkout path
(the previous version hard-coded D:/tikhub_api_skill/openapi.json).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".workbuddy" / "skills" / "tikhub-api-helper"))

from api_searcher import TikHubAPISearcher, find_spec  # noqa: E402


def main():
    searcher = TikHubAPISearcher()
    print(f"Spec: {find_spec()}")
    print(f"Endpoints: {len(searcher.operations)}\n")

    print("=== Sample API Endpoints ===\n")
    for op in searcher.operations[:15]:
        tags = ",".join(op["tags"])
        print(f'{op["method"]:6} {op["path"][:58]:58} | {tags[:38]}')
        print(f'       └─ {op["summary"][:90]}')

    print("\n=== API Categories by Tag ===\n")
    for tag in searcher.get_all_tags():
        print(f'{tag["count"]:4d} endpoints | {tag["name"]}')


if __name__ == "__main__":
    main()
