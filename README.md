# eSim Tool Manager (`esim-tm`)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![CI Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-86%25-success.svg)]()

> Automated Tool Manager for [eSim](https://esim.fossee.in/) (IIT Bombay FOSSEE).  
> Simplifies discovery, installation, compatibility checking, configuration, and upgrades for eSim's external EDA toolchain.

---

## Table of Contents

- [Overview](#overview)
- [Official Requirements Met](#official-requirements-met)
- [Key Features](#key-features)
- [Project Architecture](#project-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Configuration Management](#configuration-management)
- [Adding a New Tool (Extensibility)](#adding-a-new-tool-extensibility)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Exit Codes](#exit-codes)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [License & Acknowledgments](#license--acknowledgments)

---

## Overview

**eSim** is an open-source EDA tool for circuit design, simulation, analysis, and PCB design developed by the FOSSEE team at IIT Bombay. It integrates various external tools and compilers, including:
- **Ngspice**: Mixed-level / mixed-signal circuit simulator
- **KiCad**: Schematic capture and PCB layout suite
- **GHDL**: Open-source VHDL simulator
- **Verilator**: Fast Verilog/SystemVerilog simulator and lint tool
- **LLVM**: Compiler infrastructure for high-performance tool compilation
- **Python 3 & Makerchip**: Python runtime dependencies and cloud simulation integration

Managing these tools manually is error-prone, version-sensitive, and OS-dependent. **`esim-tm`** provides a unified CLI and automation engine that handles the entire lifecycle across Linux, macOS, and Windows.

---

## Official Requirements Met

`esim-tm` meets **all 5 official requirements** plus the optional cross-platform and package manager integrations:

| Requirement | Implementation in `esim-tm` |
|---|---|
| **1. Tool Installation Management** | Automated download and installation across Linux (APT), macOS (Homebrew), and Windows (Chocolatey/winget) with explicit version pinning and dry-run safety. |
| **2. Update and Upgrade System** | Detection of outdated tools against eSim compatibility constraints and one-click upgrades (`update`, `outdated`). |
| **3. Configuration Handling** | Automated path and environment variable management (`SPICE_LIB_DIR`, `LLVM_DIR`, `PATH`), backup before mutations, and shell export generator (`bash`, `zsh`, `fish`, `powershell`, `cmd`). |
| **4. Dependency Checker** | Recursive dependency resolution, topological ordering, compatibility verification, and clear, actionable fix suggestions. |
| **5. User Interface & Logs** | Full-featured CLI (`esim-tm`), colorized console output, machine-readable JSON output (`--json`), and rotating diagnostic logs. |
| **Optional: Cross-Platform & Backends** | Native support for Debian/Ubuntu (APT), macOS (Brew), Windows (Choco), and Python packages (pip). |
| **Creativity: Doctor Health Check** | Comprehensive `doctor` command producing Markdown reports for bug reports or automated diagnostics. |
| **Creativity: Safe Dry-Run & Backups** | Universal `--dry-run` flag guaranteeing non-destructive runs, with automatic config backups (`.bak`). |

---

## Key Features

- 🛡️ **Safe by Default**: Every mutating operation supports `--dry-run`. Subprocess executions are isolated and tested without touching the host system.
- 📋 **Manifest-Driven**: Tools, commands, version patterns, packages, and paths are defined declaratively in `tools.yaml`. Adding new tools requires zero Python code changes.
- 🩺 **Built-in Doctor**: The `doctor` command inspects package managers, binary paths, runtime versions, and system permissions, generating Markdown or JSON reports.
- 🔄 **Safe Configuration Backups**: Existing configurations are backed up with timestamps (`.YYYYMMDD_HHMMSS.bak`) before any modification.
- ⚙️ **Automated Shell Integration**: Generates POSIX `export` statements or PowerShell `$env:` statements on the fly.
- 🧮 **PEP-440 Version Engine**: Custom semantic version parser supporting `>=`, `<=`, `==`, `!=`, `<`, `>`, and `~=` (compatible release).

---

## Project Architecture

```
FOSSEE/
├── .github/
│   └── workflows/
│       └── ci.yml               # Multi-platform CI (Linux & Windows)
├── esim_toolmanager/
│   ├── __init__.py              # Version & exit codes
│   ├── __main__.py              # python -m esim_toolmanager entry
│   ├── cli.py                   # Command-line interface & argument parser
│   ├── data/
│   │   └── tools.yaml           # Default toolchain manifest (declarative)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── version.py           # Semantic version parsing & constraint evaluation
│   │   ├── process.py           # Safe subprocess execution & dry-run runner
│   │   └── log.py               # Rotating file & colorized console logging
│   ├── platform/
│   │   ├── __init__.py
│   │   └── detect.py            # OS, architecture, distro & package manager detection
│   ├── backends/
│   │   ├── __init__.py          # Backend selector
│   │   ├── base.py              # Abstract PackageBackend interface
│   │   ├── apt.py               # APT backend (Debian/Ubuntu)
│   │   ├── brew.py              # Homebrew backend (macOS)
│   │   ├── choco.py             # Chocolatey backend (Windows)
│   │   └── pip_backend.py       # Pip backend (cross-platform)
│   └── core/
│       ├── __init__.py
│       ├── registry.py          # Manifest parser & tool registry
│       ├── installer.py         # Installation orchestration & version pinning
│       ├── updater.py           # Update checker & upgrader
│       ├── config.py            # Env vars, PATH, shell exporter & backups
│       ├── dependency.py        # Dependency graph resolution & cycle detection
│       └── doctor.py            # Diagnostic health reporting engine
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures & mock platforms
│   ├── fixtures/
│   │   └── test_tools.yaml      # Isolated manifest for unit tests
│   ├── test_version.py          # Version parsing & comparisons
│   ├── test_platform.py         # Platform detection tests
│   ├── test_registry.py         # Registry loading & querying tests
│   ├── test_backends.py         # Package backend unit tests
│   ├── test_installer.py        # Installer logic tests
│   ├── test_config.py           # Config & shell export tests
│   ├── test_dependency.py       # Dependency & cycle detection tests
│   ├── test_doctor.py           # Doctor health report tests
│   └── test_cli.py              # CLI commands end-to-end tests
├── demo/
│   └── demo_script.md           # 5-minute demo video script & speaking points
├── DESIGN.md                    # Comprehensive technical design document
├── SUBMISSION_CHECKLIST.md      # IIT Bombay task submission checklist
├── pyproject.toml               # PEP 517/621 packaging metadata
├── requirements.txt             # Runtime dependencies (pyyaml)
└── README.md                    # User manual & documentation
```

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/sharma23Mukul/esim-automated-tool-manager.git
cd esim-toolmanager

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install in editable mode with development dependencies
pip install -e ".[dev]"
```

Verify the installation:
```bash
esim-tm --version
```

---

## Quick Start

### 1. View Installed Tools and Status
```bash
esim-tm list
```
*Output:*
```text
Tool             Version      Required   Min        Status    
──────────────────────────────────────────────────────────────
Ngspice          42           yes        42         ✅ installed
KiCad            7.0.2        yes        7.0        ✅ installed
GHDL             —            no         3.0        ❌ missing
Verilator        —            no         5.0        ❌ missing
LLVM             14.0.0       no         14.0       ✅ installed
Python 3         3.11.2       yes        3.8        ✅ installed
Makerchip        —            no         1.0        ❌ missing

7 tools shown.
```

### 2. Run a Dependency Check
```bash
esim-tm check
```
*Output:*
```text
Dependency Check Report
════════════════════════════════════════
  ✅ Ngspice: 42
  ✅ KiCad: 7.0.2
  ⚠️ GHDL: not installed
  ⚠️ Verilator: not installed
  ✅ LLVM: 14.0.0
  ✅ Python 3: 3.11.2
  ⚠️ Makerchip: not installed

4/7 tools OK, 0 missing, 0 outdated.
```

### 3. Simulate Installation Safely (`--dry-run`)
```bash
esim-tm --dry-run install ngspice
```
*Output:*
```text
  ✅ Would install Ngspice via apt.
```

### 4. Run System Diagnostics
```bash
esim-tm doctor
```

### 5. Generate Shell Environment Script
```bash
esim-tm configure --export --shell bash
```
*Output:*
```bash
# Generated by esim-tm configure
export SPICE_LIB_DIR="/usr/share/ngspice"
export LLVM_DIR="/usr/lib/llvm-14"
export PATH="/usr/share/ngspice/bin:$PATH"
```

---

## Command Reference

| Command | Description | Example |
|---|---|---|
| `list` | Show all tools, required versions, and current status | `esim-tm list --required` |
| `check` | Check dependencies and compatibility with actionable fixes | `esim-tm check` |
| `install <tool>` | Install specified tool (or all required tools with `--all`) | `esim-tm install ngspice --version 42` |
| `update [tool]` | Update specified tool (or all outdated tools with `--all`) | `esim-tm update --all` |
| `outdated` | Check for tools installed below the required minimum version | `esim-tm outdated` |
| `configure [tool]` | Apply environment variables and paths | `esim-tm configure --export --shell bash` |
| `doctor` | Run comprehensive health check and output Markdown or JSON | `esim-tm doctor --format json` |
| `logs` | View recent entries from the rotating log file | `esim-tm logs -n 50` |

### Global Flags

- `--dry-run`: Simulate operations without modifying the file system or invoking installers.
- `-v`, `--verbose`: Enable verbose debug logging in terminal.
- `--json`: Output results in structured JSON format (ideal for scripting and CI).
- `--config <path>`: Path to a custom `config.yaml` file.
- `--manifest <path>`: Path to a custom tool manifest YAML.

---

## Configuration Management

Configuration settings are stored in `~/.esim-toolmanager/config.yaml`:

```yaml
esim_version: "2.5"
tools:
  ngspice:
    configured: true
    configured_at: "2026-11-22T01:45:00"
env_vars:
  SPICE_LIB_DIR: "/usr/share/ngspice"
  LLVM_DIR: "/usr/lib/llvm-14"
paths:
  - "/usr/share/ngspice/bin"
```

To load these variables into your current shell session:
```bash
eval "$(esim-tm configure --export --shell bash)"
```

Or in PowerShell:
```powershell
Invoke-Expression (esim-tm configure --export --shell powershell)
```

---

## Adding a New Tool (Extensibility)

To add a new EDA tool (e.g., `yosys`), simply edit `esim_toolmanager/data/tools.yaml` or provide a custom manifest via `--manifest`:

```yaml
tools:
  yosys:
    name: "Yosys Open SYnthesis Suite"
    description: "Framework for Verilog RTL synthesis"
    homepage: "https://yosyshq.net/yosys/"
    category: synthesis
    required: false
    version_command: ["yosys", "-V"]
    version_pattern: "Yosys\\s+(\\d+\\.\\d+\\.?\\d*)"
    min_version: "0.30"
    max_version: null
    pinned_version: null
    packages:
      apt: yosys
      brew: yosys
      choco: null
      pip: null
    dependencies: []
    config_hints:
      env_vars: {}
      paths: []
    platforms:
      - linux
      - darwin
```

No Python code needs to be modified.

---

## Testing & Quality Assurance

`esim-tm` features a comprehensive test suite (159 unit & integration tests) achieving **86% test coverage**:

```bash
# Run test suite
python -m pytest tests/ -v --tb=short

# Run test suite with coverage report
python -m pytest tests/ --cov=esim_toolmanager --cov-report=term-missing
```

### Safety Guarantee
All tests mock external process executions (`subprocess.run`), file changes, and network activity. Tests will never attempt to install packages on your machine.

---

## Exit Codes

| Code | Constant | Meaning |
|---|---|---|
| `0` | `EXIT_OK` | Command completed successfully |
| `1` | `EXIT_ERROR` | General or unexpected runtime error |
| `2` | `EXIT_DEPENDENCY_MISSING` | One or more required dependencies are missing |
| `3` | `EXIT_VERSION_MISMATCH` | A tool is installed but does not satisfy version constraints |
| `4` | `EXIT_TOOL_NOT_FOUND` | Specified tool ID does not exist in the manifest |
| `5` | `EXIT_INSTALL_FAILED` | Installation backend failed |
| `6` | `EXIT_CONFIG_ERROR` | Configuration validation or file access error |

---

## Known Limitations

1. **Package Availability**: System package manager versions depend on OS repository releases (e.g., Ubuntu LTS vs. Arch).
2. **Offline Package Cache**: Requires an internet connection unless packages are pre-cached locally.
3. **GUI Interface**: Currently provided as a CLI; GUI wrapper is designed for future extension.

---

## Roadmap

- [ ] Interactive GUI mode using Tkinter wrapping the core API.
- [ ] Local mirror and offline cache directory for air-gapped lab installations.
- [ ] Cryptographic checksum verification (SHA-256) for direct binary archives.
- [ ] Support for Arch Linux (`pacman`) and Fedora/RHEL (`dnf`).
- [ ] Integration with eSim workspace settings dialog.

---

## License & Acknowledgments

- **License**: GNU General Public License v3 or later ([GPL-3.0-or-later](LICENSE)).
- **Project**: Developed for the **FOSSEE eSim Winter Internship 2026**, IIT Bombay.
- **Credits**: eSim Team, FOSSEE, Spoken Tutorial Project, and IIT Bombay.
