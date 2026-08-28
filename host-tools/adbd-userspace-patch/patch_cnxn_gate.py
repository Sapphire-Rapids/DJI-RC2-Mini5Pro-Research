#!/usr/bin/env python3
"""Create, but never install, an adbd copy with the DJI pre-AUTH CNXN gate bypassed."""

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN, Cs
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_REG
from elftools.elf.elffile import ELFFile

HANDLE_PACKET = "_Z13handle_packetP7apacketP10atransport"
SEND_AUTH = "_Z17send_auth_requestP10atransport"
ANCHORS = (b"ro.boot.mp_state\0", b"production\0", b"ro.boot.dbg_cnt\0")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def unique_offset(data, needle):
    hits = []
    start = 0
    while True:
        hit = data.find(needle, start)
        if hit < 0:
            break
        hits.append(hit)
        start = hit + 1
    if len(hits) != 1:
        raise ValueError(f"expected one {needle[:-1]!r} string, found {len(hits)}")
    return hits[0]


def symbol(section, name):
    hits = [s for s in section.iter_symbols() if s.name == name]
    if len(hits) != 1 or hits[0]["st_size"] == 0:
        raise ValueError(f"missing or ambiguous unstripped symbol: {name}")
    return int(hits[0]["st_value"]), int(hits[0]["st_size"])


def file_to_vaddr(elf, offset):
    for segment in elf.iter_segments():
        if segment["p_type"] != "PT_LOAD":
            continue
        lo = int(segment["p_offset"])
        hi = lo + int(segment["p_filesz"])
        if lo <= offset < hi:
            return int(segment["p_vaddr"]) + offset - lo
    raise ValueError(f"file offset 0x{offset:x} is outside PT_LOAD")


def vaddr_to_file(elf, address):
    for segment in elf.iter_segments():
        if segment["p_type"] != "PT_LOAD":
            continue
        lo = int(segment["p_vaddr"])
        hi = lo + int(segment["p_filesz"])
        if lo <= address < hi:
            return int(segment["p_offset"]) + address - lo
    raise ValueError(f"virtual address 0x{address:x} is outside file-backed PT_LOAD")


def disassembler():
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    return md


def adrp_add_xrefs(instructions):
    refs = {}
    for first, second in zip(instructions, instructions[1:]):
        if first.mnemonic != "adrp" or second.mnemonic != "add":
            continue
        a, b = first.operands, second.operands
        if len(a) != 2 or len(b) != 3:
            continue
        if a[0].type != ARM64_OP_REG or a[1].type != ARM64_OP_IMM:
            continue
        if any(op.type not in (ARM64_OP_REG, ARM64_OP_IMM) for op in b):
            continue
        if b[0].reg == a[0].reg == b[1].reg and b[2].type == ARM64_OP_IMM:
            refs.setdefault(a[1].imm + b[2].imm, []).append(first.address)
    return refs


def encode_mov_wzr(cset_bytes):
    """Preserve the cset destination W register, but force its value to zero."""
    rd = struct.unpack("<I", cset_bytes)[0] & 0x1F
    return struct.pack("<I", 0x2A1F03E0 | rd)  # mov w<rd>, wzr (orr alias)


