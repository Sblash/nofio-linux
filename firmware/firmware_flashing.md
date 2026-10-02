# Firmware Flashing

How the original nofio utility (`nofioUtility.exe`, .NET 7 / WPF) flashes
firmware onto the nofio base station and head adapter. This document is the
result of **static analysis only** — of the decompiled application
(`miscellaneous/nofio-decompiled/nofio-utility-cleaned/`) and of the shipped
boot images ([boot_image_format.md](boot_image_format.md)). No dynamic
captures were involved; device-side behavior is inferred and remains to be
verified live.

---

## 1. Physical setup required by the app

The UI instructions (from `FirmwareInstallFlowSteps.xaml`, step
`DevicesNotReady`, shown when devices are not wired):

> "Both of your Nofio devices need to be plugged in using USB cables before
> they can be updated."
>
> "Please note: The head unit must be plugged into this PC using its
> **right-hand USB-C port**."

The right-port requirement is repeated verbatim in the `Start` step. The app
never explains *why*; presumably only that port is wired to the head's
host-mode/Ethernet electronics (to be confirmed on hardware).

The gate is enforced in code, not just shown in text
(`UserInterface.Business.ViewModels/FirmwareInstallFlow.cs`):

```csharp
AreDevicesReady = connection.IsBaseConnected
               && connection.IsHeadConnected
               && connection.IsHeadLocal;
```

`IsHeadLocal` is the key condition: the head must be reachable **directly
from the PC**, not merely routed through the base over the wireless link. It
becomes true when the local socket to the head connects
(`UserInterface.Business.Services/NofioConnection.cs`).

## 2. Transport: TCP over USB-Ethernet

There is no USB serial / DFU-style flashing. The USB cable enumerates a
network interface and the update is a plain TCP session. Constants from
`NofioConnection.cs`:

| Device | Address | TCP port | Reached via |
|---|---|---|---|
| Base | `192.168.3.1` | 34566 | USB cable base → PC |
| Head | `192.168.4.1` | 34568 | USB cable (right-hand USB-C port) head → PC |

`NofioInterfaces.cs` watches
`NetworkInterface.GetAllNetworkInterfaces()` and considers a device's
network up when an interface with the matching subnet is operational
(`InterfaceUp(interfaces, BaseIpAddress)` / `...HeadIpAddress`).

Protocol versions negotiated in the `Connect` exchange:
`ProtocolVersion = 80`, `MinimumProtocolVersion = 49`.

## 3. Packet framing

`UserInterface.Business.Services.NofioApi/Packet.cs` — every message is a
9-byte header followed by data (max data length 65535 bytes):

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | Source (`Device` enum: PC=0, Base=1, Head=2, PC2=3) |
| 1 | 1 | Destination |
| 2 | 4 | Sequence (`uint32`, big-endian) |
| 6 | 1 | Flags: bit 0 = start packet, bit 1 = end packet |
| 7 | 2 | Data length (`uint16`, big-endian) |

The first data byte after the header is the `MessageType` (e.g.
`SoftwareUpdateMeta = 135`).

The complete framing, `MessageTag` (transaction/device bits), `Connect`
handshake and heartbeat behavior are documented — with live captures — in
[docs/PROTOCOL.md](../docs/PROTOCOL.md) ("Packet framing" and "Handshake"
sections); they are not repeated here. Relevant facts: tags are
`(destination << 14) | transactionId` (`MessageTag.DeviceMask = 0xC000`,
`TransactionMask = 0x3FFF`, connect transaction id = 1), protocol version 80
is sent by the utility, heartbeats run every 1000 ms.

## 4. The update package

The unit of update is a gzipped tarball. The packaged one ships with the app
in `Resources/Firmware/` (e.g. `nofio1-v2.5.0-001.tar.gz`, ~100 MB) and
contains, alongside a changelog `.md` next to it:

```
base_BOOT.BIN     59,459,968 bytes
head_BOOT.BIN     59,459,968 bytes
SHA1SUMS          (sha1 of each entry)
SHA1SUMS.SIG      512-byte signature over SHA1SUMS
hardware          (contains "nofio1" — hardware compatibility marker)
```

