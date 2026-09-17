# Taiwan Exam｜臺灣大型考試命題 Skill

用一般中文提出需求，讓 AI 依科目規則命題、驗算與排版，分開產出「題目 PDF」和「答案詳解 PDF」。

**不需要會寫程式，也不用註冊或操作 GitHub。** 如果你平常在瀏覽器和 AI 聊天，依下表選擇自己平台的檔案，再照對應段落操作即可。本頁的文字框都可以直接複製，貼到指定位置。

支援學測 **國綜、英文、數 A、數 B、自然、社會、國寫**；另提供會考各科的資料夾與工作流程。專案著重原創命題，不是現成題庫。

## 先下載哪個檔案？

| 檔案與下載連結 | 什麼時候用？ | 下載後怎麼做？ |
| --- | --- | --- |
| **Claude Skill ZIP：修正版待驗證** | 舊版 ZIP 已知會被 Claude 拒收；新版正在確認實際上傳結果。 | 暫用下方 Claude「聊天專案」方式，下載知識檔 MD。正式開放後會在此提供 ZIP；請勿繼續使用 2026.09.14.1 ZIP 安裝。 |
| **[直接下載網頁版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)** | ChatGPT Project、Gemini Gem，或 Claude 聊天專案的知識區。 | 把 `taiwan-exam-web-knowledge.md` 加入知識區。**Claude 目前請先用聊天專案**；原生 Skills 的新版 ZIP 尚待上傳驗證。 |
| **[下載離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)** | AI 說「無法下載模板」「缺少固定模板」，或產出的封面、頁首沒有套用模板時。 | 把 `taiwan-exam-template-resources.pdf` 上傳到出卷對話，再貼上本頁「無法套用模板」的文字。 |
| **[開啟七科版型 PDF 下載頁](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/index.html)** | 建議每次開始出卷前，先準備當科兩份版型。 | 找到科目，分別按「下載題本版型」與「下載詳解版型」，出卷時一起上傳給 AI。占位內容僅供排版參考。 |

下載連結點開後會開始下載；若沒有反應，按頁面上的下載按鈕。檔案通常會存到電腦的「下載」資料夾。上傳時，在 AI 的對話框或資料區按「＋」、迴紋針或「新增檔案」，選取剛下載的檔案；按鈕名稱以你的介面為準。

## 三種使用方式

| 你正在使用 | 看這一段 |
| --- | --- |
| ChatGPT、Claude 聊天／Cowork、Gemini | 下方對應平台：Claude Skills 用 ZIP，專案／Gem 知識區用 MD。 |
| Codex、Claude Code 桌面版 | 下方對應平台：直接在聊天框貼上安裝要求。 |
| Codex、Claude Code、Gemini CLI | 下方「本機版」：安裝一次，之後叫用技能出卷。 |

## 網頁版

先依下方平台選擇已開放的 ZIP 或[知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)，只需要看自己使用的平台。

**完成設定、準備出卷時：** 開啟[七科版型下載頁](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/index.html)，下載當科「題本版型」和「詳解版型」兩份 PDF，附到出卷對話，再貼上下方對應平台的出卷文字。只需下載當科，無須全部下載。
**知識檔版本：2026.09.17.1；工具 ZIP 版本：2026.09.15.1；七科版型維持 2026.09.14.1。** 已儲存的舊附件不會隨 GitHub 自動更新，請替換成最新版。

**讓 AI 直接使用現成工具：** 如果出卷對話能執行 Python、讀寫檔案，待新版 ZIP 正式開放後，可附上 ZIP 並加上這句：

```text
我已附上 Taiwan Exam 網頁工具 ZIP，請解壓到本次工作目錄，依內附 hosted-execution 流程執行。
直接使用內附的載入、排版與檢查工具，只讀本次科目所需資料，不要重新撰寫整套工具。
題目、圖表與解答仍須原創；若接續先前考卷，請沿用已保存進度。
```

ZIP 已包含可直接使用的工具與分開存放的規則，能減少反覆載入與重建。它不能替平台新增程式執行能力；Claude 已安裝下方原生 Skill 時，不必每次再附 ZIP。

### ChatGPT 網頁版

