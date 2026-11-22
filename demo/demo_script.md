# eSim Automated Tool Manager — 5-Minute Demo Video Script

**Candidate:** Mukul Sharma (`sharma23Mukul`)  
**Application:** FOSSEE eSim Winter Internship 2026 (IIT Bombay), Task 5  
**Topic:** Automated Tool Manager for eSim (`esim-tm`)  
**Duration:** ~5 Minutes  

---

## Video Outline & Timeline

| Time | Section | Key Demonstration / Action |
|---|---|---|
| **0:00 - 0:45** | **Introduction & Problem Statement** | Overview of eSim toolchain complexity; introducing `esim-tm`. |
| **0:45 - 1:30** | **Discovery & Status (`list`)** | Show installed tools, version status, and filtering. |
| **1:30 - 2:15** | **Dependency Checking (`check`)** | Run compatibility check and inspect actionable fix suggestions. |
| **2:15 - 3:00** | **Installation & Dry-Run Safety (`install`)** | Demonstrate safe installation simulation using `--dry-run`. |
| **3:00 - 3:45** | **System Diagnostics (`doctor`)** | Run full system diagnostic report in Markdown and JSON. |
| **3:45 - 4:15** | **Environment Configuration (`configure`)** | Automatic environment variables and shell export generation. |
| **4:15 - 4:45** | **Extensibility (Adding a New Tool)** | Show how `tools.yaml` adds tools without touching code. |
| **4:45 - 5:00** | **Test Suite & Conclusion** | Run 159 tests achieving 86% coverage; closing remarks. |

---

## Detailed Demo Script & Spoken Narrative

### 1. Introduction (0:00 - 0:45)
**Speaker Narration:**
> "Hello everyone! My name is Mukul Sharma, and this is my submission for Task 5 of the FOSSEE eSim Winter Internship 2026 at IIT Bombay: the Automated Tool Manager for eSim.
> 
> eSim depends heavily on external EDA tools such as Ngspice, KiCad, GHDL, Verilator, and LLVM. Setting these up manually across different operating systems is often tedious, prone to version mismatches, and difficult to troubleshoot.
> 
> To solve this, I designed `esim-tm` — a declarative, manifest-driven Python tool manager with full dry-run safety, cross-platform package manager support, and automated health diagnostics."

---

### 2. Inspecting Tool Status: `esim-tm list` (0:45 - 1:30)
**Speaker Narration:**
> "Let's begin by listing all the external tools eSim needs. We simply run `esim-tm list`."

**Command:**
```bash
esim-tm list
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

**Speaker Narration:**
> "Notice the clear tabular view showing installed versions, required flags, minimum compatible versions, and current status.
> We can also filter for only required tools or by category, and even pass `--json` for automated script pipelines."

---

### 3. Dependency & Compatibility Checking: `esim-tm check` (1:30 - 2:15)
**Speaker Narration:**
> "Next, let's run `esim-tm check` to verify our entire toolchain."

**Command:**
```bash
esim-tm check
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

**Speaker Narration:**
> "The checker verifies minimum version constraints, checks recursive upstream dependencies with cycle prevention, and provides clear suggestions for any missing components."

---

### 4. Automated Installation with Dry-Run Safety: `esim-tm install` (2:15 - 3:00)
**Speaker Narration:**
> "Now let's look at installation. In production and educational lab environments, safety is paramount. That's why every mutating command in `esim-tm` supports `--dry-run`.
> Let's simulate installing Ngspice."

**Command:**
```bash
esim-tm --dry-run install ngspice
```

**Expected Output:**
```text
  ✅ Would install Ngspice via apt.
```

**Speaker Narration:**
> "`esim-tm` automatically detected that we are on a Debian/Ubuntu system, mapped Ngspice to the `apt` backend, and verified what command would be run — without modifying our host system.
> The same command on macOS would use Homebrew, and on Windows it would use Chocolatey."

---

### 5. Health Check Diagnostics: `esim-tm doctor` (3:00 - 3:45)
**Speaker Narration:**
> "One of the standout features of `esim-tm` is the `doctor` command. When a student or researcher encounters a simulation error in eSim, they can run `esim-tm doctor` to generate a comprehensive diagnostic report."

**Command:**
```bash
esim-tm doctor
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

**Speaker Narration:**
> "This report renders directly as clean GitHub Flavored Markdown or structured JSON with `--format json`, making it effortless to paste into GitHub issues or FOSSEE bug reports."

---

### 6. Environment Configuration & Shell Exports: `esim-tm configure` (3:45 - 4:15)
**Speaker Narration:**
> "To ensure that external tools work seamlessly within eSim, `esim-tm configure` manages required environment variables and PATH additions, automatically backing up old configurations before saving."

**Command:**
```bash
esim-tm configure --export --shell bash
```

**Expected Output:**
```bash
# Generated by esim-tm configure
export SPICE_LIB_DIR="/usr/share/ngspice"
export LLVM_DIR="/usr/lib/llvm-14"
export PATH="/usr/share/ngspice/bin:$PATH"
```

**Speaker Narration:**
> "Users can easily evaluate this into their `.bashrc`, `.zshrc`, or PowerShell profile with a single command."

---

### 7. Extensibility: Adding a New Tool Declaratively (4:15 - 4:45)
**Speaker Narration:**
> "Extensibility is a core design principle. If eSim adds support for a new tool like `yosys` or `openlane`, developers don't need to touch a single line of Python code.
> They simply add an entry to `tools.yaml` with the tool name, category, version command, regex pattern, and package mappings for `apt`, `brew`, and `choco`.
> The manager immediately loads, checks, and installs it."

---

### 8. Testing & Conclusion (4:45 - 5:00)
**Speaker Narration:**
> "Finally, let's run the automated test suite."

**Command:**
```bash
python -m pytest tests/ -v --tb=short
```

**Expected Output:**
```text
============================= 159 passed in 1.64s =============================
```

**Speaker Narration:**
> "We have 159 tests passing in under 2 seconds, achieving 86% code coverage, with full CI on both Linux and Windows.
> 
> In summary, `esim-tm` delivers all 5 required capabilities plus cross-platform support, dry-run safety, and diagnostic reporting. Thank you for your time and consideration!"
