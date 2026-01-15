# DGXTOP Architecture Diagram

This document describes the architectural relationships between all Python modules in the DGXTOP project.

## Module Relationship Diagram

```mermaid
graph TB
    %% Entry Point
    Main[main.py<br/>DGXTop Application<br/>Entry Point]
    
    %% Core Configuration
    Config[config.py<br/>AppConfig<br/>ColorTheme<br/>COLOR_THEMES]
    
    %% Monitoring Modules
    SystemMon[system_monitor.py<br/>SystemMonitor<br/>CPU, Memory, Network Stats]
    GPUMon[gpu_monitor.py<br/>GPUMonitor<br/>GPU Statistics via nvidia-smi]
    DiskMon[disk_monitor.py<br/>DiskMonitor<br/>Disk I/O Statistics]
    NetworkMon[network_monitor.py<br/>NetworkMonitor<br/>Network Interface Stats]
    
    %% UI Layer
    RichUI[rich_ui.py<br/>RichUI<br/>Terminal UI Rendering]
    
    %% Utility Modules
    Logger[logger.py<br/>DGXTopLogger<br/>Logging System]
    
    %% External Dependencies (mentioned but may not exist)
    RoCEStats[roce_stats<br/>get_roce_counters<br/>EXTERNAL/MISSING]
    
    %% Package Init
    Init[__init__.py<br/>Package Metadata<br/>Version Info]
    
    %% Main Dependencies
    Main --> Config
    Main --> SystemMon
    Main --> GPUMon
    Main --> DiskMon
    Main --> NetworkMon
    Main --> RichUI
    Main --> Logger
    Main --> Init
    
    %% UI Dependencies
    RichUI --> Config
    
    %% Network Monitor Dependencies
    NetworkMon -.->|imports| RoCEStats
    
    %% Styling
    classDef entryPoint fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    classDef config fill:#fff3e0,stroke:#e65100
    classDef monitor fill:#e8f5e9,stroke:#2e7d32
    classDef ui fill:#f3e5f5,stroke:#6a1b9a
    classDef utility fill:#fce4ec,stroke:#c2185b
    classDef external fill:#ffebee,stroke:#c62828,stroke-dasharray: 5 5
    classDef metadata fill:#f5f5f5,stroke:#616161
    
    class Main entryPoint
    class Config config
    class SystemMon,GPUMon,DiskMon,NetworkMon monitor
    class RichUI ui
    class Logger utility
    class RoCEStats external
    class Init metadata
```

## Detailed Module Descriptions

### Entry Point Layer

#### `main.py` (DGXTop)
- **Purpose**: Main application entry point and orchestration
- **Key Class**: `DGXTop`
- **Responsibilities**:
  - Initializes all monitoring modules
  - Manages the main event loop
  - Handles keyboard input and signals
  - Coordinates data collection from all monitors
  - Updates UI with collected statistics
- **Dependencies**: 
  - All monitoring modules (SystemMonitor, GPUMonitor, DiskMonitor, NetworkMonitor)
  - UI module (RichUI)
  - Configuration (AppConfig)
  - Logging (get_logger)

### Configuration Layer

#### `config.py`
- **Purpose**: Application configuration and themes
- **Key Components**:
  - `AppConfig`: Main configuration dataclass
  - `ColorTheme`: Theme configuration
  - `COLOR_THEMES`: Predefined color themes (green, amber, blue)
- **Dependencies**: None (standalone)
- **Used By**: main.py, rich_ui.py

### Monitoring Layer

All monitoring modules follow a similar pattern: they read from system files/proc/sys and calculate rate-based statistics.

#### `system_monitor.py` (SystemMonitor)
- **Purpose**: Monitor CPU and Memory statistics
- **Data Sources**: 
  - `/proc/stat` (CPU)
  - `/proc/meminfo` (Memory)
  - `/sys/class/thermal/*` (Temperature)
  - `/sys/devices/system/cpu/*/cpufreq/*` (CPU Frequency)
- **Key Classes**: `CPUStats`, `MemoryStats`, `NetworkStats`, `SystemMonitor`
- **Dependencies**: None (standalone)

