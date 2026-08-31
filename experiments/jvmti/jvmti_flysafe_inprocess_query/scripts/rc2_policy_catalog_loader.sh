#!/system/bin/sh
# L5: one fixed RID policy catalog export and owned-file recovery.
PATH=/system/bin
LC_ALL=C
export PATH LC_ALL
set -f
umask 077
L5_SHA=3c0c5988996e79e4bc8010344b62c5dead48d07471e5d6dac282a6841939c04d
L5_SIZE=26624
L5_APK_SHA=fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c
L5_TARGET=/data/app/finduas_A060_policy_set.so
L5_LF='
'

reject_start() { printf 'L5_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 2 ] || reject_start ARGUMENTS
L5_OP=$1
L5_SID=$2
case "$L5_OP" in CATALOG_BASELINE|CATALOG_READ|CATALOG_CLEANUP) ;; *) reject_start OPERATION ;; esac
[ "${#L5_SID}" -eq 16 ] || reject_start SESSION
case "$L5_SID" in *[!0-9a-f]*) reject_start SESSION ;; esac
case "$0" in /storage/*/Download/L5.sh) ;; *) reject_start START_PATH ;; esac
L5_VOLUME=${0#/storage/}
L5_VOLUME=${L5_VOLUME%/Download/L5.sh}
case "$L5_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) reject_start VOLUME ;;
esac
L5_BASE=/storage/$L5_VOLUME/Download
L5_PROBE=$L5_BASE/FindUAS/Probe
L5_SOURCE=$L5_BASE/FindUAS_POLICY_SET.so
L5_COPY=$L5_PROBE/A060_copy.receipt
L5_ATTEMPT=$L5_PROBE/A060_attach.attempted
[ -d "$L5_PROBE" ] && [ ! -L "$L5_PROBE" ] || reject_start REPORT_DIRECTORY

# Capture a bounded command, retaining its real return code and trailing LF count.
capture() {
    L5_LABEL=$1; L5_SECONDS=$2; L5_LIMIT=$3
    shift 3
    if L5_CAPTURE=$(
        if timeout "$L5_SECONDS" "$@" 2>&1; then L5_STATUS=0; else L5_STATUS=$?; fi
        printf '.'
        exit "$L5_STATUS"
    ); then L5_RC=0; else L5_RC=$?; fi
    L5_OUT=${L5_CAPTURE%.}
    L5_TRUNCATED=0
    printf 'BEGIN %s\n' "$L5_LABEL"
    if [ "${#L5_OUT}" -gt "$L5_LIMIT" ]; then
        printf '%s' "$L5_OUT" | head -c "$L5_LIMIT"
        printf '\noutput_truncated=true\n'
        L5_TRUNCATED=1
    else printf '%s\n' "$L5_OUT"; fi
    printf 'command.%s.rc=%s\nEND %s\n' "$L5_LABEL" "$L5_RC" "$L5_LABEL"
    L5_OUT=$(printf '%s' "$L5_OUT")
}

okay() { [ "$L5_RC" -eq 0 ] && [ "$L5_TRUNCATED" -eq 0 ]; }
check() {
    printf 'check.%s=%s\n' "$1" "$2"
    [ "$2" = true ] || L5_READY=false
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
    L5_HEADER=0; L5_MATCHES=0; L5_VALUE=
    while IFS= read -r L5_LINE || [ -n "$L5_LINE" ]; do
        [ "$L5_LINE" != 'ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)' ] || L5_HEADER=1
        set -- $L5_LINE
        [ "$#" -gt 0 ] || continue
        case "$1" in \#*:) L5_INDEX=${1#\#}; L5_INDEX=${L5_INDEX%:} ;; *) continue ;; esac
        case "$L5_INDEX" in ''|*[!0-9]*) continue ;; esac
        shift
        L5_LINE_MATCHES=0
        for L5_TOKEN in "$@"; do
            case "$L5_TOKEN" in
                *:dji.go.v5/*)
                    L5_VALUE_PID=${L5_TOKEN%%:*}; L5_UID=${L5_TOKEN#*:dji.go.v5/}
                    valid_pid "$L5_VALUE_PID" || continue
                    [ "$L5_TOKEN" = "$L5_VALUE_PID:dji.go.v5/$L5_UID" ] || continue
                    case "$L5_UID" in u0a*) L5_APP_ID=${L5_UID#u0a} ;; *) return 1 ;; esac
                    case "$L5_APP_ID" in ''|*[!0-9]*) return 1 ;; esac
                    case "$L5_APP_ID" in 0) ;; 0*) return 1 ;; esac
                    [ "${#L5_APP_ID}" -le 4 ] || return 1
                    L5_VALUE_UID=$((10000 + L5_APP_ID))
                    L5_LINE_MATCHES=$((L5_LINE_MATCHES + 1)); L5_VALUE=$L5_VALUE_PID ;;
            esac
        done
        [ "$L5_LINE_MATCHES" -le 1 ] || return 1
        L5_MATCHES=$((L5_MATCHES + L5_LINE_MATCHES))
    done
    [ "$L5_HEADER" -eq 1 ] && [ "$L5_MATCHES" -eq 1 ] && valid_pid "$L5_VALUE" || return 1
    printf '%s %s' "$L5_VALUE" "$L5_VALUE_UID"
}
read_ams() {
    capture "$1" 3 4096 dumpsys activity -p dji.go.v5 lru
    L5_AMS=; L5_AMS_UID=
    if okay && L5_PAIR=$(printf '%s\n' "$L5_OUT" | ams_stream); then
        set -- $L5_PAIR
        [ "$#" -eq 2 ] && valid_pid "$1" && valid_app_uid "$2" || return 1
        L5_AMS=$1; L5_AMS_UID=$2
    else return 1; fi
}

write_once() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || return 1
    (set -C; printf '%s' "$2" >"$1")
}
read_record() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    if L5_RECORD=$(
        set -o pipefail || exit 1
        if head -c 513 "$1" | tr '\000' '\001'; then L5_RECORD_RC=0; else L5_RECORD_RC=$?; fi
        printf '.'
        exit "$L5_RECORD_RC"
    ); then :; else return 1; fi
    L5_RECORD=${L5_RECORD%.}
    [ "${#L5_RECORD}" -le 512 ] || return 1
    L5_BAD_BYTE=$(printf '\001')
    case "$L5_RECORD" in *"$L5_BAD_BYTE"*) return 1 ;; esac
}

read_copy() {
    read_record "$L5_COPY" || return 1
    set -- $L5_RECORD
    [ "$#" -eq 9 ] && [ "$1" = L5 ] && [ "$2" = COPY ] && [ "$9" = END ] || return 1
    [ "${#3}" -eq 16 ] || return 1
    case "$3" in *[!0-9a-f]*) return 1 ;; esac
    [ "$L5_OP" = CATALOG_CLEANUP ] || [ "$3" = "$L5_SID" ] || return 1
    valid_hash "$6" && [ "$6" = "$L5_SHA" ] && [ "$7" = "$L5_SIZE" ] || return 1
    case "$4" in ''|*[!0-9]*) return 1 ;; esac
    valid_pid "$5" || return 1
    valid_boot "$8" || return 1
    [ "$L5_RECORD" = "L5 COPY $3 $4 $5 $6 $7 $8 END$L5_LF" ] || return 1
    L5_COPY_SID=$3; L5_DEV=$4; L5_INO=$5; L5_COPY_BOOT=$8
}

read_attempt() {
    read_record "$L5_ATTEMPT" || return 1
    set -- $L5_RECORD
    [ "$#" -eq 7 ] && [ "$1" = L5 ] && [ "$2" = ATTEMPT ] && [ "$3" = "$L5_COPY_SID" ] && [ "$7" = END ] || return 1
    valid_pid "$4" && valid_app_uid "$5" && valid_boot "$6" || return 1
    [ "$6" = "$L5_COPY_BOOT" ] || return 1
    [ "$L5_RECORD" = "L5 ATTEMPT $3 $4 $5 $6 END$L5_LF" ] || return 1
    L5_ATTEMPT_PID=$4; L5_ATTEMPT_UID=$5; L5_ATTEMPT_BOOT=$6
}

# Native numbers are canonical and bounded before shell arithmetic is used.
bounded_native_number() {
    [ "$1" != -1 ] || return 0
    case "$1" in ''|*[!0-9]*) return 1 ;; 0) ;; 0*) return 1 ;; esac
    [ "${#1}" -le 5 ] && [ "$1" -le "$2" ]
}

native_stream() {
    L5_ENTERS=0; L5_EXPORTS=0; L5_RESULTS=0; L5_RESULT_LINE=
    L5_NATIVE_SID=${L5_COPY_SID:-$L5_SID}
    L5_UINT='(0|[1-9][0-9]{0,9})'
    L5_INT='(0|-?[1-9][0-9]{0,9})'
    L5_MAYBE='(-1|0|[1-9][0-9]{0,4})'
    L5_PRESENT='(-1|[01])'
    L5_RESULT_PATTERN="^schema=finduas-policy-set/v1 phase=result sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} uid=$L5_UINT gid=$L5_UINT abi_bits=32 ready=[01] stage=(0|[1-9]|10|13|14) exception=[01] cloud_query_count=0 product_query_count=[01] mmkv_decode_count=[01] namespace_present=$L5_PRESENT mmkv_present=$L5_PRESENT cloud_present=-1 product_present=$L5_PRESENT product_type=$L5_MAYBE receiver_type=-1 receiver_index=-1 json_rc=(-1|[0-9]|10|11) entry_count=$L5_MAYBE duplicate_count=$L5_MAYBE candidate_count=-1 match_count=-1 default_match=-1 product_blocked_count=$L5_MAYBE jni_rc=$L5_INT env_rc=$L5_INT guard_rc=$L5_MAYBE dispose_attempted=[01] dispose_rc=$L5_INT$"
    while IFS= read -r L5_LINE || [ -n "$L5_LINE" ]; do
        case "$L5_LINE" in 'schema=finduas-policy-set/v1 '*) ;; *) continue ;; esac
        set -- $L5_LINE
        [ "$3" = "sid=$L5_NATIVE_SID" ] && [ "$4" = "pid=$L5_PID" ] || continue
        case "$2" in
            phase=enter)
                [ "$L5_LINE" = "schema=finduas-policy-set/v1 phase=enter sid=$L5_NATIVE_SID pid=$L5_PID uid=$L5_TARGET_UID gid=$L5_TARGET_UID abi_bits=32" ] || return 1
                [ "$L5_ENTERS:$L5_RESULTS" = 0:0 ] || return 1
                L5_ENTERS=1 ;;
            phase=export)
                [ "$L5_ENTERS:$L5_EXPORTS:$L5_RESULTS" = 1:0:0 ] || return 1
                [ "$#" -eq 11 ] && [ "$L5_LINE" = "$*" ] || return 1
                printf '%s\n' "$L5_LINE" | grep -Eq "^schema=finduas-policy-set/v1 phase=export sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} export_rc=$L5_MAYBE export_bytes=$L5_MAYBE row_count=$L5_MAYBE nonempty_count=$L5_MAYBE distinct_count=$L5_MAYBE default_present=$L5_PRESENT default_nonempty=$L5_PRESENT$" || return 1
                bounded_native_number "${5#export_rc=}" 999 &&
                    bounded_native_number "${6#export_bytes=}" 32768 &&
                    bounded_native_number "${7#row_count=}" 256 &&
                    bounded_native_number "${8#nonempty_count=}" 256 &&
                    bounded_native_number "${9#distinct_count=}" 256 || return 1
                L5_EXPORTS=1 ;;
            phase=result)
                [ "$L5_ENTERS:$L5_EXPORTS:$L5_RESULTS" = 1:1:0 ] || return 1
                printf '%s\n' "$L5_LINE" | grep -Eq "$L5_RESULT_PATTERN" || return 1
                [ "$#" -eq 32 ] && [ "$5" = "uid=$L5_TARGET_UID" ] && [ "$6" = "gid=$L5_TARGET_UID" ] || return 1
                [ "$L5_LINE" = "$*" ] || return 1
                bounded_native_number "${18#product_type=}" 65535 &&
                    bounded_native_number "${19#receiver_type=}" 255 &&
                    bounded_native_number "${20#receiver_index=}" 255 &&
                    bounded_native_number "${30#guard_rc=}" 15 || return 1
                for L5_NUMBER in "${22#entry_count=}" "${23#duplicate_count=}" "${24#candidate_count=}" "${27#product_blocked_count=}"; do
                    bounded_native_number "$L5_NUMBER" 256 || return 1
                done
                [ "${31}" != dispose_attempted=0 ] || [ "${32}" = dispose_rc=-1 ] || return 1
                L5_EXPECT_READY=0
                if [ "$9" = stage=0 ]; then
                    [ "${10}" = exception=0 ] && [ "${28}" = jni_rc=0 ] && [ "${29}" = env_rc=0 ] &&
                        [ "${31}" = dispose_attempted=1 ] && [ "${32}" = dispose_rc=0 ] || return 1
                    case "${21}" in json_rc=0|json_rc=1|json_rc=9) ;; *) return 1 ;; esac
                    L5_EXPECT_READY=1
                fi
                [ "$8" = "ready=$L5_EXPECT_READY" ] || return 1
                L5_RESULTS=1; L5_RESULT_LINE=$L5_LINE ;;
            *) return 1 ;;
        esac
    done
    [ "$L5_ENTERS:$L5_EXPORTS:$L5_RESULTS" = 1:1:1 ] || return 1
    printf '%s' "$L5_RESULT_LINE"
}

read_native() {
    # The complete enter/result pair fits this cap. Missing caches can be terminal
    # and permit owned-file cleanup without becoming an observed policy relation.
    capture native_log 3 2048 logcat -d -b main -v raw --pid="$L5_PID" 'FindUAS-Policy-Set:I' '*:S'
    L5_NATIVE_RESULT=false; L5_NATIVE_READY=false; L5_NATIVE_OBSERVED=false
    okay || return 1
    if L5_NATIVE_CHECK=$(set -o pipefail || exit 1; printf '%s\n' "$L5_OUT" | native_stream); then :; else return 1; fi
    set -- $L5_NATIVE_CHECK
    [ "$#" -eq 32 ] || return 1
    L5_NATIVE_RESULT=true
    [ "$8" != ready=1 ] || L5_NATIVE_READY=true
    if [ "$L5_NATIVE_READY" = true ] && [ "${11}" = cloud_query_count=0 ] &&
        [ "${12}" = product_query_count=1 ] && [ "${13}" = mmkv_decode_count=1 ] &&
        [ "${14}" = namespace_present=1 ] && [ "${15}" = mmkv_present=1 ] &&
        [ "${16}" = cloud_present=-1 ] && [ "${17}" = product_present=1 ] && [ "${21}" = json_rc=0 ]; then
        L5_NATIVE_OBSERVED=true
        for L5_NUMBER in "${18#product_type=}" "${22#entry_count=}" "${23#duplicate_count=}" "${27#product_blocked_count=}"; do
            [ "$L5_NUMBER" -ge 0 ] || L5_NATIVE_OBSERVED=false
        done
    fi
    shift 7
    L5_NATIVE_FIELDS=$*
    return 0
}

network_stream() {
    L5_DEFAULT=0; L5_NETWORK_SECTION=0
    while IFS= read -r L5_LINE || [ -n "$L5_LINE" ]; do
        set -- $L5_LINE
        [ "$#" -gt 0 ] || continue
        case "$*" in
            'Active default network: none')
                [ "$L5_DEFAULT:$L5_NETWORK_SECTION" = 0:0 ] || return 1
                L5_DEFAULT=1 ;;
            'Current Networks:')
                [ "$L5_DEFAULT:$L5_NETWORK_SECTION" = 1:0 ] || return 1
                L5_NETWORK_SECTION=1 ;;
            'Restrict background: true'|'Restrict background: false')
                [ "$L5_NETWORK_SECTION" -eq 1 ] || return 1
                L5_NETWORK_SECTION=2 ;;
            *) return 1 ;;
        esac
    done
    [ "$L5_DEFAULT:$L5_NETWORK_SECTION" = 1:2 ]
}

baseline() {
    L5_READY=true
    capture caller_uid 3 256 id -u
    L5_GOOD=false; okay && [ "$L5_OUT" = 1000 ] && L5_GOOD=true; check caller_uid "$L5_GOOD"
    capture caller_domain 3 256 id -Z
    L5_GOOD=false; okay && [ "$L5_OUT" = u:r:system_app:s0 ] && L5_GOOD=true; check caller_domain "$L5_GOOD"
    capture selinux 3 256 getenforce
    L5_GOOD=false; okay && [ "$L5_OUT" = Permissive ] && L5_GOOD=true; check selinux "$L5_GOOD"
    capture ro_debuggable 3 256 getprop ro.debuggable
    L5_GOOD=false; okay && [ "$L5_OUT" = 1 ] && L5_GOOD=true; check ro_debuggable "$L5_GOOD"
    capture boot_id 3 128 cat /proc/sys/kernel/random/boot_id
    L5_BOOT=$L5_OUT; L5_GOOD=false; okay && valid_boot "$L5_BOOT" && L5_GOOD=true; check boot_id "$L5_GOOD"
    capture wifi_setting 3 256 settings get global wifi_on
    L5_GOOD=false; okay && [ "$L5_OUT" = 0 ] && L5_GOOD=true; check wifi_setting "$L5_GOOD"
    capture wifi_service 3 16384 sh -c 'set -o pipefail; dumpsys wifi | sed -n "1,30p"'
    L5_GOOD=false
    if okay; then case "$L5_OUT" in *'Wi-Fi is disabled'*|*'Wi-Fi is currently disabled'*) L5_GOOD=true ;; esac; fi
    check wifi_service "$L5_GOOD"
    capture connectivity 3 24576 sh -c 'set -o pipefail; dumpsys connectivity | sed -n "/Active default network:/p;/^[[:space:]]*Current Networks:/,/^[[:space:]]*Restrict background:/p"'
    L5_GOOD=false
    if okay && (set -o pipefail; printf '%s\n' "$L5_OUT" | network_stream); then L5_GOOD=true; fi
    check network_isolated "$L5_GOOD"
    for L5_PROP in sys.upgrade.app_self.path persist.dji.upgrade.app_update persist.upgrade.app_self sys.upgrade.app_self; do
        capture "update_$L5_PROP" 3 512 getprop "$L5_PROP"
        L5_GOOD=false
        if okay; then case "$L5_OUT" in ''|0|false) L5_GOOD=true ;; esac; fi
        check "$L5_PROP" "$L5_GOOD"
    done
    capture package_path 3 1024 pm path dji.go.v5
    L5_APK=
    if okay; then case "$L5_OUT" in package:/data/app/*) L5_APK=${L5_OUT#package:} ;; esac; fi
    case "$L5_APK" in ''|*[!a-zA-Z0-9/_.=~-]*|*'/../'*|*'/./'*) L5_APK= ;; esac
    L5_GOOD=false
    if [ -n "$L5_APK" ] && [ -f "$L5_APK" ] && [ ! -L "$L5_APK" ]; then
        capture package_hash 30 1024 sha256sum "$L5_APK"
        okay && [ "${L5_OUT%% *}" = "$L5_APK_SHA" ] && L5_GOOD=true
    fi
    check package_identity "$L5_GOOD"
    L5_GOOD=false; read_ams ams_before && L5_GOOD=true; check ams_before "$L5_GOOD"; L5_PID=$L5_AMS; L5_TARGET_UID=$L5_AMS_UID
    capture parent_metadata 3 512 stat -c '%a:%u:%g' /data/app
    L5_GOOD=false; okay && [ "$L5_OUT" = 771:1000:1000 ] && L5_GOOD=true; check parent_metadata "$L5_GOOD"
    capture parent_label 3 1024 ls -ldZ /data/app
    L5_GOOD=false
    if okay; then case "$L5_OUT" in *' u:object_r:apk_data_file:s0 '*) L5_GOOD=true ;; esac; fi
    check parent_label "$L5_GOOD"
    L5_GOOD=false
    if [ ! -e "$L5_TARGET" ] && [ ! -L "$L5_TARGET" ] && [ ! -e "$L5_COPY" ] && [ ! -L "$L5_COPY" ] && [ ! -e "$L5_ATTEMPT" ] && [ ! -L "$L5_ATTEMPT" ]; then L5_GOOD=true; fi
    check fresh_test_paths "$L5_GOOD"
    capture source_size 3 256 stat -c %s "$L5_SOURCE"
    L5_GOOD=false
    okay && [ "$L5_OUT" = "$L5_SIZE" ] && [ -f "$L5_SOURCE" ] && [ ! -L "$L5_SOURCE" ] && L5_GOOD=true
    check source_size "$L5_GOOD"
    capture source_hash 5 1024 sha256sum "$L5_SOURCE"
    L5_GOOD=false; okay && [ "${L5_OUT%% *}" = "$L5_SHA" ] && L5_GOOD=true; check source_hash "$L5_GOOD"
    capture log_write 3 1024 log -p i -t FindUAS-Catalog-Loader "schema=finduas-policy-loader-control/v1 sid=$L5_SID phase=baseline"
    L5_GOOD=false; okay && L5_GOOD=true; check log_write "$L5_GOOD"
    capture log_read 3 8192 logcat -d -b main -v raw 'FindUAS-Catalog-Loader:I' '*:S'
    L5_GOOD=false
    if okay; then case "$L5_OUT" in *"schema=finduas-policy-loader-control/v1 sid=$L5_SID phase=baseline"*) L5_GOOD=true ;; esac; fi
    check log_read "$L5_GOOD"
    if valid_pid "$L5_PID"; then
        capture target_log_control 3 8192 logcat -d -b main,system,crash -v brief --pid="$L5_PID" -t 16
        L5_GOOD=false
        if okay; then case "$L5_OUT" in *"($L5_PID)"*|*"( $L5_PID)"*|*"(  $L5_PID)"*) L5_GOOD=true ;; esac; fi
        check target_log_control "$L5_GOOD"
    fi
    L5_GOOD=false; read_ams ams_after_baseline && [ "$L5_AMS" = "$L5_PID" ] && [ "$L5_AMS_UID" = "$L5_TARGET_UID" ] && L5_GOOD=true; check ams_stable "$L5_GOOD"
    printf 'preflight_ready=%s\ntarget_pid=%s\ntarget_uid=%s\n' "$L5_READY" "$L5_PID" "$L5_TARGET_UID"
    [ "$L5_READY" = true ]
}

owned_file_matches() {
    [ -f "$L5_TARGET" ] && [ ! -L "$L5_TARGET" ] || return 1
    capture target_identity 3 256 stat -c '%d:%i:%a:%u:%g:%s' "$L5_TARGET"
    okay && [ "$L5_OUT" = "$L5_DEV:$L5_INO:644:1000:1000:$L5_SIZE" ] || return 1
    capture target_hash 5 1024 sha256sum "$L5_TARGET"
    okay && [ "${L5_OUT%% *}" = "$L5_SHA" ] || return 1
    capture target_label 3 1024 ls -ldZ "$L5_TARGET"
    okay || return 1
    case "$L5_OUT" in *' u:object_r:apk_data_file:s0 '*) ;; *) return 1 ;; esac
}

copy_file() {
    # Keep the exclusively created output FD open throughout copy and identity capture.
    (
        umask 022
        set -C
        exec 3>"$L5_TARGET" || exit 73
        set +C
        # mksh marks shell-owned descriptors close-on-exec unless redirected on
        # this command. Pass the real exclusive FD to stat, not a PID/path guess.
        L5_META=$(stat -Lc '%d:%i' /proc/self/fd/3 3>&3) || exit 74
        L5_COPY_DEV=${L5_META%%:*}; L5_COPY_INO=${L5_META#*:}
        write_once "$L5_COPY" "L5 COPY $L5_SID $L5_COPY_DEV $L5_COPY_INO $L5_SHA $L5_SIZE $L5_BOOT END$L5_LF" || exit 74
        # A replaced/growing SD source cannot expand this internal copy without bound.
        timeout 5 head -c "$((L5_SIZE + 1))" "$L5_SOURCE" >&3 || exit 74
        exec 3>&- || exit 74
    )
}

cleanup() {
    read_copy || { printf 'cleanup_error=COPY_RECEIPT_UNAVAILABLE\n'; return 73; }
    if [ ! -e "$L5_TARGET" ] && [ ! -L "$L5_TARGET" ]; then
        L5_REMOVED=true; printf 'cleanup_already_absent=true\n'; return 0
    fi
    # An accepted dispatch may still be queued. A native terminal result (or a
    # different boot) closes this narrow loader before its file is removed.
    if [ -e "$L5_ATTEMPT" ] || [ -L "$L5_ATTEMPT" ]; then
        read_attempt || return 73
        capture cleanup_boot 3 128 cat /proc/sys/kernel/random/boot_id
        okay && valid_boot "$L5_OUT" || return 73
        if [ "$L5_OUT" = "$L5_ATTEMPT_BOOT" ]; then
            L5_PID=$L5_ATTEMPT_PID; L5_TARGET_UID=$L5_ATTEMPT_UID
            read_native || { printf 'cleanup_error=NATIVE_COMPLETION_NOT_OBSERVED\n'; return 75; }
        fi
    fi
    # A partial/failed copy is deliberately retained: its creation receipt alone
    # never authorizes deleting bytes that do not match the pinned full payload.
    owned_file_matches || { printf 'cleanup_error=FILE_IDENTITY_CHANGED\n'; return 73; }
    capture remove_test_file 3 1024 rm -- "$L5_TARGET"
    okay && [ ! -e "$L5_TARGET" ] && [ ! -L "$L5_TARGET" ] || return 74
    L5_REMOVED=true
}

load_once() {
    baseline || return 10
    printf 'BEGIN copy_file\n'
    if copy_file 2>&1; then L5_COPY_RC=0; L5_CREATED=true; else L5_COPY_RC=$?; L5_CREATED=unknown; fi
    printf 'command.copy_file.rc=%s\nEND copy_file\n' "$L5_COPY_RC"
    [ "$L5_COPY_RC" -eq 0 ] || return 74
    read_copy && owned_file_matches || return 74
    capture package_before_dispatch 30 1024 sha256sum "$L5_APK"
    if ! okay || [ "${L5_OUT%% *}" != "$L5_APK_SHA" ]; then cleanup; return 10; fi
    L5_GOOD=false; read_ams ams_before_dispatch && [ "$L5_AMS" = "$L5_PID" ] && [ "$L5_AMS_UID" = "$L5_TARGET_UID" ] && L5_GOOD=true
    check dispatch_pid_stable "$L5_GOOD"
    if [ "$L5_GOOD" != true ]; then cleanup; return 10; fi
    write_once "$L5_ATTEMPT" "L5 ATTEMPT $L5_SID $L5_PID $L5_TARGET_UID $L5_BOOT END$L5_LF" || return 73
    read_attempt && [ "$L5_ATTEMPT_PID" = "$L5_PID" ] && [ "$L5_ATTEMPT_UID" = "$L5_TARGET_UID" ] && [ "$L5_ATTEMPT_BOOT" = "$L5_BOOT" ] || return 73
    L5_DISPATCH=1
    capture attach_command 8 4096 cmd activity attach-agent dji.go.v5 "$L5_TARGET=$L5_SID"
    L5_ATTACH_RC=$L5_RC
    # Observe a bounded window; elapsed delay is never a completion signal.
    L5_WINDOW=0
    while [ "$L5_WINDOW" -lt 10 ]; do
        read_native && break
        sleep 1
        L5_WINDOW=$((L5_WINDOW + 1))
    done
    L5_SEEN=$L5_NATIVE_RESULT; L5_NATIVE_OK=$L5_NATIVE_READY
    capture framework_loader_log 3 8192 logcat -d -b main,system,crash -v brief --pid="$L5_PID" -t 64 \
        'ActivityThread:W' 'AndroidRuntime:W' 'art:W' 'linker:W' 'libc:W' '*:S'
    L5_GOOD=false; read_ams ams_after_dispatch && [ "$L5_AMS" = "$L5_PID" ] && [ "$L5_AMS_UID" = "$L5_TARGET_UID" ] && L5_GOOD=true
    printf 'ams_pid_stable_after_attach=%s\nattach_command_rc=%s\n' "$L5_GOOD" "$L5_ATTACH_RC"
    capture final_package_hash 30 1024 sha256sum "$L5_APK"
    L5_PACKAGE_OK=false; okay && [ "${L5_OUT%% *}" = "$L5_APK_SHA" ] && L5_PACKAGE_OK=true
    printf 'package_unchanged=%s\n' "$L5_PACKAGE_OK"
    if [ "$L5_SEEN" = true ]; then cleanup || return 74; else return 75; fi
    [ "$L5_GOOD" = true ] && [ "$L5_PACKAGE_OK" = true ] && [ "$L5_NATIVE_OK" = true ] && [ "$L5_ATTACH_RC" -eq 0 ] || return 1
    [ "$L5_NATIVE_OBSERVED" = true ] || return 10
    L5_CACHE_STATE=OBSERVED
}

L5_DISPATCH=0; L5_CREATED=false; L5_REMOVED=false; L5_SEEN=false
L5_PID=; L5_TARGET_UID=; L5_READY=false; L5_NATIVE_RESULT=false; L5_NATIVE_READY=false
L5_NATIVE_OBSERVED=false; L5_NATIVE_FIELDS=; L5_CACHE_STATE=UNKNOWN
printf 'schema=finduas-rc2-policy-catalog-loader/v1\nsid=%s\noperation=%s\nreport_begin=true\n' "$L5_SID" "$L5_OP"
case "$L5_SIZE" in ''|0*|*[!0-9]*) L5_PINNED_SIZE=false ;; *) L5_PINNED_SIZE=true ;; esac
if ! valid_hash "$L5_SHA" || [ "$L5_PINNED_SIZE" != true ] || [ "${#L5_SIZE}" -gt 5 ] || [ "$L5_SIZE" -gt 32768 ]; then
    printf 'loader_error=UNPINNED_CATALOG_PROBE\n'; L5_FINAL_RC=69
else
    case "$L5_OP" in
        CATALOG_BASELINE) if baseline; then L5_FINAL_RC=0; else L5_FINAL_RC=10; fi ;;
        CATALOG_READ) if load_once; then L5_FINAL_RC=0; else L5_FINAL_RC=$?; fi ;;
        CATALOG_CLEANUP) if cleanup; then L5_FINAL_RC=0; else L5_FINAL_RC=$?; fi ;;
    esac
fi
printf 'attach_dispatch_count=%s\ntest_file_created=%s\ntest_file_removed=%s\nnative_result_observed=%s\n' \
    "$L5_DISPATCH" "$L5_CREATED" "$L5_REMOVED" "$L5_NATIVE_RESULT"
printf 'policy_catalog_state=%s\n' "$L5_CACHE_STATE"
# Only the already validated fixed numeric field list is rendered here.
for L5_FIELD in $L5_NATIVE_FIELDS; do printf 'native_%s\n' "$L5_FIELD"; done
printf 'report_end=true\n'
exit "$L5_FINAL_RC"
