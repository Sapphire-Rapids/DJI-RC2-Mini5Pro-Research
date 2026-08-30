#!/usr/bin/env python3
"""Offline reproduction of the Fly 1.19.4 RID policy selection rules.

Only the reviewed, strictly typed JSON subset is accepted; this is not a Gson
compatibility parser. Inputs stay in memory and summaries omit policy strings,
area codes, product numbers and payload hashes. There is no device/network API.

``audit_policy(namespace, area, product_type, cache)`` handles one observation.
Reuse ``PolicyAuditSession`` within one subscription and call ``reset()`` when
that subscription ends. The CLI reads the same four fields from a JSON file.
``cache`` is an already-decoded object with receiver_type, receiver_index, data.
Omit the CLI area field, or use ``audit_possible_candidates``, to compare possible
candidates without selecting an actual area. That mode has no emission decision.

A cache match compares receiver and selected string only. The shared cache has
other writers; matching it does not identify its writer or aircraft application.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "finduas-rid-cloud-policy-audit/v1"
POLICY_KEY = "country_and_device_type"
MISSING = object()


@dataclass(frozen=True)
class Limits:
    document_bytes: int = 1_048_576
    policy_bytes: int = 262_144
    text_bytes: int = 262_144
    area_bytes: int = 128
    namespace_entries: int = 256
    rows: int = 1024
    block_entries: int = 4096
    nodes: int = 32768
    depth: int = 16
    object_members: int = 1024
    reject_nul: bool = False

    def __post_init__(self) -> None:
        if type(self.reject_nul) is not bool or any(
            type(value) is not int or value < 1
            for key, value in vars(self).items() if key != "reject_nul"
        ):
            raise ValueError("INVALID_LIMITS")


# Matching A054 native parser profile. Both accept standard Unicode JSON but
# reject NUL/isolated surrogates; neither normalizes country or payload strings.
A054_LIMITS = Limits(document_bytes=65536, policy_bytes=65536, text_bytes=65536,
                     area_bytes=65536, namespace_entries=64, rows=256,
                     block_entries=4096, nodes=32768, depth=12,
                     object_members=64, reject_nul=True)


class _Invalid(ValueError):
    """Exceptions contain fixed codes only, never input fragments."""


def _text_size(value: str, maximum: int) -> int:
    if len(value) > maximum:
        raise _Invalid("LIMIT_EXCEEDED")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        raise _Invalid("BAD_UNICODE") from None
    if size > maximum:
        raise _Invalid("LIMIT_EXCEEDED")
    return size


def _bounded_tree(value: Any, limits: Limits) -> None:
    pending = [(value, 0)]
    count = byte_count = 0
    while pending:
        current, depth = pending.pop()
        count += 1
        if count > limits.nodes or depth > limits.depth:
            raise _Invalid("LIMIT_EXCEEDED")
        if type(current) is dict:
            if len(current) > min(limits.object_members, limits.nodes - count - len(pending)):
                raise _Invalid("LIMIT_EXCEEDED")
            for key, item in current.items():
                if type(key) is not str:
                    raise _Invalid("MALFORMED")
                if limits.reject_nul and "\0" in key:
                    raise _Invalid("MALFORMED")
                byte_count += _text_size(key, limits.text_bytes)
                pending.append((item, depth + 1))
        elif type(current) is list:
            if len(current) > limits.nodes - count - len(pending):
                raise _Invalid("LIMIT_EXCEEDED")
            pending.extend((item, depth + 1) for item in current)
        elif type(current) is str:
            if limits.reject_nul and "\0" in current:
                raise _Invalid("MALFORMED")
            byte_count += _text_size(current, limits.text_bytes)
        elif current is not None and type(current) not in (int, float, bool):
            raise _Invalid("MALFORMED")
        if byte_count > limits.document_bytes:
            raise _Invalid("LIMIT_EXCEEDED")


def _strict_json(text: str, byte_limit: int, limits: Limits) -> Any:
    _text_size(text, byte_limit)
    # Bound nesting before json.loads allocates a recursively nested structure.
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > limits.depth:
                raise _Invalid("LIMIT_EXCEEDED")
        elif char in "]}":
            depth -= 1

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise _Invalid("DUPLICATE_KEY")
            result[key] = value
        return result

    def constant(_value: str) -> None:
        raise _Invalid("BAD_JSON")

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except _Invalid:
        raise
    except (ValueError, RecursionError):
        raise _Invalid("BAD_JSON") from None
    _bounded_tree(value, limits)
    return value


def _integer(value: Any, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < (1 << (bits - 1))


def _policy_rows(namespace: Any, limits: Limits) -> tuple[str, list[dict[str, Any]]]:
    if namespace is MISSING:
        return "NAMESPACE_MISSING", []
    if namespace is None:
        return "NAMESPACE_NULL", []
    if type(namespace) is not dict:
        return "NAMESPACE_MALFORMED", []
    try:
        if len(namespace) > limits.namespace_entries:
            raise _Invalid("LIMIT_EXCEEDED")
        _bounded_tree(namespace, limits)
        if any(value is not None and type(value) is not str for value in namespace.values()):
            return "NAMESPACE_MALFORMED", []
        raw = namespace.get(POLICY_KEY, MISSING)
        if raw is MISSING:
            return "POLICY_MISSING", []
        if raw is None:
            return "POLICY_NULL", []
        if raw == "":
            return "POLICY_EMPTY_TEXT", []
        rows = _strict_json(raw, limits.policy_bytes, limits)
        if rows is None:
            return "POLICY_JSON_NULL", []
        if type(rows) is not list:
            return "POLICY_WRONG_TYPE", []
        if len(rows) > limits.rows:
            raise _Invalid("LIMIT_EXCEEDED")
        total_block_entries = 0
        for row in rows:
            if type(row) is not dict or any(
                key not in row for key in ("country_code", "data", "block_device")
            ):
                return "INVALID_ENTRY", []
            if type(row["country_code"]) is not str or type(row["data"]) is not str:
                return "INVALID_ENTRY", []
            _text_size(row["country_code"], limits.area_bytes)
            _text_size(row["data"], limits.text_bytes)
            blocked = row["block_device"]
            if type(blocked) is not list or any(not _integer(item, 64) for item in blocked):
                return "INVALID_ENTRY", []
            total_block_entries += len(blocked)
            if total_block_entries > limits.block_entries:
                raise _Invalid("LIMIT_EXCEEDED")
        return "VALID", rows
    except _Invalid as error:
        return str(error), []


def _cache(cache: Any, limits: Limits) -> tuple[str, bool | None, str | None]:
    if cache is MISSING:
        return "MISSING", None, None
    if cache is None:
        return "NULL", None, None
    if type(cache) is not dict:
        return "MALFORMED", None, None
    try:
        _bounded_tree(cache, limits)
        if any(key not in cache for key in ("receiver_type", "receiver_index", "data")):
            return "MALFORMED", None, None
        if not all(_integer(cache[key], 32) for key in ("receiver_type", "receiver_index")):
            return "MALFORMED", None, None
        if type(cache["data"]) is not str:
            return "MALFORMED", None, None
        return "VALID", cache["receiver_type"] == 18 and cache["receiver_index"] == 4, cache["data"]
    except _Invalid as error:
        return str(error), None, None


class PolicyAuditSession:
    """One offline connection/subscription lifecycle; no raw-value public state."""

    __slots__ = ("_limits", "_last_emitted", "_observation_count", "_emission_count")

    def __init__(self, limits: Limits | None = None) -> None:
        self._limits = limits or Limits()
        self.reset()

    def reset(self) -> None:
        self._last_emitted: object | str = MISSING
        self._observation_count = self._emission_count = 0

    def observe(self, namespace: Any = MISSING, area: Any = MISSING,
                product_type: Any = MISSING, cache: Any = MISSING) -> dict[str, Any]:
        self._observation_count += 1
        state, rows = _policy_rows(namespace, self._limits)
        cache_state, receiver_matches, cached_data = _cache(cache, self._limits)
        result: dict[str, Any] = {
            "schema": SCHEMA,
            "mode": "EXACT_AREA",
            "policy_state": state,
            "context_state": "VALID",
            "row_count": len(rows),
            "area_match_count": 0,
            "default_match_count": 0,
            "selected_area_blocked": None,
            "selection": "UNAVAILABLE",
            "candidate_state": "UNAVAILABLE",
            "emission": "UNAVAILABLE",
            "observation_count": self._observation_count,
            "emission_count": self._emission_count,
            "cache_state": cache_state,
            "cache_receiver_matches": receiver_matches,
            "matches_selected_candidate": None,
        }
        if area is MISSING or product_type is MISSING:
            result["context_state"] = "MISSING"
        elif area is None or product_type is None:
            result["context_state"] = "NULL"
        elif type(area) is not str or not _integer(product_type, 64):
            result["context_state"] = "MALFORMED"
        else:
            try:
                _text_size(area, self._limits.area_bytes)
            except _Invalid as error:
                result["context_state"] = str(error)
        if state != "VALID" or result["context_state"] != "VALID":
            return result

        area_rows = [row for row in rows if row["country_code"] == area]
        defaults = [row for row in rows if row["country_code"] == "DEFAULT"]
        result["area_match_count"] = len(area_rows)
        result["default_match_count"] = len(defaults)
        selected = area_rows[0] if area_rows else None
        default = defaults[0]["data"] if defaults else ""
        blocked = selected is not None and product_type in selected["block_device"]
        result["selected_area_blocked"] = blocked if selected is not None else None
        if selected is None:
            candidate = default
            result["selection"] = "DEFAULT_AREA_MISSING"
        elif blocked:
            candidate = default
            result["selection"] = "DEFAULT_PRODUCT_BLOCKED"
        else:
            candidate = selected["data"]
            result["selection"] = "AREA"
        result["candidate_state"] = "NONEMPTY" if candidate else "EMPTY"
        if not candidate:
            result["emission"] = "FILTERED_EMPTY"
        elif candidate == self._last_emitted:
            result["emission"] = "SUPPRESSED_DUPLICATE"
        else:
            result["emission"] = "EMIT"
            self._last_emitted = candidate
            self._emission_count += 1
        result["emission_count"] = self._emission_count
        if cache_state == "VALID":
            result["matches_selected_candidate"] = bool(candidate) and bool(receiver_matches) and cached_data == candidate
        return result


def audit_policy(namespace: Any = MISSING, area: Any = MISSING,
                 product_type: Any = MISSING, cache: Any = MISSING,
                 *, limits: Limits | None = None) -> dict[str, Any]:
    return PolicyAuditSession(limits).observe(namespace, area, product_type, cache)


def audit_possible_candidates(namespace: Any = MISSING,
                              product_type: Any = MISSING, cache: Any = MISSING,
                              *, limits: Limits | None = None) -> dict[str, Any]:
    """Compare a shared cache with possible strings when the area is unobserved.

    The first row per exact country string survives. A blocked row contributes
    the first DEFAULT string; an absent area also contributes that DEFAULT.
    Nonempty strings form a set. Its match does not select the actual area or
    reconstruct the emitting subscription's distinctUntilChanged history.
    """
    limits = limits or Limits()
    state, rows = _policy_rows(namespace, limits)
    cache_state, receiver_matches, cached_data = _cache(cache, limits)
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "mode": "POSSIBLE_CANDIDATES",
        "selected_actual_area": "UNOBSERVED",
        "policy_state": state,
        "context_state": "VALID",
        "row_count": len(rows),
        "effective_row_count": 0,
        "duplicate_row_count": 0,
        "default_row_count": 0,
        "blocked_row_count": 0,
        "nonempty_candidate_count": 0,
        "cache_state": cache_state,
        "cache_receiver_matches": receiver_matches,
        "matching_candidate_count": None,
        "matches_any_possible_candidate": None,
        "matches_default_candidate": None,
    }
    if product_type is MISSING:
        result["context_state"] = "MISSING"
    elif product_type is None:
        result["context_state"] = "NULL"
    elif not _integer(product_type, 64):
        result["context_state"] = "MALFORMED"
    if state != "VALID" or result["context_state"] != "VALID":
        return result
    first_rows: dict[str, dict[str, Any]] = {}
    for row in rows:
        first_rows.setdefault(row["country_code"], row)
    default_row = first_rows.get("DEFAULT")
    default = default_row["data"] if default_row is not None else ""
    candidates = {default} if default else set()
    for row in first_rows.values():
        blocked = product_type in row["block_device"]
        result["blocked_row_count"] += int(blocked)
        candidate = default if blocked else row["data"]
        if candidate:
            candidates.add(candidate)
    result["effective_row_count"] = len(first_rows)
    result["duplicate_row_count"] = len(rows) - len(first_rows)
    result["default_row_count"] = sum(row["country_code"] == "DEFAULT" for row in rows)
    result["nonempty_candidate_count"] = len(candidates)
    if cache_state == "VALID":
        matches = bool(receiver_matches) and cached_data in candidates
        result["matching_candidate_count"] = int(matches)
        result["matches_any_possible_candidate"] = matches
        result["matches_default_candidate"] = bool(receiver_matches) and bool(default) and cached_data == default
    return result


def audit_document(data: bytes, *, limits: Limits | None = None) -> dict[str, Any]:
    """Parse one CLI/input document; errors are sanitized without tracebacks."""
    limits = limits or Limits()
    try:
        if len(data) > limits.document_bytes:
            raise _Invalid("LIMIT_EXCEEDED")
        try:
            text = data.decode("utf-8")
        except UnicodeError:
            raise _Invalid("BAD_UNICODE") from None
        value = _strict_json(text, limits.document_bytes, limits)
        if type(value) is not dict:
            raise _Invalid("DOCUMENT_WRONG_TYPE")
        if "area" not in value:
            return audit_possible_candidates(*(value.get(key, MISSING) for key in
                                                ("namespace", "product_type", "cache")), limits=limits)
        return audit_policy(*(value.get(key, MISSING) for key in
                              ("namespace", "area", "product_type", "cache")), limits=limits)
    except _Invalid as error:
        return {"schema": SCHEMA, "input_state": str(error)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="JSON input file, or - for stdin")
    args = parser.parse_args(argv)
    limits = Limits()
    try:
        if args.input == "-":
            raw = sys.stdin.buffer.read(limits.document_bytes + 1)
        else:
            with Path(args.input).open("rb") as stream:
                raw = stream.read(limits.document_bytes + 1)
        result = audit_document(raw, limits=limits)
    except OSError:
        result = {"schema": SCHEMA, "input_state": "READ_ERROR"}
    print(json.dumps(result, sort_keys=True))
    if "input_state" in result:
        return 2
    valid = (result["policy_state"] == "VALID" and result["context_state"] == "VALID"
             and result["cache_state"] in ("VALID", "MISSING", "NULL"))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
