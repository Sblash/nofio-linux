# nofio-linux

Open source implementation for Nofio wireless VR adapter (Valve Index).

> **Disclaimer:** this is an independent, community reverse-engineering project
> for interoperability purposes. It is not affiliated with, endorsed by, or
> sponsored by IMRNext. "nofio" is a trademark of IMRNext. No vendor binaries,
> firmware images, or third-party proprietary software are distributed in this
> repository.

## Project Status

This project aims to create a complete open source solution for the Nofio wireless adapter, enabling native Linux support and open source firmware.

**Current Phase:** 1 - Open Source Utility (In Progress)

**Hardware:** Original Nofio hardware (base station + head adapter + Valve Index) is available for dynamic analysis and testing.

## Overview

Nofio is a wireless adapter for the Valve Index VR headset that uses VirtualHere for USB-over-IP communication between the base station and the PC. This project seeks to:

- Provide native Linux support
- Recreate firmware as open source
- Enable community development and bug fixes
- Prevent hardware abandonment (e-waste)

## Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Utility app | Dart + Flutter | Cross-platform GUI (replaces original .NET 7 app) |
| SteamVR driver | C++ (OpenVR SDK) | Native driver implementing ITrackedDeviceServerDriver_005 / IServerTrackedDeviceProvider_004 (original driver is a settings companion only, see [driver/PDB_ANALYSIS.md](driver/PDB_ANALYSIS.md)) |
| Firmware tools | Python 3 | Analysis scripts (binwalk, capstone, PDB parsing) |
| USB access | libusb (via Dart FFI) | Direct USB communication, bypassing VirtualHere |

## Quick Start

For the current VirtualHere-based solution, see [docs/ORIGINAL_README.md](docs/ORIGINAL_README.md).

**Note:** the VirtualHere client is **not** distributed in this repository
(it is third-party proprietary software). You need the Linux Intel x64 client
(`vhuit64`), available from [virtualhere.com](https://www.virtualhere.com/download).
Version **5.7.7** is the one bundled by the original Nofio utility and the one
tested here. The `vhui.ini` configuration it needs is documented (with
device-specific credentials redacted) in [docs/PROTOCOL.md](docs/PROTOCOL.md).

## Documentation

- [Analysis Report](docs/ANALYSIS.md) - Complete reverse engineering analysis
- [Architecture](docs/ARCHITECTURE.md) - System architecture
- [Protocol](docs/PROTOCOL.md) - Communication protocol
- [Utility Codebase Analysis](docs/UTILITY_CODEBASE_ANALYSIS.md) - Analysis of the original nofioUtility.exe (decompiled)
- [Utility Conceptual Map](docs/UTILITY_CONCEPTUAL_MAP.md) - Conceptual map of the original utility's codebase
- [Driver PDB Analysis](driver/PDB_ANALYSIS.md) - Analysis of the original SteamVR driver
- [Original Guide](docs/ORIGINAL_README.md) - Original Linux setup guide
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Project Structure

```
nofio-linux/
├── README.md                    # This file
├── LICENSE                     # GPLv3 license
├── CONTRIBUTING.md             # Contribution guidelines
├── docs/                       # Documentation
│   ├── ANALYSIS.md             # Reverse engineering report
│   ├── ARCHITECTURE.md         # System architecture
│   ├── PROTOCOL.md             # Communication protocol
│   ├── UTILITY_CODEBASE_ANALYSIS.md  # Original utility analysis (decompiled)
│   ├── UTILITY_CONCEPTUAL_MAP.md     # Original utility conceptual map
│   ├── ORIGINAL_README.md      # Original guide
│   └── TROUBLESHOOTING.md      # Troubleshooting guide
├── scripts/                    # Analysis and automation scripts
├── utility/                   # Open source utility app (Dart + Flutter)
├── firmware/                   # Firmware analysis and original files
└── driver/                     # SteamVR driver implementation (C++)
```

## Hardware Information

- **Base Station VID:PID:** 04b3:4010 (IBM Corp. IMRWirelessVR)
- **WiFi Chipset:** QCA2066 (Qualcomm Atheros)
- **Network:** USB Ethernet (CDC-ECM/RNDIS)
- **IP Range:** 192.168.3.x
- **VirtualHere Server:** 192.168.3.1:7575

## Phases

### Phase 0: Project Setup (1 day)
- [x] Clone repository
- [x] Create directory structure
- [x] Move existing documentation
- [x] Create README, CONTRIBUTING, LICENSE
- [x] Create initial documentation templates

### Phase 1: Open Source Utility
- [ ] Analysis Windows utility app and reverse engineering
- [ ] Open source app reimplementation for Linux
- [ ] Reading nofio-base status
- [ ] Pairing (nofio-base <-> nofio-head)
- [ ] Firmware update
- [ ] Logging and diagnostics

### Phase 2: SteamVR Driver + Dynamic Analysis
- [ ] Extract all information from PDB - Scripts in ./scripts/
- [ ] USB packet capture (Wireshark/usbmon on Linux, USBPcap on Windows)
- [ ] Reverse engineer direct USB protocol (bypassing VirtualHere)
- [ ] Driver skeleton (OpenVR SDK)
- [ ] Implement HmdDriverFactory
- [ ] Device management (ITrackedDeviceServerDriver_005)
- [ ] Device provider (IServerTrackedDeviceProvider_004)
- [ ] Wireless properties (battery, status, etc.)
- [ ] Hardware detection (VID:PID 04b3:4010)
- [ ] VirtualHere integration (interim solution)

> **Note (static analysis):** the original `driver_nofio.dll` is a
> settings/status companion device (`nofio_settings`) that performs no
> USB, network, or display I/O — it is not in the streaming path, which runs
> through SteamVR's native Valve Index driver over VirtualHere. Use the
> binary as an OpenVR API reference only; the direct-USB driver is new work.
> Details: [driver/PDB_ANALYSIS.md](driver/PDB_ANALYSIS.md).


### Phase 3: Open Source Firmware
- [ ] Complete firmware decompression
- [ ] Disassemble ARM Thumb code (Ghidra/IDA)
- [ ] Document firmware call graph
- [ ] QNX6 filesystem analysis (head_BOOT.BIN)
- [ ] Validate PGP signature / boot verification
- [ ] Port to open source framework (Zephyr, FreeRTOS)
- [ ] QCA2066 WiFi driver support

### Phase 4: Optimizations and fixes
- [ ] Fix current nofio firmware bugs
- [ ] Latency optimization

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE) for details.

## Resources

- [ValveSoftware/openvr](https://github.com/ValveSoftware/openvr) - OpenVR SDK
- [Sblash/nofio-linux](https://github.com/Sblash/nofio-linux) - Original Linux guide
- [QNX Documentation](https://www.qnx.com/developers/docs/) - QNX6 OS documentation

## Contact

For questions or discussions, please open an issue on GitHub.
