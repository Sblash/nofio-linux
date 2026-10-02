# PDB Analysis - driver_nofio.pdb

**File:** `miscellaneous/Resources/nofio_driver/bin/win64/driver_nofio.pdb`  
**Size:** 913,408 bytes (913 KB)  
**Type:** Microsoft Program Database (PDB) - Debug symbols  
**Architecture:** x64 (AMD64)  
**Compiler:** Visual Studio 2022 Community (VC++ 14.36.32532)

---

## Source Files

| File | Type |
|------|------|
| driver_factory.cpp | Implementation |
| device_provider.cpp | Implementation |
| device_provider.h | Header |
| device_settings.cpp | Implementation |
| device_settings.h | Header |
| device_status.cpp | Implementation |
| device_status.h | Header |
| idevice.h | Interface |

---

## Classes and Interfaces

### IDevice Interface

**Methods:**
- `DebugRequest` - Handle debug requests
- `EnterStandby` - Enter standby mode
- `GetComponent` - Get component by name

---

### device_provider Class

**Methods:**
- `Cleanup` - Clean up resources
- `Init` - Initialize the device provider
- `RunFrame` - Run frame processing
- `GetInterfaceVersions` - Get supported interface versions
- `EnterStandby` - Enter standby mode
- `LeaveStandby` - Leave standby mode
- `ShouldBlockStandbyMode` - Check if standby should be blocked

**Features:**
- Has virtual function table
- Uses `std::unique_ptr<device_provider, std::default_delete<device_provider>>`

---

### device_settings Class

**Methods:**
- `Activate` - Activate device settings
- `Deactivate` - Deactivate device settings
- `GetPose` - Get current pose
- `RunFrame` - Run frame processing

**Features:**
- Has virtual function table
- Uses `std::unique_ptr<device_settings, std::default_delete<device_settings>>`

**Return Types:**
- `Activate` returns `EVRInitError`
- `GetPose` returns `DriverPose_t`

---

### device_status Class

**Features:**
- Uses `std::unique_ptr<device_status, std::default_delete<device_status>>`

---

## Variables

- `device_provider_instance` - Global or static instance

---

## Types

### SteamVR Types
- `EVRInitError` - Error code type
- `DriverPose_t` - Pose structure
- `IVRDriverContext` - Driver context interface

---

## Required Tools for Complete Extraction

To extract **complete** information from the PDB (function signatures, parameter types, class hierarchies, etc.), the following tools are required:

### Primary Options

1. **pdbparse** (Recommended)
   - Python library from Microsoft
   - Command: `pip install pdbparse`
   - Provides: Complete symbol extraction, type information, class hierarchies
   - Platform: Linux/Windows

2. **Ghidra** (Alternative)
   - NSA reverse engineering framework
   - Download: https://ghidra-sre.org/
   - Provides: PDB symbol loading, disassembly with names
   - Platform: Linux/Windows/macOS (Java)

3. **IDA Pro** (Commercial)
   - Hex-Rays reverse engineering tool
   - Provides: Native PDB support, full symbol extraction
   - Platform: Windows/Linux

4. **pykd**
   - Python kernel debugger
   - Command: `pip install pykd`
   - Provides: PDB reading, debugging capabilities
   - Platform: Windows

### Secondary Options

5. **llvm-readobj**
   - LLVM tool for object file inspection
   - May support PDB in newer versions
   - Command: `apt install llvm` (requires root)

6. **readpdb**
   - Standalone Python script
   - Source: https://github.com/ermig1979/ReadPdb

---

## Current Status

**Extracted:**
- Source file names
- Class and interface names
- Method names
- Basic type information

**Requires Specialized Tools:**
- Full function signatures (parameters, return types)
- Class inheritance hierarchies
- Variable names and types
- Source line numbers

---

## Runtime Behavior (Reconstructed)

Behavior below is reconstructed from the symbol set, class methods, and log
strings embedded in the binary. Line-level confirmation requires disassembly
(Ghidra/IDA) of `driver_nofio.dll` against this PDB.

### Startup Flow

1. SteamVR loads `driver_nofio.dll` and calls the only export,
   `HmdDriverFactory` (RVA 0x16C0).
2. `device_provider` (`IServerTrackedDeviceProvider_004`) `Init()` logs
   `"Driver loaded, adding devices..."`, instantiates exactly one virtual
   device, then logs `"Driver load complete!"`.
3. `device_settings` (`ITrackedDeviceServerDriver_005`) `Activate()` logs
   `"Settings device activated! Adding properties..."` and registers tracked
   properties on SteamVR.
4. The device serial / settings section is the string constant
   `"nofio_settings"` (used with `IVRSettings_003`).

### What the Settings Device Is

- A **single stationary virtual device**: `GetPose()` returns a `DriverPose_t`
  with a static pose (`bPoseIsValid` handling present in symbols). It does not
  track anything.
- It implements **no** display, camera, or direct-mode components. The
  component interface strings found in the DLL (`IVRDisplayComponent_002`,
  `IVRDriverDirectModeComponent_008`, `IVRCameraComponent_003`,
  `IVRVirtualDisplay_002`) are the standard names queried through
  `IDevice::GetComponent`, which returns `nullptr` for each.
- `device_status` exists as a class in the PDB but adds no further device.

### DLL Imports Analysis

`driver_nofio.dll` (17 KB) imports only:

| DLL | Imports | Meaning |
|-----|---------|---------|
| `kernel32.dll` | `GetCurrentProcess`, `QueryPerformanceCounter`, `InitializeSListHead`, ... | CRT boilerplate |
| `VCRUNTIME140.dll` + `api-ms-win-crt-*` | `malloc`, `memcpy`, `strcmp`, exception handling | C runtime |

**No `winusb`, `setupapi`, `ws2_32`, or any other I/O library is imported.**
The driver performs **zero** USB, network, or display I/O.

### Role in the Windows Stack

Since the driver does no I/O, it is **not part of the streaming path**, even in
the original Windows setup:

```
SteamVR -> native Valve Index driver (lighthouse) -> VirtualHere Client
        -> 192.168.3.1:7575 (VirtualHere Server on base station) -> USB -> Index
```

`driver_nofio.dll` sits *beside* this chain: the `alwaysActivate: true`
manifest plus the `nofio_settings` virtual device give `nofioUtility.exe` a
permanent settings/status channel inside SteamVR (properties read/written via
`IVRSettings_003` / `IVRProperties_001`). It is a companion device, not a
functional dependency: the headset chain works without it.

### Implications for nofio-linux

1. **The binary cannot be used on Linux** (PE32+ x86-64, Windows-only). Its
   only value is as an OpenVR API reference.
2. **The function it performs is optional.** The streaming chain on Linux
   (SteamVR native Index driver + VirtualHere Linux client) needs no custom
   driver. A settings companion would only be reimplemented (small C++ `.so`)
   for feature parity with `nofioUtility.exe`.
3. **The "Target (Direct USB)" driver is new work.** A driver that talks to the
   base station over libusb, bypassing VirtualHere, does not exist in the
   original product; this artifact is not a starting point for it beyond
   OpenVR API usage.
4. **Upstream risk:** SteamVR for Linux is effectively unmaintained by Valve
   (no significant updates since 2023). If the direct-USB target is pursued,
   evaluating Monado/OpenXR as the runtime is advisable before investing in a
   SteamVR Linux driver.

**Recommendation:** declassify `nofio_driver` from "component to reimplement"
to "documentation reference" for the Phase 2 driver skeleton. Priority stays
on firmware, the USB/VirtualHere protocol, and the utility.
