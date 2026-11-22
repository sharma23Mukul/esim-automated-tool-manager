# eSim Tool Manager (`esim-tm`)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![CI Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-88%25-success.svg)]()

Automated tool manager for [eSim](https://esim.fossee.in/) (IIT Bombay FOSSEE). Manages the discovery, installation, configuration, dependency resolution, and updates of external EDA tools and compilers used in circuit simulation and PCB design.

---

## Features

- **Multi-Backend Package Management**: Supports APT (Ubuntu/Debian), Homebrew (macOS), Chocolatey (Windows), and pip for Python-based simulation tools.
- **Declarative Tool Manifest (`tools.yaml`)**: Tool definitions, version detection regex, package mappings, and configuration hints are defined in YAML. New tools can be added without modifying source code.
- **Dependency & Compatibility Checker**: Verifies installed tools against minimum and pinned version constraints, resolves dependency trees, and detects cyclic dependencies.
- **Configuration & Shell Integration**: Manages environment variables (`SPICE_LIB_DIR`, `LLVM_DIR`) and system `PATH`. Generates export scripts for Bash, Zsh, Fish, PowerShell, and Cmd. Automatically backs up existing configs with timestamps (`.bak`).
- **Dry-Run Safety**: Every mutating command (`install`, `update`, `configure`) supports `--dry-run` to inspect commands before execution.
- **Diagnostic Health Check (`doctor`)**: Inspects system environment, package managers, and toolchain status, generating clean Markdown or JSON reports for troubleshooting and bug reporting.
- **Scriptable CLI**: Provides human-readable table outputs by default, with `--json` support across commands for automated pipelines.

---

## Architecture Overview

```
FOSSEE/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI (Ubuntu & Windows matrix)
├── esim_toolmanager/
│   ├── __init__.py              # Package entry & exit code constants
│   ├── __main__.py              # python -m esim_toolmanager execution
│   ├── cli.py                   # argparse CLI entry point
│   ├── data/
│   │   └── tools.yaml           # Declarative toolchain manifest
│   ├── utils/
│   │   ├── version.py           # Semantic version parser and comparator
│   │   ├── process.py           # Subprocess wrapper with dry-run support
│   │   └── log.py               # Rotating file and console logger
│   ├── platform/
│   │   └── detect.py            # OS, architecture, and package manager detection
│   ├── backends/
│   │   ├── base.py              # Abstract PackageBackend interface
│   │   ├── apt.py               # Debian/Ubuntu APT backend
│   │   ├── brew.py              # macOS Homebrew backend
│   │   ├── choco.py             # Windows Chocolatey backend
│   │   └── pip_backend.py       # Python pip backend
│   └── core/
│       ├── registry.py          # Tool manifest parser and query engine
│       ├── installer.py         # Tool installer & version pinning logic
│       ├── updater.py           # Outdated tool checker & updater
│       ├── config.py            # Environment variable & path manager
│       ├── dependency.py        # Dependency resolution & cycle detection
│       └── doctor.py            # System health diagnostics generator
├── tests/
│   ├── conftest.py              # Pytest fixtures and mock platform configs
│   ├── fixtures/
│   │   └── test_tools.yaml      # Isolated manifest for testing
│   ├── test_version.py          # Version parsing & constraint evaluation tests
│   ├── test_platform.py         # Platform detection tests
│   ├── test_registry.py         # Manifest parsing & tool query tests
│   ├── test_backends.py         # Package backend unit tests
│   ├── test_installer.py        # Installer execution & dry-run tests
│   ├── test_updater.py          # Update checker & updater unit tests
│   ├── test_config.py           # Config backup & shell export tests
│   ├── test_dependency.py       # Dependency tree & cycle detection tests
│   ├── test_doctor.py           # Health report output tests
│   └── test_cli.py              # End-to-end CLI command tests
├── demo/
│   └── demo_script.md           # 5-minute video demonstration script
├── DESIGN.md                    # Technical design document
├── SUBMISSION_CHECKLIST.md      # Project submission notes
├── pyproject.toml               # PEP 517/621 packaging metadata
├── requirements.txt             # Dependencies (PyYAML)
└── README.md
```

---

## Installation

### Requirements
- Python 3.8 or higher
- Git

### Setup
```bash
git clone https://github.com/sharma23Mukul/esim-automated-tool-manager.git
cd esim-automated-tool-manager

# Create and activate a virtual environment (optional)
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

Verify installation:
```bash
esim-tm --version
```

---

## Quick Start

### 1. Check Toolchain Status
```bash
esim-tm list
```
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

### 2. Run Dependency and Compatibility Checks
```bash
esim-tm check
```
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

### 3. Dry-Run Installation
```bash
esim-tm --dry-run install ngspice
```
```text
  ✅ Would install Ngspice via apt.
```

### 4. Run Diagnostic Health Check
```bash
esim-tm doctor
```

### 5. Generate Shell Environment Script
```bash
esim-tm configure --export --shell bash
```
```bash
# Generated by esim-tm configure
export SPICE_LIB_DIR="/usr/share/ngspice"
export LLVM_DIR="/usr/lib/llvm-14"
export PATH="/usr/share/ngspice/bin:$PATH"
```

---

## Command Reference

| Command | Arguments / Flags | Description | Example |
|---|---|---|---|
| `list` | `--category`, `--required` | Display all configured tools, versions, and statuses | `esim-tm list --required` |
| `check` | | Check tool dependencies and compatibility with fix suggestions | `esim-tm check` |
| `install` | `<tool>`, `--all`, `--version` | Install a specific tool or all required tools | `esim-tm install ngspice --version 42` |
| `update` | `<tool>`, `--all` | Upgrade installed tools | `esim-tm update --all` |
| `outdated` | | List installed tools that are below minimum version requirements | `esim-tm outdated` |
| `configure` | `[tool]`, `--export`, `--shell` | Apply or export environment variables and path settings | `esim-tm configure --export --shell bash` |
| `doctor` | `--format <markdown\|json>` | Run full system and tool diagnostic report | `esim-tm doctor --format json` |
| `logs` | `-n`, `--lines` | View recent entries from the rotating log file | `esim-tm logs -n 50` |

### Global Flags

- `--dry-run`: Preview actions without making changes to the filesystem or system packages.
- `-v`, `--verbose`: Enable debug logging to standard error.
- `--json`: Output machine-readable JSON format for scripts.
- `--config <path>`: Use a custom config file path (default: `~/.esim-toolmanager/config.yaml`).
- `--manifest <path>`: Use a custom manifest file path (default: built-in `tools.yaml`).

---

## Configuration & Environment

User settings are saved to `~/.esim-toolmanager/config.yaml`. Before making changes, `esim-tm` saves a timestamped backup copy (`config.<timestamp>.bak`).

To apply managed environment variables in your current shell:

```bash
# Bash / Zsh
eval "$(esim-tm configure --export --shell bash)"

# Fish
eval (esim-tm configure --export --shell fish)
```

In PowerShell:
```powershell
Invoke-Expression (esim-tm configure --export --shell powershell)
```

---

## Adding a New Tool

To add a new tool, define it in `esim_toolmanager/data/tools.yaml` or provide a standalone manifest with `--manifest`:

```yaml
tools:
  yosys:
    name: "Yosys Open SYnthesis Suite"
    description: "Verilog synthesis framework"
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

`esim-tm` immediately recognizes and manages the tool without code modifications.

---

## Testing

The project includes an extensive test suite covering version comparison, platform detection, package backends, installation orchestration, configuration handling, cycle detection, and CLI entry points.

```bash
# Run unit and integration tests
python -m pytest tests/ -v --tb=short

# Run tests with coverage report
python -m pytest tests/ --cov=esim_toolmanager --cov-report=term-missing
```

All tests use mocks for subprocess and file modifications to guarantee they run safely without touching system packages.

---

## Exit Codes

| Code | Constant | Meaning |
|---|---|---|
| `0` | `EXIT_OK` | Successful execution |
| `1` | `EXIT_ERROR` | General error |
| `2` | `EXIT_DEPENDENCY_MISSING` | Required tool or dependency is not installed |
| `3` | `EXIT_VERSION_MISMATCH` | Tool version is below required constraint |
| `4` | `EXIT_TOOL_NOT_FOUND` | Specified tool identifier was not found in manifest |
| `5` | `EXIT_INSTALL_FAILED` | Package manager installation failed |
| `6` | `EXIT_CONFIG_ERROR` | Configuration error or invalid format |

---

## License & Credits

- **License**: GNU General Public License v3 or later ([GPL-3.0-or-later](LICENSE)).
- **Project**: Developed for the eSim ecosystem under FOSSEE, IIT Bombay.
