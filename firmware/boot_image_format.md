# BOOT.BIN Format Analysis (Xilinx ZynqMP Boot Image)

Static analysis of `base_BOOT.BIN` / `head_BOOT.BIN`
(`miscellaneous/Resources/Firmware/`, from the v2.5.0 update package).
Tool: [`scripts/parse_boot_bin.py`](../scripts/parse_boot_bin.py).

**Headline findings**

1. Both files are **Xilinx Zynq UltraScale+ MPSoC boot images** (bootgen
   v1.2.0 output), not raw filesystem dumps. Nofio base and head are ZynqMP
   boards (Cortex-A53 + R5 + FPGA fabric) with a QCA2066 WiFi module.
2. The whole image is **AES-encrypted with an eFUSE key**
   (Boot Header `encryption = 0xA5C3C5A3` = `ENCRYPTION_EFUSE`) and every
   partition is **RSA-4096 signed**. Partition data entropy is 8.0 bits/byte.
3. Consequently the OS image (which contains the firmware-update daemon) **cannot
   be extracted statically** — it can only be read by the SoC, which holds the
   eFUSE key. All earlier binwalk findings (QNX6 superblock, PGP key, ARM
   Thumb code, GIF) were false positives on encrypted data; see the correction
   notice in [firmware_analysis.md](firmware_analysis.md).

## Image structure (ZynqMP boot image layout)

```
0x0000  Boot Header (BH, 0x8C0 bytes)
        +0x00 interrupt vectors (8 x 0x14000000 = A64 "b ." self-loop)
        +0x20 width detection   0xAA995566
        +0x24 image identifier  0x584C4E58 ("XNLX" bytes = "XLNX" u32)
        +0x28 encryption        0xA5C3C5A3 = ENCRYPTION_EFUSE
        +0x2C image_load        0xFFFC0000 (FSBL load address, OCM)
        +0x30 image_offset      0x2800    (FSBL data offset in file)
        +0x3C image_size        0x19228   (FSBL unencrypted size)
        +0x40 image_stored_size 0x1A180   (FSBL stored size incl. cert)
        +0x98 IHT offset        0x8C0
        +0x9C PH offset         0x1100
0x08C0  Image Header Table (IHT, 0x40 bytes)
        version 0x01020000, 8 partitions, image headers @ 0x900,
        partition headers @ 0x1100, IHT auth certificate @ 0x1940
0x0900  Image Headers (0x40 bytes each, linked list)
        name field: 8 bytes stored as two byte-swapped u32s
0x1100  Partition Headers (0x40 bytes each, linked list)
0x1940  IHT auth certificate (0xEC0 bytes, plaintext RSA-4096)
0x2800  first partition data
```

Partition Header fields (offsets in **words**, multiply by 4):
`+0x00` encrypted length, `+0x04` unencrypted length, `+0x08` stored length,
`+0x0C` next partition header, `+0x10` entry point (u64), `+0x18` load
address (u64), `+0x20` data offset, `+0x24` attributes,
`+0x34` auth certificate offset. Reference: u-boot `tools/zynqmpimage.{c,h}`
(UG1085 ch. 11 / UG1137 ch. 16).

## Partition layout

Head (`head_BOOT.BIN`, 59,459,968 bytes = 0x38B4980):

| # | Image | File offset | Unenc size | Stored size | Load addr | Attributes |
|---|-------|-------------|-----------|-------------|-----------|------------|
| 1 | fsbl.elf | 0x2800 | 0x19228 | 0x1A180 | 0xFFFC0000 | RSA, AES, a53-0, EL3 |
| 2 | pmufw.elf (seg 1) | 0x1C980 | 0x16614 | 0x17580 | 0xFFDC0000 | RSA, AES, pmu |
| 3 | pmufw.elf (seg 2) | 0x33F00 | 0x91C | 0x1880 | 0xFFDDA33C | RSA, AES, pmu |
| 4 | pmufw.elf (seg 3) | 0x35780 | 0x400 | 0x1340 | 0xFFDDF6E0 | RSA, AES, pmu |
| 5 | fpga.bit | 0x36AC0 | 0x76FBBC (7.8 MB) | 0x770B00 | — (PL) | RSA, AES, PL |
| 6 | bl31.elf (ATF) | 0x7A75C0 | 0xC7A0 | 0xD700 | 0xFFFEA000 | RSA, AES, a53-0, EL3, TZ-secure |
| 7 | u-boot.elf | 0x7B4CC0 | 0x1317E8 | 0x132740 | 0x08000000 | RSA, AES, a53-0, EL2 |
| 8 | linux.ub (OS image) | 0x10A0000 | 0x2813A0C (42 MB) | 0x2814980 | 0x10000000 | RSA, AES, a53-0 |

