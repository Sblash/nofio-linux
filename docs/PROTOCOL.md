# Communication Protocol

This document describes the communication protocols used by the Nofio wireless VR adapter.

## Overview

The Nofio system uses multiple layers of communication:

1. **USB Layer** - Physical connection between PC and Base Station
2. **Network Layer** - USB-over-IP via VirtualHere
3. **WiFi Layer** - Wireless communication between Base Station and Head Adapter
4. **Device Layer** - Communication with Valve Index headset

## Current Implementation (VirtualHere-based)

### USB Interface

- **VID:PID:** 04b3:4010 (IBM Corp. IMRWirelessVR)
- **Interface Class:** CDC Ethernet (USB CDC-ECM or RNDIS)
- **Driver:** `cdc_ether` / `usbnet` on Linux

#### USB Descriptors

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
    uint8_t  iManufacturer;        // 1 (IBM Corp.)
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

VirtualHere uses a proprietary protocol for USB-over-IP. The protocol structure is not publicly documented, but analysis reveals:

1. **Handshake Phase**
   - Client connects to server
   - Authentication via EasyFindId and EasyFindPin
   - Device enumeration

2. **Data Transfer Phase**
   - USB packets encapsulated in IP packets
   - Bidirectional communication
   - Device control and data transfer

## Target Implementation (Direct USB)

### Protocol Stack

```
┌─────────────────────────────────────┐
│           Application Layer            │  (SteamVR API)
├─────────────────────────────────────┤
│           OpenVR Driver Layer          │  (driver_nofio)
├─────────────────────────────────────┤
│           Transport Layer              │  (Direct USB)
├─────────────────────────────────────┤
│           Physical Layer               │  (USB 3.0 / WiFi)
└─────────────────────────────────────┘
```

### Message Types

#### USB Control Messages

| Message ID | Direction | Description | Payload Size |
|------------|-----------|-------------|--------------|
| 0x01 | PC → Base | Device Initialization | Variable |
| 0x02 | Base → PC | Device Response | Variable |
| 0x03 | PC → Base | Configuration Request | 64 bytes |
| 0x04 | Base → PC | Configuration Response | 64 bytes |
| 0x05 | PC → Base | Firmware Update Start | 32 bytes |
| 0x06 | PC → Base | Firmware Data | 1024 bytes |
| 0x07 | Base → PC | Firmware ACK | 8 bytes |
| 0x08 | PC → Base | Status Request | 0 bytes |
| 0x09 | Base → PC | Status Response | 32 bytes |

#### WiFi Protocol (QCA2066)

The QCA2066 chipset uses Qualcomm's proprietary WiFi protocol for low-latency audio/video transmission.

- **Frequency:** 5 GHz (recommended for VR)
- **Channel Width:** 80 MHz
- **Modulation:** OFDM
- **Latency Target:** < 5ms

### Data Frame Structure

```
┌─────────┬─────────┬──────────┬──────────────┬─────────┐
│  SOF     │  Type   │  Length  │    Payload    │  CRC    │
│  2 bytes │  1 byte │  2 bytes │  0-1024 bytes │  4 bytes │
└─────────┴─────────┴──────────┴──────────────┴─────────┘
```

#### Field Descriptions

- **SOF (Start of Frame):** 0xAA55 (little-endian)
- **Type:** Message type identifier
- **Length:** Payload length (excluding SOF, Type, Length, CRC)
- **Payload:** Actual data
- **CRC:** CRC32 checksum of all fields

### Known Message Types

| Type | Name | Description |
|------|------|-------------|
| 0x00 | PING | Connection keep-alive |
| 0x01 | DEVICE_INFO | Device information request |
| 0x02 | DEVICE_STATUS | Device status update |
| 0x03 | TRACKING_DATA | Tracking information |
| 0x04 | INPUT_EVENT | Button/joystick input |
| 0x05 | AUDIO_STREAM | Audio data stream |
| 0x06 | VIDEO_STREAM | Video data stream |
| 0x07 | CONFIG | Configuration data |
| 0x08 | FIRMWARE | Firmware update |
| 0x0F | ERROR | Error notification |

### Device Information Message (0x01)

```c
struct DeviceInfoMessage {
    uint8_t  type;           // 0x01
    uint16_t length;        // sizeof(DeviceInfo) = 32
    struct {
        uint16_t vendorId;         // 0x04b3
        uint16_t productId;        // 0x4010
        uint32_t serialNumber;     // Device serial
        uint8_t  hwVersion;        // Hardware version
        uint8_t  fwVersion[4];     // Firmware version (major.minor.patch.build)
        uint8_t  batteryLevel;     // 0-100%
        uint8_t  connectionStatus; // 0 = disconnected, 1 = connected
        uint8_t  reserved[14];     // Reserved for future use
    } info;
    uint32_t crc;           // CRC32 checksum
};
```

### Tracking Data Message (0x03)

