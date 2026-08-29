#!/bin/sh
# Read-only WA150 baseline session — NO writes, NO motors, NO RF measurement.
#
# Sequences the two fixed read-only probes for the Mini 5 Pro (wa150) Remote ID
# parameter candidates so an operator can capture a same-session baseline in one
# command batch and hand the redacted reports back:
#
#   1. by-index FLYC 0xE0/0xE1/0xE2 probe — table CRC/count positive control,
#      then the three wa150 RID rows (EU_CE_enable_c0_rid 1306,
#      EU_CE_Reg_RID_Enable 1308, eu_ce_support_remote_set_level 1315);
#   2. by-hash FLYC 0xF7/0xF8 — maximum-height positive control, the
#      EU_CE_enable_c0_rid_0 bridge, and the rid_ctrl_enable_0 baseline.
#
# Neither tool is ever given --target, so no F9/E3 write, no restore path, and no
# state change is possible from this script. The tools emit no serial, coordinate,
# account, or raw-frame material; review the reports before sharing them.
#
# Usage:
#   readonly_baseline_session.sh [aircraft|rc2] [legacy|modern]
#   (defaults: aircraft, legacy; modern routing is aircraft-only and is rejected
#    by the tools for the rc2 transport)

set -eu

transport=${1:-aircraft}
route=${2:-legacy}

case "$transport" in aircraft|rc2) ;; *) echo "transport must be aircraft or rc2" >&2; exit 2;; esac
case "$route" in legacy|modern) ;; *) echo "route must be legacy or modern" >&2; exit 2;; esac

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
stamp=$(date +%Y%m%dT%H%M%S)
out_dir="${READONLY_BASELINE_OUT_DIR:-$here/readonly_baseline_$stamp}"
mkdir -p "$out_dir"

echo "[1/2] by-index read-only probe -> $out_dir/by_index.json"
python3 "$here/rid_param_index_readonly.py" \
    --transport "$transport" --route "$route" \
    > "$out_dir/by_index.json"

echo "[2/2] by-hash positive control + EU C0 bridge + rid_ctrl baseline -> $out_dir/by_hash.json"
python3 "$here/rid_switch_control.py" \
    --transport "$transport" --route "$route" --index-bridge \
    > "$out_dir/by_hash.json"

echo "baseline reports written to $out_dir/"
echo "Review the two JSON files for unexpected identifiers before sharing."
