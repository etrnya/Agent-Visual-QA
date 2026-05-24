# Agent-Visual-QA (AI Visual Auto-Layout Checker)

[English](README.md) • [繁體中文](README_zh.md)

`Agent-Visual-QA` is a lightweight, high-precision visual regression and layout QA tool built for AI coding agents and CI/CD pipelines. It automates responsive visual audits, using **Playwright** for multi-breakpoint RWD screenshot capture, a **Pillow-based local pixel diffing engine** to filter out identical pages, and **Gemini 2.5 Flash** for structural layout audits (identifying overlapping elements, overflow, and low-contrast issues).

```
[Current Render] ------+
                       |---> (Local Pillow Pixel Diff) --[Similar (0% diff)]--> [PASS (0 Tokens)]
[Baseline Image] ------+                  |
                                    [Mismatch (>0.1%)]
                                          |
                                          v
                              (WebP ROI compression)
                                          |
                                          v
                              (Gemini 2.5 Flash Vision) ---> [Audit Report & CSS Fixes]
```

---

## 🌟 Key Features

*   **RWD Breakpoints**: Captures screenshots across customizable resolutions (Mobile, Tablet, Desktop) in a single run.
*   **Token-Saver Differential Engine**: Performs local, pixel-by-pixel comparisons first. If changes are below your threshold (e.g. 0.1%), it exits with `0` immediately, saving **100% of LLM tokens**.
*   **WebP ROI Compression**: Automatically resizes and compresses mismatched images into WebP format before sending to Gemini, keeping prompt payload small and cost negligible.
*   **AI Vision Layout Audits**: Evaluates changes using Gemini 2.5 Flash with strict JSON schema constraints. Detects layout defects (overlapping text, clipping, low contrast) and outputs exact CSS patches.
*   **Seamless Developer Flow**: Clean CLI commands (`check`, `approve`, `status`) to easily manage baselines.

---

## 🚀 Getting Started

### 1. Requirements & Setup

*   Python 3.10+
*   Node.js (for Playwright dependency installation)

Clone the repository and initialize the virtual environment:

```bash
# Clone the repository
git clone https://github.com/etrnya/Agent-Visual-QA.git
cd Agent-Visual-QA

# Run setup scripts (installs virtualenv, dependencies, and headless browser binaries)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure API Key

To use the AI Vision audit, set your Gemini API key in your terminal session or write it to `visual_qa_config.json`:

```bash
# On Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key"

# On Linux / macOS
export GEMINI_API_KEY="your-gemini-api-key"
```

---

## 💻 CLI Command Reference

Execute commands using the `visual-qa` runner wrapper:

### `status`
Displays current baseline directories, existing screenshot counts, and default viewport resolutions.
```bash
.\visual-qa.bat status
```

### `check <url_or_file>`
Captures current rendering and compares it against baseline images.
```bash
# Perform standard check
.\visual-qa.bat check https://example.com

# Check a local HTML file
.\visual-qa.bat check tests/fixtures/test.html

# Force regenerate baselines instead of comparing
.\visual-qa.bat check https://example.com --baseline
```

### `approve`
Promotes all screenshots in the current temp workspace to the baseline directory.
```bash
.\visual-qa.bat approve
```

---

## 🤖 AI Agent & CI/CD Integration

To enable automated visual QA verification inside AI agents (like Google Antigravity, Cursor, Cline, or Claude Code), place `CLAUDE.md` in the project root containing:

```markdown
# Visual QA Integration
Always run visual verification on modified layouts:
$env:GEMINI_API_KEY="..."; .\visual-qa.bat check <url_or_path>
```

This prevents AI agents from creating broken responsive layouts and overlapping text blocks by letting the checker report failing layout nodes and exact CSS corrections automatically.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
