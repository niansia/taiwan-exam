# Taiwan Exam｜臺灣大型考試命題 Skill

Taiwan Exam 是一套給 AI 代理使用的學測／會考命題、排版與驗證規格。你可以用一般中文提出需求；AI 依科目規則建立原創題目、詳解、正式卷面與檢查紀錄，不需要你先學會寫程式。

目前支援學測國綜、國寫、英文、數學 A、數學 B、社會、自然，以及會考各科的資料夾與工作流程。專案不是題庫，也不會把歷屆題換數字後重新輸出。

> **可執行 Skill ZIP 仍暫停。** 舊草稿與舊 ZIP 已刪除；先前候選的
> Chrome 下載問題尚未解除。純 PDF／圖片的學測來源資料包另以
> `source-corpus-2026.09.11` Data Release 提供，不含程式或安裝檔，且由
> source manifest 驗證；兩者不是同一個發布面。軟體 ZIP 狀態見
> [SOFTWARE_RELEASE_STATUS.json](SOFTWARE_RELEASE_STATUS.json)。

## 三種使用方式

| 你正在使用 | 第一次怎麼做 | 以後怎麼叫出來 |
| --- | --- | --- |
| ChatGPT、Claude.ai、Gemini 網頁版 | 點[「直接下載網頁版知識檔」](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)，再上傳以建立 Skill、Project 或 Gem | 開啟同一個 Skill／Project／Gem，再說要出的科目 |
| Codex CLI、Claude Code、Gemini CLI | 從 GitHub 原始碼安裝完整 Skill | Codex 用 `$taiwan-exam-generator`、Claude Code 用 `/taiwan-exam-generator`；Gemini CLI 可直接用自然語言要求採用該 Skill |
| Codex 或 Claude Code 桌面版 | 在聊天框請代理從本儲存庫安裝，不必自己搬檔案 | 從技能選單選取 Taiwan Exam，或輸入對應的 `$`／`/` 名稱 |

無論用哪一種方式，完整考卷都要分開交付「題目 PDF」與「答案詳解 PDF」，並完成內容、答案及逐頁版面檢查。只想試幾題時請明說「自訂練習」。

## 網頁版：ChatGPT、Claude.ai、Gemini

### [⬇ 直接下載網頁版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)

點上面的連結後，瀏覽器會自動下載 `taiwan-exam-web-knowledge.md`；不需要理解 GitHub、尋找 `Raw` 或按右上角的小圖示。若瀏覽器阻擋自動下載，開啟的頁面會保留一個明顯的「再次下載」按鈕。[查看檔案內容與版本](web/taiwan-exam-web-knowledge.md)。

這份檔案是同一套正式規則自動彙整、方便網頁平台讀取的單一 Markdown，不是另一套命題器，也不是 ZIP 或執行檔。

### ChatGPT 網頁版

先在目前的 ChatGPT「對話」模式輸入 `@skill-creator`。只要選單能選到它（如使用者畫面已出現藍色 `@skill-creator` 標籤），對話模式就可以建立 Skill，不必強制切換「工作」。若帳號在對話模式找不到它，再切到「工作」模式重試。附上知識檔後貼上：

```text
請使用我附上的 taiwan-exam-web-knowledge.md 建立「Taiwan Exam Generator」Skill。
完整保留其中規則與資源索引，不要另寫一套通用出題器。
完整考卷必須分開交付題目 PDF 與答案詳解 PDF，並完成逐頁檢查。
```

建立後，在新對話的輸入框鍵入 `@`；確實能選到 `Taiwan Exam Generator` 才算保存成功。選取後再貼上：

```text
請出一份 116 學測社會完整模擬考。
請分開交付題目 PDF 與答案詳解 PDF，依 Skill 完成命題、解題驗證與逐頁版面檢查。
```

完整考卷、兩份 PDF 與逐頁檢查屬於成品工作，建議建立成功後切到「工作」模式執行；但這是能力與穩定性建議，不是建立或叫用 Skill 的硬性條件。若對話模式本身已有檔案建立與檢查能力，也可以直接使用。若帳號沒有 Skills，可建立一個固定 Project，把同一知識檔與第一次設定文字放入 Project；不要把普通聊天的一次附件上傳稱為永久安裝。

### Claude.ai 網頁版

建立 `Taiwan Exam` Project，把知識檔加入 `Project Knowledge`，並把這段存入 `Project Instructions`：

```text
本 Project 一律採用 Knowledge 中的 Taiwan Exam Skill 規則出題。
不要另寫通用命題器；完整考卷須分開交付題目 PDF 與答案詳解 PDF，
並完成內容、答案與逐頁版面檢查。能力不足時請明確回報，不得以聊天文字冒充 PDF。
```

