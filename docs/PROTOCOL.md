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

Extracted from the `vhui.ini` file bundled with the Nofio utility:

```ini
[General]
HideMenuItems=VHTBI
MainFrameWidth=400
MainFrameHeight=250
ReverseLookup=1
AutoFind=1
SSLReverseLookup=1

[Transport]
EasyFindId=WmQBJDfgXaTgoaJKHRe7Cz
EasyFindPin=7FAzRQ

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
