#!/usr/bin/env python3
"""Read-only official DJI Assistant metadata client for RC 2 (rc331).

This helper is deliberately narrower than a general firmware client. It only
retrieves the official firmware list and the two small signed configuration
manifests for rc331 10.00.0700 and 10.00.0800. It has no module-body route,
device transport, upgrade call, login operation, or mutable device action.

Installed Assistant application material is reconstructed in memory by the
shared audited metadata module and is never printed or serialized.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

import dji_official_metadata as common


RC2_DYLIB = Path(
    "/Applications/DJI Assistant 2(Consumer Drones Series).app/Contents/"
    "MacOS/DJIServices/libDJIRc2Service.dylib"
)
PRODUCT_ID = "rc331"
TARGET_VERSIONS = ("10.00.0700", "10.00.0800")


def _public_config_source(source: Mapping[str, Any]) -> dict[str, Any]:
    """Retain only the CDN host and manifest basename, never its opaque path."""

    path = str(source.get("path", ""))
    return {
        "host": str(source.get("host", "")),
        "filename": common._safe_filename(PurePosixPath(path).name),
        "query": "omitted",
        "redirect_count": source.get("redirect_count"),
    }


def _module_index(config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    modules = config.get("modules")
    if not isinstance(modules, list):
        raise common.FormatError("configuration is missing its module array")
    index: dict[str, Mapping[str, Any]] = {}
    for item in modules:
        if not isinstance(item, dict):
            raise common.FormatError("configuration has a non-object module record")
        module_id = str(item.get("module_id", ""))
        if not re.fullmatch(r"[0-9A-Za-z_-]{1,32}", module_id):
            raise common.FormatError("configuration has an invalid module identifier")
        if module_id in index:
            raise common.FormatError("configuration has a duplicate module identifier")
        index[module_id] = item
    return index


def compare_configs(
    older: Mapping[str, Any], newer: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a de-identified, module-level manifest difference."""

    old_index = _module_index(older)
    new_index = _module_index(newer)
    changed: list[dict[str, Any]] = []
    for module_id in sorted(old_index.keys() & new_index.keys()):
        old = old_index[module_id]
        new = new_index[module_id]
        differing_fields = [
            field
            for field in ("module_version", "size", "md5", "filename", "group", "base_sha1")
            if old.get(field) != new.get(field)
        ]
        if differing_fields:
            changed.append(
                {
                    "module_id": module_id,
                    "differing_fields": differing_fields,
                    "old": {field: old.get(field) for field in differing_fields},
                    "new": {field: new.get(field) for field in differing_fields},
                }
            )
    return {
        "old_version": older.get("product_version"),
        "new_version": newer.get("product_version"),
        "unchanged_module_ids": sorted(
            module_id
            for module_id in old_index.keys() & new_index.keys()
            if not any(item["module_id"] == module_id for item in changed)
        ),
        "changed_modules": changed,
        "added_modules": [new_index[key] for key in sorted(new_index.keys() - old_index.keys())],
        "removed_modules": [old_index[key] for key in sorted(old_index.keys() - new_index.keys())],
    }


def fetch_metadata(
    dylib: Path = RC2_DYLIB, timeout: float = 20.0
) -> dict[str, Any]:
    _, secret, binary_sha256 = common.extract_assistant_material(dylib)
    token = ""
    account = ""
    client = common.AllowlistedMetadataHttp(timeout=timeout)

    list_params = [
        ("product_id", PRODUCT_ID),
        ("token", token),
        ("signature", common.signature_getallfile(secret, PRODUCT_ID, token)),
        ("account", account),
        ("eng", "false"),
        ("force_update", "true"),
    ]
    list_body = client.get(
        "/getfile/getallfile",
        list_params,
        headers={"x-app-ver": common.APP_VERSION_HEADER},
        max_bytes=common.MAX_LIST_BYTES,
    )
    entries = common._list_entries(list_body)
    selected = {
        str(entry.get("product_version")): entry
        for entry in entries
        if str(entry.get("product_version")) in TARGET_VERSIONS
    }

    configs: list[dict[str, Any]] = []
    for version in TARGET_VERSIONS:
        if version not in selected:
            configs.append(
                {
                    "product_version": version,
                    "available_in_list": False,
                    "metadata_requested": False,
                }
            )
            continue
        params = [
            ("product_version", version),
            ("product_id", PRODUCT_ID),
            ("token", token),
            ("device", "pc"),
            ("signature", common.signature_download(secret, PRODUCT_ID, version, token)),
            ("account", account),
            ("eng", "false"),
        ]
        body = client.get(
            "/getfile/download", params, max_bytes=common.MAX_CONFIG_BYTES
        )
        xml_body, container = common._extract_config_xml(body)
        summary = common.summarize_config(xml_body, version, container)
        summary.update(
            {
                "available_in_list": True,
                "metadata_requested": True,
                "xml_retrieved": True,
            }
        )
        if client.last_followed_config_redirect:
            summary["config_source"] = _public_config_source(
                client.last_followed_config_redirect
            )
        configs.append(summary)

    complete = [config for config in configs if config.get("xml_retrieved")]
    delta = compare_configs(complete[0], complete[1]) if len(complete) == 2 else None

    del secret
    return {
        "safety": {
            "mode": "metadata-only",
            "http_method": "GET",
            "api_host_allowlist": [common.ALLOWED_HOST],
            "config_redirect_host_rule": "HTTPS *.djicdn.com; one redirect; *.pro.cfg.sig only",
            "metadata_paths_used": sorted(common.METADATA_PATHS),
            "firmware_module_bodies": "not requested; route blocked by imported client",
            "device_transport": "absent",
            "upgrade_calls": "absent",
        },
        "assistant_binary": {
            "path": str(dylib),
            "sha256": binary_sha256,
            "embedded_material": "decoded in memory; never emitted",
        },
        "request_redaction": {
            "token": "empty by design for this metadata request",
            "account": "empty by design for this metadata request",
            "signature": "computed in memory; value omitted",
            "CDN_query": "used in memory; omitted",
        },
        "product_id": PRODUCT_ID,
        "target_versions": list(TARGET_VERSIONS),
        "matching_list_entries": [
            common._public_list_entry(selected[version])
            for version in TARGET_VERSIONS
            if version in selected
        ],
        "configs": configs,
        "delta": delta,
    }


def self_test(dylib: Path = RC2_DYLIB) -> dict[str, Any]:
    host, secret, binary_sha256 = common.extract_assistant_material(dylib)
    checks = (
        common.signature_getallfile(secret, PRODUCT_ID, ""),
        common.signature_download(secret, PRODUCT_ID, TARGET_VERSIONS[0], ""),
    )
    if not all(re.fullmatch(r"[0-9a-f]{32}", value) for value in checks):
        raise common.FormatError("signature self-test failed")
    del secret, checks
    return {
        "ok": True,
        "network_used": False,
        "validated_host": host,
        "assistant_binary_sha256": binary_sha256,
        "embedded_material": "validated but not emitted",
        "product_id": PRODUCT_ID,
        "target_versions": list(TARGET_VERSIONS),
        "firmware_body_path": "blocked",
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--fetch-metadata", action="store_true")
    parser.add_argument("--dylib", type=Path, default=RC2_DYLIB)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = (
            self_test(args.dylib)
            if args.self_test
            else fetch_metadata(args.dylib, timeout=args.timeout)
        )
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"wrote de-identified report: {args.output}")
        else:
            sys.stdout.write(rendered)
        return 0
    except (
        common.FormatError,
        common.SafetyError,
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