**第一次：** 開啟 [ChatGPT](https://chatgpt.com/)，在對話輸入框輸入 `@skill-creator`。若選單有出現就點選它，上傳剛下載的工具／Skill ZIP，再貼上：

```text
請使用我附上的 Taiwan Exam 工具／Skill ZIP 建立「Taiwan Exam Generator」Skill。
請保留短版 SKILL.md 入口與分開的 scripts、references、schemas，不要合併成一份巨型技能正文。
請完整保存規則與資源索引，讓本對話立即可用，之後的新對話也能選取。
安裝時先保存資源索引，實際出卷時才取得當科模板。
完成後直接在本對話接受出卷需求。
```

依介面按「儲存」或「安裝」。若找不到 `@skill-creator`，可改在側邊欄建立「專案／Project」，命名為 `Taiwan Exam`，加入知識檔，並在專案指示貼上：

```text
這個專案的所有出卷需求，都依我上傳的 Taiwan Exam 知識檔規則執行。
完整考卷要完成解題與逐頁版面檢查，分開提供題目 PDF 和答案詳解 PDF。
```

**之後出卷：** 選取 `Taiwan Exam Generator`，或進入同一個 Project，貼上：

```text
請出一份 116 學測數 A 完整模擬考。
我已附上當科題本與詳解版型，請參考排版；題目、圖形與解答仍須重新設計。
依 Taiwan Exam Skill 完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

**第一次沒有輸出結果怎麼辦？** 部分使用者可能遇到第一輪尚未提供 PDF，或回覆「尚未完成」。請留在**同一個對話**，再次輸入：

```text
繼續完成
```

也可以說得更明確：「請接續剛才的考卷，完成剩餘的排版修正與檢查，再交付題目 PDF 和答案詳解 PDF，不要重新命題。」若 AI 回報先前檔案已遺失，再依提示重新附上檔案。

### Claude：聊天專案、Skills 與 Cowork

先選擇你要用的入口；**建立聊天專案**與**上傳 Skill**是兩種設定方式，不必都做。

| 你看到的入口 | 本專案怎麼用？ |
| --- | --- |
| **Customize → Skills → Upload a skill（建議）** | 這是安裝技能。上傳新版 **ZIP，不要解壓**，儲存後啟用；不必另建聊天專案。 |
| **聊天／Chat → Projects（專案）** | 找不到 Skills 時，可在專案知識加入 MD，之後在同一專案開聊天出卷；若能執行程式，可在對話另附工具 ZIP。 |
| **輸入框選 Cowork** | 這是執行任務的模式。先啟用 Skill，再附上當科版型並提出出卷需求。它與 Chat 是不同模式，帳號須有 Cowork。 |
| **Claude for Word** | 這是 Microsoft Word 內的外掛；本專案尚未驗證在該外掛中完成固定模板的兩份 PDF。請先用 Chat 或 Cowork。 |

**Skills 上傳（修正版尚待驗證，暫用下方聊天專案）：** 正式開放 ZIP 後，到 `Customize → Skills → ＋ → Create skill → Upload a skill`，直接選取下載的 ZIP，按 `Save` 並啟用。**不要解壓，也不要將 MD 改名為 ZIP。** 這個版本使用短版技能入口與分開的工具／規則檔，不再把約 2.5 MB 的聚合知識檔當作原生 Skill 正文。曾安裝舊 MD 的使用者，請停用舊版本，改用此 ZIP。

**若出現「Zip file contains path with invalid characters」：** 舊版 `2026.09.14.1.zip` 已有此上傳問題，修正版 `2026.09.15.1.zip` 已準備，待實際上傳確認後開放；不需自行修改壓縮檔。能下載不代表已安裝；請確認 Claude 儲存成功、技能出現在清單中再開始出卷。若新版仍被拒收，請保留錯誤文字回報。

到 `Settings → Capabilities` 確認 `Code execution and file creation` 已開啟；組織帳號可能由管理員控制。儲存時 Claude 仍會執行自己的檢查，下載檔驗證不代表你的帳號已完成實際上傳或出卷。

**備用方式，聊天專案：** 開啟 [Claude](https://claude.ai/)，在聊天介面的 `Projects` 建立 `Taiwan Exam` 專案。在「知識／Project Knowledge」上傳[知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)，在「專案指示／Project Instructions」貼上：

```text
本 Project 一律依 Knowledge 中的 Taiwan Exam Skill 規則出題。
完整考卷須分開交付題目 PDF 與答案詳解 PDF，完成解題與逐頁版面檢查。
```

**之後出卷：** 已安裝 Skill 就開 Chat，或在輸入框選 `Cowork` 執行任務；採用聊天專案則進入同一專案。附上當科兩份版型 PDF，再貼上：

```text
請依 Taiwan Exam Skill 出一份 116 學測英文完整模擬考。
我已附上當科題本與詳解版型，請參考排版；題目、圖形與解答仍須重新設計。
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

**第一次沒有輸出結果怎麼辦？** 若尚未提供 PDF、回覆「尚未完成」，或顯示這一輪工具使用已達上限，請留在**同一個對話**，按畫面上的 `Continue／繼續`（若有顯示），或再次輸入：

```text
繼續完成
```

也可以說：「請接續剛才的考卷，完成剩餘的命題、解題、排版與檢查，再交付題目 PDF 和答案詳解 PDF，不要重新開始。」若 AI 回報先前檔案已遺失，再依提示重新附上檔案。

Cowork 是否可用以帳號介面為準；需要讀取電腦上的資料夾時，須保持 Claude Desktop 開啟並連線。不要只因進入 Cowork 就省略品質檢查，也不保證完整卷能在固定分鐘數內完成。

入口與格式參考 [Claude Skills 說明](https://support.claude.com/en/articles/12512180-use-skills-in-claude)、[Skill 格式](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)與 [Cowork 入門](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork)。**Claude Code** 的桌面／CLI 安裝請看下方本機版。

### Gemini 網頁版

**第一次：** 開啟 [Gemini](https://gemini.google.com/)，找到 `Gems`，建立新的 Gem，命名為 `Taiwan Exam`。在「知識／Knowledge」上傳知識檔，在「指示／Instructions」貼上以下文字後儲存：

```text
採用 Knowledge 中的 Taiwan Exam Skill 全部規則出題。
完整考卷須分開交付題目 PDF 與答案詳解 PDF，完成解題與逐頁版面檢查。
```

**之後出卷：** 開啟同一個 Gem，貼上：

```text
請依 Taiwan Exam Skill 出一份 116 學測自然完整模擬考。
我已附上當科題本與詳解版型，請參考排版；題目、圖形與解答仍須重新設計。
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

**第一次沒有輸出結果怎麼辦？** 若第一輪尚未提供 PDF，或回覆「尚未完成」，請留在**同一個對話**，再次輸入：

```text
繼續完成
```

也可以說：「請接續剛才的考卷，完成剩餘的命題、解題、排版與檢查，再交付題目 PDF 和答案詳解 PDF，不要重新開始。」若 AI 回報先前檔案已遺失，再依提示重新附上檔案。

各平台選單與可用工具以帳號實際介面為準。若找不到上述儲存功能，也可以先在普通對話上傳知識檔並貼上出卷需求；之後換新對話時需重新上傳。

## AI 說無法套用模板，怎麼辦？

1. 點[下載離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)。
2. 回到**原本出卷的對話**，上傳下載好的 `taiwan-exam-template-resources.pdf`。
3. 複製下面這段貼給 AI；科目可自行替換：

```text
這是離線模板資源 PDF，請用它處理這份數 A 考卷的固定模板。
請讀取 PDF 內附的原始模板附件，不要只讀可見首頁；只取用本次科目的檔案。
依 Taiwan Exam 規則核對後，使用原始 PDF 套版，保留固定封面、頁首尾及公式頁。
請接續目前這份考卷，修正排版並重新檢查，分開提供題目 PDF 與答案詳解 PDF。
如果仍無法處理附件或套版，請明確說明缺少哪個功能及已保存的進度。
```

這份約 3.5 MB 的 PDF 裡已附上原始模板，你不需要自行解出附件；打開時只看到說明首頁也正常。如果 AI 的環境沒有讀取附件或合併 PDF 的功能，還是需要換到有這些功能的模式或平台，補傳檔案無法新增平台功能。

**如果固定模板已有套用，但題目仍壓字、選項跑位：** 從下方表格下載當科版型，附上有問題的考卷與版型 PDF，再貼上：

```text
請參考我附上的當科版型，修正目前考卷的題幹、選項、作答欄與圖表排版。
版型中的占位文字只供排版參考，不可作為題目，也不要照抄示範的題號、配分或留白。
請保留原始固定模板，重新檢查修正後兩份 PDF 的每一頁，再提供下載。
```

**如果出卷途中逾時：** 回到同一對話，貼上「請接續已保存的這份考卷，先確認尚未完成的檢查，再完成排版與驗收，不要重新命題。」如果 AI 回報原檔已遺失，再把先前下載的檔案重新附上。

## 本機版：桌面與 CLI

只有你已經在使用 Codex、Claude Code 或 Gemini CLI 時，才需要看這一區。`CLI` 是終端機裡的 AI 工具；不熟悉終端機可直接使用上面的網頁版。下面的安裝文字是**貼給 AI 執行**，不用自己到 GitHub 找程式或搬檔案；Gemini CLI 的單行安裝指令另有標示。

### Codex 桌面版／CLI

**第一次：** 在 Codex 聊天框貼上：

```text
$skill-installer
請從 https://github.com/niansia/taiwan-exam 安裝 taiwan-exam-generator 為使用者層級 Skill。
先讀 INSTALL.md 並完成驗證；請保留我的私人考試資料與自訂模板。
```

**之後出卷：** 從技能選單選取，或貼上：

```text
$taiwan-exam-generator
請出一份 116 學測國綜完整模擬考。
我已附上當科題本與詳解版型，請參考排版；題目、圖形與解答仍須重新設計。
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

### Claude Code 桌面版／CLI

**第一次：** 在 Claude Code 聊天框貼上：

```text
請從 https://github.com/niansia/taiwan-exam 取得完整原始碼，先讀 INSTALL.md，
再安裝 taiwan-exam-generator 為使用者層級 Skill 並驗證。
請保留我的私人考試資料與自訂模板。
```

**之後出卷：** 輸入 `/` 選取 `taiwan-exam-generator`，再貼上：

```text
請出一份 116 學測社會完整模擬考。
我已附上當科題本與詳解版型，請參考排版；題目、圖形與解答仍須重新設計。
依 Taiwan Exam Skill 完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

### Gemini CLI

**第一次：** 在一般終端機執行這一行：

```sh
gemini skills install https://github.com/niansia/taiwan-exam
```

**之後出卷：** 進入 Gemini CLI，貼上：

```text
請使用 taiwan-exam-generator，出一份 116 學測數 B 完整模擬考。
我已附上當科題本與詳解版型，請參考排版；題目、圖形與解答仍須重新設計。
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

安裝與更新的細節見 [INSTALL.md](INSTALL.md)。也提供 [v0.7.1 安裝 ZIP](https://github.com/niansia/taiwan-exam/releases/download/v0.7.1/taiwan-exam-generator-v0.7.1.zip)，但未包含後續修正；最新功能請使用 main 原始碼或新版網頁知識檔。

以上範例都可替換年份與科目；只想出幾題時，請註明「自訂練習」。

## 七科版型與品質

每科都有「題本版型」和「詳解版型」。建議先到[下載頁](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/index.html)按當科兩個下載按鈕，出卷時一起附給 AI。下表也保留直接預覽連結；在閱讀器中可按下載圖示儲存。

| 科目 | 題本版型 PDF | 詳解版型 PDF |
| --- | --- | --- |
| 國綜 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/chinese-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/chinese-solutions.pdf) |
| 英文 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/english-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/english-solutions.pdf) |
| 數 A | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/math-a-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/math-a-solutions.pdf) |
| 數 B | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/math-b-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/math-b-solutions.pdf) |
| 自然 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/science-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/science-solutions.pdf) |
| 社會 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/social-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/social-solutions.pdf) |
| 國寫 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/writing-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/writing-solutions.pdf) |

