# Complete Codebase Analysis - nofio-utility-cleaned

> Source: static reverse engineering of the decompiled `nofioUtility.exe`
> (WPF/.NET 7 utility by IMRNext). The decompiled tree lives outside the
> published repository (`miscellaneous/nofio-decompiled/`, git-ignored).
> Companion document: [UTILITY_CONCEPTUAL_MAP.md](UTILITY_CONCEPTUAL_MAP.md).

## General Overview

**nofio-utility-cleaned** is a WPF (.NET 7) application developed by
**IMRNext** for managing nofio devices, a VR wireless system. The
application acts as a utility for configuration, firmware updates, device
status monitoring and notifications.

---

## Project Structure

Note: the decompiler flattens namespaces using dots in folder names, so
`UserInterface.Business.Views.Flows/` is a **top-level** folder, not a
subfolder of `UserInterface.Business.Views/`.

```
nofio-utility-cleaned/
├── Properties/
│   └── AssemblyInfo.cs          # Assembly metadata (version 0.1.0.0)
├── UserInterface/
│   ├── App.xaml(.cs)            # WPF Application (theme, startup handler)
│   └── Program.cs               # Entry point, host and DI configuration
├── UserInterface.Resources.DashboardIcon.png   # Graphic resource (embedded)
├── UserInterface.Business.Models/
│   ├── PersistentState.cs       # Persistent application state (root state)
│   ├── TaskDescription.cs       # Task description (Status, Progress, IsIndeterminate)
│   └── VirtualHereState.cs     # VirtualHere state (Servers/Devices, record struct)
├── UserInterface.Business.Models.Persistent/
│   ├── Settings.cs              # User settings
│   ├── NofioHardware.cs         # Nofio hardware (empty class: placeholder)
│   ├── Logging.cs               # Logging configuration
│   └── ThemePreference.cs       # Theme preference (Auto/Light/Dark)
├── UserInterface.Business.Models.Enums/
│   ├── DeviceCommand.cs         # Device commands (Reboot, RestartController)
│   ├── DriverInstallResult.cs   # VirtualHere driver install outcome
│   ├── FirmwareInstallFlowStep.cs
│   ├── FirmwareValidity.cs      # Firmware package validity
│   ├── NotificationUrgency.cs   # Notification urgency
│   ├── OverallStatus.cs         # Overall system status
│   ├── PairDevicesFlowStep.cs
│   ├── PairingStatus.cs
│   ├── PairingStatusMethods.cs  # Helper methods for PairingStatus
│   ├── SupportReportFlowStep.cs
│   ├── VideoState.cs
│   └── VirtualHereStatus.cs
├── UserInterface.Business.Services/
│   ├── NofioInterfaces.cs       # Network interface monitoring
│   ├── NofioState.cs            # Connection and device state
│   ├── NofioConnection.cs       # Socket connection management
│   ├── NofioSocket.cs           # Custom socket (TcpClient wrapper)
│   ├── NofioRequests.cs         # Reply dispatch (HandleIfReply)
│   ├── Pairing.cs               # Device pairing management
│   ├── Firmware.cs               # Firmware package (identification/validation)
│   ├── VirtualHere.cs           # VirtualHere integration
│   ├── Persistence.cs           # Data persistence (nofio.json)
│   ├── ErrorReporting.cs        # Error reporting (Sentry)
│   ├── CommandLineInterface.cs  # Single-instance + argument redirect
│   └── ImrDevToolMonitor.cs     # imr_devtool process monitoring
├── UserInterface.Business.Services.NofioApi/
│   ├── Device.cs                # Device enum (PC, Base, Head, PC2, Max)
│   ├── DeviceContext.cs         # Per-device transaction counters
│   ├── DisconnectException.cs / DisconnectReason.cs / NakException.cs
│   ├── UnexpectedReplyException.cs
│   ├── Message.cs               # Base message (Header with Tag)
│   ├── Packet.cs                # Packet header (Source/Destination/Sequence)
│   ├── MessageType.cs           # Message types (ushort)
│   ├── MessageTypeAttribute.cs / ProtobufTypeAttribute.cs / MinimumProtocolAttribute.cs
│   ├── MessageTag.cs            # ushort tag (Device in high bits, TransactionId in low bits)
│   ├── MessageErrorCode.cs      # Nak error codes (uint)
│   ├── IReply.cs                # Reply interfaces (Notify/Task<T>)
│   └── IReplyExtensions.cs      # GetAwaiter for IReply<T>
├── UserInterface.Business.Services.NofioApi.Replies/
│   ├── Reply.cs                 # Reply<T> : IReply<T> (TaskCompletionSource)
│   └── ProtobufReply.cs         # ProtobufReply<T> (parse IMessage<T>)
├── UserInterface.Business.Services.NofioApi.Messages/
│   ├── Ack.cs / Nak.cs / Connect.cs / Disconnect.cs / Heartbeat.cs
│   ├── Protobuf.cs              # Container (Content, ContentType)
│   ├── RequestStatus.cs
│   ├── SoftwareFileType.cs      # Transferable file enum (LinuxUb, FpgaBit, ...)
│   ├── SoftwareUpdateMeta.cs / SoftwareUpdateData.cs / SoftwareUpdateComplete.cs
│   └── SoftwareVersion.cs       # Version + CheckForVersionMatch/IsOnFallbackFirmware
├── UserInterface.Business.ViewModels/
│   ├── BatteryNotification.cs   # Battery notification VM
│   ├── DeviceConnectionSummary.cs # Connection status VM
│   ├── DeviceStatus.cs          # Device status VM
│   ├── SettingsNotificationButton.cs # Settings/notification button VM
│   ├── FirmwareInstallFlow.cs   # Firmware install flow VM
│   ├── OptionsFlow.cs           # Options flow VM
│   ├── PairDevicesFlow.cs       # Pairing flow VM
│   └── SupportReportFlow.cs     # Support report flow VM
├── UserInterface.Business.Views/
│   ├── BatteryNotification.cs   # Battery notification view (DependentControl<T>)
│   ├── DeviceConnectionSummary.cs # Connection status view
│   ├── DeviceStatus.cs          # Device status view
│   └── SettingsNotificationButton.cs
├── UserInterface.Business.Views.Flows/          # Flow views (TOP-LEVEL folder)
│   ├── FirmwareInstallFlow.xaml(.cs) + FirmwareInstallFlowControl.cs
│   ├── OptionsFlow.xaml(.cs) + OptionsFlowControl.cs
│   ├── PairDevicesFlow.xaml(.cs) + PairDevicesFlowControl.cs
│   └── SupportReportFlow.xaml(.cs) + SupportReportFlowControl.cs
│       # The *FlowControl are generated base classes:
│       # DependentFlowControl<UserInterface.Business.ViewModels.XxxFlow>
├── UserInterface.Business.Windows/
│   ├── BatteryOverlay.cs        # Battery overlay window (VRWindow)
│   ├── DashboardOverlay.cs     # Dashboard overlay window (VRWindow)
│   ├── ProductionTestWindow.cs # Production test window (AppWindow)
│   ├── ToolsWindow.cs           # Tools window (AppWindow)
│   └── UtilityWindow.cs         # Main window (AppWindow)
├── UserInterface.Controls/
│   ├── Battery.xaml(.cs)        # Battery control (UserControl)
│   └── TitleBar.xaml(.cs)       # Title bar control (UserControl)
├── business/                    # Actual XAML (views/, views/flows/, windows/)
├── controls/                    # (empty directory)
├── properties/                  # designtimeresources.xaml
├── --f__AnonymousType0.cs       # Compiler-generated anonymous type
├── -PrivateImplementationDetails-.cs  # Compiler implementation details
├── nofioUtility-cleaned.csproj  # .NET 7 project (AssemblyName: nofioUtility)
├── app.ico                      # Application icon
└── app.manifest                 # Application manifest
```

