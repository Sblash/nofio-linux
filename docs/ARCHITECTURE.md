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

The SteamVR driver implements the following interfaces:

- **ITrackedDeviceServerDriver_005** - Main device interface
- **IServerTrackedDeviceProvider_004** - Device provider interface
- **IVRWatchdogProvider_001** - Watchdog interface
- **IVRCompositorPluginProvider_001** - Compositor plugin interface
- **IVRProperties_001** - Properties interface
- **IVRDriverLog_001** - Logging interface
- **IVRSettings_003** - Settings interface

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

The utility provides GUI and management functionality.

#### Architecture

```
┌─────────────────────────────────────────────┐
│                 MainWindow                       │
│  + MainWindow()                                │
│  + InitializeComponents()                      │
│  + UpdateStatus()                              │
└─────────────────────┬────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐
│   SettingsManager    │ │   FirmwareUpdater    │
│  + LoadSettings()    │ │  + CheckForUpdates() │
│  + SaveSettings()    │ │  + DownloadFirmware()│
│  + GetSetting()      │ │  + InstallFirmware() │
└─────────────────────┘ └─────────────────────┘
```

#### File Structure

```
utility/
├── CMakeLists.txt
├── include/
│   └── settings.h              # Settings interface
├── src/
│   ├── main.cpp                # Entry point
│   ├── mainwindow.cpp           # Main window
│   ├── settings.cpp             # Settings manager
│   └── firmware_updater.cpp     # Firmware update logic
└── resources/
    └── icons/                   # Application icons
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

The project uses CMake for cross-platform builds.

### Dependencies

- **OpenVR SDK** - SteamVR driver interfaces
- **libusb** - USB access on Linux
- **Qt 5/6** - GUI framework (for utility)
- **C++17** - Minimum C++ standard
- **Python 3** - For analysis scripts

### CMake Targets

- `nofio-driver` - SteamVR driver library
- `nofio-utility` - GUI utility application
- `firmware-tools` - Firmware analysis tools

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
