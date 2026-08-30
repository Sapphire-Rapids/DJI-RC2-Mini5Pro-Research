#!/usr/bin/env python3
"""Private, serialized client for the fixed B1 SD diagnostic protocol."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import time

BASE = "Download/FindUAS/Bridge"
LIMIT = 64
MAX_REPORT = 131072
SID = r"[0-9a-f]{16}"
SEQ = r"[0-9]{4}"
NUMBER = r"(?:0|[1-9][0-9]*)"
SHA = r"[0-9a-f]{64}"
CANARY_OPS = ("CANARY_BASELINE", "CANARY_LOAD", "CANARY_CLEANUP")
OPERATIONS = ("PING", "SNAPSHOT", "STOP", *CANARY_OPS)
PATTERNS = {
    "SESSION": rf"B1 SESSION (?P<sid>{SID}) END\n",
    "READY_SESSION": rf"B1 READY_SESSION (?P<sid>{SID}) (?P<pid>[1-9][0-9]*) (?P<uptime>{NUMBER}) END\n",
    "JOB": rf"B1 JOB (?P<sid>{SID}) (?P<seq>{SEQ}) (?P<op>{'|'.join(OPERATIONS)}) END\n",
    "READY": rf"B1 READY (?P<sid>{SID}) (?P<seq>{SEQ}) (?P<size>{NUMBER}) (?P<sha>{SHA}) END\n",
    "ACCEPTED": rf"B1 ACCEPTED (?P<sid>{SID}) (?P<seq>{SEQ}) (?P<size>{NUMBER}) (?P<sha>{SHA}) END\n",
    "DONE": rf"B1 DONE (?P<sid>{SID}) (?P<seq>{SEQ}) (?P<rc>{NUMBER}) (?P<size>{NUMBER}) (?P<sha>{SHA}) END\n",
    "CLOSED": rf"B1 CLOSED (?P<sid>{SID}) (?P<reason>STOP|TTL|LIMIT|ERROR) END\n",
    "RECEIVER": rf"B1 RECEIVER (?P<sid>{SID}) B2 END\n",
}
SNAPSHOT_PATH = re.compile(
    r"report=/storage/[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}/Download/FindUAS/Probe/"
    r"(?P<name>FindUAS_F4_[0-9]{8}T[0-9]{6}Z_[1-9][0-9]*\.txt)"
)


class BridgeError(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record(data: bytes, kind: str, sid: str | None = None, seq: str | None = None) -> dict:
    if len(data) > 256:
        raise BridgeError("RECORD_TOO_LARGE")
    try:
        match = re.fullmatch(PATTERNS[kind], data.decode("ascii"))
    except UnicodeDecodeError:
        match = None
    if match is None:
        raise BridgeError("NONCANONICAL_" + kind)
    fields = match.groupdict()
    if (sid is not None and fields["sid"] != sid) or (seq is not None and fields.get("seq") != seq):
        raise BridgeError("RECORD_ID_MISMATCH")
    if "seq" in fields and not 1 <= int(fields["seq"]) <= LIMIT:
        raise BridgeError("SEQUENCE_OUT_OF_RANGE")
    if "rc" in fields and int(fields["rc"]) > 255:
        raise BridgeError("INVALID_HANDLER_RC")
    if "size" in fields and not 1 <= int(fields["size"]) <= (MAX_REPORT if kind == "DONE" else 256):
        raise BridgeError("RECORD_SIZE_OUT_OF_RANGE")
    return fields


def session_text(sid: str) -> bytes:
    return f"B1 SESSION {sid} END\n".encode("ascii")


def job_text(sid: str, seq: str, op: str) -> bytes:
    data = f"B1 JOB {sid} {seq} {op} END\n".encode("ascii")
    record(data, "JOB", sid, seq)
    return data


def ready_text(job: bytes) -> bytes:
    fields = record(job, "JOB")
    return f"B1 READY {fields['sid']} {fields['seq']} {len(job)} {digest(job)} END\n".encode("ascii")


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def immutable(path: Path, data: bytes) -> None:
    """Publish a durable local snapshot without replacing another record."""
    if path.is_symlink():
        raise BridgeError("LOCAL_RECORD_SYMLINK")
    if path.exists():
        if path.read_bytes() != data:
            raise BridgeError("LOCAL_RECORD_CONFLICT")
        return
    temp = path.parent / (".new-" + secrets.token_hex(12))
    with temp.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    try:
        os.link(temp, path)
        sync_directory(path.parent)
    finally:
        temp.unlink()


class State:
    def __init__(self, path: Path):
        path = path.expanduser().absolute()
        repo = Path(__file__).resolve().parents[2]
        resolved = path.resolve()
        if resolved.is_relative_to(repo) and not resolved.is_relative_to(repo / "private"):
            raise BridgeError("STATE_DIR_MUST_BE_PRIVATE_OR_OUTSIDE_REPOSITORY")
        if path.is_symlink():
            raise BridgeError("STATE_DIR_SYMLINK")
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = path.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise BridgeError("STATE_DIR_MUST_BE_OWNED_AND_MODE_0700")
        self.root = path
        for name in ("logs", "receipts", "sessions", "staged"):
            child = path / name
            if child.is_symlink():
                raise BridgeError("STATE_SUBDIRECTORY_SYMLINK")
            child.mkdir(mode=0o700, exist_ok=True)

    @contextmanager
    def lock(self):
        fd = os.open(self.root / ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise BridgeError("STATE_BUSY") from None
            yield
        finally:
            os.close(fd)

    def current(self) -> str | None:
        path = self.root / "current.session"
        return record(path.read_bytes(), "SESSION")["sid"] if path.exists() else None

    def select(self, sid: str):
        data = session_text(sid)
        record(data, "SESSION")
        temp = self.root / (".current-" + secrets.token_hex(12))
        immutable(temp, data)
        os.replace(temp, self.root / "current.session")
        sync_directory(self.root)

    def session(self, sid: str) -> Path:
        if not re.fullmatch(SID, sid):
            raise BridgeError("INVALID_SESSION_ID")
        return self.root / "sessions" / sid

    def own(self, sid: str):
        directory = self.session(sid)
        directory.mkdir(mode=0o700, exist_ok=True)
        (directory / "tasks").mkdir(mode=0o700, exist_ok=True)
        immutable(directory / "owned.session", session_text(sid))
        self.select(sid)

    def require_owned(self, sid: str):
        path = self.session(sid) / "owned.session"
        if not path.is_file() or path.is_symlink() or path.read_bytes() != session_text(sid):
            raise BridgeError("ORIGINAL_STATE_DIR_REQUIRED")


class Transport:
    def __init__(self, executable: Path, state: State, timeout: float = 30):
        if not 0 < timeout <= 30:
            raise BridgeError("INVALID_TRANSPORT_TIMEOUT")
        self.executable, self.state, self.timeout = executable.absolute(), state, timeout
        # Cool down before the first call too, including across separate CLI processes.
        self.last_finished = time.monotonic()

    def call(self, operation: str, *arguments: str) -> int:
        wait = 1.0 - (time.monotonic() - self.last_finished)
        if wait > 0:
            time.sleep(wait)
        token = secrets.token_hex(12)
        prefix = self.state.root / "logs" / token
        args = [str(self.executable), operation, *map(str, arguments)]
        result = {"argv": args, "timeout_seconds": self.timeout}
        try:
            with prefix.with_suffix(".stdout").open("xb") as stdout, prefix.with_suffix(".stderr").open("xb") as stderr:
                completed = subprocess.run(args, stdout=stdout, stderr=stderr, timeout=self.timeout, check=False)
                result["returncode"] = completed.returncode
        except subprocess.TimeoutExpired:
            result["timeout"] = True
            raise BridgeError("TRANSPORT_TIMEOUT_UNCERTAIN") from None
        except OSError:
            result["spawn_error"] = True
            raise BridgeError("TRANSPORT_START_FAILED") from None
        finally:
            self.last_finished = time.monotonic()
            result["ended_monotonic"] = self.last_finished
            immutable(prefix.with_suffix(".json"), json.dumps(result, sort_keys=True).encode() + b"\n")
        if completed.returncode == 3 and operation == "get":
            return 3
        if completed.returncode != 0:
            raise BridgeError("TRANSPORT_FAILED_UNCERTAIN")
        return 0

    def get(self, remote: str) -> bytes | None:
        target = self.state.root / "receipts" / (secrets.token_hex(12) + ".bin")
        if self.call("get", remote, str(target)) == 3:
            if target.exists():
                raise BridgeError("MISSING_WITH_LOCAL_PAYLOAD")
            return None
        if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_REPORT:
            raise BridgeError("INVALID_TRANSPORT_PAYLOAD")
        return target.read_bytes()

    def put(self, remote: str, local: Path):
        self.call("put", remote, str(local))

    def mkdir(self, remote: str):
        self.call("mkdir", remote)

    def archive(self, sid: str):
        self.call("archive-active", sid)


def canary_preflight_ready(content: bytes) -> bool:
    try:
        lines = content.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        return False
    section, previous, fields = None, "", []
    for line in lines:
        if section is not None:
            if line == "END " + section:
                if not re.fullmatch(rf"command\.{re.escape(section)}\.rc={NUMBER}", previous):
                    return False
                section = None
        elif line.startswith("BEGIN "):
            if not re.fullmatch(r"BEGIN [a-z][a-z0-9_.]*", line):
                return False
            section = line[6:]
        elif line.startswith("END "):
            return False
        elif line.startswith("preflight_ready="):
            fields.append(line)
        previous = line
    return section is None and fields == ["preflight_ready=true"]


def validate_result(job: bytes, accepted: bytes, done: bytes, report: bytes) -> dict:
    task = record(job, "JOB")
    sid, seq, op = task["sid"], task["seq"], task["op"]
    ack = record(accepted, "ACCEPTED", sid, seq)
    result = record(done, "DONE", sid, seq)
    if int(ack["size"]) != len(job) or ack["sha"] != digest(job):
        raise BridgeError("ACCEPTED_JOB_MISMATCH")
    if int(result["size"]) != len(report) or result["sha"] != digest(report):
        raise BridgeError("REPORT_DIGEST_OR_SIZE_MISMATCH")
    rc = int(result["rc"])
    prefix = f"schema=finduas-sd-bridge/v1\nsid={sid}\nseq={seq}\nop=".encode()
    suffix = f"handler_end=true\nhandler_rc={rc}\nreport_end=true\n".encode()
    actual_op = op
    if report.startswith(prefix + b"REJECTED\nhandler_begin=true\n") and rc == 65:
        actual_op = "REJECTED"
    beginning = prefix + actual_op.encode() + b"\nhandler_begin=true\n"
    if not report.startswith(beginning) or not report.endswith(suffix):
        raise BridgeError("REPORT_ENVELOPE_MISMATCH")
    body = report[len(beginning):-len(suffix)]
    if b"handler_begin=true\n" in body or b"handler_end=true\n" in body:
        raise BridgeError("REPORT_DUPLICATE_BOUNDARY")
    summary = {"sid": sid, "seq": seq, "op": actual_op, "handler_rc": rc,
               "report_sha256": digest(report), "snapshot": None}
    if actual_op in CANARY_OPS:
        beginning = (f"schema=finduas-rc2-canary-loader/v1\nsid={sid}\n"
                     f"operation={actual_op}\nreport_begin=true\n").encode()
        ending = b"report_end=true\n"
        complete = body.startswith(beginning) and body.endswith(ending)
        summary["canary_validation"] = ("envelope_received_only" if complete else
                                        "incomplete_envelope" if rc else "invalid_envelope")
        summary["canary_preflight_ready"] = complete and canary_preflight_ready(body[len(beginning):-len(ending)])
    if actual_op == "SNAPSHOT" and rc in (0, 10):
        try:
            lines = body.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            raise BridgeError("SNAPSHOT_OUTPUT_ENCODING") from None
        paths = [line for line in lines if line.startswith("report=")]
        match = SNAPSHOT_PATH.fullmatch(paths[0]) if len(paths) == 1 else None
        if match is None or len(match["name"]) > 127 or lines.count("F4_END") != 1:
            raise BridgeError("SNAPSHOT_PATH_OR_END_MARKER_INVALID")
        expected_state = "COMPLETE" if rc == 0 else "INCOMPLETE"
        if lines.count("F4_SAVED state=" + expected_state) != 1:
            raise BridgeError("SNAPSHOT_HANDLER_STATE_MISMATCH")
        summary["snapshot"] = match["name"]
    return summary


def validate_snapshot(data: bytes):
    if len(data) > MAX_REPORT or not data.startswith(b"schema=finduas-rc2-fuli-baseline/v4\nreport_begin=true\n") or not data.endswith(b"report_end=true\n"):
        raise BridgeError("F4_ENVELOPE_INVALID")


def unavailable_summary(task: dict, closed: bytes) -> dict:
    fields = record(closed, "CLOSED", task["sid"])
    return {"sid": task["sid"], "seq": task["seq"], "op": task["op"],
            "outcome": "UNKNOWN", "closed_reason": fields["reason"], "closed_sha256": digest(closed)}


class Client:
    def __init__(self, state: State, transport):
        self.state, self.transport = state, transport

    def task_path(self, sid: str, seq: str, suffix: str) -> Path:
        return self.state.session(sid) / "tasks" / (seq + suffix)

    def history(self, sid: str) -> list[dict]:
        self.state.require_owned(sid)
        directory = self.state.session(sid) / "tasks"
        tasks = []
        for path in sorted(directory.glob("*.job")):
            seq = f"{len(tasks) + 1:04d}"
            if path.name != seq + ".job" or len(tasks) >= LIMIT:
                raise BridgeError("LOCAL_SEQUENCE_HISTORY_INVALID")
            job = path.read_bytes()
            task = record(job, "JOB", sid, seq)
            task["complete"] = False
            task["unavailable"] = False
            ready = self.task_path(sid, seq, ".ready")
            if ready.exists() and ready.read_bytes() != ready_text(job):
                raise BridgeError("LOCAL_READY_CONFLICT")
            marker = self.task_path(sid, seq, ".collected.json")
            unavailable = self.task_path(sid, seq, ".unavailable.json")
            if marker.exists() and unavailable.exists():
                raise BridgeError("LOCAL_TERMINAL_RECORD_CONFLICT")
            if marker.exists():
                summary = validate_result(job, self.task_path(sid, seq, ".accepted").read_bytes(),
                    self.task_path(sid, seq, ".done").read_bytes(), self.task_path(sid, seq, ".report").read_bytes())
                if summary["snapshot"]:
                    snapshot = self.task_path(sid, seq, ".snapshot.txt").read_bytes()
                    validate_snapshot(snapshot)
                    summary["snapshot_sha256"] = digest(snapshot)
                    summary["snapshot_validation"] = "envelope_received_only"
                if json.loads(marker.read_bytes()) != summary:
                    raise BridgeError("LOCAL_COLLECTION_RECORD_INVALID")
                task["complete"] = True
                task["handler_rc"] = summary["handler_rc"]
                task["canary_validation"] = summary.get("canary_validation")
                task["canary_preflight_ready"] = summary.get("canary_preflight_ready", False)
            elif unavailable.exists():
                closed = self.task_path(sid, seq, ".closed").read_bytes()
                if json.loads(unavailable.read_bytes()) != unavailable_summary(task, closed):
                    raise BridgeError("LOCAL_UNAVAILABLE_RECORD_INVALID")
                task["complete"] = task["unavailable"] = True
            tasks.append(task)
        if any(not task["complete"] for task in tasks[:-1]):
            raise BridgeError("LOCAL_UNFINISHED_SEQUENCE_GAP")
        known = {task["seq"] for task in tasks}
        for path in directory.iterdir():
            if not path.name.startswith(".") and path.name[:4] not in known:
                raise BridgeError("ORPHAN_LOCAL_TASK_RECORD")
        return tasks

    def active(self) -> str | None:
        data = self.transport.get(BASE + "/active.session")
        return record(data, "SESSION")["sid"] if data is not None else None

    def check_next_empty(self, sid: str, sequence: int):
        if sequence > LIMIT:
            return
        seq = f"{sequence:04d}"
        for area, suffix in (("inbox", ".job"), ("inbox", ".ready"),
                             ("outbox", ".accepted"), ("outbox", ".report"), ("outbox", ".done")):
            if self.transport.get(f"{BASE}/{sid}/{area}/{seq}{suffix}") is not None:
                raise BridgeError("REMOTE_HISTORY_REQUIRES_ORIGINAL_STATE")

    def prepare(self) -> str:
        active, current = self.active(), self.state.current()
        if active is not None and current not in (None, active):
            raise BridgeError("LOCAL_ACTIVE_SESSION_CONFLICT")
        if active is not None:
            closed = self.transport.get(f"{BASE}/{active}/session.closed")
            if closed is None:
                self.state.require_owned(active)
                if current not in (None, active):
                    raise BridgeError("LOCAL_ACTIVE_SESSION_CONFLICT")
                tasks = self.history(active)
                if any(task["unavailable"] for task in tasks):
                    raise BridgeError("CLOSED_SESSION_RECORD_MISSING")
                self.check_next_empty(active, len(tasks) + 1)
                self.state.select(active)
                return "SESSION_REUSED"
            record(closed, "CLOSED", active)
            if current == active and any(not t["complete"] for t in self.history(active)):
                raise BridgeError("COLLECT_PENDING_TASK_BEFORE_ROTATION")
            self.transport.archive(active)
            if current == active:
                immutable(self.state.session(active) / "closed.session", closed)
            current = None
        elif current is not None:
            tasks = self.history(current)
            closed = self.transport.get(f"{BASE}/{current}/session.closed")
            if closed is not None:
                record(closed, "CLOSED", current)
                if any(not t["complete"] for t in tasks):
                    raise BridgeError("COLLECT_PENDING_TASK_BEFORE_ROTATION")
                archived = self.transport.get(f"{BASE}/{current}/active.session")
                if archived != session_text(current):
                    raise BridgeError("ARCHIVED_SESSION_NOT_VERIFIED")
                immutable(self.state.session(current) / "closed.session", closed)
                current = None
            elif tasks:
                raise BridgeError("ACTIVE_MISSING_WITH_LOCAL_TASKS")
        if current is None:
            current = secrets.token_hex(8)
            self.state.own(current)
        self.check_next_empty(current, 1)
        if self.transport.get(f"{BASE}/{current}/worker.lock") is not None:
            raise BridgeError("REMOTE_HISTORY_REQUIRES_ORIGINAL_STATE")
        for path in (f"{BASE}/{current}/inbox", f"{BASE}/{current}/outbox", "Download/FindUAS/Probe"):
            self.transport.mkdir(path)
        # The durable SID and owned.session already exist locally before activation.
        self.transport.put(BASE + "/active.session", self.state.session(current) / "owned.session")
        return "SESSION_PREPARED"

    def stage(self, b1: Path, f4: Path) -> str:
        return self.stage_files((("B1.sh", b1), ("F4.sh", f4)))

    def stage_canary(self, b2: Path, l1: Path, canary: Path) -> str:
        return self.stage_files((("B2.sh", b2), ("L1.sh", l1), ("FindUAS_ARTTI_V2.so", canary)))

    def stage_files(self, files) -> str:
        for basename, source in files:
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 32768:
                raise BridgeError("STAGE_SOURCE_INVALID")
            data = source.read_bytes()
            if not data or len(data) > 32768:
                raise BridgeError("STAGE_SOURCE_INVALID")
            saved = self.state.root / "staged" / (digest(data) + "-" + basename)
            immutable(saved, data)
            self.transport.put("Download/" + basename, saved)
        return "SCRIPTS_STAGED_VERIFIED"

    def status(self) -> str:
        sid = self.active()
        if sid is None:
            return "NO_ACTIVE_SESSION"
        closed = self.transport.get(f"{BASE}/{sid}/session.closed")
        if closed is not None:
            return "SESSION_CLOSED reason=" + record(closed, "CLOSED", sid)["reason"]
        ready = self.transport.get(f"{BASE}/{sid}/session.ready")
        if ready is None:
            return "SESSION_AWAITING_START"
        record(ready, "READY_SESSION", sid)
        return "SESSION_READY_LIVENESS_NOT_PROVEN"

    def submit(self, operation: str) -> str:
        if operation not in OPERATIONS:
            raise BridgeError("INVALID_OPERATION")
        sid = self.state.current()
        if sid is None:
            raise BridgeError("PREPARE_REQUIRED")
        tasks = self.history(sid)
        if any(task["unavailable"] for task in tasks):
            raise BridgeError("CLOSED_SESSION_MUST_ROTATE")
        if self.active() != sid:
            raise BridgeError("ACTIVE_SESSION_CHANGED")
        closed = self.transport.get(f"{BASE}/{sid}/session.closed")
        if closed is not None:
            record(closed, "CLOSED", sid)
            raise BridgeError("SESSION_CLOSED")
        ready = self.transport.get(f"{BASE}/{sid}/session.ready")
        if ready is None:
            raise BridgeError("SESSION_NOT_READY")
        record(ready, "READY_SESSION", sid)
        if operation in CANARY_OPS:
            receiver = self.transport.get(f"{BASE}/{sid}/session.receiver")
            if receiver is None:
                raise BridgeError("B2_RECEIVER_REQUIRED")
            record(receiver, "RECEIVER", sid)
        if operation == "CANARY_LOAD":
            previous_loads = [task for task in tasks if task["op"] == "CANARY_LOAD"]
            if previous_loads and not (previous_loads[-1] is tasks[-1] and not tasks[-1]["complete"]):
                raise BridgeError("CANARY_LOAD_ALREADY_CREATED_FOR_SESSION")
            baselines = [task for task in tasks if task["op"] == "CANARY_BASELINE"]
            if not baselines or not baselines[-1]["complete"] or baselines[-1].get("handler_rc") != 0 or \
                    baselines[-1].get("canary_validation") != "envelope_received_only" or \
                    not baselines[-1].get("canary_preflight_ready"):
                raise BridgeError("SUCCESSFUL_CANARY_BASELINE_REQUIRED")
        if tasks and not tasks[-1]["complete"]:
            task = tasks[-1]
            if task["op"] != operation:
                raise BridgeError("TASK_PENDING_DIFFERENT_OPERATION")
            seq = task["seq"]
        else:
            if len(tasks) >= LIMIT:
                raise BridgeError("SESSION_TASK_LIMIT")
            seq = f"{len(tasks) + 1:04d}"
            self.check_next_empty(sid, len(tasks) + 1)
            immutable(self.task_path(sid, seq, ".job"), job_text(sid, seq, operation))
        job = self.task_path(sid, seq, ".job")
        ready_file = self.task_path(sid, seq, ".ready")
        immutable(ready_file, ready_text(job.read_bytes()))
        self.transport.put(f"{BASE}/{sid}/inbox/{seq}.job", job)
        self.transport.put(f"{BASE}/{sid}/inbox/{seq}.ready", ready_file)
        return "TASK_SUBMITTED seq=" + seq

    def collect(self, sequence: str) -> str:
        if not re.fullmatch(SEQ, sequence) or not 1 <= int(sequence) <= LIMIT:
            raise BridgeError("INVALID_SEQUENCE")
        sid = self.state.current()
        if sid is None:
            raise BridgeError("ORIGINAL_STATE_DIR_REQUIRED")
        tasks = self.history(sid)
        if int(sequence) > len(tasks):
            raise BridgeError("UNKNOWN_LOCAL_TASK")
        task = tasks[int(sequence) - 1]
        if task["complete"]:
            if task["unavailable"]:
                return "TASK_UNAVAILABLE seq=" + sequence + " outcome=UNKNOWN"
            return "TASK_ALREADY_COLLECTED seq=" + sequence
        remote = f"{BASE}/{sid}/outbox/{sequence}"
        done = self.transport.get(remote + ".done")
        if done is None:
            closed = self.transport.get(f"{BASE}/{sid}/session.closed")
            if closed is not None:
                summary = unavailable_summary(task, closed)
                # A normal STOP can finish between the first done read and closed.
                done = self.transport.get(remote + ".done")
                if done is None:
                    immutable(self.task_path(sid, sequence, ".closed"), closed)
                    immutable(self.task_path(sid, sequence, ".unavailable.json"),
                              json.dumps(summary, sort_keys=True).encode() + b"\n")
                    return "TASK_UNAVAILABLE seq=" + sequence + " outcome=UNKNOWN"
            else:
                return "TASK_PENDING seq=" + sequence
        record(done, "DONE", sid, sequence)
        accepted = self.transport.get(remote + ".accepted")
        report = self.transport.get(remote + ".report")
        if accepted is None or report is None:
            raise BridgeError("DONE_WITH_MISSING_RESULT_FILES")
        job = self.task_path(sid, sequence, ".job").read_bytes()
        summary = validate_result(job, accepted, done, report)
        if summary["snapshot"]:
            snapshot = self.transport.get("Download/FindUAS/Probe/" + summary["snapshot"])
            if snapshot is None:
                raise BridgeError("SNAPSHOT_REPORT_NOT_RECEIVED")
            validate_snapshot(snapshot)
            immutable(self.task_path(sid, sequence, ".snapshot.txt"), snapshot)
            summary["snapshot_sha256"] = digest(snapshot)
            summary["snapshot_validation"] = "envelope_received_only"
        for suffix, data in ((".accepted", accepted), (".done", done), (".report", report)):
            immutable(self.task_path(sid, sequence, suffix), data)
        immutable(self.task_path(sid, sequence, ".collected.json"), json.dumps(summary, sort_keys=True).encode() + b"\n")
        return f"TASK_COLLECTED seq={sequence} handler_rc={summary['handler_rc']}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--transport", type=Path, default=Path(__file__).resolve().parent / "build/mtp_bridge")
    parser.add_argument("--transport-timeout", type=float, default=30)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "status"):
        commands.add_parser(name)
    stage = commands.add_parser("stage")
    stage.add_argument("--b1", type=Path, required=True)
    stage.add_argument("--f4", type=Path, required=True)
    canary = commands.add_parser("stage-canary")
    canary.add_argument("--b2", type=Path, required=True)
    canary.add_argument("--l1", type=Path, required=True)
    canary.add_argument("--canary", type=Path, required=True)
    submit = commands.add_parser("submit")
    submit.add_argument("operation", choices=OPERATIONS)
    commands.add_parser("collect").add_argument("sequence")
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        state = State(args.state_dir)
        with state.lock():
            client = Client(state, Transport(args.transport, state, args.transport_timeout))
            if args.command == "stage":
                output = client.stage(args.b1, args.f4)
            elif args.command == "stage-canary":
                output = client.stage_canary(args.b2, args.l1, args.canary)
            elif args.command == "submit":
                output = client.submit(args.operation)
            elif args.command == "collect":
                output = client.collect(args.sequence)
            else:
                output = getattr(client, args.command)()
            print(output)
        return 0
    except BridgeError as error:
        print("ERROR code=" + str(error), file=sys.stderr)
    except (OSError, ValueError, KeyError):
        print("ERROR code=LOCAL_STATE_OR_IO_INVALID", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