#### `gpu_monitor.py` (GPUMonitor)
- **Purpose**: Monitor NVIDIA GPU statistics
- **Data Source**: `nvidia-smi` command (subprocess)
- **Key Classes**: `GPUStats`, `GPUMonitor`
- **Dependencies**: None (standalone, requires nvidia-smi)

#### `disk_monitor.py` (DiskMonitor)
- **Purpose**: Monitor disk I/O statistics
- **Data Sources**: 
  - `/proc/diskstats` (I/O statistics)
  - `/proc/mounts` (Mounted devices)
- **Key Classes**: `DiskStats`, `DiskMonitor`
- **Dependencies**: None (standalone)

#### `network_monitor.py` (NetworkMonitor)
- **Purpose**: Monitor network interface statistics
- **Data Sources**: 
  - `/proc/net/dev` (Network statistics)
  - `/sys/class/net/*/statistics/` (Interface stats)
  - `nmcli device status` (Connected interfaces via subprocess)
- **Key Classes**: `NetworkStats`, `NetworkMonitor`
- **Dependencies**: 
  - `ibifc.py` (InfiniBand device mapping)
  - RoCE counter functionality integrated directly

### UI Layer

#### `rich_ui.py` (RichUI)
- **Purpose**: Terminal UI rendering using Rich library
- **Key Features**:
  - Layout management
  - Panel rendering (CPU, GPU, Memory, Disk, Network)
  - Sparkline generation
  - Progress bars
  - Color themes
- **Dependencies**: 
  - `config.py` (AppConfig)
  - Rich library (external)

### Utility Layer

#### `logger.py` (DGXTopLogger)
- **Purpose**: Comprehensive logging system
- **Key Features**:
  - File logging (detailed logs)
  - Console logging
  - Error logging (separate file)
  - Thread-safe singleton pattern
- **Key Functions**: `get_logger()`, `log_system_info()`, etc.
- **Dependencies**: None (standalone)

#### `__init__.py`
- **Purpose**: Package initialization and metadata
- **Exports**: Version, author, description
- **Dependencies**: None

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (DGXTop)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Event Loop:                                          │   │
│  │  1. Collect stats from all monitors                  │   │
│  │  2. Aggregate data                                    │   │
│  │  3. Pass to RichUI.get_renderable()                  │   │
│  │  4. Update Live display                               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Monitors    │    │   Config     │    │    UI        │
│              │    │              │    │              │
│ SystemMonitor│    │  AppConfig   │    │   RichUI     │
│ GPUMonitor   │    │  ColorTheme  │    │              │
│ DiskMonitor  │    │              │    │  - Panels    │
│ NetworkMonitor│   │              │    │  - Tables    │
└──────────────┘    └──────────────┘    │  - Sparklines│
        │                                │              │
        │                                └──────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│      System Data Sources                │
│  /proc/stat, /proc/meminfo              │
│  /proc/diskstats, /proc/net/dev         │
│  /sys/class/net/*/statistics/           │
│  nvidia-smi (subprocess)                │
│  nmcli (subprocess)                     │
└─────────────────────────────────────────┘
```

## Key Design Patterns

1. **Monitor Pattern**: All monitoring modules follow a similar structure:
   - Read raw data from system files
   - Calculate deltas/rates from previous measurements
   - Return structured dataclass objects

2. **Singleton Pattern**: Logger uses a thread-safe singleton pattern via `get_logger()`

3. **Observer Pattern**: Main loop observes all monitors and updates UI

4. **Separation of Concerns**: 
   - Monitoring logic separated from UI logic
   - Configuration separated from implementation
   - Each monitor is independent

## Module Independence

- **Fully Independent**: `config.py`, `logger.py`, `__init__.py`
- **Independent Monitors**: `system_monitor.py`, `gpu_monitor.py`, `disk_monitor.py`
- **UI Dependent on Config**: `rich_ui.py` → `config.py`
- **Main Orchestrator**: `main.py` depends on all modules

## Potential Issues

1. **Missing Dependency**: `network_monitor.py` uses `ibifc.py` for InfiniBand device mapping (may fail gracefully if not available)
2. **Circular Dependencies**: None detected (clean architecture)
