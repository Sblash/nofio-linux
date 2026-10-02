# Communication Protocol

This document describes the communication protocols used by the Nofio wireless VR adapter.

> **Disclaimer:** Only sections marked as **[Verified]** are based on direct analysis of concrete artifacts (binaries, configuration files, PDB symbols, USB descriptors). Sections marked as **[Hypothetical]** are design targets or speculation that has not been confirmed by dynamic reverse engineering. The Nofio USB protocol has not been captured or analyzed; all message formats below the VirtualHere layer are unknown.

## Overview

The Nofio system uses multiple layers of communication:

1. **USB Layer** - Physical connection between PC and Base Station **[Verified]**
2. **Network Layer** - USB-over-IP via VirtualHere **[Verified]**
3. **WiFi Layer** - Wireless communication between Base Station and Head Adapter **[Hypothetical]** (chipset identified, protocol unknown)
4. **Device Layer** - Communication with Valve Index headset **[Hypothetical]** (handled entirely by VirtualHere tunneling)

## Current Implementation (VirtualHere-based) **[Verified]**

### USB Interface

- **VID:PID:** 04b3:4010 (IBM Corp. IMRWirelessVR)
- **Interface Class:** CDC Ethernet (USB CDC-ECM or RNDIS)
- **Driver:** `cdc_ether` / `usbnet` on Linux

#### USB Descriptors

The device descriptor values below were extracted from the binary analysis of `nofioUtility.exe` and confirmed by the `lsusb` output described in the original Linux guide.

```c
// Device Descriptor
struct UsbDeviceDescriptor {
    uint8_t  bLength;             // 18
    uint8_t  bDescriptorType;     // 1 (DEVICE)
    uint16_t bcdUSB;              // 0x0200 (USB 2.0)
    uint8_t  bDeviceClass;        // 2 (Communications)
    uint8_t  bDeviceSubClass;     // 0
    uint8_t  bDeviceProtocol;     // 0
    uint8_t  bMaxPacketSize0;     // 64
    uint16_t idVendor;            // 0x04b3
    uint16_t idProduct;           // 0x4010
    uint16_t bcdDevice;           // 0x0100
    uint8_t  iManufacturer;       // 1 (IBM Corp.)
    uint8_t  iProduct;            // 2 (IMRWirelessVR)
    uint8_t  iSerialNumber;       // 3
    uint8_t  bNumConfigurations;  // 1
};
```

### Network Configuration

- **IP Address (Base Station):** 192.168.3.1
- **Port:** 7575
- **Subnet:** 192.168.3.0/24
- **Protocol:** VirtualHere proprietary USB/IP

#### VirtualHere Configuration (vhui.ini)

Extracted from the `vhui.ini` file bundled with the Nofio utility (the
EasyFindId/Pin values are device-specific pairing credentials and have been
redacted; get them from the `vhui.ini` shipped with the official Nofio
utility, in the `Resources` folder of its installation directory):

```ini
[General]
HideMenuItems=VHTBI
MainFrameWidth=400
MainFrameHeight=250
ReverseLookup=1
AutoFind=1
SSLReverseLookup=1

[Transport]
EasyFindId=<device-specific, redacted>
EasyFindPin=<device-specific, redacted>

[Settings]
ManualHubs=192.168.3.1,192.168.3.1,192.168.3.1,192.168.3.1:7575
```

### VirtualHere Protocol

VirtualHere uses a proprietary protocol for USB-over-IP. The protocol is not publicly documented. What is known from the configuration:

1. **Handshake Phase**
   - Client connects to server at 192.168.3.1:7575
   - Authentication via EasyFindId and EasyFindPin
   - Device enumeration

2. **Data Transfer Phase**
   - USB packets encapsulated in IP packets
   - Bidirectional communication
   - Device control and data transfer

> The detailed VirtualHere wire protocol is proprietary and has not been reverse engineered. No packet captures have been performed. Any further detail would require Wireshark/tcpdump analysis during active sessions.

## Direct TCP Control Protocol (nofioUtility ↔ Base/Head) **[Verified - decompiled source]**

