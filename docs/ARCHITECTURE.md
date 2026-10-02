# System Architecture

This document describes the architecture of the nofio-linux open source implementation.

## Overview

The Nofio wireless VR system consists of the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PC (Linux/Windows)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   SteamVR       │    │   OpenVR Driver  │    │  Utility    │  │
│  │                 │    │  (driver_nofio)  │    │  (optional)  │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│           ▲                  ▲  ▲  ▲                ▲           │
│           │                  │  │  └────────────────┘           │
│           │                  │  │                                   │
│           │                  │  └─── USB Interface (Virtual)  │
│           │                  │                                      │
└────────────────────────────────┼──────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nofio Base Station                            │
├─────────────────────────────────────────────────────────────────┤
│  VID:PID: 04b3:4010                                                  │
│  Chipset: QCA2066 WiFi                                               │
│  Firmware: base_BOOT.BIN                                            │
│  Network: 192.168.3.1:7575 (VirtualHere Server)                      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼ (WiFi QCA2066)
┌─────────────────────────────────────────────────────────────────┐
│                    Nofio Head Adapter                             │
├─────────────────────────────────────────────────────────────────┤
│  Chipset: QCA2066 WiFi                                             │
│  OS: QNX6 Neutrino                                               │
│  Firmware: head_BOOT.BIN                                          │
│  Connection: Oculink USB to Valve Index                           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Valve Index Headset                            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. OpenVR Driver (driver_nofio)

> **Findings on the original binary** (`miscellaneous/Resources/nofio_driver`,
> see [driver/PDB_ANALYSIS.md](../driver/PDB_ANALYSIS.md)): the original
> `driver_nofio.dll` is a **settings/status companion device** — a single
> stationary virtual device (`nofio_settings`) registered with
> `alwaysActivate: true`. It performs **no USB, network, or display I/O**
> (imports only CRT/`kernel32`) and is therefore **not part of the streaming
> path**, which runs through SteamVR's native Valve Index (lighthouse) driver
> over VirtualHere. On Linux the binary is unusable (PE32+) and its function
> is optional; it is kept as an OpenVR API reference only.

The interfaces actually implemented by the original binary's classes:

- **ITrackedDeviceServerDriver_005** - Device interface (class `device_settings`)
- **IServerTrackedDeviceProvider_004** - Provider interface (class `device_provider`)

Interfaces referenced via the driver context / `GetComponent` (version strings
present in the binary, no implementation): `IVRWatchdogProvider_001`,
`IVRCompositorPluginProvider_001`, `IVRProperties_001`, `IVRDriverLog_001`,
`IVRSettings_003`.

#### Class Diagram

```
┌─────────────────────────────────────────────┐
│                 HmdDriverFactory                 │
│  + HmdDriverFactory()                          │
│  + ~HmdDriverFactory()                         │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              ServerDriverHost                  │
│  + CreateTrackedDeviceServerDriver()          │
│  + GetInterface()                              │
└─────────────────────┬────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐
│  TrackedDeviceServer │ │  DeviceProvider      │
│  - m_pHmd           │ │  - m_pWatchdog      │
│  + Activate()        │ │  + GetInterface()    │
│  + Deactivate()      │ └─────────────────────┘
│  + EnterStandby()    │
│  + Update()          │
│  + GetComponent()    │
└─────────────────────┘
```

#### File Structure

The structure below describes the **planned reimplementation** for
nofio-linux, not the original binary.

```
driver/
├── CMakeLists.txt              # Build configuration
├── include/
│   ├── driver_factory.h        # Factory interface
│   ├── device_provider.h       # Device provider
│   ├── tracked_device.h         # Tracked device implementation
│   ├── device_settings.h       # Settings interface
│   ├── device_status.h         # Status monitoring
│   └── idevice.h               # Device interface
├── src/
│   ├── driver_factory.cpp      # Factory implementation
│   ├── device_provider.cpp     # Device provider implementation
│   ├── tracked_device.cpp       # Tracked device implementation
│   ├── device_settings.cpp     # Settings implementation
│   └── device_status.cpp       # Status implementation
└── resources/
    └── driver.vrresources       # SteamVR resources
```

### 2. Utility Application

The utility provides GUI and management functionality, replacing the original `nofioUtility.exe` (.NET 7) with a cross-platform Dart + Flutter application.

#### Architecture

```
┌─────────────────────────────────────────────┐
│                 MainApp (Flutter)                │
│  + main()                                       │
│  + build()                                      │
│  + initState()                                  │
└────────────────────┬────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐
│   SettingsService    │ │   FirmwareService   │
│  + loadSettings()    │ │  + checkUpdates()  │
│  + saveSettings()    │ │  + download()     │
│  + getSetting()      │ │  + install()       │
└─────────────────────┘ └─────────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────────┐
│              DeviceService (FFI)                 │
│  + getStatus()      → libusb / network          │
│  + pairDevices()    → base ↔ head              │
│  + readDiagnostics()                            │
└─────────────────────────────────────────────┘
```

