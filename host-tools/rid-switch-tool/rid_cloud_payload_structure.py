"""Bounded offline structure triage for an already captured matched/DEFAULT pair.

The input is private hex data, not an aircraft request. Successful generic syntax
parsing does not assign RID semantics. Output masks string/byte values; named JSON
boolean fields are reported only as name-based candidates. No packet/network API.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import zlib


@dataclass(frozen=True)
class Limits:
    payload_bytes: int = 65536
    fields: int = 2048
    depth: int = 12
    diff_ranges: int = 128
    decompression_layers: int = 2


class Invalid(ValueError):
    pass


SEMANTIC_NAMES = frozenset({
    "rid", "remote_id", "remoteid", "broadcast", "rid_enabled", "rid_enable",
    "remote_id_enabled", "broadcast_enabled", "enable", "enabled", "disable",
    "disabled", "switch", "version", "type", "flags", "mode", "value", "data",
    "config", "policy", "region", "country", "message",
})
BOOLEAN_NAMES = frozenset({"rid_enabled", "rid_enable", "remote_id_enabled",
                           "broadcast_enabled", "enabled", "enable", "disabled",
                           "disable", "switch"})


def strict_hex(value: str, limits: Limits) -> bytes:
    if type(value) is not str:
        raise Invalid("HEX_NOT_STRING")
    if len(value) > limits.payload_bytes * 2:
        raise Invalid("LIMIT_EXCEEDED")
    if len(value) % 2:
        raise Invalid("ODD_HEX_LENGTH")
    if re.fullmatch(r"[0-9A-Fa-f]*", value) is None:
        raise Invalid("NON_CANONICAL_HEX")
    return bytes.fromhex(value)


def scalar_kind(value) -> str:
    if value is None: return "NULL"
    if type(value) is bool: return "TRUE" if value else "FALSE"
    if type(value) in (int, float):
        return "ZERO" if value == 0 else "ONE" if value == 1 else "OTHER_NUMBER"
    if type(value) is str: return "STRING"
    if type(value) is list: return "ARRAY"
    return "OBJECT"


def json_structure(data: bytes, limits: Limits) -> dict:
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        raise Invalid("NOT_UTF8") from None
    depth = 0; quoted = escaped = False
    for char in text:
        if quoted:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char in "[{":
            depth += 1
            if depth > limits.depth: raise Invalid("LIMIT_EXCEEDED")
        elif char in "]}": depth -= 1
    def pairs(items):
        obj = {}
        for key, val in items:
            if key in obj: raise Invalid("DUPLICATE_JSON_KEY")
            obj[key] = val
        return obj
    def constant(_): raise Invalid("NON_JSON_CONSTANT")
    def integer(value):
        if len(value) > 80: raise Invalid("INTEGER_LIMIT")
        return int(value)
    try:
        root = json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_int=integer)
    except Invalid: raise
    except (ValueError, RecursionError): raise Invalid("INVALID_JSON") from None
    fields = []; named = []; stack = [((), root, 0)]
    while stack:
        path, value, depth = stack.pop()
        if depth > limits.depth or len(fields) >= limits.fields: raise Invalid("LIMIT_EXCEEDED")
        entry = {"path": list(path), "kind": scalar_kind(value)}
        if type(value) is float and not math.isfinite(value): raise Invalid("NON_FINITE_NUMBER")
        if type(value) is str:
            try: entry["utf8_bytes"] = len(value.encode("utf-8"))
            except UnicodeError: raise Invalid("INVALID_UNICODE") from None
        elif type(value) in (int, float) and type(value) is not bool:
            entry["integer"] = type(value) is int
        fields.append(entry)
        if type(value) is dict:
            if len(stack) + len(fields) + len(value) > limits.fields: raise Invalid("LIMIT_EXCEEDED")
            for i, (key, child) in reversed(list(enumerate(value.items()))):
                try: key.encode("utf-8")
                except UnicodeError: raise Invalid("INVALID_UNICODE") from None
                # Dynamic/unknown keys are represented by stable object ordinals.
                display = key if key.lower() in SEMANTIC_NAMES else f"key[{i}]"
                child_path = path + (display,)
                if key.lower() in BOOLEAN_NAMES and type(child) is bool:
                    named.append({"path": list(child_path), "boolean": child,
                                  "basis": "JSON_FIELD_NAME_ONLY"})
                stack.append((child_path, child, depth + 1))
        elif type(value) is list:
            if len(stack) + len(fields) + len(value) > limits.fields: raise Invalid("LIMIT_EXCEEDED")
            stack.extend((path + (f"item[{i}]",), child, depth + 1) for i, child in reversed(list(enumerate(value))))
    return {"status": "SYNTAX_VALID", "root_kind": scalar_kind(root), "fields": fields,
            "named_boolean_candidates": named}


def varint(data: bytes, at: int, end: int) -> tuple[int, int]:
    value = 0
    for i in range(10):
        if at == end: raise Invalid("TRUNCATED_VARINT")
        byte = data[at]; at += 1
        if i == 9 and byte > 1: raise Invalid("VARINT_OVERFLOW")
        value |= (byte & 127) << (7 * i)
        if byte < 128:
            if i and byte == 0: raise Invalid("NON_MINIMAL_VARINT")
            return value, at
    raise Invalid("VARINT_OVERFLOW")


def protobuf_structure(data: bytes, limits: Limits) -> dict:
    fields = []
    def parse(start, end, depth, path):
        if depth > limits.depth: raise Invalid("LIMIT_EXCEEDED")
        at = start; occurrences = Counter()
        if at == end: raise Invalid("EMPTY_MESSAGE")
        while at < end:
            if len(fields) >= limits.fields: raise Invalid("LIMIT_EXCEEDED")
            begin = at; key, at = varint(data, at, end)
            number, wire = key >> 3, key & 7
            if not 1 <= number < (1 << 29): raise Invalid("INVALID_FIELD_NUMBER")
            if wire not in (0, 1, 2, 5): raise Invalid("UNSUPPORTED_WIRE_TYPE")
            occurrence = occurrences[number]; occurrences[number] += 1
            field_path = path + (f"field[{number}][{occurrence}]",)
            entry = {"path": list(field_path), "field": number, "wire": wire, "offset": begin}
            if wire == 0:
                value, at = varint(data, at, end)
                entry.update(value_kind=scalar_kind(value), bit_width=value.bit_length())
                if value <= 65535: entry["small_unsigned_value"] = value
            elif wire in (1, 5):
                count = 8 if wire == 1 else 4
                if end - at < count: raise Invalid("TRUNCATED_FIXED")
                at += count; entry["bytes"] = count
            else:
                count, at = varint(data, at, end)
                if count > end - at: raise Invalid("TRUNCATED_LENGTH_FIELD")
                value_start = at; at += count
                entry["bytes"] = count
                if count:
                    mark = len(fields)
                    try:
                        # A complete child parse is retained only as an ambiguous
                        # embedded-message candidate; length-delimited also means bytes/string.
                        parse(value_start, at, depth + 1, field_path)
                        entry["embedded_message_syntax"] = True
                    except Invalid as error:
                        del fields[mark:]
                        if str(error) == "LIMIT_EXCEEDED": raise
                        entry["embedded_message_syntax"] = False
            entry["encoded_bytes"] = at - begin
            if len(fields) >= limits.fields: raise Invalid("LIMIT_EXCEEDED")
            fields.append(entry)
    parse(0, len(data), 0, ())
    fields.sort(key=lambda value: (value["offset"], len(value["path"])))
    return {"status": "SYNTAX_VALID", "encoding": "CANONICAL_PROTOBUF_WIRE_SUBSET",
            "fields": fields, "named_boolean_candidates": []}


def der_structure(data: bytes, limits: Limits) -> dict:
    fields = []
    def sequence(start, end, depth, path):
        if depth > limits.depth: raise Invalid("LIMIT_EXCEEDED")
        at = start; index = 0
        if at == end: return
        while at < end:
            if len(fields) >= limits.fields: raise Invalid("LIMIT_EXCEEDED")
            begin = at; first = data[at]; at += 1
            tag_class, constructed, tag = first >> 6, bool(first & 32), first & 31
            if tag == 31:
                tag = 0; octets = 0
                while True:
                    if at == end: raise Invalid("TRUNCATED_TAG")
                    byte = data[at]; at += 1; octets += 1
                    if octets == 1 and byte & 127 == 0: raise Invalid("NON_MINIMAL_TAG")
                    if octets > 5: raise Invalid("TAG_LIMIT")
                    tag = (tag << 7) | (byte & 127)
                    if byte < 128: break
                if tag < 31: raise Invalid("NON_MINIMAL_TAG")
            if tag_class == 0 and tag == 0: raise Invalid("END_OF_CONTENTS_NOT_DER")
            if at == end: raise Invalid("TRUNCATED_LENGTH")
            length = data[at]; at += 1
            if length & 128:
                count = length & 127
                if count == 0: raise Invalid("INDEFINITE_LENGTH_NOT_DER")
                if count > 4 or count > end - at: raise Invalid("LENGTH_LIMIT")
                if data[at] == 0: raise Invalid("NON_MINIMAL_LENGTH")
                length = int.from_bytes(data[at:at + count], "big"); at += count
                if length < 128: raise Invalid("NON_MINIMAL_LENGTH")
            if length > end - at: raise Invalid("TRUNCATED_TLV")
            value_end = at + length
            node_path = path + (f"tlv[{index}]",); index += 1
            entry = {"path": list(node_path), "offset": begin, "tag_class": tag_class,
                     "tag": tag, "constructed": constructed, "value_bytes": length,
                     "encoded_bytes": value_end - begin}
            if tag_class == 0:
                if tag in (16, 17) and not constructed: raise Invalid("PRIMITIVE_SEQUENCE_OR_SET")
                if tag in (1, 2, 3, 4, 5, 6, 12) and constructed: raise Invalid("CONSTRUCTED_PRIMITIVE_DER")
                if tag == 1:
                    if length != 1 or data[at] not in (0, 255): raise Invalid("INVALID_DER_BOOLEAN")
                    entry["value_kind"] = "TRUE" if data[at] else "FALSE"
                elif tag == 2:
                    if length == 0: raise Invalid("EMPTY_INTEGER")
                    if length > 1 and ((data[at] == 0 and data[at + 1] < 128) or
                                       (data[at] == 255 and data[at + 1] >= 128)):
                        raise Invalid("NON_MINIMAL_INTEGER")
                    entry["value_kind"] = scalar_kind(int.from_bytes(data[at:value_end], "big", signed=True))
                elif tag == 3:
                    if not length or data[at] > 7 or (length == 1 and data[at]): raise Invalid("INVALID_BIT_STRING")
                    if data[at] and data[value_end - 1] & ((1 << data[at]) - 1): raise Invalid("INVALID_UNUSED_BITS")
                elif tag == 5 and length != 0: raise Invalid("INVALID_NULL_LENGTH")
                elif tag == 6:
                    if not length: raise Invalid("EMPTY_OID")
                    first_arc_octet = True
                    for byte in data[at:value_end]:
                        if first_arc_octet and byte == 128: raise Invalid("NON_MINIMAL_OID")
                        first_arc_octet = byte < 128
                    if not first_arc_octet: raise Invalid("TRUNCATED_OID")
                elif tag == 12:
                    try: data[at:value_end].decode("utf-8")
                    except UnicodeError: raise Invalid("INVALID_UTF8") from None
            fields.append(entry)
            if constructed: sequence(at, value_end, depth + 1, node_path)
            at = value_end
    if not data: raise Invalid("EMPTY_INPUT")
    sequence(0, len(data), 0, ())
    return {"status": "SYNTAX_VALID", "encoding": "ASN1_DEFINITE_TLV_DER_CONSTRAINTS",
            "fields": fields, "named_boolean_candidates": []}


def analyze_bytes(data: bytes, limits: Limits = Limits(), layer: int = 0) -> dict:
    if len(data) > limits.payload_bytes: raise Invalid("LIMIT_EXCEEDED")
    result = {"bytes": len(data), "unique_byte_count": len(set(data)),
              "evidence_level": "STRUCTURAL_SYNTAX_ONLY", "formats": {}, "rid_switch_field": None}
    if not data:
        result["state"] = "EMPTY"; return result
    result["state"] = "PRESENT"
    for name, parser in [("json", json_structure), ("protobuf", protobuf_structure), ("asn1_tlv", der_structure)]:
        try: result["formats"][name] = parser(data, limits)
        except Invalid as error: result["formats"][name] = {"status": "NOT_ACCEPTED", "reason": str(error)}
    compression = None
    if data.startswith(b"\x1f\x8b"): compression = ("gzip", 16 + zlib.MAX_WBITS)
    elif len(data) >= 2 and data[0] & 15 == 8 and data[0] >> 4 <= 7 and int.from_bytes(data[:2], "big") % 31 == 0:
        compression = ("zlib", zlib.MAX_WBITS)
    if compression is not None:
        name, mode = compression
        if layer >= limits.decompression_layers:
            result["formats"][name] = {"status": "NOT_ACCEPTED", "reason": "LAYER_LIMIT"}
        else:
            try:
                decoder = zlib.decompressobj(mode)
                plain = decoder.decompress(data, limits.payload_bytes + 1)
                if len(plain) > limits.payload_bytes or decoder.unconsumed_tail: raise Invalid("DECOMPRESSION_LIMIT")
                if not decoder.eof or decoder.unused_data: raise Invalid("INCOMPLETE_OR_TRAILING_STREAM")
                result["formats"][name] = {"status": "SYNTAX_VALID", "uncompressed": analyze_bytes(plain, limits, layer + 1)}
            except Invalid as error: result["formats"][name] = {"status": "NOT_ACCEPTED", "reason": str(error)}
            except zlib.error: result["formats"][name] = {"status": "NOT_ACCEPTED", "reason": "INVALID_COMPRESSED_STREAM"}
    return result


def byte_difference(left: bytes, right: bytes, limits: Limits) -> dict:
    overlap = min(len(left), len(right)); prefix = 0; suffix = 0
    while prefix < overlap and left[prefix] == right[prefix]: prefix += 1
    while suffix < overlap - prefix and left[len(left)-1-suffix] == right[len(right)-1-suffix]: suffix += 1
    ranges = []; differences = 0; start = None
    for i in range(max(len(left), len(right))):
        changed = i >= overlap or left[i] != right[i]
        differences += int(changed)
        if changed and start is None: start = i
        if not changed and start is not None:
            if len(ranges) < limits.diff_ranges: ranges.append([start, i])
            start = None
    if start is not None and len(ranges) < limits.diff_ranges: ranges.append([start, max(len(left), len(right))])
    return {"identical": left == right, "matched_bytes": len(left), "default_bytes": len(right),
            "common_prefix_bytes": prefix, "common_suffix_bytes": suffix,
            "changed_offset_count": differences, "changed_ranges": ranges,
            "ranges_may_be_truncated": len(ranges) == limits.diff_ranges}


def structure_difference(left: dict, right: dict) -> dict:
    output = {}
    for name in ("json", "protobuf", "asn1_tlv"):
        a = left.get("formats", {}).get(name, {}); b = right.get("formats", {}).get(name, {})
        if a.get("status") != "SYNTAX_VALID" or b.get("status") != "SYNTAX_VALID": continue
        keyed_a = {tuple(x["path"]): x for x in a["fields"]}
        keyed_b = {tuple(x["path"]): x for x in b["fields"]}
        differences = []
        for path in sorted(keyed_a.keys() | keyed_b.keys()):
            av = keyed_a.get(path); bv = keyed_b.get(path)
            # Compare structural metadata; raw opaque/string values are never emitted.
            def clean(item):
                if item is None: return None
                return {k: v for k, v in item.items() if k not in ("path", "offset")}
            if clean(av) != clean(bv):
                differences.append({"path": list(path), "matched": clean(av), "default": clean(bv)})
        output[name] = {"changed_structural_fields": differences}
    return output


def analyze_pair(matched_hex: str, default_hex: str | None = None, *, default_present: bool | None = None,
                 matching_row_count: int | None = None, limits: Limits = Limits()) -> dict:
    matched = strict_hex(matched_hex, limits)
    if default_present is not None and type(default_present) is not bool: raise Invalid("INVALID_DEFAULT_STATE")
    if default_present is False and default_hex is not None: raise Invalid("CONFLICTING_DEFAULT_STATE")
    if matching_row_count is not None and (type(matching_row_count) is not int or matching_row_count < 1):
        raise Invalid("INVALID_MATCHING_ROW_COUNT")
    result = {"schema": "finduas-rid-policy-structure/v1", "matched": analyze_bytes(matched, limits),
              "matching_row_count": matching_row_count, "default_present": default_present,
              "default_state": "UNOBSERVED" if default_present is None else "MISSING" if not default_present else "UNCAPTURED"}
    if default_hex is not None:
        default = strict_hex(default_hex, limits)
        result["default_present"] = True
        result["default_state"] = "NONEMPTY" if default else "EMPTY"
        result["default"] = analyze_bytes(default, limits)
        result["byte_difference"] = byte_difference(matched, default, limits)
        result["structure_difference"] = structure_difference(result["matched"], result["default"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="private JSON with matched_hex/default_hex and presence metadata")
    parser.add_argument("--output", type=Path, required=True, help="private JSON analysis path")
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(300001)
        if len(raw) > 300000: raise Invalid("CAPTURE_LIMIT")
        capture = json.loads(raw)
        result = analyze_pair(capture["matched_hex"], capture.get("default_hex"),
                              default_present=capture.get("default_present"), matching_row_count=capture.get("matching_row_count"))
    except (Invalid, ValueError, KeyError, TypeError, OSError):
        print("structure analysis failed: invalid or unavailable private input")
        return 2
    try:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
        args.output.chmod(0o600)
    except OSError:
        print("structure analysis failed: private output unavailable")
        return 2
    print("private structure analysis saved")
    return 0


if __name__ == "__main__": raise SystemExit(main())
