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
