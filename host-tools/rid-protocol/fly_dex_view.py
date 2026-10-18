#!/usr/bin/env python3
"""Build one synthetic DEX analysis view from the pinned local Fly data carrier.

The carrier must be supplied explicitly and match SOURCE_SHA256. The output
folder must be new; keep input and generated files private and excluded from Git.
No vendor code is executed, no key is tried, and the carrier is never modified.
The header version/link fields are assumptions, not decrypted original values.
This tool does not establish original DEX identity, STUE/firmware decryption,
loader behavior, device control or RF effects.
Format reference: https://source.android.com/docs/core/runtime/dex-format
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zlib

SOURCE_SHA256 = "5a62603110efe22bbaed35ed34bdc8a292bf0fc657b4790fb0df086e497d1b22"
DEFAULT_BASE = 0x689F00C
UNREADABLE_PREFIX_END = 0x20000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mutf16(raw):
    """Decode DEX MUTF-8 to UTF-16 code units, including isolated surrogates."""
    units, i = [], 0
    while i < len(raw):
        c = raw[i]
        if 0 < c < 0x80:
            units.append(c)
            i += 1
        elif 0xC0 <= c <= 0xDF:
            d = raw[i + 1]
            assert d & 0xC0 == 0x80
            u = ((c & 31) << 6) | (d & 63)
            assert u >= 0x80 or (c == 0xC0 and d == 0x80)
            units.append(u)
            i += 2
        else:
            assert 0xE0 <= c <= 0xEF
            d, e = raw[i + 1:i + 3]
            assert d & 0xC0 == 0x80 and e & 0xC0 == 0x80
            u = ((c & 15) << 12) | ((d & 63) << 6) | (e & 63)
            assert u >= 0x800
            units.append(u)
            i += 3
    return tuple(units)


def main():
    if not __debug__:
        raise RuntimeError("Run without Python optimization so validation assertions remain enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carrier", type=Path, help="Pinned local libdatajar.so carrier")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="New private output directory; existing paths are refused")
    parser.add_argument("--base", type=lambda s: int(s, 0), default=DEFAULT_BASE,
                        help="File base of one directory-backed segment; default 0x689f00c")
    args = parser.parse_args()
    source = args.carrier.resolve(strict=True)
    out = args.output_dir.resolve()
    target_base = args.base
    output_stem = "target_segment" if target_base == DEFAULT_BASE else f"segment_{target_base:#x}"
    carrier = source.read_bytes()
    assert sha(carrier) == SOURCE_SHA256
    known_types = set(range(7)) | {0x1000, 0x1001, 0x1002, 0x1003} | set(range(0x2000, 0x2007))
    pattern = bytes.fromhex("00000000010000000000000001000000")
    maps, at = [], 0
    while True:
        at = carrier.find(pattern, at)
        if at < 0:
            break
        map_at, at = at - 4, at + 1
        if map_at < 0 or map_at % 4:
            continue
        count = struct.unpack_from("<I", carrier, map_at)[0]
        if not 8 <= count <= 32 or map_at + 4 + count * 12 > len(carrier):
            continue
        entries = list(struct.iter_unpack("<HHII", carrier[map_at + 4:map_at + 4 + 12 * count]))
        if any(t not in known_types or unused or not n for t, unused, n, o in entries):
            continue
        if len({t for t, _, _, _ in entries}) != count:
            continue
        if any(a[3] >= b[3] for a, b in zip(entries, entries[1:])):
            continue
        self_entries = [x for x in entries if x[0] == 0x1000 and x[2] == 1]
        if len(self_entries) != 1 or self_entries[0] != entries[-1]:
            continue
        base = map_at - self_entries[0][3]
        end = map_at + 4 + 12 * count
        if base < 0 or base >= map_at:
            continue
        by = {t: (n, o) for t, _, n, o in entries}
        if not all(t in by for t in range(7)) or by[0] != (1, 0) or by[1][1] != 0x70:
            continue
        sizes = {1: 4, 2: 4, 3: 12, 4: 8, 5: 8, 6: 32}
        if any(by[t][1] + by[t][0] * sizes[t] != by[t + 1][1] for t in range(1, 6)):
            continue
        if by[6][1] + by[6][0] * 32 != by[0x2002][1]:
            continue
        maps.append({
            "map_file_offset": hex(map_at), "record_base_candidate": hex(base),
            "map_count": count, "map_is_last_by_offset": True,
            "end_if_map_last": hex(end), "logical_length": hex(end - base),
            "logical_bytes_sha256": sha(carrier[base:end]),
            "entries": [{"type": hex(t), "count": n, "relative_offset": hex(o)} for t, _, n, o in entries],
        })
    assert len(maps) == 22
    for i, item in enumerate(maps):
        end = int(item["end_if_map_last"], 16)
        following = int(maps[i + 1]["record_base_candidate"], 16) if i + 1 < len(maps) else 0xC3EF00C
        item["following_base_or_blob_end"] = hex(following)
        base = int(item["record_base_candidate"], 16)
        item["page_rounding_rule_matches"] = following == base + ((end - base + 0xFFF) & ~0xFFF)
        item["gap_bytes"] = following - end
    assert all(m["page_rounding_rule_matches"] for m in maps)
    first_base, blob_start, blob_end = 0x500C, 0x4008, 0xC3EF00C
    directory_start = first_base - 16 * len(maps)
    payload_size = struct.unpack_from(">I", carrier, blob_start)[0]
    assert payload_size == blob_end - blob_start - 4
    for i, item in enumerate(maps):
        entry_at = directory_start + 16 * i
        relative, size, zero1, zero2 = struct.unpack_from(">4I", carrier, entry_at)
        assert relative + first_base == int(item["record_base_candidate"], 16)
        assert size == int(item["logical_length"], 16)
        assert zero1 == zero2 == 0
        item["directory_entry_file_offset"] = hex(entry_at)
        item["directory_relative_to_first_segment"] = hex(relative)
        item["directory_logical_size"] = hex(size)
        item["directory_matches_map_base_and_size"] = True
    container_layout = {
        "input": str(source), "input_sha256": SOURCE_SHA256,
        "blob_file_range": [hex(blob_start), hex(blob_end)],
        "big_endian_payload_size_at_blob_start": hex(payload_size),
        "payload_start": hex(blob_start + 4), "metadata_page_size": "0x1000",
        "first_segment_base": hex(first_base), "directory_file_start": hex(directory_start),
        "directory_file_end": hex(first_base), "directory_count": len(maps),
        "directory_entry_bytes": 16,
        "directory_layout": "BE u32 offset relative to first segment base; BE u32 logical size; two observed zero u32 words",
        "all_22_directory_records_match_independent_dex_map_bases_and_sizes": True,
        "segment_storage_rule": "Next base = current base + round_up(logical size, 4096); last storage end equals blob end",
        "unknown_metadata_range": [hex(blob_start + 4), hex(directory_start)],
        "unknown_metadata_note": "No interpretation or decryption attempted for this prefix or the two zero directory words.",
    }

    m = next((x for x in maps if int(x["record_base_candidate"], 16) == target_base), None)
    if m is None:
        raise ValueError(f"Requested base {target_base:#x} is not a directory/map-validated segment")
    base, end = target_base, int(m["end_if_map_last"], 16)
    original = carrier[base:end]
    by = {int(x["type"], 16): (x["count"], int(x["relative_offset"], 16)) for x in m["entries"]}
    string_count, string_ids_off = by[1]
    assert by[0x2002][0] == string_count
    if string_ids_off + 4 * string_count < UNREADABLE_PREFIX_END:
        raise ValueError(f"Refusing segment {base:#x}: prefix ends at 0x20000 but string_ids end at {string_ids_off + 4 * string_count:#x}; would require recovery of other tables")
    p = by[0x2002][1]
    string_data_end = next(int(x["relative_offset"], 16) for x in m["entries"] if int(x["relative_offset"], 16) > p)
    offsets, raw_strings, previous_units = [], [], None
    for i in range(string_count):
        offsets.append(p)
        size, shift = 0, 0
        while True:
            c = original[p]
            p += 1
            size |= (c & 127) << shift
            shift += 7
            assert shift <= 35
            if not c & 128:
                break
        zero = original.index(0, p, string_data_end)
        raw = original[p:zero]
        units = mutf16(raw)
        assert len(units) == size, i
        assert previous_units is None or previous_units < units, i
        previous_units = units
        raw_strings.append(raw)
        p = zero + 1
    assert string_data_end - p <= 3 and original[p:string_data_end] == b"\x00" * (string_data_end - p)
    old_offsets = struct.unpack_from(f"<{string_count}I", original, string_ids_off)
    first_clear_index = (UNREADABLE_PREFIX_END - string_ids_off) // 4
    assert string_ids_off + first_clear_index * 4 == UNREADABLE_PREFIX_END
    assert all(old_offsets[i] == offsets[i] for i in range(first_clear_index, string_count))
    invalid = [i for i, value in enumerate(old_offsets) if not by[0x2002][1] <= value < string_data_end]
    assert invalid[-1] == first_clear_index - 1

    type_count, type_off = by[2]
    descriptor_ids = struct.unpack_from(f"<{type_count}I", original, type_off)
    assert all(i < string_count for i in descriptor_ids)
    assert all(a < b for a, b in zip(descriptor_ids, descriptor_ids[1:]))
    descriptors = [raw_strings[i] for i in descriptor_ids]
    for descriptor in descriptors:
        atom = descriptor.lstrip(b"[")
        assert atom in (b"V", b"Z", b"B", b"S", b"C", b"I", b"J", b"F", b"D") or (len(atom) > 2 and atom.startswith(b"L") and atom.endswith(b";"))
        assert not (descriptor.startswith(b"[") and atom == b"V")


    def read_type_list(off):
        if not off:
            return ()
        assert by[0x1001][1] <= off < by[0x2005][1] and off % 4 == 0
        count = struct.unpack_from("<I", original, off)[0]
        assert off + 4 + count * 2 <= by[0x2005][1]
        ids = struct.unpack_from(f"<{count}H", original, off + 4)
        assert all(i < type_count and descriptors[i] != b"V" for i in ids)
        return ids


    protos = list(struct.iter_unpack("<III", original[by[3][1]:by[4][1]]))
    for shorty, ret, params in protos:
        assert shorty < string_count and ret < type_count
        signature_types = [descriptors[i] for i in (ret, *read_type_list(params))]
        expected_shorty = b"".join(d if len(d) == 1 else b"L" for d in signature_types)
        assert raw_strings[shorty] == expected_shorty
    fields = list(struct.iter_unpack("<HHI", original[by[4][1]:by[5][1]]))
    assert all(c < type_count and t < type_count and n < string_count for c, t, n in fields)
    methods = list(struct.iter_unpack("<HHI", original[by[5][1]:by[6][1]]))
    assert all(c < type_count and p < by[3][0] and n < string_count for c, p, n in methods)
    classes = list(struct.iter_unpack("<8I", original[by[6][1]:by[0x2002][1]]))
    assert len({c[0] for c in classes}) == len(classes)
    for cls, access, superclass, interfaces, source_file, annotations, class_data, static_values in classes:
        assert cls < type_count and descriptors[cls].startswith(b"L")
        assert superclass == 0xFFFFFFFF or (superclass < type_count and descriptors[superclass].startswith(b"L"))
        assert source_file == 0xFFFFFFFF or source_file < string_count
        assert class_data == 0 or by[0x2000][1] <= class_data < by[0x1000][1]
        assert all(descriptors[i].startswith(b"L") for i in read_type_list(interfaces))
        assert annotations == 0 or by[0x2006][1] <= annotations < by[0x2003][1]
        assert static_values == 0 or by[0x2005][1] <= static_values < by[0x2004][1]

    synthetic = bytearray(original)
    header_values = [len(original), 0x70, 0x12345678, 0, 0, by[0x1000][1]]
    for typ in range(1, 7):
        header_values.extend(by[typ])
    header_values.extend([len(original) - by[0x2002][1], by[0x2002][1]])
    synthetic[:112] = b"dex\n035\x00" + bytes(24) + struct.pack("<20I", *header_values)
    struct.pack_into(f"<{first_clear_index}I", synthetic, string_ids_off, *offsets[:first_clear_index])
    synthetic[12:32] = hashlib.sha1(synthetic[32:]).digest()
    struct.pack_into("<I", synthetic, 8, zlib.adler32(synthetic[12:]) & 0xFFFFFFFF)
    assert synthetic[UNREADABLE_PREFIX_END:] == original[UNREADABLE_PREFIX_END:]
    out.mkdir(parents=True, exist_ok=False)
    output = out / f"{output_stem}.analysis_only.dex"
    output.write_bytes(synthetic)

    targets = []
    for i, raw in enumerate(raw_strings):
        if raw == b"Luav/sdk/provider/jni/JNIProviderManagerForCPP;" or raw.startswith(b"clientLocation"):
            targets.append({"text": raw.decode("ascii"), "string_id": i,
                            "string_data_relative_offset": hex(offsets[i]),
                            "string_data_absolute_offset": hex(base + offsets[i])})
    manifest = {
        "input": str(source), "input_sha256": SOURCE_SHA256,
        "format_reference": "https://source.android.com/docs/core/runtime/dex-format",
        "source_modified": False, "kind": "synthetic analysis-only DEX view; not decryption",
        "target_map": m, "container_layout": container_layout, "all_segment_maps": maps,
        "output": str(output), "output_sha256": sha(synthetic),
        "original_slice_sha256": sha(original),
        "header_raw_hex": original[:112].hex(),
        "assumed_header_fields": {"version": "035", "header_size": "0x70", "endian_tag": "0x12345678", "link_size": 0, "link_off": 0},
        "assumption_note": "Original header is unreadable. These fields are synthetic parser settings; original version/link fields and original checksums are not recovered. Size, map location, table sizes/offsets and data range follow the surviving map. Checksums describe the synthetic view only.",
        "string_validation": {"parsed_count": len(offsets), "map_count": string_count,
            "all_mutf8_sequences_valid": True, "all_declared_utf16_lengths_match": True,
            "strict_utf16_sort_order": True, "trailing_padding_hex": original[p:string_data_end].hex(),
            "original_string_offset_in_range_count": string_count - len(invalid),
            "original_string_offset_invalid_count": len(invalid),
            "last_invalid_index": invalid[-1], "clear_suffix_first_index": first_clear_index,
            "clear_suffix_count": string_count - first_clear_index,
            "all_clear_suffix_offsets_match_reconstruction": True},
        "cross_table_validation": {
            "type_ids_valid_unique_and_sorted": len(descriptor_ids),
            "all_type_strings_have_descriptor_shapes": True,
            "protos_with_matching_shorty_return_and_parameter_types": len(protos),
            "field_ids_in_bounds": len(fields), "method_ids_in_bounds": len(methods),
            "class_defs_with_unique_class_types_and_valid_referenced_indices_offsets": len(classes),
            "target_class_definitions": [{"class_def_index": i, "class_idx": c[0], "descriptor_string_id": descriptor_ids[c[0]], "class_data_off": hex(c[6])} for i, c in enumerate(classes) if descriptors[c[0]] == b"Luav/sdk/provider/jni/JNIProviderManagerForCPP;"],
            "target_method_ids": [{"method_id": i, "class_idx": c, "proto_idx": p, "name_string_id": n, "name": raw_strings[n].decode("ascii")} for i, (c, p, n) in enumerate(methods) if descriptors[c] == b"Luav/sdk/provider/jni/JNIProviderManagerForCPP;" and raw_strings[n] == b"clientLocation"],
        },
        "patches": [
            {"relative_start": "0x0", "relative_end_exclusive": "0x70", "length": 112,
             "purpose": "Synthetic DEX header from map; new SHA-1 digest and Adler-32 checksum",
             "old_sha256": sha(original[:112]), "new_sha256": sha(synthetic[:112])},
            {"relative_start": "0x70", "relative_end_exclusive": "0x20000", "length": UNREADABLE_PREFIX_END - 112,
             "purpose": "Reconstruct first 32740 string_ids from validated sorted string_data",
             "old_sha256": sha(original[112:UNREADABLE_PREFIX_END]), "new_sha256": sha(synthetic[112:UNREADABLE_PREFIX_END])},
        ],
        "unchanged_relative_range": ["0x20000", hex(len(original))], "target_strings": targets,
        "checks": {"source_hash_unchanged": sha(source.read_bytes()) == SOURCE_SHA256,
                   "all_bytes_after_0x20000_identical": True,
                   "source_has_valid_header": False},
        "limitations": "Structural recovery produces a consistent analysis view, not original DEX identity, original header recovery or decryption. It establishes neither STUE/firmware decryption nor loader, device or RF behavior. No code_item execution, full verifier or Java-semantic analysis is performed by this script. Keep the carrier and generated files private/excluded.",
    }
    manifest_path = out / f"{output_stem}_reconstruction.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"segments_validated": len(maps), "base": hex(base),
                      "output": str(output), "manifest": str(manifest_path),
                      "sha256": sha(synthetic), "kind": "synthetic analysis-only DEX view; not decryption"}, indent=2))


if __name__ == "__main__":
    main()
