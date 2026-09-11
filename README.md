# Taiwan Exam｜臺灣大型考試命題 Skill

Taiwan Exam 是一套給 AI 代理使用的學測／會考命題、排版與驗證規格。你可以用一般中文提出需求；AI 依科目規則建立原創題目、詳解、正式卷面與檢查紀錄，不需要你先學會寫程式。

目前支援學測國綜、國寫、英文、數學 A、數學 B、社會、自然，以及會考各科的資料夾與工作流程。專案不是題庫，也不會把歷屆題換數字後重新輸出。

> **ZIP／Release 仍暫停。** 舊草稿與舊 ZIP 已刪除；2026-09-11 的新候選雖通過最新版 Defender 檔案與附件檢查，一般 Chrome 下載仍回報 `ERR_BLOCKED_BY_CLIENT`，因此候選 release 與標籤也已撤下。不可從 Git 歷史取回或把通過的檔案掃描誤當成瀏覽器驗收。事實與復原條件見 [SOFTWARE_RELEASE_STATUS.json](SOFTWARE_RELEASE_STATUS.json)、[安全事件紀錄](references/security-incident-2026-09-09.md)及[候選檢查紀錄](references/security-resolution-2026-09-11.md)。

## 網頁版一分鐘開始

不會寫程式也可以使用。先下載同一套規則自動彙整的[網頁版知識檔](web/taiwan-exam-web-knowledge.md)。它可用於 ChatGPT 的 Skill／Project、Claude Project 與 Gemini Gem，不是另一套命題器。

第一次在 ChatGPT Work 的 Skill/Project、Claude Project 或 Gemini 的 Gem 建立頁面中，上傳這份 Markdown 並貼上：

```text
請採用我附上的 Taiwan Exam Skill，完整保留它的規則與支援資源，
並儲存為之後對話可用的 Taiwan Exam Skill／Gem。不要另寫通用出題器。
```

以後開啟該 Skill／Gem，只要說：

```text
請使用 Taiwan Exam，出一份 116 學測數學 B 完整模擬考。
請分開交付題目 PDF 與答案詳解 PDF，依 Skill 完成內容、答案與逐頁版面檢查。
```

ChatGPT Work 建立 Skill 後可在輸入框鍵入 `@` 選擇；Claude 可把 Markdown 放進 Project Knowledge；Gemini 到 `Gems > New Gem`，把 Markdown 加入 `Knowledge`。各平台完整步驟見[網頁版使用說明](references/web-platform-use.md)及 [INSTALL.md](INSTALL.md)。Claude 的原生 Skill ZIP 上傳路徑要等通過安全驗收的新 ZIP；目前不要使用舊包。帳號若未開放檔案建立或程式執行，AI 必須明確說明缺少的能力，不能用聊天文字冒充兩份已驗收 PDF。

## 本機版一分鐘開始

建議使用能讀寫本機檔案、執行驗證程式並檢查 PDF 的 AI 代理：Codex、Claude Code 或 Gemini CLI。Windows、macOS、Linux 使用同一份 Skill；路徑與工具差異由代理處理。

第一次只要把下面這段貼給 AI：

```text
請把 Taiwan Exam 安裝成我的使用者層級 Skill：
https://github.com/niansia/taiwan-exam

請先讀儲存庫中的 INSTALL.md，依我目前的 Codex／Claude Code／Gemini CLI
與作業系統完成安裝及驗證。不要使用舊版 ZIP，不要關閉安全防護；
若已安裝就沿用，不要覆寫我的私人考試資料。
```

安裝後可直接說：

```text
請使用 Taiwan Exam，出一份 116 學測數學 B 完整模擬考，附答案、詳解與 PDF。
請先核對課綱與卷型；每頁排版和公式都要檢查，未通過不得稱為正式版。
```

或：

```text
請使用 Taiwan Exam，出學測社會與自然各一份。
題目要原創、課綱內、重視材料推理；真實照片轉黑白後仍須保留解題證據。
答案與詳解另外輸出。
```

只想試幾題時請明說「自訂練習」；完整模考不會因資料或工具不足而偷偷縮成短題組。

## 平台支援

| 平台 | 支援方式 | 能力範圍 |
| --- | --- | --- |
| OpenAI Codex 桌面版／CLI／IDE | 請代理使用內建 Skill Installer 從本儲存庫安裝使用者技能 | 完整：可讀參考資料、執行驗證、排版及檢查 PDF，仍取決於本機工具與授權 |
| Claude Code | 安裝至個人 `skills` 目錄，或在單一專案使用專案技能 | 完整：可執行本機工作流程；安裝位置依 Claude Code 的使用者／專案範圍決定 |
| Gemini CLI | 從 Git 儲存庫安裝 Agent Skill；也可連結本機副本 | 完整：可執行本機工作流程；首次安裝與啟用會依 Gemini CLI 要求確認 |
| ChatGPT 網頁版 | 在 ChatGPT Work 用 `@skill-creator` 與 Web Knowledge 建立 Skill；或放入有固定指示的 Project | 可持續在該 Skill／Project 使用；完整 PDF 驗收仍取決於工作區工具 |
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

## 為什麼公開儲存庫沒有歷屆試卷？

公開版只保留自有規則、程式、結構化彙總、空白版型與合成測試資料。它不散布出版社模考、歷屆試題全文、掃描圖片、答案原檔、字型或使用者私人資料。

第一次製作正式卷時，代理會依需求從[大考中心](https://www.ceec.edu.tw/)等官方來源核對可合法取得的考試說明與試題；需要你自己的模考或版面樣本時，才請你提供指定檔案。私人資料應留在本機且不得提交到公開儲存庫。

各科預留資料夾如下：

```text
exam_packs/<考試>/subjects/<科目>/
├─ 歷屆試題/
├─ 模擬考/
├─ format-references/
├─ answer-profiles/
└─ 命題範圍/
```

資料匯入不等於完成校準；公開版的官方結構紀錄刻意維持 `needs_review`，必須在實際來源可讀時重新核對。

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