Client-side validation (`UserInterface.Business.Services/Firmware.cs`):
the tar is decompressed (`GZipStream`), every entry is hashed and compared
against the `SHA1SUMS` manifest; the result is a `FirmwareValidity`:

| State | Meaning |
|---|---|
| `Valid` | all manifest entries present and hash-matching |
| `NoManifest` | tar has no `SHA1SUMS` |
| `InvalidManifest` | manifest exists but is malformed |
| `CorruptContent` | hash mismatch |
| `MissingContent` | manifest entries absent from the tar |
| `Unknown` | not checked yet |

The user can also drop/browse a custom `.gz` package (file picker filter
`".gz"`); the packaged one is auto-discovered by newest
`.md` changelog + matching `.tar.gz` in `Resources/Firmware/`.

## 5. Transfer sequence

Flow steps (`FirmwareInstallFlowStep`):
`DevicesNotReady → Start → SelectUpdate → DoUpdate → VerifyUpdate → Complete`
(plus `FailedUpdate`).

In `DoUpdate`, `SendFirmwareToDevice(connection, firmwarePath, device, progress)`
is started for **both devices in parallel** (`Task.WhenAll`), with separate
progress bars (BaseTask / HeadTask) and the warning "Don't unplug either of
your nofio devices."

Notable details from `FirmwareInstallFlow.cs`:

