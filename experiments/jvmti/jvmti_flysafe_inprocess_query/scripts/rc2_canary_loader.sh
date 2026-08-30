#!/system/bin/sh
# L1: fixed baseline, one named-process ART TI attempt, and owned-file recovery.
PATH=/system/bin
LC_ALL=C
export PATH LC_ALL
set -f
umask 077
L1_SHA=28b96744bef7f4cf3e64911134683ee71a6c950c44a88193fae2fdc7b60b4f4b
L1_SIZE=8372
L1_APK_SHA=fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c
L1_TARGET=/data/app/finduas_A048_identity.so
L1_LF='
'

reject_start() { printf 'L1_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 2 ] || reject_start ARGUMENTS
L1_OP=$1
L1_SID=$2
case "$L1_OP" in CANARY_BASELINE|CANARY_LOAD|CANARY_CLEANUP) ;; *) reject_start OPERATION ;; esac
[ "${#L1_SID}" -eq 16 ] || reject_start SESSION
case "$L1_SID" in *[!0-9a-f]*) reject_start SESSION ;; esac
case "$0" in /storage/*/Download/L1.sh) ;; *) reject_start START_PATH ;; esac
L1_VOLUME=${0#/storage/}
L1_VOLUME=${L1_VOLUME%/Download/L1.sh}
case "$L1_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) reject_start VOLUME ;;
esac
L1_BASE=/storage/$L1_VOLUME/Download
L1_PROBE=$L1_BASE/FindUAS/Probe
L1_SOURCE=$L1_BASE/FindUAS_ARTTI_V2.so
L1_COPY=$L1_PROBE/A048_copy.receipt
L1_ATTEMPT=$L1_PROBE/A048_attach.attempted
[ -d "$L1_PROBE" ] && [ ! -L "$L1_PROBE" ] || reject_start REPORT_DIRECTORY

# Capture a bounded command, retaining its real return code and trailing LF count.
capture() {
    L1_LABEL=$1; L1_SECONDS=$2; L1_LIMIT=$3
    shift 3
    if L1_CAPTURE=$(
        if timeout "$L1_SECONDS" "$@" 2>&1; then L1_STATUS=0; else L1_STATUS=$?; fi
        printf '.'
        exit "$L1_STATUS"
    ); then L1_RC=0; else L1_RC=$?; fi
    L1_OUT=${L1_CAPTURE%.}
    L1_TRUNCATED=0
    printf 'BEGIN %s\n' "$L1_LABEL"
    if [ "${#L1_OUT}" -gt "$L1_LIMIT" ]; then
        printf '%s' "$L1_OUT" | head -c "$L1_LIMIT"
        printf '\noutput_truncated=true\n'
        L1_TRUNCATED=1
    else printf '%s\n' "$L1_OUT"; fi
    printf 'command.%s.rc=%s\nEND %s\n' "$L1_LABEL" "$L1_RC" "$L1_LABEL"
    L1_OUT=$(printf '%s' "$L1_OUT")
}

okay() { [ "$L1_RC" -eq 0 ] && [ "$L1_TRUNCATED" -eq 0 ]; }
check() {
    printf 'check.%s=%s\n' "$1" "$2"
    [ "$2" = true ] || L1_READY=false
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
    L1_HEADER=0; L1_MATCHES=0; L1_VALUE=
    while IFS= read -r L1_LINE || [ -n "$L1_LINE" ]; do
        [ "$L1_LINE" != 'ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)' ] || L1_HEADER=1
        set -- $L1_LINE
        [ "$#" -gt 0 ] || continue
        case "$1" in \#*:) L1_INDEX=${1#\#}; L1_INDEX=${L1_INDEX%:} ;; *) continue ;; esac
        case "$L1_INDEX" in ''|*[!0-9]*) continue ;; esac
        shift
        L1_LINE_MATCHES=0
        for L1_TOKEN in "$@"; do
            case "$L1_TOKEN" in
                *:dji.go.v5/*)
                    L1_VALUE_PID=${L1_TOKEN%%:*}; L1_UID=${L1_TOKEN#*:dji.go.v5/}
                    valid_pid "$L1_VALUE_PID" || continue
                    [ "$L1_TOKEN" = "$L1_VALUE_PID:dji.go.v5/$L1_UID" ] || continue
                    case "$L1_UID" in u0a*) L1_APP_ID=${L1_UID#u0a} ;; *) return 1 ;; esac
                    case "$L1_APP_ID" in ''|*[!0-9]*) return 1 ;; esac
                    case "$L1_APP_ID" in 0) ;; 0*) return 1 ;; esac
                    [ "${#L1_APP_ID}" -le 4 ] || return 1
                    L1_VALUE_UID=$((10000 + L1_APP_ID))
                    L1_LINE_MATCHES=$((L1_LINE_MATCHES + 1)); L1_VALUE=$L1_VALUE_PID ;;
            esac
        done
        [ "$L1_LINE_MATCHES" -le 1 ] || return 1
        L1_MATCHES=$((L1_MATCHES + L1_LINE_MATCHES))
    done
    [ "$L1_HEADER" -eq 1 ] && [ "$L1_MATCHES" -eq 1 ] && valid_pid "$L1_VALUE" || return 1
    printf '%s %s' "$L1_VALUE" "$L1_VALUE_UID"
}
read_ams() {
    capture "$1" 3 4096 dumpsys activity -p dji.go.v5 lru
    L1_AMS=; L1_AMS_UID=
    if okay && L1_PAIR=$(printf '%s\n' "$L1_OUT" | ams_stream); then
        set -- $L1_PAIR
        [ "$#" -eq 2 ] && valid_pid "$1" && valid_app_uid "$2" || return 1
        L1_AMS=$1; L1_AMS_UID=$2
    else return 1; fi
}

write_once() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || return 1
    (set -C; printf '%s' "$2" >"$1")
}
read_record() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    if L1_RECORD=$(
        set -o pipefail || exit 1
        if head -c 513 "$1" | tr '\000' '\001'; then L1_RECORD_RC=0; else L1_RECORD_RC=$?; fi
        printf '.'
        exit "$L1_RECORD_RC"
    ); then :; else return 1; fi
    L1_RECORD=${L1_RECORD%.}
    [ "${#L1_RECORD}" -le 512 ] || return 1
    L1_BAD_BYTE=$(printf '\001')
    case "$L1_RECORD" in *"$L1_BAD_BYTE"*) return 1 ;; esac
}

read_copy() {
    read_record "$L1_COPY" || return 1
    set -- $L1_RECORD
    [ "$#" -eq 9 ] && [ "$1" = L1 ] && [ "$2" = COPY ] && [ "$9" = END ] || return 1
    [ "${#3}" -eq 16 ] || return 1
    case "$3" in *[!0-9a-f]*) return 1 ;; esac
    [ "$L1_OP" = CANARY_CLEANUP ] || [ "$3" = "$L1_SID" ] || return 1
    valid_hash "$6" && [ "$6" = "$L1_SHA" ] && [ "$7" = "$L1_SIZE" ] || return 1
    case "$4" in ''|*[!0-9]*) return 1 ;; esac
    valid_pid "$5" || return 1
    valid_boot "$8" || return 1
    [ "$L1_RECORD" = "L1 COPY $3 $4 $5 $6 $7 $8 END$L1_LF" ] || return 1
    L1_COPY_SID=$3; L1_DEV=$4; L1_INO=$5; L1_COPY_BOOT=$8
}

read_attempt() {
    read_record "$L1_ATTEMPT" || return 1
    set -- $L1_RECORD
    [ "$#" -eq 7 ] && [ "$1" = L1 ] && [ "$2" = ATTEMPT ] && [ "$3" = "$L1_COPY_SID" ] && [ "$7" = END ] || return 1
    valid_pid "$4" && valid_app_uid "$5" && valid_boot "$6" || return 1
    [ "$6" = "$L1_COPY_BOOT" ] || return 1
    [ "$L1_RECORD" = "L1 ATTEMPT $3 $4 $5 $6 END$L1_LF" ] || return 1
    L1_ATTEMPT_PID=$4; L1_ATTEMPT_UID=$5; L1_ATTEMPT_BOOT=$6
}

native_stream() {
    L1_ENTERS=0; L1_RESULTS=0; L1_RESULT_READY=0
    L1_NATIVE_SID=${L1_COPY_SID:-$L1_SID}
    L1_UINT='(0|[1-9][0-9]{0,9})'
    L1_INT='(0|-?[1-9][0-9]{0,9})'
    L1_RESULT_PATTERN="^schema=finduas-artti-identity/v1 phase=result sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} uid=$L1_UINT gid=$L1_UINT abi_bits=32 ready=[01] identity_ok=[01] artti_ok=[01] dispose_ok=[01] context_rc=[0-7] context_errno=$L1_UINT context=[A-Za-z0-9_:,.-]{1,255} stat_rc=[0-7] stat_errno=$L1_UINT starttime=(UNAVAILABLE|[0-9]{1,20}) env_rc=$L1_INT version_called=[01] version_rc=$L1_INT interface_version=0x[0-9a-f]{8} dispose_attempted=[01] dispose_rc=$L1_INT$"
    while IFS= read -r L1_LINE || [ -n "$L1_LINE" ]; do
        case "$L1_LINE" in 'schema=finduas-artti-identity/v1 '*) ;; *) continue ;; esac
        set -- $L1_LINE
        [ "$3" = "sid=$L1_NATIVE_SID" ] && [ "$4" = "pid=$L1_PID" ] || continue
        case "$2" in
            phase=enter)
                [ "$L1_LINE" = "schema=finduas-artti-identity/v1 phase=enter sid=$L1_NATIVE_SID pid=$L1_PID uid=$L1_TARGET_UID gid=$L1_TARGET_UID abi_bits=32" ] || return 1
                [ "$L1_ENTERS" -eq 0 ] && [ "$L1_RESULTS" -eq 0 ] || return 1
                L1_ENTERS=1 ;;
            phase=result)
                [ "$L1_ENTERS" -eq 1 ] && [ "$L1_RESULTS" -eq 0 ] || return 1
                printf '%s\n' "$L1_LINE" | grep -Eq "$L1_RESULT_PATTERN" || return 1
                [ "$#" -eq 23 ] && [ "$5" = "uid=$L1_TARGET_UID" ] && [ "$6" = "gid=$L1_TARGET_UID" ] || return 1
                if [ "${12}" = context_rc=0 ]; then
                    [ "${13}" = context_errno=0 ] && [ "${14}" != context=UNAVAILABLE ] || return 1
                else [ "${14}" = context=UNAVAILABLE ] || return 1; fi
                if [ "${15}" = stat_rc=0 ]; then
                    [ "${16}" = stat_errno=0 ] && [ "${17}" != starttime=UNAVAILABLE ] || return 1
                else [ "${17}" = starttime=UNAVAILABLE ] || return 1; fi
                L1_IDENTITY_OK=0; L1_ARTTI_OK=0; L1_DISPOSE_OK=0; L1_EXPECT_READY=0
                [ "${12}" != context_rc=0 ] || [ "${15}" != stat_rc=0 ] || L1_IDENTITY_OK=1
                [ "${18}" != env_rc=0 ] || [ "${19}" != version_called=1 ] || [ "${20}" != version_rc=0 ] || L1_ARTTI_OK=1
                [ "${22}" != dispose_attempted=1 ] || [ "${23}" != dispose_rc=0 ] || L1_DISPOSE_OK=1
                if [ "${18}" != env_rc=0 ]; then
                    [ "${19}" = version_called=0 ] && [ "${22}" = dispose_attempted=0 ] || return 1
                fi
                [ "${19}" != version_called=0 ] || [ "${20}" = version_rc=-1 ] || return 1
                [ "${22}" != dispose_attempted=0 ] || [ "${23}" = dispose_rc=-1 ] || return 1
                [ "$9" = "identity_ok=$L1_IDENTITY_OK" ] && [ "${10}" = "artti_ok=$L1_ARTTI_OK" ] && [ "${11}" = "dispose_ok=$L1_DISPOSE_OK" ] || return 1
                [ "$L1_IDENTITY_OK:$L1_ARTTI_OK:$L1_DISPOSE_OK" != 1:1:1 ] || L1_EXPECT_READY=1
                [ "$8" = "ready=$L1_EXPECT_READY" ] || return 1
                # The request selector and reported interface version are distinct;
                # preserve the version as evidence and honor the native rc contract.
                L1_RESULTS=1; L1_RESULT_READY=$L1_EXPECT_READY ;;
            *) return 1 ;;
        esac
    done
    [ "$L1_ENTERS:$L1_RESULTS" = 1:1 ] || return 1
    printf '%s' "$L1_RESULT_READY"
}

read_native() {
    # Two canonical records fit this bound; ten failed polls must not grow the
    # outer bridge report past its fixed transport limit.
    capture native_log 3 2048 logcat -d -b main -v raw --pid="$L1_PID" 'FindUAS-ARTTI-Identity:I' '*:S'
    L1_NATIVE_RESULT=false; L1_NATIVE_READY=false
    okay || return 1
    if L1_NATIVE_CHECK=$(set -o pipefail || exit 1; printf '%s\n' "$L1_OUT" | native_stream); then :; else return 1; fi
    L1_NATIVE_RESULT=true
    [ "$L1_NATIVE_CHECK" != 1 ] || L1_NATIVE_READY=true
    return 0
}

network_stream() {
    L1_DEFAULT=0; L1_NETWORK_SECTION=0
    while IFS= read -r L1_LINE || [ -n "$L1_LINE" ]; do
        set -- $L1_LINE
        [ "$#" -gt 0 ] || continue
        case "$*" in
            'Active default network: none')
                [ "$L1_DEFAULT:$L1_NETWORK_SECTION" = 0:0 ] || return 1
                L1_DEFAULT=1 ;;
            'Current Networks:')
                [ "$L1_DEFAULT:$L1_NETWORK_SECTION" = 1:0 ] || return 1
                L1_NETWORK_SECTION=1 ;;
            'Restrict background: true'|'Restrict background: false')
                [ "$L1_NETWORK_SECTION" -eq 1 ] || return 1
                L1_NETWORK_SECTION=2 ;;
            *) return 1 ;;
        esac
    done
    [ "$L1_DEFAULT:$L1_NETWORK_SECTION" = 1:2 ]
}

baseline() {
    L1_READY=true
    capture caller_uid 3 256 id -u
    L1_GOOD=false; okay && [ "$L1_OUT" = 1000 ] && L1_GOOD=true; check caller_uid "$L1_GOOD"
    capture caller_domain 3 256 id -Z
    L1_GOOD=false; okay && [ "$L1_OUT" = u:r:system_app:s0 ] && L1_GOOD=true; check caller_domain "$L1_GOOD"
    capture selinux 3 256 getenforce
    L1_GOOD=false; okay && [ "$L1_OUT" = Permissive ] && L1_GOOD=true; check selinux "$L1_GOOD"
    capture ro_debuggable 3 256 getprop ro.debuggable
    L1_GOOD=false; okay && [ "$L1_OUT" = 1 ] && L1_GOOD=true; check ro_debuggable "$L1_GOOD"
    capture boot_id 3 128 cat /proc/sys/kernel/random/boot_id
    L1_BOOT=$L1_OUT; L1_GOOD=false; okay && valid_boot "$L1_BOOT" && L1_GOOD=true; check boot_id "$L1_GOOD"
    capture wifi_setting 3 256 settings get global wifi_on
    L1_GOOD=false; okay && [ "$L1_OUT" = 0 ] && L1_GOOD=true; check wifi_setting "$L1_GOOD"
    capture wifi_service 3 16384 sh -c 'set -o pipefail; dumpsys wifi | sed -n "1,30p"'
    L1_GOOD=false
    if okay; then case "$L1_OUT" in *'Wi-Fi is disabled'*|*'Wi-Fi is currently disabled'*) L1_GOOD=true ;; esac; fi
    check wifi_service "$L1_GOOD"
    capture connectivity 3 24576 sh -c 'set -o pipefail; dumpsys connectivity | sed -n "/Active default network:/p;/^[[:space:]]*Current Networks:/,/^[[:space:]]*Restrict background:/p"'
    L1_GOOD=false
    if okay && (set -o pipefail; printf '%s\n' "$L1_OUT" | network_stream); then L1_GOOD=true; fi
    check network_isolated "$L1_GOOD"
    for L1_PROP in sys.upgrade.app_self.path persist.dji.upgrade.app_update persist.upgrade.app_self sys.upgrade.app_self; do
        capture "update_$L1_PROP" 3 512 getprop "$L1_PROP"
        L1_GOOD=false
        if okay; then case "$L1_OUT" in ''|0|false) L1_GOOD=true ;; esac; fi
        check "$L1_PROP" "$L1_GOOD"
    done
    capture package_path 3 1024 pm path dji.go.v5
    L1_APK=
    if okay; then case "$L1_OUT" in package:/data/app/*) L1_APK=${L1_OUT#package:} ;; esac; fi
    case "$L1_APK" in ''|*[!a-zA-Z0-9/_.=~-]*|*'/../'*|*'/./'*) L1_APK= ;; esac
    L1_GOOD=false
    if [ -n "$L1_APK" ] && [ -f "$L1_APK" ] && [ ! -L "$L1_APK" ]; then
        capture package_hash 30 1024 sha256sum "$L1_APK"
        okay && [ "${L1_OUT%% *}" = "$L1_APK_SHA" ] && L1_GOOD=true
    fi
    check package_identity "$L1_GOOD"
    L1_GOOD=false; read_ams ams_before && L1_GOOD=true; check ams_before "$L1_GOOD"; L1_PID=$L1_AMS; L1_TARGET_UID=$L1_AMS_UID
    capture parent_metadata 3 512 stat -c '%a:%u:%g' /data/app
    L1_GOOD=false; okay && [ "$L1_OUT" = 771:1000:1000 ] && L1_GOOD=true; check parent_metadata "$L1_GOOD"
    capture parent_label 3 1024 ls -ldZ /data/app
    L1_GOOD=false
    if okay; then case "$L1_OUT" in *' u:object_r:apk_data_file:s0 '*) L1_GOOD=true ;; esac; fi
    check parent_label "$L1_GOOD"
    L1_GOOD=false
    if [ ! -e "$L1_TARGET" ] && [ ! -L "$L1_TARGET" ] && [ ! -e "$L1_COPY" ] && [ ! -L "$L1_COPY" ] && [ ! -e "$L1_ATTEMPT" ] && [ ! -L "$L1_ATTEMPT" ]; then L1_GOOD=true; fi
    check fresh_test_paths "$L1_GOOD"
    capture source_size 3 256 stat -c %s "$L1_SOURCE"
    L1_GOOD=false
    okay && [ "$L1_OUT" = "$L1_SIZE" ] && [ -f "$L1_SOURCE" ] && [ ! -L "$L1_SOURCE" ] && L1_GOOD=true
    check source_size "$L1_GOOD"
    capture source_hash 5 1024 sha256sum "$L1_SOURCE"
    L1_GOOD=false; okay && [ "${L1_OUT%% *}" = "$L1_SHA" ] && L1_GOOD=true; check source_hash "$L1_GOOD"
    capture log_write 3 1024 log -p i -t FindUAS-Loader "schema=finduas-loader-control/v1 sid=$L1_SID phase=baseline"
    L1_GOOD=false; okay && L1_GOOD=true; check log_write "$L1_GOOD"
    capture log_read 3 8192 logcat -d -b main -v raw 'FindUAS-Loader:I' '*:S'
    L1_GOOD=false
    if okay; then case "$L1_OUT" in *"schema=finduas-loader-control/v1 sid=$L1_SID phase=baseline"*) L1_GOOD=true ;; esac; fi
    check log_read "$L1_GOOD"
    if valid_pid "$L1_PID"; then
        capture target_log_control 3 8192 logcat -d -b main,system,crash -v brief --pid="$L1_PID" -t 16
        L1_GOOD=false
        if okay; then case "$L1_OUT" in *"($L1_PID)"*|*"( $L1_PID)"*|*"(  $L1_PID)"*) L1_GOOD=true ;; esac; fi
        check target_log_control "$L1_GOOD"
    fi
    L1_GOOD=false; read_ams ams_after_baseline && [ "$L1_AMS" = "$L1_PID" ] && [ "$L1_AMS_UID" = "$L1_TARGET_UID" ] && L1_GOOD=true; check ams_stable "$L1_GOOD"
    printf 'preflight_ready=%s\ntarget_pid=%s\ntarget_uid=%s\n' "$L1_READY" "$L1_PID" "$L1_TARGET_UID"
    [ "$L1_READY" = true ]
}

owned_file_matches() {
    [ -f "$L1_TARGET" ] && [ ! -L "$L1_TARGET" ] || return 1
    capture target_identity 3 256 stat -c '%d:%i:%a:%u:%g:%s' "$L1_TARGET"
    okay && [ "$L1_OUT" = "$L1_DEV:$L1_INO:644:1000:1000:$L1_SIZE" ] || return 1
    capture target_hash 5 1024 sha256sum "$L1_TARGET"
    okay && [ "${L1_OUT%% *}" = "$L1_SHA" ] || return 1
    capture target_label 3 1024 ls -ldZ "$L1_TARGET"
    okay || return 1
    case "$L1_OUT" in *' u:object_r:apk_data_file:s0 '*) ;; *) return 1 ;; esac
}

copy_file() {
    # Keep the exclusively created output FD open throughout copy and identity capture.
    (
        umask 022
        set -C
        exec 3>"$L1_TARGET" || exit 73
        set +C
        # mksh marks shell-owned descriptors close-on-exec unless redirected on
        # this command. Pass the real exclusive FD to stat, not a PID/path guess.
        L1_META=$(stat -Lc '%d:%i' /proc/self/fd/3 3>&3) || exit 74
        L1_COPY_DEV=${L1_META%%:*}; L1_COPY_INO=${L1_META#*:}
        write_once "$L1_COPY" "L1 COPY $L1_SID $L1_COPY_DEV $L1_COPY_INO $L1_SHA $L1_SIZE $L1_BOOT END$L1_LF" || exit 74
        # A replaced/growing SD source cannot expand this internal copy without bound.
        timeout 5 head -c "$((L1_SIZE + 1))" "$L1_SOURCE" >&3 || exit 74
        exec 3>&- || exit 74
    )
}

cleanup() {
    read_copy || { printf 'cleanup_error=COPY_RECEIPT_UNAVAILABLE\n'; return 73; }
    if [ ! -e "$L1_TARGET" ] && [ ! -L "$L1_TARGET" ]; then
        L1_REMOVED=true; printf 'cleanup_already_absent=true\n'; return 0
    fi
    # An accepted dispatch may still be queued. A native terminal result (or a
    # different boot) closes this narrow loader before its file is removed.
    if [ -e "$L1_ATTEMPT" ] || [ -L "$L1_ATTEMPT" ]; then
        read_attempt || return 73
        capture cleanup_boot 3 128 cat /proc/sys/kernel/random/boot_id
        okay && valid_boot "$L1_OUT" || return 73
        if [ "$L1_OUT" = "$L1_ATTEMPT_BOOT" ]; then
            L1_PID=$L1_ATTEMPT_PID; L1_TARGET_UID=$L1_ATTEMPT_UID
            read_native || { printf 'cleanup_error=NATIVE_COMPLETION_NOT_OBSERVED\n'; return 75; }
        fi
    fi
    # A partial/failed copy is deliberately retained: its creation receipt alone
    # never authorizes deleting bytes that do not match the pinned full payload.
    owned_file_matches || { printf 'cleanup_error=FILE_IDENTITY_CHANGED\n'; return 73; }
    capture remove_test_file 3 1024 rm -- "$L1_TARGET"
    okay && [ ! -e "$L1_TARGET" ] && [ ! -L "$L1_TARGET" ] || return 74
    L1_REMOVED=true
}

load_once() {
    baseline || return 10
    printf 'BEGIN copy_file\n'
    if copy_file 2>&1; then L1_COPY_RC=0; L1_CREATED=true; else L1_COPY_RC=$?; L1_CREATED=unknown; fi
    printf 'command.copy_file.rc=%s\nEND copy_file\n' "$L1_COPY_RC"
    [ "$L1_COPY_RC" -eq 0 ] || return 74
    read_copy && owned_file_matches || return 74
    capture package_before_dispatch 30 1024 sha256sum "$L1_APK"
    if ! okay || [ "${L1_OUT%% *}" != "$L1_APK_SHA" ]; then cleanup; return 10; fi
    L1_GOOD=false; read_ams ams_before_dispatch && [ "$L1_AMS" = "$L1_PID" ] && [ "$L1_AMS_UID" = "$L1_TARGET_UID" ] && L1_GOOD=true
    check dispatch_pid_stable "$L1_GOOD"
    if [ "$L1_GOOD" != true ]; then cleanup; return 10; fi
    write_once "$L1_ATTEMPT" "L1 ATTEMPT $L1_SID $L1_PID $L1_TARGET_UID $L1_BOOT END$L1_LF" || return 73
    read_attempt && [ "$L1_ATTEMPT_PID" = "$L1_PID" ] && [ "$L1_ATTEMPT_UID" = "$L1_TARGET_UID" ] && [ "$L1_ATTEMPT_BOOT" = "$L1_BOOT" ] || return 73
    L1_DISPATCH=1
    capture attach_command 8 4096 cmd activity attach-agent dji.go.v5 "$L1_TARGET=$L1_SID"
    L1_ATTACH_RC=$L1_RC
    # Observe a bounded window; elapsed delay is never a completion signal.
    L1_WINDOW=0
    while [ "$L1_WINDOW" -lt 10 ]; do
        read_native && break
        sleep 1
        L1_WINDOW=$((L1_WINDOW + 1))
    done
    L1_SEEN=$L1_NATIVE_RESULT; L1_NATIVE_OK=$L1_NATIVE_READY
    capture framework_loader_log 3 8192 logcat -d -b main,system,crash -v brief --pid="$L1_PID" -t 64 \
        'ActivityThread:W' 'AndroidRuntime:W' 'art:W' 'linker:W' 'libc:W' '*:S'
    L1_GOOD=false; read_ams ams_after_dispatch && [ "$L1_AMS" = "$L1_PID" ] && [ "$L1_AMS_UID" = "$L1_TARGET_UID" ] && L1_GOOD=true
    printf 'ams_pid_stable_after_attach=%s\nattach_command_rc=%s\n' "$L1_GOOD" "$L1_ATTACH_RC"
    capture final_package_hash 30 1024 sha256sum "$L1_APK"
    L1_PACKAGE_OK=false; okay && [ "${L1_OUT%% *}" = "$L1_APK_SHA" ] && L1_PACKAGE_OK=true
    printf 'package_unchanged=%s\n' "$L1_PACKAGE_OK"
    if [ "$L1_SEEN" = true ]; then cleanup || return 74; else return 75; fi
    [ "$L1_GOOD" = true ] && [ "$L1_PACKAGE_OK" = true ] && [ "$L1_NATIVE_OK" = true ] && [ "$L1_ATTACH_RC" -eq 0 ]
}

L1_DISPATCH=0; L1_CREATED=false; L1_REMOVED=false; L1_SEEN=false
L1_PID=; L1_TARGET_UID=; L1_READY=false; L1_NATIVE_RESULT=false; L1_NATIVE_READY=false
printf 'schema=finduas-rc2-canary-loader/v1\nsid=%s\noperation=%s\nreport_begin=true\n' "$L1_SID" "$L1_OP"
case "$L1_SIZE" in ''|0*|*[!0-9]*) L1_PINNED_SIZE=false ;; *) L1_PINNED_SIZE=true ;; esac
if ! valid_hash "$L1_SHA" || [ "$L1_PINNED_SIZE" != true ] || [ "${#L1_SIZE}" -gt 5 ] || [ "$L1_SIZE" -gt 32768 ]; then
    printf 'loader_error=UNPINNED_CANARY\n'; L1_FINAL_RC=69
else
    case "$L1_OP" in
        CANARY_BASELINE) if baseline; then L1_FINAL_RC=0; else L1_FINAL_RC=10; fi ;;
        CANARY_LOAD) if load_once; then L1_FINAL_RC=0; else L1_FINAL_RC=$?; fi ;;
        CANARY_CLEANUP) if cleanup; then L1_FINAL_RC=0; else L1_FINAL_RC=$?; fi ;;
    esac
fi
printf 'attach_dispatch_count=%s\ntest_file_created=%s\ntest_file_removed=%s\nnative_result_observed=%s\n' \
    "$L1_DISPATCH" "$L1_CREATED" "$L1_REMOVED" "$L1_NATIVE_RESULT"
printf 'report_end=true\n'
exit "$L1_FINAL_RC"
