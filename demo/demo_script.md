# eSim Automated Tool Manager — Video Demonstration Script

**Author:** Mukul Sharma (`sharma23Mukul`)  
**Project:** eSim Automated Tool Manager (`esim-tm`)  
**Duration:** ~5 Minutes  

---

## Timeline & Structure

| Time | Section | Action / Command | Key Points Covered |
|---|---|---|---|
| **0:00 - 0:40** | **Introduction** | Terminal / README | Project scope: managing external tools (Ngspice, KiCad, GHDL, Verilator, LLVM) in eSim. |
| **0:40 - 1:20** | **Tool Status (`list`)** | `python -m esim_toolmanager list` | Tool table, version detection, status flags, and `--json` format. |
| **1:20 - 2:00** | **Dependency Checking (`check`)** | `python -m esim_toolmanager check` | Compatibility validation against minimum constraints and fix suggestions. |
| **2:00 - 2:45** | **Installation & Dry-Run Mode** | `python -m esim_toolmanager --dry-run install ngspice` | Safe simulation across APT, Homebrew, and Chocolatey. |
| **2:45 - 3:30** | **System Diagnostics (`doctor`)** | `python -m esim_toolmanager doctor` | Diagnostic health report in Markdown/JSON for troubleshooting. |
| **3:30 - 4:00** | **Environment Configuration** | `python -m esim_toolmanager configure --export --shell bash` | Exporting environment variables (`SPICE_LIB_DIR`), `PATH`, and `.bak` backups. |
| **4:00 - 4:30** | **Manifest Extensibility** | View `data/tools.yaml` | Adding new tools declaratively via YAML without modifying source code. |
| **4:30 - 5:00** | **Automated Tests & Summary** | `python -m pytest tests/` | 169 unit tests passing with 88% coverage. |

---

## Spoken Narration & Terminal Commands

### 1. Introduction (0:00 - 0:40)
**Spoken:**
> "Hello! My name is Mukul Sharma, and this is a demonstration of the Automated Tool Manager for eSim, or `esim-tm`.
> 
> eSim depends on external EDA tools and compilers such as Ngspice, KiCad, GHDL, Verilator, and LLVM. Managing these manually across different platforms can lead to version mismatches and broken paths.
> 
> `esim-tm` is a Python tool that manages the entire lifecycle of these dependencies—including discovery, installation, configuration, and version checks—across Linux, macOS, and Windows."

---

### 2. Checking Tool Status: `list` (0:40 - 1:20)
**Command:**
```bash
python -m esim_toolmanager list
```

**Expected Output:**
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

**Spoken:**
> "Running `esim-tm list` shows a clean table of all tools configured in our manifest. It displays the detected runtime version, whether the tool is required by eSim, the minimum version constraint, and the current installation status.
> 
> We can filter this list by category or requirement, or pass `--json` when integrating into automated setup scripts."

---

### 3. Dependency & Compatibility Checking: `check` (1:20 - 2:00)
**Command:**
```bash
python -m esim_toolmanager check
```

**Expected Output:**
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

**Spoken:**
> "Next, `esim-tm check` validates whether all dependencies meet compatibility constraints. It checks installed versions against minimum requirements, inspects recursive dependencies with cycle detection, and provides concrete fix suggestions whenever a required component is missing."

---

### 4. Installation with Dry-Run Mode: `install` (2:00 - 2:45)
**Command:**
```bash
python -m esim_toolmanager --dry-run install ngspice
```

**Expected Output:**
```text
  ✅ Would install Ngspice via apt.
```

**Spoken:**
> "When installing tools, it is useful to preview actions before running them. All mutating commands in `esim-tm` support the `--dry-run` flag.
> 
> Here, `esim-tm` detects the host OS, maps Ngspice to the APT package manager backend, and verifies the command without touching system files. The same command maps to Homebrew on macOS or Chocolatey on Windows."

---

### 5. System Health Diagnostics: `doctor` (2:45 - 3:30)
**Command:**
```bash
python -m esim_toolmanager doctor
```

**Expected Output:**
```markdown
# eSim Tool Manager – Health Report

**Generated:** 2026-11-22T02:00:00
**Platform:** linux x86_64 (ubuntu 22.04)
**Python:** 3.11.2
**Package Manager:** apt

## Checks

| Status | Check | Message |
|--------|-------|---------|
| ✅ | Package Manager | Detected: apt |
| ✅ | Ngspice | Installed (42) |
| ✅ | KiCad | Installed (7.0.2) |
| ⚠️ | GHDL | Not installed (optional) |
| ⚠️ | Verilator | Not installed (optional) |
| ✅ | LLVM | Installed (14.0.0) |
| ✅ | Python 3 | Installed (3.11.2) |
| ⚠️ | Makerchip | Not installed (optional) |
| ✅ | Configuration | Loaded from ~/.esim-toolmanager/config.yaml |

## Dependency Summary

4/7 tools OK, 0 missing, 0 outdated.
```

**Spoken:**
> "For troubleshooting, the `doctor` command runs an end-to-end diagnostic check on the system environment, active package managers, and toolchain versions.
> 
> The output renders as Markdown or JSON, which makes it easy for users to paste into bug reports or discussion forums."

---

### 6. Environment & Configuration: `configure` (3:30 - 4:00)
**Command:**
```bash
python -m esim_toolmanager configure --export --shell bash
```

**Expected Output:**
```bash
# Generated by esim-tm configure
export SPICE_LIB_DIR="/usr/share/ngspice"
export LLVM_DIR="/usr/lib/llvm-14"
export PATH="/usr/share/ngspice/bin:$PATH"
```

**Spoken:**
> "To ensure tools integrate properly with eSim, `configure` manages environment variables like `SPICE_LIB_DIR` and `PATH`.
> 
> It can output export scripts for Bash, Zsh, Fish, or PowerShell. Any updates automatically create timestamped `.bak` files to prevent configuration loss."

---

### 7. Adding New Tools via Manifest (4:00 - 4:30)
**Spoken:**
> "Adding new tools requires zero code changes. In `esim_toolmanager/data/tools.yaml`, each tool is defined with its name, version detection command, regex pattern, and package mappings for `apt`, `brew`, and `choco`.
> 
> Maintainers can add or modify tool definitions directly in YAML, and `esim-tm` immediately picks them up."

---

### 8. Testing & Summary (4:30 - 5:00)
**Command:**
```bash
python -m pytest tests/ -v --tb=short
```

**Expected Output:**
```text
============================= 169 passed in 3.19s =============================
```

**Spoken:**
> "Finally, let's run the test suite. We have 169 unit and integration tests passing with 88% code coverage, with automated CI running on Ubuntu and Windows.
> 
> In summary, `esim-tm` provides a practical, safe, and extensible tool manager for the eSim toolchain. Thank you!"