- The opened file is the **whole `.tar.gz`** — `File.Open(firmwarePath)` is
  streamed raw; the app never extracts `base_BOOT.BIN` / `head_BOOT.BIN`
  itself. Unpacking, signature checks and choosing the correct image happen
  **on the device** (status strings "Unpacking update...", "Sending
  firmware...", "Preparing for update...").
- Message sequence per device:

```
SoftwareUpdateMeta (type 135)
  ├─ FileType      = SoftwareFileType.ImrOs (2)
  ├─ PacketCount   = ceil(fileSize / 65523)   (max 65523)
  └─ FinalPacketSize = fileSize % 65523
        → device replies Ack
SoftwareUpdateData × N (type 137)
  ├─ PacketIndex   = ushort, big-endian
  └─ Data          = 65523-byte chunk (last chunk smaller)
SoftwareUpdateComplete (type 138)
  ├─ ReturnCode    = byte
  └─ Message       = ASCII string
```

- Progress reaches 100 % when all chunks are sent; "Unpacking update..." is
  reported while waiting for the device-side `SoftwareUpdateComplete`.
- In `VerifyUpdate`, the units have rebooted and their TCP connections drop.
  The app waits (progress "Almost there!"; base/head recovery-mode banners
  shown here) until both devices reconnect on their USB networks
  (`AreDevicesReady` changes re-trigger
  `HandleDevicesReadyOnVerifyUpdate`), then sends a final
  `SoftwareUpdateComplete` to both devices in parallel; if both sends
  succeed, the step `Complete` is reached.
- Failure paths: `NakException` with codes
  `129 IncorrectSoftwareUpdatePacket`, `130 IncorrectSoftwareUpdateFile`;
  generic errors are shown as "An unknown error occurred. Error code N".
  If the package exceeds 65523 packets: "The firmware package is too big!".
- Recovery mode: if a unit was detected in recovery mode
  (`Base/HeadRequiresManualRestart`), it powers off after the update and the
  user is told to power it back on manually ("...it will turn off once the
  update is complete. Please power it back on manually once it shuts down.").

### `SoftwareFileType` values

From `SoftwareFileType.cs` — the update channel accepts more than the OS
image:

| Value | Name | Notes |
|---|---|---|
| 0 | LinuxUb | |
| 1 | FpgaBit | FPGA bitstream |
| 2 | ImrOs | full OS image — used by the install flow |
| 3 | ReleaseZip | |
| 4 | Firmware | |
| 5 | SupportReport | diagnostics extraction |
| 6 | FoveationConfig | |
| 7 | Nothing | |
| 8 | NothingReboot | |

## 6. Version reporting and fallback firmware

`SoftwareVersion` (type 134) returns an ASCII `key=value` blob (one entry per
line). Keys observed in the client (`SoftwareVersion.cs`,
`NofioState.cs`):

| Key | Use |
|---|---|
| `imr_software` | exact version match against the update package name |
| `release` | alternate match, prefix `release/` |
| `build` | alternate match |
| `is_fallback` | `1` → the unit booted its fallback image |

When `is_fallback=1` on either unit, `NofioState.IsBaseOnFallback` /
`IsHeadOnFallback` become true and the settings notification button turns into
**"Recover Firmware"** (`SettingsNotificationButton.cs`), which opens the same
install flow. A unit in this state is recoverable by an ordinary install —
consistent with `IsOnFallbackFirmware()` parsing.

## 7. Related device-update paths (not the main flash)

- `Setup.UpdateParadeFw` (protobuf `Imr.Proto.Setup`, field 29) — updates the
  WiFi (Parade/QCA) firmware on the device; distinct from the ImrOs flash.
  Marked brick-risk in `docs/PROTOCOL.md`.
- `Setup.Remove` — deletes `FIRMWARE` / `FPGA` / `BOARD` / `FOVEATIONCONF` /
  `IMR_CONTROLLER` files from device storage (destructive; does not respect
  the fallback-image protection).
- `DeviceCommand.Reboot` / `RestartController` — used after updates and in
  the tools window.
- `ToolsWindow` → "Save Diagnostic Report" (`SupportReportFlow`) pulls
  diagnostics from the devices (`SoftwareFileType.SupportReport`).

### 7.1 Support report: a device → PC file-transfer channel

The same `SoftwareUpdate*` message family also works **in reverse**, as a
client-driven file request (verified in `SupportReportFlow.cs`):

```
PC  → device : SoftwareUpdateMeta { FileType = SupportReport (5),
                                     ActualFileName = "meta" }      ← request
device → PC  : SoftwareUpdateMeta { PacketCount = N }                ← ready, N chunks
PC  → device : SoftwareUpdateMeta { FileType = SupportReport,
                                     PacketCount = i }              ← "send chunk i"
device → PC  : SoftwareUpdateData { PacketIndex = i, Data = ... }    ← content
```

The client controls both the `FileType` and the `ActualFileName`, and
`Setup.Remove` (`Imr.Proto.Setup`) names device-storage files `FIRMWARE`,
`FPGA`, `BOARD`, `FOVEATIONCONF`, `IMR_CONTROLLER` — likely the same
namespace. This makes the channel a candidate for reading device storage
over TCP (no hardware access needed). Realistic expectations:

- Files served are probably the **stored (encrypted)** images — which we
  already have — so a dump would be confirmatory rather than new material.
- The support report **content itself** (logs, paths, version strings,
  process names) is likely the most informative readable artifact and may
  reveal how the device-side update daemon is structured.
- Decrypted RAM is not reachable through this channel; nothing in
  `SoftwareFileType` points at runtime memory.

Suggested low-risk experiments (requests only; worst case is a `Nak`):

1. Capture a legitimate support report via "Save Diagnostic Report" and
   inspect its contents.
2. Request `FileType = SupportReport` with different `ActualFileName` values
   (`FIRMWARE`, `BOARD`, ...) to see whether names resolve freely.
3. Request other file types (`Firmware` (4), `ImrOs` (2), `FpgaBit` (1)) with
   `ActualFileName = "meta"` and plausible names, and map what the device
   is willing to serve.

### 7.2 Live verification (base, firmware v2.5.0)

Experiments 1-3 above were performed against a live base station
(2026-10-02, `nofio_probe.py raw 135 ...`):

| Request | Reply | Meaning |
|---|---|---|
| `FileType=5`, name `meta` | meta `chunks=0 final=45279` | report generated on demand (size varies between requests) |
| chunk request (`FileType=5`, `PacketCount=i`) | `SoftwareUpdateData`, 65523 B payload | client trims the single packet to `final` size |
| `FileType=5`, any other name | **Nak 129** (IncorrectSoftwareUpdatePacket) | name is validated — no free file resolution |
| `FileType` = 1, 3, 4, 6, 8 | **Nak 130** (IncorrectSoftwareUpdateFile) | file types other than SupportReport are not served |
| `FileType=2` (ImrOs), name `meta` | **Ack** | this is the *upload* channel start (no data followed; session dropped) |
| `FileType=7` (Nothing) | meta with a small dynamic size (21-561 B) | appears to be a status/ephemeral blob, not a file |

So the reverse channel is **not a generic file reader**: only the support
report (exact name `meta`) is served, and everything else is refused with
the two dedicated `Nak` codes. The report itself is a **ZIP** containing:

- `support-report.txt` — system info, versions, configuration dumps,
  process listing, mounts, boot `dmesg`, `journalctl`
- `local-logger.csv` — periodic telemetry

It turned out to be highly informative (see §9.0): the process listing
reveals the whole device-side architecture, including the update daemon
itself (`/usr/bin/imr_controller`).

## 8. Implications for the Linux reimplementation

Everything needed to flash from Linux is in the client:

1. Wait for both USB networks (`192.168.3.0/24`, `192.168.4.0/24`).
2. TCP-connect to `192.168.3.1:34566` and `192.168.4.1:34568`, do the
   `Connect` handshake (protocol version 80).
3. Optionally validate the tarball against its `SHA1SUMS`.
4. For each device, send `SoftwareUpdateMeta` → N × `SoftwareUpdateData`
   (65523-byte chunks) → await `SoftwareUpdateComplete`; then send
   `SoftwareUpdateComplete` back and re-check `SoftwareVersion`.

No VirtualHere involvement is required for the update; VirtualHere is only
used for the HMD streaming path.

## 9. Device-side update mechanism (updated with boot-image findings)

Static analysis of the shipped `base/head_BOOT.BIN`
([boot_image_format.md](boot_image_format.md)) resolved much of the earlier
speculation. Confirmed facts first, then the remaining hypotheses.

### 9.0 Confirmed device architecture

Static analysis of the shipped `base/head_BOOT.BIN`
([boot_image_format.md](boot_image_format.md)) resolved much of the earlier
speculation, and the live support report (§7.2) then revealed the rest.

Both nofio units are **Xilinx Zynq UltraScale+ MPSoC** boards (Trenz
**TE0803** SoM on a custom IMRNext carrier — per the FPGA bitfile name
`nofio1-te0803-03-3ae11-a_mipi_base`) booting this chain, all components
AES-encrypted (eFUSE key) and RSA-4096 signed:

```
BootROM → FSBL (OCM) → PMU fw + FPGA bitstream + ATF bl31 → U-Boot → 42 MB
OS image ("linux.ub" partition) loaded at DDR 0x10000000
```

The OS is **Buildroot Linux** — *not* QNX as previously assumed:

- Kernel `Linux 5.10.0-nofio` (aarch64, built with gcc 9.2.1), booted with
  `root=/dev/ram0 bootmode=qspi` — the whole system runs from an
  **initramfs in RAM**.
- Process tree (from the support report): systemd, `imr_controller.service`
  (**`/usr/bin/imr_controller base` — this is the update daemon and the TCP
  protocol server**), `dnsmasq@usb0`, `hostapd@wlp1s0` (QCA WiFi, 10.0.0.0/28),
  avahi publishing `IMR VirtualHere _imrusb._tcp 7575` (mDNS), `dropbear -F -R -s`
  (SSH, key-only), plus Jim-Tcl helpers (`ledman`, `wireless-checkd`,
  `systemwatchd`, `imr_thermal_mon`, `imr_video_bridge_mon`).
- Persistent storage on separate MTD partitions: `/dev/mtdblock1` (128 KB →
  `/settings`), `/dev/mtdblock2` (20 MB → `/data`); the rest is RAM.
- Build config (`/etc/build.conf`): `FINAL_SWUPDATE_KEYS=1`,
  `FINAL_SSH_KEYS=1`, `ENCRYPTION_AUTHENTICATION=1`, `FULL_AUTHENTICATION=1`,
  `ENCRYPT_PAIRING=1`, `RELEASE_OPTION=PRODUCTION_AND_USER_FINAL` —
  production units ship with signature/encryption enforcement on.
- Wireless: QCA2066 for the 2.4/5 GHz link side plus 60 GHz Wilocity-family
  firmware on board (`wil6210.fw`, `wil6436.fw` / "Talyn") — the head-to-base
  streaming link is WiGig-class.
- The OS partition is stored at a **fixed flash offset 0x10A0000**, with an
  erased (0xFF) gap between the boot chain and it — the update file is a raw
  flash image over a fixed partition map.
- Base and head differ mainly in the FPGA bitstream (7.8 MB vs 5.5 MB) and
  the OS image bytes; the boot chain is per-role but structurally identical,
  and the same RSA key pair signs all images.
- The 512-byte `SHA1SUMS.SIG` matches an RSA-4096 signature, but it does
  **not** verify with the boot image keys — a separate update key must exist
  inside the encrypted OS image (consistent with `FINAL_SWUPDATE_KEYS=1`).
  The utility never checks `.SIG` itself (only the `SHA1SUMS` hashes);
  signature enforcement, if any, is device-side.

### 9.1 Who receives and installs the update

The `SoftwareUpdate*` handlers live in the **running OS image itself**: the
units accept an ordinary TCP session (ports 34566/34568) while fully booted,
which means the update daemon is part of the system being replaced. The
plausible pipeline inside the device:

```
SoftwareUpdateMeta  →  allocate staging buffer / file for N chunks
SoftwareUpdateData  →  append chunk[PacketIndex]; reject gaps (Nak 129)
last chunk          →  gunzip → untar → verify SHA1SUMS against entries
                     → verify SHA1SUMS.SIG (embedded pubkey)
                     → check `hardware` marker ("nofio1")
                     → pick own image: base_BOOT.BIN or head_BOOT.BIN
                     → write to the *inactive* slot / staging file
SoftwareUpdateComplete (device→PC) → ReturnCode + human-readable Message
reboot              →  bootloader verifies and boots the new image
```

Evidence: the app ships the tarball untouched (no client-side extraction),
the client UI shows "Unpacking update..." while *waiting on the device*, and
the dedicated `Nak` codes `129 IncorrectSoftwareUpdatePacket` /
`130 IncorrectSoftwareUpdateFile` imply device-side structural and
content-level validation. `Setup.Remove` deleting `FIRMWARE` / `FPGA` /
`BOARD` / `FOVEATIONCONF` / `IMR_CONTROLLER` from "device storage" shows the
OS-level storage keeps components as named files (these names are likely the
OS-level view; the QSPI boot image itself is a single raw blob, see the note
below).

> Confirmed: the shipped `*_BOOT.BIN` files are complete flash images
> (headers + encrypted partitions + erased gap), so the device-side update
> almost certainly rewrites the whole flash image and reboots — consistent
> with the observed "transfer → silence → reboot" flow.

### 9.2 Why send one tarball to both devices

Since the package contains both `base_BOOT.BIN` and `head_BOOT.BIN` plus a
single signed manifest, the simplest consistent design is: both device roles
run the same update handler, each unit picks the image whose name matches its
own role (`base_` / `head_` prefixes), and the single `SHA1SUMS.SIG` covers
the whole package. The `hardware` file ("nofio1") is most likely a device
family check so a future nofio2 package is rejected by nofio1 units (Nak 130).

### 9.3 Signature verification

`SHA1SUMS.SIG` is exactly 512 bytes — consistent with a raw 4096-bit RSA
signature over the `SHA1SUMS` manifest. The boot images embed two RSA-4096
public keys, but the `.SIG` does **not** verify with either of them
(tested with `scripts/parse_boot_bin.py` output), so the update uses a
separate key pair whose public half lives inside the encrypted OS image.
The hypothesis stands: the device may refuse an unsigned/modified package
(`IncorrectSoftwareUpdateFile`), and since the utility never checks `.SIG`
itself, only a live test with a tampered manifest answers whether
enforcement actually happens. **If verification is enforced, custom firmware
packages require bypassing it in the running OS — and the boot chain itself
(eFUSE AES + RSA) blocks replacing the OS with an unsigned one.**

### 9.4 Dual image / fallback and recovery mode

The `is_fallback=1` line in `SoftwareVersion` and the "Recover Firmware"
notification imply a **two-image scheme**: a main image and a fallback image
(the bootloader boots the fallback when the main image fails verification or
fails to start). The recovery-mode banners ("...it will turn off once the
update is complete. Please power it back on manually...") suggest a third
state: a minimal recovery environment (likely the fallback image, or a
bootloader-mode server) that accepts the same update protocol but, after
flashing, powers off instead of rebooting — hence the manual power cycle.
This also explains how a factory-fresh or wiped unit can always be
re-flashed: the recovery path cannot be overwritten by a bad update.

### 9.5 The chicken-and-egg question

"Is it the firmware they run that lets them receive and install the
package?" — **yes, with a bootstrap chain**: the running OS image (daemon)
receives and stages the new image, but the Boot ROM + FSBL are what decrypt,
verify and launch images at boot (eFUSE AES key + vendor RSA keys, see
[boot_image_format.md](boot_image_format.md)), and the fallback/recovery
image is what saves the unit when the running image is the problem. An update
most likely rewrites the **whole flash image** (the shipped `*_BOOT.BIN` is a
complete flash dump including headers and the erased gap) but cannot replace
the Boot ROM's keys — which is also why the units are hard to permanently
brick through this channel. Note that "the bootloader" in the ZynqMP chain
(FSBL) *is* part of the shipped image and therefore updated with it; only the
mask-ROM verification keys are immutable.

### 9.6 What we would expect to observe live

Concrete predictions a dynamic capture could confirm or falsify:

1. After the last `SoftwareUpdateData`, the device goes silent ("Unpacking")
   for a while, then sends `SoftwareUpdateComplete` — then the TCP
   connection drops (reboot), not before.
2. No retransmission protocol: the client never resends a chunk; a failed
   transfer aborts the whole install.
3. During reboot the USB network interface disappears and re-enumerates; the
   app's reconnect gate fires when the interface comes back.
4. `SoftwareVersion` right after update reports the new version with
   `is_fallback` absent or `0`.
5. Sending a tarball with a tampered `SHA1SUMS` yields `Nak 130`
   (IncorrectSoftwareUpdateFile) at or after the final chunk.

## 10. Open questions (dynamic analysis needed)

- Why the head's **right-hand** USB-C port specifically (hardware wiring).
- USB identity of the head's network interface — the base enumerates as
  `04b3:1234` ("Nofio Wireless Base", IMRNext, CDC network class; verified
  live); the value `04b3:4010` previously recorded in the docs likely refers
  to the head unit or another mode.
- Confirm or falsify the speculations in §9 with a live capture
  (`tcpdump` on `192.168.3.0/24` and `192.168.4.0/24` during an update,
  plus `lsusb`/`ip link` before/after).
- ~~Full extraction of the "QNX6 filesystem" in `head_BOOT.BIN`~~ — **moot**:
  the OS is Buildroot Linux (§9.0), the QNX6 lead was a binwalk false
  positive, and the OS partition is AES-encrypted with the device's eFUSE
  key ([boot_image_format.md](boot_image_format.md)). Device-side ground
  truth now requires dynamic analysis (update capture, UART/JTAG on the
  TE0803 SoM, or the report/SSH channels).
- Whether the device verifies `SHA1SUMS.SIG` at all, and with which key
  (the boot image keys do not verify it; `FINAL_SWUPDATE_KEYS=1` suggests
  dedicated update keys — the tampered-manifest upload test remains open).
- ~~Whether the reverse file-request channel (§7.1) can read device storage
  beyond the support report~~ — **answered live (§7.2)**: no, names are
  validated (`Nak 129`) and non-report file types are refused (`Nak 130`).
- Whether the fallback image lives in flash beyond the shipped image end
  (0x38B4980) or in the erased gap region.
- Whether `Setup.UpdateParadeFw` (WiFi/QCA2066 firmware) shares this flash
  path or targets the WiFi module's own storage.
- `dropbear` SSH runs on the base (key-only, `FINAL_SSH_KEYS=1`) — with
  which authorized keys, and on which address/interface it listens.
