#!/usr/bin/env python3
"""Parser for the Nofio base/head BOOT.BIN firmware images.

The files turn out to be standard Xilinx Zynq UltraScale+ MPSoC boot
images (bootgen output), not raw filesystem dumps. This tool decodes the
Boot Header, Image Header Table, Image Headers and Partition Headers and
prints the flash layout of every partition.

Structure reference: u-boot tools/zynqmpimage.{c,h} (Xilinx), which follows
UG1085 (TRM, ch. 11) and UG1137 (SW dev guide, ch. 16).

Usage:
    python3 scripts/parse_boot_bin.py <BOOT.BIN> [<BOOT.BIN> ...] [-x OUTDIR]

With -x, each partition's data (still AES-encrypted; see
firmware/boot_image_format.md) is dumped to OUTDIR.

This file is part of the nofio-linux project (GPLv3).
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
from pathlib import Path

WIDTH_DETECTION = 0xAA995566
IMAGE_IDENTIFIER = 0x584C4E58  # "XNLX" bytes, "XLNX" as u32

ENCRYPTION_NAMES = {
    0xA5C3C5A3: "EFUSE",
    0xA5C3C5A7: "OEFUSE",
    0x3A5C3C5A: "BBRAM",
    0xA35C7CA5: "OBBRAM",
    0x0: "NONE",
}

DEST_CPUS = {
    0: "none", 1: "a53-0", 2: "a53-1", 3: "a53-2", 4: "a53-3",
    5: "r5-0", 6: "r5-1", 7: "r5-lockstep", 8: "pmu",
}
DEST_DEVICES = {0: "none", 0x10: "PS", 0x20: "PL", 0x30: "PMU", 0x40: "XIP"}


def u16(d: bytes, o: int) -> int:
    return struct.unpack_from("<H", d, o)[0]


def u32(d: bytes, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


def u64(d: bytes, o: int) -> int:
    return struct.unpack_from("<Q", d, o)[0]


def entropy(b: bytes) -> float:
    if not b:
        return 0.0
    freq = [0] * 256
    for x in b:
        freq[x] += 1
    n = len(b)
    return -sum((c / n) * math.log2(c / n) for c in freq if c)


def attr_str(a: int) -> str:
    parts = []
    if a & 0x800000:
        parts.append("vec-location")
    if a & 0x040000:
        parts.append("big-endian")
    if (a >> 16) & 3 == 1:
        parts.append("owner=uboot")
    if a & 0x008000:
        parts.append("RSA-sig")
    ck = (a >> 12) & 7
    if ck:
        parts.append(["ck:md5", "ck:sha2", "ck:sha3"][ck - 1] if ck <= 3 else f"ck:{ck}")
    if a & 0x000080:
        parts.append("AES-ENCRYPTED")
    parts.append("cpu=" + DEST_CPUS.get((a >> 8) & 0xF, "?"))
    parts.append("dev=" + DEST_DEVICES.get((a >> 4) & 7, "?"))
    parts.append(f"EL{(a >> 1) & 3}")
    if a & 1:
        parts.append("TZ-secure")
    return ",".join(parts)


def image_name(d: bytes, ih_off: int) -> str:
    """Image Header name field: 8 bytes stored as two byte-swapped u32s."""
    raw = d[ih_off + 0x10 : ih_off + 0x18]
    return (raw[0:4][::-1] + raw[4:8][::-1]).decode("latin-1").strip("\x00")


def parse(path: Path, extract: Path | None = None) -> None:
    d = path.read_bytes()
    print(f"=== {path.name} ({len(d)} bytes = {hex(len(d))}) ===")

    # Boot Header sanity checks
    if u32(d, 0x20) != WIDTH_DETECTION or u32(d, 0x24) != IMAGE_IDENTIFIER:
        sys.exit(f"{path}: not a ZynqMP boot image (bad width detection / image id)")

    enc = u32(d, 0x28)
    print(f"Boot Header:")
    print(f"  encryption          = {enc:#010x} ({ENCRYPTION_NAMES.get(enc, '?')})")
    print(f"  image_load          = {u32(d, 0x2C):#x}")
    print(f"  image_offset        = {u32(d, 0x30):#x}   (FSBL data)")
    print(f"  image_size          = {u32(d, 0x3C):#x}")
    print(f"  image_stored_size   = {u32(d, 0x40):#x}")
    print(f"  image_attributes    = {u32(d, 0x44):#x} (CPU select: A53 64-bit)")
    print(f"  checksum            = {u32(d, 0x48):#x}")
    iht_off = u32(d, 0x98)
    print(f"  IHT offset (0x98)  = {iht_off:#x}")
    print(f"  PH offset  (0x9C)  = {u32(d, 0x9C):#x}")

    # Image Header Table
    ver, nr_parts, ph_off_w, ih_off_w, ac_off, boot_dev = struct.unpack_from("<6I", d, iht_off)
    ih_off, ph_off = ih_off_w * 4, ph_off_w * 4
    print(f"\nImage Header Table @ {iht_off:#x}:")
    print(f"  bootgen version = {ver:#x}, partitions = {nr_parts}, "
          f"image headers @ {ih_off:#x}, partition headers @ {ph_off:#x}")
    print(f"  IHT auth certificate @ {ac_off * 4:#x}, boot device = {boot_dev:#x}")

    # Image headers
    print(f"\nImages:")
    names = []
    i, off = 0, ih_off
    while off and i < nr_parts:
        nxt = u32(d, off) * 4
        first_ph = u32(d, off + 4) * 4
        name = image_name(d, off)
        names.append(name)
        print(f"  IH{i}: next={nxt:#x} first_partition_header={first_ph:#x} name={name!r}")
        off = nxt
        i += 1

    # Partition headers
    print(f"\nPartitions:")
    i, off = 0, ph_off
    while off and i < nr_parts:
        len_enc = u32(d, off) * 4
        len_unc = u32(d, off + 4) * 4
        stored = u32(d, off + 8) * 4
        nxt = u32(d, off + 12) * 4
        entry = u64(d, off + 16)
        load = u64(d, off + 24)
        data_off = u32(d, off + 32) * 4
        attr = u32(d, off + 36)
        auth_cert = u32(d, off + 52) * 4
        cksum = u32(d, off + 60)
        region = d[data_off : data_off + min(stored, 0x10000)]
        print(f"  PH{i + 1} @ {off:#x}: data @ {data_off:#x}, unencrypted len {len_unc:#x} "
              f"({len_unc} B), stored len {stored:#x}")
        print(f"        load={load:#x} entry={entry:#x} "
              f"auth_cert={auth_cert:#x} hdr_checksum={cksum:#x}")
        print(f"        attrs: {attr_str(attr)}")
        print(f"        region [{data_off:#x}, {data_off + stored:#x}) "
              f"entropy={entropy(region):.2f}")
        if extract:
            out = extract / f"part{i + 1}_{(names[i] if i < len(names) else '?').replace('.', '_')}"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(d[data_off : data_off + stored])
            print(f"        extracted -> {out}")
        off = nxt
        i += 1
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("images", nargs="+", type=Path, help="BOOT.BIN files")
    ap.add_argument("-x", "--extract", type=Path, default=None,
                    help="directory to dump (encrypted) partition data into")
    args = ap.parse_args()
    for p in args.images:
        parse(p, args.extract)


if __name__ == "__main__":
    main()