---

## Technologies and Dependencies

### Framework
- **.NET 7.0** targeting Windows 10.0.22621.0+
- **WPF** (Windows Presentation Foundation)
- **x64** platform target

### External Libraries (from the csproj)

Note: the decompiled csproj uses `<Reference>` with `HintPath` pointing to
DLLs (`nofio-decompiled/output/...`), not `<PackageReference>`. References
absent from the csproj should not be taken for granted.

#### Microsoft Core
- `Microsoft.Extensions.Hosting` (+ `.Abstractions`)
- `Microsoft.Extensions.DependencyInjection.Abstractions` (Abstractions only;
  the `Add*From` functions come from UserInterfaceLib)
- `Microsoft.Extensions.Configuration` (+ `.Json`, `.Abstractions`)
- `Microsoft.Extensions.Logging` (+ `.Abstractions`, `.EventLog`)
- `Microsoft.Windows.SDK.NET`
- `Microsoft.Windows.AppLifecycle.Projection`
- `Microsoft.WindowsAppRuntime.Bootstrap.Net`
- `WinRT.Runtime`

#### Community & Open Source
- **CommunityToolkit.Mvvm** - MVVM Toolkit (ObservableObject, RelayCommand)
- **Sentry** - Error tracking and reporting
- **NReco.Logging.File** - File logging
- **Google.Protobuf** - Protocol Buffers serialization
- **ProtobufTypes** - Custom protobuf types (Imr.Proto, no HintPath)
- **System.Management** - System management (WMI)
- **OpenTK.Mathematics** - Math library
- **InjectX.Shared** - Dependency injection (`[Singleton]` attribute, Ioc)

#### UserInterfaceLib (external dependency)
- `UserInterfaceLib` - Custom IMRNext library (single reference, no HintPath)
- `UserInterfaceLib.OpenVR` and `UserInterfaceLib.Extensions` are **not**
  separate references: they are *internal* namespaces of UserInterfaceLib
  (e.g. `VR.Install.AddDriver`, `SystemTextJson.PopulateObject`)

---

## Application Architecture

### Architectural Pattern
The application follows an **MVVM pattern (Model-View-ViewModel)** with:
- **Dependency Injection** via `Microsoft.Extensions.DependencyInjection`
- **Hosting** via `Microsoft.Extensions.Hosting`
- **MVVM Toolkit** (CommunityToolkit.Mvvm) for ObservableObject, Singleton, etc.

### Startup Flow

```
Program.Main() [STAThread]
    ↓
Ioc.Default.GetRequiredService<ErrorReporting>()  - Forces Sentry init (DSN from AssemblyInfo)
    ↓
Bootstrap.TryInitialize(65538u) - Initializes Windows App SDK
    ├── Failure → SentrySdk.CaptureMessage(Error) + Exit()
    ↓
CommandLineInterface.ShouldQuit?  - Single-instance (AppInstance "nofio.UserInterface")
    ├── true → Exit() (activation redirected to the existing instance)
    ↓
Host.CreateDefaultBuilder()
    │
    ├── ConfigureAppConfiguration() - Loads nofio.json
    │
    ├── ConfigureLogging()
    │   ├── File logging (nofio.log, append, 409600 B, 10 rolling files)
    │   └── EventLog logging (source nofio.UserInterface, filter >= Warning)
    │
    └── ConfigureServices() - AddServicesTo()
        ├── AddSingleton(typeof(App))
        ├── AddServicesFrom(assembly, "Business.Models", "Business.Services")
        ├── AddViewsAndViewModelsFrom(assembly, "Business.Views", "Business.ViewModels")
        └── AddWindowsFrom(assembly, "Business.Windows")
    ↓
Ioc.Default.ConfigureServices(AppHost.Services) - Configures the global container
    ↓
AppHost.Start()
    ↓
App (from Ioc.Default) + App.Startup += Program.OnAppStartup
    ↓
App.Run()
    ↓
OnAppStartup() (static handler in Program.cs, wired to the App.Startup event)
    ├── MicrosoftExtensionsHosting.ShowWindow<UtilityWindow>(AppHost)
    ├── MicrosoftExtensionsHosting.CreateVRWindow<BatteryOverlay>(AppHost)
    └── MicrosoftExtensionsHosting.CreateVRWindow<DashboardOverlay>(AppHost)
```

### Main Components

#### 1. **NofioInterfaces** (`NofioInterfaces.cs`)
- **Role**: Network interface monitoring
- **Functionality**:
  - Detects availability of the Base (192.168.3.1) and Head (192.168.4.1)
    interfaces: an interface is considered "up" if it is
    `OperationalStatus.Up` and the device address appears among its
    `DhcpServerAddresses`
  - Uses `NetworkChange.NetworkAddressChanged` to detect changes
  - Debounce timer (40ms) to avoid multiple triggers
- **Properties**:
  - `IsBaseAvailable` - Base is reachable
  - `IsHeadAvailable` - Head is reachable

#### 2. **NofioConnection** (`NofioConnection.cs`)
- **Role**: Socket connection management to the devices
- **Constants**: `BaseIpAddress = 192.168.3.1`, `HeadIpAddress = 192.168.4.1`,
  `BasePort = 34566`, `HeadPort = 34568`
