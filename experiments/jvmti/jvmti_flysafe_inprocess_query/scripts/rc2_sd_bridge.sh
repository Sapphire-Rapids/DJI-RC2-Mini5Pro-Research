#!/system/bin/sh
# B1: finite SD mailbox; job data selects only PING, SNAPSHOT or STOP.
PATH=/system/bin
LC_ALL=C
export PATH LC_ALL
set -f
umask 077
B1_LF='
'
B1_NUL_MARKER=$(printf '\001')
B1_F4_EXPECTED_SHA=91c77ffcfcae83f062dd43425ea350cf161c4ea67a429cd527f0a01f410a817e
B1_F4_MAX_BYTES=32768

valid_sid() {
    [ "${#1}" -eq 16 ] || return 1
    case "$1" in *[!0-9a-f]*) return 1 ;; esac
}

valid_sha() {
    [ "${#1}" -eq 64 ] || return 1
    case "$1" in *[!0-9a-f]*) return 1 ;; esac
}

fail_start() { printf 'B1_ERROR code=%s\n' "$1"; exit 64; }
case "$0" in /storage/*/Download/B1.sh) ;; *) fail_start INVALID_START_PATH ;; esac
B1_VOLUME=${0#/storage/}
B1_VOLUME=${B1_VOLUME%/Download/B1.sh}
case "$B1_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) fail_start INVALID_VOLUME ;;
esac
[ -f "$0" ] && [ ! -L "$0" ] || fail_start SCRIPT_NOT_REGULAR
B1_BASE=/storage/$B1_VOLUME/Download
B1_BRIDGE=$B1_BASE/FindUAS/Bridge
B1_F4_PATH=$B1_BASE/F4.sh

# Read at most limit+1 bytes once. A marker preserves the final newline in RAM;
# NUL is replaced with a forbidden byte so shell NUL handling cannot erase it.
read_snapshot() {
    [ -f "$1" ] && [ ! -L "$1" ] && [ -r "$1" ] || return 1
    if B1_CAPTURE=$(
        set -o pipefail || exit 1
        if head -c "$(($2 + 1))" "$1" | tr '\000' '\001'; then
            B1_CAPTURE_RC=0
        else
            B1_CAPTURE_RC=$?
        fi
        printf '.'
        exit "$B1_CAPTURE_RC"
    ); then :; else return 1; fi
    B1_TEXT=${B1_CAPTURE%.}
    B1_TEXT_SIZE=${#B1_TEXT}
    [ "$B1_TEXT_SIZE" -le "$2" ] || return 1
    case "$B1_TEXT" in *"$B1_NUL_MARKER"*) return 1 ;; esac
}

hash_text() {
    if B1_HASH_OUTPUT=$(set -o pipefail || exit 1; printf '%s' "$1" | sha256sum); then
        B1_HASH=${B1_HASH_OUTPUT%% *}
        valid_sha "$B1_HASH"
    else
        return 1
    fi
}

write_once() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || return 1
    (set -C; printf '%s' "$2" >"$1")
}

monotonic_seconds() {
    IFS=' ' read -r B1_UPTIME B1_UNUSED </proc/uptime || return 1
    case "$B1_UPTIME" in *.*) ;; *) return 1 ;; esac
    B1_NOW=${B1_UPTIME%%.*}
    B1_FRACTION=${B1_UPTIME#*.}
    case "$B1_NOW" in ''|*[!0-9]*) return 1 ;; esac
    case "$B1_FRACTION" in ''|*[!0-9]*) return 1 ;; esac
    case "$B1_NOW" in 0|[1-9]*) ;; *) return 1 ;; esac
    [ "${#B1_NOW}" -le 10 ] || return 1
    [ "$B1_NOW" -le 2147480000 ] || return 1
}

parse_ready() {
    read_snapshot "$B1_INBOX/$B1_SEQ.ready" 256 || return 1
    set -- $B1_TEXT
    [ "$#" -eq 7 ] || return 1
    [ "$1" = B1 ] && [ "$2" = READY ] && [ "$3" = "$B1_SID" ] &&
        [ "$4" = "$B1_SEQ" ] && [ "$7" = END ] || return 1
    case "$5" in ''|0*|*[!0-9]*) return 1 ;; esac
    [ "${#5}" -le 3 ] && [ "$5" -le 256 ] || return 1
    valid_sha "$6" || return 1
    [ "$B1_TEXT" = "B1 READY $B1_SID $B1_SEQ $5 $6 END$B1_LF" ] || return 1
    B1_JOB_SIZE=$5
    B1_JOB_SHA=$6
}

parse_job() {
    read_snapshot "$B1_INBOX/$B1_SEQ.job" 256 || return 1
    [ "$B1_TEXT_SIZE" -eq "$B1_JOB_SIZE" ] || return 1
    hash_text "$B1_TEXT" && [ "$B1_HASH" = "$B1_JOB_SHA" ] || return 1
    set -- $B1_TEXT
    [ "$#" -eq 6 ] || return 1
    [ "$1" = B1 ] && [ "$2" = JOB ] && [ "$3" = "$B1_SID" ] &&
        [ "$4" = "$B1_SEQ" ] && [ "$6" = END ] || return 1
    case "$5" in PING|SNAPSHOT|STOP) ;; *) return 1 ;; esac
    [ "$B1_TEXT" = "B1 JOB $B1_SID $B1_SEQ $5 END$B1_LF" ] || return 1
    B1_OP=$5
}

handle_ping() {
    id
    B1_ID_RC=$?
    printf 'command.identity.rc=%s\n' "$B1_ID_RC"
    if monotonic_seconds; then
        printf 'uptime_seconds=%s\ncommand.uptime.rc=0\n' "$B1_NOW"
    else
        printf 'command.uptime.rc=70\n'
        return 70
    fi
    return "$B1_ID_RC"
}

handle_snapshot() {
    valid_sha "$B1_F4_EXPECTED_SHA" || { printf 'snapshot_error=EXPECTED_HASH_UNSET\n'; return 69; }
    read_snapshot "$B1_F4_PATH" "$B1_F4_MAX_BYTES" || {
        printf 'snapshot_error=HELPER_READ_REJECTED\n'; return 65;
    }
    hash_text "$B1_TEXT" && [ "$B1_HASH" = "$B1_F4_EXPECTED_SHA" ] || {
        printf 'snapshot_error=HELPER_HASH_MISMATCH\n'; return 65;
    }
    monotonic_seconds || return 70
    [ "$((B1_NOW - B1_STARTED))" -lt 3555 ] || {
        printf 'snapshot_error=SESSION_EXPIRING\n'; return 124;
    }
    # This is only the reviewed F4 text, never a job's bytes or a caller argument.
    timeout 45 sh -c "$B1_TEXT" "$B1_F4_PATH"
}

dispatch() {
    case "$B1_OP" in
        PING) handle_ping ;;
        SNAPSHOT) handle_snapshot ;;
        STOP) printf 'stop_requested=true\n' ;;
        REJECTED) printf 'job_error=SNAPSHOT_OR_CANONICAL_CHECK_FAILED\n'; return 65 ;;
        *) return 65 ;;
    esac
}

write_report() {
    [ ! -e "$B1_REPORT" ] && [ ! -L "$B1_REPORT" ] || return 74
    (
        set -C
        exec 3>"$B1_REPORT" || exit 74
        set +C
        printf 'schema=finduas-sd-bridge/v1\nsid=%s\nseq=%s\nop=%s\nhandler_begin=true\n' \
            "$B1_SID" "$B1_SEQ" "$B1_OP" >&3 || exit 74
        if dispatch >&3 2>&1; then B1_HANDLER_RC=0; else B1_HANDLER_RC=$?; fi
        printf 'handler_end=true\nhandler_rc=%s\nreport_end=true\n' "$B1_HANDLER_RC" >&3 || exit 74
        exec 3>&- || exit 74
        # Only a newly created, completed and closed report returns a handler rc.
        printf '%s' "$B1_HANDLER_RC"
    )
}

close_session() {
    write_once "$B1_SESSION/session.closed" "B1 CLOSED $B1_SID $1 END$B1_LF"
}

worker() {
    trap '' HUP
    write_once "$B1_SESSION/worker.lock" "B1 LOCK $B1_SID $$ END$B1_LF" || return 73
    for B1_TOOL in head tr sha256sum timeout id sleep stat tail; do
        command -v "$B1_TOOL" >/dev/null 2>&1 || { close_session ERROR; return 70; }
    done
    monotonic_seconds || { close_session ERROR; return 70; }
    B1_STARTED=$B1_NOW
    write_once "$B1_SESSION/session.ready" "B1 READY_SESSION $B1_SID $$ $B1_STARTED END$B1_LF" || {
        close_session ERROR; return 74;
    }
    B1_NUMBER=1
    while [ "$B1_NUMBER" -le 64 ]; do
        monotonic_seconds || { close_session ERROR; return 70; }
        if [ "$B1_NOW" -lt "$B1_STARTED" ]; then close_session ERROR; return 70; fi
        if [ "$((B1_NOW - B1_STARTED))" -ge 3600 ]; then close_session TTL; return; fi
        B1_SEQ=$(printf '%04d' "$B1_NUMBER")
        if ! parse_ready; then sleep 1; continue; fi
        for B1_SUFFIX in report done; do
            if [ -e "$B1_OUTBOX/$B1_SEQ.$B1_SUFFIX" ] || [ -L "$B1_OUTBOX/$B1_SEQ.$B1_SUFFIX" ]; then
                close_session ERROR; return 74;
            fi
        done
        write_once "$B1_OUTBOX/$B1_SEQ.accepted" \
            "B1 ACCEPTED $B1_SID $B1_SEQ $B1_JOB_SIZE $B1_JOB_SHA END$B1_LF" || {
            close_session ERROR; return 73;
        }
        B1_OP=REJECTED
        parse_job || B1_OP=REJECTED
        B1_REPORT=$B1_OUTBOX/$B1_SEQ.report
        if B1_RC=$(write_report); then :; else close_session ERROR; return 74; fi
        case "$B1_RC" in ''|*[!0-9]*) close_session ERROR; return 74 ;; esac
        [ "${#B1_RC}" -le 3 ] && [ "$B1_RC" -le 255 ] || { close_session ERROR; return 74; }
        [ -f "$B1_REPORT" ] && [ ! -L "$B1_REPORT" ] &&
            [ "$(tail -n 1 "$B1_REPORT")" = report_end=true ] || {
                close_session ERROR; return 74;
            }
        B1_REPORT_SIZE=$(stat -c %s "$B1_REPORT") || { close_session ERROR; return 74; }
        case "$B1_REPORT_SIZE" in ''|*[!0-9]*) close_session ERROR; return 74 ;; esac
        B1_HASH_OUTPUT=$(sha256sum "$B1_REPORT") || { close_session ERROR; return 74; }
        B1_HASH=${B1_HASH_OUTPUT%% *}
        valid_sha "$B1_HASH" || { close_session ERROR; return 74; }
        write_once "$B1_OUTBOX/$B1_SEQ.done" \
            "B1 DONE $B1_SID $B1_SEQ $B1_RC $B1_REPORT_SIZE $B1_HASH END$B1_LF" || {
            close_session ERROR; return 74;
        }
        if [ "$B1_OP" = STOP ]; then close_session STOP; return; fi
        B1_NUMBER=$((B1_NUMBER + 1))
        sleep 1
    done
    close_session LIMIT
}

case "$#" in
    0)
        read_snapshot "$B1_BRIDGE/active.session" 256 || fail_start ACTIVE_SESSION_UNAVAILABLE
        set -- $B1_TEXT
        [ "$#" -eq 4 ] && [ "$1" = B1 ] && [ "$2" = SESSION ] && [ "$4" = END ] ||
            fail_start INVALID_ACTIVE_SESSION
        B1_SID=$3
        valid_sid "$B1_SID" || fail_start INVALID_SESSION_ID
        [ "$B1_TEXT" = "B1 SESSION $B1_SID END$B1_LF" ] || fail_start NONCANONICAL_ACTIVE_SESSION
        B1_MODE=launch
        ;;
    2)
        [ "$1" = --worker ] || fail_start ARGUMENTS_REJECTED
        B1_SID=$2
        valid_sid "$B1_SID" || fail_start INVALID_SESSION_ID
        B1_MODE=worker
        ;;
    *) fail_start ARGUMENTS_REJECTED ;;
esac
B1_SESSION=$B1_BRIDGE/$B1_SID
B1_INBOX=$B1_SESSION/inbox
B1_OUTBOX=$B1_SESSION/outbox
for B1_DIRECTORY in "$B1_BASE" "$B1_BASE/FindUAS" "$B1_BRIDGE" "$B1_SESSION" "$B1_INBOX" "$B1_OUTBOX"; do
    [ -d "$B1_DIRECTORY" ] && [ ! -L "$B1_DIRECTORY" ] || fail_start SESSION_DIRECTORY_UNAVAILABLE
done

if [ "$B1_MODE" = worker ]; then
    worker
    exit $?
fi
[ ! -L "$B1_SESSION/worker.log" ] || fail_start INVALID_WORKER_LOG
if [ -e "$B1_SESSION/worker.log" ] && [ ! -f "$B1_SESSION/worker.log" ]; then
    fail_start INVALID_WORKER_LOG
fi
(
    trap '' HUP
    exec sh "$0" --worker "$B1_SID" </dev/null >>"$B1_SESSION/worker.log" 2>&1 3>&-
) &
printf 'B1_START_REQUESTED sid=%s\n' "$B1_SID"
exit 0