```c
struct TrackingDataMessage {
    uint8_t  type;           // 0x03
    uint16_t length;        // sizeof(TrackingData) + sensorCount * sizeof(SensorData)
    struct {
        uint64_t timestamp;       // Nanoseconds since epoch
        uint8_t  sensorCount;      // Number of sensors
        uint8_t  reserved[3];      // Padding
    } header;
    struct {
        uint8_t  sensorId;         // Sensor identifier
        uint8_t  trackingState;    // 0 = invalid, 1 = valid
        float   position[3];      // X, Y, Z in meters
        float   rotation[4];      // Quaternion (x, y, z, w)
        float   velocity[3];      // Velocity in m/s
        float   angularVelocity[3]; // Angular velocity in rad/s
    } sensors[];
    uint32_t crc;           // CRC32 checksum
};
```

### Input Event Message (0x04)

```c
struct InputEventMessage {
    uint8_t  type;           // 0x04
    uint16_t length;        // sizeof(InputEvent) = 16
    struct {
        uint64_t timestamp;       // Nanoseconds since epoch
        uint16_t buttonState;     // Button bitmask
        uint8_t  axisCount;       // Number of axes
        uint8_t  reserved;        // Padding
        struct {
            uint8_t  axisId;          // Axis identifier
            float   value;           // Axis value (-1.0 to 1.0)
        } axes[4];               // Maximum 4 axes
    } event;
    uint32_t crc;           // CRC32 checksum
};

## SteamVR Integration

### Driver Interfaces

The driver implements the following SteamVR interfaces:

#### ITrackedDeviceServerDriver_005

```cpp
class ITrackedDeviceServerDriver_005 {
public:
    // Device activation
    virtual EVRInitError Activate(uint32_t unObjectId) = 0;
    virtual void Deactivate() = 0;
    virtual void EnterStandby() = 0;
    
    // Device information
    virtual void *GetComponent(const char *pchComponentNameAndVersion) = 0;
    
    // Device control
    virtual void DebugRequest(const char *pchRequest, char *pchResponseBuffer, uint32_t unResponseBufferSize) = 0;
    
    // Properties
    virtual DriverPose_t GetPose() = 0;
    
    // Status
    virtual bool IsPoseValid() = 0;
    virtual bool ShouldBlockStandbyMode() = 0;
    virtual void RunFrame() = 0;
    
    // Input
    virtual bool IsTrackedDeviceConnected() = 0;
};
```

#### IServerTrackedDeviceProvider_004

```cpp
class IServerTrackedDeviceProvider_004 {
public:
    virtual EVRInitError Init(IVRDriverLog_001 *pDriverLog, IVRSettings_003 *pSettings, IServerDriverHost_006 *pDriverHost) = 0;
    virtual void Cleanup() = 0;
    virtual const char * const *GetInterfaceVersions() = 0;
    virtual void RunFrame() = 0;
    virtual bool ShouldBlockStandbyMode() = 0;
    virtual void EnterStandby() = 0;
    virtual void LeaveStandby() = 0;
};
```

### Properties

The driver exposes the following properties to SteamVR:

| Property | Type | Description | Value |
|----------|------|-------------|-------|
| Prop_ModelNumber_String | String | Model number | "Nofio Wireless VR Adapter" |
| Prop_ManufacturerName_String | String | Manufacturer | "Nofio" |
| Prop_RegisteredDeviceType_String | String | Device type | "WirelessHMD" |
| Prop_ControllerRoleHint_Int | Int32 | Controller role | 0 (Invalid), 1 (Left), 2 (Right) |
| Prop_ControllerHandSelection_Priority_Int | Int32 | Hand selection priority | 0 |
| Prop_DeviceIsWireless_Bool | Bool | Wireless device | true |
| Prop_DeviceIsCharging_Bool | Bool | Charging state | true/false |
| Prop_Firmware_UpdateAvailable_Bool | Bool | Firmware update available | true/false |
| Prop_Firmware_ManualUpdate_Bool | Bool | Manual firmware update | false |
| Prop_BlockServerShutdown_Bool | Bool | Block server shutdown | true |
| Prop_CanUnifyCoordinateSystemWithHmd_Bool | Bool | Can unify coordinate system | true |
| Prop_ContainsProximitySensor_Bool | Bool | Proximity sensor | false |
| Prop_DeviceProvidesBatteryStatus_Bool | Bool | Battery status available | true |
| Prop_DeviceCanPowerOff_Bool | Bool | Can power off | false |
| Prop_Firmware_Version_String | String | Firmware version | "2.5.0" |
| Prop_Hardware_Version_String | String | Hardware version | "1.0" |

## Error Codes

### SteamVR Error Codes

| Error Code | Value | Description |
|------------|-------|-------------|
| VRInitError_None | 0 | No error |
| VRInitError_Init_HmdDriverIdIsNone | 100 | HMD driver ID is none |
| VRInitError_Init_FirmwareUpdateBusy | 138 | Firmware update in progress |
| VRInitError_Init_FirmwareRecoveryBusy | 139 | Firmware recovery in progress |
| VRInitError_Init_USBServiceBusy | 140 | USB service busy |
| VRInitError_Driver_Failed | 200 | Driver initialization failed |
| VRInitError_Driver_NotLoaded | 203 | Driver not loaded |
| VRInitError_Driver_NotKnown | 204 | Driver not known |
| VRInitError_Driver_RuntimeOutOfDate | 205 | Driver runtime out of date |
| VRInitError_Driver_WirelessHmdNotConnected | 213 | Wireless HMD not connected |

### Nofio-Specific Error Codes

| Error Code | Value | Description |
|------------|-------|-------------|
| NofioError_BaseNotFound | 0x1000 | Base station not found |
| NofioError_HeadNotFound | 0x1001 | Head adapter not found |
| NofioError_ConnectionFailed | 0x1002 | Connection to device failed |
| NofioError_FirmwareMismatch | 0x1003 | Firmware version mismatch |
| NofioError_InvalidConfiguration | 0x1004 | Invalid configuration |
| NofioError_USBCommunicationError | 0x1005 | USB communication error |
| NofioError_WiFiSignalLost | 0x1006 | WiFi signal lost |
| NofioError_BatteryLow | 0x1007 | Battery level low |

## Sequence Diagrams

### Initialization Sequence

```
PC                  Base Station           Head Adapter
  │                     │                     │
  │───── USB Connect ───▶│                     │
  │                     │                     │
  │───── Network Setup ──▶│                     │
  │                     │                     │
  │───── VirtualHere Connect ───▶│              │
  │                     │                     │
  │◀──── VirtualHere Handshake ────│              │
  │                     │                     │
  │───── Device Enumerate ────────▶│              │
  │                     │                     │
  │◀──── Device List ─────────────│              │
  │                     │                     │
  │───── SteamVR Driver Load ──▶│                     │
  │                     │                     │
  │◀──── Driver Ready ───────────│                     │
