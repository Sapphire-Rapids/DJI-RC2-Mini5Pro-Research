#!/usr/bin/env python3
"""Mutation tests for the final-DEX completion-gate audit."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from audit_artifact import (
    AuditFailure,
    application_dex_dump,
    audit_app_dex_safety,
    audit_completion_gate_dex_dump,
    dex_class_block,
    dex_enclosing_method_block,
    dex_instructions,
    dex_method_block,
    local_register,
    REPORT_DESCRIPTOR,
    SAMPLE_DESCRIPTOR,
    CURRENT_PROFILE,
    PROFILES,
    run,
    tool,
)


POLICY_DESCRIPTOR = "Lcom/finduas/ridobserver/ProbeCompletionPolicy;"
CALL_NEEDLE = (
    "Lcom/finduas/ridobserver/ProbeCompletionPolicy;.terminalState:"
    "(ZZLcom/finduas/ridobserver/ArtIdentityState;)"
    "Lcom/finduas/ridobserver/ProbeRunState;"
)


def replace_policy(dex_dump: str, pattern: str, replacement: str) -> str:
    block = dex_class_block(dex_dump, POLICY_DESCRIPTOR)
    mutated, count = re.subn(pattern, replacement, block, count=1)
    if count != 1:
        raise RuntimeError(f"mutation target did not match exactly once: {pattern}")
    return dex_dump.replace(block, mutated, 1)


def replace_completion_caller(dex_dump: str, pattern: str, replacement) -> str:
    call_offset = dex_dump.find(CALL_NEEDLE)
    if call_offset < 0:
        raise RuntimeError("completion call site missing")
    start = dex_dump.rfind("Class descriptor  : '", 0, call_offset)
    end = dex_dump.find("\nClass #", call_offset)
    if start < 0:
        raise RuntimeError("completion caller class missing")
    block = dex_dump[start:] if end < 0 else dex_dump[start:end]
    method = dex_enclosing_method_block(block, CALL_NEEDLE)
    mutated, count = re.subn(pattern, replacement, method, count=1)
    if count != 1:
        raise RuntimeError(f"caller mutation target did not match exactly once: {pattern}")
    return dex_dump.replace(method, mutated, 1)


def completion_caller(dex_dump: str) -> str:
    offset = dex_dump.index(CALL_NEEDLE)
    start = dex_dump.rfind("Class descriptor  : '", 0, offset)
    end = dex_dump.find("\nClass #", offset)
    block = dex_dump[start:] if end < 0 else dex_dump[start:end]
    return dex_enclosing_method_block(block, CALL_NEEDLE)


def replace_report_class(dex_dump: str, descriptor: str, old: str, new: str) -> str:
    block = dex_class_block(dex_dump, descriptor)
    if old not in block:
        raise RuntimeError(f"report mutation target missing: {old}")
    return dex_dump.replace(block, block.replace(old, new, 1), 1)


def duplicate_protocol_argument(match: re.Match[str]) -> str:
    return (
        match.group(1) + match.group(2) + ", " + match.group(2) + ", " +
        match.group(4) + match.group(5)
    )


def overwrite_file_error(match: re.Match[str]) -> str:
    pc = int(match.group(2), 16) + 1
    return (match.group(1) + f"\n|{pc:04x}: sget-object {match.group(3)}, "
            "Lcom/finduas/ridobserver/ArtIdentityState;.COMPLETE:"
            "Lcom/finduas/ridobserver/ArtIdentityState;")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(PROFILES), default=CURRENT_PROFILE)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    apk = args.apk.resolve()
    dex_dump = run(tool("dexdump"), "-d", apk)
    audit_completion_gate_dex_dump(dex_dump)
    caller = completion_caller(dex_dump)
    protocol_register = local_register(caller, "nextProtocolCompleted", "Z")
    bridge_register = local_register(caller, "nextLocalBridgeCompleted", "Z")
    art_register = local_register(caller, "nextArtIdentity",
                                  "Lcom/finduas/ridobserver/AndroidArtIdentityResult;")
    instructions = dex_instructions(caller)
    art_call_index = next(index for index, (_, operation) in enumerate(instructions)
                          if "AndroidArtIdentityProbe;.run:()" in operation)
    art_success_pc = instructions[art_call_index + 2][0]

    policy_mutations = {
        "protocol_branch_removed": (
            r"(\|[0-9a-f]{4}:\s+)if-eqz v\d+, [0-9a-f]{4}",
            r"\1nop",
        ),
        "protocol_branch_inverted": (
            r"(\|[0-9a-f]{4}:\s+)if-eqz (v\d+), ([0-9a-f]{4})",
            r"\1if-nez \2, \3",
        ),
        "one_rejection_target_bypasses_incomplete": (
            r"(\|[0-9a-f]{4}:\s+if-eqz v\d+, )[0-9a-f]{4}",
            r"\g<1>0000",
        ),
        "art_state_changed_from_complete": (
            r"ArtIdentityState;\.COMPLETE:Lcom/finduas/ridobserver/ArtIdentityState;",
            "ArtIdentityState;.DIFFERENT:Lcom/finduas/ridobserver/ArtIdentityState;",
        ),
        "art_comparison_inverted": (
            r"(\|[0-9a-f]{4}:\s+)if-ne (v\d+), (v\d+), ([0-9a-f]{4})",
            r"\1if-eq \2, \3, \4",
        ),
        "art_branch_removed": (
            r"(\|[0-9a-f]{4}:\s+)if-ne v\d+, v\d+, [0-9a-f]{4}",
            r"\1nop",
        ),
        "complete_result_changed": (
            r"ProbeRunState;\.COMPLETE:Lcom/finduas/ridobserver/ProbeRunState;",
            "ProbeRunState;.RUNNING:Lcom/finduas/ridobserver/ProbeRunState;",
        ),
    }
    mutations = [
        (name, replace_policy(dex_dump, pattern, replacement))
        for name, (pattern, replacement) in policy_mutations.items()
    ]
    mutations.extend(
        [
            (
                "protocol_completion_initialized_true",
                replace_completion_caller(
                    dex_dump,
                    rf"(\|[0-9a-f]{{4}}:\s+const/4 {protocol_register}, #int )0",
                    r"\g<1>1",
                ),
            ),
            (
                "bridge_completion_initialized_true",
                replace_completion_caller(
                    dex_dump,
                    rf"(\|[0-9a-f]{{4}}:\s+const/4 {bridge_register}, #int )0",
                    r"\g<1>1",
                ),
            ),
            (
                "art_result_getter_removed",
                replace_completion_caller(
                    dex_dump,
                    r"(invoke-virtual \{v\d+\}, "
                    r"Lcom/finduas/ridobserver/AndroidArtIdentityResult;)\.getState:\(\)"
                    r"Lcom/finduas/ridobserver/ArtIdentityState;",
                    r"\1.getSdk:()I",
                ),
            ),
            (
                "bridge_argument_replaced_by_protocol",
                replace_completion_caller(
                    dex_dump,
                    r"(invoke-virtual \{v\d+, )(v\d+), (v\d+), (v\d+)(\}, "
                    r"Lcom/finduas/ridobserver/ProbeCompletionPolicy;\.terminalState:)",
                    duplicate_protocol_argument,
                ),
            ),
            (
                "art_argument_replaced_by_protocol",
                replace_completion_caller(
                    dex_dump,
                    r"(invoke-virtual \{v\d+, )(v\d+), (v\d+), (v\d+)(\}, "
                    r"Lcom/finduas/ridobserver/ProbeCompletionPolicy;\.terminalState:)",
                    lambda match: (
                        match.group(1) + match.group(2) + ", " + match.group(3) +
                        ", " + match.group(2) + match.group(5)
                    ),
                ),
            ),
            (
                "art_probe_success_result_replaced",
                replace_completion_caller(
                    dex_dump,
                    rf"(\|{art_success_pc:04x}:\s+move-object {art_register}, )v\d+",
                    rf"\g<1>{protocol_register}",
                ),
            ),
            (
                "art_exception_fallback_forced_complete",
                replace_completion_caller(
                    dex_dump,
                    r"ArtIdentityState;\.FILE_READ_ERROR:"
                    r"Lcom/finduas/ridobserver/ArtIdentityState;",
                    "ArtIdentityState;.COMPLETE:"
                    "Lcom/finduas/ridobserver/ArtIdentityState;",
                ),
            ),
            (
                "terminal_result_replaced_before_snapshot",
                replace_completion_caller(
                    dex_dump,
                    r"(invoke-static/range \{)([^}]+)(\}, "
                    r"Lcom/finduas/ridobserver/ProbeSessionSnapshot;\.copy\$default:)",
                    lambda match: match.group(1) + ", ".join(
                        protocol_register if index == 6 else value.strip()
                        for index, value in enumerate(match.group(2).split(","))
                    ) + match.group(3),
                ),
            ),
            (
                "snapshot_result_not_persisted",
                replace_completion_caller(
                    dex_dump,
                    r"(\|[0-9a-f]{4}:\s+)sput-object (v\d+), "
                    r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;\.state:",
                    r"\1sget-object \2, "
                    r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;.state:",
                ),
            ),
            (
                "file_error_overwritten_before_fallback_constructor",
                replace_completion_caller(
                    dex_dump,
                    r"(\|([0-9a-f]{4}):\s+sget-object (v\d+), "
                    r"Lcom/finduas/ridobserver/ArtIdentityState;\.FILE_READ_ERROR:"
                    r"Lcom/finduas/ridobserver/ArtIdentityState;[^\n]*)",
                    overwrite_file_error,
                ),
            ),
            (
                "snapshot_mask_defaults_observed_run_state",
                replace_completion_caller(
                    dex_dump,
                    r"(\|[0-9a-f]{4}:\s+const/16 v\d+, #int )3776",
                    r"\g<1>3808",
                ),
            ),
            (
                "duplicate_retained_state_store",
                replace_completion_caller(
                    dex_dump,
                    r"(\|[0-9a-f]{4}:\s+)sget-object (v\d+), "
                    r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;\.state:",
                    r"\1sput-object \2, "
                    r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;.state:",
                ),
            ),
        ]
    )

    rejected = 0
    for name, mutation in mutations:
        try:
            audit_completion_gate_dex_dump(mutation)
        except AuditFailure:
            rejected += 1
        else:
            print(f"MUTATION_ACCEPTED: {name}", file=sys.stderr)
            return 1
    app_dump = application_dex_dump(dex_dump)
    audit_app_dex_safety(app_dump, profile=args.profile)
    safety_mutations = {
        "system_load_call_added": (
            app_dump + "\n|fffe: invoke-static {v0}, "
            "Ljava/lang/System;.load:(Ljava/lang/String;)V"
        ),
        "kotlin_write_text_call_added": (
            app_dump + "\n|ffff: invoke-static/range {v0, v1, v2, v3, v4}, "
            "Lkotlin/io/FilesKt;.writeText$default:"
            "(Ljava/io/File;Ljava/lang/String;Ljava/nio/charset/Charset;"
            "ILjava/lang/Object;)V"
        ),
    }
    if args.profile in ("v11", "v12"):
        store_descriptor = REPORT_DESCRIPTOR + ";"
        android_descriptor = REPORT_DESCRIPTOR + "$AndroidStore;"
        safety_mutations.update({
            "report_directory_becomes_arbitrary_path": replace_report_class(
                app_dump, android_descriptor, "Download/FindUAS/Probe/", "/data/local/tmp/"),
            "report_relative_path_becomes_data_path": replace_report_class(
                app_dump, android_descriptor, '"relative_path"', '"_data"'),
            "report_file_prefix_becomes_arbitrary_uri": replace_report_class(
                app_dump, store_descriptor, PROFILES[args.profile]["report_prefix"], "content://other/"),
            "primary_volume_rejection_removed": replace_report_class(
                app_dump, store_descriptor, '"external_primary"', '"unmatched_volume"'),
            "removable_check_replaced_by_primary_check": replace_report_class(
                app_dump, android_descriptor, ".isRemovable:()Z", ".isPrimary:()Z"),
            "report_output_changes_to_append_mode": replace_report_class(
                app_dump, android_descriptor, '"w"', '"wa"'),
            "additional_class_opens_arbitrary_uri": (
                app_dump + "\nClass #999999 -\n"
                "  Class descriptor  : 'Lcom/finduas/ridobserver/UnreviewedWriter;'\n"
                "|0000: invoke-virtual {v0, v1, v2}, "
                "Landroid/content/ContentResolver;.openOutputStream:"
                "(Landroid/net/Uri;Ljava/lang/String;)Ljava/io/OutputStream;"
            ),
            "additional_class_writes_existing_stream": (
                app_dump + "\nClass #999999 -\n"
                "  Class descriptor  : 'Lcom/finduas/ridobserver/UnreviewedWriter;'\n"
                "|0000: invoke-virtual {v0, v1}, Ljava/io/OutputStream;.write:([B)V"
            ),
        })
        android_block = dex_class_block(app_dump, android_descriptor)
        cleanup_method = dex_method_block(android_block, "remove")
        if ".ownedUri:" not in cleanup_method:
            raise RuntimeError("owned cleanup URI call missing")
        safety_mutations["cleanup_uses_unowned_uri"] = app_dump.replace(
            cleanup_method, cleanup_method.replace(".ownedUri:", ".unownedUri:", 1), 1
        )
    if args.profile == "v12":
        sample = SAMPLE_DESCRIPTOR + ";"
        source = SAMPLE_DESCRIPTOR + "$AndroidSource;"
        store = SAMPLE_DESCRIPTOR + "$AndroidStore;"
        entry = SAMPLE_DESCRIPTOR + "$Entry;"
        safety_mutations.update({
            "sample_targets_another_package": replace_report_class(
                app_dump, source, '"dji.go.v5"', '"com.dpad.fuli"'),
            "sample_uses_app_data_instead_of_apk": replace_report_class(
                app_dump, source, ".sourceDir:Ljava/lang/String;", ".dataDir:Ljava/lang/String;"),
            "sample_uses_app_data_instead_of_native_dir": replace_report_class(
                app_dump, source, ".nativeLibraryDir:Ljava/lang/String;", ".dataDir:Ljava/lang/String;"),
            "sample_archive_entry_escapes_fixed_set": replace_report_class(
                app_dump, entry, '"libsdk_jni.so"', '"../license.db"'),
            "sample_output_directory_widens": replace_report_class(
                app_dump, store, "Download/FindUAS/Samples/", "Download/"),
            "sample_target_version_changes": replace_report_class(
                app_dump, sample, '"1.19.4"', '"1.21.10"'),
            "another_class_constructs_zip_writer": (
                app_dump + "\nClass #999999 -\n"
                "  Class descriptor  : 'Lcom/finduas/ridobserver/UnreviewedZipWriter;'\n"
                "|0000: new-instance v0, Ljava/util/zip/ZipOutputStream;"
            ),
        })
    for name, mutation in safety_mutations.items():
        try:
            audit_app_dex_safety(mutation, enforce_frozen_surface=False, profile=args.profile)
        except AuditFailure:
            rejected += 1
        else:
            print(f"MUTATION_ACCEPTED: {name}", file=sys.stderr)
            return 1
    print("MUTATION_AUDIT_PASS")
    print(f"mutations_rejected={rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
