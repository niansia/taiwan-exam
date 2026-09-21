# 各平台使用指引

[返回首頁](../README.md) · [下載最新知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)

**2026.09.21.3：** Claude Skills 與有 Skills 的 ChatGPT 帳號，建議下載內建七科模板與版型的[網頁工具 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.3/taiwan-exam-hosted-2026.09.21.3.zip)，不解壓直接上傳。ChatGPT Project、Claude Project、Gemini Gem 的知識區仍可使用 MD。可執行 Python／讀寫檔案的網頁對話，也能附上同一 ZIP，請模型解壓後使用既有工具。

以下保留各平台的安裝與叫用範例；選單與可用工具以帳號實際介面為準。
網頁版更新須替換已儲存的知識檔，GitHub 更新不會自動同步舊附件。

### ChatGPT 網頁版

**有 Skills 的帳號，建議直接上傳 ZIP：** 依 [OpenAI 官方說明](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)，Skills 目前開放給 Business、Enterprise、Healthcare、Edu 帳號，並受工作區設定限制。在左側欄點 `Plugins`，選 `Skills` 分頁，再點 `Create → Upload from your computer`，選取未解壓的[網頁工具 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.3/taiwan-exam-hosted-2026.09.21.3.zip)。ChatGPT 會先掃描：通過後即可使用；顯示 `Needs Review` 時請自行檢視後再決定；顯示 `Blocked` 則無法使用。直接上傳保留原始 SKILL.md、scripts 與 references，不經模型改寫，因此不必再用 `@skill-creator` 建立。

安裝後開新對話即可提出需求，也可以在輸入框鍵入 `@` 選取 `taiwan-exam-generator`：

```text
請出一份 116 學測社會完整模擬考。
請分開交付題目 PDF 與答案詳解 PDF，依 Skill 完成命題、解題驗證與逐頁版面檢查。
```

**上傳被管理員關閉，但仍有 `@skill-creator`：** 在「對話」模式輸入 `@skill-creator`。只要選單能選到它（如使用者畫面已出現藍色 `@skill-creator` 標籤），對話模式就可以建立 Skill，不必強制切換「工作」；找不到時再切到「工作」模式重試。附上知識檔後貼上：

```text
請使用我附上的 taiwan-exam-web-knowledge.md 建立「Taiwan Exam Generator」Skill。
請永久儲存，使本對話立即可用，之後的新對話也能選取。
完整保留其中規則與資源索引，不要另寫一套通用出題器；安裝時須保存
七科共 30 個逐檔 PDF 直連與驗證資料，但不要下載 PDF 本體。
實際開始出某科時，才取得該科 3 份固定 PDF（數學為 4 份），
逐份驗證後以原 PDF 當底層，不得 OCR、重打、重排或另做相似版面。
完成後不要要求我另開新對話，直接在本對話接受出卷需求。
```

若介面顯示「安裝」或「儲存」按鈕，按一次是 ChatGPT 的原生永久保存確認，檔案內容無法替使用者略過這個安全步驟。確認後可在**同一個對話立刻**出卷；之後開新對話時，鍵入 `@` 並選取 `Taiwan Exam Generator` 即可，不必重新上傳知識檔。

完整考卷、兩份 PDF 與逐頁檢查屬於成品工作，建議在「工作」模式執行；但這是能力與穩定性建議，不是建立或叫用 Skill 的硬性條件。若對話模式本身已有檔案建立與檢查能力，也可以直接使用。若帳號沒有 Skills，可建立一個固定 Project，把知識檔與第一次設定文字放入 Project；不要把普通聊天的一次附件上傳稱為永久安裝。

### Claude：聊天專案／Skills／Cowork

**聊天專案方式：** 在 Claude 的 Chat 介面進入 `Projects`，建立 `Taiwan Exam`，把[新版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)加入 `Project Knowledge`，並把這段存入 `Project Instructions`：

```text
本 Project 一律採用 Knowledge 中的 Taiwan Exam Skill 規則出題。
不要另寫通用命題器；完整考卷須分開交付題目 PDF 與答案詳解 PDF，
並完成內容、答案與逐頁版面檢查。能力不足時請明確回報，不得以聊天文字冒充 PDF。
封面、頁首頁尾與公式頁一律套用原始模板，不可自行重畫；無法套用時先停下來告訴我，其他情況不要中途停下來回報進度。
```

以後進入同一個 Project，附上當科兩份版型與[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)（知識檔不含模板），只要說：

```text
請依 Taiwan Exam Skill 出一份 116 學測英文完整模擬考，分開交付題目 PDF 與答案詳解 PDF。
```

**原生 Skill 方式（建議）：** 到 `Customize → Skills → ＋ → Create skill → Upload a skill`，直接上傳[新版 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.3/taiwan-exam-hosted-2026.09.21.3.zip)，**不要解壓**，儲存並啟用。此套件的短版入口會按需使用分開的規則與工具，不再把約 2.5 MB 的聚合 MD 當作原生 Skill 正文。曾安裝舊 MD 的使用者請停用舊版並改用 ZIP。之後開 Chat 或選取輸入框的 **Cowork**，直接貼上出卷需求；版型與模板已內建，不必附檔。不必另建聊天專案，也不必每次再附 ZIP。不能把 Markdown 改名成 ZIP。