```

### Tracking Data Flow

```
Head Adapter       Base Station           PC
    │                  │                  │
    │─ Sensor Data ──▶│                  │
    │                  │                  │
    │                  │─── WiFi ——▶│ (encrypted)
    │                  │                  │
    │                  │◀── WiFi ——│ (ACK)
    │                  │                  │
    │◀─ ACK ───────────│                  │
    │                  │                  │
    │                  │─── USB ——▶│ (to SteamVR)
```

## Performance Requirements

### Latency Budget

| Component | Maximum Latency | Notes |
|-----------|-----------------|-------|
| USB Transfer | 1 ms | Full speed USB |
| WiFi Transfer | 3 ms | QCA2066 with 80 MHz channel |
| Processing | 2 ms | On PC and devices |
| **Total** | **6 ms** | Must be < 10ms for comfortable VR |

### Throughput Requirements

| Data Type | Required Throughput | Priority |
|-----------|---------------------|----------|
| Tracking Data | 1 Mbps | High |
| Input Events | 100 Kbps | High |
| Audio (Input) | 2 Mbps | Medium |
| Audio (Output) | 2 Mbps | Medium |
| Video (Future) | 50 Mbps | Low |
| **Total** | **~55 Mbps** | Maximum |

## Security Considerations

### Authentication

- VirtualHere uses EasyFindId and EasyFindPin
- Future implementation should use:
  - Certificate-based authentication
  - Encrypted communication
  - Device pairing mechanism

### Encryption

- WiFi should use WPA3 for maximum security
- USB communication should be encrypted if sensitive data is transferred
- Firmware updates must be signed and verified

## Implementation Notes

### Current State

- The original driver (`driver_nofio.dll`) does NOT directly access USB
- All communication goes through VirtualHere
- The driver only implements SteamVR interfaces

### Target Implementation

1. **Phase 1:** Implement driver that uses VirtualHere (current functionality)
2. **Phase 2:** Replace VirtualHere with direct USB communication
3. **Phase 3:** Implement custom WiFi protocol for better performance

### Compatibility

- Must maintain compatibility with SteamVR API
- Should support both Windows and Linux
- Must work with existing Nofio hardware

## Testing Protocol

### Test Cases

1. **Connection Test** - Verify device detection and connection
2. **Tracking Test** - Verify tracking data accuracy and latency
3. **Input Test** - Verify button and axis input
4. **Firmware Update Test** - Verify firmware update process
5. **Stress Test** - Long-duration testing with continuous use
6. **Interference Test** - Test with WiFi interference

### Test Equipment

- Nofio Base Station
- Nofio Head Adapter
- Valve Index Headset
- PC with Linux and Windows
- WiFi analyzer
- USB protocol analyzer

## References

- [OpenVR SDK Documentation](https://github.com/ValveSoftware/openvr/wiki)
- [USB Specification](https://www.usb.org/documents)
- [QCA2066 Datasheet](https://www.qualcomm.com/)
- [QNX6 Documentation](https://www.qnx.com/developers/docs/)
