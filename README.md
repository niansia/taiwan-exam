# Taiwan Exam｜臺灣大型考試命題 Skill

讓 AI 幫你出一份原創的**學測模擬考**：命題、解題驗算、套用正式考卷版面，最後交給你**題目 PDF** 和**答案詳解 PDF** 兩個檔案。

- **不用會寫程式，也不用註冊 GitHub。** 照下面步驟點選、複製、貼上就好；灰色框裡的文字可以直接複製。
- 支援學測**國綜、英文、數 A、數 B、自然、社會、國寫**七科；另有會考各科的資料夾與工作流程。
- 每次都重新命題，不是現成題庫。

## 新手三步驟

| 步驟 | 要做什麼 | 多久做一次 |
| --- | --- | --- |
| [第 1 步：安裝](#第-1-步安裝) | 依你用的 AI，下載一個檔案並上傳到指定位置 | 只做一次，有新版時再更新 |
| [第 2 步：準備檔案](#第-2-步準備檔案只有專案或-gem-需要) | 只有用專案或 Gem 的人需要：下載當科 2 份版型和離線模板資源 PDF | 用 Skill ZIP 的人跳過 |
| [第 3 步：出卷](#第-3-步出卷) | 開新對話，貼上出卷文字（用專案或 Gem 的人再附上第 2 步的檔案） | 每次出卷 |

出卷途中停下來也沒關係，在同一個對話輸入「繼續完成」就能接著做，見[卡住了怎麼辦？](#卡住了怎麼辦)

## 第 1 步：安裝

找到你用的 AI，只看那一列就好。畫面若是中文，請找意思相同的按鈕。

| 你用的 AI | 下載這個檔案 | 接著看 |
| --- | --- | --- |
| **Claude**（claude.ai） | [Skill ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip) | [Claude](#claude) |
| **ChatGPT**，左側欄有 **Plugins**，裡面有 **Skills** 分頁 | [Skill ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip) | [ChatGPT](#chatgpt) |
| **ChatGPT**，找不到 Skills | [直接下載網頁版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html) | [ChatGPT](#chatgpt) 的「沒有 Skills」 |
| **Gemini** | [直接下載網頁版知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html) | [Gemini](#gemini) |
| Codex、Claude Code、Gemini CLI | 不用下載 | [進階：本機版](#進階本機版) |

- 點連結會直接下載，檔案通常存在電腦的「**下載**」資料夾。
- **ZIP 不要解壓縮**，上傳時直接選整個 ZIP 檔。
- 知識檔 `taiwan-exam-web-knowledge.md` 是一般文字檔，不是程式。

### Claude

1. 下載 [Skill ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip)，不要解壓縮。
2. 開啟 [Claude](https://claude.ai/)，依序點 **Customize → Skills → ＋ → Create skill → Upload a skill**。
3. 選剛下載的 `taiwan-exam-hosted-2026.09.22.19.zip`，按 **Save**。
4. 確認技能清單出現 `taiwan-exam-generator`，而且已開啟。
5. 到 **Settings → Capabilities**，確認 **Code execution and file creation** 已開啟。學校或公司帳號可能由管理員控制。

完成後直接看[第 3 步](#第-3-步出卷)，出卷時不必附任何檔案。一般對話（Chat）和 **Cowork** 都能使用；Claude for Word 外掛尚未驗證，請先不要用。

<details>
<summary>找不到 Skills？改用 Claude 專案</summary>

1. 下載[知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)。
2. 在 Claude 左側點 **Projects**，建立專案，名稱填 `Taiwan Exam`。
3. 在專案的 **Project knowledge** 上傳 `taiwan-exam-web-knowledge.md`。
4. 在 **Project instructions** 貼上下面這段並儲存：

   ```text
   本 Project 一律依 Knowledge 中的 Taiwan Exam Skill 規則出題。
   完整考卷須分開交付題目 PDF 與答案詳解 PDF，完成解題與逐頁版面檢查。
   封面、頁首頁尾與公式頁一律套用原始模板，不可自行重畫；無法套用時先停下來告訴我，其他情況不要中途停下來回報進度。
   ```

以後出卷都在這個專案裡開新對話，並照[第 2 步](#第-2-步準備檔案只有專案或-gem-需要)附上檔案。

</details>

### ChatGPT

**有 Skills 的帳號：直接上傳 ZIP（建議）**

依 [OpenAI 官方說明](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)，Skills 目前開放給 Business、Enterprise、Healthcare、Edu 帳號，工作區管理員也可能關閉上傳。一般 Free、Plus、Pro 帳號請看下面的「沒有 Skills」。

1. 下載 [Skill ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip)，不要解壓縮。
2. 開啟 [ChatGPT](https://chatgpt.com/)，在左側欄點 **Plugins**，再點上方的 **Skills** 分頁。
3. 點 **Create → Upload from your computer**，選剛下載的 ZIP。
4. 等 ChatGPT 掃描完成，技能清單出現 `taiwan-exam-generator` 就完成了。

直接上傳會保留完整的原版技能，不必再用 `@skill-creator` 請 AI 幫你建立。掃描結果若是 **Needs Review**，請看完畫面說明再決定是否使用；若是 **Blocked** 就無法使用，請改用下面的專案方式。

**沒有 Skills 的帳號：建立專案**

1. 下載[知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)。
2. 在 ChatGPT 左側欄點 **Projects**，新增專案，名稱填 `Taiwan Exam`。
3. 在專案裡上傳 `taiwan-exam-web-knowledge.md`。
4. 打開專案的 **Instructions**，貼上下面這段並儲存：

   ```text
   這個專案的所有出卷需求，都依我上傳的 Taiwan Exam 知識檔規則執行。
   完整考卷要完成解題與逐頁版面檢查，分開提供題目 PDF 和答案詳解 PDF。
   封面、頁首頁尾與公式頁一律套用原始模板，不可自行重畫；無法套用時先停下來告訴我，其他情況不要中途停下來回報進度。
   ```

以後出卷都在這個專案裡開新對話，並照[第 2 步](#第-2-步準備檔案只有專案或-gem-需要)附上檔案。

### Gemini

1. 下載[知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)。
2. 開啟 [Gemini](https://gemini.google.com/)，在左側找到 **Gems**，建立新的 Gem，名稱填 `Taiwan Exam`。
3. 在 **Knowledge（知識）** 上傳 `taiwan-exam-web-knowledge.md`。
4. 在 **Instructions（指示）** 貼上下面這段，按 **Save（儲存）**：

   ```text
   採用 Knowledge 中的 Taiwan Exam Skill 全部規則出題。
   完整考卷須分開交付題目 PDF 與答案詳解 PDF，完成解題與逐頁版面檢查。
   封面、頁首頁尾與公式頁一律套用原始模板，不可自行重畫；無法套用時先停下來告訴我，其他情況不要中途停下來回報進度。
   ```

以後出卷都開這個 Gem，並照[第 2 步](#第-2-步準備檔案只有專案或-gem-需要)附上檔案。

## 第 2 步：準備檔案（只有專案或 Gem 需要）

**用 Skill ZIP 的人（Claude、有 Skills 的 ChatGPT）：跳過這一步。** 七科版型和原始模板都已內建在 ZIP 裡，出卷時不必附任何檔案。

**用專案或 Gem（知識檔）的人**，每個科目準備一次：

1. 開啟[七科版型下載頁](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/index.html)，找到要出的科目，分別按「**下載題本版型**」和「**下載詳解版型**」。
2. 下載[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)，七科共用一份。
3. 出卷時把這 3 份檔案一起附上。

版型 PDF 讓 AI 知道這一科正式考卷長什麼樣子，裡面的文字都是占位內容，AI 只參考排版，不會照抄。離線模板資源 PDF 讓 AI 不必連網就能套用原始模板。

## 第 3 步：出卷

1. 開一個新對話：
   - **已上傳 Skill（Claude、ChatGPT）**：直接開新對話，不用附檔案。ChatGPT 可在輸入框打 `@`，選 `taiwan-exam-generator`。
   - ChatGPT 剛上傳完 Skill 時，輸入框可能自動出現一段英文（I just added the … skill. Let's explore …）。先把它刪掉，只留下面的出卷文字，免得 AI 先做一份示範。
   - **用專案或 Gem**：先進入 `Taiwan Exam` 專案或 Gem，再開新對話，按輸入框的「**＋**」或迴紋針，附上[第 2 步](#第-2-步準備檔案只有專案或-gem-需要)的 3 份檔案。
2. 複製下面這段，貼上並送出。把「數 A」換成你要的科目：

   ```text
   請依 Taiwan Exam Skill 出一份 116 學測數 A 完整模擬考。
   封面、頁首頁尾與公式頁必須直接套用原始模板，不可自行重畫或改用 LaTeX 排版。
   版型只供對照，題目、圖形與解答都要重新設計。
   完成解題、逐頁版面檢查與最終檢查，分開交付題目 PDF 與答案詳解 PDF，並告訴我最終檢查結果。
   過程中不要停下來回報進度，一路做到交付兩份 PDF。
   如果無法套用原始模板，請先停下來告訴我缺少什麼，不要交付自己畫的版本。
   ```

3. 等 AI 做完，下載**題目 PDF** 和**答案詳解 PDF**，再對照版型看一下封面（見[卡住了怎麼辦？](#卡住了怎麼辦)第二項）。

- 科目可以填：國綜、英文、數 A、數 B、自然、社會、國寫；年份也可以改。
- 只想出幾題：改成「請出 5 題學測數 A 自訂練習」，通常一輪就好。
- **完整考卷（20 題）通常要 2～3 輪。** 每個平台單輪能跑的時間和指令數都有上限，AI 跑到上限就會停在存檔點；你在同一個對話回覆「繼續」，它會接著做，不會重來。ChatGPT 若有 **Work** 模式，完整考卷建議在 Work 模式出。

## 卡住了怎麼辦？

<details>
<summary>AI 沒給 PDF、說「尚未完成」、中途逾時或停住</summary>

留在**同一個對話**。畫面有 **Continue／繼續** 就按它，沒有就輸入：

```text
繼續完成
```

也可以貼上這段，說得更清楚：

```text
請接續剛才的考卷，完成剩餘的命題、解題、排版與檢查，再交付題目 PDF 和答案詳解 PDF，不要重新開始。
過程中不要停下來回報進度，一路做到交付兩份 PDF。
```

如果 AI 說先前的檔案不見了，再依提示重新附上檔案。

</details>

<details>
<summary>封面、頁首跟版型不一樣，看起來是 AI 自己重畫的</summary>

正確的考卷，封面和每頁頁首會和版型一模一樣（可在[七科版型下載頁](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/index.html)開啟當科版型對照）：字型、作答注意事項、劃記範例、頁首位置都相同，只有年份、考試名稱和頁碼不同。如果明顯不一樣，代表 AI 沒有套用原始模板，只是照著畫，這份不能用。請在同一個對話貼上：

```text
這份 PDF 沒有套用原始模板，是自行重畫的版本，不能使用。
請改用 Taiwan Exam Skill 內附的原始模板與工具重新組版，最後執行最終檢查並告訴我結果。
已寫好的題目可以沿用，但要依 Skill 流程補齊解題驗證與版面檢查。
封面、頁首頁尾與公式頁一律使用原始模板，不可用 LaTeX、HTML 或 Word 重畫。
如果還是無法套用，請說明缺少什麼。
```

用專案或 Gem 的人，再附上[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates) 一起送出。

</details>

<details>
<summary>AI 說無法下載或套用模板</summary>

用 2026.09.18.1 以後的 Skill ZIP，模板已內建；若仍出現這個訊息，先確認技能已換成新版。用專案或 Gem 的人請照下面做：

1. 點[下載離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)。
2. 回到**原本出卷的對話**，上傳 `taiwan-exam-template-resources.pdf`。
3. 貼上下面這段（科目自行替換）：

   ```text
   這是離線模板資源 PDF，請用它處理這份數 A 考卷的固定模板。
   請讀取 PDF 內附的原始模板附件，不要只讀可見首頁；只取用本次科目的檔案。
   依 Taiwan Exam 規則核對後，使用原始 PDF 套版，保留固定封面、頁首尾及公式頁。
   請接續目前這份考卷，修正排版並重新檢查，分開提供題目 PDF 與答案詳解 PDF。
   如果仍無法處理附件或套版，請明確說明缺少哪個功能及已保存的進度。
   ```

這份約 3.5 MB 的 PDF 已內附原始模板，打開只看到說明首頁是正常的，不用自己解出附件。如果 AI 的環境不能讀取附件或合併 PDF，補傳檔案也沒有用，要換到有這些功能的模式或平台。

</details>

<details>
<summary>AI 說缺少繁體中文字型</summary>

有些環境（例如 ChatGPT）沒有繁體中文字型，也不能自己安裝。2026.09.19.3 以後的 Skill 會自動改用內建的中文字型繼續，不會停下來；這個字型是黑體：正文，以及封面標題、頁首填入的文字都會是黑體，和明體略有不同；封面、頁首頁尾與公式頁的版面照樣是原始模板。

如果 AI 還是停下來要字型，在同一個對話貼上：

```text
不用等我提供字型：請改用 PyMuPDF 內建的中文字型繼續。
用 python 把 pymupdf.Font('cjk').buffer 存成字型檔，再用 --font 指向它重新執行預檢；之後的 proof、build 都用同一個字型檔。
其餘規則不變：封面、頁首頁尾與公式頁一律套用原始模板，完成最終檢查後再交付。
```

想要明體效果：下載 [Noto Serif CJK TC 字型檔](https://github.com/notofonts/noto-cjk/raw/main/Serif/OTF/TraditionalChinese/NotoSerifCJKtc-Regular.otf)（約 25 MB），出卷時附上，並請 AI 用它當正文字型。

</details>

<details>
<summary>模板有套用，但題目壓字、選項跑位</summary>

在同一個對話貼上下面這段（用專案或 Gem 的人再附上當科版型 PDF）：

```text
請依 Taiwan Exam Skill 的流程修正目前考卷的題幹、選項、作答欄與圖表排版：改存檔的題目或排版提示，再用內附工具重新組版。
版型只供對照，占位文字不可作為題目，也不要照抄示範的題號、配分或留白。
請保留原始固定模板，重新檢查修正後兩份 PDF 的每一頁，完成最終檢查後再提供下載。
```

</details>

<details>
<summary>AI 說「執行環境缺少 PyMuPDF，且無法安裝」</summary>

那個對話的執行環境沒有 PyMuPDF，又擋掉 pypi。2026.09.21.4 起，Skill 會自己從本專案的 GitHub Release 下載 wheel（以 SHA-256 驗證後離線安裝），通常不需要你做任何事；AI 也可以直接執行 `python -m pip install "https://github.com/niansia/taiwan-exam/releases/download/wheels-pymupdf-1.26.0/pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"`。只有連 github.com 也被擋時，AI 才會請你做三步：

1. 下載 wheel 檔：[pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl](https://github.com/niansia/taiwan-exam/releases/download/wheels-pymupdf-1.26.0/pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl)（PyMuPDF 1.26.0，適用 Linux 容器上的 Python 3.9 以上）。
2. 把這個檔案直接上傳到同一個出卷對話，回「繼續」。
3. AI 會執行 `python scripts/ensure_pymupdf.py --wheel 上傳的檔案`（離線 `pip install`），然後從存檔接著出卷。

仍失敗時，請把它印出的 JSON 貼到[回報問題](https://github.com/niansia/taiwan-exam/issues)。

</details>

<details>
<summary>上傳 ZIP 時出現「Zip contains too many files (maximum 200)」或「Zip file contains path with invalid characters」</summary>

「too many files」是 2026.09.22.1～2026.09.22.3 ZIP 的問題（檔案數超過 Claude 的 200 個上限；2026.09.22.4 起把參考文件與資料合併成兩個 JSON 成員，約 100 個檔案）；「invalid characters」是更舊的 `2026.09.14.1` ZIP 的問題。請重新下載[新版 Skill ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip) 再上傳，不需要自己解壓或修改。看到技能出現在清單中才算安裝完成；若新版仍被拒收，請保留錯誤文字並[回報問題](https://github.com/niansia/taiwan-exam/issues)。

</details>

<details>
<summary>ChatGPT 有 Skills，但沒有 Upload from your computer</summary>

上傳功能可能被工作區管理員關閉。可以在對話輸入框打 `@skill-creator` 並選取它，附上 Skill ZIP，再貼上：

```text
請使用我附上的 Taiwan Exam Skill ZIP 建立 taiwan-exam-generator Skill。
請完整保留 SKILL.md、scripts、references、schemas，不要合併、改寫或另寫一套出題器。
完成後直接在本對話接受出卷需求。
```

依畫面按「儲存」或「安裝」。若也找不到 `@skill-creator`，請改用 [ChatGPT](#chatgpt) 的「沒有 Skills」專案方式。

</details>

<details>
<summary>找不到 Skills、Projects 或 Gems</summary>

各平台依帳號方案開放的功能不同，以你的畫面為準。都找不到時，可以在一般對話附上知識檔、2 份版型 PDF 和[離線模板資源 PDF](https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates)，再貼上出卷文字；但換新對話時要重新上傳。AI 的環境也需要能建立與檢查 PDF，才能交出兩份 PDF。

</details>

<details>
<summary>進階：讓專案或 Gem 的對話直接使用 ZIP 裡的工具</summary>

如果出卷對話能執行 Python、讀寫檔案，可以額外附上 [Skill ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip)，並加上這段：

```text
我已附上 Taiwan Exam 網頁工具 ZIP，請解壓到本次工作目錄，依內附 hosted-execution 流程執行。
直接使用內附的載入、排版與檢查工具，只讀本次科目所需資料，不要重新撰寫整套工具。
題目、圖表與解答仍須原創；若接續先前考卷，請沿用已保存進度。
```

只在對話中解壓不等於永久安裝；已上傳 Skill 的人不必每次再附 ZIP。

</details>

## 更新到新版

**目前版本：知識檔與 Skill ZIP 皆為 2026.09.22.19（ZIP 內建七科模板與版型）；七科版型 2026.09.22.19。** [看更新紀錄](docs/web-updates.md)

GitHub 有新版時，你帳號裡已經放好的檔案**不會自動更新**，要自己換：

- **Claude、ChatGPT 的 Skill**：先停用或移除舊的 `taiwan-exam-generator`，再依[第 1 步](#第-1-步安裝)上傳新版 ZIP。
- **專案或 Gem**：刪掉裡面舊的 `taiwan-exam-web-knowledge.md`，再上傳重新下載的知識檔。
- **版型 PDF**：版本沒變就不用重新下載。

## 進階：本機版

只有已經在用 Codex、Claude Code 或 Gemini CLI 的人才需要看這段；不熟悉終端機請用上面的網頁版。下面的安裝文字是**貼給 AI 執行**的，不用自己到 GitHub 找程式或搬檔案；Gemini CLI 的單行安裝指令另有標示。

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
封面、頁首頁尾與公式頁必須直接套用原始模板，不可自行重畫或改用 LaTeX 排版。
版型只供對照，題目、圖形與解答都要重新設計。
完成解題、逐頁版面檢查與最終檢查，分開交付題目 PDF 與答案詳解 PDF，並告訴我最終檢查結果。
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
請依 Taiwan Exam Skill 出一份 116 學測社會完整模擬考。
封面、頁首頁尾與公式頁必須直接套用原始模板，不可自行重畫或改用 LaTeX 排版。
版型只供對照，題目、圖形與解答都要重新設計。
完成解題、逐頁版面檢查與最終檢查，分開交付題目 PDF 與答案詳解 PDF，並告訴我最終檢查結果。
```

### Gemini CLI

**第一次：** 在一般終端機執行這一行：

```sh
gemini skills install https://github.com/niansia/taiwan-exam
```

**之後出卷：** 進入 Gemini CLI，貼上：

```text
請使用 taiwan-exam-generator，出一份 116 學測數 B 完整模擬考。
封面、頁首頁尾與公式頁必須直接套用原始模板，不可自行重畫或改用 LaTeX 排版。
版型只供對照，題目、圖形與解答都要重新設計。
完成解題、逐頁版面檢查與最終檢查，分開交付題目 PDF 與答案詳解 PDF，並告訴我最終檢查結果。
```

安裝與更新的細節見 [INSTALL.md](INSTALL.md)。也提供 [v0.7.1 安裝 ZIP](https://github.com/niansia/taiwan-exam/releases/download/v0.7.1/taiwan-exam-generator-v0.7.1.zip)，但未包含後續修正；最新功能請使用 main 原始碼或新版網頁知識檔。

## 七科版型與品質

每科都有「題本版型」和「詳解版型」。Skill ZIP 已內建全部版型；用專案或 Gem 的人再到[下載頁](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/index.html)按當科兩個下載按鈕，出卷時一起附給 AI。下表保留直接預覽連結，也可用來對照交付的考卷。

| 科目 | 題本版型 PDF | 詳解版型 PDF |
| --- | --- | --- |
| 國綜 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/chinese-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/chinese-solutions.pdf) |
| 英文 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/english-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/english-solutions.pdf) |
| 數 A | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/math-a-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/math-a-solutions.pdf) |
| 數 B | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/math-b-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/math-b-solutions.pdf) |
| 自然 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/science-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/science-solutions.pdf) |
| 社會 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/social-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/social-solutions.pdf) |
| 國寫 | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/writing-questions.pdf) | [開啟／下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/writing-solutions.pdf) |

- **各科一組題本＋詳解，共 14 份示範 PDF**，涵蓋段落、選項、選填、圖表、混合題與評分格式。
- 範例僅含占位內容，供排版參考；不能照抄題目、題號、配分或留白。出卷只載入當科版型。
- 正式交付須完成解題、難度與最終 PDF 檢查；軟體測試通過不代表考卷驗收通過。

平台須具備檔案建立與 PDF 檢查能力。流程會保存進度、重用已驗證資源，但不能保證在單輪時限內完成；中斷後請接續同一份工作。

[七科版型下載](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.22.19/index.html) · [最新修正與難度設定](docs/web-updates.md)

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
