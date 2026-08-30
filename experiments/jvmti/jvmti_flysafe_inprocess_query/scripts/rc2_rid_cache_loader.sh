#!/system/bin/sh
# L2: fixed baseline, one named-process RID cache read, and owned-file recovery.
PATH=/system/bin
LC_ALL=C
export PATH LC_ALL
set -f
umask 077
L2_SHA=3dea20698eee556706189fd9910705fa60a1d80d0d18ba31a496fa443b38837b
L2_SIZE=14376
L2_APK_SHA=fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c
L2_TARGET=/data/app/finduas_A051_rid_cache.so
L2_LF='
'

reject_start() { printf 'L2_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 2 ] || reject_start ARGUMENTS
L2_OP=$1
L2_SID=$2
case "$L2_OP" in RID_BASELINE|RID_READ|RID_CLEANUP) ;; *) reject_start OPERATION ;; esac
[ "${#L2_SID}" -eq 16 ] || reject_start SESSION
case "$L2_SID" in *[!0-9a-f]*) reject_start SESSION ;; esac
case "$0" in /storage/*/Download/L2.sh) ;; *) reject_start START_PATH ;; esac
L2_VOLUME=${0#/storage/}
L2_VOLUME=${L2_VOLUME%/Download/L2.sh}
case "$L2_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) reject_start VOLUME ;;
esac
L2_BASE=/storage/$L2_VOLUME/Download
L2_PROBE=$L2_BASE/FindUAS/Probe
L2_SOURCE=$L2_BASE/FindUAS_RID_CACHE.so
L2_COPY=$L2_PROBE/A051_copy.receipt
L2_ATTEMPT=$L2_PROBE/A051_attach.attempted
[ -d "$L2_PROBE" ] && [ ! -L "$L2_PROBE" ] || reject_start REPORT_DIRECTORY

# Capture a bounded command, retaining its real return code and trailing LF count.
capture() {
    L2_LABEL=$1; L2_SECONDS=$2; L2_LIMIT=$3
    shift 3
    if L2_CAPTURE=$(
        if timeout "$L2_SECONDS" "$@" 2>&1; then L2_STATUS=0; else L2_STATUS=$?; fi
        printf '.'
        exit "$L2_STATUS"
    ); then L2_RC=0; else L2_RC=$?; fi
    L2_OUT=${L2_CAPTURE%.}
    L2_TRUNCATED=0
    printf 'BEGIN %s\n' "$L2_LABEL"
    if [ "${#L2_OUT}" -gt "$L2_LIMIT" ]; then
        printf '%s' "$L2_OUT" | head -c "$L2_LIMIT"
        printf '\noutput_truncated=true\n'
        L2_TRUNCATED=1
    else printf '%s\n' "$L2_OUT"; fi
    printf 'command.%s.rc=%s\nEND %s\n' "$L2_LABEL" "$L2_RC" "$L2_LABEL"
    L2_OUT=$(printf '%s' "$L2_OUT")
}

okay() { [ "$L2_RC" -eq 0 ] && [ "$L2_TRUNCATED" -eq 0 ]; }
check() {
    printf 'check.%s=%s\n' "$1" "$2"
    [ "$2" = true ] || L2_READY=false
}
valid_pid() { case "$1" in ''|0*|*[!0-9]*) return 1 ;; esac; }
valid_app_uid() { case "$1" in 1[0-9][0-9][0-9][0-9]) ;; *) return 1 ;; esac; }
valid_hash() { [ "${#1}" -eq 64 ] || return 1; case "$1" in *[!0-9a-f]*) return 1 ;; esac; }
valid_boot() {
    [ "${#1}" -eq 36 ] || return 1
    case "$1" in *[!0-9a-f-]*) return 1 ;; esac
    case "$1" in ????????-????-????-????-????????????) ;; *) return 1 ;; esac
}

# The verified F4 grammar: one complete exact-name main-process record and header.
ams_stream() {
    L2_HEADER=0; L2_MATCHES=0; L2_VALUE=
    while IFS= read -r L2_LINE || [ -n "$L2_LINE" ]; do
        [ "$L2_LINE" != 'ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)' ] || L2_HEADER=1
        set -- $L2_LINE
        [ "$#" -gt 0 ] || continue
        case "$1" in \#*:) L2_INDEX=${1#\#}; L2_INDEX=${L2_INDEX%:} ;; *) continue ;; esac
        case "$L2_INDEX" in ''|*[!0-9]*) continue ;; esac
        shift
        L2_LINE_MATCHES=0
        for L2_TOKEN in "$@"; do
            case "$L2_TOKEN" in
                *:dji.go.v5/*)
                    L2_VALUE_PID=${L2_TOKEN%%:*}; L2_UID=${L2_TOKEN#*:dji.go.v5/}
                    valid_pid "$L2_VALUE_PID" || continue
                    [ "$L2_TOKEN" = "$L2_VALUE_PID:dji.go.v5/$L2_UID" ] || continue
                    case "$L2_UID" in u0a*) L2_APP_ID=${L2_UID#u0a} ;; *) return 1 ;; esac
                    case "$L2_APP_ID" in ''|*[!0-9]*) return 1 ;; esac
                    case "$L2_APP_ID" in 0) ;; 0*) return 1 ;; esac
                    [ "${#L2_APP_ID}" -le 4 ] || return 1
                    L2_VALUE_UID=$((10000 + L2_APP_ID))
                    L2_LINE_MATCHES=$((L2_LINE_MATCHES + 1)); L2_VALUE=$L2_VALUE_PID ;;
            esac
        done
        [ "$L2_LINE_MATCHES" -le 1 ] || return 1
        L2_MATCHES=$((L2_MATCHES + L2_LINE_MATCHES))
    done
    [ "$L2_HEADER" -eq 1 ] && [ "$L2_MATCHES" -eq 1 ] && valid_pid "$L2_VALUE" || return 1
    printf '%s %s' "$L2_VALUE" "$L2_VALUE_UID"
}
read_ams() {
    capture "$1" 3 4096 dumpsys activity -p dji.go.v5 lru
    L2_AMS=; L2_AMS_UID=
    if okay && L2_PAIR=$(printf '%s\n' "$L2_OUT" | ams_stream); then
        set -- $L2_PAIR
        [ "$#" -eq 2 ] && valid_pid "$1" && valid_app_uid "$2" || return 1
        L2_AMS=$1; L2_AMS_UID=$2
    else return 1; fi
}

write_once() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || return 1
    (set -C; printf '%s' "$2" >"$1")
}
read_record() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    if L2_RECORD=$(
        set -o pipefail || exit 1
        if head -c 513 "$1" | tr '\000' '\001'; then L2_RECORD_RC=0; else L2_RECORD_RC=$?; fi
        printf '.'
        exit "$L2_RECORD_RC"
    ); then :; else return 1; fi
    L2_RECORD=${L2_RECORD%.}
    [ "${#L2_RECORD}" -le 512 ] || return 1
    L2_BAD_BYTE=$(printf '\001')
    case "$L2_RECORD" in *"$L2_BAD_BYTE"*) return 1 ;; esac
}

read_copy() {
    read_record "$L2_COPY" || return 1
    set -- $L2_RECORD
    [ "$#" -eq 9 ] && [ "$1" = L2 ] && [ "$2" = COPY ] && [ "$9" = END ] || return 1
    [ "${#3}" -eq 16 ] || return 1
    case "$3" in *[!0-9a-f]*) return 1 ;; esac
    [ "$L2_OP" = RID_CLEANUP ] || [ "$3" = "$L2_SID" ] || return 1
    valid_hash "$6" && [ "$6" = "$L2_SHA" ] && [ "$7" = "$L2_SIZE" ] || return 1
    case "$4" in ''|*[!0-9]*) return 1 ;; esac
    valid_pid "$5" || return 1
    valid_boot "$8" || return 1
    [ "$L2_RECORD" = "L2 COPY $3 $4 $5 $6 $7 $8 END$L2_LF" ] || return 1
    L2_COPY_SID=$3; L2_DEV=$4; L2_INO=$5; L2_COPY_BOOT=$8
}

read_attempt() {
    read_record "$L2_ATTEMPT" || return 1
    set -- $L2_RECORD
    [ "$#" -eq 7 ] && [ "$1" = L2 ] && [ "$2" = ATTEMPT ] && [ "$3" = "$L2_COPY_SID" ] && [ "$7" = END ] || return 1
    valid_pid "$4" && valid_app_uid "$5" && valid_boot "$6" || return 1
    [ "$6" = "$L2_COPY_BOOT" ] || return 1
    [ "$L2_RECORD" = "L2 ATTEMPT $3 $4 $5 $6 END$L2_LF" ] || return 1
    L2_ATTEMPT_PID=$4; L2_ATTEMPT_UID=$5; L2_ATTEMPT_BOOT=$6
}

native_stream() {
    L2_ENTERS=0; L2_RESULTS=0; L2_RESULT_READY=0; L2_RESULT_PRESENT=0
    L2_NATIVE_SID=${L2_COPY_SID:-$L2_SID}
    L2_UINT='(0|[1-9][0-9]{0,9})'
    L2_INT='(0|-?[1-9][0-9]{0,9})'
    L2_RESULT_PATTERN="^schema=finduas-rid-cache/v1 phase=result sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} uid=$L2_UINT gid=$L2_UINT abi_bits=32 ready=[01] stage=(0|[1-9]|10|13|14) exception=[01] query_count=[01] value_present=[01] rid_support=(-1|[01]) rid_normal=(-1|[01]) eid_support=(-1|[01]) eid_normal=(-1|[01]) fail_reason=$L2_UINT jni_rc=$L2_INT env_rc=$L2_INT parse_rc=(-1|[0-3]) dispose_attempted=[01] dispose_rc=$L2_INT$"
    while IFS= read -r L2_LINE || [ -n "$L2_LINE" ]; do
        case "$L2_LINE" in 'schema=finduas-rid-cache/v1 '*) ;; *) continue ;; esac
        set -- $L2_LINE
        [ "$3" = "sid=$L2_NATIVE_SID" ] && [ "$4" = "pid=$L2_PID" ] || continue
        case "$2" in
            phase=enter)
                [ "$L2_LINE" = "schema=finduas-rid-cache/v1 phase=enter sid=$L2_NATIVE_SID pid=$L2_PID uid=$L2_TARGET_UID gid=$L2_TARGET_UID abi_bits=32" ] || return 1
                [ "$L2_ENTERS" -eq 0 ] && [ "$L2_RESULTS" -eq 0 ] || return 1
                L2_ENTERS=1 ;;
            phase=result)
                [ "$L2_ENTERS" -eq 1 ] && [ "$L2_RESULTS" -eq 0 ] || return 1
                printf '%s\n' "$L2_LINE" | grep -Eq "$L2_RESULT_PATTERN" || return 1
                [ "$#" -eq 22 ] && [ "$5" = "uid=$L2_TARGET_UID" ] && [ "$6" = "gid=$L2_TARGET_UID" ] || return 1
                [ "$L2_LINE" = "$*" ] || return 1
                [ "${21}" != dispose_attempted=0 ] || [ "${22}" = dispose_rc=-1 ] || return 1
                [ "${11}" != query_count=0 ] || [ "${20}" = parse_rc=-1 ] || return 1
                L2_EXPECT_READY=0
                if [ "$9" = stage=0 ]; then
                    [ "${10}" = exception=0 ] && [ "${11}" = query_count=1 ] &&
                        [ "${18}" = jni_rc=0 ] && [ "${19}" = env_rc=0 ] &&
                        [ "${21}" = dispose_attempted=1 ] && [ "${22}" = dispose_rc=0 ] || return 1
                    case "${20}" in
                        parse_rc=0)
                            [ "${12}" = value_present=1 ] || return 1
                            for L2_FLAG in "${13#rid_support=}" "${14#rid_normal=}" "${15#eid_support=}" "${16#eid_normal=}"; do
                                case "$L2_FLAG" in 0|1) ;; *) return 1 ;; esac
                            done ;;
                        parse_rc=1) [ "${12}" = value_present=0 ] || return 1 ;;
                        *) return 1 ;;
                    esac
                    L2_EXPECT_READY=1
                else [ "${12}" = value_present=0 ] || return 1; fi
                if [ "${12}" = value_present=0 ]; then
                    [ "${13}" = rid_support=-1 ] && [ "${14}" = rid_normal=-1 ] &&
                        [ "${15}" = eid_support=-1 ] && [ "${16}" = eid_normal=-1 ] &&
                        [ "${17}" = fail_reason=0 ] || return 1
                fi
                [ "$8" = "ready=$L2_EXPECT_READY" ] || return 1
                L2_RESULTS=1; L2_RESULT_READY=$L2_EXPECT_READY
                L2_RESULT_PRESENT=${12#value_present=}
                L2_FLAGS="${13#rid_support=} ${14#rid_normal=} ${15#eid_support=} ${16#eid_normal=} ${17#fail_reason=}"
                L2_QUERY_COUNT=${11#query_count=}; L2_STAGE=${9#stage=} ;;
            *) return 1 ;;
        esac
    done
    [ "$L2_ENTERS:$L2_RESULTS" = 1:1 ] || return 1
    printf '%s %s %s %s %s' "$L2_RESULT_READY" "$L2_RESULT_PRESENT" "$L2_QUERY_COUNT" "$L2_STAGE" "$L2_FLAGS"
}

read_native() {
    # Two canonical records fit this bound; polling cannot grow the outer report
    # beyond the fixed transport limit. A null value is terminal, never RID-off.
    capture native_log 3 2048 logcat -d -b main -v raw --pid="$L2_PID" 'FindUAS-RID-Cache:I' '*:S'
    L2_NATIVE_RESULT=false; L2_NATIVE_READY=false
    okay || return 1
    if L2_NATIVE_CHECK=$(set -o pipefail || exit 1; printf '%s\n' "$L2_OUT" | native_stream); then :; else return 1; fi
    set -- $L2_NATIVE_CHECK
    [ "$#" -eq 9 ] || return 1
    L2_NATIVE_RESULT=true
    [ "$1" != 1 ] || L2_NATIVE_READY=true
    L2_NATIVE_PRESENT=$2; L2_NATIVE_QUERIES=$3; L2_NATIVE_STAGE=$4
    L2_RID_SUPPORT=$5; L2_RID_NORMAL=$6; L2_EID_SUPPORT=$7; L2_EID_NORMAL=$8; L2_FAIL_REASON=$9
    return 0
}

network_stream() {
    L2_DEFAULT=0; L2_NETWORK_SECTION=0
    while IFS= read -r L2_LINE || [ -n "$L2_LINE" ]; do
        set -- $L2_LINE
        [ "$#" -gt 0 ] || continue
        case "$*" in
            'Active default network: none')
                [ "$L2_DEFAULT:$L2_NETWORK_SECTION" = 0:0 ] || return 1
                L2_DEFAULT=1 ;;
            'Current Networks:')
                [ "$L2_DEFAULT:$L2_NETWORK_SECTION" = 1:0 ] || return 1
                L2_NETWORK_SECTION=1 ;;
            'Restrict background: true'|'Restrict background: false')
                [ "$L2_NETWORK_SECTION" -eq 1 ] || return 1
                L2_NETWORK_SECTION=2 ;;
            *) return 1 ;;
        esac
    done
    [ "$L2_DEFAULT:$L2_NETWORK_SECTION" = 1:2 ]
}

baseline() {
    L2_READY=true
    capture caller_uid 3 256 id -u
    L2_GOOD=false; okay && [ "$L2_OUT" = 1000 ] && L2_GOOD=true; check caller_uid "$L2_GOOD"
    capture caller_domain 3 256 id -Z
    L2_GOOD=false; okay && [ "$L2_OUT" = u:r:system_app:s0 ] && L2_GOOD=true; check caller_domain "$L2_GOOD"
    capture selinux 3 256 getenforce
    L2_GOOD=false; okay && [ "$L2_OUT" = Permissive ] && L2_GOOD=true; check selinux "$L2_GOOD"
    capture ro_debuggable 3 256 getprop ro.debuggable
    L2_GOOD=false; okay && [ "$L2_OUT" = 1 ] && L2_GOOD=true; check ro_debuggable "$L2_GOOD"
    capture boot_id 3 128 cat /proc/sys/kernel/random/boot_id
    L2_BOOT=$L2_OUT; L2_GOOD=false; okay && valid_boot "$L2_BOOT" && L2_GOOD=true; check boot_id "$L2_GOOD"
    capture wifi_setting 3 256 settings get global wifi_on
    L2_GOOD=false; okay && [ "$L2_OUT" = 0 ] && L2_GOOD=true; check wifi_setting "$L2_GOOD"
    capture wifi_service 3 16384 sh -c 'set -o pipefail; dumpsys wifi | sed -n "1,30p"'
    L2_GOOD=false
    if okay; then case "$L2_OUT" in *'Wi-Fi is disabled'*|*'Wi-Fi is currently disabled'*) L2_GOOD=true ;; esac; fi
    check wifi_service "$L2_GOOD"
    capture connectivity 3 24576 sh -c 'set -o pipefail; dumpsys connectivity | sed -n "/Active default network:/p;/^[[:space:]]*Current Networks:/,/^[[:space:]]*Restrict background:/p"'
    L2_GOOD=false
    if okay && (set -o pipefail; printf '%s\n' "$L2_OUT" | network_stream); then L2_GOOD=true; fi
    check network_isolated "$L2_GOOD"
    for L2_PROP in sys.upgrade.app_self.path persist.dji.upgrade.app_update persist.upgrade.app_self sys.upgrade.app_self; do
        capture "update_$L2_PROP" 3 512 getprop "$L2_PROP"
        L2_GOOD=false
        if okay; then case "$L2_OUT" in ''|0|false) L2_GOOD=true ;; esac; fi
        check "$L2_PROP" "$L2_GOOD"
    done
    capture package_path 3 1024 pm path dji.go.v5
    L2_APK=
    if okay; then case "$L2_OUT" in package:/data/app/*) L2_APK=${L2_OUT#package:} ;; esac; fi
    case "$L2_APK" in ''|*[!a-zA-Z0-9/_.=~-]*|*'/../'*|*'/./'*) L2_APK= ;; esac
    L2_GOOD=false
    if [ -n "$L2_APK" ] && [ -f "$L2_APK" ] && [ ! -L "$L2_APK" ]; then
        capture package_hash 30 1024 sha256sum "$L2_APK"
        okay && [ "${L2_OUT%% *}" = "$L2_APK_SHA" ] && L2_GOOD=true
    fi
    check package_identity "$L2_GOOD"
    L2_GOOD=false; read_ams ams_before && L2_GOOD=true; check ams_before "$L2_GOOD"; L2_PID=$L2_AMS; L2_TARGET_UID=$L2_AMS_UID
    capture parent_metadata 3 512 stat -c '%a:%u:%g' /data/app
    L2_GOOD=false; okay && [ "$L2_OUT" = 771:1000:1000 ] && L2_GOOD=true; check parent_metadata "$L2_GOOD"
    capture parent_label 3 1024 ls -ldZ /data/app
    L2_GOOD=false
    if okay; then case "$L2_OUT" in *' u:object_r:apk_data_file:s0 '*) L2_GOOD=true ;; esac; fi
    check parent_label "$L2_GOOD"
    L2_GOOD=false
    if [ ! -e "$L2_TARGET" ] && [ ! -L "$L2_TARGET" ] && [ ! -e "$L2_COPY" ] && [ ! -L "$L2_COPY" ] && [ ! -e "$L2_ATTEMPT" ] && [ ! -L "$L2_ATTEMPT" ]; then L2_GOOD=true; fi
    check fresh_test_paths "$L2_GOOD"
    capture source_size 3 256 stat -c %s "$L2_SOURCE"
    L2_GOOD=false
    okay && [ "$L2_OUT" = "$L2_SIZE" ] && [ -f "$L2_SOURCE" ] && [ ! -L "$L2_SOURCE" ] && L2_GOOD=true
    check source_size "$L2_GOOD"
    capture source_hash 5 1024 sha256sum "$L2_SOURCE"
    L2_GOOD=false; okay && [ "${L2_OUT%% *}" = "$L2_SHA" ] && L2_GOOD=true; check source_hash "$L2_GOOD"
    capture log_write 3 1024 log -p i -t FindUAS-RID-Loader "schema=finduas-rid-loader-control/v1 sid=$L2_SID phase=baseline"
    L2_GOOD=false; okay && L2_GOOD=true; check log_write "$L2_GOOD"
    capture log_read 3 8192 logcat -d -b main -v raw 'FindUAS-RID-Loader:I' '*:S'
    L2_GOOD=false
    if okay; then case "$L2_OUT" in *"schema=finduas-rid-loader-control/v1 sid=$L2_SID phase=baseline"*) L2_GOOD=true ;; esac; fi
    check log_read "$L2_GOOD"
    if valid_pid "$L2_PID"; then
        capture target_log_control 3 8192 logcat -d -b main,system,crash -v brief --pid="$L2_PID" -t 16
        L2_GOOD=false
        if okay; then case "$L2_OUT" in *"($L2_PID)"*|*"( $L2_PID)"*|*"(  $L2_PID)"*) L2_GOOD=true ;; esac; fi
        check target_log_control "$L2_GOOD"
    fi
    L2_GOOD=false; read_ams ams_after_baseline && [ "$L2_AMS" = "$L2_PID" ] && [ "$L2_AMS_UID" = "$L2_TARGET_UID" ] && L2_GOOD=true; check ams_stable "$L2_GOOD"
    printf 'preflight_ready=%s\ntarget_pid=%s\ntarget_uid=%s\n' "$L2_READY" "$L2_PID" "$L2_TARGET_UID"
    [ "$L2_READY" = true ]
}

owned_file_matches() {
    [ -f "$L2_TARGET" ] && [ ! -L "$L2_TARGET" ] || return 1
    capture target_identity 3 256 stat -c '%d:%i:%a:%u:%g:%s' "$L2_TARGET"
    okay && [ "$L2_OUT" = "$L2_DEV:$L2_INO:644:1000:1000:$L2_SIZE" ] || return 1
    capture target_hash 5 1024 sha256sum "$L2_TARGET"
    okay && [ "${L2_OUT%% *}" = "$L2_SHA" ] || return 1
    capture target_label 3 1024 ls -ldZ "$L2_TARGET"
    okay || return 1
    case "$L2_OUT" in *' u:object_r:apk_data_file:s0 '*) ;; *) return 1 ;; esac
}

copy_file() {
    # Keep the exclusively created output FD open throughout copy and identity capture.
    (
        umask 022
        set -C
        exec 3>"$L2_TARGET" || exit 73
        set +C
        # mksh marks shell-owned descriptors close-on-exec unless redirected on
        # this command. Pass the real exclusive FD to stat, not a PID/path guess.
        L2_META=$(stat -Lc '%d:%i' /proc/self/fd/3 3>&3) || exit 74
        L2_COPY_DEV=${L2_META%%:*}; L2_COPY_INO=${L2_META#*:}
        write_once "$L2_COPY" "L2 COPY $L2_SID $L2_COPY_DEV $L2_COPY_INO $L2_SHA $L2_SIZE $L2_BOOT END$L2_LF" || exit 74
        # A replaced/growing SD source cannot expand this internal copy without bound.
        timeout 5 head -c "$((L2_SIZE + 1))" "$L2_SOURCE" >&3 || exit 74
        exec 3>&- || exit 74
    )
}

cleanup() {
    read_copy || { printf 'cleanup_error=COPY_RECEIPT_UNAVAILABLE\n'; return 73; }
    if [ ! -e "$L2_TARGET" ] && [ ! -L "$L2_TARGET" ]; then
        L2_REMOVED=true; printf 'cleanup_already_absent=true\n'; return 0
    fi
    # An accepted dispatch may still be queued. A native terminal result (or a
    # different boot) closes this narrow loader before its file is removed.
    if [ -e "$L2_ATTEMPT" ] || [ -L "$L2_ATTEMPT" ]; then
        read_attempt || return 73
        capture cleanup_boot 3 128 cat /proc/sys/kernel/random/boot_id
        okay && valid_boot "$L2_OUT" || return 73
        if [ "$L2_OUT" = "$L2_ATTEMPT_BOOT" ]; then
            L2_PID=$L2_ATTEMPT_PID; L2_TARGET_UID=$L2_ATTEMPT_UID
            read_native || { printf 'cleanup_error=NATIVE_COMPLETION_NOT_OBSERVED\n'; return 75; }
        fi
    fi
    # A partial/failed copy is deliberately retained: its creation receipt alone
    # never authorizes deleting bytes that do not match the pinned full payload.
    owned_file_matches || { printf 'cleanup_error=FILE_IDENTITY_CHANGED\n'; return 73; }
    capture remove_test_file 3 1024 rm -- "$L2_TARGET"
    okay && [ ! -e "$L2_TARGET" ] && [ ! -L "$L2_TARGET" ] || return 74
    L2_REMOVED=true
}

load_once() {
    baseline || return 10
    printf 'BEGIN copy_file\n'
    if copy_file 2>&1; then L2_COPY_RC=0; L2_CREATED=true; else L2_COPY_RC=$?; L2_CREATED=unknown; fi
    printf 'command.copy_file.rc=%s\nEND copy_file\n' "$L2_COPY_RC"
    [ "$L2_COPY_RC" -eq 0 ] || return 74
    read_copy && owned_file_matches || return 74
    capture package_before_dispatch 30 1024 sha256sum "$L2_APK"
    if ! okay || [ "${L2_OUT%% *}" != "$L2_APK_SHA" ]; then cleanup; return 10; fi
    L2_GOOD=false; read_ams ams_before_dispatch && [ "$L2_AMS" = "$L2_PID" ] && [ "$L2_AMS_UID" = "$L2_TARGET_UID" ] && L2_GOOD=true
    check dispatch_pid_stable "$L2_GOOD"
    if [ "$L2_GOOD" != true ]; then cleanup; return 10; fi
    write_once "$L2_ATTEMPT" "L2 ATTEMPT $L2_SID $L2_PID $L2_TARGET_UID $L2_BOOT END$L2_LF" || return 73
    read_attempt && [ "$L2_ATTEMPT_PID" = "$L2_PID" ] && [ "$L2_ATTEMPT_UID" = "$L2_TARGET_UID" ] && [ "$L2_ATTEMPT_BOOT" = "$L2_BOOT" ] || return 73
    L2_DISPATCH=1
    capture attach_command 8 4096 cmd activity attach-agent dji.go.v5 "$L2_TARGET=$L2_SID"
    L2_ATTACH_RC=$L2_RC
    # Observe a bounded window; elapsed delay is never a completion signal.
    L2_WINDOW=0
    while [ "$L2_WINDOW" -lt 10 ]; do
        read_native && break
        sleep 1
        L2_WINDOW=$((L2_WINDOW + 1))
    done
    L2_SEEN=$L2_NATIVE_RESULT; L2_NATIVE_OK=$L2_NATIVE_READY
    capture framework_loader_log 3 8192 logcat -d -b main,system,crash -v brief --pid="$L2_PID" -t 64 \
        'ActivityThread:W' 'AndroidRuntime:W' 'art:W' 'linker:W' 'libc:W' '*:S'
    L2_GOOD=false; read_ams ams_after_dispatch && [ "$L2_AMS" = "$L2_PID" ] && [ "$L2_AMS_UID" = "$L2_TARGET_UID" ] && L2_GOOD=true
    printf 'ams_pid_stable_after_attach=%s\nattach_command_rc=%s\n' "$L2_GOOD" "$L2_ATTACH_RC"
    capture final_package_hash 30 1024 sha256sum "$L2_APK"
    L2_PACKAGE_OK=false; okay && [ "${L2_OUT%% *}" = "$L2_APK_SHA" ] && L2_PACKAGE_OK=true
    printf 'package_unchanged=%s\n' "$L2_PACKAGE_OK"
    if [ "$L2_SEEN" = true ]; then cleanup || return 74; else return 75; fi
    [ "$L2_GOOD" = true ] && [ "$L2_PACKAGE_OK" = true ] && [ "$L2_NATIVE_OK" = true ] && [ "$L2_ATTACH_RC" -eq 0 ] || return 1
    [ "$L2_NATIVE_PRESENT" -eq 1 ] || return 10
    L2_CACHE_STATE=VALUE_RECEIVED
}

L2_DISPATCH=0; L2_CREATED=false; L2_REMOVED=false; L2_SEEN=false
L2_PID=; L2_TARGET_UID=; L2_READY=false; L2_NATIVE_RESULT=false; L2_NATIVE_READY=false
L2_NATIVE_PRESENT=0; L2_NATIVE_QUERIES=0; L2_NATIVE_STAGE=-1; L2_CACHE_STATE=UNKNOWN
L2_RID_SUPPORT=-1; L2_RID_NORMAL=-1; L2_EID_SUPPORT=-1; L2_EID_NORMAL=-1; L2_FAIL_REASON=0
printf 'schema=finduas-rc2-rid-cache-loader/v1\nsid=%s\noperation=%s\nreport_begin=true\n' "$L2_SID" "$L2_OP"
case "$L2_SIZE" in ''|0*|*[!0-9]*) L2_PINNED_SIZE=false ;; *) L2_PINNED_SIZE=true ;; esac
if ! valid_hash "$L2_SHA" || [ "$L2_PINNED_SIZE" != true ] || [ "${#L2_SIZE}" -gt 5 ] || [ "$L2_SIZE" -gt 32768 ]; then
    printf 'loader_error=UNPINNED_RID_PROBE\n'; L2_FINAL_RC=69
else
    case "$L2_OP" in
        RID_BASELINE) if baseline; then L2_FINAL_RC=0; else L2_FINAL_RC=10; fi ;;
        RID_READ) if load_once; then L2_FINAL_RC=0; else L2_FINAL_RC=$?; fi ;;
        RID_CLEANUP) if cleanup; then L2_FINAL_RC=0; else L2_FINAL_RC=$?; fi ;;
    esac
fi
printf 'attach_dispatch_count=%s\ntest_file_created=%s\ntest_file_removed=%s\nnative_result_observed=%s\n' \
    "$L2_DISPATCH" "$L2_CREATED" "$L2_REMOVED" "$L2_NATIVE_RESULT"
printf 'rid_cache_state=%s\nnative_value_present=%s\nnative_query_count=%s\nnative_stage=%s\n' \
    "$L2_CACHE_STATE" "$L2_NATIVE_PRESENT" "$L2_NATIVE_QUERIES" "$L2_NATIVE_STAGE"
printf 'rid_support=%s\nrid_normal=%s\neid_support=%s\neid_normal=%s\nfail_reason=%s\n' \
    "$L2_RID_SUPPORT" "$L2_RID_NORMAL" "$L2_EID_SUPPORT" "$L2_EID_NORMAL" "$L2_FAIL_REASON"
printf 'report_end=true\n'
exit "$L2_FINAL_RC"