> **Source:** static reverse engineering of the decompiled `nofioUtility.exe`
> (C#, `UserInterface.Business.Services.NofioApi.*`). All frame formats below are
> taken directly from the decompiled encoder/decoder code, not from packet
> captures. Dynamic confirmation against real hardware is pending; a ready-made
> client is provided in `scripts/nofio_probe.py`.

The utility app talks to the stations on a dedicated TCP control channel,
independent of VirtualHere (which only tunnels the headset's USB devices).

### Endpoints

| Station | Address            | Port  | Client identity (source byte) |
|---------|--------------------|-------|-------------------------------|
| Base    | `192.168.3.1`      | 34566 | `PC` (0)                      |
| Head    | `192.168.4.1`      | 34568 | `PC2` (3)                     |

Device bytes: `PC = 0`, `Base = 1`, `Head = 2`, `PC2 = 3`, `Max = 4`.

### Other open ports on the base (live scan, 192.168.3.1, 2026-10-02)

Full TCP scan (65535 ports) finds only four listeners:

| Port | Service | Notes |
|------|---------|-------|
| 22 | `dropbear_2019.78` | SSH, **publickey only** (`-s` disables passwords); `root` login exists but requires a vendor key (`FINAL_SSH_KEYS=1`, `/etc/build.conf`). Host keys: ssh-rsa + ecdsa-nistp256 (per-device). The utility **never uses SSH** — no SSH client code, libraries, or port-22 references exist anywhere in the decompiled app. Its only related behavior is `ImrDevToolMonitor`: a WMI watcher for a vendor process named `imr_devtool` on the PC; while it runs, `NofioConnection` defers its own base/head sockets. `imr_devtool` (never distributed) is the presumed consumer of this SSH channel — the factory/developer tool. The authorized public keys are not readable through the control protocol |
| 5355 | LLMNR | `systemd-resolved` |
| 34567 | unknown | open but does not answer the control-protocol `Connect` handshake; purpose undocumented |
| 34566 | control protocol | documented above |

VirtualHere's 7575 was **closed** in this state (base unpaired, head off) — the
server likely starts only when the wireless link is up. mDNS (unicast to the
device's avahi) enumerates the advertised services:

| Service | Instance | Endpoint |
|---|---|---|
| `_ssh._tcp.local` | `imr-nofio1` | `imr-nofio1.local:22` (A 192.168.3.1) |
| `_sftp-ssh._tcp.local` | `imr-nofio1` | `imr-nofio1.local:22` |
| `_imrusb._tcp.local` | `IMR VirtualHere` | `imr-nofio1.local:7575` (advertised even while closed) |

### Readable messages via RequestStatus (live sweep, base fw v2.5.0)

Sending `RequestStatus(body=u16 type)` for every known type and watching the
reply (all read-only) yields:

| Requested type | Reply |
|---|---|
| 129 BaseStatus | `Protobuf` (140) wrapping BaseStatus |
| 131 HMDSuspended | `00` (not suspended) |
| 145 Configuration | **`Protobuf` with the full configuration dump** (below) |
| 146 TestFrameGenerator | empty `Protobuf` |
| 147 VirtualHere | `Protobuf`: field1 = serial, field3 = `UNLICENSED` (VirtualHere server license status) |
| 149 PeerInfo | `Protobuf` (2 fields) |
| 153 VideoStatus | `Nak(VideoNotConnected)` (no head) |
| 130, 132-133, 136, 139, 141-144, 148, 150, 152, 154-158 | `Nak(InvalidStatusRequest)` |
| 64-67 | `Nak(InvalidStatusRequest)` (events, not pollable) |

#### Configuration dump (type 145)

The reply is the `Configuration` protobuf
([docs/protos/nofio.proto](protos/nofio.proto)): sections `DefaultConf`,
`FactoryConf`, `UserConf`, `SystemConf`, `ActualValues`, each a list of
key/value items. Observed on the base (2026-10-02), most informative keys:

```
FactoryConf:  hw_serial = 240104-02E3-NI-b
SystemConf:   imr_controller_log_level = 1, wi_channel = 13, wi_country = IT

DefaultConf (highlights):
  # streaming bridge (base -> head over the 60 GHz link)
  bridge = wi  bridge_protocol = udp  bridge_port = 44444
  packet_size = 7828  max_packet_blocks = 1280
  bridge_drop_seconds = 20  disable_bridge = 0
  latency_target = 6000000        # base (head: 11000000)
  rate_control_mode = dynamic  rate_control_kp = 50  ki = 90  kd = 20
  rate_control_hold_time = 5  recovery_time = 20  netrate_mult_percent = 1000
  tx_queue_target = 2800000  irq_coalesce = 57
  # wireless (wi = the base-head link, QCA2066/WiGig)
  wi_mode = ap  wi_ap_mode = hostapd  wi_channel = 77  wi_channel_default = 77
  wi_country = US  wi_ssid = auto  wi_psk = auto  wi_addr = 10.0.0.1/28
  wi_hw = bdwlan02g.e66  wi_version = 5.2.0.220S  wi_owe_mode = 0
  # USB network (the host-side gadget interface)
  usb = proxy  usb_type = virtualhere  usb_compression = 0  usb_kmem = 0
  usb0_addr = 192.168.3.1/24  usb0_dir = peripheral  usb0_port = B  usb0_mtu = 15300
  usb1_addr = none  usb1_dir = peripheral  usb1_mtu = 15300
  # foveated encoding (Index eye tracking)
  foveation_en = 1  codec_subsample_mode = 3
  fov_luma_intercept/slope = 420 / -3096   fov_chroma_intercept/slope = 420 / -3096
  fov_luma_min/max_coeffs = 4 / 48         fov_chroma_min/max_coeffs = 4 / 48
  fov_offset_left_x/y = 12 / 30  fov_offset_right_x/y = -12 / 30
  # misc
  platform = vr  eth0/1/2_* = (none/1500)  local_log_poll_rate = 1000
  local_log_size = 36000  imr_controller_log_level = 2  host_manager = 0
  pirate_mode = 0  pirate_x_offset = 52  eth0_addr = none  eth2_dhcp = 1
```

The `bridge_port = 44444` UDP stream (7828-byte packets) matches the bridge
statistics exposed in the support report (`src_port: 44444`), and
`BaseStatus.ChannelFreq = 6015` (live) is consistent with a 60 GHz-band
channel — together these document the video path: raw video flows over UDP
44444 on the wireless link while control uses TCP 34566.

#### Head vs base configuration (live, paired link, fw v2.5.0)

With the head on and paired, the same reads work against the head through
base routing (`--target head`). `HeadStatus` additionally reports the video
link state (live sample: Wireless MCS 7 both ways, RSSI 49,
PeakUncompressedVideoTXSpeed 2.06 Gbps, head batteries 1 %/1 %, head FPGA
bitfile `nofio1-te0803-03-4ae11-a_dp_head`). The configuration difference
between the roles is the interesting part:

| Key | Base | Head | Meaning |
|---|---|---|---|
| `wi_mode` | `ap` | `sta` | base is the 60 GHz AP, head is the station |
| `wi_addr` | `10.0.0.1/28` | `10.0.0.2/28` | wireless link addressing |
| `usb0_addr` | `192.168.3.1/24` | `192.168.4.1/24` | PC-facing gadget networks |
| `usb1_dir` | `peripheral` | `host` | the head's second USB port is a **USB host** — presumably where the Valve Index connects |

Note: requesting a support report from the **head** (via base routing,
paired link) currently fails device-side with `SoftwareUpdateComplete`
return code 0 and message `failed to open /tmp/support-report.zip`
(reproduced twice) — the head cannot generate the report zip (its `/tmp`
appears too small or in a degraded state). The error message itself is
informative: the device-side report generator writes to
`/tmp/support-report.zip` before serving it, confirming the
`/bin/support-report` script flow seen in the base process list.

Keys that exist **only on the base** (the encoder side): all `rate_control_*`
(PID bitrate adaptation), `packet_size = 7828`, `max_packet_blocks = 1280`,
all `fov_*` foveation parameters, `foveation_en`.

Keys that exist **only on the head** (the display side):
`video_buffer_delay = 10500000`, `video_buffer_catchup/margin` (ns — the
display-side buffering), `loss_time = 950`, `cache_time`,
`bridge_error_color = tracking_grey`, `additional_splash_screen_dir =
/etc/sink/frame`, `source_overlay_*`, `dp_vswing = 3` (DisplayPort drive
strength), `force_ycc*`, `sync_gpio = 416`,
`wireless_blocked_threshold = 60`.

In short: **encoding decisions (rate control, foveation, packetization) live
on the base; display timing, buffering and the DisplayPort link live on the
head.** The `usb1_dir = host` finding also explains the head's two USB-C
ports: one gadget port toward the PC, one host port toward the headset.

### Packet framing (big-endian)

```
offset  size  field
0       1     source device
1       1     destination device
2       4     sequence (uint, increments per packet; receiver drops the
              connection with PacketSequenceError on gaps)
6       1     options: bit0 = start-of-message, bit1 = end-of-message
7       2     payload length (max 65535)
9       ...   payload chunk
```

Messages larger than 65535 bytes are chunked across packets (start flag on the
first, end flag on the last, sequence increments per packet).

### Message format (reassembled payload)

```
offset  size  field
0       2     tag (ushort): (device << 14) | transaction id (14 bit)
2       2     message type (ushort)
4       ...   message body
```

The tag identifies the request/reply pair: replies echo the tag of the request.
Tag `0` is broadcast (used for heartbeats). The connect handshake uses
transaction id 1; regular requests take per-destination transaction ids.

### Handshake (dynamically verified against real hardware)

1. TCP connect
2. Client sends `Connect` (type 2) with body `uint32 protocol version` (the utility
   uses **80**) and tag `(destination << 14) | 1`
3. The station replies with its **own `Connect`** (same tag, body = its protocol
   version — the base reports 80). The client must answer `Ack` (type 0, empty
   body, echoing the station's tag). **The station does not Ack the client's
   Connect** — the connection is established once the client has acked the
   station's Connect
4. Keep-alive: client sends `Heartbeat` (type 4, body `uint32 0`, tag 0) every
   1000 ms. The station echoes each heartbeat with body = **3000** (0x0BB8,
   presumably its keep-alive timeout in ms); an idle connection is dropped after
   roughly 2-3 seconds without traffic
5. A `Nak` (type 1, body `uint32` error code) rejects the connect (e.g.
   `OldVersion` on protocol mismatch). The utility treats station versions
   below 49 as remote-old

### Command messages

| Type | Name                 | Body (big-endian)                            | Reply |
|------|----------------------|----------------------------------------------|-------|
| 0    | Ack                  | empty                                        | — |
| 1    | Nak                  | `uint32` error code (see below)              | — |
| 2    | Connect              | `uint32` protocol version                    | Ack |
| 3    | Disconnect           | empty                                        | — |
| 4    | Heartbeat            | `uint32` next (client sends 0)              | heartbeat echo, body 3000 |
| 128  | RequestStatus        | `uint16` expected reply message type        | message of the requested type, same tag (verified live: requesting type 134 returns the firmware version) |
| 134  | SoftwareVersion      | `uint16` length + version string             | — |
| 140  | Protobuf             | `uint8` packet count + `uint16` content type + protobuf bytes | — |

`RequestStatus` is the general query mechanism: e.g. requesting type 134
(SoftwareVersion) makes the station answer with a `SoftwareVersion` message
whose body is `[uint16 length][version string]` (multi-line, the utility splits
it on `\n` into a key=value dictionary). The utility also requests
`SoftwareVersion` on connect to compute `IsFirmwareUpToDate` and
`IsOnFallbackFirmware`.

Message types carried inside `Protobuf` (type 140) include `BaseStatus` (129),
`HeadStatus` (130), `Setup` (144), `Configuration` (145) and `Pairing` (158,
requires protocol ≥ 76). The protobuf field schemas live in the separate
`ProtobufTypes` assembly and are not yet documented.

### Write operations and risk levels

The protocol is not read-only. Sending arbitrary messages with `raw` can
change device state, and a few paths are genuinely dangerous:

| Level | Operations | Effect / recovery |
|---|---|---|
| Safe | `RequestStatus`, `SoftwareVersion`, heartbeats, malformed bodies | rejected with `Nak` or disconnect, no state change |
| Reversible | `Setup.WirelessCountry/Channel`, `Setup.Pair`, `Setup.Reboot`, `RestartWireless/Controller` | config/behavior changes; worst case the wireless link breaks and needs re-setting over USB or factory reset |
| Destructive | `Setup.FactoryReset` (Force/All/Data), `Setup.Remove` (deletes FIRMWARE / FPGA / BOARD / FOVEATIONCONF / IMR_CONTROLLER files from device storage), `Pairing` Ssid/Psk overwrite | wipes configuration or removes firmware files from storage |
| Brick risk | `SoftwareUpdateMeta` -> `SoftwareUpdateData` -> `SoftwareUpdateComplete` (TCP firmware flashing), `Setup.UpdateParadeFw`, interrupted/corrupted transfers | wrong or interrupted flash can leave a unit unbootable |

Mitigations (verified in the decompiled utility and on hardware): the units
keep a **fallback firmware image** (the `is_fallback` line in SoftwareVersion,
`IsBaseOnFallback`/`IsHeadOnFallback` in the utility, its "Recover Firmware"
flow and `FirmwareValidity` checks); the device validates update transfers
(`Nak` IncorrectSoftwareUpdatePacket/File, the app checks SHA1SUMS manifests)
and rejects nonsense with `Nak`. A fallback image however does NOT protect
against `Setup.Remove` on firmware files, `FactoryReset(Force/All)`, or a
flash interrupted at the wrong moment. Real damage requires deliberately
sending a well-formed destructive sequence — a typo'd query just gets `Nak`'d
and sequence errors only drop the connection.

### Nak error codes (`uint32`)

`0` None, `1` OldVersion, `2` NoPath, `3` AlreadyConnected, `64` InternalStart,
`128` InvalidStatusRequest, `129` IncorrectSoftwareUpdatePacket,
`130` IncorrectSoftwareUpdateFile, `131` SyncRebootFailed, `132` WirelessChanged,
`133` InvalidRequest, `134` IncorrectResponse, `135` ExceptionCaught, `136` Busy,
`137` Timeout, `138` VideoNotConnected, `139` VdmaNotIncluded, `140` SyncShutdownFailed.

### Other observed message types (device → PC, utility listens)

`BaseStatus` (129), `HeadStatus` (130), `HMDSuspended` (131), `Statistics` (136),
`VideoStatus` (153), `AudioInfo` (154), `PeerInfo` (149), `EDID` (148) and the
video/FPGA events (64–67, 139, 141–143, 152, 155–157). Firmware updates use
`SoftwareUpdateMeta` (135) → `SoftwareUpdateData` (137, 65523-byte chunks) →
`SoftwareUpdateComplete` (138).

### Base → Head routing (dynamically verified)

The base acts as a router for the control protocol: packets sent on the base
TCP connection with `Destination = Head (2)` are forwarded to the head adapter
over the wireless link, and the head's replies come back on the same TCP
connection (tag device-bits = Head). The full Connect exchange works with the
head through the base — no direct network path to 192.168.4.0/24 is needed.

Session rules (all verified live, base firmware v2.5.0):

- The routing is **transparent**: a head-only session needs NO base handshake —
  connect to the base endpoint and address packets to the head directly
- **One TCP connection talks to one device**: mixing base-directed requests
  into a head-routed session makes the base send `Disconnect` and drop the
  connection (this is why the original utility uses two separate sockets)
- `RequestStatus{PeerInfo}` on the base returns a protobuf with the wireless
  peer: field 1 = 2 (`Device.Head`), field 2 = 80 (its protocol version)
- The base answers `BaseStatus` and `SoftwareVersion` itself, but refuses
  head-only queries with `Nak(InvalidStatusRequest)`: `HeadStatus`,
  `Statistics`; `VideoStatus` is refused with `Nak(VideoNotConnected)` when no
  video source is connected — query the head for those (via the base)
- 192.168.4.0/24 is NOT routed by the base at the IP layer (it answers
  `ICMP Destination Net Unreachable`); the head's direct address only works
  when the head is locally connected (see `IsHeadLocal` in the utility)
- Packet sequence counters are tracked **per source device**: the base's and
  the head's packets arrive interleaved on the same TCP connection, each with
  its own counter

### Byte-level walkthrough (real captured traffic)

Everything is big-endian. One full status query against the base:

```
PC -> Base   Connect (handshake, step 1)
  packet : 00 01 00000000 03 0008
           │  │  │       │  └─ payload length: 8
           │  │  │       └─ options: 03 = start+end (single packet)
           │  │  └─ sequence: 0 (increments per packet)
           │  └─ destination: 01 = Base
           └─ source: 00 = PC
  message: 4001 0002 00000050
           │    │    └─ body: protocol version 80
           │    └─ message type: 0x0002 = Connect
           └─ tag: (Base << 14) | 1 = 0x4001

Base -> PC   Connect (the station announces ITS version)
  packet : 01 00 <seq> 03 0008
  message: 4001 0002 00000050          (same tag, protocol version 80)

PC -> Base   Ack (completes the handshake)
  packet : 00 01 00000001 03 0004
  message: 4001 0000                    (type 0 = Ack, empty body, echo tag)

PC -> Base   RequestStatus (the actual query)
  packet : 00 01 00000002 03 0006
  message: 4002 0080 0086              (type 128, body: expect 0x0086 = 134)

Base -> PC   SoftwareVersion reply (echoes the tag 0x4002)
  message: 4002 0086 <u16 len> <version string, multi-line>

PC -> Base   Heartbeat (every 1000 ms, tag 0 = broadcast)
  message: 0000 0004 00000000
Base -> PC   heartbeat echo
  message: 0000 0004 00000bb8          (3000: the base's keep-alive timeout
                                         in ms — idle sessions are dropped
                                         after roughly 2-3 seconds)
```

Querying the head uses the same exchange on a fresh connection, with
`destination = 02` and tags `(2 << 14) | n` (0x8001, 0x8002, ...).

### Protobuf schema (reconstructed, [Verified])

The `ProtobufTypes.dll` assembly (namespace `Imr.Proto`) was deobfuscated with
de4dot and decompiled with ilspycmd. The complete reconstructed schema is in
**`docs/protos/nofio.proto`**. Summary of the messages carried inside
`Protobuf` (140):

- **BaseStatus** (content type 129): link booleans (WirelessLink, BridgeLink),
  temperatures (CpuTemp, FpgaTemp, BasebandTemp, RadioTemp), WiFi stats
  (WirelessTx/RxMcs, WirelessChannel, ChannelFreq, RSSI, SignalStrength),
  per-core CpuLoad (packed repeated), bridge/video speeds,
  PeakUncompressedVideoTXSpeed64, Isax, WirelessState (bit flags:
  PairingStarted/Success/Failure, ConnectionLost/Ok, WifiError, ...),
  nested Radio messages (RF name + Temp)
- **HeadStatus** (130): nested BaseStatus (the head's own view),
  PowerSource (Unknown/InternalBattery/ExternalBattery/Charger/LowVoltage),
  VoltageIn, ChargeCurrent, BatteryVoltage, VideoTxSpeed,
  VideoBufferReady/GeneratedPackets, PacketErrorRate,
  LeftBatteryCharge/RightBatteryCharge (battery packs powering the head over
  USB-C — the head runs on an external powerbank; -1 = not connected)
- **Setup** (144): the base's configuration/command message — WirelessCountry,
  WirelessChannel, VideoQuality, Pair, FactoryReset (None/Force/All/Data/Check),
  Reboot, LogLevel, Query, UpdateUserConf/SystemConf, firmware/board/FPGA
  file lists, Remove (FPGA/BOARD/FIRMWARE/...), RestartWireless/Controller,
  WirelessAP, AYMode (DMG/CB2), EdmgChannel(s), Diversity, UpdateParadeFw,
  IsAX, AxChannel(s)
- **Pairing** (158): PairingType (READ/SEND/SET/DONE/FAIL), Ssid, Psk,
  BaseErrorMsg/HeadErrorMsg, BeginPairing, BaseCompleted/HeadCompleted,
  PairingState (Unknown/None/Started/Success/Failure/Unpaired)
- **Configuration** (145): DefaultConf/FactoryConf/UserConf/SystemConf/
  ActualValues, each a list of ConfigurationItem{Key, Value}

### Observed status payloads (live, decoded with the schema)

```
$ python3 scripts/nofio_probe.py state                # BaseStatus
  WirelessLink = 1, ControllerInterface = 1, ControllerDevice = 1
  CpuTemp = 57, FpgaTemp = 55, BasebandTemp = 42      (°C)
  WirelessTxMcs = 7, WirelessRxMcs = 7
  WirelessChannel = 13, ChannelFreq = 6015            (6 GHz, WiFi 6E)
  RSSI = 97, Isax = 1
  BridgeRxMaxSpeed = 206000
  WirelessState = 260 (0x104: PairingSuccess, ConnectionOk)

$ python3 scripts/nofio_probe.py state --target head  # HeadStatus (via base)
  BaseStatus: CpuTemp = 60, FpgaTemp = 59, RSSI = 95, ChannelFreq = 5220
  BridgeTxSpeed/BridgeRxSpeed = -1                    (no video source yet)
  PeakUncompressedVideoTXSpeed64 = 2058000000
  LeftBatteryCharge = 76, RightBatteryCharge = 1
```

LeftBatteryCharge tracks the USB-C powerpack that powers the head unit and
discharges in real time (observed 96 -> 92 -> 88 -> 76 -> 70% over ~2 h of
live session - consistent with the advertised ~2-2.5 h battery life). This is
the value the original utility's VR battery overlay shows; it is NOT an Index
controller charge. RightBatteryCharge is a second power input: the nofio head
is designed for hot-swapping (verified online: nofio.co sells "Additional
Hot Swap Battery (~2.5hrs)" packs; the Kickstarter-era FAQ states battery
swapping takes ~20 seconds without restarting SteamVR, the head draws <15W
over USB-C PD and any 20W USB-PD pack works - QC3.0 is not supported).
With a single pack connected, RightBatteryCharge was observed pinned at 1%.

Notes: `-1` (0xFF...) is the "not available" sentinel; repeated numeric fields
are protobuf-packed; HeadStatus carries a nested BaseStatus with the head's
own radio view (different ChannelFreq than the base). Status is served
**on demand only** — while idle the head just echoes heartbeats and pushes
nothing, so poll with `RequestStatus` to get fresh values (verified: the
head's battery percentage updates between polls and never arrives unsolicited).

The head unit's battery **percentage** is `LeftBatteryCharge`/`RightBatteryCharge`
in HeadStatus: the head runs on EXTERNAL battery packs connected via USB-C
(`PowerSource.ExternalBattery`), and these fields report each pack's charge
level. The raw electrical telemetry (`PowerSource`, `VoltageIn`,
`ChargeCurrent`, `BatteryVoltage`) has been observed absent/zero with a
powerbank connected — possibly populated only while charging; capture one
to confirm. The original utility's VR overlay displays exactly
`LeftBatteryCharge` (fallback Right).

### Try it from Linux

Verified live against a base station connected over USB (CDC-Ethernet interface
on 192.168.3.0/24), no drivers and no VirtualHere involved:

```sh
# firmware version of the base (no drivers, no VirtualHere)
python3 scripts/nofio_probe.py status

# firmware version of the head adapter, routed through the base
python3 scripts/nofio_probe.py status --target head

# decoded BaseStatus / HeadStatus (temperatures, WiFi, batteries)
python3 scripts/nofio_probe.py state
python3 scripts/nofio_probe.py state --target head

# head battery percentage only (hot-swap powerpacks, single read or watch)
python3 scripts/nofio_probe.py battery
python3 scripts/nofio_probe.py battery --watch --interval 30

# print everything the base sends for 10 s
python3 scripts/nofio_probe.py monitor --duration 10

# send an arbitrary message (type 128 = RequestStatus, body 0086 = expect SoftwareVersion)
python3 scripts/nofio_probe.py raw 128 0086
```

Example `status` output (base, firmware v2.5.0):

```
=== 192.168.3.1:34566 ===
station protocol version: 80
SoftwareVersion reply:
  release=release/v2.5.0
  build=release/v2.5.0
  buildroot=release/v2.5.0
  imr_drivers=release/v2.5.0
  imr_software=release/v2.5.0
  linux=release/v2.5.0
  mcu=major=2 minor=14
  qca2066-lea=release/v2.5.0
  fpga=spark-60 (f5ac868)|nofio1-te0803-03-3ae11-a_mipi_base|10-05-2024 23:47
  hw_serial=240104-02E3-NI-b
  is_fallback=0
```

The head adapter (`--target head`, routed via the base) reports the same
software stack with board `..._dp_head`, its own serial
(`240104-074D-NI-h`) and FPGA build timestamp.

## Direct USB Protocol **[Hypothetical]**

> **Warning:** The Nofio direct USB protocol (bypassing VirtualHere) has NOT been reverse engineered. The message types, frame formats, and data structures that appeared in earlier versions of this document were speculative templates, not derived from captured traffic. They have been removed.
>
> To document this section, the following is needed:
> - USB packet captures (Wireshark + USBPcap on Windows, or usbmon on Linux)
> - Dynamic analysis with a debugger attached to `driver_nofio.dll` or `nofioUtility.exe`
> - Comparison of VirtualHere-tunneled USB traffic vs. the underlying USB device endpoints

### What is known

From the PDB analysis of `driver_nofio.pdb`:

- The driver (`driver_nofio.dll`) implements standard SteamVR interfaces and does **not** directly access USB hardware
- All USB communication is delegated to VirtualHere
- The driver registers a device provider (`device_provider`) and device classes (`device_settings`, `device_status`)
- Source files identified: `driver_factory.cpp`, `device_provider.cpp`, `device_settings.cpp`, `device_status.cpp`, `idevice.h`

This means the "Nofio protocol" as seen by the PC is simply standard USB encapsulated by VirtualHere. The proprietary part is the WiFi link between base and head, which is inside the firmware and not accessible from the PC side.

## SteamVR Integration **[Verified]**

### Driver Interfaces

The driver implements the following SteamVR interfaces (confirmed via PDB symbol analysis and cross-referenced with the OpenVR SDK headers):

#### ITrackedDeviceServerDriver_005

Source: [openvr_driver.h](https://github.com/ValveSoftware/openvr/blob/master/headers/openvr_driver.h), line ~2969

```cpp
class ITrackedDeviceServerDriver
{
public:
    virtual EVRInitError Activate( uint32_t unObjectId ) = 0;
    virtual void Deactivate() = 0;
    virtual void EnterStandby() = 0;
    virtual void *GetComponent( const char *pchComponentNameAndVersion ) = 0;
    virtual void DebugRequest( const char *pchRequest, char *pchResponseBuffer, uint32_t unResponseBufferSize ) = 0;
    virtual DriverPose_t GetPose() = 0;
};
```

#### IServerTrackedDeviceProvider_004

Source: [openvr_driver.h](https://github.com/ValveSoftware/openvr/blob/master/headers/openvr_driver.h), line ~3226

```cpp
class IServerTrackedDeviceProvider
{
public:
    virtual EVRInitError Init( IVRDriverContext *pDriverContext ) = 0;
    virtual void Cleanup() = 0;
    virtual const char * const *GetInterfaceVersions() = 0;
    virtual void RunFrame() = 0;
    virtual bool ShouldBlockStandbyMode() = 0;
    virtual void EnterStandby() = 0;
    virtual void LeaveStandby() = 0;
};
```

> **Note:** `ShouldBlockStandbyMode`, `RunFrame`, `EnterStandby`, and `LeaveStandby` belong to `IServerTrackedDeviceProvider`, not to `ITrackedDeviceServerDriver`. The device-level interface (`ITrackedDeviceServerDriver_005`) has only the six methods listed above.

### Properties

The driver exposes properties to SteamVR. The property names below are real OpenVR property identifiers. The specific values shown for Nofio are inferred from the PDB class names (`device_settings`, `device_status`) and the strings found in the binary, not from runtime observation.

| Property | Type | Description |
|----------|------|-------------|
| Prop_ModelNumber_String | String | Model number |
| Prop_ManufacturerName_String | String | Manufacturer |
| Prop_RegisteredDeviceType_String | String | Device type |
| Prop_DeviceIsWireless_Bool | Bool | Wireless device flag |
| Prop_DeviceIsCharging_Bool | Bool | Charging state |
| Prop_DeviceBatteryPercentage_Float | Float | Battery level (0.0-1.0) |
| Prop_Firmware_UpdateAvailable_Bool | Bool | Firmware update available |
| Prop_Firmware_ManualUpdate_Bool | Bool | Manual firmware update |
| Prop_BlockServerShutdown_Bool | Bool | Block server shutdown |
| Prop_CanUnifyCoordinateSystemWithHmd_Bool | Bool | Coordinate system unification |
| Prop_ContainsProximitySensor_Bool | Bool | Proximity sensor |
| Prop_DeviceProvidesBatteryStatus_Bool | Bool | Battery status available |
| Prop_DeviceCanPowerOff_Bool | Bool | Can power off |
| Prop_FirmwareVersion_Uint64 | Uint64 | Firmware version |
| Prop_HardwareRevision_String | String | Hardware revision |

## Error Codes

### SteamVR Error Codes **[Verified]**

The following error codes were found as strings in `nofioUtility.exe` and `driver_nofio.dll`. Numeric values are from the OpenVR SDK headers (`openvr.h`):

| Error Code | Value | Description |
|------------|-------|-------------|
| VRInitError_Init_HmdDriverIdIsNone | 125 | HMD driver ID is none |
| VRInitError_Init_FirmwareUpdateBusy | 138 | Firmware update in progress |
| VRInitError_Init_FirmwareRecoveryBusy | 139 | Firmware recovery in progress |
| VRInitError_Init_USBServiceBusy | 140 | USB service busy |
| VRInitError_Driver_Failed | 200 | Driver initialization failed |
| VRInitError_Driver_NotLoaded | 203 | Driver not loaded |
| VRInitError_Driver_RuntimeOutOfDate | 204 | Driver runtime out of date |
| VRInitError_Driver_HmdDriverIdOutOfBounds | 211 | HMD driver ID out of bounds |
| VRInitError_Driver_WirelessHMDNotConnected | 215 | Wireless HMD not connected |
| VRInitError_Compositor_FirmwareRequiresUpdate | 402 | Compositor firmware requires update |

> **Correction note:** Earlier versions of this document listed incorrect numeric values for several error codes (e.g., HmdDriverIdIsNone as 100, WirelessHmdNotConnected as 213). These have been corrected against the official OpenVR headers.

### Nofio-Specific Error Codes

> No Nofio-specific error codes have been identified in the binary analysis. The `NofioError_*` codes that appeared in earlier versions of this document were fabricated and have been removed. Any custom error handling in the utility likely uses standard .NET exception types or SteamVR error codes.

## Communication Flow **[Verified - high level]**

The following flow is confirmed by the original Linux guide and the VirtualHere configuration:

```
PC                  Base Station           Head Adapter
  │                     │                     │
  │───── USB Connect ───▶│                     │
  │   (CDC Ethernet,      │                     │
  │    VID:PID 04b3:4010) │                     │
  │                     │                     │
  │───── DHCP/Static ────▶│                     │
  │   (192.168.3.x)       │                     │
  │                     │                     │
  │───── VirtualHere ────────────────────────▶│
  │   Connect to 192.168.3.1:7575              │
  │                     │                     │
  │◀──── VirtualHere Handshake ──────────────│
  │   (EasyFindId/Pin auth)                    │
  │                     │                     │
  │───── USB Device Enumerate ───────────────▶│
  │   (via VirtualHere tunnel)                 │
  │                     │                     │
  │◀──── Device List ────────────────────────│
  │                     │                     │
  │───── SteamVR Driver Load ───────────────▶│
  │   (driver_nofio via HmdDriverFactory)      │
  │                     │                     │
  │◀──── Driver Ready ───────────────────────│
```

### What happens inside the tunnel **[Hypothetical]**

Between the VirtualHere tunnel and the Valve Index, the USB traffic is standard USB device communication. The Nofio-specific part is the WiFi link between base and head, which operates entirely within the firmware:

- Base station receives USB packets from PC via the CDC Ethernet interface
- Packets are tunneled to the head adapter over WiFi (QCA2066)
- Head adapter presents the USB device to the Valve Index via Oculink

The WiFi protocol between base and head is proprietary, runs inside the firmware, and has not been captured or analyzed from the PC side.

## Performance Characteristics **[Hypothetical]**

> No latency or throughput measurements have been performed. The Nofio firmware changelog (v2.5.0) mentions "reduced latency spikes" and "reduced CPU usage on head device," but no concrete numbers are published. Any specific latency budget or throughput figures would require measurement with proper equipment.

What is known:
- The WiFi chipset is QCA2066 (Qualcomm Atheros) **[Verified]**
- The system targets wireless VR, which typically requires < 20ms motion-to-photon latency
- The current VirtualHere-based solution adds USB-over-IP overhead

## Implementation Notes

### Current State **[Verified]**

- The original driver (`driver_nofio.dll`) does NOT directly access USB
- All communication goes through VirtualHere
- The driver only implements SteamVR interfaces (confirmed by PDB analysis)
- The utility (`nofioUtility.exe`) is a .NET 7 C# application that manages firmware updates, settings, and notifications

### Target Implementation **[Hypothetical]**

1. **Phase 1:** Open source utility that replicates nofioUtility functionality (status, pairing, firmware update)
2. **Phase 2:** Open source SteamVR driver that works with existing VirtualHere setup
3. **Phase 3:** Direct USB communication bypassing VirtualHere (requires USB protocol reverse engineering)
4. **Phase 4:** Open source firmware (requires complete firmware reverse engineering)

### Compatibility

- Must maintain compatibility with SteamVR API
- Should support both Windows and Linux
- Must work with existing Nofio hardware

## Testing **[Not yet performed]**

No dynamic testing has been done. The following would be needed:

### Test Equipment

- Nofio Base Station
- Nofio Head Adapter
- Valve Index Headset
- PC with Linux and Windows
- USB protocol analyzer (hardware)
- WiFi analyzer

### Test Cases

1. **Connection Test** - Verify device detection and VirtualHere tunnel establishment
2. **USB Capture** - Capture and analyze USB traffic between PC and base station
3. **WiFi Capture** - Capture and analyze WiFi traffic between base and head (requires specialized equipment)
4. **Firmware Update** - Document the firmware update process
5. **Latency Measurement** - Measure end-to-end motion-to-photon latency
6. **Stress Test** - Long-duration testing with continuous use

## References

- [OpenVR SDK](https://github.com/ValveSoftware/openvr) - Driver API headers
- [OpenVR Driver Header](https://github.com/ValveSoftware/openvr/blob/master/headers/openvr_driver.h) - Interface definitions
- [VirtualHere](https://www.virtualhere.com/) - USB-over-IP software
- [USB Specification](https://www.usb.org/documents) - USB standards
