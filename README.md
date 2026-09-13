# Taiwan Exam｜臺灣大型考試命題 Skill

用一般中文提出需求，讓 AI 依科目規則命題、驗算與排版，分開產出「題目 PDF」和「答案詳解 PDF」。

支援學測 **國綜、英文、數 A、數 B、自然、社會、國寫**；另提供會考各科的資料夾與工作流程。專案著重原創命題，不是現成題庫。

**[直接下載網頁版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)** · **[查看七科版型](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.13.7/index.html)** · [安裝指引](INSTALL.md)

## 三種使用方式

| 使用環境 | 開始方式 |
| --- | --- |
| ChatGPT、Claude.ai、Gemini 網頁版 | 下載知識檔，加入可保存指示的 Skill／Project／Gem。 |
| Codex、Claude Code、Gemini CLI | 請代理從本儲存庫安裝完整 Skill。 |
| Codex、Claude Code 桌面版 | 在聊天框提出相同安裝要求，完成後從技能選單叫用。 |

[各平台的複製貼上範例](docs/usage-guide.md) · [安裝、更新與手動備援](INSTALL.md)

### 網頁版

1. [下載知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)，加入平台可保存的 Skill／Project／Gem。
2. 儲存指示：「採用 Taiwan Exam 全部規則；完整考卷分開交付題目與詳解 PDF，完成解題及逐頁版面檢查。」
3. 在同一個 Skill／Project／Gem 中提出出卷需求。

**目前知識檔版本：2026.09.13.7。** 已儲存的舊附件不會隨 GitHub 自動更新，請替換成最新版。

若 AI 無法下載固定模板，可把[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates) 附到出卷對話；只需取用當科附件，不必每次下載全部模板。

### 本機版

在代理聊天框貼上：

```text
請從 https://github.com/niansia/taiwan-exam 安裝 taiwan-exam-generator。
先讀 INSTALL.md，完成驗證；若已有安裝，請保留私人考試資料與自訂模板。
```

也提供 [v0.7.1 安裝 ZIP](https://github.com/niansia/taiwan-exam/releases/download/v0.7.1/taiwan-exam-generator-v0.7.1.zip)（4.34 MB；[發行與掃描紀錄](https://github.com/niansia/taiwan-exam/releases/tag/v0.7.1)）。**此 ZIP 未包含後續修正；最新功能請使用 main 原始碼或新版網頁知識檔。**

## 出卷範例

```text
請依 Taiwan Exam Skill 出一份 116 學測數 A 完整模擬考。
請分開交付題目 PDF 與答案詳解 PDF，完成命題、解題驗證與逐頁版面檢查。
```

替換年份與科目即可；只想出幾題時，請註明「自訂練習」。完整卷應依該科規格處理題型、配分、難度、原創性及固定版面。

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
