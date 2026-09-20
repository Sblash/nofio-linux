# nofio-linux

Open source implementation for Nofio wireless VR adapter (Valve Index).

## Project Status

This project aims to create a complete open source solution for the Nofio wireless adapter, enabling native Linux support and open source firmware.

**Current Phase:** 1 - Complete Analysis (In Progress)

## Overview

Nofio is a wireless adapter for the Valve Index VR headset that uses VirtualHere for USB-over-IP communication between the base station and the PC. This project seeks to:

- Provide native Linux support
- Recreate firmware as open source
- Enable community development and bug fixes
- Prevent hardware abandonment (e-waste)

## Quick Start

For the current VirtualHere-based solution, see [docs/ORIGINAL_README.md](docs/ORIGINAL_README.md).

## Documentation

- [Analysis Report](docs/ANALYSIS.md) - Complete reverse engineering analysis
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
│   ├── ORIGINAL_README.md      # Original guide
│   └── TROUBLESHOOTING.md      # Troubleshooting guide
├── scripts/                    # Analysis and automation scripts
├── firmware/                   # Firmware analysis and original files
└── driver/                     # SteamVR driver implementation
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

### Phase 1: Complete Analysis (1-2 weeks)
- [ ] Extract all information from PDB - Scripts in ./scripts/
- [ ] Decompress firmware
- [ ] Disassemble all Thumb functions
- [ ] Document firmware call graph

### Phase 2: Open Source SteamVR Driver (2-4 weeks)
- [ ] Driver skeleton (OpenVR SDK)
- [ ] Implement HmdDriverFactory
- [ ] Device management (ITrackedDeviceServerDriver)
- [ ] Wireless properties (battery, status, etc.)
- [ ] Hardware detection (VID:PID 04b3:4010)
- [ ] VirtualHere integration

### Phase 3: Open Source Utility (1-2 weeks)
- [ ] User interface
- [ ] Configuration system (JSON)
- [ ] Firmware update protocol
- [ ] Dashboard overlay (SteamVR)
- [ ] Logging and diagnostics

### Phase 4: Direct Protocol (1-3 months)
- [ ] USB traffic analysis
- [ ] Reverse VirtualHere protocol
- [ ] Direct USB implementation
- [ ] Latency optimization

### Phase 5: Open Source Firmware (3-12 months)
- [ ] Complete firmware decompression
- [ ] QNX6 filesystem analysis
- [ ] ARM Thumb code reverse engineering
- [ ] Port to open source framework (Zephyr, FreeRTOS)
- [ ] QCA2066 WiFi support

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
