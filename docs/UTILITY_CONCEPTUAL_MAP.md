# Conceptual Map - nofio-utility-cleaned

> Source: static reverse engineering of the decompiled `nofioUtility.exe`
> (WPF/.NET 7 utility by IMRNext). The decompiled tree lives outside the
> published repository (`miscellaneous/nofio-decompiled/`, git-ignored);
> this document and [UTILITY_CODEBASE_ANALYSIS.md](UTILITY_CODEBASE_ANALYSIS.md)
> are the English rewrite of the original Italian analysis notes.

## Index

1. [Hierarchical Overview](#1-hierarchical-overview)
2. [Component Map](#2-component-map)
3. [Dependency Map](#3-dependency-map)
4. [Data Flow](#4-data-flow)
5. [Class and Interface Map](#5-class-and-interface-map)
6. [Namespace Map](#6-namespace-map)
7. [Component Relations](#7-component-relations)

---

## 1. Hierarchical Overview

```
nofio-utility-cleaned
├── 📦 PACKAGE: UserInterface (Root)
│
├── 🎯 ENTRY POINTS
│   ├── Program.cs (Main, Configuration, DI Setup)
│   └── App.xaml.cs (WPF Application, Initialization)
│
├── 🏗️ INFRASTRUCTURE
│   ├── Properties/AssemblyInfo.cs (Metadata, Versioning, Sentry DSN)
│   ├── nofioUtility-cleaned.csproj (Project Configuration)
│   └── UserInterface.Resources.DashboardIcon.png (embedded) + app.ico
│
├── 🧠 BUSINESS LAYER
│   │
│   ├── 📊 MODELS (Data)
│   │   ├── PersistentState.cs (Root state container)
│   │   ├── TaskDescription.cs
│   │   ├── VirtualHereState.cs
│   │   │
│   │   ├── Persistent/ (Persistent data)
│   │   │   ├── Settings.cs (User preferences)
│   │   │   ├── NofioHardware.cs (Hardware info)
│   │   │   ├── Logging.cs (Log configuration)
│   │   │   └── ThemePreference.cs (Theme enum)
│   │   │
│   │   └── Enums/ (State/flow enumerations)
│   │       ├── OverallStatus.cs
│   │       ├── PairingStatus.cs
│   │       ├── PairingStatusMethods.cs (helper for PairingStatus)
│   │       ├── FirmwareValidity.cs
│   │       ├── FirmwareInstallFlowStep.cs
│   │       ├── PairDevicesFlowStep.cs
│   │       ├── SupportReportFlowStep.cs
│   │       ├── VideoState.cs
│   │       ├── VirtualHereStatus.cs
│   │       ├── DeviceCommand.cs
│   │       ├── DriverInstallResult.cs
│   │       └── NotificationUrgency.cs
│   │
│   ├── ⚙️ SERVICES (Logic)
│   │   ├── Core Services/
│   │   │   ├── NofioInterfaces.cs (Network interface monitoring)
│   │   │   ├── NofioState.cs (Device state management)
│   │   │   ├── NofioConnection.cs (Socket connections)
│   │   │   ├── NofioSocket.cs (Custom socket implementation)
│   │   │   ├── NofioRequests.cs (API requests)
│   │   │   ├── Pairing.cs (Device pairing)
│   │   │   ├── Firmware.cs (Firmware management)
│   │   │   ├── VirtualHere.cs (VirtualHere integration)
│   │   │   ├── Persistence.cs (Data persistence)
│   │   │   ├── ErrorReporting.cs (Sentry integration)
│   │   │   ├── CommandLineInterface.cs (CLI parsing)
│   │   │   └── ImrDevToolMonitor.cs (DevTool monitoring)
│   │   │
│   │   └── NofioApi/ (Communication Protocol)
│   │       ├── Device.cs (Device enum)
│   │       ├── DeviceContext.cs
│   │       ├── DisconnectException.cs
│   │       ├── DisconnectReason.cs
│   │       ├── IReply.cs (Reply interface)
│   │       ├── IReplyExtensions.cs
│   │       ├── Message.cs (Base message)
│   │       ├── MessageErrorCode.cs
│   │       ├── MessageTag.cs
│   │       ├── MessageType.cs (Message types)
│   │       ├── MessageTypeAttribute.cs
│   │       ├── MinimumProtocolAttribute.cs
│   │       ├── NakException.cs
│   │       ├── Packet.cs
│   │       ├── ProtobufTypeAttribute.cs
│   │       ├── UnexpectedReplyException.cs
│   │       ├── Replies/ (Reply types)
│   │       │   ├── ProtobufReply.cs
│   │       │   └── Reply.cs
│   │       └── Messages/ (Message types)
│   │           ├── Ack.cs
│   │           ├── Connect.cs
│   │           ├── Disconnect.cs
│   │           ├── Heartbeat.cs
│   │           ├── Nak.cs
│   │           ├── Protobuf.cs
│   │           ├── RequestStatus.cs
│   │           ├── SoftwareFileType.cs
│   │           ├── SoftwareUpdateComplete.cs
│   │           ├── SoftwareUpdateData.cs
│   │           ├── SoftwareUpdateMeta.cs
│   │           └── SoftwareVersion.cs
│   │
│   └── 🎨 VIEWS & VIEWMODELS (UI Logic)
│       ├── ViewModels/
│       │   ├── BatteryNotification.cs
│       │   ├── DeviceConnectionSummary.cs
│       │   ├── DeviceStatus.cs
│       │   ├── SettingsNotificationButton.cs
│       │   ├── FirmwareInstallFlow.cs
│       │   ├── OptionsFlow.cs
│       │   ├── PairDevicesFlow.cs
│       │   └── SupportReportFlow.cs
│       │
│       ├── Views/
│       │   ├── BatteryNotification.cs
│       │   ├── DeviceConnectionSummary.cs
│       │   ├── DeviceStatus.cs
│       │   └── SettingsNotificationButton.cs
│       │
│       ├── Views.Flows/ (TOP-LEVEL folder: UserInterface.Business.Views.Flows/)
│       │   ├── FirmwareInstallFlow.xaml(.cs) + FirmwareInstallFlowControl.cs
│       │   ├── OptionsFlow.xaml(.cs) + OptionsFlowControl.cs
│       │   ├── PairDevicesFlow.xaml(.cs) + PairDevicesFlowControl.cs
│       │   └── SupportReportFlow.xaml(.cs) + SupportReportFlowControl.cs
│       │
│       └── Windows/ (Windows)
│           ├── BatteryOverlay.cs (VR Overlay)
│           ├── DashboardOverlay.cs (VR Overlay)
│           ├── ProductionTestWindow.cs
│           ├── ToolsWindow.cs
│           └── UtilityWindow.cs (Main window)
│
└── 🎨 PRESENTATION LAYER
    ├── UserInterface.Controls/ (Custom controls)
    │   ├── Battery.xaml(.cs)
    │   └── TitleBar.xaml(.cs)
    │
    ├── UserInterface.Business.Views.Flows/ (Flow views: XAML + code-behind
    │   + base classes *FlowControl : DependentFlowControl<UserInterface.Business.ViewModels.XxxFlow>)
    │   ├── FirmwareInstallFlow.xaml(.cs) / FirmwareInstallFlowControl.cs
    │   ├── OptionsFlow.xaml(.cs) / OptionsFlowControl.cs
    │   ├── PairDevicesFlow.xaml(.cs) / PairDevicesFlowControl.cs
    │   └── SupportReportFlow.xaml(.cs) / SupportReportFlowControl.cs
    │
    └── XAML Files (in business/ and properties/ directories)
        ├── batterynotification.xaml
        ├── deviceconnectionsummary.xaml
        ├── devicestatus.xaml
        ├── flows/ (Flow XAMLs)
        │   ├── firmwareinstallflowsteps.xaml
        │   ├── pairdevicesflowsteps.xaml
        │   └── supportreportflowsteps.xaml
        ├── settingsnotificationbutton.xaml
        └── windows/ (Window XAMLs)
            ├── batteryoverlay.xaml
            ├── dashboardoverlay.xaml
            ├── productiontestwindow.xaml
            ├── toolswindow.xaml
            └── utilitywindow.xaml
```

---

## 2. Component Map

### Main Components by Category

#### 🔌 **Communication Components**
```
┌────────────────────────────────────────────────────────────┐
│                      COMMUNICATION                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────┐     ┌─────────────────┐              │
│  │  NofioInterfaces │     │  NofioConnection │              │
│  │                  │     │                  │              │
│  │ • IsBaseAvailable│     │ • _baseSocket    │              │
│  │ • IsHeadAvailable│     │ • _headSocket    │              │
│  │ • Timer (40ms)   │     │ • SendRequest()  │              │
│  │ • NetworkChange  │     │ • BeginConnecting│              │
│  └────────┬─────────┘     └────────┬────────┘              │
│           │                        │                        │
│           │ Monitors               │ Manages                │
│           │ IP addresses           │ connections            │
│           ▼                        ▼                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │                   API PROTOCOL                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐   │    │
│  │  │   Message    │  │  Protobuf   │  │ IReply<T>  │   │    │
│  │  │              │  │              │  │            │   │    │
│  │  │ • Type       │  │ • ContentType│  │ • Task<T>  │   │    │
│  │  │ • IsValid    │  │ • Content    │  │ • Notify() │   │    │
│  │  │ • Header(Tag)│  │              │  │ • NotifyError()│ │    │
│  │  └─────────────┘  └─────────────┘  └────────────┘   │    │
│  │                                                     │    │
│  │  Message Types: Connect, Disconnect, Heartbeat,      │    │
│  │  Ack, Nak, RequestStatus, Setup, SoftwareUpdate...   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### ⚙️ **State Components**
```
┌────────────────────────────────────────────────────────────┐
│                    APPLICATION STATE                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    NofioState                          │ │
│  │  ┌──────────────────────────────────────────────────┐│ │
│  │  │  DEVICE STATE                                     ││ │
│  │  │  • IsBaseConnected / IsHeadConnected              ││ │
│  │  │  • IsHeadLocal (no IsBaseLocal exists)             ││ │
│  │  │  • LastBaseDisconnectReason / LastHeadDisconnect…  ││ │
│  │  └──────────────────────────────────────────────────┘│ │
│  │                                                       │ │
│  │  ┌──────────────────────────────────────────────────┐│ │
│  │  │  NETWORK INFO                                     ││ │
│  │  │  • WiFiChannel / WiFiCountry                      ││ │
│  │  │  • AvailableWiFiChannels                          ││ │
│  │  └──────────────────────────────────────────────────┘│ │
│  │                                                       │ │
│  │  ┌──────────────────────────────────────────────────┐│ │
│  │  │  FIRMWARE INFO                                    ││ │
│  │  │  • IsFirmwareUpToDate                             ││ │
│  │  │  • IsBaseOnFallback / IsHeadOnFallback            ││ │
│  │  └──────────────────────────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                  PersistentState                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │  Settings    │  │  Logging    │  │NofioHardware│   │ │
│  │  │              │  │             │  │             │   │ │
│  │  │•ThemePref    │  │•LogLevel    │  │(empty:       │   │ │
│  │  │•IsDeveloper  │  │  (dict)     │  │ placeholder) │   │ │
│  │  │•StatusPinned │  │•DefaultLog  │  │              │   │ │
│  │  │•Battery*     │  │  Level      │  │              │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  │                                                       │ │
│  │  File: nofio.json                                     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 🎨 **UI Components**
```
┌────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 MAIN WINDOWS                         │  │
│  │                                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │UtilityWindow│  │ToolsWindow  │  │BatteryOverlay│  │  │
│  │  │  (Main)     │  │ (Debug)     │  │  (VR)        │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                      │  │
│  │  ┌─────────────────┐  ┌──────────────────────┐     │  │
│  │  │DashboardOverlay  │  │ProductionTestWindow  │     │  │
│  │  │  (VR)            │  │                      │     │  │
│  │  └─────────────────┘  └──────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                       FLOWS                           │  │
│  │                                                      │  │
│  │  ┌──────────────────┐  ┌──────────────────┐          │  │
│  │  │FirmwareInstall   │  │PairDevices        │          │  │
│  │  │  Flow            │  │  Flow             │          │  │
│  │  └────────┬─────────┘  └────────┬─────────┘          │  │
│  │           │                     │                    │  │
│  │  ┌────────▼─────────┐  ┌────────▼─────────┐         │  │
│  │  │ Steps            │  │ Steps             │         │  │
│  │  │ (FirmwareInstall │  │ (PairDevicesFlow  │         │  │
│  │  │  FlowStep):      │  │  Step):           │         │  │
│  │  │  Start →         │  │ Prepare →         │         │  │
│  │  │  SelectUpdate →  │  │ Process →         │         │  │
│  │  │  DoUpdate →      │  │ Complete          │         │  │
│  │  │  VerifyUpdate →  │  │ (+errors:         │         │  │
│  │  │  Complete        │  │  UnsupportedFirm, │         │  │
│  │  │ (+errors:        │  │  Error)           │         │  │
│  │  │  DevicesNotReady,│  │                   │         │  │
│  │  │  FailedUpdate)   │  │                   │         │  │
│  │  └──────────────────┘  └──────────────────┘         │  │
│  │                                                      │  │
│  │  ┌──────────────────┐  ┌──────────────────┐          │  │
│  │  │OptionsFlow       │  │SupportReportFlow  │          │  │
│  │  │                  │  │                    │          │  │
│  │  └──────────────────┘  └──────────────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 VIEW COMPONENTS                      │  │
│  │                                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │BatteryNoti- │  │DeviceStatus │  │Battery      │  │  │
│  │  │fication     │  │             │  │(Control)    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                      │  │
│  │  ┌─────────────────┐  ┌──────────────────────┐     │  │
│  │  │DeviceConnection  │  │SettingsNotification  │     │  │
│  │  │  Summary         │  │  Button              │     │  │
│  │  └─────────────────┘  └──────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 🔧 **Support Services**
```
┌────────────────────────────────────────────────────────────┐
│                   SUPPORT SERVICES                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Persistence    │  │  ErrorReporting  │                  │
│  │                 │  │                  │                  │
│  │ • Persist<T>()  │  │ • Sentry init    │                  │
│  │ • Restore<T>()  │  │ • BreadcrumbAdd- │                  │
│  │ • nofio.json    │  │   ing            │                  │
│  │ • System.Text.  │  │ • EventSending   │                  │
│  │   Json          │  │ • breadcrumbs    │                  │
│  │                 │  │   → ILogger      │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Firmware       │  │  Pairing         │                  │
│  │  (class, not    │  │                  │                  │
│  │   an install    │  │ • PairDevices()  │                  │
│  │   service)      │  │                  │                  │
│  │ • Version       │  │                  │                  │
│  │ • Changelog     │  │                  │                  │
│  │ • FirmwarePath  │  │                  │                  │
│  │ • manifest      │  │                  │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  VirtualHere    │  │  ImrDevTool      │                  │
│  │                 │  │  Monitor         │                  │
│  │ • Status (VH   │  │ • IsRunning      │                  │
│  │   Status enum) │  │  (PropertyChanged)│                  │
│  │ • IsDriverInst-│  │                  │                  │
│  │   alled (bool?)│  │                  │                  │
│  │ • IsConnected  │  │ • WMI watcher    │                  │
│  │ • InstallDriver│  │   Win32_Process  │                  │
│  │ • UninstallDrv │  │   (3 s poll)     │                  │
│  │ • vhclient pipe│  │                  │                  │
│  │ • manages      │  │                  │                  │
│  │   vhui64.exe   │  │                  │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │              CommandLineInterface                    │   │
│  │  • Single-instance + argument redirect (AppInstance) │   │
│  │  • ShouldQuit (readonly)                             │   │
│  │  • Instance key: "nofio.UserInterface"               │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Dependency Map

### Internal Dependencies (Between Classes)

```
                      ┌─────────────────────┐
                      │     Program.cs       │
                      │   (Entry Point)      │
                      └──────────┬──────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                         │                        │
        ▼                         ▼                        ▼
┌───────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Host.Builder     │   │   Ioc.Default    │   │AppConfiguration │
│  (Configure)      │   │   (DI Container) │   │   (nofio.json)  │
└──────────┬────────┘   └──────────┬────────┘   └──────────┬──────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │   App.xaml.cs   │   │  NofioState      │   │ NofioInterfaces  │
    │   (WPF App)     │   │   (Singleton)    │   │   (Singleton)    │
    └──────────┬──────┘   └──────────┬──────┘   └──────────┬──────┘
               │                     │                     │
               │                     │                     │
               ▼                     ▼                     ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │  UtilityWindow   │   │  NofioConnection │   │  NetworkChange  │
    │  (Main Window)   │   │   (Singleton)    │   │  (System)       │
    │  + VR Overlays   │   └──────────┬──────┘   └─────────────────┘
    │  (Battery/       │              │
    │  Dashboard)      │   ┌──────────┴──────────┐
    │  created by      │   │                     │
    │  Program.OnApp   │   ▼                     ▼
    │  Startup()       │  ┌─────────────────┐  ┌─────────────────┐
    └─────────────────┘  │ _baseSocket     │  │ _interfaces     │
                          │ (TCP :34566)    │  │ (NofioInterfaces)│
                          └─────────────────┘  └─────────────────┘

    ┌─────────────────┐
    │ _headSocket     │
    │ (TCP :34568)    │
    └─────────────────┘
```

### External Dependencies

```
nofio-utility-cleaned
│
├── Microsoft.NET.Sdk (Framework)
│   ├── System.Runtime
│   ├── System.ComponentModel
│   ├── System.Threading.Tasks
│   └── System.Collections.Generic
│
├── Microsoft.Extensions.* (Hosting & DI)
│   ├── Microsoft.Extensions.Hosting (+ .Abstractions)
│   ├── Microsoft.Extensions.DependencyInjection.Abstractions
│   ├── Microsoft.Extensions.Configuration (+ .Json, .Abstractions)
│   └── Microsoft.Extensions.Logging (+ .Abstractions, .EventLog)
│
├── WPF & Windows
│   ├── System.Windows (WPF)
│   ├── Microsoft.Windows.SDK.NET
│   ├── Microsoft.Windows.AppLifecycle.Projection
│   └── Microsoft.WindowsAppRuntime.Bootstrap.Net
│
├── Logging
│   ├── NReco.Logging.File (File logging)
│   └── Microsoft.Extensions.Logging.EventLog (Windows EventLog)
│
├── Serialization
│   ├── Google.Protobuf (Protocol Buffers)
│   └── System.Text.Json (JSON serialization)
│
├── MVVM & DI
│   ├── CommunityToolkit.Mvvm (ObservableObject, Singleton)
│   └── InjectX.Shared (DI utilities)
│
├── Network
│   ├── System.Net (Sockets, IP addresses)
│   └── System.Net.NetworkInformation (Network interfaces)
│
├── System
│   ├── System.Management (WMI)
│   └── WinRT.Runtime
│
├── Math
│   └── OpenTK.Mathematics
│
├── Error Tracking
│   └── Sentry (Error reporting)
│
└── IMRNext Custom
    ├── UserInterfaceLib (single reference; OpenVR and Extensions
    │   are INTERNAL namespaces of that library, not separate references)
    ├── ProtobufTypes (Custom protobuf types: Imr.Proto)
    └── InjectX.Shared (DI framework)
```

---

## 4. Data Flow

### Main Data Flow (Firmware Update)

```
User triggers         ┌─────────────┐       Selects file         ┌─────────┐
"Update Firmware"     │             │ ──────────────────────────▶│ File    │
┌─────────────────┐   │   UI        │                             │ Dialog │
│  View:           │   │             │                             └─────────┘
│  Firmware        │   └──────┬──────┘                                    │
│  Install Flow    │          │                                            │
└────────┬────────┘          │                                            │
         │                   │                                            │
┌────────▼────────┐          │                                            │
│  ViewModel:      │          │                                            │
│  Firmware        │          │                                            │
│  InstallFlow     │          │                                            │
└────────┬────────┘          │                                            │
         │                   │                                            │
┌────────▼────────┐          │                                            │
│  Class:          │          │                                            │
│  Firmware        │          │                                            │
│  (package:       │          │                                            │
│  Version,        │          │                                            │
│  Changelog,      │          │                                            │
│  FirmwarePath,   │          │                                            │
│  manifest)       │          │                                            │
└────────┬────────┘          │                                            │
         │                   │                                            │
┌────────▼────────┐          │                                            │
│ ValidateFirmware │◀─────────┘                                            │
│ () (Firmware)   │         ┌────────────────────────────────────────────┘
│  • Check SHA1   │         │
│  • Check tar/   │         ▼
│    manifest     │
└────────┬────────┘
         │        ┌─────────────────┐
         │        │ NofioConnection  │
         └───────▶│ SendRequest()   │
                  │                  │
                  │ • Device.Base / │
                  │ • MessageType:  │
                  │   SoftwareUpdate│
                  │   Meta → Data   │
                  │   → Complete    │
                  └────────┬────────┘
                           │
                           ▼
              ┌─────────────────┐         ┌─────────────────┐
              │   Base Device   │         │   Head Device   │
              │   192.168.3.1   │         │   192.168.4.1   │
              │                 │         │                 │
              │  receives the   │         │  (if applicable)│
              │  firmware file  │         │                 │
              └─────────────────┘         └─────────────────┘

              ┌──────────────────────────────┐
              │ Reply<SoftwareUpdateComplete> │  (Ack/Nak + Nak/
              │                              │   Disconnect/UnexpectedReply
              └──────────────────────────────┘   exceptions)

 [Start] → [SelectUpdate] → [DoUpdate] → [VerifyUpdate] → [Complete]
                              │
                              ▼
              ┌─────────────────────────────────────────────┐
              │                Flow Completion               │
              │   ┌─────────┐  ┌─────────┐  ┌─────────┐   │
              │   │ Success │  │ Failed  │  │Cancelled│   │
              │   └─────────┘  └─────────┘  └─────────┘   │
              └─────────────────────────────────────────────┘
```

### Connection Data Flow

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│NofioInterfaces  │       │NofioConnection  │       │  NofioState     │
│                 │       │                 │       │                 │
│ • IsBaseAvail-  │──────▶│ • OnInterfaces  │       │ • OnConnection  │
│   able          │       │   Changed()     │──────▶│   Property      │
│ • IsHeadAvail-  │       │ • BeginConnect- │       │   Changed()    │
│   able         │       │   ingTo()        │       │ • Determine     │
└─────────────────┘       │ • _baseSocket   │       │   Status()     │
                          │ • _headSocket   │       └─────────────────┘
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  NofioSocket    │
                          │                 │
                          │ • Open()        │
                          │ • SendMessage() │
                          │ • Close(reason) │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
          ┌─────────────────┐           ┌─────────────────┐
          │  Base Socket    │           │  Head Socket    │
          │  192.168.3.1:   │           │  192.168.4.1:   │
          │  34566 (TCP)    │           │  34568 (TCP)    │
          └─────────────────┘           └─────────────────┘
```

### Driver & VirtualHere Data Flow

The app manages two distinct drivers, in two separate places:

```
┌─────────────────────────────────────────────────────────────────────────┐
│          DRIVER 1: SteamVR/OpenVR (App.xaml.cs)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  App ctor ──▶ VR.Install.State == 1? (OpenVR detected)                  │
│                 ├── YES ▶ "OpenVR detected, ensuring Nofio driver       │
│                 │        is installed."                                  │
│                 │        VR.Install.AddDriver(Resources\nofio_driver)    │
│                 │        (OpenVR VRPathRegistry API → SteamVR external  │
│                 │         drivers; Task<VRPathRegResponse>)              │
│                 └── NO  ▶ "Starting VR watcher..."                      │
│                          VRWatcher.Initialize()                          │
│                          (waits for SteamVR, then registers the driver) │
│                                                                          │
│  Context: Overlay.KeyPrefix = "nofio.UserInterface." (VR overlay)        │
│  NB: it is the SteamVR driver package that makes the nofio headset       │
│      visible to SteamVR (HMD + tracking), NOT a Windows driver          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│      DRIVER 2: VirtualHere kernel driver vhusb3hc (VirtualHere.cs)       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Why: USB-over-network. The headset's USB devices sit on the Base; the    │
│  VirtualHere client presents them as local USB to Windows. The kernel    │
│  driver vhusb3hc (virtual USB3 host controller) is required on the PC.   │
│                                                                          │
│  Detection:     WMI SELECT * FROM Win32_SystemDriver                     │
│                 WHERE Name = 'vhusb3hc'  (Count > 0)                     │
│                 → UpdateIsDriverInstalled() (ctor + after each command)  │
│                                                                          │
│  Installation:  vhui64.exe -d   with Verb="runas" (UAC elevation)        │
│  Uninstallation:vhui64.exe -y   with Verb="runas"                       │
│  UAC declined:  Win32Exception 1223 → DriverInstallResult.Cancelled      │
│                                                                          │
│  Client lifecycle (vhui64.exe, bundled in Resources\):                   │
│                                                                          │
│    OnNofioInterfacesChanged (Base available)                             │
│        ├── driver absent   → Status = DriverNotInstalled                 │
│        └── driver present                                                │
│            → Starting       launches vhui64.exe -g -l OSEventLog         │
│                            -c "Resources\vhui.ini"                       │
│            → Configuring    pipe "AUTO USE ALL"                          │
│            → ConnectedNoDevices                                          │
│            → poll "GET CLIENT STATE" every 1.5 s (ThreadedClock 1500ms) │
│                ├── devices in use → Active                               │
│                └── otherwise      → Ready                                │
│                                                                          │
│  Communication: named pipe "vhclient" (InOut, Async)                     │
│  Commands: AUTO USE ALL / AUTO USE CLEAR ALL / STOP USING ALL /          │
│            GET CLIENT STATE / EXIT                                        │
│  Replies: XML (XmlReader …)                                              │
│            → VirtualHereState (Servers/ServerRecord/DeviceRecord)        │
│                                                                          │
│  UI entry points (all converge on Install/UninstallDriver):              │
│    • DeviceStatus.RunDriverInstallCommand → InstallDriver()              │
│    • ToolsWindow.HandleToggleDriverCommand → toggle Install/Uninstall    │
│      (with DependencyProperty IsDriverInstalled)                         │
│    • SettingsNotificationButton → "Install Driver" notification           │
│      when IsDriverInstalled != true                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Impact on overall status (NofioState.DetermineStatus):
- VirtualHereStatus.DriverNotInstalled → OverallStatus.VirtualHereDriverMissing
- VirtualHereStatus.UnknownError/DriverInstallError → OverallStatus.VirtualHereError
```

Note (exhaustive search): the codebase contains **no** other drivers or local
system APIs — no SetupAPI/`SetupDi*`, no PnP WMI queries, no
DriverStore/`pnputil`/`.inf`/`.sys`/`.cat`, no Registry access, no
DllImport/P-Invoke. The three existing `Process.Start` calls are all in
`VirtualHere.cs` (`-d`, `-y`, `-g`). The only WMI queries are
`Win32_SystemDriver` (VirtualHere) and the `Win32_Process` watcher in
ImrDevToolMonitor. `OpenTK.Mathematics` (BatteryOverlay) is just math for
overlay positioning, not a driver.

### TCP Protocol Data Flow (verified on real hardware)

Three-layer structure: TCP → packets (9-byte header) → messages (tag + type +
body). All numbers big-endian. Full details in [PROTOCOL.md](PROTOCOL.md);
step-by-step guide in [UTILITY_CODEBASE_ANALYSIS.md](UTILITY_CODEBASE_ANALYSIS.md)
("Step-by-step guide" section).

```
┌─────────────────────────────────────────────────────────────────────┐
│     TYPICAL SESSION (one connection = ONE device)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PC ──TCP 34566──▶ Base (192.168.3.1)                                │
│                                                                      │
│  1. HANDSHAKE                                                       │
│     PC ──▶ Connect(version=80, tag=(dst<<14)|1)                      │
│     Base ──▶ Connect(its own version 80, same tag)                    │
│     PC ──▶ Ack (same tag)          → connected                       │
│                                                                      │
│  2. KEEP-ALIVE                                                       │
│     PC ──▶ Heartbeat(body=0, tag=0)   every 1000 ms                   │
│     Base ──▶ echoes Heartbeat(body=3000)  ← ~3 s timeout:            │
│                                           silent sessions get closed │
│  3. QUERIES                                                          │
│     PC ──▶ RequestStatus{expected type}(new tag)                     │
│     Base ──▶ reply of the requested type (same tag)                  │
│            or Nak(error code)                                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│     BASE → HEAD ROUTING (key dynamic discovery)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  The packet header's Destination field (Head=2) acts as an "address":│
│  the Base forwards packets to the Head over radio, replies come back │
│  on the same TCP connection:                                         │
│                                                                      │
│  PC ──TCP──▶ Base ══radio══▶ Head                                    │
│     Connect(dst=Head) ─────▶ Connect from the Head                   │
│     Ack ─────────────────▶ Head handshake complete                   │
│     RequestStatus ────────▶ HeadStatus (protobuf)                   │
│                                                                      │
│  Rules (verified):                                                    │
│   • 192.168.4.0/24 is NOT reachable at the IP level (ICMP Net        │
│     Unreachable from the Base) — you go through packet routing ONLY  │
│   • transparent routing: no handshake with the Base needed           │
│   • packet sequences tracked PER SOURCE DEVICE                       │
│   • mixing Base queries into a Head session ⇒ Disconnect             │
│                                                                      │
│  Devices successfully queried (firmware v2.5.0):                      │
│   Base: BaseStatus, PeerInfo, SoftwareVersion                        │
│   Head (via Base): SoftwareVersion, HeadStatus                       │
│   Base refuses with Nak(InvalidStatusRequest): HeadStatus, Statistics │
│   Base refuses with Nak(VideoNotConnected): VideoStatus             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Class and Interface Map

### Main Classes by Namespace

#### `UserInterface` (Root)
```
UserInterface
├── App : Application
│   ├── _logger : ILogger<App>
│   ├── _persistentState : PersistentState
│   ├── OnSettingsPropertyChanged()
│   └── Theme management
│
└── Program : static
    ├── Organization = "IMRNext"
    ├── Product = "nofio"
    ├── Component = "UserInterface"
    ├── FullPersistencePath
    ├── Assembly
    ├── AppHost : IHost
    ├── Main() - Entry point
    ├── OnAppStartup() - Window creation
    ├── AddServicesTo() - DI configuration
    └── Exit() - Clean shutdown
```

#### `UserInterface.Business.Models`
```
UserInterface.Business.Models
├── PersistentState : ObservableObject
│   ├── Settings : Settings
│   ├── NofioHardware : NofioHardware
│   ├── Logging : Logging
│   ├── PersistenceService : Persistence
│   └── OnApplicationStopping()
│
├── Settings : ObservableObject
│   ├── ThemePreference
│   ├── IsDeveloper
│   ├── StatusPinned / StatusLocation
│   ├── BatteryOverlayX/Y/Distance/Size
│   └── BatteryOverlayShowText
│
├── NofioHardware : ObservableObject
│   └── (Empty - placeholder for hardware info)
│
├── Logging : ObservableObject
│   ├── LogLevel : Dictionary<string, LogLevel>
│   └── DefaultLogLevel : LogLevel
│
├── ThemePreference : enum
│   ├── Auto
│   ├── Light
│   └── Dark
│
└── (Other models...)
```

#### `UserInterface.Business.Services`
```
UserInterface.Business.Services
├── NofioInterfaces : ObservableObject, IDisposable
│   ├── IsBaseAvailable : bool
│   ├── IsHeadAvailable : bool
│   ├── _eventDebounceTimer : Timer (40ms)
│   ├── OnNetworkAddressChanged()
│   ├── UpdateInterfaceAvailability()
│   └── IsInterfaceUp()
│
├── NofioState : ObservableObject, IDisposable
│   ├── _logger : ILogger<NofioState>
│   ├── ctor(ILogger<NofioState>, NofioConnection, Firmware, Pairing, VirtualHere)
│   │   (NB: does NOT depend on NofioInterfaces)
│   ├── IsBaseConnected / IsHeadConnected : bool (delegates to _connection)
│   ├── IsHeadLocal : bool
│   ├── LastBaseDisconnectReason / LastHeadDisconnectReason : DisconnectReason
│   ├── Status : OverallStatus (computed by DetermineStatus())
│   ├── IsFirmwareUpToDate / IsBaseOnFallback / IsHeadOnFallback : bool
│   ├── WiFiChannel / WiFiCountry : string
│   ├── AvailableWiFiChannels : string[]
│   ├── IsWiFiSetupAvailable : bool
│   ├── DetermineStatus()
│   ├── TryUpdateHardwareFirmwareStatus()
│   ├── QueryBaseWiFiSetup()
│   ├── ChangeWiFiChannel()
│   └── ClearBaseWiFiSetup()
│
├── NofioConnection : ObservableObject, IDisposable
│   ├── _logger : ILogger<NofioConnection>
│   ├── _interfaces : NofioInterfaces
│   ├── _imrDevTool : ImrDevToolMonitor
│   ├── _baseSocket : NofioSocket
│   ├── _headSocket : NofioSocket
│   ├── LastBaseDisconnectReason : DisconnectReason
│   ├── LastHeadDisconnectReason : DisconnectReason
│   ├── IsBaseConnected : bool
│   ├── IsHeadConnected : bool
│   ├── IsHeadLocal : bool (no IsBaseLocal exists)
│   ├── SendRequest<T>()
│   ├── BeginConnectingTo()
│   ├── HandleDisconnect()
│   ├── DoDisconnect()
│   └── OnDevToolStateChanged()
│
├── NofioSocket : ObservableObject
│   ├── (TCP wrapper over TcpClient / NetworkStream)
│   ├── Configure(Device identity, string endpoint, int port)
│   ├── IsOpening : bool
│   ├── IsOpen : bool
│   ├── Open()
│   ├── Close(DisconnectReason)
│   ├── SendMessage(Device, Message, MessageTag?)
│   ├── GetNextTag(Device)
│   └── Opened / Closed / MessageReceived events
│
├── Reply<T> : IReply<T> (in NofioApi.Replies, T : Message)
│   ├── Task<T> Task (TaskCompletionSource)
│   └── NotifyError(Nak) → NakException / NotifyError(Disconnect) → DisconnectException
│
├── ProtobufReply<T> : IReply<T> (in NofioApi.Replies, T : IMessage<T>)
│   └── Parses Protobuf content; wrong type → UnexpectedReplyException
│
├── VirtualHere : ObservableObject, IDisposable
│   ├── ctor(NofioInterfaces)  (observes IsBaseAvailable)
│   ├── Status : VirtualHereStatus
│   ├── IsDriverInstalled : bool?  (WMI: Win32_SystemDriver, Name='vhusb3hc')
│   ├── IsConnected : bool  (vhclient pipe state)
│   ├── InstallDriver() → vhui64.exe -d (runas) → Task<DriverInstallResult>
│   ├── UninstallDriver() → vhui64.exe -y (runas) → Task<DriverInstallResult>
│   ├── DoInstallDriver/DoUninstallDriver (elevated process launch; 1223 = Cancelled)
│   ├── _statePollCheck : ThreadedClock (1500 ms) → OnPresencePollTick()
│   ├── ConnectToClientApi()/ConnectToPipe()/Configure()/CleanupPipe()
│   ├── ApiInvokeCommand(client, command) - "vhclient" pipe commands
│   ├── ExecutablePath : Resources\vhui64.exe
│   └── ConfigPath : Resources\vhui.ini
│
└── (Other services: Pairing, Firmware, Persistence, ErrorReporting, CLI)
```

#### `UserInterface.Business.Services.NofioApi`
```
UserInterface.Business.Services.NofioApi
├── Device : enum
│   ├── PC
│   ├── Base
│   ├── Head
│   ├── PC2
│   └── Max
│
├── DeviceContext
│   └── NextSendId / NextReceiveId : uint, NextTransaction : ushort
│
├── DisconnectReason : enum
│   ├── DevToolOverride
│   ├── NoPathFound
│   └── (others)
│
├── MessageType : enum
│   ├── Connect
│   ├── Disconnect
│   ├── Ack
│   ├── Nak
│   ├── Heartbeat
│   ├── RequestStatus
│   ├── Setup
│   ├── SoftwareUpdateData
│   ├── SoftwareUpdateMeta
│   ├── SoftwareUpdateComplete
│   └── (others)
│
├── IReply / IReply<T> : interface
│   ├── Notify(Message reply)
│   ├── NotifyError(Nak) / NotifyError(Disconnect)
│   ├── NotifyCancelled()
│   └── Task<T> Task (IReply<T>)
│
├── Message : abstract class
│   ├── Type : MessageType
│   ├── IsValid : bool
│   └── Header (nested) with Tag : MessageTag
│       (NB: no Device/Timestamp on Message;
│        Source/Destination/Sequence live in Packet.Header)
│
├── Packet : class
│   ├── Header (nested): Source/Destination (Device), Sequence (uint),
│   │   DataLength, IsStartPacket/IsEndPacket, IsValid
│   └── Header.Data : Memory<byte> (9 bytes)
│
└── Messages/ (Specific message types)
    ├── Ack
    ├── Connect
    ├── Disconnect
    ├── Heartbeat
    ├── Nak
    ├── Protobuf
    ├── RequestStatus
    ├── SoftwareFileType
    ├── SoftwareUpdateComplete
    ├── SoftwareUpdateData
    ├── SoftwareUpdateMeta
    └── SoftwareVersion
```

#### `UserInterface.Business.ViewModels`
```
UserInterface.Business.ViewModels
├── BatteryNotification
│   └── (Battery notification view model)
│
├── DeviceConnectionSummary
│   └── (Device connection summary view model)
│
├── DeviceStatus
│   └── (Device status view model)
│
├── FirmwareInstallFlow
│   ├── CurrentStep : FirmwareInstallFlowStep
│   ├── IsNewUpdateAvailable : bool
│   ├── PackagedFirmwareName / PackagedFirmwareChangelog : string
│   ├── SelectedFirmwareFileName / SelectedFirmwarePath : string
│   ├── IsSelectedFirmwareValid : bool?
│   ├── IsFlowActive (binding used by views; not declared in the decompiled
│   │   VM, comes from UserInterfaceLib DependentFlowControl)
│   ├── AreDevicesReady : bool
│   ├── BaseRequiresManualRestart / HeadRequiresManualRestart : bool
│   ├── UpdateLog : string
│   ├── CurrentTask / BaseTask / HeadTask : TaskDescription
│   └── CancelCommand / PreviousStepCommand / NextStepCommand / SelectFirmwareCommand
│
├── OptionsFlow
│   └── (Options flow view model)
│
├── PairDevicesFlow
│   └── (Pairing flow view model)
│
└── SupportReportFlow
    └── (Support report flow view model)
```

---

## 6. Namespace Map

```
nofio-utility-cleaned
│
├── global::
│   └── (Assembly attributes, etc.)
│
├── UserInterface
│   ├── App
│   └── Program
│
├── UserInterface.Business
│   ├── Models
│   │   ├── PersistentState
│   │   ├── TaskDescription
│   │   ├── VirtualHereState
│   │   ├── Persistent
│   │   │   ├── Logging
│   │   │   ├── NofioHardware
│   │   │   ├── Settings
│   │   │   └── ThemePreference
│   │   └── Enums
│   │       ├── DeviceCommand
│   │       ├── DriverInstallResult
│   │       ├── FirmwareInstallFlowStep
│   │       ├── FirmwareValidity
│   │       ├── NotificationUrgency
│   │       ├── OverallStatus
│   │       ├── PairDevicesFlowStep
│   │       ├── PairingStatus (+ PairingStatusMethods)
│   │       ├── SupportReportFlowStep
│   │       ├── VideoState
│   │       └── VirtualHereStatus
│   │
│   └── Services
│       ├── NofioApi
│       │   ├── Messages
│       │   │   ├── Ack
│       │   │   ├── Connect
│       │   │   ├── Disconnect
│       │   │   ├── Heartbeat
│       │   │   ├── Nak
│       │   │   ├── Protobuf
│       │   │   ├── RequestStatus
│       │   │   ├── SoftwareFileType
│       │   │   ├── SoftwareUpdateComplete
│       │   │   ├── SoftwareUpdateData
│       │   │   ├── SoftwareUpdateMeta
│       │   │   └── SoftwareVersion
│       │   ├── Replies
│       │   │   ├── ProtobufReply
│       │   │   └── Reply
│       │   ├── Device
│       │   ├── DeviceContext
│       │   ├── DisconnectException
│       │   ├── DisconnectReason
│       │   ├── IReply
│       │   ├── IReplyExtensions
│       │   ├── Message
│       │   ├── MessageErrorCode
│       │   ├── MessageTag
│       │   ├── MessageType
│       │   ├── MessageTypeAttribute
│       │   ├── MinimumProtocolAttribute
│       │   ├── NakException
│       │   ├── Packet
│       │   ├── ProtobufTypeAttribute
│       │   └── UnexpectedReplyException
│       │
│       ├── CommandLineInterface
│       ├── ErrorReporting
│       ├── Firmware
│       ├── ImrDevToolMonitor
│       ├── NofioConnection
│       ├── NofioInterfaces
│       ├── NofioRequests
│       ├── NofioSocket
│       ├── NofioState
│       ├── Pairing
│       ├── Persistence
│       └── VirtualHere
│
├── UserInterface.Business.ViewModels
│   ├── BatteryNotification
│   ├── DeviceConnectionSummary
│   ├── DeviceStatus
│   ├── SettingsNotificationButton
│   ├── FirmwareInstallFlow
│   ├── OptionsFlow
│   ├── PairDevicesFlow
│   └── SupportReportFlow
│
├── UserInterface.Business.Views
│   ├── BatteryNotification
│   ├── DeviceConnectionSummary
│   ├── DeviceStatus
│   └── SettingsNotificationButton
│
├── UserInterface.Business.Views.Flows
│   ├── FirmwareInstallFlowControl
│   ├── FirmwareInstallFlow
│   ├── OptionsFlowControl
│   ├── OptionsFlow
│   ├── PairDevicesFlowControl
│   ├── PairDevicesFlow
│   ├── SupportReportFlowControl
│   └── SupportReportFlow
│
├── UserInterface.Business.Windows
│   ├── BatteryOverlay
│   ├── DashboardOverlay
│   ├── ProductionTestWindow
│   ├── ToolsWindow
│   └── UtilityWindow
│
├── UserInterface.Controls
│   ├── Battery
│   └── TitleBar
│
└── Properties
    └── AssemblyInfo
```

---

## 7. Component Relations

### One-to-Many Relations

```
NofioConnection (1)
├── Manages: NofioSocket (2) - _baseSocket, _headSocket
├── Depends on: NofioInterfaces (1), ImrDevToolMonitor (1)
└── Used by: NofioState (1) for connection state

NofioState (1)
├── Depends on: NofioConnection, Firmware, Pairing, VirtualHere (via ctor)
├── Exposes: connection state delegated from NofioConnection (Base and Head)
├── Manages: WiFi info (channel, country, available channels)
└── Monitors: Connection/Firmware/Pairing/VirtualHere property changes

PersistentState (1)
├── Contains: Settings (1)
├── Contains: NofioHardware (1)
└── Contains: Logging (1)

UtilityWindow (1)
├── Shows: DeviceStatus View (1)
├── Shows: DeviceConnectionSummary View (1)
└── Shows: SettingsNotificationButton View (1)

FirmwareInstallFlow (1)
├── Has: Steps (FirmwareInstallFlowStep: Start, SelectUpdate, DoUpdate, VerifyUpdate, Complete + errors DevicesNotReady/FailedUpdate)
└── Uses: Firmware ([Singleton]) and NofioConnection for sending
```

### Inheritance Relations

```
ObservableObject (CommunityToolkit.Mvvm)
├── PersistentState
├── Settings / Logging / NofioHardware (Models.Persistent)
├── TaskDescription
├── NofioInterfaces
├── NofioState
├── NofioConnection
├── NofioSocket
├── Firmware
├── Pairing
├── VirtualHere
├── ImrDevToolMonitor
├── BatteryNotification (ViewModel)
├── DeviceConnectionSummary (ViewModel)
├── DeviceStatus (ViewModel)
├── SettingsNotificationButton (ViewModel)
├── FirmwareInstallFlow (ViewModel)
├── OptionsFlow (ViewModel)
├── PairDevicesFlow (ViewModel)
└── SupportReportFlow (ViewModel)

Application (System.Windows)
└── App  (NOT ObservableObject; also registers Theme.Apply on Settings change)

IDisposable
├── NofioInterfaces
├── NofioState
├── NofioConnection
├── VirtualHere
├── ImrDevToolMonitor
└── ErrorReporting
    (NofioSocket does NOT implement IDisposable: just ObservableObject)

[Singleton] (InjectX.Shared attribute)
├── NofioInterfaces
├── NofioState
├── NofioConnection
├── PersistentState
├── Firmware
├── Pairing
├── VirtualHere
├── Persistence
├── ImrDevToolMonitor
├── CommandLineInterface
└── ErrorReporting
    (App does NOT use the attribute: registered explicitly
     with services.AddSingleton(typeof(App)) in AddServicesTo)
```

### Dependency Injection Relations

```
Ioc.Default (DI Container)
│
├── Registered as Singleton:
│   ├── App (explicitly with AddSingleton(typeof(App)))
│   ├── PersistentState
│   ├── NofioInterfaces
│   ├── NofioState
│   ├── NofioConnection
│   ├── ErrorReporting
│   ├── Firmware
│   ├── Pairing
│   ├── VirtualHere
│   ├── Persistence
│   ├── ImrDevToolMonitor
│   └── CommandLineInterface
│
├── Registered as Services:
│   └── Models/services from the "Business.Models" and "Business.Services" namespaces
│
├── Registered as Views/ViewModels:
│   ├── BatteryNotification
│   ├── DeviceConnectionSummary
│   ├── DeviceStatus
│   ├── SettingsNotificationButton
│   ├── FirmwareInstallFlow
│   ├── OptionsFlow
│   ├── PairDevicesFlow
│   └── SupportReportFlow
│
└── Registered as Windows:
    ├── BatteryOverlay
    ├── DashboardOverlay
    ├── ProductionTestWindow
    ├── ToolsWindow
    └── UtilityWindow
```

### Event Handling Relations

```
NetworkChange.NetworkAddressChanged
│
└── NofioInterfaces.OnNetworkAddressChanged()
    └── NofioInterfaces.UpdateInterfaceAvailability()
        └── NofioInterfaces.IsBaseAvailable / IsHeadAvailable changed
            └── NofioConnection.OnInterfacesChanged()
                └── NofioConnection.BeginConnectingTo()
                    └── NofioConnection._baseSocket / _headSocket.Open()

NofioConnection._baseSocket / _headSocket Property Changed
│
└── NofioState.OnConnectionPropertyChanged()
    └── NofioState.DetermineStatus()
        └── NofioState.IsBaseConnected / IsHeadConnected updated

ImrDevToolMonitor.IsRunning Changed
│   (detection: process scan + WMI ManagementEventWatcher
│    "__InstanceOperationEvent WITHIN 3 ... TargetInstance ISA 'Win32_Process'
│    ... Name LIKE '%imr_devtool%.exe'" - 3 s poll)
│
└── NofioConnection.OnDevToolStateChanged()
    └── NofioConnection._baseSocket.Close() / _headSocket.Close()
        └── NofioConnection.BeginConnectingTo() (reconnect)

NofioInterfaces.IsBaseAvailable Changed
│
└── VirtualHere.OnNofioInterfacesChanged()
    ├── driver absent → Status = DriverNotInstalled
    │                    → NofioState → OverallStatus.VirtualHereDriverMissing
    └── driver present → launches vhui64.exe → "AUTO USE ALL"
        → Status Starting → Configuring → ConnectedNoDevices/Active
        → ThreadedClock (1500ms) → OnPresencePollTick()
            → "GET CLIENT STATE" → VirtualHereState (XML parse)
            → Status = Active (devices in use) / Ready

App startup (App ctor)
│
└── VR.Install.State == 1?
    ├── YES → VR.Install.AddDriver(Resources\nofio_driver) (VRPathRegistry)
    └── NO  → VRWatcher.Initialize() (waits for SteamVR, then AddDriver)

PersistentState.Settings.PropertyChanged
│
└── App.OnSettingsPropertyChanged()
    └── Theme.Apply() (Changes UI theme)

HostApplicationLifetime.ApplicationStopping
│
└── PersistentState.OnApplicationStopping()
    └── Persistence.Persist() (Saves state to file)
```

---

## Legend

### Symbols Used

```
┌────────┐         Section / Root component
├────────┤         Section separator
│  Text   │         Component / Class
└────────┘         End of section

┌─┐               Connection / Dependency
│ │               Multiple connections
└─┘               End connection

▶                 Flow direction
─┬─               Branch
 │                Vertical connection
 ├──              Tree branch
 └──              Tree end

(*)               Interface / Abstract
[Enum]           Enum type
{Property}       Property / Field
→                 Inheritance
≡                 Implementation
```

### Colors (in the conceptual diagrams)
- **🟦 Blue**: Main components / Entry points
- **🟩 Green**: Services and business logic
- **🟨 Yellow**: Models and data
- **🟥 Red**: Communication and network
- **🟪 Purple**: User interface
- **⚪ Gray**: System / external components

---

## Summary

This conceptual map illustrates:

1. The **complete hierarchy** of the project with all components
2. **Relations** between classes, services and UI components
3. Main **data flows** (connection, firmware update)
4. **Dependencies**, internal and external
5. The complete **namespace structure**
6. **Architectural patterns** (MVVM, DI, Singleton)
7. **Communication mechanisms** between components

The application is well structured, with a clear separation of concerns and
consistent use of modern patterns such as Dependency Injection and MVVM.
