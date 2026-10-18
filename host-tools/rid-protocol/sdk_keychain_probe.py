"""Emulate one pinned SDK keychain path in isolated ARM64 memory; print hashes only."""
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2
from unicorn.arm64_const import UC_ARM64_REG_X3, UC_ARM64_REG_X8, UC_ARM64_REG_X30
from unicorn.arm64_const import UC_ARM64_REG_SP, UC_ARM64_REG_PC, UC_ARM64_REG_CPACR_EL1

PIN = "e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873"
BASE, STACK, IO, HEAP, TRAPS, STOP = 0x100000, 0x2000000, 0x3000000, 0x4000000, 0x5000000, 0x5100000


class Probe:
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        assert hashlib.sha256(self.raw).hexdigest() == PIN, "Unexpected SDK artifact"
        b = self.raw
        phoff = struct.unpack_from("<Q", b, 32)[0]
        es, count = struct.unpack_from("<HH", b, 54)
        self.ph = [struct.unpack_from("<IIQQQQQQ", b, phoff + es*i) for i in range(count)]
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        limit = max(p[3] + p[6] for p in self.ph if p[0] == 1)
        self.uc.mem_map(BASE, (limit + 4095) & ~4095)
        for p in self.ph:
            if p[0] == 1:
                self.uc.mem_write(BASE + p[3], b[p[2]:p[2] + p[5]])
        for addr, size in [(STACK, 0x200000), (IO, 0x10000), (HEAP, 0x100000),
                           (TRAPS, 0x10000), (STOP, 0x1000)]:
            self.uc.mem_map(addr, size)
        self.uc.reg_write(UC_ARM64_REG_CPACR_EL1, 3 << 20)
        self.next_heap = HEAP
        self.external = {}
        self.hook_calls = {}
        dynamic = next(p for p in self.ph if p[0] == 2)
        # Use the virtual address mapped through PT_LOAD, not this artifact's decoy p_offset.
        self.dynamic_file_offset = self.offset(dynamic[3])
        d = {}
        for pos in range(self.dynamic_file_offset, self.dynamic_file_offset + dynamic[5], 16):
            tag, value = struct.unpack_from("<QQ", b, pos)
            if tag == 0:
                break
            d[tag] = value
        strings = b[self.offset(d[5]):self.offset(d[5]) + d[10]]

        def symbol(index):
            name, info, other, section, value, size = struct.unpack_from(
                "<IBBHQQ", b, self.offset(d[6]) + index*d[11])
            name = strings[name:strings.index(b"\0", name)].decode()
            if section:
                return BASE + value
            if name not in self.external:
                self.external[name] = TRAPS + 4*len(self.external)
            return self.external[name]

        relocations = [(d[7], d[8]), (d[23], d[2])]
        self.relocation_types = {}
        for addr, size in relocations:
            start = self.offset(addr)
            for pos in range(start, start + size, 24):
                target, info, addend = struct.unpack_from("<QQq", b, pos)
                kind, index = info & 0xffffffff, info >> 32
                self.relocation_types[kind] = self.relocation_types.get(kind, 0) + 1
                if kind == 1027:
                    value = BASE + addend
                elif kind in (257, 1025, 1026):
                    value = symbol(index) + addend
                else:
                    raise ValueError(f"Unsupported relocation {kind}")
                self.uc.mem_write(BASE + target, struct.pack("<Q", value))
        self.trap_names = {v: k for k, v in self.external.items()}
        self.uc.hook_add(UC_HOOK_CODE, self.on_external, begin=TRAPS, end=TRAPS + 0xffff)

    def offset(self, address):
        return next(p[2] + address - p[3] for p in self.ph
                    if p[0] == 1 and p[3] <= address < p[3] + p[5])

    def on_external(self, uc, address, size, user):
        name = self.trap_names[address]
        self.hook_calls[name] = self.hook_calls.get(name, 0) + 1
        x0, x1, x2 = (uc.reg_read(r) for r in (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2))
        if name in ("malloc", "_Znwm", "_Znam"):
            result = self.next_heap
            self.next_heap += (x0 + 15) & ~15
            assert self.next_heap < HEAP + 0x100000
        elif name in ("free", "_ZdlPv", "_ZdaPv"):
            result = 0
        elif name in ("memcpy", "memmove"):
            uc.mem_write(x0, bytes(uc.mem_read(x1, x2)))
            result = x0
        elif name == "memset":
            uc.mem_write(x0, bytes([x1 & 255])*x2)
            result = x0
        else:
            raise RuntimeError(f"Unexpected external call: {name}")
        uc.reg_write(UC_ARM64_REG_X0, result)
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))

    def call(self, address, args=(), result_ptr=None):
        uc = self.uc
        for reg, value in zip((UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3), args):
            uc.reg_write(reg, value)
        if result_ptr is not None:
            uc.reg_write(UC_ARM64_REG_X8, result_ptr)
        uc.reg_write(UC_ARM64_REG_SP, STACK + 0x1fff00)
        uc.reg_write(UC_ARM64_REG_X30, STOP)
        uc.emu_start(address, STOP, timeout=5000000, count=2000000)
        assert uc.reg_read(UC_ARM64_REG_PC) == STOP, "Emulation did not return within bounds"
        return uc.reg_read(UC_ARM64_REG_X0)

    def block(self, address, data):
        assert len(data) == 16
        self.uc.mem_write(IO, data)
        self.call(address, (IO, IO + 0x100))
        return bytes(self.uc.mem_read(IO + 0x100, 16))

    def key(self, index):
        self.uc.mem_write(IO + 0x300, bytes(32))
        self.call(0x44d640, (index,), result_ptr=IO + 0x300)
        raw = bytes(self.uc.mem_read(IO + 0x300, 24))
        capacity, size, pointer = struct.unpack("<QQQ", raw)
        if capacity & 1:
            return bytes(self.uc.mem_read(pointer, size))
        return raw[1:1 + (raw[0] >> 1)]


