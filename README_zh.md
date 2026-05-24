# Agent-Visual-QA (AI 視覺自動排版檢查器)

[English](README.md) • [繁體中文](README_zh.md)

`Agent-Visual-QA` 是一款專為 AI 代理人 (AI Coding Agents) 與 CI/CD 流程設計的輕量級、高精度視覺回歸與排版 QA 工具。它能自動執行響應式設計 (RWD) 的網頁視覺檢測，利用 **Playwright** 在多個斷點進行截圖，並透過**基於 Pillow 的本地像素差異引擎**過濾未變更的頁面。當檢測到變化時，它會調用 **Gemini 2.5 Flash** 進行結構化排版審計（自動識別元素重疊、邊界溢出與對比度不足等問題）。

```
[當前網頁渲染] ---+
                  +---> (本地 Pillow 像素比對) --[完全相同 (0% 差異)]--> [通過 (消耗 0 Token)]
[基準線圖片] -----+                |
                               [檢測到變更 (>0.1%)]
                                   |
                                   v
                             (WebP 區域自動壓縮)
                                   |
                                   v
                             (Gemini 2.5 Flash Vision) ---> [輸出審計報告與 CSS 修復建議]
```

---

## 🌟 核心特色

*   **RWD 多斷點截圖**：支援在單次運行中自動捕獲多種自定義解析度（手機、平板、桌面）的頁面截圖。
*   **Token 熔斷省電引擎**：優先進行本地像素級對比。若圖像差異低於閾值（如 0.1%），直接以 `0` 退出，節省 **100% 的 LLM Token**。
*   **WebP 圖像極致壓縮**：發送至 Gemini 之前，自動將變更圖像壓縮成高效率 WebP 格式，使 Prompt 酬載極小化，API 費用幾乎為零。
*   **結構化 AI 視覺評估**：使用 Gemini 2.5 Flash 配合嚴格的 JSON Schema 進行視覺檢測。自動捕獲重疊文字、被遮擋的按鈕、低對比度文字，並給出精準的 CSS Patch。
*   **簡潔的開發者工作流**：提供直覺的 CLI 指令 (`check`、`approve`、`status`)，輕鬆管理視覺測試基準線 (Baseline)。

---

## 🚀 快速上手

### 1. 安裝環境與依賴

*   Python 3.10+
*   Node.js (用於安裝 Playwright 瀏覽器核心)

複製專案庫並初始化虛擬環境：

```bash
# 複製專案
git clone https://github.com/etrnya/Agent-Visual-QA.git
cd Agent-Visual-QA

# 建立並啟用虛擬環境，安裝相關套件
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置 API Key

要啟用 AI 視覺排版檢查，請在終端機中設置您的 Gemini API key 或寫入 `visual_qa_config.json`：

```bash
# Windows PowerShell 設置方式
$env:GEMINI_API_KEY="your-gemini-api-key"

# Linux / macOS 設置方式
export GEMINI_API_KEY="your-gemini-api-key"
```

---

## 💻 CLI 指令說明

使用 `visual-qa` 包裝指令執行工具：

### `status`
顯示當前基準線目錄位置、現有基準線截圖數量，以及默認 viewports 解析度設定。
```bash
.\visual-qa.bat status
```

### `check <url_or_file>`
捕獲當前渲染狀態並與基準線圖片進行對比。
```bash
# 進行標準網頁檢查
.\visual-qa.bat check https://example.com

# 檢查本地 HTML 檔案
.\visual-qa.bat check tests/fixtures/test.html

# 強制重新生成基準線圖片，而不進行比對
.\visual-qa.bat check https://example.com --baseline
```

### `approve`
將當前 temp 暫存區中捕獲的所有最新截圖提升 (Promote) 為基準線 (Baseline) 圖片。
```bash
.\visual-qa.bat approve
```

---

## 🤖 AI 代理人與 CI/CD 整合

為了在 AI 代理人（如 Google Antigravity, Cursor, Cline 或 Claude Code）中自動套用此排版檢查，可在您的專案根目錄下放置包含以下內容的 `CLAUDE.md`：

```markdown
# 視覺 QA 整合規範
在修改排版與 CSS 後，請務必執行視覺驗證：
$env:GEMINI_API_KEY="..."; .\visual-qa.bat check <url_or_path>
```

這能阻止 AI 代理人生產出跑版、文字疊加或不可讀的響應式佈局，使其能自動讀取排版錯誤報告並進行 CSS 修復。

---

## 📄 授權條款

本專案基於 MIT 授權條款進行開源。詳見 [LICENSE](LICENSE) 檔案。
