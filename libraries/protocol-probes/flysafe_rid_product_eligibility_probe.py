#!/usr/bin/env python3
"""Privacy-minimizing DJI FlySafe RID eligibility probe.

This tool intentionally has no option for an authorization header, cookie, DJI
account credential, or aircraft serial number.  It can:

* perform anonymous GETs and report only whether public/protected endpoints are
  reachable; or
* inspect an already-exported JSON *response body* offline and emit only the
  minimum product capability or qualification booleans needed by this study.

It never submits an unlock request and never writes to an aircraft.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

try:
    import certifi
except ImportError:  # pragma: no cover - system Python may already have a CA store
    certifi = None


PUBLIC_DRONES_URL = "https://flysafe-api.dji.com/dji/drones"
REGIONAL_API_HOSTS = (
    "https://flysafe-website-us.dji.com",
    "https://flysafe-website-cn.dji.com",
)
PROTECTED_PATHS = (
    "/api/qep/unlock/device_type",
    "/api/qep/background",
)
MAX_INPUT_BYTES = 10 * 1024 * 1024
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where() if certifi else None)

_SECRET_KEY_PARTS = (
    "authorization",
    "cookie",
    "password",
    "passwd",
    "access_token",
    "refresh_token",
    "session_token",
    "secret",
)


class UnsafeInputError(ValueError):
    """Raised when an exported object looks like a credential-bearing HAR."""


def _normalized(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _walk(value: Any) -> Iterable[tuple[str | None, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield None, item
            yield from _walk(item)


def reject_credential_bearing_input(value: Any) -> None:
    """Reject likely HAR/request exports before doing any reporting."""

    for key, item in _walk(value):
        if key is not None:
            lowered = key.lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise UnsafeInputError(
                    "input contains a credential-like key; provide only the JSON response body"
                )
        if isinstance(item, str) and item.lstrip().lower().startswith("bearer "):
            raise UnsafeInputError(
                "input contains a bearer credential; provide only the JSON response body"
            )


def _payload(value: Any) -> Any:
    if isinstance(value, dict) and "data" in value:
        return value["data"]
    return value


def _records(value: Any) -> list[dict[str, Any]]:
    value = _payload(value)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("records", "list", "items", "device_types", "drones"):
            candidate = value.get(key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
    return []


def sanitize_product_response(value: Any, query: str = "Mini 5 Pro") -> dict[str, Any]:
    reject_credential_bearing_input(value)
    wanted = _normalized(query)
    matches: list[dict[str, Any]] = []
    matching_capability_field_seen = False
    for row in _records(value):
        name = next(
            (
                row.get(key)
                for key in ("name", "product_name", "display_name", "title")
                if row.get(key) not in (None, "")
            ),
            "",
        )
        slug = row.get("slug", "")
        searchable = _normalized(f"{name} {slug}")
        if wanted not in searchable:
            continue
        capability_field_present = "support_unlock_type" in row
        matching_capability_field_seen |= capability_field_present
        raw_support = row.get("support_unlock_type")
        support = (
            sorted({str(item) for item in raw_support})
            if isinstance(raw_support, list)
            else []
        )
        safe: dict[str, Any] = {
            "name": str(name),
            "capability_field_present": capability_field_present,
            "support_unlock_type": support,
            "supports_rid": "Rid" in support if capability_field_present else None,
        }
        if row.get("id") is not None:
            safe["product_type_id"] = str(row["id"])
        if slug:
            safe["slug"] = str(slug)
        matches.append(safe)
    return {
        "query": query,
        "record_count": len(_records(value)),
        "matches": matches,
        "eligibility_known": matching_capability_field_seen,
    }


def sanitize_background_response(value: Any) -> dict[str, Any]:
    reject_credential_bearing_input(value)
    info = _payload(value)
    if not isinstance(info, dict):
        return {"recognized": False}

    background_type = info.get("background_type")
    status = info.get("status")
    qualify = info.get("qualify")
    country = info.get("country")
    type_names = {
        0: "Government",
        1: "Business",
        2: "Customer",
        3: "EuropeanFcc",
    }
    status_names = {
        1: "WaitForReview",
        2: "Reviewing",
        3: "Withdrawn",
        4: "Passed",
        5: "Rejected",
        6: "Revised",
        7: "Expired",
    }
    result = {
        "recognized": all(key in info for key in ("background_type", "status", "qualify")),
        "background_type": type_names.get(background_type, "Unknown"),
        "status": status_names.get(status, "Unknown"),
        "participated": qualify == 1,
        "country_is_china": country == 156,
        "mainland_rid_card_gate": (
            background_type == 0 and status == 4 and qualify == 1 and country == 156
        ),
        "abroad_rid_card_gate": (
            background_type == 3 and status == 4 and qualify == 1
        ),
    }
    return result


def _read_json(path: Path) -> Any:
    size = path.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise ValueError(f"input is too large ({size} bytes; limit {MAX_INPUT_BYTES})")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _anonymous_get(url: str, timeout: float) -> tuple[int, Any]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "FindUAS-FlySafe-anonymous-readonly-probe/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=TLS_CONTEXT) as response:
            status = int(response.status)
            raw = response.read(2 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(64 * 1024)
    try:
        return status, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, None


def anonymous_probe(timeout: float = 15.0) -> dict[str, Any]:
    result: dict[str, Any] = {
        "mode": "anonymous_read_only",
        "credentials_supplied": False,
        "requests": [],
    }

    status, body = _anonymous_get(PUBLIC_DRONES_URL, timeout)
    public_summary = sanitize_product_response(body or {}, "Mini 5 Pro")
    result["requests"].append(
        {
            "url": PUBLIC_DRONES_URL,
            "http_status": status,
            "public_catalog_match": public_summary["matches"],
        }
    )

    for host in REGIONAL_API_HOSTS:
        for path in PROTECTED_PATHS:
            status, body = _anonymous_get(host + path, timeout)
            api_code = body.get("code") if isinstance(body, dict) else None
            result["requests"].append(
                {
                    "url": host + path,
                    "http_status": status,
                    "api_code": api_code,
                    "authentication_required": status == 401 or api_code == 10,
                }
            )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    anonymous = sub.add_parser(
        "anonymous", help="perform anonymous GETs; no token/cookie option exists"
    )
    anonymous.add_argument("--timeout", type=float, default=15.0)

    product = sub.add_parser(
        "inspect-product", help="sanitize an exported unlock/device_type JSON response body"
    )
    product.add_argument("response_json", type=Path)
    product.add_argument("--query", default="Mini 5 Pro")

    background = sub.add_parser(
        "inspect-background", help="sanitize an exported qep/background JSON response body"
    )
    background.add_argument("response_json", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "anonymous":
            output = anonymous_probe(args.timeout)
        elif args.command == "inspect-product":
            output = sanitize_product_response(_read_json(args.response_json), args.query)
        else:
            output = sanitize_background_response(_read_json(args.response_json))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
