# Firmware Analysis

This document contains analysis of the Nofio firmware files.

---

## Files

| File | Size | MD5 | Source |
|------|------|-----|--------|
| base_BOOT.BIN | 59,459,968 bytes | 5164b9a65fad809706bf60ad1cbebf0b | miscellaneous/Resources/Firmware/ |
| head_BOOT.BIN | 59,459,968 bytes | 123fcca1d3f0d1582f58350c52404f0e | miscellaneous/Resources/Firmware/ |

---

## General Structure

Both firmware files have:
- **Identical headers** (first 0x48 bytes)
- **High entropy** (~7.25 bits/byte) indicating compression and/or encryption
- **ARM Thumb Little-Endian code** sections
- **Compressed sections** (gzip, zstd signatures found)

---

## base_BOOT.BIN Analysis

### Header

| Offset | Size | Description | Hex Values |
|--------|------|-------------|------------|
| 0x00 | 0x20 | Padding/Signature | 00 00 00 14 (repeated 8 times) |
| 0x20 | 8 | Magic | 66 55 99 aa 58 4e 4c 58 ("fU..XNLX") |
| 0x28 | 8 | Unknown | a3 c5 c3 a5 00 00 fc ff |
| 0x30 | 8 | Unknown | 00 28 00 00 00 00 00 00 |
| 0x38 | 8 | Unknown | 00 28 92 01 00 80 a1 01 00 |
| 0x40 | 8 | Possible timestamp | 0c 08 00 00 ea 32 57 57 ("2WW") |

### Identified Sections

| Offset | Type | Details |
|--------|------|---------|
| 0x000968E4 | ARM Thumb LE | Function: push {r1, r3, r5, r6, r7, r8, sb, sl, fp, ip, lr} |
| 0x00214B00 | ARM Thumb LE | Function: push {r4, r5, r7, lr} |
| 0x002BA18 | ARM Thumb LE | Function: push {r2, r5, r6, lr} |
| 0x003B9D8 | ARM Thumb LE | Function: push {r0, r2, r3, r4, r6} |
| 0x004D8A8 | ARM Thumb LE | Function: push {r2, r5, lr} |
| 0x0000E40E | Gzip | Gzip signature found |
| 0x034602E9 | Zstd | Zstd signature found |
| 0x0037DF803 | GIF image | Embedded GIF image (27699 x 61353) |

### Extracted Files

- **extracted/base_embedded.gif** - GIF image extracted from offset 0x37DF803
  - Size: ~100KB (partial extraction)
  - Dimensions: 27699 x 61353 pixels
  - Status: Likely corrupted or compressed

### ARM Thumb Functions

**Total found:** 108+ functions

**Architecture:**
- ISA: ARM Thumb (mixed 16/32-bit)
- Endianness: Little-Endian
- Mode: Thumb (0x1 state)

**Sample disassembly (0x000968E4):**
```armasm
0x000968E4: push       {r1, r3, r5, r6, r7, r8, sb, sl, fp, ip, lr}
0x000968E8: ldr        r2, [r4], #-0x133
0x000968EC: ldr        ip, [r0, #-0x73e]!
0x000968F0: bhi        #0x1d7cd00
0x000968F4: svcvc      #0x2f9714
```

---

## head_BOOT.BIN Analysis

### Header

Same as base_BOOT.BIN (identical first 0x48 bytes).

### Identified Sections

| Offset | Type | Details |
|--------|------|---------|
| 0x012D2610 | QNX6 Super Block | QNX6 filesystem header |
| 0x0203BCE | ARM Thumb LE | Function |
| 0x07178324 | ARM Thumb LE | Function |
| 0x0000E40E | Gzip | Gzip signature found |
| 0x034602E9 | Zstd | Zstd signature found |
| 0x035C87AF | PGP RSA Key | 1024-bit, KeyID: B5BE2F1D 6952F57F |

### QNX6 Filesystem

- **Offset:** 0x012D2610
- **Type:** QNX6 Super Block
- **Status:** Detected by binwalk, but not yet extracted

**QNX6:**
- Real-time operating system (QNX Neutrino)
- Common in embedded devices
- Uses filesystem with superblock, inode, etc.
- Head adapter likely runs QNX6

### PGP RSA Key

- **Offset:** 0x035C87AF
- **Type:** PGP RSA encrypted session key
- **KeyID:** B5BE2F1D 6952F57F
- **Key Size:** 1024-bit

**Implications:**
- Firmware may be digitally signed
- Signature verification may occur at boot
- Custom firmware updates may need to bypass verification

### ARM Thumb Functions

**Many functions** found (exact count to be determined).

---

## Comparative Analysis

| Property | base_BOOT.BIN | head_BOOT.BIN |
|-----------|---------------|---------------|
| Size | 59,459,968 bytes | 59,459,968 bytes |
| MD5 | 5164b9a65fad809706bf60ad1cbebf0b | 123fcca1d3f0d1582f58350c52404f0e |
| Header | Identical | Identical |
| ARM Code | 108+ functions | Many functions |
| QNX6 Filesystem | No | Yes (at 0x012D2610) |
| PGP Key | No | Yes (at 0x035C87AF) |
| GIF Image | Yes (at 0x37DF803) | No |
| Gzip | Yes | Yes |
| Zstd | Yes | Yes |

---

## Hypothesis

### base_BOOT.BIN
- **Role:** Bootloader + base station control code
- **Content:** ARM Thumb code, embedded GIF, compressed data

### head_BOOT.BIN
- **Role:** QNX6 OS + head adapter applications
- **Content:** QNX6 filesystem, ARM Thumb code, PGP signed sections, compressed data

---

## Tools Used

- **binwalk** - Firmware analysis and signature detection
- **dd** - Manual extraction of embedded files
- **file** - File type identification

---

## Next Steps

1. **Complete QNX6 extraction**
   - Use QNX6-specific tools
   - Try different extraction methods
   - Analyze the superblock at 0x012D2610

2. **Full ARM Thumb disassembly**
   - Use Ghidra with ARM Thumb support
   - Use Capstone engine
   - Document all functions

3. **Decompression**
   - Try manual gzip/zstd extraction
   - Identify compression boundaries
   - Use firmware-mod-kit

4. **PGP key analysis**
   - Extract the PGP RSA key
   - Attempt signature verification
   - Research bypass methods

---

## References

- [QNX6 Documentation](https://www.qnx.com/developers/docs/)
- [binwalk](https://github.com/ReFirmLabs/binwalk)
- [Ghidra](https://ghidra-sre.org/)
- [Capstone Engine](https://www.capstone-engine.org/)
- [firmware-mod-kit](https://github.com/mirrors/firmware-mod-kit)
