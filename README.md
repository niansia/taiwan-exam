# Taiwan Exam｜臺灣大型考試命題 Skill

用一般中文提出需求，讓 AI 依科目規則命題、驗算與排版，分開產出「題目 PDF」和「答案詳解 PDF」。

支援學測 **國綜、英文、數 A、數 B、自然、社會、國寫**；另提供會考各科的資料夾與工作流程。專案著重原創命題，不是現成題庫。

**[直接下載網頁版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)** · **[查看七科版型](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.13.7/index.html)** · [安裝指引](INSTALL.md)

## 三種使用方式

| 你正在使用 | 看這一段 |
| --- | --- |
| ChatGPT、Claude.ai、Gemini 網頁版 | 下方「網頁版」：下載知識檔，再貼入設定文字。 |
| Codex、Claude Code 桌面版 | 下方對應平台：直接在聊天框貼上安裝要求。 |
| Codex、Claude Code、Gemini CLI | 下方「本機版」：安裝一次，之後叫用技能出卷。 |

## 網頁版

先[下載知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)，再依平台完成以下設定。
**目前版本：2026.09.13.7。** 已儲存的舊附件不會隨 GitHub 自動更新，請替換成最新版。

### ChatGPT 網頁版

**第一次：** 若技能選單能選到 `@skill-creator`，選取它、附上知識檔，再貼上：

```text
請使用我附上的 taiwan-exam-web-knowledge.md 建立「Taiwan Exam Generator」Skill。
請完整保存規則與資源索引，讓本對話立即可用，之後的新對話也能選取。
安裝時先保存資源索引，實際出卷時才取得當科模板。
完成後直接在本對話接受出卷需求。
```

依介面完成儲存。若帳號沒有 Skills，可建立固定 Project，加入知識檔並設定「所有出卷需求都依 Taiwan Exam 規則執行」。

**之後出卷：** 選取 `Taiwan Exam Generator`，或進入同一個 Project，貼上：

```text
請出一份 116 學測數 A 完整模擬考。
依 Taiwan Exam Skill 完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

### Claude.ai 網頁版

**第一次：** 建立 `Taiwan Exam` Project，把知識檔加入 `Project Knowledge`，在 `Project Instructions` 貼上：

```text
本 Project 一律依 Knowledge 中的 Taiwan Exam Skill 規則出題。
完整考卷須分開交付題目 PDF 與答案詳解 PDF，完成解題與逐頁版面檢查。
```

**之後出卷：** 進入同一個 Project，貼上：

```text
請依 Taiwan Exam Skill 出一份 116 學測英文完整模擬考。
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

### Gemini 網頁版

**第一次：** 建立 `Taiwan Exam` Gem，將知識檔加入 `Knowledge`，在 Instructions 貼上：

```text
採用 Knowledge 中的 Taiwan Exam Skill 全部規則出題。
完整考卷須分開交付題目 PDF 與答案詳解 PDF，完成解題與逐頁版面檢查。
```

**之後出卷：** 開啟同一個 Gem，貼上：

```text
請依 Taiwan Exam Skill 出一份 116 學測自然完整模擬考。
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

若 AI 無法下載固定模板，可把[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates) 附到出卷對話；只需取用當科附件。各平台選單與可用工具以帳號實際介面為準。

## 本機版：桌面與 CLI

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
完成解題與逐頁版面檢查，分開交付題目 PDF 與答案詳解 PDF。
```

安裝與更新的細節見 [INSTALL.md](INSTALL.md)。也提供 [v0.7.1 安裝 ZIP](https://github.com/niansia/taiwan-exam/releases/download/v0.7.1/taiwan-exam-generator-v0.7.1.zip)，但未包含後續修正；最新功能請使用 main 原始碼或新版網頁知識檔。

以上範例都可替換年份與科目；只想出幾題時，請註明「自訂練習」。

## 七科版型與品質

- **各科一組題本＋詳解，共 14 份示範 PDF**，涵蓋段落、選項、選填、圖表、混合題與評分格式。
- 範例僅含占位內容，供排版參考；不能照抄題目、題號、配分或留白。出卷只載入當科版型。
- 正式交付須完成解題、難度與最終 PDF 檢查；軟體測試通過不代表考卷驗收通過。

平台須具備檔案建立與 PDF 檢查能力。流程會保存進度、重用已驗證資源，但不能保證在單輪時限內完成；中斷後請接續同一份工作。

[七科版型下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.13.7/index.html) · [最新修正與難度設定](docs/web-updates.md)

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