- **Functionality**:
  - Connects to Base and Head over TCP sockets
  - Connection state management (Opening, Open, Closed)
  - Automatic reconnection
  - Disconnect handling (Reasons: DevToolOverride, NoPathFound,
    PoliteDisconnect, etc.)
  - Protocol version negotiation (`Connect.ProtocolVersion`)
- **Components**:
  - `_baseSocket` - Socket for the Base
  - `_headSocket` - Socket for the Head
  - `_imrDevTool` - ImrDevTool monitoring (`OnDevToolStateChanged` event)
  - `_interfaces` - Reference to NofioInterfaces
- **Properties**: `IsBaseConnected` / `IsHeadConnected` / `IsHeadLocal`,
  `LastBaseDisconnectReason` / `LastHeadDisconnectReason`,
  `BaseProtocolVersion` / `HeadProtocolVersion` (uint)
- **Methods**: `SendRequest<T>()`, `BeginConnectingTo(Device)`,
  `HandleDisconnect(Device, reason)`, `DoDisconnect(Device)`

#### 3. **NofioState** (`NofioState.cs`)
- **Role**: Central application state
- **Functionality**:
  - Device state management (Base and Head)
  - Firmware and version tracking
  - Device pairing management
  - Battery status monitoring (`LeftBatteryStatus` / `RightBatteryStatus`, double?)
  - WiFi configuration (channel, country)
  - VirtualHere handling (constructor dependency)
- **Key properties** (verified from source):
  - `IsBaseConnected` / `IsHeadConnected` / `IsHeadLocal` (delegates to
    `NofioConnection`; no `IsBaseLocal` property exists)
  - `LastBaseDisconnectReason` / `LastHeadDisconnectReason` : DisconnectReason
  - `Status` : OverallStatus (computed by `DetermineStatus()`)
  - `IsFirmwareUpToDate`, `IsBaseOnFallback`, `IsHeadOnFallback`, `IsWiFiSetupAvailable`
  - `WiFiChannel` / `WiFiCountry` / `AvailableWiFiChannels`
- **Methods**: `DetermineStatus()`, `TryUpdateHardwareFirmwareStatus()`,
  `QueryBaseWiFiSetup()`, `ChangeWiFiChannel()`, `ClearBaseWiFiSetup()`

#### 4. **PersistentState** (`PersistentState.cs`)
- **Role**: Persistent application state
- **Functionality**:
  - Automatic loading and saving from `nofio.json`
  - Application lifecycle handling
  - Integrated with the host application lifetime
- **Components**:
  - `Settings` - User settings
  - `NofioHardware` - Hardware information
  - `Logging` - Logging configuration

#### 5. **Settings** (`Settings.cs`)
- **Role**: Persistent user settings
- **Properties**:
  - `ThemePreference` - Theme (Auto/Light/Dark)
  - `IsDeveloper` - Developer mode
  - `StatusPinned` / `StatusLocation` - Status window position
  - `BatteryOverlayX/Y/Distance/Size` - Battery overlay position
  - `BatteryOverlayShowText` - Show overlay text

---

## Device Communication

### Protocol
- **Transport**: TCP (NofioSocket is a wrapper over `TcpClient`/`NetworkStream`)
- **Addresses and ports**:
  - Base: `192.168.3.1:34566` (socket local identity: `Device.PC`)
  - Head: `192.168.4.1:34568` (socket local identity: `Device.PC2`)
- **Serialization**: Protocol Buffers (Google.Protobuf) for `Protobuf` contents
- **Message format**: `Protobuf` structure with `MessageType` (ushort) and
  binary content

### Wire format (verified from the decompilation, byte-exact)

TCP packet — 9-byte header, all fields **big-endian**:

```
[0]      Source (Device, byte)
[1]      Destination (Device, byte)
[2:6]    Sequence (uint) - increments per packet; the receiver
          closes with PacketSequenceError if one is skipped
[6]      Options: bit0 = IsStartPacket, bit1 = IsEndPacket
[7:9]    DataLength (ushort, max 65535)
[9:...]  payload chunk
```

Message (reassembled payload of one or more packets):

```
[0:2]    Tag (ushort): (device << 14) | transactionId (14 bits)
[2:4]    MessageType (ushort)
[4:...]  message body
```

Bodies of the main messages:

| Type | Name | Body (BE) | Notes |
|---|---|---|---|
| 0 | Ack | empty | echoes the request tag |
| 1 | Nak | uint32 MessageErrorCode | rejects the transaction |
| 2 | Connect | uint32 protocol version (the app uses **80**) | tag = (dst<<14)\|1 |
| 3 | Disconnect | empty | |
| 4 | Heartbeat | uint32 Next (the app sends 0) | tag 0 (Broadcast), every 1000 ms |
| 128 | RequestStatus | uint16 expected reply type | the reply echoes the tag |
| 134 | SoftwareVersion | [uint16 len][string] | multi-line, split on `\n` |
| 140 | Protobuf | [u8 pktCount][uint16 contentType][protobuf bytes] | |