def analyze(path):
    data = Path(path).read_bytes()
    with Path(path).open("rb") as stream:
        elf = ELFFile(stream)
        if elf["e_machine"] != "EM_AARCH64":
            raise ValueError(f"expected AArch64 ELF, got {elf['e_machine']}")
        symtab = elf.get_section_by_name(".symtab")
        if symtab is None:
            raise ValueError(".symtab is absent; refusing an unanchored patch")
        handle_addr, handle_size = symbol(symtab, HANDLE_PACKET)
        send_auth_addr, _ = symbol(symtab, SEND_AUTH)
        handle_off = vaddr_to_file(elf, handle_addr)
        anchor_addrs = [file_to_vaddr(elf, unique_offset(data, s)) for s in ANCHORS]

        md = disassembler()
        insns = list(md.disasm(data[handle_off : handle_off + handle_size], handle_addr))
        if not insns or insns[-1].address + 4 != handle_addr + handle_size:
            raise ValueError("handle_packet did not disassemble completely")
        refs = adrp_add_xrefs(insns)
        xrefs = []
        for anchor, address in zip(ANCHORS, anchor_addrs):
            hits = refs.get(address, [])
            if len(hits) != 1:
                raise ValueError(f"expected one handle_packet xref to {anchor[:-1]!r}, found {len(hits)}")
            xrefs.append(hits[0])
        if not (xrefs[0] < xrefs[1] < xrefs[2] and xrefs[2] - xrefs[0] < 0x100):
            raise ValueError("DJI property-gate anchors are not in the expected order/window")

        csets = [i for i in insns if xrefs[2] < i.address <= xrefs[2] + 0x80 and i.mnemonic == "cset"]
        if len(csets) != 1 or not csets[0].op_str.endswith(", lt"):
            raise ValueError("expected one dbg_cnt < 1 cset after ro.boot.dbg_cnt")
        gate_reg = csets[0].operands[0].reg
        branches = []
        for insn in insns:
            if not (csets[0].address < insn.address <= csets[0].address + 0x80):
                continue
            if insn.mnemonic != "cbz" or len(insn.operands) != 2:
                continue
            if insn.operands[0].reg == gate_reg and insn.operands[1].type == ARM64_OP_IMM:
                branches.append(insn)
        if len(branches) != 1:
            raise ValueError(f"expected one gate-register cbz, found {len(branches)}")
        branch = branches[0]
        target = branch.operands[1].imm
        if not branch.address < target <= branch.address + 0x100:
            raise ValueError("gate cbz does not have the expected small forward target")
        auth_calls = [
            i for i in insns
            if target <= i.address < target + 0x80
            and i.mnemonic == "bl"
            and i.operands[0].type == ARM64_OP_IMM
            and i.operands[0].imm == send_auth_addr
        ]
        if len(auth_calls) != 1:
            raise ValueError("normal branch target does not lead to the named send_auth_request")

        patch_off = vaddr_to_file(elf, csets[0].address)
        before = data[patch_off : patch_off + 4]
        after = encode_mov_wzr(before)
        decoded = list(md.disasm(after, csets[0].address))
        expected_dest = csets[0].reg_name(gate_reg)
        if len(decoded) != 1 or decoded[0].mnemonic != "mov" or decoded[0].op_str != f"{expected_dest}, wzr":
            raise ValueError("internal gate-zero encoding verification failed")

    return data, {
        "input_sha256": sha256(data),
        "handle_packet_vaddr": f"0x{handle_addr:x}",
        "property_xrefs": [f"0x{x:x}" for x in xrefs],
        "patch_file_offset": f"0x{patch_off:x}",
        "patch_vaddr": f"0x{csets[0].address:x}",
        "gate_branch_vaddr": f"0x{branch.address:x}",
        "branch_target": f"0x{target:x}",
        "send_auth_request_vaddr": f"0x{send_auth_addr:x}",
        "before_hex": before.hex(),
        "before_disasm": f"{csets[0].mnemonic} {csets[0].op_str}",
        "after_hex": after.hex(),
        "after_disasm": f"{decoded[0].mnemonic} {decoded[0].op_str}",
        "_offset": patch_off,
        "_after": after,
    }


def create_copy(source, output, manifest=None):
    source = Path(source).resolve()
    output = Path(output).resolve()
    if source == output:
        raise ValueError("in-place patching is forbidden")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    data, plan = analyze(source)
    patched = bytearray(data)
    offset = plan.pop("_offset")
    patched[offset : offset + 4] = plan.pop("_after")
    differing = [i for i, (a, b) in enumerate(zip(data, patched)) if a != b]
    if not differing or any(i < offset or i >= offset + 4 for i in differing):
        raise ValueError(f"unexpected changed byte offsets: {differing}")
    plan["output_sha256"] = sha256(patched)
    plan["changed_offsets"] = [f"0x{x:x}" for x in differing]
    output.write_bytes(patched)
    os.chmod(output, source.stat().st_mode & 0o777)
    plan["output"] = str(output)
    if manifest:
        Path(manifest).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, help="write a new patched copy; input is never modified")
    parser.add_argument("--manifest", type=Path, help="optional JSON audit record (requires --output)")
    args = parser.parse_args()
    if args.manifest and not args.output:
        parser.error("--manifest requires --output")
    if args.output:
        plan = create_copy(args.input, args.output, args.manifest)
    else:
        _, plan = analyze(args.input)
        plan.pop("_offset")
        plan.pop("_after")
    print(json.dumps(plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