- **各科一組題本＋詳解，共 14 份示範 PDF**，涵蓋段落、選項、選填、圖表、混合題與評分格式。
- 範例僅含占位內容，供排版參考；不能照抄題目、題號、配分或留白。出卷只載入當科版型。
- 正式交付須完成解題、難度與最終 PDF 檢查；軟體測試通過不代表考卷驗收通過。

平台須具備檔案建立與 PDF 檢查能力。流程會保存進度、重用已驗證資源，但不能保證在單輪時限內完成；中斷後請接續同一份工作。

[七科版型下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/index.html) · [最新修正與難度設定](docs/web-updates.md)

## 進一步閱讀

| 文件 | 內容 |
| --- | --- |
| [SKILL.md](SKILL.md) | 命題與交付規則入口 |
| [各平台使用指引](docs/usage-guide.md) | 網頁、CLI、桌面版的操作範例 |
| [網頁版更新紀錄](docs/web-updates.md) | 固定模板、排版、複核與效率修正 |
| [來源資料與維護](docs/sources-and-maintenance.md) | 歷屆資料取得、執行環境、測試與發布 |
| [正文排版元件](references/hosted-body-workflow.md) | 各科可重用版型與審閱流程 |

## 授權

本專案不是大考中心、心測中心、OpenAI、Anthropic 或 Google 的官方產品。

自有程式與文件採 [MIT License](LICENSE)；著作權、來源與改作要求見 [NOTICE](NOTICE)、[ORIGIN.json](ORIGIN.json) 及[改作說明](references/attribution-and-forks.md)。MIT 不替第三方試卷、文章、圖片、資料或字型授權。