以後進入同一個 Project，只要說：

```text
請依 Taiwan Exam Skill 出一份 116 學測英文完整模擬考，分開交付題目 PDF 與答案詳解 PDF。
```

Claude 的原生 Skill ZIP 上傳要等本專案重新開放安全 ZIP；目前不要使用舊包。

### Gemini 網頁版

到 `Gems > New Gem`，名稱填 `Taiwan Exam`，把知識檔加入 `Knowledge`，並把這段放入 Instructions：

```text
採用 Knowledge 中的 Taiwan Exam Skill 全部規則；不要另寫通用命題器。
完整考卷須分開交付題目 PDF 與答案詳解 PDF，並完成可用的內容與逐頁檢查。
```

以後從 `My Gems` 選取 `Taiwan Exam`，再說：

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

各平台的安裝範圍、手動備援與驗證方式見 [INSTALL.md](INSTALL.md)。帳號若未開放檔案建立、程式執行或逐頁 PDF 檢查，AI 必須明確說明缺少的能力，不能用聊天文字冒充兩份已驗收 PDF。

## 平台支援

| 平台 | 支援方式 | 能力範圍 |
| --- | --- | --- |
| OpenAI Codex 桌面版／CLI／IDE | 請代理使用內建 Skill Installer 從本儲存庫安裝使用者技能 | 完整：可讀參考資料、執行驗證、排版及檢查 PDF，仍取決於本機工具與授權 |
| Claude Code | 安裝至個人 `skills` 目錄，或在單一專案使用專案技能 | 完整：可執行本機工作流程；安裝位置依 Claude Code 的使用者／專案範圍決定 |
| Gemini CLI | 從 Git 儲存庫安裝 Agent Skill；也可連結本機副本 | 完整：可執行本機工作流程；首次安裝與啟用會依 Gemini CLI 要求確認 |
| ChatGPT 網頁版 | 對話模式能選到 `@skill-creator` 就可建立；找不到時改用工作模式，或放入有固定指示的 Project | 可持續在該 Skill／Project 使用；完整 PDF 建議在工作模式執行，最終仍取決於帳號工具 |
| Claude.ai | 把 Web Knowledge 加入 Project Knowledge 並設定 Project Instructions；安全 ZIP 恢復後才使用原生 Skill 上傳 | 可持續在該 Project 的各聊天使用；PDF 需要 Code execution/file creation |
| Gemini 網頁版 | 建立 `Taiwan Exam` Gem，加入同版 Web Knowledge Markdown | 可持續在該 Gem 使用；完整 PDF 驗收取決於帳號提供的檔案建立與檢查工具 |

本專案採通用 `SKILL.md` 結構；網頁版單一知識檔由相同規則自動彙整，不是另一套命題規則。三家產品的帳號權限與工具能力仍可能不同。網頁聊天中的一次普通附件上傳，不等於跨對話安裝。

