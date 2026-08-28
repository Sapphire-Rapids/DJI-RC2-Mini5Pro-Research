#!/usr/bin/env python3
"""Mutation tests for the final-DEX completion-gate audit."""

from __future__ import annotations

from pathlib import Path
import re
import sys

from audit_artifact import (
    AuditFailure,
    application_dex_dump,
    audit_app_dex_safety,
    audit_completion_gate_dex_dump,
    dex_class_block,
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
    mutated, count = re.subn(pattern, replacement, block, count=1)
    if count != 1:
        raise RuntimeError(f"caller mutation target did not match exactly once: {pattern}")
    return dex_dump[:start] + mutated + dex_dump[start + len(block):]


def duplicate_protocol_argument(match: re.Match[str]) -> str:
    return (
        match.group(1) + match.group(2) + ", " + match.group(2) + ", " +
        match.group(4) + match.group(5)
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: test_audit_mutations.py APK", file=sys.stderr)
        return 2
    apk = Path(sys.argv[1]).resolve()
    dex_dump = run(tool("dexdump"), "-d", apk)
    audit_completion_gate_dex_dump(dex_dump)

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
                    r"(\|0000:\s+const/4 v1, #int )0",
                    r"\g<1>1",
                ),
            ),
            (
                "bridge_completion_initialized_true",
                replace_completion_caller(
                    dex_dump,
                    r"(\|0017:\s+const/4 v2, #int )0",
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
                    r"(\|0072:\s+move-object v7, )v0",
                    r"\g<1>v4",
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
                    r"(\|0100:\s+invoke-static/range "
                    r"\{v4, v5, v6, v7, v8, v9, )v10",
                    r"\g<1>v12",
                ),
            ),
            (
                "snapshot_result_not_persisted",
                replace_completion_caller(
                    dex_dump,
                    r"(\|0104:\s+)sput-object (v\d+), "
                    r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;\.state:",
                    r"\1sget-object \2, "
                    r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;.state:",
                ),
            ),
            (
                "file_error_overwritten_before_fallback_constructor",
                replace_completion_caller(
                    dex_dump,
                    r"(\|0078:\s+sget-object v8, "
                    r"Lcom/finduas/ridobserver/ArtIdentityState;\.FILE_READ_ERROR:"
                    r"Lcom/finduas/ridobserver/ArtIdentityState;[^\n]*)",
                    r"\1\n|0079: sget-object v8, "
                    r"Lcom/finduas/ridobserver/ArtIdentityState;.COMPLETE:"
                    r"Lcom/finduas/ridobserver/ArtIdentityState;",
                ),
            ),
            (
                "snapshot_mask_defaults_observed_run_state",
                replace_completion_caller(
                    dex_dump,
                    r"(\|00ef:\s+const/16 v17, #int )3776",
                    r"\g<1>3808",
                ),
            ),
            (
                "duplicate_retained_state_store",
                replace_completion_caller(
                    dex_dump,
                    r"(\|00b6:\s+)sget-object (v\d+), "
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
    for name, mutation in safety_mutations.items():
        try:
            audit_app_dex_safety(mutation, enforce_frozen_surface=False)
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
