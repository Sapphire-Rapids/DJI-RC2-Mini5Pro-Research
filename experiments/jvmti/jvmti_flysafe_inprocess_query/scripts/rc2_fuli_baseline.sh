#!/system/bin/sh
# Fixed read-only Fuli baseline. Only a new report on the launching SD may be written.
exec 2>&1
PATH=/system/bin
export PATH
LC_ALL=C
export LC_ALL
set -f

fail_start() { printf 'F4_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 0 ] || fail_start ARGUMENTS_REJECTED
case "$0" in /storage/*/Download/F4.sh) ;; *) fail_start INVALID_START_PATH ;; esac
FINDUAS_VOLUME=${0#/storage/}
FINDUAS_VOLUME=${FINDUAS_VOLUME%/Download/F4.sh}
case "$FINDUAS_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) fail_start INVALID_VOLUME_NAME ;;
esac
[ -f "$0" ] && [ ! -L "$0" ] || fail_start SCRIPT_NOT_REGULAR
FINDUAS_SD=/storage/$FINDUAS_VOLUME
for FINDUAS_DIRECTORY in "$FINDUAS_SD" "$FINDUAS_SD/Download" \
    "$FINDUAS_SD/Download/FindUAS" "$FINDUAS_SD/Download/FindUAS/Probe"; do
    [ -d "$FINDUAS_DIRECTORY" ] && [ ! -L "$FINDUAS_DIRECTORY" ] ||
        fail_start REPORT_DIRECTORY_UNAVAILABLE
done
FINDUAS_DATE=$(date -u +%Y%m%dT%H%M%SZ) || fail_start DATE_UNAVAILABLE
case "$FINDUAS_DATE" in ''|*[!0-9TZ]*) fail_start INVALID_DATE ;; esac
FINDUAS_REPORT=$FINDUAS_SD/Download/FindUAS/Probe/FindUAS_F4_${FINDUAS_DATE}_$$.txt
FINDUAS_SOURCE=$FINDUAS_SD/Download/FindUAS_ARTTI_V1.so
FINDUAS_EXPECTED_SHA=9b02f2b3a7e5a8e2afb200bd7d1fae2e75d2753eaa9c7ea86071dd47cccf086a
FINDUAS_CANDIDATE=/data/app/finduas_A040_canary.so

# Each fixed command is captured separately; stderr and exit status are retained.
run_read() {
    FINDUAS_LABEL=$1
    shift
    # The final dot preserves trailing newlines while measuring the byte limit.
    if FINDUAS_CAPTURE=$(
        if "$@" 2>&1; then FINDUAS_CAPTURE_RC=0; else FINDUAS_CAPTURE_RC=$?; fi
        printf '.'
        exit "$FINDUAS_CAPTURE_RC"
    ); then
        FINDUAS_RC=0
    else
        FINDUAS_RC=$?
    fi
    FINDUAS_OUTPUT=${FINDUAS_CAPTURE%.}
    FINDUAS_OUTPUT_BYTES=${#FINDUAS_OUTPUT}
    # Preserve F2's normalized text comparisons (for example stat's numeric value).
    FINDUAS_OUTPUT=$(printf '%s' "$FINDUAS_OUTPUT")
    FINDUAS_TRUNCATED=0
    printf 'BEGIN %s\n' "$FINDUAS_LABEL"
    if [ "$FINDUAS_OUTPUT_BYTES" -gt 4096 ]; then
        FINDUAS_TRUNCATED=1
        printf '%.4096s\noutput_truncated=true\n' "$FINDUAS_OUTPUT"
        FINDUAS_PARTIAL=1
    else
        printf '%s\n' "$FINDUAS_OUTPUT"
    fi
    printf 'command.%s.rc=%s\nEND %s\n' "$FINDUAS_LABEL" "$FINDUAS_RC" "$FINDUAS_LABEL"
    [ "$FINDUAS_RC" -eq 0 ] || FINDUAS_PARTIAL=1
}

timed_read() {
    if [ "$FINDUAS_TIMEOUT_AVAILABLE" -eq 1 ]; then
        FINDUAS_TIMED_LABEL=$1
        shift
        run_read "$FINDUAS_TIMED_LABEL" timeout 3 "$@"
    else
        FINDUAS_OUTPUT=timeout_tool_unavailable
        FINDUAS_RC=127
        FINDUAS_TRUNCATED=0
        FINDUAS_PARTIAL=1
        printf 'BEGIN %s\n%s\ncommand.%s.rc=127\nEND %s\n' "$1" "$FINDUAS_OUTPUT" "$1" "$1"
    fi
}

valid_pid() {
    case "$1" in ''|0*|*[!0-9]*) return 1 ;; esac
}

# Parse a pipe instead of a heredoc: Android mksh must not create a temp file.
# Pipeline-local variables do not alter the collector.
ams_pid_stream() {
    FINDUAS_AMS_HEADER=0
    FINDUAS_AMS_MATCHES=0
    FINDUAS_AMS_PID=
    while IFS= read -r FINDUAS_AMS_LINE || [ -n "$FINDUAS_AMS_LINE" ]; do
        if [ "$FINDUAS_AMS_LINE" = 'ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)' ]; then
            FINDUAS_AMS_HEADER=1
        fi
        set -- $FINDUAS_AMS_LINE
        [ "$#" -gt 0 ] || continue
        case "$1" in
            \#*:) FINDUAS_AMS_INDEX=${1#\#}; FINDUAS_AMS_INDEX=${FINDUAS_AMS_INDEX%:} ;;
            *) continue ;;
        esac
        case "$FINDUAS_AMS_INDEX" in ''|*[!0-9]*) continue ;; esac
        shift
        FINDUAS_AMS_LINE_MATCHES=0
        for FINDUAS_AMS_TOKEN in "$@"; do
            case "$FINDUAS_AMS_TOKEN" in
                *:dji.go.v5/*)
                    FINDUAS_AMS_CANDIDATE=${FINDUAS_AMS_TOKEN%%:*}
                    FINDUAS_AMS_UID=${FINDUAS_AMS_TOKEN#*:dji.go.v5/}
                    valid_pid "$FINDUAS_AMS_CANDIDATE" || continue
                    [ -n "$FINDUAS_AMS_UID" ] || continue
                    [ "$FINDUAS_AMS_TOKEN" = "$FINDUAS_AMS_CANDIDATE:dji.go.v5/$FINDUAS_AMS_UID" ] || continue
                    FINDUAS_AMS_LINE_MATCHES=$((FINDUAS_AMS_LINE_MATCHES + 1))
                    FINDUAS_AMS_PID=$FINDUAS_AMS_CANDIDATE
                    ;;
            esac
        done
        [ "$FINDUAS_AMS_LINE_MATCHES" -le 1 ] || return 1
        if [ "$FINDUAS_AMS_LINE_MATCHES" -eq 1 ]; then
            FINDUAS_AMS_MATCHES=$((FINDUAS_AMS_MATCHES + 1))
        fi
    done
    [ "$FINDUAS_AMS_HEADER" -eq 1 ] && [ "$FINDUAS_AMS_MATCHES" -eq 1 ] || return 1
    valid_pid "$FINDUAS_AMS_PID" || return 1
    printf '%s' "$FINDUAS_AMS_PID"
}

ams_pid() {
    [ "$FINDUAS_RC" -eq 0 ] && [ "$FINDUAS_TRUNCATED" -eq 0 ] || return 1
    [ "$FINDUAS_OUTPUT_BYTES" -le 4096 ] || return 1
    printf '%s\n' "$FINDUAS_OUTPUT" | ams_pid_stream
}

# /proc/PID/stat field 22; comm may contain spaces or parentheses.
starttime() {
    case "$1" in "$FINDUAS_PID ("*") "*) ;; *) return 1 ;; esac
    FINDUAS_STAT_FIELDS=${1##*) }
    set -- $FINDUAS_STAT_FIELDS
    [ "$#" -ge 20 ] || return 1
    shift 19
    case "$1" in ''|*[!0-9]*) return 1 ;; esac
    printf '%s' "$1"
}

collect_report() {
    FINDUAS_PARTIAL=0
    printf 'schema=finduas-rc2-fuli-baseline/v4\nreport_begin=true\n'
    printf 'utc=%s\nprotocol_request_count=0\nattach_count=0\ninternal_copy_count=0\n' "$FINDUAS_DATE"
    printf 'automatic_update_control=NOT_ESTABLISHED\n'
    run_read identity id
    run_read selinux_context id -Z
    run_read selinux_enforcing getenforce
    run_read timeout_tool command -v timeout
    FINDUAS_TIMEOUT_AVAILABLE=0
    [ "$FINDUAS_RC" -ne 0 ] || FINDUAS_TIMEOUT_AVAILABLE=1
    timed_read ro_debuggable getprop ro.debuggable
    timed_read wifi_on settings get global wifi_on
    # pidof remains a recorded diagnostic, never the authority for /proc paths.
    run_read fly_pidof pidof dji.go.v5
    timed_read fly_ams_before dumpsys activity -p dji.go.v5 lru
    FINDUAS_AMS_BEFORE=
    if FINDUAS_AMS_BEFORE=$(ams_pid); then FINDUAS_AMS_BEFORE_RC=0; else
        FINDUAS_AMS_BEFORE_RC=$?
        FINDUAS_PARTIAL=1
    fi
    printf 'ams_before_parse_rc=%s\n' "$FINDUAS_AMS_BEFORE_RC"
    run_read proc_mounts grep ' /proc ' /proc/self/mountinfo
    run_read shell_status sed -n '/^Pid:/p;/^PPid:/p;/^NSpid:/p;/^Uid:/p;/^Gid:/p;/^Groups:/p' "/proc/$$/status"
    FINDUAS_START_BEFORE=
    FINDUAS_START_AFTER=
    # Validate again immediately before constructing a target-owned path.
    if valid_pid "$FINDUAS_AMS_BEFORE"; then
        FINDUAS_PID=$FINDUAS_AMS_BEFORE
        printf 'target_pid=%s\n' "$FINDUAS_PID"
        FINDUAS_PROC=/proc/$FINDUAS_PID
        run_read fly_stat_before cat "$FINDUAS_PROC/stat"
        if [ "$FINDUAS_RC" -eq 0 ]; then
            FINDUAS_START_BEFORE=$(starttime "$FINDUAS_OUTPUT") || FINDUAS_PARTIAL=1
        fi
        run_read fly_context cat "$FINDUAS_PROC/attr/current"
        run_read fly_cmdline od -An -v -tc -N256 "$FINDUAS_PROC/cmdline"
        run_read fly_exe readlink "$FINDUAS_PROC/exe"
        run_read fly_status sed -n '/^Name:/p;/^State:/p;/^Uid:/p;/^Gid:/p;/^Threads:/p;/^TracerPid:/p;/^NoNewPrivs:/p;/^Seccomp:/p' "$FINDUAS_PROC/status"
        run_read fly_stat_after cat "$FINDUAS_PROC/stat"
        if [ "$FINDUAS_RC" -eq 0 ]; then
            FINDUAS_START_AFTER=$(starttime "$FINDUAS_OUTPUT") || FINDUAS_PARTIAL=1
        fi
    else
        printf 'target_state=AMS_UNAVAILABLE_OR_NOT_UNIQUE\n'
        FINDUAS_PARTIAL=1
    fi
    run_read fly_pidof_after pidof dji.go.v5
    # Always take the second AMS observation, including when all /proc reads fail.
    timed_read fly_ams_after dumpsys activity -p dji.go.v5 lru
    FINDUAS_AMS_AFTER=
    if FINDUAS_AMS_AFTER=$(ams_pid); then FINDUAS_AMS_AFTER_RC=0; else
        FINDUAS_AMS_AFTER_RC=$?
        FINDUAS_PARTIAL=1
    fi
    printf 'ams_after_parse_rc=%s\n' "$FINDUAS_AMS_AFTER_RC"
    FINDUAS_AMS_STABLE=unknown
    if [ "$FINDUAS_AMS_BEFORE_RC" -eq 0 ] && [ "$FINDUAS_AMS_AFTER_RC" -eq 0 ]; then
        FINDUAS_AMS_STABLE=false
        [ "$FINDUAS_AMS_BEFORE" != "$FINDUAS_AMS_AFTER" ] || FINDUAS_AMS_STABLE=true
    fi
    printf 'ams_pid_stable=%s\n' "$FINDUAS_AMS_STABLE"
    [ "$FINDUAS_AMS_STABLE" = true ] || FINDUAS_PARTIAL=1
    FINDUAS_PROC_STABLE=unknown
    if [ -n "$FINDUAS_START_BEFORE" ] && [ -n "$FINDUAS_START_AFTER" ]; then
        FINDUAS_PROC_STABLE=false
        [ "$FINDUAS_START_BEFORE" != "$FINDUAS_START_AFTER" ] || FINDUAS_PROC_STABLE=true
    fi
    printf 'proc_starttime_stable=%s\n' "$FINDUAS_PROC_STABLE"
    [ "$FINDUAS_PROC_STABLE" = true ] || FINDUAS_PARTIAL=1
    run_read data_app_entries ls -laZ /data/app
    if [ -e "$FINDUAS_CANDIDATE" ] || [ -L "$FINDUAS_CANDIDATE" ]; then
        printf 'candidate_exists_test=true\n'
        run_read candidate_metadata ls -ldZ "$FINDUAS_CANDIDATE"
    else
        printf 'candidate_exists_test=false\n'
    fi
    run_read canary_metadata ls -ldZ "$FINDUAS_SOURCE"
    FINDUAS_SOURCE_VERIFIED=false
    if [ -f "$FINDUAS_SOURCE" ] && [ ! -L "$FINDUAS_SOURCE" ]; then
        run_read canary_size stat -c %s "$FINDUAS_SOURCE"
        if [ "$FINDUAS_RC" -eq 0 ] && [ "$FINDUAS_OUTPUT" = 4340 ]; then
            timed_read canary_sha256 sha256sum "$FINDUAS_SOURCE"
            if [ "$FINDUAS_RC" -eq 0 ] && [ "${FINDUAS_OUTPUT%% *}" = "$FINDUAS_EXPECTED_SHA" ]; then
                run_read canary_size_after stat -c %s "$FINDUAS_SOURCE"
                if [ "$FINDUAS_RC" -eq 0 ] && [ "$FINDUAS_OUTPUT" = 4340 ]; then
                    FINDUAS_SOURCE_VERIFIED=true
                fi
            fi
        fi
    fi
    printf 'canary_source_verified=%s\n' "$FINDUAS_SOURCE_VERIFIED"
    [ "$FINDUAS_SOURCE_VERIFIED" = true ] || FINDUAS_PARTIAL=1
    FINDUAS_STATE=COMPLETE
    [ "$FINDUAS_PARTIAL" -eq 0 ] || FINDUAS_STATE=INCOMPLETE
    printf 'run_state=%s\nreport_end=true\n' "$FINDUAS_STATE"
    [ "$FINDUAS_PARTIAL" -eq 0 ] || return 10
}

# noclobber protects existing reports; a failed open terminates only this subshell.
(
    umask 077
    set -C
    exec 3>"$FINDUAS_REPORT"
    set +C
    set -e
    collect_report >&3 2>&1
)
FINDUAS_RESULT=$?
case "$FINDUAS_RESULT" in
    0) printf 'F4_SAVED state=COMPLETE\nreport=%s\nF4_END\n' "$FINDUAS_REPORT" ;;
    10) printf 'F4_SAVED state=INCOMPLETE\nreport=%s\nF4_END\n' "$FINDUAS_REPORT" ;;
    *) printf 'F4_ERROR code=REPORT_CREATE_OR_WRITE_FAILED rc=%s\nF4_END\n' "$FINDUAS_RESULT" ;;
esac
exit "$FINDUAS_RESULT"
