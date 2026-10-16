#!/usr/bin/env python3
"""Verify that a pinned Termux OpenCode ELF embeds a Bionic OpenTUI library.

This is intentionally a static verifier: GitHub-hosted Linux cannot execute
Android/Bionic AArch64 programs. It checks the outer ELF and parses embedded
AArch64 ELF dynamic tables instead of only grepping for "libopentui.so".
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ELF_MAGIC = b"\x7fELF"
EM_AARCH64 = 183
ET_DYN = 3
PT_LOAD = 1
PT_DYNAMIC = 2
PT_INTERP = 3
DT_NULL = 0
DT_NEEDED = 1
DT_STRTAB = 5
DT_STRSZ = 10
DT_SONAME = 14
BIONIC_INTERPRETER = "/system/bin/linker64"
GLIBC_NEEDED = {
    "libc.so.6",
    "libm.so.6",
    "libdl.so.2",
    "libpthread.so.0",
    "librt.so.1",
    "libresolv.so.2",
    "libutil.so.1",
}


class InvalidELF(ValueError):
    pass


def u16(data: bytes, off: int) -> int:
    return struct.unpack_from("<H", data, off)[0]


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def u64(data: bytes, off: int) -> int:
    return struct.unpack_from("<Q", data, off)[0]


def c_string(data: bytes, offset: int) -> str:
    if offset < 0 or offset >= len(data):
        raise InvalidELF("string offset outside file")
    end = data.find(b"\x00", offset)
    if end < 0:
        raise InvalidELF("unterminated ELF string")
    return data[offset:end].decode("utf-8", "replace")


def parse_elf(data: bytes, base: int) -> dict | None:
    """Parse an ELF64 little-endian AArch64 dynamic ELF embedded at base."""
    if base < 0 or data[base:base + 4] != ELF_MAGIC or base + 64 > len(data):
        return None
    if data[base + 4] != 2 or data[base + 5] != 1:
        return None
    e_type = u16(data, base + 0x10)
    machine = u16(data, base + 0x12)
    if e_type != ET_DYN or machine != EM_AARCH64:
        return None

    phoff = u64(data, base + 0x20)
    phentsize = u16(data, base + 0x36)
    phnum = u16(data, base + 0x38)
    if phentsize < 56 or phnum == 0 or phnum > 4096:
        return None
    if phoff + phentsize * phnum > len(data) - base:
        return None

    loads = []
    dynamic = None
    interp = None
    for i in range(phnum):
        off = base + phoff + i * phentsize
        p_type = u32(data, off)
        p_offset = u64(data, off + 8)
        p_vaddr = u64(data, off + 16)
        p_filesz = u64(data, off + 32)
        p_memsz = u64(data, off + 40)
        if p_offset + p_filesz > len(data) - base:
            return None
        segment = {
            "type": p_type, "offset": p_offset, "vaddr": p_vaddr,
            "filesz": p_filesz, "memsz": p_memsz,
        }
        if p_type == PT_LOAD:
            loads.append(segment)
        elif p_type == PT_DYNAMIC:
            dynamic = segment
        elif p_type == PT_INTERP:
            interp = c_string(data, base + p_offset)

    needed_offsets: list[int] = []
    soname_offset = None
    strtab_vaddr = None
    strtab_size = None
    if dynamic is not None:
        dyn_off = base + dynamic["offset"]
        dyn_end = dyn_off + dynamic["filesz"]
        if dynamic["filesz"] % 16:
            return None
        terminated = False
        for off in range(dyn_off, dyn_end, 16):
            tag, value = struct.unpack_from("<qQ", data, off)
            if tag == DT_NULL:
                terminated = True
                break
            if tag == DT_NEEDED:
                needed_offsets.append(value)
            elif tag == DT_STRTAB:
                strtab_vaddr = value
            elif tag == DT_STRSZ:
                strtab_size = value
            elif tag == DT_SONAME:
                soname_offset = value
        if not terminated or (needed_offsets and (strtab_vaddr is None or strtab_size is None)):
            return None

    needed: list[str] = []
    soname = None
    if strtab_vaddr is not None and strtab_size is not None:
        strtab_fileoff = None
        for load in loads:
            begin = load["vaddr"]
            end = begin + load["filesz"]
            if begin <= strtab_vaddr and strtab_vaddr + strtab_size <= end:
                strtab_fileoff = base + load["offset"] + (strtab_vaddr - begin)
                break
        if strtab_fileoff is None or strtab_fileoff + strtab_size > len(data):
            return None
        strtab = data[strtab_fileoff:strtab_fileoff + strtab_size]
        for item in needed_offsets:
            needed.append(c_string(strtab, item))
        if soname_offset is not None:
            soname = c_string(strtab, soname_offset)

    return {
        "offset": base,
        "type": e_type,
        "machine": "AArch64",
        "interpreter": interp,
        "soname": soname,
        "needed": needed,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <native-opencode-elf>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = path.read_bytes()
    outer = parse_elf(data, 0)
    if outer is None:
        raise SystemExit("FAIL: outer file is not a valid ELF64 AArch64 PIE")
    if outer["interpreter"] != BIONIC_INTERPRETER:
        raise SystemExit(
            f"FAIL: expected Android/Bionic interpreter {BIONIC_INTERPRETER!r}, "
            f"got {outer['interpreter']!r}"
        )

    # A real glibc binary may contain versioned DT_NEEDED entries such as
    # libc.so.6/libm.so.6. Check the outer ELF and every embedded AArch64
    # shared object, especially the exact libopentui.so loaded by the TUI.
    elf_candidates = [outer]
    cursor = 1
    while True:
        offset = data.find(ELF_MAGIC, cursor)
        if offset < 0:
            break
        parsed = parse_elf(data, offset)
        if parsed is not None:
            elf_candidates.append(parsed)
        cursor = offset + 1

    for elf in elf_candidates:
        bad = sorted(set(elf["needed"]) & GLIBC_NEEDED)
        if bad:
            where = "outer ELF" if elf["offset"] == 0 else f"embedded ELF at {elf['offset']:#x}"
            raise SystemExit(f"FAIL: glibc DT_NEEDED in {where}: {', '.join(bad)}")

    opentui = [item for item in elf_candidates if item["offset"] != 0 and item["soname"] == "libopentui.so"]
    if len(opentui) != 1:
        report = [
            {"offset": hex(x["offset"]), "soname": x["soname"], "needed": x["needed"]}
            for x in elf_candidates if x["offset"] != 0
        ]
        raise SystemExit(
            "FAIL: expected exactly one embedded AArch64 libopentui.so ELF; "
            f"found {len(opentui)}. Embedded ELF candidates: {json.dumps(report)}"
        )

    result = {
        "file": str(path),
        "outer_elf": {
            "machine": outer["machine"],
            "interpreter": outer["interpreter"],
            "needed": outer["needed"],
        },
        "embedded_aarch64_elfs": [
            {"offset": hex(x["offset"]), "soname": x["soname"], "needed": x["needed"]}
            for x in elf_candidates if x["offset"] != 0
        ],
        "opentui": {
            "offset": hex(opentui[0]["offset"]),
            "soname": opentui[0]["soname"],
            "needed": opentui[0]["needed"],
            "glibc_dependencies": [],
        },
        "result": "PASS",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InvalidELF, struct.error, OSError) as exc:
        print(f"FAIL: cannot verify native ELF: {exc}", file=sys.stderr)
        raise SystemExit(1)
