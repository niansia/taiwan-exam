# Taiwan Exam 一次安裝指引

這份文件主要給 AI 代理讀。目標是讓使用者只需貼一次儲存庫網址，之後直接用自然語言出題；不要把終端機操作轉嫁給不會寫程式的使用者。給一般使用者複製的「網頁版／CLI 版／桌面版」逐平台文字集中放在 [README](README.md#三種使用方式)，本文件只維護安裝、驗證與安全備援細節。

## 目前可安裝的內容

目前使用 GitHub 公開原始碼與網頁版知識檔：

```text
本機 Skill 原始碼：
https://github.com/niansia/taiwan-exam

ChatGPT／Claude／Gemini 網頁知識檔（一鍵下載頁）：
https://niansia.github.io/taiwan-exam/download-web-knowledge.html

知識檔原始文字（檢視／代理取得）：
https://raw.githubusercontent.com/niansia/taiwan-exam/main/web/taiwan-exam-web-knowledge.md
```

給一般使用者時優先提供一鍵下載頁；它會把原始文字存成
`taiwan-exam-web-knowledge.md`，不要求使用者操作 GitHub 的 Raw／Download 按鈕。
可執行 Skill ZIP 仍暫停；純 PDF／圖片的學測來源資料包是另一個發布面，
放在 `source-corpus-2026.09.11` GitHub Release，並由
`exam_packs/學測/source-pack-manifest.json` 驗證。不可把兩者混稱為同一個
ZIP 安全結論。網頁知識檔是純文字、由本儲存庫的正式 Skill 規則機械
彙整；它不包含本機執行程式，也不能把網頁平台缺少的多 GB 來源與逐頁
檢查工具假裝成已存在。

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

在 Codex CLI 或桌面版可用 `$skill-installer` 提出安裝要求；安裝後用 `/skills` 檢查，並以 `$taiwan-exam-generator` 明確叫用。這些名稱應出現在產品自己的技能選單，不得只在聊天中聲稱已安裝。

若內建安裝器不可用，才將經使用者同意取得的本機原始碼副本放到：

- Windows：`%USERPROFILE%\.codex\skills\taiwan-exam-generator\`
- macOS／Linux：`~/.codex/skills/taiwan-exam-generator/`

若設定了自訂 `CODEX_HOME`，以該環境實際的 `skills` 目錄為準。不要猜測其他裝置或 ChatGPT 網頁版會自動同步。

#### Claude Code

安裝完整原始碼資料夾到個人技能位置：

- Windows：`%USERPROFILE%\.claude\skills\taiwan-exam-generator\`
- macOS／Linux：`~/.claude/skills/taiwan-exam-generator/`

若使用者只要單一專案可用，可改放 `<專案>/.claude/skills/taiwan-exam-generator/`。`SKILL.md` 必須正好位於該技能資料夾根目錄；不要只複製一份 Markdown 而遺失支援資源。已存在同名資料夾時不要直接覆寫。

安裝後應能從 Claude Code CLI 或 Desktop 的 `/` 選單找到 `/taiwan-exam-generator`。若沒有出現，先檢查資料夾結構與重新載入，不得用普通對話假裝技能已啟用。

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

### 4. 準備當次科目的來源與執行環境

安裝 Skill 不等於一次安裝所有 PDF／瀏覽器工具。第一次實際出題時，依科目與輸出需求檢查：

- Python 3.10+
- `requirements.txt` 中的 PDF／HTML 依賴
- 可用的 Chrome、Chromium 或 Edge（需要瀏覽器排版時）
- 繁體中文字型與逐頁 PDF／影像檢查能力

代理還必須自行檢查當次科目的來源包，不要要求不會寫程式的使用者操作：

```text
python scripts/bootstrap_exam_sources.py --subject 社會 --verify-only
python scripts/bootstrap_exam_sources.py --subject 社會
```

第一行已通過就不需下載；未通過才執行第二行，再重跑第一行。只下載
當次科目與共用資料，不必每次抓取整個語料庫。既有檔案若雜湊不同，
安裝器會停止而不是覆寫。

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

## 網頁版 ChatGPT／Claude／Gemini

網頁版使用平台自己的持續自訂功能。建立一次後，在後續對話選取同一 Skill／Gem 即可；普通聊天中的一次附件上傳仍不算安裝。

### ChatGPT 網頁版

需要帳號或工作區已提供 Skills。先在 ChatGPT 對話模式輸入 `@skill-creator`；只要原生選單能選到它，就可附上 `taiwan-exam-web-knowledge.md` 建立或更新 `Taiwan Exam Generator`，不必強制切到工作模式。若對話模式找不到 `@skill-creator`，才切換工作模式重試。平台若顯示「安裝」或「儲存」按鈕，使用者仍須完成一次原生確認；Markdown 不能略過平台的永久保存確認。確認後，Skill 應在建立它的同一對話立即套用，不得要求先開新對話；之後的新對話可輸入 `@` 選取同一 Skill，無須重新上傳。完整考卷與兩份 PDF 建議在工作模式執行，但最終以該帳號是否提供檔案建立、程式執行與逐頁檢查能力為準。若工作區沒有 Skills，可把同一檔案加入固定 Project 指示；不得把普通聊天附件聲稱為永久安裝。

知識檔內含 111～115 各科正式試題、答案與評分原則的已驗證大考中心
直連。完整卷命題前，網頁代理應自行開啟當科五年份試題，不要要求
使用者逐份尋找；搜尋摘要不能取代實際 PDF。若介面無法搜尋、讀取
或逐頁查看 PDF，必須保留相應的未驗證狀態。

知識檔也內建七科固定版型元件的可驗證直連。網頁代理必須自行
在出卷時取得當科正式組版 PDF：非數學科 3 份，數學 A／B 4 份。核對
雜湊後以原始位元組當作不可重排的底層；只覆疊四個
可變欄位與正文。不得藉由 OCR、HTML、Word、截圖或改字型重建封面。
平台無法匯入原始 PDF 或合併 PDF 圖層時，不得宣稱已套用固定模板。
永久 Skill 必須保存規則與完整資產索引，包含七科共 30 個逐檔直接下載
網址及其 SHA-256、大小與頁數；只有資料夾網址不合格。安裝時不下載任何
模板 PDF，開始出題後才下載當科元件，
也不得以 `0/30` 判定安裝失敗。完整快取可以加速，但只是選用最佳化。
出卷時先執行內建 `fetch_hosted_template_assets.py`；raw URL 失敗時改走
GitHub Contents API/base64，解碼後驗證。大考中心個別歷史 PDF 逾時時，
使用已綁定來源雜湊的內建 release calibration 並另記 live access 狀態，
不得因此拒絕整卷。網頁版缺少本機 validator 路徑時，執行同等的內建
schema/profile 檢查；缺少 PMingLiU／DFKai 名稱本身也不是拒絕理由。

官方說明：<https://learn.chatgpt.com/docs/skills-and-plugins>、<https://learn.chatgpt.com/docs/build-skills>

### Claude.ai

在 Claude 建立 `Taiwan Exam` Project，把 `taiwan-exam-web-knowledge.md` 加入 Project Knowledge，並把下面的一次性文字存成 Project Instructions。該知識會在 Project 內的各聊天沿用。待通過安全驗收的新 ZIP 發布後，才可改走 `Customize > Skills > Upload a skill`；不要使用已撤回的 ZIP。PDF 產生需要 `Code execution and file creation`，若功能關閉必須回報限制。

官方說明：<https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects>、<https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude>

### Gemini 網頁版

進入 `Gems > New Gem`，名稱填 `Taiwan Exam`；在 Instructions 貼上下面的一次性設定文字，並於 `Knowledge > Add files` 加入 `taiwan-exam-web-knowledge.md`，然後儲存。後續從 `My Gems` 選取它再提出考卷需求。該 Markdown 由正式 Skill 與公開規則機械彙整，不是另一套命題器。

官方說明：<https://support.google.com/gemini/answer/15146780>

### 第一次只貼這段

```text
請採用我附上的 Taiwan Exam Skill，完整保留它的規則與支援資源，
並儲存為之後對話可用的 Taiwan Exam Skill／Gem。
建立時保存七科共 30 個逐檔 PDF 直連與驗證資料，不下載 PDF 本體。
開始出卷時才下載並驗證當科正式組版所需的 3 份 PDF（數學為 4 份）。
不要另寫通用出題器，也不要將模板重打或重排。
```

### 以後直接這樣說

```text
請使用 Taiwan Exam，出一份 116 學測社會完整模擬考。
請分開交付題目 PDF 與答案詳解 PDF，依 Skill 完成內容、答案與逐頁版面檢查。
```

所有網頁平台仍須遵守同一交付底線：完整卷必須有分開的題目 PDF 與答案詳解 PDF，並完成可用的驗證與逐頁視覺檢查。若帳號沒有檔案建立、程式執行、合法來源取得或逐頁檢查能力，只能明確回報缺口，不得把貼在聊天中的文字或未檢查 PDF 稱為正式完成。

## 更新與移除

只有在使用者明確要求時更新。更新前先辨識專案自有檔案與使用者加入的私人資料，採可復原方式備份或搬移；不要用破壞性重設覆蓋工作。

移除時只刪除已確認的技能安裝資料夾或使用平台的原生解除安裝功能。不得刪除其他專案、使用者的 `exam_packs` 副本或共享技能目錄。