def main():
    p = Probe(sys.argv[1])
    for data in [bytes(16), bytes(range(16)), bytes([255])*16]:
        encrypted = p.block(0x44e3f0, data)
        assert p.block(0x44e3e4, encrypted) == data
    key = p.key(0x37)
    assert len(key) == 32, "Unexpected position key length"
    ptr, size, ivptr = struct.unpack("<QQQ", bytes(p.uc.mem_read(0x7daaa0, 24)))
    encrypted = bytes(p.uc.mem_read(ptr, size))
    iv = bytes(p.uc.mem_read(ivptr, 16))
    previous = iv
    plain = bytearray()
    for at in range(0, len(encrypted), 16):
        block = encrypted[at:at+16]
        plain += bytes(a ^ b for a,b in zip(p.block(0x44e3e4, block), previous))
        previous = block
    pad = plain[-1]
    assert pad == 16 and plain[-pad:] == bytes([pad])*pad
    assert bytes(plain[:-pad]) == key
    assert key != encrypted[:32]
    previous = iv
    restored = bytearray()
    for at in range(0, len(plain), 16):
        previous = p.block(0x44e3f0, bytes(a ^ b for a,b in zip(plain[at:at+16],previous)))
        restored += previous
    assert bytes(restored) == encrypted
    print(json.dumps({
        "subject_sha256": PIN, "emulator": "Unicorn ARM64; no OS or device execution",
        "dynamic_table_mapped_file_offset": hex(p.dynamic_file_offset),
        "keychain_index": "0x37", "stored_ciphertext_length": size,
        "returned_key_length": len(key), "returned_key_sha256": hashlib.sha256(key).hexdigest(),
        "stored_first32_is_returned_key": False, "padding_bytes": pad,
        "full_native_GetWhiteBoxKeyChainString_call": "PASS",
        "three_block_roundtrips": "PASS", "CBC_rewrap_matches_stored_blob": True,
        "external_calls": p.hook_calls,
        "limit": "Pinned SDK artifact only; no key bytes exported, no aircraft state or RF correspondence."}, indent=2))


if __name__ == "__main__":
    main()
