#!/system/bin/sh
# L4: one matched-policy/DEFAULT private export and owned-file recovery.
PATH=/system/bin
LC_ALL=C
export PATH LC_ALL
set -f
umask 077
L4_SHA=3b62094ac76515277bf251c59ecac0e2cca761aab92c60d925e4daa0bb16112e
L4_SIZE=27072
L4_APK_SHA=fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c
L4_TARGET=/data/app/finduas_A057_policy_structure.so
L4_LF='
'

reject_start() { printf 'L4_ERROR code=%s\n' "$1"; exit 64; }
[ "$#" -eq 2 ] || reject_start ARGUMENTS
L4_OP=$1
L4_SID=$2
case "$L4_OP" in STRUCTURE_BASELINE|STRUCTURE_READ|STRUCTURE_CLEANUP) ;; *) reject_start OPERATION ;; esac
[ "${#L4_SID}" -eq 16 ] || reject_start SESSION
case "$L4_SID" in *[!0-9a-f]*) reject_start SESSION ;; esac
case "$0" in /storage/*/Download/L4.sh) ;; *) reject_start START_PATH ;; esac
L4_VOLUME=${0#/storage/}
L4_VOLUME=${L4_VOLUME%/Download/L4.sh}
case "$L4_VOLUME" in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
    *) reject_start VOLUME ;;
esac
L4_BASE=/storage/$L4_VOLUME/Download
L4_PROBE=$L4_BASE/FindUAS/Probe
L4_SOURCE=$L4_BASE/FindUAS_POLICY_STRUCTURE.so
L4_COPY=$L4_PROBE/A057_copy.receipt
L4_ATTEMPT=$L4_PROBE/A057_attach.attempted
[ -d "$L4_PROBE" ] && [ ! -L "$L4_PROBE" ] || reject_start REPORT_DIRECTORY

# Capture a bounded command, retaining its real return code and trailing LF count.
capture() {
    L4_LABEL=$1; L4_SECONDS=$2; L4_LIMIT=$3
    shift 3
    if L4_CAPTURE=$(
        if timeout "$L4_SECONDS" "$@" 2>&1; then L4_STATUS=0; else L4_STATUS=$?; fi
        printf '.'
        exit "$L4_STATUS"
    ); then L4_RC=0; else L4_RC=$?; fi
    L4_OUT=${L4_CAPTURE%.}
    L4_TRUNCATED=0
    printf 'BEGIN %s\n' "$L4_LABEL"
    if [ "${#L4_OUT}" -gt "$L4_LIMIT" ]; then
        printf '%s' "$L4_OUT" | head -c "$L4_LIMIT"
        printf '\noutput_truncated=true\n'
        L4_TRUNCATED=1
    else printf '%s\n' "$L4_OUT"; fi
    printf 'command.%s.rc=%s\nEND %s\n' "$L4_LABEL" "$L4_RC" "$L4_LABEL"
    L4_OUT=$(printf '%s' "$L4_OUT")
}

okay() { [ "$L4_RC" -eq 0 ] && [ "$L4_TRUNCATED" -eq 0 ]; }
check() {
    printf 'check.%s=%s\n' "$1" "$2"
    [ "$2" = true ] || L4_READY=false
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
    L4_HEADER=0; L4_MATCHES=0; L4_VALUE=
    while IFS= read -r L4_LINE || [ -n "$L4_LINE" ]; do
        [ "$L4_LINE" != 'ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)' ] || L4_HEADER=1
        set -- $L4_LINE
        [ "$#" -gt 0 ] || continue
        case "$1" in \#*:) L4_INDEX=${1#\#}; L4_INDEX=${L4_INDEX%:} ;; *) continue ;; esac
        case "$L4_INDEX" in ''|*[!0-9]*) continue ;; esac
        shift
        L4_LINE_MATCHES=0
        for L4_TOKEN in "$@"; do
            case "$L4_TOKEN" in
                *:dji.go.v5/*)
                    L4_VALUE_PID=${L4_TOKEN%%:*}; L4_UID=${L4_TOKEN#*:dji.go.v5/}
                    valid_pid "$L4_VALUE_PID" || continue
                    [ "$L4_TOKEN" = "$L4_VALUE_PID:dji.go.v5/$L4_UID" ] || continue
                    case "$L4_UID" in u0a*) L4_APP_ID=${L4_UID#u0a} ;; *) return 1 ;; esac
                    case "$L4_APP_ID" in ''|*[!0-9]*) return 1 ;; esac
                    case "$L4_APP_ID" in 0) ;; 0*) return 1 ;; esac
                    [ "${#L4_APP_ID}" -le 4 ] || return 1
                    L4_VALUE_UID=$((10000 + L4_APP_ID))
                    L4_LINE_MATCHES=$((L4_LINE_MATCHES + 1)); L4_VALUE=$L4_VALUE_PID ;;
            esac
        done
        [ "$L4_LINE_MATCHES" -le 1 ] || return 1
        L4_MATCHES=$((L4_MATCHES + L4_LINE_MATCHES))
    done
    [ "$L4_HEADER" -eq 1 ] && [ "$L4_MATCHES" -eq 1 ] && valid_pid "$L4_VALUE" || return 1
    printf '%s %s' "$L4_VALUE" "$L4_VALUE_UID"
}
read_ams() {
    capture "$1" 3 4096 dumpsys activity -p dji.go.v5 lru
    L4_AMS=; L4_AMS_UID=
    if okay && L4_PAIR=$(printf '%s\n' "$L4_OUT" | ams_stream); then
        set -- $L4_PAIR
        [ "$#" -eq 2 ] && valid_pid "$1" && valid_app_uid "$2" || return 1
        L4_AMS=$1; L4_AMS_UID=$2
    else return 1; fi
}

write_once() {
    [ ! -e "$1" ] && [ ! -L "$1" ] || return 1
    (set -C; printf '%s' "$2" >"$1")
}
read_record() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    if L4_RECORD=$(
        set -o pipefail || exit 1
        if head -c 513 "$1" | tr '\000' '\001'; then L4_RECORD_RC=0; else L4_RECORD_RC=$?; fi
        printf '.'
        exit "$L4_RECORD_RC"
    ); then :; else return 1; fi
    L4_RECORD=${L4_RECORD%.}
    [ "${#L4_RECORD}" -le 512 ] || return 1
    L4_BAD_BYTE=$(printf '\001')
    case "$L4_RECORD" in *"$L4_BAD_BYTE"*) return 1 ;; esac
}

read_copy() {
    read_record "$L4_COPY" || return 1
    set -- $L4_RECORD
    [ "$#" -eq 9 ] && [ "$1" = L4 ] && [ "$2" = COPY ] && [ "$9" = END ] || return 1
    [ "${#3}" -eq 16 ] || return 1
    case "$3" in *[!0-9a-f]*) return 1 ;; esac
    [ "$L4_OP" = STRUCTURE_CLEANUP ] || [ "$3" = "$L4_SID" ] || return 1
    valid_hash "$6" && [ "$6" = "$L4_SHA" ] && [ "$7" = "$L4_SIZE" ] || return 1
    case "$4" in ''|*[!0-9]*) return 1 ;; esac
    valid_pid "$5" || return 1
    valid_boot "$8" || return 1
    [ "$L4_RECORD" = "L4 COPY $3 $4 $5 $6 $7 $8 END$L4_LF" ] || return 1
    L4_COPY_SID=$3; L4_DEV=$4; L4_INO=$5; L4_COPY_BOOT=$8
}

read_attempt() {
    read_record "$L4_ATTEMPT" || return 1
    set -- $L4_RECORD
    [ "$#" -eq 7 ] && [ "$1" = L4 ] && [ "$2" = ATTEMPT ] && [ "$3" = "$L4_COPY_SID" ] && [ "$7" = END ] || return 1
    valid_pid "$4" && valid_app_uid "$5" && valid_boot "$6" || return 1
    [ "$6" = "$L4_COPY_BOOT" ] || return 1
    [ "$L4_RECORD" = "L4 ATTEMPT $3 $4 $5 $6 END$L4_LF" ] || return 1
    L4_ATTEMPT_PID=$4; L4_ATTEMPT_UID=$5; L4_ATTEMPT_BOOT=$6
}

# Native numbers are canonical and bounded before shell arithmetic is used.
bounded_native_number() {
    [ "$1" != -1 ] || return 0
    case "$1" in ''|*[!0-9]*) return 1 ;; 0) ;; 0*) return 1 ;; esac
    [ "${#1}" -le 5 ] && [ "$1" -le "$2" ]
}

native_stream() {
    L4_ENTERS=0; L4_EXPORTS=0; L4_RESULTS=0; L4_RESULT_LINE=
    L4_NATIVE_SID=${L4_COPY_SID:-$L4_SID}
    L4_UINT='(0|[1-9][0-9]{0,9})'
    L4_INT='(0|-?[1-9][0-9]{0,9})'
    L4_MAYBE='(-1|0|[1-9][0-9]{0,4})'
    L4_PRESENT='(-1|[01])'
    L4_RESULT_PATTERN="^schema=finduas-policy-structure/v1 phase=result sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} uid=$L4_UINT gid=$L4_UINT abi_bits=32 ready=[01] stage=(0|[1-9]|10|13|14) exception=[01] cloud_query_count=[01] product_query_count=[01] mmkv_decode_count=[01] namespace_present=$L4_PRESENT mmkv_present=$L4_PRESENT cloud_present=$L4_PRESENT product_present=$L4_PRESENT product_type=$L4_MAYBE receiver_type=$L4_MAYBE receiver_index=$L4_MAYBE json_rc=(-1|[0-9]|10|11) entry_count=$L4_MAYBE duplicate_count=$L4_MAYBE candidate_count=$L4_MAYBE match_count=$L4_PRESENT default_match=$L4_PRESENT product_blocked_count=$L4_MAYBE jni_rc=$L4_INT env_rc=$L4_INT guard_rc=$L4_MAYBE dispose_attempted=[01] dispose_rc=$L4_INT$"
    while IFS= read -r L4_LINE || [ -n "$L4_LINE" ]; do
        case "$L4_LINE" in 'schema=finduas-policy-structure/v1 '*) ;; *) continue ;; esac
        set -- $L4_LINE
        [ "$3" = "sid=$L4_NATIVE_SID" ] && [ "$4" = "pid=$L4_PID" ] || continue
        case "$2" in
            phase=enter)
                [ "$L4_LINE" = "schema=finduas-policy-structure/v1 phase=enter sid=$L4_NATIVE_SID pid=$L4_PID uid=$L4_TARGET_UID gid=$L4_TARGET_UID abi_bits=32" ] || return 1
                [ "$L4_ENTERS:$L4_RESULTS" = 0:0 ] || return 1
                L4_ENTERS=1 ;;
            phase=export)
                [ "$L4_ENTERS:$L4_EXPORTS:$L4_RESULTS" = 1:0:0 ] || return 1
                [ "$#" -eq 11 ] && [ "$L4_LINE" = "$*" ] || return 1
                printf '%s\n' "$L4_LINE" | grep -Eq "^schema=finduas-policy-structure/v1 phase=export sid=[0-9a-f]{16} pid=[1-9][0-9]{0,9} export_rc=$L4_MAYBE export_bytes=$L4_MAYBE matched_rows=$L4_MAYBE default_present=$L4_PRESENT default_nonempty=$L4_PRESENT matched_hex_length=$L4_MAYBE default_hex_length=$L4_MAYBE$" || return 1
                bounded_native_number "${5#export_rc=}" 999 &&
                    bounded_native_number "${6#export_bytes=}" 32768 &&
                    bounded_native_number "${7#matched_rows=}" 256 &&
                    bounded_native_number "${10#matched_hex_length=}" 65536 &&
                    bounded_native_number "${11#default_hex_length=}" 65536 || return 1
                L4_EXPORTS=1 ;;
            phase=result)
                [ "$L4_ENTERS:$L4_EXPORTS:$L4_RESULTS" = 1:1:0 ] || return 1
                printf '%s\n' "$L4_LINE" | grep -Eq "$L4_RESULT_PATTERN" || return 1
                [ "$#" -eq 32 ] && [ "$5" = "uid=$L4_TARGET_UID" ] && [ "$6" = "gid=$L4_TARGET_UID" ] || return 1
                [ "$L4_LINE" = "$*" ] || return 1
                bounded_native_number "${18#product_type=}" 65535 &&
                    bounded_native_number "${19#receiver_type=}" 255 &&
                    bounded_native_number "${20#receiver_index=}" 255 &&
                    bounded_native_number "${30#guard_rc=}" 15 || return 1
                for L4_NUMBER in "${22#entry_count=}" "${23#duplicate_count=}" "${24#candidate_count=}" "${27#product_blocked_count=}"; do
                    bounded_native_number "$L4_NUMBER" 256 || return 1
                done
                [ "${31}" != dispose_attempted=0 ] || [ "${32}" = dispose_rc=-1 ] || return 1
                L4_EXPECT_READY=0
                if [ "$9" = stage=0 ]; then
                    [ "${10}" = exception=0 ] && [ "${28}" = jni_rc=0 ] && [ "${29}" = env_rc=0 ] &&
                        [ "${31}" = dispose_attempted=1 ] && [ "${32}" = dispose_rc=0 ] || return 1
                    case "${21}" in json_rc=0|json_rc=1|json_rc=9) ;; *) return 1 ;; esac
                    L4_EXPECT_READY=1
                fi
                [ "$8" = "ready=$L4_EXPECT_READY" ] || return 1
                L4_RESULTS=1; L4_RESULT_LINE=$L4_LINE ;;
            *) return 1 ;;
        esac
    done
    [ "$L4_ENTERS:$L4_EXPORTS:$L4_RESULTS" = 1:1:1 ] || return 1
    printf '%s' "$L4_RESULT_LINE"
}

read_native() {
    # The complete enter/result pair fits this cap. Missing caches can be terminal
    # and permit owned-file cleanup without becoming an observed policy relation.
    capture native_log 3 2048 logcat -d -b main -v raw --pid="$L4_PID" 'FindUAS-Policy-Structure:I' '*:S'
    L4_NATIVE_RESULT=false; L4_NATIVE_READY=false; L4_NATIVE_OBSERVED=false
    okay || return 1
    if L4_NATIVE_CHECK=$(set -o pipefail || exit 1; printf '%s\n' "$L4_OUT" | native_stream); then :; else return 1; fi
    set -- $L4_NATIVE_CHECK
    [ "$#" -eq 32 ] || return 1
    L4_NATIVE_RESULT=true
    [ "$8" != ready=1 ] || L4_NATIVE_READY=true
    if [ "$L4_NATIVE_READY" = true ] && [ "${11}" = cloud_query_count=1 ] &&
        [ "${12}" = product_query_count=1 ] && [ "${13}" = mmkv_decode_count=1 ] &&
        [ "${14}" = namespace_present=1 ] && [ "${15}" = mmkv_present=1 ] &&
        [ "${16}" = cloud_present=1 ] && [ "${17}" = product_present=1 ] && [ "${21}" = json_rc=0 ]; then
        L4_NATIVE_OBSERVED=true
        for L4_NUMBER in "${18#product_type=}" "${19#receiver_type=}" "${20#receiver_index=}" \
            "${22#entry_count=}" "${23#duplicate_count=}" "${24#candidate_count=}" \
            "${25#match_count=}" "${26#default_match=}" "${27#product_blocked_count=}"; do
            [ "$L4_NUMBER" -ge 0 ] || L4_NATIVE_OBSERVED=false
        done
    fi
    shift 7
    L4_NATIVE_FIELDS=$*
    return 0
}

network_stream() {
    L4_DEFAULT=0; L4_NETWORK_SECTION=0
    while IFS= read -r L4_LINE || [ -n "$L4_LINE" ]; do
        set -- $L4_LINE
        [ "$#" -gt 0 ] || continue
        case "$*" in
            'Active default network: none')
                [ "$L4_DEFAULT:$L4_NETWORK_SECTION" = 0:0 ] || return 1
                L4_DEFAULT=1 ;;
            'Current Networks:')
                [ "$L4_DEFAULT:$L4_NETWORK_SECTION" = 1:0 ] || return 1
                L4_NETWORK_SECTION=1 ;;
            'Restrict background: true'|'Restrict background: false')
                [ "$L4_NETWORK_SECTION" -eq 1 ] || return 1
                L4_NETWORK_SECTION=2 ;;
            *) return 1 ;;
        esac
    done
    [ "$L4_DEFAULT:$L4_NETWORK_SECTION" = 1:2 ]
}

baseline() {
    L4_READY=true
    capture caller_uid 3 256 id -u
    L4_GOOD=false; okay && [ "$L4_OUT" = 1000 ] && L4_GOOD=true; check caller_uid "$L4_GOOD"
    capture caller_domain 3 256 id -Z
    L4_GOOD=false; okay && [ "$L4_OUT" = u:r:system_app:s0 ] && L4_GOOD=true; check caller_domain "$L4_GOOD"
    capture selinux 3 256 getenforce
    L4_GOOD=false; okay && [ "$L4_OUT" = Permissive ] && L4_GOOD=true; check selinux "$L4_GOOD"
    capture ro_debuggable 3 256 getprop ro.debuggable
    L4_GOOD=false; okay && [ "$L4_OUT" = 1 ] && L4_GOOD=true; check ro_debuggable "$L4_GOOD"
    capture boot_id 3 128 cat /proc/sys/kernel/random/boot_id
    L4_BOOT=$L4_OUT; L4_GOOD=false; okay && valid_boot "$L4_BOOT" && L4_GOOD=true; check boot_id "$L4_GOOD"
    capture wifi_setting 3 256 settings get global wifi_on
    L4_GOOD=false; okay && [ "$L4_OUT" = 0 ] && L4_GOOD=true; check wifi_setting "$L4_GOOD"
    capture wifi_service 3 16384 sh -c 'set -o pipefail; dumpsys wifi | sed -n "1,30p"'
    L4_GOOD=false
    if okay; then case "$L4_OUT" in *'Wi-Fi is disabled'*|*'Wi-Fi is currently disabled'*) L4_GOOD=true ;; esac; fi
    check wifi_service "$L4_GOOD"
    capture connectivity 3 24576 sh -c 'set -o pipefail; dumpsys connectivity | sed -n "/Active default network:/p;/^[[:space:]]*Current Networks:/,/^[[:space:]]*Restrict background:/p"'
    L4_GOOD=false
    if okay && (set -o pipefail; printf '%s\n' "$L4_OUT" | network_stream); then L4_GOOD=true; fi
    check network_isolated "$L4_GOOD"
    for L4_PROP in sys.upgrade.app_self.path persist.dji.upgrade.app_update persist.upgrade.app_self sys.upgrade.app_self; do
        capture "update_$L4_PROP" 3 512 getprop "$L4_PROP"
        L4_GOOD=false
        if okay; then case "$L4_OUT" in ''|0|false) L4_GOOD=true ;; esac; fi
        check "$L4_PROP" "$L4_GOOD"
    done
    capture package_path 3 1024 pm path dji.go.v5
    L4_APK=
    if okay; then case "$L4_OUT" in package:/data/app/*) L4_APK=${L4_OUT#package:} ;; esac; fi
    case "$L4_APK" in ''|*[!a-zA-Z0-9/_.=~-]*|*'/../'*|*'/./'*) L4_APK= ;; esac
    L4_GOOD=false
    if [ -n "$L4_APK" ] && [ -f "$L4_APK" ] && [ ! -L "$L4_APK" ]; then
        capture package_hash 30 1024 sha256sum "$L4_APK"
        okay && [ "${L4_OUT%% *}" = "$L4_APK_SHA" ] && L4_GOOD=true
    fi
    check package_identity "$L4_GOOD"
    L4_GOOD=false; read_ams ams_before && L4_GOOD=true; check ams_before "$L4_GOOD"; L4_PID=$L4_AMS; L4_TARGET_UID=$L4_AMS_UID
    capture parent_metadata 3 512 stat -c '%a:%u:%g' /data/app
    L4_GOOD=false; okay && [ "$L4_OUT" = 771:1000:1000 ] && L4_GOOD=true; check parent_metadata "$L4_GOOD"
    capture parent_label 3 1024 ls -ldZ /data/app
    L4_GOOD=false
    if okay; then case "$L4_OUT" in *' u:object_r:apk_data_file:s0 '*) L4_GOOD=true ;; esac; fi
    check parent_label "$L4_GOOD"
    L4_GOOD=false
    if [ ! -e "$L4_TARGET" ] && [ ! -L "$L4_TARGET" ] && [ ! -e "$L4_COPY" ] && [ ! -L "$L4_COPY" ] && [ ! -e "$L4_ATTEMPT" ] && [ ! -L "$L4_ATTEMPT" ]; then L4_GOOD=true; fi
    check fresh_test_paths "$L4_GOOD"
    capture source_size 3 256 stat -c %s "$L4_SOURCE"
    L4_GOOD=false
    okay && [ "$L4_OUT" = "$L4_SIZE" ] && [ -f "$L4_SOURCE" ] && [ ! -L "$L4_SOURCE" ] && L4_GOOD=true
    check source_size "$L4_GOOD"
    capture source_hash 5 1024 sha256sum "$L4_SOURCE"
    L4_GOOD=false; okay && [ "${L4_OUT%% *}" = "$L4_SHA" ] && L4_GOOD=true; check source_hash "$L4_GOOD"
    capture log_write 3 1024 log -p i -t FindUAS-Structure-Loader "schema=finduas-policy-loader-control/v1 sid=$L4_SID phase=baseline"
    L4_GOOD=false; okay && L4_GOOD=true; check log_write "$L4_GOOD"
    capture log_read 3 8192 logcat -d -b main -v raw 'FindUAS-Structure-Loader:I' '*:S'
    L4_GOOD=false
    if okay; then case "$L4_OUT" in *"schema=finduas-policy-loader-control/v1 sid=$L4_SID phase=baseline"*) L4_GOOD=true ;; esac; fi
    check log_read "$L4_GOOD"
    if valid_pid "$L4_PID"; then
        capture target_log_control 3 8192 logcat -d -b main,system,crash -v brief --pid="$L4_PID" -t 16
        L4_GOOD=false
        if okay; then case "$L4_OUT" in *"($L4_PID)"*|*"( $L4_PID)"*|*"(  $L4_PID)"*) L4_GOOD=true ;; esac; fi
        check target_log_control "$L4_GOOD"
    fi
    L4_GOOD=false; read_ams ams_after_baseline && [ "$L4_AMS" = "$L4_PID" ] && [ "$L4_AMS_UID" = "$L4_TARGET_UID" ] && L4_GOOD=true; check ams_stable "$L4_GOOD"
    printf 'preflight_ready=%s\ntarget_pid=%s\ntarget_uid=%s\n' "$L4_READY" "$L4_PID" "$L4_TARGET_UID"
    [ "$L4_READY" = true ]
}

owned_file_matches() {
    [ -f "$L4_TARGET" ] && [ ! -L "$L4_TARGET" ] || return 1
    capture target_identity 3 256 stat -c '%d:%i:%a:%u:%g:%s' "$L4_TARGET"
    okay && [ "$L4_OUT" = "$L4_DEV:$L4_INO:644:1000:1000:$L4_SIZE" ] || return 1
    capture target_hash 5 1024 sha256sum "$L4_TARGET"
    okay && [ "${L4_OUT%% *}" = "$L4_SHA" ] || return 1
    capture target_label 3 1024 ls -ldZ "$L4_TARGET"
    okay || return 1
    case "$L4_OUT" in *' u:object_r:apk_data_file:s0 '*) ;; *) return 1 ;; esac
}

copy_file() {
    # Keep the exclusively created output FD open throughout copy and identity capture.
    (
        umask 022
        set -C
        exec 3>"$L4_TARGET" || exit 73
        set +C
        # mksh marks shell-owned descriptors close-on-exec unless redirected on
        # this command. Pass the real exclusive FD to stat, not a PID/path guess.
        L4_META=$(stat -Lc '%d:%i' /proc/self/fd/3 3>&3) || exit 74
        L4_COPY_DEV=${L4_META%%:*}; L4_COPY_INO=${L4_META#*:}
        write_once "$L4_COPY" "L4 COPY $L4_SID $L4_COPY_DEV $L4_COPY_INO $L4_SHA $L4_SIZE $L4_BOOT END$L4_LF" || exit 74
        # A replaced/growing SD source cannot expand this internal copy without bound.
        timeout 5 head -c "$((L4_SIZE + 1))" "$L4_SOURCE" >&3 || exit 74
        exec 3>&- || exit 74
    )
}

cleanup() {
    read_copy || { printf 'cleanup_error=COPY_RECEIPT_UNAVAILABLE\n'; return 73; }
    if [ ! -e "$L4_TARGET" ] && [ ! -L "$L4_TARGET" ]; then
        L4_REMOVED=true; printf 'cleanup_already_absent=true\n'; return 0
    fi
    # An accepted dispatch may still be queued. A native terminal result (or a
    # different boot) closes this narrow loader before its file is removed.
    if [ -e "$L4_ATTEMPT" ] || [ -L "$L4_ATTEMPT" ]; then
        read_attempt || return 73
        capture cleanup_boot 3 128 cat /proc/sys/kernel/random/boot_id
        okay && valid_boot "$L4_OUT" || return 73
        if [ "$L4_OUT" = "$L4_ATTEMPT_BOOT" ]; then
            L4_PID=$L4_ATTEMPT_PID; L4_TARGET_UID=$L4_ATTEMPT_UID
            read_native || { printf 'cleanup_error=NATIVE_COMPLETION_NOT_OBSERVED\n'; return 75; }
        fi
    fi
    # A partial/failed copy is deliberately retained: its creation receipt alone
    # never authorizes deleting bytes that do not match the pinned full payload.
    owned_file_matches || { printf 'cleanup_error=FILE_IDENTITY_CHANGED\n'; return 73; }
    capture remove_test_file 3 1024 rm -- "$L4_TARGET"
    okay && [ ! -e "$L4_TARGET" ] && [ ! -L "$L4_TARGET" ] || return 74
    L4_REMOVED=true
}

load_once() {
    baseline || return 10
    printf 'BEGIN copy_file\n'
    if copy_file 2>&1; then L4_COPY_RC=0; L4_CREATED=true; else L4_COPY_RC=$?; L4_CREATED=unknown; fi
    printf 'command.copy_file.rc=%s\nEND copy_file\n' "$L4_COPY_RC"
    [ "$L4_COPY_RC" -eq 0 ] || return 74
    read_copy && owned_file_matches || return 74
    capture package_before_dispatch 30 1024 sha256sum "$L4_APK"
    if ! okay || [ "${L4_OUT%% *}" != "$L4_APK_SHA" ]; then cleanup; return 10; fi
    L4_GOOD=false; read_ams ams_before_dispatch && [ "$L4_AMS" = "$L4_PID" ] && [ "$L4_AMS_UID" = "$L4_TARGET_UID" ] && L4_GOOD=true
    check dispatch_pid_stable "$L4_GOOD"
    if [ "$L4_GOOD" != true ]; then cleanup; return 10; fi
    write_once "$L4_ATTEMPT" "L4 ATTEMPT $L4_SID $L4_PID $L4_TARGET_UID $L4_BOOT END$L4_LF" || return 73
    read_attempt && [ "$L4_ATTEMPT_PID" = "$L4_PID" ] && [ "$L4_ATTEMPT_UID" = "$L4_TARGET_UID" ] && [ "$L4_ATTEMPT_BOOT" = "$L4_BOOT" ] || return 73
    L4_DISPATCH=1
    capture attach_command 8 4096 cmd activity attach-agent dji.go.v5 "$L4_TARGET=$L4_SID"
    L4_ATTACH_RC=$L4_RC
    # Observe a bounded window; elapsed delay is never a completion signal.
    L4_WINDOW=0
    while [ "$L4_WINDOW" -lt 10 ]; do
        read_native && break
        sleep 1
        L4_WINDOW=$((L4_WINDOW + 1))
    done
    L4_SEEN=$L4_NATIVE_RESULT; L4_NATIVE_OK=$L4_NATIVE_READY
    capture framework_loader_log 3 8192 logcat -d -b main,system,crash -v brief --pid="$L4_PID" -t 64 \
        'ActivityThread:W' 'AndroidRuntime:W' 'art:W' 'linker:W' 'libc:W' '*:S'
    L4_GOOD=false; read_ams ams_after_dispatch && [ "$L4_AMS" = "$L4_PID" ] && [ "$L4_AMS_UID" = "$L4_TARGET_UID" ] && L4_GOOD=true
    printf 'ams_pid_stable_after_attach=%s\nattach_command_rc=%s\n' "$L4_GOOD" "$L4_ATTACH_RC"
    capture final_package_hash 30 1024 sha256sum "$L4_APK"
    L4_PACKAGE_OK=false; okay && [ "${L4_OUT%% *}" = "$L4_APK_SHA" ] && L4_PACKAGE_OK=true
    printf 'package_unchanged=%s\n' "$L4_PACKAGE_OK"
    if [ "$L4_SEEN" = true ]; then cleanup || return 74; else return 75; fi
    [ "$L4_GOOD" = true ] && [ "$L4_PACKAGE_OK" = true ] && [ "$L4_NATIVE_OK" = true ] && [ "$L4_ATTACH_RC" -eq 0 ] || return 1
    [ "$L4_NATIVE_OBSERVED" = true ] || return 10
    L4_CACHE_STATE=OBSERVED
}

L4_DISPATCH=0; L4_CREATED=false; L4_REMOVED=false; L4_SEEN=false
L4_PID=; L4_TARGET_UID=; L4_READY=false; L4_NATIVE_RESULT=false; L4_NATIVE_READY=false
L4_NATIVE_OBSERVED=false; L4_NATIVE_FIELDS=; L4_CACHE_STATE=UNKNOWN
printf 'schema=finduas-rc2-policy-structure-loader/v1\nsid=%s\noperation=%s\nreport_begin=true\n' "$L4_SID" "$L4_OP"
case "$L4_SIZE" in ''|0*|*[!0-9]*) L4_PINNED_SIZE=false ;; *) L4_PINNED_SIZE=true ;; esac
if ! valid_hash "$L4_SHA" || [ "$L4_PINNED_SIZE" != true ] || [ "${#L4_SIZE}" -gt 5 ] || [ "$L4_SIZE" -gt 32768 ]; then
    printf 'loader_error=UNPINNED_STRUCTURE_PROBE\n'; L4_FINAL_RC=69
else
    case "$L4_OP" in
        STRUCTURE_BASELINE) if baseline; then L4_FINAL_RC=0; else L4_FINAL_RC=10; fi ;;
        STRUCTURE_READ) if load_once; then L4_FINAL_RC=0; else L4_FINAL_RC=$?; fi ;;
        STRUCTURE_CLEANUP) if cleanup; then L4_FINAL_RC=0; else L4_FINAL_RC=$?; fi ;;
    esac
fi
printf 'attach_dispatch_count=%s\ntest_file_created=%s\ntest_file_removed=%s\nnative_result_observed=%s\n' \
    "$L4_DISPATCH" "$L4_CREATED" "$L4_REMOVED" "$L4_NATIVE_RESULT"
printf 'policy_structure_state=%s\n' "$L4_CACHE_STATE"
# Only the already validated fixed numeric field list is rendered here.
for L4_FIELD in $L4_NATIVE_FIELDS; do printf 'native_%s\n' "$L4_FIELD"; done
printf 'report_end=true\n'
exit "$L4_FINAL_RC"
