#!/system/bin/sh
# Fixed read-only Fuli baseline. Only a new report on the launching SD may be written.
exec 2>&1
PATH=/system/bin
export PATH
LC_ALL=C
export LC_ALL
set -f

fail_start() { printf 'F2_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 0 ] || fail_start ARGUMENTS_REJECTED
case "$0" in /storage/*/Download/F2.sh) ;; *) fail_start INVALID_START_PATH ;; esac
FINDUAS_VOLUME=${0#/storage/}
FINDUAS_VOLUME=${FINDUAS_VOLUME%/Download/F2.sh}
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
FINDUAS_REPORT=$FINDUAS_SD/Download/FindUAS/Probe/FindUAS_F2_${FINDUAS_DATE}_$$.txt
FINDUAS_SOURCE=$FINDUAS_SD/Download/FindUAS_ARTTI_V1.so
FINDUAS_EXPECTED_SHA=9b02f2b3a7e5a8e2afb200bd7d1fae2e75d2753eaa9c7ea86071dd47cccf086a
FINDUAS_CANDIDATE=/data/app/finduas_A040_canary.so

# Each fixed command is captured separately; stderr and exit status are retained.
run_read() {
    FINDUAS_LABEL=$1
    shift
    if FINDUAS_OUTPUT=$("$@" 2>&1); then FINDUAS_RC=0; else FINDUAS_RC=$?; fi
    printf 'BEGIN %s\n' "$FINDUAS_LABEL"
    if [ "${#FINDUAS_OUTPUT}" -gt 4096 ]; then
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
        FINDUAS_PARTIAL=1
        printf 'BEGIN %s\n%s\ncommand.%s.rc=127\nEND %s\n' "$1" "$FINDUAS_OUTPUT" "$1" "$1"
    fi
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
    printf 'schema=finduas-rc2-fuli-baseline/v2\nreport_begin=true\n'
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
    run_read fly_pidof pidof dji.go.v5
    FINDUAS_PID=
    if [ "$FINDUAS_RC" -eq 0 ]; then
        case "$FINDUAS_OUTPUT" in
            ''|*[!0-9\ ]*) ;;
            *) set -- $FINDUAS_OUTPUT; [ "$#" -ne 1 ] || FINDUAS_PID=$1 ;;
        esac
    fi
    if [ -n "$FINDUAS_PID" ] && [ "$FINDUAS_PID" -gt 0 ]; then
        printf 'target_pid=%s\n' "$FINDUAS_PID"
        FINDUAS_PROC=/proc/$FINDUAS_PID
        run_read fly_stat_before cat "$FINDUAS_PROC/stat"
        FINDUAS_START_BEFORE=
        if [ "$FINDUAS_RC" -eq 0 ]; then
            FINDUAS_START_BEFORE=$(starttime "$FINDUAS_OUTPUT") || FINDUAS_PARTIAL=1
        fi
        run_read fly_context cat "$FINDUAS_PROC/attr/current"
        run_read fly_cmdline od -An -v -tc -N256 "$FINDUAS_PROC/cmdline"
        run_read fly_exe readlink "$FINDUAS_PROC/exe"
        run_read fly_status sed -n '/^Name:/p;/^State:/p;/^Uid:/p;/^Gid:/p;/^Threads:/p;/^TracerPid:/p;/^NoNewPrivs:/p;/^Seccomp:/p' "$FINDUAS_PROC/status"
        run_read fly_stat_after cat "$FINDUAS_PROC/stat"
        FINDUAS_START_AFTER=
        if [ "$FINDUAS_RC" -eq 0 ]; then
            FINDUAS_START_AFTER=$(starttime "$FINDUAS_OUTPUT") || FINDUAS_PARTIAL=1
        fi
        run_read fly_pidof_after pidof dji.go.v5
        if [ "$FINDUAS_RC" -eq 0 ] && [ "$FINDUAS_OUTPUT" = "$FINDUAS_PID" ] &&
            [ -n "$FINDUAS_START_BEFORE" ] && [ "$FINDUAS_START_BEFORE" = "$FINDUAS_START_AFTER" ]; then
            printf 'target_pid_starttime_stable=true\n'
        else
            printf 'target_pid_starttime_stable=false\n'
            FINDUAS_PARTIAL=1
        fi
    else
        printf 'target_state=NOT_VISIBLE_OR_NOT_UNIQUE\n'
        FINDUAS_PARTIAL=1
    fi
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
    0) printf 'F2_SAVED state=COMPLETE\nreport=%s\nF2_END\n' "$FINDUAS_REPORT" ;;
    10) printf 'F2_SAVED state=INCOMPLETE\nreport=%s\nF2_END\n' "$FINDUAS_REPORT" ;;
    *) printf 'F2_ERROR code=REPORT_CREATE_OR_WRITE_FAILED rc=%s\nF2_END\n' "$FINDUAS_RESULT" ;;
esac
exit "$FINDUAS_RESULT"