官方平台文件：[ChatGPT Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude.ai Skills](https://support.claude.com/en/articles/12512180-use-skills-in-claude)、[Gemini Gems](https://support.google.com/gemini/answer/15146780)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[Gemini CLI Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)。介面可能更新，實際帳號顯示為準。

### 作業系統

| 系統 | 使用者層級技能位置（手動備援） |
| --- | --- |
| Windows | Codex：`%USERPROFILE%\.codex\skills\taiwan-exam-generator`；Claude Code：`%USERPROFILE%\.claude\skills\taiwan-exam-generator` |
| macOS／Linux | Codex：`~/.codex/skills/taiwan-exam-generator`；Claude Code：`~/.claude/skills/taiwan-exam-generator` |
| Gemini CLI | 優先使用 `gemini skills install https://github.com/niansia/taiwan-exam`，由 CLI 管理使用者層級位置 |

一般使用者不必自行搬資料夾。只有平台的自動安裝不可用時，才參考 [INSTALL.md](INSTALL.md) 的手動備援；遇到權限或防毒警告應停止並回報，不要解除保護。

## 能做什麼

- 依現行學測／會考範圍，分科建立完整考卷或指定題型練習。
- 以 111～115 學測正式卷型為現行學測的主要結構依據，區分國綜／國寫、數 A／數 B，不混用舊制數學。
- 控制題型、配分、難度、知識分布、單選答案位置、素養材料、圖表與黑白列印可讀性。
- 要求每題有新的證據與推理架構；換人名、換數字、換圖片或套固定題幹不算創新。
- 產生學生卷、答案詳解與驗證摘要；完整卷必須通過內容與逐頁版面檢查。
- 以 115 學測樣貌的空白頁面資產作為排版起點，年份、測驗名稱與頁數可由當次需求填入。

各科的硬性規則都在 [SKILL.md](SKILL.md) 與 `references/`。例如自然第 1～36 題的單／多選結構、四科九題連續區塊，社會史地公民平衡，英文 7,000 字詞範圍內提高誘答競爭，及國綜／國寫的選文與字數要求，都不是通用模板自行猜測。

## 完整考卷的品質門檻

完成一份卷不是只產生 PDF。代理必須依序完成：

1. 核對該科官方考試說明、題數、題型、配分、作答方式與卷面。
2. 建立整卷藍圖，檢查課綱核心、章節／學科比例、難度曲線與作答時間。
3. 為每題設計新的材料關係、解題路徑與有效誘答；禁止由舊題表面改寫。
4. 獨立解題並核對答案、配分、詳解與多選規則。
5. 套用科目版型，逐頁檢查字形、公式、圖表、題號、頁首、留白、裁切與黑白輸出。
6. 執行同一套發布驗證；任何必要項目失敗，就回報缺口而不是把校樣改名成正式版。

「軟體測試通過」只代表工具按預期工作，不代表某份考卷的內容已通過，也不等於學生實測難度證據。

## 歷屆試卷與模考來源如何取得？

一般 Git clone 保持輕量，不把約 3.4 GB 的 PDF 直接寫進 Git 歷史；GitHub
也會封鎖超過 100 MiB 的一般 Git 檔案。完整來源沒有被當成可有可無：
它們依科目放在 GitHub 的
[`source-corpus-2026.09.11` 資料 Release](https://github.com/niansia/taiwan-exam/releases/tag/source-corpus-2026.09.11)，並由
Skill 自動下載、逐檔驗證後放回 Exam Pack。第一次製作某科完整卷時，
本機代理應自行執行，例如：

```text
python scripts/bootstrap_exam_sources.py --subject 社會
```

一般使用者不必自己操作終端機；直接要求 AI「準備社會來源資料並出卷」
即可。下載採科目分包，不需要為一科考卷先抓完整 3.4 GB。來源包的
資產、檔案路徑、大小與 SHA-256 都記錄於
[`source-pack-manifest.json`](exam_packs/學測/source-pack-manifest.json)。

官方正式卷也可由 `scripts/download_ceec_gsat.py` 從[大考中心](https://www.ceec.edu.tw/)
重新取得。使用者另外提供的私人資料不會因此自動進入公開資料包。

各科預留資料夾如下：

```text
exam_packs/<考試>/subjects/<科目>/
├─ 歷屆試題/
├─ 模擬考/
├─ format-references/
├─ answer-profiles/
└─ 命題範圍/
```

資料匯入不等於完成校準；實際來源必須可讀、雜湊相符並通過 Exam Pack
稽核，才能使用 `verified` 的正式卷面主張。`放資料到這裡.md` 只是保留
空目錄的提示檔，不是 PDF 或校準證據的替代品。

## 交付內容

完整卷通過後，通常包含：

- 學生版試卷 PDF
- 分開的答案與完整詳解 PDF
- 結構化考卷資料與驗證摘要

若環境無法完成 PDF 產生或逐頁檢查，代理可以在你同意後提供 HTML／文字校樣，但不得把它宣稱為已驗收正式 PDF。

## 維護者與進階使用者

基本環境為 Python 3.10+。PDF 讀取與排版依賴列在 `requirements.txt`；舊式 Excel 統計匯入才需要 `requirements-statistics.txt`。Chrome／Chromium／Edge、繁體中文字型與其他排版工具只在相關工作需要時準備。

```sh
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
python scripts/validate_attribution.py .
```

正式封裝必須通過 [SOFTWARE_RELEASE_STATUS.json](SOFTWARE_RELEASE_STATUS.json) 與[軟體發布安全流程](references/software-release-security.md)；不得自行改名、換網址或沿用舊掃描紀錄。原始碼發布與預先封裝安裝檔是兩個不同的發布面。

## 授權與非官方聲明

本專案不是大考中心、心測中心、OpenAI、Anthropic 或 Google 的官方產品，也不代表其背書。

自有程式與文件採 [MIT License](LICENSE)，著作權與來源見 [NOTICE](NOTICE)、[ORIGIN.json](ORIGIN.json) 及[改作說明](references/attribution-and-forks.md)。MIT 不替第三方試卷、文章、圖片、資料或字型授權。
