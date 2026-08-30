#!/system/bin/sh
# L3: fixed baseline, one named-process cloud-policy cache read, and owned-file recovery.
PATH=/system/bin
LC_ALL=C
export PATH LC_ALL
set -f
umask 077
L3_SHA=23c769203a26c6649c95770f50f49676965b06b30d292a302ddb2ce6eba8ea7f
L3_SIZE=22336
L3_APK_SHA=fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c
L3_TARGET=/data/app/finduas_A054_cloud_policy.so
L3_LF='
'

reject_start() { printf 'L3_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 2 ] || reject_start ARGUMENTS
L3_OP=$1
L3_SID=$2
case "$L3_OP" in POLICY_BASELINE|POLICY_READ|POLICY_CLEANUP) ;; *) reject_start OPERATION ;; esac
[ "${#L3_SID}" -eq 16 ] || reject_start SESSION
case "$L3_SID" in *[!0-9a-f]*) reject_start SESSION ;; esac
case "$0" in /storage/*/Download/L3.sh) ;; *) reject_start START_PATH ;; esac
L3_VOLUME=${0#/storage/}
L3_VOLUME=${L3_VOLUME%/Download/L3.sh}
case "$L3_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) reject_start VOLUME ;;
esac
L3_BASE=/storage/$L3_VOLUME/Download
L3_PROBE=$L3_BASE/FindUAS/Probe
L3_SOURCE=$L3_BASE/FindUAS_CLOUD_POLICY.so
L3_COPY=$L3_PROBE/A054_copy.receipt
L3_ATTEMPT=$L3_PROBE/A054_attach.attempted
[ -d "$L3_PROBE" ] && [ ! -L "$L3_PROBE" ] || reject_start REPORT_DIRECTORY

# Capture a bounded command, retaining its real return code and trailing LF count.
capture() {
    L3_LABEL=$1; L3_SECONDS=$2; L3_LIMIT=$3
    shift 3
    if L3_CAPTURE=$(
        if timeout "$L3_SECONDS" "$@" 2>&1; then L3_STATUS=0; else L3_STATUS=$?; fi
        printf '.'
        exit "$L3_STATUS"
    ); then L3_RC=0; else L3_RC=$?; fi
    L3_OUT=${L3_CAPTURE%.}
    L3_TRUNCATED=0
    printf 'BEGIN %s\n' "$L3_LABEL"
    if [ "${#L3_OUT}" -gt "$L3_LIMIT" ]; then
        printf '%s' "$L3_OUT" | head -c "$L3_LIMIT"
        printf '\noutput_truncated=true\n'
        L3_TRUNCATED=1
    else printf '%s\n' "$L3_OUT"; fi
    printf 'command.%s.rc=%s\nEND %s\n' "$L3_LABEL" "$L3_RC" "$L3_LABEL"
    L3_OUT=$(printf '%s' "$L3_OUT")
}

okay() { [ "$L3_RC" -eq 0 ] && [ "$L3_TRUNCATED" -eq 0 ]; }
check() {
    printf 'check.%s=%s\n' "$1" "$2"
    [ "$2" = true ] || L3_READY=false
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
    L3_HEADER=0; L3_MATCHES=0; L3_VALUE=
    while IFS= read -r L3_LINE || [ -n "$L3_LINE" ]; do
        [ "$L3_LINE" != 'ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)' ] || L3_HEADER=1
        set -- $L3_LINE
        [ "$#" -gt 0 ] || continue
        case "$1" in \#*:) L3_INDEX=${1#\#}; L3_INDEX=${L3_INDEX%:} ;; *) continue ;; esac
        case "$L3_INDEX" in ''|*[!0-9]*) continue ;; esac
        shift
        L3_LINE_MATCHES=0
        for L3_TOKEN in "$@"; do
            case "$L3_TOKEN" in
                *:dji.go.v5/*)
                    L3_VALUE_PID=${L3_TOKEN%%:*}; L3_UID=${L3_TOKEN#*:dji.go.v5/}
                    valid_pid "$L3_VALUE_PID" || continue
                    [ "$L3_TOKEN" = "$L3_VALUE_PID:dji.go.v5/$L3_UID" ] || continue
                    case "$L3_UID" in u0a*) L3_APP_ID=${L3_UID#u0a} ;; *) return 1 ;; esac
                    case "$L3_APP_ID" in ''|*[!0-9]*) return 1 ;; esac
                    case "$L3_APP_ID" in 0) ;; 0*) return 1 ;; esac
                    [ "${#L3_APP_ID}" -le 4 ] || return 1
                    L3_VALUE_UID=$((10000 + L3_APP_ID))
                    L3_LINE_MATCHES=$((L3_LINE_MATCHES + 1)); L3_VALUE=$L3_VALUE_PID ;;
            esac
        done
        [ "$L3_LINE_MATCHES" -le 1 ] || return 1
        L3_MATCHES=$((L3_MATCHES + L3_LINE_MATCHES))
    done
    [ "$L3_HEADER" -eq 1 ] && [ "$L3_MATCHES" -eq 1 ] && valid_pid "$L3_VALUE" || return 1
    printf '%s %s' "$L3_VALUE" "$L3_VALUE_UID"
}
read_ams() {
    capture "$1" 3 4096 dumpsys activity -p dji.go.v5 lru
    L3_AMS=; L3_AMS_UID=
    if okay && L3_PAIR=$(printf '%s\n' "$L3_OUT" | ams_stream); then
        set -- $L3_PAIR
        [ "$#" -eq 2 ] && valid_pid "$1" && valid_app_uid "$2" || return 1
        L3_AMS=$1; L3_AMS_UID=$2
    else return 1; fi
}

write_once() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || return 1
    (set -C; printf '%s' "$2" >"$1")
}
read_record() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    if L3_RECORD=$(
        set -o pipefail || exit 1
        if head -c 513 "$1" | tr '\000' '\001'; then L3_RECORD_RC=0; else L3_RECORD_RC=$?; fi
        printf '.'
        exit "$L3_RECORD_RC"
    ); then :; else return 1; fi
    L3_RECORD=${L3_RECORD%.}
    [ "${#L3_RECORD}" -le 512 ] || return 1
    L3_BAD_BYTE=$(printf '\001')
    case "$L3_RECORD" in *"$L3_BAD_BYTE"*) return 1 ;; esac
}

read_copy() {
    read_record "$L3_COPY" || return 1
    set -- $L3_RECORD
    [ "$#" -eq 9 ] && [ "$1" = L3 ] && [ "$2" = COPY ] && [ "$9" = END ] || return 1
    [ "${#3}" -eq 16 ] || return 1
    case "$3" in *[!0-9a-f]*) return 1 ;; esac
    [ "$L3_OP" = POLICY_CLEANUP ] || [ "$3" = "$L3_SID" ] || return 1
    valid_hash "$6" && [ "$6" = "$L3_SHA" ] && [ "$7" = "$L3_SIZE" ] || return 1
    case "$4" in ''|*[!0-9]*) return 1 ;; esac
    valid_pid "$5" || return 1
    valid_boot "$8" || return 1
    [ "$L3_RECORD" = "L3 COPY $3 $4 $5 $6 $7 $8 END$L3_LF" ] || return 1
    L3_COPY_SID=$3; L3_DEV=$4; L3_INO=$5; L3_COPY_BOOT=$8
}

read_attempt() {
    read_record "$L3_ATTEMPT" || return 1
    set -- $L3_RECORD
    [ "$#" -eq 7 ] && [ "$1" = L3 ] && [ "$2" = ATTEMPT ] && [ "$3" = "$L3_COPY_SID" ] && [ "$7" = END ] || return 1
    valid_pid "$4" && valid_app_uid "$5" && valid_boot "$6" || return 1
    [ "$6" = "$L3_COPY_BOOT" ] || return 1
    [ "$L3_RECORD" = "L3 ATTEMPT $3 $4 $5 $6 END$L3_LF" ] || return 1
    L3_ATTEMPT_PID=$4; L3_ATTEMPT_UID=$5; L3_ATTEMPT_BOOT=$6
}

# Native numbers are canonical and bounded before shell arithmetic is used.
bounded_native_number() {
    [ "$1" != -1 ] || return 0
    case "$1" in ''|*[!0-9]*) return 1 ;; 0) ;; 0*) return 1 ;; esac
    [ "${#1}" -le 5 ] && [ "$1" -le "$2" ]
}

native_stream() {
    L3_ENTERS=0; L3_RESULTS=0; L3_RESULT_LINE=
    L3_NATIVE_SID=${L3_COPY_SID:-$L3_SID}
    L3_UINT='(0|[1-9][0-9]{0,9})'
    L3_INT='(0|-?[1-9][0-9]{0,9})'
    L3_MAYBE='(-1|0|[1-9][0-9]{0,4})'
    L3_PRESENT='(-1|[01])'
    L3_RESULT_PATTERN="^schema=finduas-cloud-cache/v1 phase=result sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} uid=$L3_UINT gid=$L3_UINT abi_bits=32 ready=[01] stage=(0|[1-9]|10|13|14) exception=[01] cloud_query_count=[01] product_query_count=[01] mmkv_decode_count=[01] namespace_present=$L3_PRESENT mmkv_present=$L3_PRESENT cloud_present=$L3_PRESENT product_present=$L3_PRESENT product_type=$L3_MAYBE receiver_type=$L3_MAYBE receiver_index=$L3_MAYBE json_rc=(-1|[0-9]|10|11) entry_count=$L3_MAYBE duplicate_count=$L3_MAYBE candidate_count=$L3_MAYBE match_count=$L3_PRESENT default_match=$L3_PRESENT product_blocked_count=$L3_MAYBE jni_rc=$L3_INT env_rc=$L3_INT guard_rc=$L3_MAYBE dispose_attempted=[01] dispose_rc=$L3_INT$"
    while IFS= read -r L3_LINE || [ -n "$L3_LINE" ]; do
        case "$L3_LINE" in 'schema=finduas-cloud-cache/v1 '*) ;; *) continue ;; esac
        set -- $L3_LINE
        [ "$3" = "sid=$L3_NATIVE_SID" ] && [ "$4" = "pid=$L3_PID" ] || continue
        case "$2" in
            phase=enter)
                [ "$L3_LINE" = "schema=finduas-cloud-cache/v1 phase=enter sid=$L3_NATIVE_SID pid=$L3_PID uid=$L3_TARGET_UID gid=$L3_TARGET_UID abi_bits=32" ] || return 1
                [ "$L3_ENTERS:$L3_RESULTS" = 0:0 ] || return 1
                L3_ENTERS=1 ;;
            phase=result)
                [ "$L3_ENTERS:$L3_RESULTS" = 1:0 ] || return 1
                printf '%s\n' "$L3_LINE" | grep -Eq "$L3_RESULT_PATTERN" || return 1
                [ "$#" -eq 32 ] && [ "$5" = "uid=$L3_TARGET_UID" ] && [ "$6" = "gid=$L3_TARGET_UID" ] || return 1
                [ "$L3_LINE" = "$*" ] || return 1
                bounded_native_number "${18#product_type=}" 65535 &&
                    bounded_native_number "${19#receiver_type=}" 255 &&
                    bounded_native_number "${20#receiver_index=}" 255 &&
                    bounded_native_number "${30#guard_rc=}" 15 || return 1
                for L3_NUMBER in "${22#entry_count=}" "${23#duplicate_count=}" "${24#candidate_count=}" "${27#product_blocked_count=}"; do
                    bounded_native_number "$L3_NUMBER" 256 || return 1
                done
                [ "${31}" != dispose_attempted=0 ] || [ "${32}" = dispose_rc=-1 ] || return 1
                L3_EXPECT_READY=0
                if [ "$9" = stage=0 ]; then
                    [ "${10}" = exception=0 ] && [ "${28}" = jni_rc=0 ] && [ "${29}" = env_rc=0 ] &&
                        [ "${31}" = dispose_attempted=1 ] && [ "${32}" = dispose_rc=0 ] || return 1
                    case "${21}" in json_rc=0|json_rc=1|json_rc=9) ;; *) return 1 ;; esac
                    L3_EXPECT_READY=1
                fi
                [ "$8" = "ready=$L3_EXPECT_READY" ] || return 1
                L3_RESULTS=1; L3_RESULT_LINE=$L3_LINE ;;
            *) return 1 ;;
        esac
    done
    [ "$L3_ENTERS:$L3_RESULTS" = 1:1 ] || return 1
    printf '%s' "$L3_RESULT_LINE"
}

read_native() {
    # The complete enter/result pair fits this cap. Missing caches can be terminal
    # and permit owned-file cleanup without becoming an observed policy relation.
    capture native_log 3 2048 logcat -d -b main -v raw --pid="$L3_PID" 'FindUAS-Cloud-Cache:I' '*:S'
    L3_NATIVE_RESULT=false; L3_NATIVE_READY=false; L3_NATIVE_OBSERVED=false
    okay || return 1
    if L3_NATIVE_CHECK=$(set -o pipefail || exit 1; printf '%s\n' "$L3_OUT" | native_stream); then :; else return 1; fi
    set -- $L3_NATIVE_CHECK
    [ "$#" -eq 32 ] || return 1
    L3_NATIVE_RESULT=true
    [ "$8" != ready=1 ] || L3_NATIVE_READY=true
    if [ "$L3_NATIVE_READY" = true ] && [ "${11}" = cloud_query_count=1 ] &&
        [ "${12}" = product_query_count=1 ] && [ "${13}" = mmkv_decode_count=1 ] &&
        [ "${14}" = namespace_present=1 ] && [ "${15}" = mmkv_present=1 ] &&
        [ "${16}" = cloud_present=1 ] && [ "${17}" = product_present=1 ] && [ "${21}" = json_rc=0 ]; then
        L3_NATIVE_OBSERVED=true
        for L3_NUMBER in "${18#product_type=}" "${19#receiver_type=}" "${20#receiver_index=}" \
            "${22#entry_count=}" "${23#duplicate_count=}" "${24#candidate_count=}" \
            "${25#match_count=}" "${26#default_match=}" "${27#product_blocked_count=}"; do
            [ "$L3_NUMBER" -ge 0 ] || L3_NATIVE_OBSERVED=false
        done
    fi
    shift 7
    L3_NATIVE_FIELDS=$*
    return 0
}

network_stream() {
    L3_DEFAULT=0; L3_NETWORK_SECTION=0
    while IFS= read -r L3_LINE || [ -n "$L3_LINE" ]; do
        set -- $L3_LINE
        [ "$#" -gt 0 ] || continue
        case "$*" in
            'Active default network: none')
                [ "$L3_DEFAULT:$L3_NETWORK_SECTION" = 0:0 ] || return 1
                L3_DEFAULT=1 ;;
            'Current Networks:')
                [ "$L3_DEFAULT:$L3_NETWORK_SECTION" = 1:0 ] || return 1
                L3_NETWORK_SECTION=1 ;;
            'Restrict background: true'|'Restrict background: false')
                [ "$L3_NETWORK_SECTION" -eq 1 ] || return 1
                L3_NETWORK_SECTION=2 ;;
            *) return 1 ;;
        esac
    done
    [ "$L3_DEFAULT:$L3_NETWORK_SECTION" = 1:2 ]
}

baseline() {
    L3_READY=true
    capture caller_uid 3 256 id -u
    L3_GOOD=false; okay && [ "$L3_OUT" = 1000 ] && L3_GOOD=true; check caller_uid "$L3_GOOD"
    capture caller_domain 3 256 id -Z
    L3_GOOD=false; okay && [ "$L3_OUT" = u:r:system_app:s0 ] && L3_GOOD=true; check caller_domain "$L3_GOOD"
    capture selinux 3 256 getenforce
    L3_GOOD=false; okay && [ "$L3_OUT" = Permissive ] && L3_GOOD=true; check selinux "$L3_GOOD"
    capture ro_debuggable 3 256 getprop ro.debuggable
    L3_GOOD=false; okay && [ "$L3_OUT" = 1 ] && L3_GOOD=true; check ro_debuggable "$L3_GOOD"
    capture boot_id 3 128 cat /proc/sys/kernel/random/boot_id
    L3_BOOT=$L3_OUT; L3_GOOD=false; okay && valid_boot "$L3_BOOT" && L3_GOOD=true; check boot_id "$L3_GOOD"
    capture wifi_setting 3 256 settings get global wifi_on
    L3_GOOD=false; okay && [ "$L3_OUT" = 0 ] && L3_GOOD=true; check wifi_setting "$L3_GOOD"
    capture wifi_service 3 16384 sh -c 'set -o pipefail; dumpsys wifi | sed -n "1,30p"'
    L3_GOOD=false
    if okay; then case "$L3_OUT" in *'Wi-Fi is disabled'*|*'Wi-Fi is currently disabled'*) L3_GOOD=true ;; esac; fi
    check wifi_service "$L3_GOOD"
    capture connectivity 3 24576 sh -c 'set -o pipefail; dumpsys connectivity | sed -n "/Active default network:/p;/^[[:space:]]*Current Networks:/,/^[[:space:]]*Restrict background:/p"'
    L3_GOOD=false
    if okay && (set -o pipefail; printf '%s\n' "$L3_OUT" | network_stream); then L3_GOOD=true; fi
    check network_isolated "$L3_GOOD"
    for L3_PROP in sys.upgrade.app_self.path persist.dji.upgrade.app_update persist.upgrade.app_self sys.upgrade.app_self; do
        capture "update_$L3_PROP" 3 512 getprop "$L3_PROP"
        L3_GOOD=false
        if okay; then case "$L3_OUT" in ''|0|false) L3_GOOD=true ;; esac; fi
        check "$L3_PROP" "$L3_GOOD"
    done
    capture package_path 3 1024 pm path dji.go.v5
    L3_APK=
    if okay; then case "$L3_OUT" in package:/data/app/*) L3_APK=${L3_OUT#package:} ;; esac; fi
    case "$L3_APK" in ''|*[!a-zA-Z0-9/_.=~-]*|*'/../'*|*'/./'*) L3_APK= ;; esac
    L3_GOOD=false
    if [ -n "$L3_APK" ] && [ -f "$L3_APK" ] && [ ! -L "$L3_APK" ]; then
        capture package_hash 30 1024 sha256sum "$L3_APK"
        okay && [ "${L3_OUT%% *}" = "$L3_APK_SHA" ] && L3_GOOD=true
    fi
    check package_identity "$L3_GOOD"
    L3_GOOD=false; read_ams ams_before && L3_GOOD=true; check ams_before "$L3_GOOD"; L3_PID=$L3_AMS; L3_TARGET_UID=$L3_AMS_UID
    capture parent_metadata 3 512 stat -c '%a:%u:%g' /data/app
    L3_GOOD=false; okay && [ "$L3_OUT" = 771:1000:1000 ] && L3_GOOD=true; check parent_metadata "$L3_GOOD"
    capture parent_label 3 1024 ls -ldZ /data/app
    L3_GOOD=false
    if okay; then case "$L3_OUT" in *' u:object_r:apk_data_file:s0 '*) L3_GOOD=true ;; esac; fi
    check parent_label "$L3_GOOD"
    L3_GOOD=false
    if [ ! -e "$L3_TARGET" ] && [ ! -L "$L3_TARGET" ] && [ ! -e "$L3_COPY" ] && [ ! -L "$L3_COPY" ] && [ ! -e "$L3_ATTEMPT" ] && [ ! -L "$L3_ATTEMPT" ]; then L3_GOOD=true; fi
    check fresh_test_paths "$L3_GOOD"
    capture source_size 3 256 stat -c %s "$L3_SOURCE"
    L3_GOOD=false
    okay && [ "$L3_OUT" = "$L3_SIZE" ] && [ -f "$L3_SOURCE" ] && [ ! -L "$L3_SOURCE" ] && L3_GOOD=true
    check source_size "$L3_GOOD"
    capture source_hash 5 1024 sha256sum "$L3_SOURCE"
    L3_GOOD=false; okay && [ "${L3_OUT%% *}" = "$L3_SHA" ] && L3_GOOD=true; check source_hash "$L3_GOOD"
    capture log_write 3 1024 log -p i -t FindUAS-Policy-Loader "schema=finduas-policy-loader-control/v1 sid=$L3_SID phase=baseline"
    L3_GOOD=false; okay && L3_GOOD=true; check log_write "$L3_GOOD"
    capture log_read 3 8192 logcat -d -b main -v raw 'FindUAS-Policy-Loader:I' '*:S'
    L3_GOOD=false
    if okay; then case "$L3_OUT" in *"schema=finduas-policy-loader-control/v1 sid=$L3_SID phase=baseline"*) L3_GOOD=true ;; esac; fi
    check log_read "$L3_GOOD"
    if valid_pid "$L3_PID"; then
        capture target_log_control 3 8192 logcat -d -b main,system,crash -v brief --pid="$L3_PID" -t 16
        L3_GOOD=false
        if okay; then case "$L3_OUT" in *"($L3_PID)"*|*"( $L3_PID)"*|*"(  $L3_PID)"*) L3_GOOD=true ;; esac; fi
        check target_log_control "$L3_GOOD"
    fi
    L3_GOOD=false; read_ams ams_after_baseline && [ "$L3_AMS" = "$L3_PID" ] && [ "$L3_AMS_UID" = "$L3_TARGET_UID" ] && L3_GOOD=true; check ams_stable "$L3_GOOD"
    printf 'preflight_ready=%s\ntarget_pid=%s\ntarget_uid=%s\n' "$L3_READY" "$L3_PID" "$L3_TARGET_UID"
    [ "$L3_READY" = true ]
}

owned_file_matches() {
    [ -f "$L3_TARGET" ] && [ ! -L "$L3_TARGET" ] || return 1
    capture target_identity 3 256 stat -c '%d:%i:%a:%u:%g:%s' "$L3_TARGET"
    okay && [ "$L3_OUT" = "$L3_DEV:$L3_INO:644:1000:1000:$L3_SIZE" ] || return 1
    capture target_hash 5 1024 sha256sum "$L3_TARGET"
    okay && [ "${L3_OUT%% *}" = "$L3_SHA" ] || return 1
    capture target_label 3 1024 ls -ldZ "$L3_TARGET"
    okay || return 1
    case "$L3_OUT" in *' u:object_r:apk_data_file:s0 '*) ;; *) return 1 ;; esac
}

copy_file() {
    # Keep the exclusively created output FD open throughout copy and identity capture.
    (
        umask 022
        set -C
        exec 3>"$L3_TARGET" || exit 73
        set +C
        # mksh marks shell-owned descriptors close-on-exec unless redirected on
        # this command. Pass the real exclusive FD to stat, not a PID/path guess.
        L3_META=$(stat -Lc '%d:%i' /proc/self/fd/3 3>&3) || exit 74
        L3_COPY_DEV=${L3_META%%:*}; L3_COPY_INO=${L3_META#*:}
        write_once "$L3_COPY" "L3 COPY $L3_SID $L3_COPY_DEV $L3_COPY_INO $L3_SHA $L3_SIZE $L3_BOOT END$L3_LF" || exit 74
        # A replaced/growing SD source cannot expand this internal copy without bound.
        timeout 5 head -c "$((L3_SIZE + 1))" "$L3_SOURCE" >&3 || exit 74
        exec 3>&- || exit 74
    )
}

cleanup() {
    read_copy || { printf 'cleanup_error=COPY_RECEIPT_UNAVAILABLE\n'; return 73; }
    if [ ! -e "$L3_TARGET" ] && [ ! -L "$L3_TARGET" ]; then
        L3_REMOVED=true; printf 'cleanup_already_absent=true\n'; return 0
    fi
    # An accepted dispatch may still be queued. A native terminal result (or a
    # different boot) closes this narrow loader before its file is removed.
    if [ -e "$L3_ATTEMPT" ] || [ -L "$L3_ATTEMPT" ]; then
        read_attempt || return 73
        capture cleanup_boot 3 128 cat /proc/sys/kernel/random/boot_id
        okay && valid_boot "$L3_OUT" || return 73
        if [ "$L3_OUT" = "$L3_ATTEMPT_BOOT" ]; then
            L3_PID=$L3_ATTEMPT_PID; L3_TARGET_UID=$L3_ATTEMPT_UID
            read_native || { printf 'cleanup_error=NATIVE_COMPLETION_NOT_OBSERVED\n'; return 75; }
        fi
    fi
    # A partial/failed copy is deliberately retained: its creation receipt alone
    # never authorizes deleting bytes that do not match the pinned full payload.
    owned_file_matches || { printf 'cleanup_error=FILE_IDENTITY_CHANGED\n'; return 73; }
    capture remove_test_file 3 1024 rm -- "$L3_TARGET"
    okay && [ ! -e "$L3_TARGET" ] && [ ! -L "$L3_TARGET" ] || return 74
    L3_REMOVED=true
}

load_once() {
    baseline || return 10
    printf 'BEGIN copy_file\n'
    if copy_file 2>&1; then L3_COPY_RC=0; L3_CREATED=true; else L3_COPY_RC=$?; L3_CREATED=unknown; fi
    printf 'command.copy_file.rc=%s\nEND copy_file\n' "$L3_COPY_RC"
    [ "$L3_COPY_RC" -eq 0 ] || return 74
    read_copy && owned_file_matches || return 74
    capture package_before_dispatch 30 1024 sha256sum "$L3_APK"
    if ! okay || [ "${L3_OUT%% *}" != "$L3_APK_SHA" ]; then cleanup; return 10; fi
    L3_GOOD=false; read_ams ams_before_dispatch && [ "$L3_AMS" = "$L3_PID" ] && [ "$L3_AMS_UID" = "$L3_TARGET_UID" ] && L3_GOOD=true
    check dispatch_pid_stable "$L3_GOOD"
    if [ "$L3_GOOD" != true ]; then cleanup; return 10; fi
    write_once "$L3_ATTEMPT" "L3 ATTEMPT $L3_SID $L3_PID $L3_TARGET_UID $L3_BOOT END$L3_LF" || return 73
    read_attempt && [ "$L3_ATTEMPT_PID" = "$L3_PID" ] && [ "$L3_ATTEMPT_UID" = "$L3_TARGET_UID" ] && [ "$L3_ATTEMPT_BOOT" = "$L3_BOOT" ] || return 73
    L3_DISPATCH=1
    capture attach_command 8 4096 cmd activity attach-agent dji.go.v5 "$L3_TARGET=$L3_SID"
    L3_ATTACH_RC=$L3_RC
    # Observe a bounded window; elapsed delay is never a completion signal.
    L3_WINDOW=0
    while [ "$L3_WINDOW" -lt 10 ]; do
        read_native && break
        sleep 1
        L3_WINDOW=$((L3_WINDOW + 1))
    done
    L3_SEEN=$L3_NATIVE_RESULT; L3_NATIVE_OK=$L3_NATIVE_READY
    capture framework_loader_log 3 8192 logcat -d -b main,system,crash -v brief --pid="$L3_PID" -t 64 \
        'ActivityThread:W' 'AndroidRuntime:W' 'art:W' 'linker:W' 'libc:W' '*:S'
    L3_GOOD=false; read_ams ams_after_dispatch && [ "$L3_AMS" = "$L3_PID" ] && [ "$L3_AMS_UID" = "$L3_TARGET_UID" ] && L3_GOOD=true
    printf 'ams_pid_stable_after_attach=%s\nattach_command_rc=%s\n' "$L3_GOOD" "$L3_ATTACH_RC"
    capture final_package_hash 30 1024 sha256sum "$L3_APK"
    L3_PACKAGE_OK=false; okay && [ "${L3_OUT%% *}" = "$L3_APK_SHA" ] && L3_PACKAGE_OK=true
    printf 'package_unchanged=%s\n' "$L3_PACKAGE_OK"
    if [ "$L3_SEEN" = true ]; then cleanup || return 74; else return 75; fi
    [ "$L3_GOOD" = true ] && [ "$L3_PACKAGE_OK" = true ] && [ "$L3_NATIVE_OK" = true ] && [ "$L3_ATTACH_RC" -eq 0 ] || return 1
    [ "$L3_NATIVE_OBSERVED" = true ] || return 10
    L3_CACHE_STATE=OBSERVED
}

L3_DISPATCH=0; L3_CREATED=false; L3_REMOVED=false; L3_SEEN=false
L3_PID=; L3_TARGET_UID=; L3_READY=false; L3_NATIVE_RESULT=false; L3_NATIVE_READY=false
L3_NATIVE_OBSERVED=false; L3_NATIVE_FIELDS=; L3_CACHE_STATE=UNKNOWN
printf 'schema=finduas-rc2-cloud-policy-loader/v1\nsid=%s\noperation=%s\nreport_begin=true\n' "$L3_SID" "$L3_OP"
case "$L3_SIZE" in ''|0*|*[!0-9]*) L3_PINNED_SIZE=false ;; *) L3_PINNED_SIZE=true ;; esac
if ! valid_hash "$L3_SHA" || [ "$L3_PINNED_SIZE" != true ] || [ "${#L3_SIZE}" -gt 5 ] || [ "$L3_SIZE" -gt 32768 ]; then
    printf 'loader_error=UNPINNED_POLICY_PROBE\n'; L3_FINAL_RC=69
else
    case "$L3_OP" in
        POLICY_BASELINE) if baseline; then L3_FINAL_RC=0; else L3_FINAL_RC=10; fi ;;
        POLICY_READ) if load_once; then L3_FINAL_RC=0; else L3_FINAL_RC=$?; fi ;;
        POLICY_CLEANUP) if cleanup; then L3_FINAL_RC=0; else L3_FINAL_RC=$?; fi ;;
    esac
fi
printf 'attach_dispatch_count=%s\ntest_file_created=%s\ntest_file_removed=%s\nnative_result_observed=%s\n' \
    "$L3_DISPATCH" "$L3_CREATED" "$L3_REMOVED" "$L3_NATIVE_RESULT"
printf 'policy_cache_state=%s\n' "$L3_CACHE_STATE"
# Only the already validated fixed numeric field list is rendered here.
for L3_FIELD in $L3_NATIVE_FIELDS; do printf 'native_%s\n' "$L3_FIELD"; done
printf 'report_end=true\n'
exit "$L3_FINAL_RC"