Handshake (verified dynamically on real hardware):
TCP → `Connect(80)` → the Base answers with **its own** `Connect`
(version 80) → the client answers `Ack` (echoing the tag) → connection
established. The Base does NOT send an Ack for the client's Connect.
Heartbeat every 1000 ms (body 0, tag 0): the Base answers every heartbeat
with body 3000 (0x0BB8, keep-alive timeout ~3 s; silent connections get
closed). Queries: `RequestStatus{ExpectingReply=SoftwareVersion}` with the
next transaction (the app's DeviceContext starts at 128; connect uses 1).
Pending replies are indexed by **MessageTag** in `NofioRequests`.

Note: a working Linux client based on this format is
`scripts/nofio_probe.py` (full details in [PROTOCOL.md](PROTOCOL.md),
"Direct TCP Control Protocol" section, successfully tested against a real
Base: firmware version v2.5.0 retrieved). Additional dynamic discovery:
the Base **routes packets to the Head** over wireless (packet header
`Destination = Head`), so the Head can be queried through the Base socket
without a direct path to 192.168.4.0/24; packet sequences must be tracked
per source device. `RequestStatus{PeerInfo}` on the Base returns the
wireless peer (device=2=Head, protocol=80).

### Message Types (MessageType : ushort)
```csharp
// Connection control (0-4)
Ack = 0, Nak = 1, Connect = 2, Disconnect = 3, Heartbeat = 4

// Video/HMD events (64-67)
HMDConnected = 64, PCConnected = 65, VideoLost = 66, ConfirmVideoState = 67

// Status and configuration (128-150)
RequestStatus = 128, BaseStatus = 129, HeadStatus = 130, HMDSuspended = 131,
BridgeParams = 132, FoveationParams = 133, SoftwareVersion = 134,
SoftwareUpdateMeta = 135, Statistics = 136, SoftwareUpdateData = 137,
SoftwareUpdateComplete = 138, FPGAErrorStatus = 139, Protobuf = 140,
FPGAFramerConfiguration = 141, FPGAStatus = 142, GenlockControl = 143,
Setup = 144, Configuration = 145, TestFrameGenerator = 146, VirtualHere = 147,
EDID = 148, PeerInfo = 149, CodecParams = 150

// Others (152-158)
SourceConnected = 152, VideoStatus = 153, AudioInfo = 154, FrameCaptures = 155,
Wifi6ESim = 156, FPGARegisters = 157,
Pairing = 158  // requires protocol >= 76 ([MinimumProtocol(76)])

Invalid = ushort.MaxValue
```

Note: `BaseStatus`, `HeadStatus`, `Setup`, `Configuration` and `Pairing` are
annotated with `[ProtobufType]`, which binds them to the corresponding
protobuf message.

### Devices (Device Enum, byte)
```csharp
PC     // Main computer (socket local identity)
Base   // Base station
Head   // VR headset
PC2    // Second computer
Max    // Limit
// Implicit values 0-4 (no explicit assignment in the decompiled source)
```

### Communication Flow
```
NofioConnection
    │
    ├── _baseSocket.Open() → Connect to Base (192.168.3.1:34566, TCP)
    │
    ├── _headSocket.Open() → Connect to Head (192.168.4.1:34568, TCP)
    │
    └── SendRequest<T>() → Send message and await reply
        │
        ├── Message → NofioSocket.SendMessage(destination, message, tag)
        ├── The reply is routed by NofioRequests.HandleIfReply()
        └── Reply wait via IReply<T> (Task-based)
            │
            ├── Reply<T>/ProtobufReply<T> complete a TaskCompletionSource
            │   (ProtobufReply<T> parses the IMessage<T> type;
            │   wrong expected type → UnexpectedReplyException)
            ├── Nak → NakException
            ├── Disconnect → DisconnectException
            └── Await via IReplyExtensions.GetAwaiter<T>()
```

---

## Application Flows

### 1. **Firmware Install Flow**
- **Purpose**: Device firmware updates
- **Components**:
  - `UserInterface.Business.ViewModels/FirmwareInstallFlow.cs` - ViewModel
  - `UserInterface.Business.Views.Flows/FirmwareInstallFlow.xaml.cs` - View (code-behind)
  - `UserInterface.Business.Views.Flows/FirmwareInstallFlowControl.cs` - View base class (DependentFlowControl<FirmwareInstallFlow>)
  - `UserInterface.Business.Services/Firmware.cs` - Firmware service
- **Steps** (`FirmwareInstallFlowStep`): DevicesNotReady, FailedUpdate, Start, SelectUpdate, DoUpdate, VerifyUpdate, Complete
- **Main ViewModel members**: `CurrentStep`, `IsNewUpdateAvailable`, `PackagedFirmwareName`, `PackagedFirmwareChangelog`, `SelectedFirmwarePath`, `SelectedFirmwareFileName`, `IsSelectedFirmwareValid` (bool?), `AreDevicesReady`, `BaseRequiresManualRestart`, `HeadRequiresManualRestart`, `UpdateLog`, `CurrentTask`/`BaseTask`/`HeadTask` (TaskDescription), commands `CancelCommand`, `PreviousStepCommand`, `NextStepCommand`, `SelectFirmwareCommand`

### 2. **Pair Devices Flow**
- **Purpose**: Base and Head device pairing
- **Components**:
  - `UserInterface.Business.ViewModels/PairDevicesFlow.cs` - ViewModel
  - `UserInterface.Business.Views.Flows/PairDevicesFlow.xaml.cs` - View (code-behind)
  - `UserInterface.Business.Views.Flows/PairDevicesFlowControl.cs` - View base class
  - `UserInterface.Business.Services/Pairing.cs` - Pairing service
- **Steps** (`PairDevicesFlowStep`): UnsupportedFirmware, Error, Prepare, Process, Complete
- The `Pairing` service exposes the method `PairDevices()`

### 3. **Options Flow**
- **Purpose**: Application options configuration
- **Components**:
  - `UserInterface.Business.ViewModels/OptionsFlow.cs` - ViewModel
  - `UserInterface.Business.Views.Flows/OptionsFlow.xaml.cs` - View (code-behind)
  - `UserInterface.Business.Views.Flows/OptionsFlowControl.cs` - View base class

### 4. **Support Report Flow**
- **Purpose**: Support report generation
- **Components**:
  - `UserInterface.Business.ViewModels/SupportReportFlow.cs` - ViewModel
  - `UserInterface.Business.Views.Flows/SupportReportFlow.xaml.cs` - View (code-behind)
  - `UserInterface.Business.Views.Flows/SupportReportFlowControl.cs` - View base class

---

## Windows and VR Overlays

### Standard Windows (extend `AppWindow`, from UserInterfaceLib)
- **UtilityWindow** - Main utility window
- **ToolsWindow** - Debugging tools window (opened by `SettingsNotificationButton.OpenToolsCommand`)
- **ProductionTestWindow** - Production test window

### VR Overlays (SteamVR, extend `VRWindow`, from UserInterfaceLib)
- **BatteryOverlay** - Battery status overlay in VR
- **DashboardOverlay** - Dashboard overlay in VR

### OpenVR Integration
- Uses the `UserInterfaceLib.OpenVR` namespace (internal to the UserInterfaceLib library)
- Registers the nofio driver: `VR.Install.AddDriver()` with path `Resources\nofio_driver`
  (if OpenVR is already present; otherwise `VRWatcher.Initialize()` waits for SteamVR)
- Creates VR windows: `MicrosoftExtensionsHosting.CreateVRWindow<T>()`
- OpenVR key: `nofio.UserInterface`
- Details in the [Driver Management](#driver-management) section

---

## Error Handling and Logging

### Error Reporting
- **Sentry** - Remote error reporting, initialized by `ErrorReporting` (`[Singleton]`)
- DSN: `https://<redacted>@<org>.ingest.sentry.io/<project>` (redacted; it is
  the client-side DSN embedded via the `[Dsn]` attribute in AssemblyInfo.cs)
- Init options (verified from source): `AutoSessionTracking = true`,
  `IsGlobalModeEnabled = true`, `Release` = `AssemblyInformationalVersion` (0.1.0+e6f8f66f-dirty)
- There is no explicit minimum level filter in the init; `ErrorReporting`
  exposes the `BreadcrumbAdding` and `EventSending` events
  (BeforeBreadcrumb/BeforeSend hooks) and logs breadcrumbs to the local
  logger; the DSN is read from the assembly attribute

### Local Logging
- **File logging** (NReco.Logging.File):
  - File: `%APPDATA%/IMRNext/nofio/nofio.log`
  - Append: true
  - Max file size: 409,600 bytes (~400KB)
  - Max rolling files: 10

- **EventLog** (Microsoft.Extensions.Logging.EventLog):
  - Source: `nofio.UserInterface`
  - Filter: Warning and above

### Breadcrumb Tracking (Sentry)
- Managed by `PersistentState` for critical operations
- Levels: Info, Debug, Warning, Error

---

## Configuration and Persistence

### Persistence Path
- Base: `%APPDATA%/IMRNext/nofio/`
- State file: `nofio.json`
- Log file: `nofio.log`

### Persistence Format
- **JSON** via System.Text.Json
- Automatic serialization via the `Persistence` service
- Save trigger: ApplicationStopping event

---

## Enums and Key Types

### State Enums (defined in `UserInterface.Business.Models.Enums/`)
- **OverallStatus**: Unknown, DevToolRunning, BaseNotConnected, HeadNotConnected, HeadLostConnection, VirtualHereDriverMissing, VirtualHereError, HeadNotPaired, PairingError, Pairing, WaitingForHeadset, WaitingForHeadsetUsbConnection, WaitingForHeadsetUsbDevices, WaitingForHeadsetDisplay, Standby, ConnectionDropped, VideoStarting, Active
- **PairingStatus**: Unknown, Unsupported, Error, NotPaired, Pairing, Paired
- **PairDevicesFlowStep**: UnsupportedFirmware, Error, Prepare, Process, Complete
- **FirmwareInstallFlowStep**: DevicesNotReady, FailedUpdate, Start, SelectUpdate, DoUpdate, VerifyUpdate, Complete
- **SupportReportFlowStep**: Pending, GeneratingReport, Complete
- **VideoState**: HMDVideo, PCVideo, VideoAck, Active, WirelessDrop, BridgeNotConfigured, BridgeError, VideoDisabled
- **VirtualHereStatus**: Unknown, UnknownError, DriverNotInstalled, DriverInstallError, Starting, Configuring, Ready, ConnectedNoDevices, Active
- **DeviceCommand**: Reboot, RestartController
- **DriverInstallResult**: Success, Cancelled, UnknownError
- **NotificationUrgency**: Normal, Warning, Urgent, Persistent
- **DisconnectReason** (in `NofioApi/`): Normal, NoPathFound, ConnectRefused, ConnectTimedOut, ConnectionBusy, ConnectionAborted, PoliteDisconnect, PacketHeaderError, PacketDestinationMismatch, PacketStreamError, PacketSequenceError, RemoteOldVersion, LocalOldVersion, UnhandledNakError, DevToolOverride, Unknown

### API Message Types
- **Message** - Abstract base class: `Type` (MessageType), `IsValid`, nested `Header` with `Tag` (MessageTag)
- **Packet** - Packet header with `Source`/`Destination` (Device), `Sequence`, IsStart/IsEnd flags
- **Protobuf** - Container: `Content` (ReadOnlyMemory<byte>), `ContentType` (MessageType)
- **IReply / IReply<T>** - Reply interfaces: `Notify(...)`, `NotifyError(Nak/Disconnect)`, `Task<T> Task`
- **Reply<T>** - Implementation for messages (`T : Message`), TaskCompletionSource-based
- **ProtobufReply<T>** - Implementation for protobuf types (`T : IMessage<T>`), parses the content
- **MessageTag** - ushort: high bits = Device, low bits = TransactionId (masks 0xC000/0x3FFF)
- **MessageErrorCode** - Error codes carried by Naks (uint)

---

## Dependency Injection

### DI Container
- **Ioc.Default** (InjectX.Shared) - Global container
- **Microsoft.Extensions.DependencyInjection** - DI framework
- Configuration in `Program.AddServicesTo()`

### Registered Services
- Convention-based registration via `UserInterfaceLib` extensions:
  - `AddServicesFrom(assembly, "Business.Models", "Business.Services")` - services, the main ones decorated with `[Singleton]`: `NofioInterfaces`, `NofioState`, `NofioConnection`, `PersistentState`, `Firmware`, `Pairing`, `VirtualHere`, `Persistence`, `ImrDevToolMonitor`, `CommandLineInterface`, `ErrorReporting`
  - `AddViewsAndViewModelsFrom(assembly, "Business.Views", "Business.ViewModels")` - views and view models
  - `AddWindowsFrom(assembly, "Business.Windows")` - windows
- The actual lifetimes of views/view models/windows are decided inside
  `UserInterfaceLib` (not decompiled in this project), so they cannot be
  verified from the available source
- `App` is registered explicitly with `services.AddSingleton(typeof(App))`

### Singleton Pattern
```csharp
[Singleton]  // InjectX attribute
public class MyService : ObservableObject, IDisposable
{
    // Implementation
}
```

---

## Network Monitoring

### NofioInterfaces
- Monitors IP address changes via `NetworkChange.NetworkAddressChanged`
- Checks interface availability every 40ms (debounce)
- Monitored addresses:
  - Base: `192.168.3.1`
  - Head: `192.168.4.1`

### ImrDevToolMonitor
- Monitors the external `imr_devtool(.exe)` process
- Detection (verified from source):
  - Initial scan of running processes (case-insensitive match on "imr_devtool")
  - WMI `ManagementEventWatcher`: `SELECT targetInstance FROM __InstanceOperationEvent WITHIN 3 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name LIKE "%imr_devtool%.exe"` (3 s poll on process start/stop)
- Trigger: IsRunning property changed
- Actions: `NofioConnection.OnDevToolStateChanged()` → closes sockets with
  `DisconnectReason.DevToolOverride` and reconnects (the DevTool takes
  direct control of the devices, the app steps aside)

---

## Firmware Management

### Firmware Class (`Firmware.cs`, `[Singleton]`)
- Represents an observable firmware package, not an "installation service":
  it exposes `Version`, `Changelog`, `FirmwarePath` and checks the package
  contents (tar with hash manifest; `hasManifest` field).
- `CheckFirmware()` (called by the constructor) → `IdentifyPackagedFirmware()`
  scans `<app folder>/Resources/Firmware` looking for the newest `.md`
  changelog and `.gz` package
- `ValidateFirmware(path)` → `FirmwareValidity`: compares the SHA1 hashes of
  the manifest (`SHA1SUMS`) with those of the tar entries
- The actual installation logic lives in the `FirmwareInstallFlow` flow and
  in the API requests (`SoftwareUpdateMeta`, `SoftwareUpdateData`,
  `SoftwareUpdateComplete`).

### Firmware Types
- **FirmwareValidity**: Unknown, CorruptContent, MissingContent, NoManifest, InvalidManifest, Valid
- **SoftwareVersion**: message with version information (`Version`,
  `ToDictionary()`, `CheckForVersionMatch()`, `IsOnFallbackFirmware()`)
- **SoftwareFileType** (byte enum): LinuxUb, FpgaBit, ImrOs, ReleaseZip, Firmware, SupportReport, FoveationConfig, Nothing, NothingReboot
- **SoftwareUpdateData**: 65,523-byte packets (`DataLength`) with `PacketIndex`

---

## Device Pairing

### Pairing Service (`Pairing.cs`, `[Singleton]`)
- Handles the pairing process between Base and Head via the `Pairing` protobuf
  message (MessageType 158, requires protocol >= 76)
- Main method: `PairDevices()`
- States tracked in `PairingStatus`: Unknown, Unsupported, Error, NotPaired, Pairing, Paired

---

## VirtualHere Integration

### VirtualHere Service (`VirtualHere.cs`, `[Singleton]`)
- Integration with VirtualHere (USB over network, needed for the headset's USB devices)
- Properties: `Status` (VirtualHereStatus), `IsDriverInstalled` (bool?), `IsConnected` (bool)
- Constructor: receives `NofioInterfaces` as a dependency (observes `IsBaseAvailable`)
- Methods: `InstallDriver()`, `UninstallDriver()` → `Task<DriverInstallResult>` (Success, Cancelled, UnknownError)
- States (`VirtualHereStatus`): Unknown, UnknownError, DriverNotInstalled, DriverInstallError, Starting, Configuring, Ready, ConnectedNoDevices, Active
- For driver detection, client lifecycle and API command details see the
  [Driver Management](#driver-management) section

---

## Driver Management

The application manages **two distinct drivers**, in two separate places of
the codebase.

### 1. SteamVR/OpenVR Driver - `Resources\nofio_driver` (App.xaml.cs)

Not a Windows driver: it is the **SteamVR driver package** that makes the
nofio headset visible to SteamVR (HMD + tracking). Without this
registration SteamVR would not see the device.

```
App() (constructor)
    ├── VR.Install.State == 1 (OpenVR detected)
    │     → log "OpenVR detected, ensuring Nofio driver is installed."
    │     → VR.Install.AddDriver(<app folder>\Resources\nofio_driver)
    │         (OpenVR VRPathRegistry API: registers the path among
    │          SteamVR's external drivers; Task<VRPathRegResponse> reply)
    └── otherwise
          → log "Starting VR watcher..."
          → VRWatcher.Initialize()   (waits for SteamVR to be installed and
            registers the driver as soon as OpenVR appears)
```

- Also sets `Overlay.KeyPrefix = "nofio.UserInterface."` (for the VR overlays)
- The `VRInstall`/`VRWatcher` logic lives in `UserInterfaceLib.OpenVR` (not decompiled)

### 2. VirtualHere Kernel Driver - `vhusb3hc` (VirtualHere.cs)

**Why VirtualHere.cs "installs a driver"**: nofio works over
USB-over-network. The headset's USB devices are physically connected to the
Base and are presented to Windows as local USB by the VirtualHere client;
the kernel driver `vhusb3hc` (virtual USB3 host controller) must therefore
be installed on the PC.

| Phase | Mechanism (verified from source) |
|---|---|
| Detection | WMI: `SELECT * FROM Win32_SystemDriver WHERE Name = 'vhusb3hc'` (Count > 0), in `GetIsDriverInstalled()`; invoked by the ctor (`UpdateIsDriverInstalled()`) and re-run after every command |
| Installation | Launches `Resources\vhui64.exe -d` with `UseShellExecute=true`, `Verb="runas"` (UAC elevation): the VirtualHere client installs the kernel driver |
| Uninstallation | `Resources\vhui64.exe -y` with `Verb="runas"` |
| Cancelled | `Win32Exception` 1223 (UAC declined) → `DriverInstallResult.Cancelled` |

### 3. VirtualHere Client - `vhui64.exe` (process, not a driver)

The app bundles the VirtualHere GUI client (`Resources\vhui64.exe`, config
`Resources\vhui.ini`) and controls its entire lifecycle:

```
OnNofioInterfacesChanged (Base becomes available)
    ├── driver absent       → Status = DriverNotInstalled
    └── driver present
        → Starting:            launches vhui64.exe -g -l OSEventLog -c "Resources\vhui.ini"
        → Configuring:         pipe "AUTO USE ALL" (automatic device use)
        → ConnectedNoDevices
        → poll "GET CLIENT STATE" every 1.5 s (ThreadedClock, 1500 ms)
            ├── devices in use → Active
            └── otherwise      → Ready
```

- Communication over named pipe `vhclient`
  (`NamedPipeClientStream(".", "vhclient", InOut, Async)`)
- Observed API commands: `AUTO USE ALL`, `AUTO USE CLEAR ALL`,
  `STOP USING ALL`, `GET CLIENT STATE`, `EXIT`
- XML replies (`XmlReader` with `ConformanceLevel.Fragment` over a
  1024-byte `CircularBufferStream`) are mapped into `VirtualHereState`
  (Servers/ServerRecord/DeviceRecord, record structs)
- `IsConnected` = false on pipe close/error

### Impact on overall status (NofioState.DetermineStatus)

- `VirtualHereStatus.DriverNotInstalled` → `OverallStatus.VirtualHereDriverMissing`
- VirtualHere errors (`UnknownError`, `DriverInstallError`) → `OverallStatus.VirtualHereError`

### UI entry points for driver commands

All UI commands touching the driver converge on
`VirtualHere.InstallDriver()` / `UninstallDriver()`:

- `DeviceStatus.RunDriverInstallCommand` → `_virtualHere.InstallDriver()`
- `ToolsWindow.HandleToggleDriverCommand` → toggle: installed →
  `UninstallDriver()`, absent → `InstallDriver()` (ToolsWindow also exposes
  an `IsDriverInstalled` DependencyProperty)
- `SettingsNotificationButton` → shows the "Install Driver" notification
  when `_virtualHere.IsDriverInstalled != true`

### Exhaustive search: no other drivers

Verified that the codebase contains **no** other local driver mechanisms or
system APIs:

- No SetupAPI (`SetupDi*`), no `Win32_PnPEntity` / `Win32_PnPSignedDriver`
  queries, no DriverStore, `pnputil`, `.inf` / `.sys` / `.cat` files
- No Registry access, no DllImport / native P-Invoke
- The only three `Process.Start` calls are all in `VirtualHere.cs`:
  `vhui64.exe -d` (install driver), `-y` (uninstall driver),
  `-g -l OSEventLog -c <vhui.ini>` (client start)
- The only WMI queries in the whole codebase: `Win32_SystemDriver WHERE
  Name='vhusb3hc'` (VirtualHere.cs) and the process watcher of
  `ImrDevToolMonitor` (see [Network Monitoring](#network-monitoring))
- `OpenTK.Mathematics` (used only in `BatteryOverlay`) is vector math to
  position the VR overlay in 3D space, not a driver
- The firmware is not a local driver: it is transferred to the devices over
  the TCP protocol (`SoftwareUpdateMeta` → `Data` → `Complete`)

---

## Command Line Interface

### CommandLineInterface (`CommandLineInterface.cs`, `[Singleton]`)
- Handles single-instance and argument redirection via Windows App Lifecycle (`AppInstance`)
- If the app is already running, it redirects the activation to the existing
  instance ("Another instance is running, redirecting!") and sets
  `ShouldQuit = true`, making the new instance exit
- Exposes `ShouldQuit` (readonly), used by `Program.Main()` to decide whether to exit

---

## Unreferenced External Dependencies

From AssemblyInfo.cs:
- **Sentry.ProjectDirectory**: `C:\Users\Nathan\Documents\git\steamvr_integration\UserInterface\`
- Suggests the project is part of a larger SteamVR integration system

---

## Security and Protections

- **SuppressIldasm** attribute in AssemblyInfo.cs (anti-decompilation)
- **Sentry** for error monitoring
- **File logging** for debugging
- **EventLog** for system logging

---

## Summary Statistics

- **C# files**: 93 files (plus 20 XAML files)
- **Main namespace**: `UserInterface`, `UserInterface.Business.*`
- **Patterns**: MVVM + Dependency Injection
- **UI**: WPF + VR overlays (SteamVR)
- **Communication**: TCP + Protocol Buffers
- **Persistence**: JSON + File System

---

## Architecture Diagram (Textual)

```
┌─────────────────────────────────────────────────────────────┐
│                        nofio-utility                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   Program    │────▶│     App     │────▶│  MainWindow  │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│          │                   │                            │   │
│          ▼                   ▼                            ▼   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Host Configuration                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │ AppConfig   │  │   Logging    │  │  Services    │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│          │                                                 │
│          ▼                                                 ▼
│  ┌─────────────────────┐          ┌─────────────────────┐   │
│  │   NofioInterfaces    │          │   NofioConnection    │   │
│  │  - IsBaseAvailable   │          │  - _baseSocket      │   │
│  │  - IsHeadAvailable   │◀─────────▶│  - _headSocket      │   │
│  └─────────────────────┘          │  - SendRequest()    │   │
│                                    └──────────┬─────────┘   │
│                                               │             │
│                                               ▼             │
│                                      ┌─────────────────┐    │
│                                      │   NofioState     │    │
│                                      │  - IsBaseConnected│   │
│                                      │  - IsHeadConnected│   │
│                                      │  - WiFiChannel    │   │
│                                      │  - Firmware       │   │
│                                      └──────────┬────────┘    │
│                                                 │             │
│          ┌─────────────────────┐     ┌─────────▼───────┐    │
│          │   PersistentState    │     │    ViewModels     │    │
│          │  - Settings          │◀────▶│  - DeviceStatus  │    │
│          │  - Logging           │     │  - BatteryNotification│ │
│          │  - NofioHardware    │     │  - Flow VMs       │    │
│          └─────────────────────┘     └─────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│                  ┌──────────────────────────────────────┐   │
│                  │            Persistence Service         │   │
│                  │   nofio.json (load/save on exit)       │   │
│                  └──────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Connected to:
- Base Device: 192.168.3.1:34566 (TCP)
- Head Device: 192.168.4.1:34568 (TCP)
- OpenVR: nofio.UserInterface
- SteamVR Driver: Resources\nofio_driver
```

---

## Step-by-Step Guide: How to Talk to the Nofio Hardware (for humans)

This section explains in plain words **what happens** when the PC
communicates with the Base and the Head, and **how** we found out. All
statements were verified on real hardware (firmware v2.5.0) with the
`scripts/nofio_probe.py` tool. The complete technical reference is
[PROTOCOL.md](PROTOCOL.md).

### 1. The physical picture

```
PC ──USB cable──> Nofio Base (192.168.3.1) ~~~60GHz wireless~~~ Nofio Head (192.168.4.1)
```

- The Base connected to the PC presents itself as a **USB network card**
  (CDC-Ethernet): the PC receives an IP like `192.168.3.49` from the Base.
- The Head has **no cable to the PC**: it is linked to the Base by radio.
- Only the network is needed: **no driver**. On Linux it is enough that the
  interface exists (`enp0s20f0u3u1` in our case).

Summary of the channels (verified by exclusion over the whole codebase:
zero SetupAPI/HID/DllImport/USB in the app - only TCP sockets):

| Channel | What | Medium |
|---|---|---|
| TCP 34566 (Base) / 34568 (Head via radio) | status, telemetry, config, pairing, **firmware flash** | IP (USB cable to the Base, then radio) |
| TCP 7575 | the Index's USB devices via VirtualHere | IP, same path |
| DisplayPort → OCuLink | video | dedicated cable (FPGA), NOT network |
| USB cable | Base power + network | USB |

So: all control is TCP/IP — even the USB cable to the Base carries only IP
(there is no USB control protocol), and firmware flashing also travels over
the network. The only things outside the network: video and power.

### 2. The three layers of communication

Think of an envelope inside an envelope inside an envelope:

1. **TCP**: the "pipe" to the Base (`192.168.3.1`, port `34566`).
2. **Packet** (outer envelope, 9-byte header + content): says *who sends*,
   *who must receive* (PC=0, Base=1, Head=2, PC2=3), *what order number it
   has* (every packet is numbered: if one is skipped the device closes the
   connection), and *how much content there is*.
3. **Message** (inner envelope, the packet's content): has a *tag* (a number
   identifying the conversation, so each reply knows which question it
   belongs to) and a *type* (which command it is: 2=Connect, 4=Heartbeat,
   128=RequestStatus, etc.), then the *data*.

Every number is written **big-endian** (most significant bytes first, like
counting "thousands-hundreds-tens-units").

### 3. The "hello" (handshake) - including the story of our mistake

When you connect, the Base does not talk to you until you greet each other
like this:

1. The PC sends `Connect` containing its protocol version (**80**)
2. The Base replies with **its own** `Connect` (its version, also 80)
3. The PC replies `Ack` ("received") - and the connection is established

Field discovery: we had reconstructed the handshake wrongly (we waited for
an `Ack` from the Base that never arrives). Result: timeout. Looking at the
real traffic we saw the Base replying with a `Connect` of its own - and the
decompiled code confirms that the app, in that case, sends `Ack`
(`SendMessage(e.From, new Ack(), connect.Tag)`).

There is also a clock: the Base answers every "beat" (heartbeat, one per
second) with `3000` - its way of saying "if you do not talk to me for 3
seconds I disconnect you". That is why our first sessions died after ~2-3
seconds.

### 4. Asking questions

The universal command is `RequestStatus`: "tell me X", where X is the
message type you expect as the reply. Real example, byte by byte:

```
PC -> Base:  [packet: from=0(PC) to=1(Base) num=2] [message: tag=0x4002 type=128] 00 86
             00 86 = 134 = "SoftwareVersion"

Base -> PC: [message: tag=0x4002 type=134] <length> <text>
             same tag = "this is the answer to your question"
```

The text is the firmware version, on multiple lines: `release=v2.5.0`,
`hw_serial=240104-02E3-NI-b`, `fpga=spark-60...`, etc.

If the device cannot answer, it sends a `Nak` with an error code (e.g.
`InvalidStatusRequest`: "I do not accept this question from here").

### 5. Talking to the Head (the most important discovery)

The Head lives on another network (`192.168.4.x`) that the Base does **not**
let the PC reach (it answers "network unreachable"). We therefore thought we
could not talk to it without connecting it directly.

Wrong: the packet header has a "recipient" field, and the Base knows how to
**forward packets to the Head over radio**. Just open a connection to the
Base and write "recipient: Head (2)":

```
PC → Base → (radio) → Head:   Connect... complete handshake
Head → (radio) → Base → PC:   Head's replies
```

Everything works: handshake, heartbeat, queries. And the Head's packet
identity has its *own* counter (separate from the Base's).

### 6. Session rules (learned the hard way)

- **One TCP connection = one device**: if after talking to the Head you ask
  the Base a question on the same connection, the Base sends `Disconnect`
  and kicks you out. The original app uses two separate sockets - now we
  know why.
- Routing to the Head is "transparent": you do not need to greet the Base
  before talking to the Head.
- Packets must be numbered in order (0, 1, 2...); each direction and each
  device has its own counter.

### 7. What we obtained so far

| Device | Firmware | Notes |
|---|---|---|
| Base | v2.5.0 | board `mipi_base`, serial 240104-02E3-NI-b |
| Head | v2.5.0 | board `dp_head`, serial 240104-074D-NI-h |

- `BaseStatus` (via `python3 scripts/nofio_probe.py state`): real
  temperatures (Cpu 57C, Fpga 55C, Baseband 42C), WiFi 6E (MCS 7/7, channel
  13 at 6015 MHz, RSSI 97, Isax=1), state `PairingSuccess | ConnectionOk`
- `HeadStatus` (from the Head, `state --target head`): **charge of the USB-C
  powerbank feeding the Head** (`LeftBatteryCharge`: observed in real time
  96 → 92 → 88 → 76% over ~1.5 h of session; it is the value shown by the
  battery overlay in the original app's VR UI), second power input
  (`RightBatteryCharge`, stuck at 1% with a single pack connected),
  `PeakUncompressedVideoTXSpeed64` = 2.058 Gbps, CPU 60C.
  NB: these are NOT the Index controller batteries, despite the name
  (field-verified correction). Online check (official nofio.co store +
  Kickstarter-era FAQ): the Head is designed for USB-C battery hot-swap
  (~2.5 h each, <15W, USB-PD, swap in ~20 s without restarting SteamVR); the
  observed drain rate (96 → 70% in ~2 h) matches the advertised battery life.
- `PeerInfo` from the Base: "my wireless peer is the Head (2), protocol 80"

The protobuf field names are now known: `ProtobufTypes.dll` was deobfuscated
(de4dot) and decompiled (ilspycmd). The reconstructed schema is in
`docs/protos/nofio.proto` (messages: BaseStatus, HeadStatus, Setup, Pairing,
Configuration); the decompiled source remains in the git-ignored
`miscellaneous/nofio-decompiled/ProtobufTypes-decompiled/`.

### 8. How to reproduce everything

```sh
python3 scripts/nofio_probe.py status                    # Base firmware
python3 scripts/nofio_probe.py status --target head      # Head firmware (via Base)
python3 scripts/nofio_probe.py state                     # decoded BaseStatus
python3 scripts/nofio_probe.py state --target head       # decoded HeadStatus
python3 scripts/nofio_probe.py battery                   # Head battery % (powerpack)
python3 scripts/nofio_probe.py battery --watch           # continuous battery monitor
python3 scripts/nofio_probe.py raw 128 0081              # BaseStatus (protobuf bytes)
python3 scripts/nofio_probe.py monitor --duration 10     # everything that arrives
```

Every command opens its own connection, greets (handshake), asks, and
politely closes (`Disconnect`). No driver, no app, just the network.

---

## Final Notes

1. **Decompiled Code**: The code appears decompiled from IL (Intermediate
   Language), with many compiler-generated structures (`_003C_003E` prefix
   for compiler-generated classes).

2. **Code Quality**: Despite the decompilation, the architecture is well
   structured with:
   - Clear separation between View, ViewModel, Services
   - Consistent use of DI and MVVM patterns
   - Centralized error handling (Sentry)
   - Complete logging

3. **Active Development**: Version 0.1.0.0 with commit hash
   `e6f8f66f-dirty` suggests ongoing development.

4. **VR Integration**: Strong integration with SteamVR/OpenVR for overlays
   in virtual reality.

5. **Network-Centric**: The application is deeply dependent on network
   connectivity with specific devices (Base and Head).