#### File Structure

```
utility/
├── pubspec.yaml                # Dart dependencies
├── lib/
│   ├── main.dart               # Entry point
│   ├── app.dart                # App widget
│   ├── services/
│   │   ├── device_service.dart # Device communication (FFI to libusb)
│   │   ├── settings_service.dart # Settings management
│   │   └── firmware_service.dart # Firmware update logic
│   ├── models/
│   │   ├── device_info.dart    # Device info model
│   │   └── device_status.dart  # Status model
│   └── widgets/
│       ├── status_panel.dart   # Status display
│       └── settings_panel.dart  # Settings UI
└── assets/
    └── icons/                  # Application icons
```

### 3. Firmware Analysis Tools

Tools for analyzing and working with firmware files.

#### File Structure

```
firmware/
├── CMakeLists.txt
├── include/
│   ├── firmware.h              # Firmware header definitions
│   └── qnx6_fs.h               # QNX6 filesystem definitions
├── src/
│   ├── firmware_analyzer.cpp    # Analysis tool
│   ├── decompressor.cpp         # Decompression utilities
│   └── qnx6_extractor.cpp       # QNX6 filesystem extractor
├── tools/
│   ├── extract_firmware.py      # Python extraction scripts
│   ├── analyze_header.py        # Header analysis
│   └── disassemble_thumb.py     # ARM Thumb disassembler
└── docs/
    ├── firmware_format.md       # Firmware format documentation
    └── qnx6_analysis.md          # QNX6 filesystem analysis
```

## Communication Flow

### Current (VirtualHere-based)

```
PC Application → VirtualHere Client → Network (192.168.3.1:7575) → VirtualHere Server → USB Device
```

### Target (Direct USB)

```
PC Application → OpenVR Driver → USB Interface → Base Station → WiFi → Head Adapter → Valve Index
```

Note: no such driver exists in the original product. The original
`driver_nofio.dll` does no I/O (settings companion only, see
[driver/PDB_ANALYSIS.md](../driver/PDB_ANALYSIS.md)); a direct-USB driver is
new work and the original artifact serves only as an OpenVR API reference.
Also consider that SteamVR for Linux is effectively unmaintained by Valve
(no significant updates since 2023): evaluate Monado/OpenXR as the runtime
before investing in a SteamVR Linux driver.

## Data Structures

### Device Information

```cpp
struct NofioDeviceInfo {
    uint16_t vendorId;      // 0x04b3
    uint16_t productId;     // 0x4010
    std::string serialNumber;
    std::string firmwareVersion;
    uint8_t batteryLevel;
    bool isWireless;
    bool isConnected;
};
```

### Firmware Header

```cpp
#pragma pack(push, 1)
struct FirmwareHeader {
    uint8_t padding[0x20];        // 32 bytes of 0x00 0x00 0x00 0x14
    uint8_t magic[8];            // "fU\x99\xaaXNLX"
    uint8_t unknown1[8];         // a3 c5 c3 a5 00 00 fc ff
    uint8_t unknown2[8];         // 00 28 00 00 00 00 00 00
    uint8_t unknown3[8];         // 00 28 92 01 00 80 a1 01 00
    uint8_t timestamp[8];        // 0c 08 00 00 ea 32 57 57 (2WW)
};
#pragma pack(pop)
```

## Build System

The project uses multiple build systems:

- **Driver:** CMake (C++, cross-platform)
- **Utility:** Flutter build system (`flutter build`, Dart)
- **Firmware tools:** Python 3 (standalone scripts)

### Dependencies

- **OpenVR SDK** - SteamVR driver interfaces (C++)
- **libusb** - USB access on Linux (via Dart FFI for utility, direct for driver)
- **Dart + Flutter** - Cross-platform GUI for utility app
- **C++17** - Minimum C++ standard for driver
- **Python 3** - For firmware analysis scripts

### Build Targets

- `nofio-driver` - SteamVR driver library (C++, CMake)
- `nofio-utility` - GUI utility application (Dart/Flutter, `flutter build`)
- `firmware-tools` - Firmware analysis tools (Python 3)

## Platform Support

### Linux
- Primary target platform
- Uses libusb for USB access
- Integrates with SteamVR via OpenVR

### Windows
- Secondary platform
- Can use original driver as reference
- VirtualHere client available

## Testing Strategy

1. **Unit Tests** - Individual components
2. **Integration Tests** - Driver + Utility communication
3. **Hardware Tests** - Actual Nofio hardware testing
4. **Performance Tests** - Latency and throughput measurements

## Performance Considerations

- **Latency:** Critical for VR (< 10ms end-to-end)
- **Bandwidth:** USB 3.0 + WiFi 6 should be sufficient
- **CPU Usage:** Minimize processing overhead
- **Memory:** Efficient buffer management