`Settings → Capabilities` 需開啟 `Code execution and file creation`；組織帳號可能由管理員控制。**Cowork 是任務模式、Claude for Word 是 Word 外掛、Claude Code 是另一種開發工具**。本專案尚未驗證 Word 外掛的固定模板 PDF 流程。Cowork 的本機檔案存取需 Claude Desktop 開啟並連線。詳見 [README 的 Claude 安裝](../README.md#claude)、[出卷步驟](../README.md#第-3-步出卷)與 [Claude 官方 Cowork 說明](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork)。

v0.7.1 是較舊的本機安裝包，不含後續網頁修正。網頁原生 Skill 請使用 `taiwan-exam-hosted-2026.09.21.3.zip`；聊天專案則替換新版知識檔。套件驗證不代表帳號實際上傳、安全掃描或完整出卷已通過。

若一般出卷對話已附上工具 ZIP，可貼上：

```text
請解壓我附上的 Taiwan Exam 網頁工具 ZIP，依 hosted-execution 流程使用內附工具。
只讀本次科目所需資料，不要重新建立排版與檢查工具；題目、圖表與解答仍须原創。
若接續先前考卷，請沿用已保存進度，完成剩餘檢查後再交付兩份 PDF。
```

若第一輪尚未交付，在同一對話輸入「繼續完成」；Claude 若有 `Continue` 按鈕也可點選。這是接續同一份工作，並非重新命題；如果平台回報檔案已遺失，再補傳可恢復的檔案。

### Gemini 網頁版

到 `Gems > New Gem`，名稱填 `Taiwan Exam`，把知識檔加入 `Knowledge`，並把這段放入 Instructions：

```text
採用 Knowledge 中的 Taiwan Exam Skill 全部規則；不要另寫通用命題器。
完整考卷須分開交付題目 PDF 與答案詳解 PDF，並完成可用的內容與逐頁檢查。
封面、頁首頁尾與公式頁一律套用原始模板，不可自行重畫；無法套用時先停下來告訴我，其他情況不要中途停下來回報進度。
```

以後從 `My Gems` 選取 `Taiwan Exam`，附上當科兩份版型與[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)，再說：

```text
請出一份 116 學測自然完整模擬考，依 Skill 交付題目 PDF 與答案詳解 PDF。
```

## CLI 版：Codex、Claude Code、Gemini CLI

Windows、macOS、Linux 使用同一份 Skill。以下第一個區塊是在對應 AI 的互動視窗中輸入；只有 Gemini 的安裝指令是在一般終端機執行。

### Codex CLI

第一次在 Codex 輸入：

```text
$skill-installer
請從 https://github.com/niansia/taiwan-exam 安裝 taiwan-exam-generator 為使用者層級 Skill。
先讀 INSTALL.md，完成完整性檢查；不要使用舊 ZIP，也不要覆寫我的私人考試資料。
```

安裝後可用 `/skills` 確認；以後輸入：

```text
$taiwan-exam-generator
請出一份 116 學測數學 B 完整模擬考，分開交付題目 PDF 與答案詳解 PDF。
```

### Claude Code CLI

第一次啟動 Claude Code 後貼上：

```text
請從 https://github.com/niansia/taiwan-exam 取得完整原始碼，先讀 INSTALL.md，
再把 taiwan-exam-generator 安裝到我的使用者層級 Skills 並驗證。不要使用舊 ZIP，
若已安裝就沿用，不要覆寫私人 exam_packs 或自訂模板。
```

以後可輸入 `/taiwan-exam-generator` 或從 `/` 選單選取技能，再接著說：

```text
請出一份 116 學測社會完整模擬考，分開交付題目 PDF 與答案詳解 PDF。
```

### Gemini CLI

第一次在一般終端機執行：

```sh
gemini skills install https://github.com/niansia/taiwan-exam
```

進入 Gemini CLI 後用 `/skills list` 確認，需要重新掃描時用 `/skills reload`。以後直接說：

```text
請使用 taiwan-exam-generator，出一份 116 學測英文完整模擬考，
分開交付題目 PDF 與答案詳解 PDF，並完成逐頁檢查。
```

## 桌面版：Codex 與 Claude Code Desktop

### Codex 桌面版

不用開終端機。第一次在聊天框貼上：

```text
請使用 $skill-installer，從 https://github.com/niansia/taiwan-exam
安裝 taiwan-exam-generator 為我的使用者層級 Skill。先讀 INSTALL.md 並完成驗證；
不要使用舊 ZIP，也不要覆寫我的私人考試資料。
```

以後輸入 `$` 選取 `taiwan-exam-generator`，或直接貼上：

```text
$taiwan-exam-generator
請出一份 116 學測國綜完整模擬考，分開交付題目 PDF 與答案詳解 PDF。
```

### Claude Code Desktop

在桌面版開啟一個本機資料夾，第一次貼上與 Claude Code CLI 相同的安裝文字。安裝後輸入 `/`，從技能清單選取 `taiwan-exam-generator`，再描述考卷需求。一般 ChatGPT／Claude 桌面聊天若沒有本機代理或技能安裝能力，請照上面的「網頁版」做法使用 Project／Skill；不要把兩者混為一談。

各平台的安裝範圍、手動備援與驗證方式見 [INSTALL.md](../INSTALL.md)。帳號若未開放檔案建立、程式執行或逐頁 PDF 檢查，AI 必須明確說明缺少的能力，不能用聊天文字冒充兩份已驗收 PDF。