Base (`base_BOOT.BIN`, same total size): same structure and same FSBL/PMUFW/
BL31/U-Boot/OS sizes, except `fpga.bit` is **5.5 MB** (0x54F89C) instead of
7.8 MB, which shifts the intermediate offsets; `linux.ub` sits at the same
fixed offset 0x10A0000 with the same size 0x2813A0C.

Notes:

- Between the end of the boot chain (head: 0x8E7400, base: 0x6C70C0) and the
  OS image at 0x10A0000 the flash content is **erased (0xFF)**. The file is a
  raw flash image; the gap suggests a fixed flash partition map (boot region /
  reserved region / OS region) rather than a packed image.
- Every partition carries an RSA-4096 auth certificate (0xEC0 bytes) at the
  end of its stored region; the IHT has one at 0x1940 covering the headers.
- Each stored region ends right where the next partition begins — the layout
  is fully packed apart from the erased gap.

## Boot chain

```
BootROM (verifies BH, decrypts FSBL with eFUSE AES key, verifies RSA)
  → FSBL (A53-0, EL3, OCM 0xFFFC0000)
      → PMU firmware (R5/PMU RAM 0xFFDC0000)
      → FPGA bitstream (PL, via PCAP) — different design for base vs head
      → ARM Trusted Firmware bl31 (EL3, TZ-secure, 0xFFFEA000)
        → U-Boot (EL2, DDR 0x08000000)
          → OS image "linux.ub" (42 MB, DDR 0x10000000)
              Buildroot Linux 5.10.0-nofio initramfs with the nofio
              applications + update daemon (confirmed live via the
              support report; the partition name is literal)
```

## Base vs head differences

| Component | Same? |
|---|---|
| fsbl.elf | same size, **different bytes** (per-role build) |
| pmufw.elf | slightly different sizes/entry addresses |
| fpga.bit | **very different** (head 7.8 MB vs base 5.5 MB — different PL design per role) |
| bl31.elf, u-boot.elf | same sizes, different bytes |
| linux.ub (OS) | same size (42 MB), **different bytes** (role-specific OS image) |
| RSA keys | **identical** in both images |

## Cryptographic keys (plaintext in the images)

The IHT auth certificate at 0x1940-0x2800 is readable (the Boot ROM must read
the public keys before it can decrypt anything). It contains two RSA-4096
public keys (512-byte modulus, exponent 65537) — a primary (PPK) and a
secondary (SPK) key:

| Key | Modulus MD5 | Used by |
|---|---|---|
| key1 @ 0x1B81 | d2a37c833a783cdae1b51902ad67c53e | both base and head images |
| key2 @ 0x1FC1 | b8beccf16ea6b308ef265a053d41543f | both base and head images |

The same key pair signs base and head images (and presumably all shipped
nofio units), but it does **not** verify the update package's
`SHA1SUMS.SIG` (tested: no PKCS#1 v1.5 structure results when raising the
signature to e = 65537 with either boot key). The update signing key must be
a different pair, embedded in the encrypted OS image.

## Implications

1. **Static extraction of the update daemon / Linux rootfs is impossible**
   without the device's eFUSE AES key. The earlier plan to extract a QNX6
   filesystem from `head_BOOT.BIN` does not apply: the OS is Buildroot Linux
   (confirmed live via the support report) and the "QNX6 superblock" was a
   binwalk false positive on encrypted data.
2. **Custom / open-source firmware on stock hardware is blocked by hardware
   secure boot**: the Boot ROM will not load an FSBL that is not encrypted
   with the eFUSE key and signed by the vendor RSA key. The eFUSE key and the
   signing keys are not in the image (only public keys are).
3. The only remaining routes to device-side ground truth are **dynamic**:
   network capture during an update (see
   [firmware_flashing.md](firmware_flashing.md)), and UART/JTAG if the board
   exposes test points.
4. The role difference between base and head lives mainly in the FPGA
   bitstream and the OS image; the boot chain (FSBL/ATF/U-Boot) is per-role
   but structurally identical.

## Open questions

- Flash device size/layout (the image is 59.4 MB; the erased gap and the
  fixed OS offset 0x10A0000 imply a partition map worth confirming on
  hardware — e.g. whether a fallback image lives beyond 0x38B4980).
- Whether `SHA1SUMS.SIG` is verified by the device at all (the utility only
  checks the `SHA1SUMS` manifest hashes, never the `.SIG`), and with which key.
- Whether the QCA2066 firmware update (`Setup.UpdateParadeFw`) reuses any of
  this infrastructure or is a separate path on the WiFi module.
