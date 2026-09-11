# Taiwan Exam 一次安裝指引

這份文件主要給 AI 代理讀。目標是讓使用者只需貼一次儲存庫網址，之後直接用自然語言出題；不要把終端機操作轉嫁給不會寫程式的使用者。

## 目前可安裝的內容

只使用 GitHub 上的公開原始碼：

```text
https://github.com/niansia/taiwan-exam
```

預先封裝 ZIP／Release 仍因 2026-09-09 Defender 下載附件事件暫停。不可從 Git 歷史還原舊包、改用舊下載網址、關閉防毒、解除檔案封鎖或聲稱新的檔名已解決事件。若原始碼取得也觸發安全警告，停止安裝並明確回報。

## 代理的安裝流程

### 1. 先檢查既有安裝

在目前平台列出或搜尋已啟用的技能，確認 `taiwan-exam-generator` 是否存在。

- 已存在且檔案完整：直接沿用；不要為了「確保最新」自動覆寫。
- 使用者要求更新：先保存其私人 `exam_packs`、自訂模板與未提交工作，再比較版本。
- 只缺某科參考資料：補該科資料，不要重裝整個 Skill。
- 名稱存在但檔案不全：說明缺少項目，再採可復原的更新或重新安裝。

安裝範圍必須說清楚：使用者層級、單一工作區，或只在本次暫存環境有效。不得把「本次讀過 README」說成已永久安裝。

### 2. 依平台安裝

#### OpenAI Codex

優先使用 Codex 內建的 Skill Installer，從上述 GitHub 儲存庫安裝為使用者層級技能。安裝器應保留完整儲存庫結構，讓 `SKILL.md`、`references/`、`scripts/`、`schemas/`、`templates/` 與 `exam_packs/` 位於同一技能根目錄。

若內建安裝器不可用，才將經使用者同意取得的本機原始碼副本放到：

- Windows：`%USERPROFILE%\.codex\skills\taiwan-exam-generator\`
- macOS／Linux：`~/.codex/skills/taiwan-exam-generator/`

若設定了自訂 `CODEX_HOME`，以該環境實際的 `skills` 目錄為準。不要猜測其他裝置或 ChatGPT 網頁版會自動同步。

#### Claude Code

安裝完整原始碼資料夾到個人技能位置：

- Windows：`%USERPROFILE%\.claude\skills\taiwan-exam-generator\`
- macOS／Linux：`~/.claude/skills/taiwan-exam-generator/`

若使用者只要單一專案可用，可改放 `<專案>/.claude/skills/taiwan-exam-generator/`。`SKILL.md` 必須正好位於該技能資料夾根目錄；不要只複製一份 Markdown 而遺失支援資源。已存在同名資料夾時不要直接覆寫。

參考：[Claude Code Skills](https://code.claude.com/docs/en/skills)。

#### Gemini CLI

優先使用 Gemini CLI 的技能管理功能安裝 Git 儲存庫；需要使用者確認時，讓產品顯示原生確認流程：

```sh
gemini skills install https://github.com/niansia/taiwan-exam
```

安裝後以 `/skills list` 確認，必要時用 `/skills reload`。若使用本機開發副本，可由代理選擇 `gemini skills link <本機資料夾>`；不要手動製造不受管理的重複副本。

Gemini CLI 的使用者技能通常由 `~/.gemini/skills/` 或 `~/.agents/skills/` 發現，工作區技能則位於 `.gemini/skills/` 或 `.agents/skills/`。以當前版本實際顯示為準。

參考：[Gemini CLI Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)。

### 3. 驗證技能完整性

至少確認下列項目存在且可讀：

```text
SKILL.md
NOTICE
ORIGIN.json
references/first-use.md
references/exam-pack-execution-contract.md
scripts/validate_exam_release.py
scripts/render_gsat_official.py
schemas/exam.schema.json
exam_packs/學測/manifest.json
exam_packs/學測/templates/115/template-pack.json
```

確認技能名稱為 `taiwan-exam-generator`，並讓平台重新載入技能清單。若平台提供原生技能清單，必須看得到此名稱；只看到普通資料夾不算完成。

### 4. 只準備當次需要的執行環境

安裝 Skill 不等於一次安裝所有 PDF／瀏覽器工具。第一次實際出題時，依科目與輸出需求檢查：

- Python 3.10+
- `requirements.txt` 中的 PDF／HTML 依賴
- 可用的 Chrome、Chromium 或 Edge（需要瀏覽器排版時）
- 繁體中文字型與逐頁 PDF／影像檢查能力

代理應在權限允許時自行準備必要依賴，並避免改動無關的系統設定。`xlrd` 只在匯入舊式 `.xls` 統計資料時才需要，不得阻擋一般安裝或出題。

這個專案不需要 API key、遠端授權碼、裝置識別或維護者啟用。缺少正式卷校準資料仍可能阻擋完整考卷，但那是內容證據問題，不是安裝失敗。

### 5. 向使用者回報

回報必須包含：

- 安裝的平台與範圍
- 技能是否已被原生清單辨識
- 是否尚缺當次出題才需要的 PDF／字型／參考資料
- 下一句可直接使用的範例

建議最後只給使用者這句：

```text
安裝完成。你現在可以說：「請使用 Taiwan Exam，出一份學測數學 A 完整模擬考，附答案、詳解與 PDF。」
```

若沒有實際跨新對話測試，只能寫「跨對話呼叫待確認」，不能保證永久可用。

## 網頁版 GPT／Claude／Gemini

若平台只有自訂指示、知識檔或附件上傳，可把 `SKILL.md` 與相關 `references/` 作為規則來源；但必須標示為**有限模式**。下列任一能力缺少時，不可宣稱完整支援：

- 保留技能完整目錄並按需讀取檔案
- 執行 Python 驗證器與排版器
- 取得或讀取合法的官方參考資料
- 檢查每一頁 PDF 的實際畫面

一次附件上傳不等於跨對話安裝。不要捏造 ChatGPT、Claude.ai 或 Gemini 網頁版尚未提供的安裝按鈕、持久性或本機執行能力。

## 更新與移除

只有在使用者明確要求時更新。更新前先辨識專案自有檔案與使用者加入的私人資料，採可復原方式備份或搬移；不要用破壞性重設覆蓋工作。

移除時只刪除已確認的技能安裝資料夾或使用平台的原生解除安裝功能。不得刪除其他專案、使用者的 `exam_packs` 副本或共享技能目錄。
