# 網頁版更新紀錄

[返回首頁](../README.md) · [下載最新知識檔](https://niansia.github.io/taiwan-exam/download-web-knowledge.html)

以下是修正摘要；目前執行規則以 [SKILL.md](../SKILL.md) 與最新版知識檔為準。
更新 GitHub 不會自動替換帳號內已儲存的附件，請更新原本的 Skill／Project／Gem。

## 2026.09.22.19：數學式、標題、說明框、頁首與字型全部依官方 111～115 排版

維護者要求把前兩版列出的剩餘差距一次修完。逐項量官方 115 各科題本後修正：

- **數學式**（數A、數B）：官方的分數一律上下疊排、根號有覆蓋被開方數的橫線、向量字母上有箭號、線段有上橫線、變數為 Times 斜體。預檢的 PyMuPDF 1.26.0 不支援行內垂直對齊，渲染器改為先在行內保留與式子等大的透明佔位，排版後原地畫上真正的 Times 字形與線條，再移除佔位（文字仍可搜尋）。作者照常寫 `2/3`、`2√2/3`、`π/3`、`√6`；向量與線段寫 `{{vec:AB}}`、`{{seg:BC}}`，契約拒絕「向量AB」與組合符號。單一字母、點名（△ABC、∠BAC）斜體；sin、log、單位與縮寫（CPI、AI）正體；說明框的「2B鉛筆」不斜體。運算符號、括號、希臘字母、選項標號與題號也改用 Times。
- **題號、題幹與選項位置**：題號對齊官方版心左緣（63.8pt），題幹與選項一律從 18pt 後起排（自然 19.5），選項欄距依官方 90／120／150／180pt（五／四／三／兩欄，自然窄 2pt），超出時才平均分欄。1.26.0 忽略所有表格寬度，改以實測寬度加內距定位；1.28 另給半點餘裕，避免分數被擠到下一行。版心左右不再內縮 4pt，下緣收到 786pt（官方頁尾數字上緣約 788pt）。
- **大題標題**：官方為約 13pt、加字距（數學 2.0、國綜 2.15、自然 2.4、國寫／英文／社會 4.56pt）的描邊粗體；改為同樣方式繪製。國寫「一、」「二、」同樣粗體。
- **說明框**：「說明：」後的續行懸掛對齊，並在官方換行的句子前換行（「作答使用筆尖」「選擇（填）題與」「選擇題與「非選擇題作圖部分」」「選擇題使用2B鉛筆」）；國寫說明第一段依官方壓縮為 11.4pt 字距，四行斷點與 115 相同。
- **頁首頁尾**：七科固定模板改為官方 115 樣式：細明體 11pt、數字 Times、「年學測」固定在模板中、灰底楷體簽名提示置中、各科頁尾字級照官方；只填年度三位數、頁碼與總頁數。封面不變。
- **字型**：電腦裡有新細明體與標楷體（官方字型）就直接使用（預檢從系統複製到本次工作目錄，不散布）；雲端沒有這兩套字型，改用數位發展部全字庫正宋體與正楷體（OFL 1.1，重掛於本專案 Release `fonts-tw-sung-1`、`fonts-tw-kai-1`，固定 SHA-256）。正宋體的半形空白為全形寬度，空白一律改用 Times 寬度。七科版型範例 PDF 以雲端字型重出（2026.09.22.19）。

仍有的字型差異只有一項：雲端無法使用新細明體、標楷體與 Times New Roman（授權不允許散布），改用同標準字形的全字庫字型與 Times 的開源同形字 Nimbus Roman。

新 ZIP（SHA-256 `e5096a8269ef20e77661321c9c9be07093b7c79e0df357f74cb7967aaca5448a`，7,020,646 位元組，98 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.19 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.19/taiwan-exam-hosted-2026.09.22.19.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.19) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.18：數A 選項欄位、第壹部分標題與題組體例依官方，已通過的審查鎖定不重看

維護者交來 Claude（MA116A）與 ChatGPT（M116A0923）兩份 116 數A，逐頁與官方 111～115 比對，並由兩個獨立審題者先解題再對詳解：40 題答案全對、無錯鍵；但難度都偏低（官方每卷約 5–7 題難題，Claude 卷 2–3 題、ChatGPT 卷 0 題；選填壓軸與題組都只到課本例題程度），兩卷都沒有矩陣、平面向量或正餘弦定理題，Claude 卷機率統計占 6 題。排版上，兩卷的單選選項都擠成「(1) 6 (2) 8 (3) 9」一行（官方為 90pt 等距五欄）；ChatGPT 卷沒印「第壹部分、選擇（填）題（占85分）」，第 19 題把「（4」留在行尾；兩卷都寫「第 18 至 20 題為題組」、第 19、20 題只標「（4分）」「（8分）」，ChatGPT 多選題問「下列敘述哪些正確」。ChatGPT 交付檔沒有組版戳記、文字層把「1」對成「俳」，是檢查後又被另存過的檔案。

根源與修正：
- 選項擠成一行：預檢下載的 PyMuPDF 1.26.0 忽略所有表格與儲存格寬度（style、屬性、百分比、固定版面、間隔圖都試過）；本機 1.28 會照寬度排，所以本機測試一直通過。渲染器改為在執行中的引擎量每個選項的實際寬度，再用 padding 補到固定欄距，1.26 與 1.28 都排成等距欄；英文、國綜等各科的選項表一併受益。
- 第壹部分沒印：沒有題目的段落標題原本不會輸出；現在會在第一個後續段落前印出，最終檢查也直接讀題本 PDF 文字確認五個官方標題都在。
- 體例：題組標示改為加底線的「18-20 題為題組」（數A、數B、自然；英文維持「第 11 至 15 題為題組」）；存批契約要求多選題「試選出正確的選項。」、禁止「下列敘述哪些正確」「以下何者正確」，分數選填以「。（化為最簡分數）」作結，第 18 題「（單選題，3分）」、第 19、20 題「（非選擇題，N分）」；配分括號在各科都不再斷行。
- 數A 單元覆蓋：依官方 111～115 逐題分類（100 題，含題組），整卷須有指數與對數、多項式、直線與圓、三角、排列組合、機率、數據分析、矩陣、平面向量、空間各至少一題；機率至多 3 題，數據、排列組合、數列、數與式各至多 2 題，任一單元至多 5 題，11A 專屬代碼 6–14 題。
- 難度：第 17 題（選填壓軸）與第 20 題（題組壓軸）的審查難度須為難或極難，官方每卷如此。
- 已通過的審查鎖定：同一題內容與印出像素（或同一組字形、線條、圖）不變時，後續 `proof` 與 `build` 自動沿用先前通過的結果，不再排入人工佇列（`retained_reviews`，全部沿用時回報 `proof-retained`）；只移動圖檔路徑不算內容變更，審查與難度紀錄改以圖檔 SHA-256 比對。ChatGPT 那次第二版把四張圖改成相對路徑，就讓 8 頁、10 個裁圖重看一輪、難度紀錄全部失效。
- 交付：交付檔須與檢查過的位元組相同，不得再用 PDF 程式另存、壓縮或改標題。

未改：官方的分數一律上下疊排、變數用斜體、向量加箭號，本版仍是「2/3」式的斜線分數與正體字母；多選題正確選項數維持 1～5 隨機（維護者決定保留；官方 111～115 每題 1～4 個）。

新 ZIP（SHA-256 `c133dab36dc0050f0f1c7d031747d5366d4701fc41b1e809235b0cc8d38afaf9`，6,883,800 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.18 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.18/taiwan-exam-hosted-2026.09.22.18.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.18) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.17：國寫材料字型改由 PDF 實際字型把關、楷體改用全字庫正楷體、甲乙加框

維護者把 Claude（W116M1）與 ChatGPT（GW0923）兩份 116 國寫交來，和官方 111～115 逐頁比對字型、版面與選材。ChatGPT 那份的兩大題材料嵌入的是 Noto Serif TC（明體），只有說明框是楷體：它把材料放在 `passage` 區塊，而渲染器只替題幹裡的材料套楷體，passage 走另一個閱讀字型，沒傳 `--reading-font` 就退回明體；逐頁檢查看的是畫面，沒讀嵌入字型，所以仍判通過。另外兩份共同的問題：楷體 LXGW WenKai TC 採傳承字形，「為」印成「爲」（Claude 材料「較爲」「改爲」兩處），文字層還把共用字形對到異體碼位（説明、評閲、硏究）；甲、乙標記沒有官方 113、115 的方框；Claude 的問題（一）把「（占」留在行尾、「4分）」掉到下一行；ChatGPT 的問題（一）少了「：」，「（至多4行）」與「（占4分）」之間少了「。」，材料首行也沒縮排。

修正：國寫的 passage 區塊與題幹材料走同一套規則（楷體、首行縮排兩字、來源單獨成段時靠邊界、甲乙標記加 18pt 方框）。最終檢查與 PDF 檢查器新增 `writing-font-role`：直接讀國寫題本的嵌入字型，說明框或材料不是楷體、「請…回答下列問題：」或問題（一）（二）是楷體，都判失敗；官方 112～115 四份都通過（111 的字型沒有名稱）。楷體改用數位發展部全字庫正楷體 TW-Kai（依教育部標準字形，與標楷體同形；OFL 1.1，未修改，重掛於本專案 Release `fonts-tw-kai-1`，固定 SHA-256，36,925,608 位元組），預檢下載逾時放寬到 120 秒；下載失敗時國寫題本無法交付，須上傳楷體 TTF 並以 `--kai-font` 指定。「（占N分）」不再從中斷行（官方 115 會在「（至多／19 行）」中斷，所以只鎖配分）。存批契約新增：問題（一）（二）須印全形「：」，字數限制與配分之間須印「。」。

仍與官方不同、本版未改：標題「非選擇題（共二大題，占50分）」官方是粗體加字距，這裡是一般明體；說明框官方在「說明：」後懸掛縮排；頁首官方用 11pt 明體，這裡是固定模板的 10pt 楷體。數字與英文用 Nimbus Roman（Times 的開源替代），不是 Times New Roman；標楷體、細明體、Times New Roman 都不能隨 ZIP 散布。

新 ZIP（SHA-256 `64ea093abaef8aa6390eb420a344cdd0f633e105d897dda1b969f3691f98e778`，6,878,800 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.17 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.17/taiwan-exam-hosted-2026.09.22.17.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.17) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.16：國寫題號欄與詳解標題依官方、問題（二）可繼承稽核

ChatGPT 出的 116 國寫（GX7Q2M，最終 run 28 分，其中難度／原創／證據驗證 16 分、逐頁視覺檢查 6 分 41 秒含 4 次 proof、3 次 plan、2 次 build 與一次「題號重複」修正）：選材與題目合格（材料 471／415 字、問題（一）80 字 4 分、問題（二）400 字 21 分、「忽然有了重量」為題 25 分），但版面與 Claude 那份相同（明體 11pt、無「請…回答下列問題：」）之外，還多印了「1.」「2.」題號欄，詳解標題成了「(1)」「(2)」「第2題」，題本標題寫「國寫非選擇題」。根源是國寫題目骨架沒有給印刷標籤：骨架現在直接產生 number_display 一、／空字串／二、與詳解標題 一、問題（一）／一、問題（二）／二、，契約拒絕「1.」「2.」與非官方標題「非選擇題（共二大題，占50分）」。

時間面：問題（二）與問題（一）同一題號、共用材料，但原本只有共用 group_stimulus 的題組可以繼承原創性等稽核紀錄，國寫第二筆必須重寫整套；改為同題號子題也可 `inherits_audit_from`。「題號重複」修正與詳解標題重排本版起不再發生。

新 ZIP（SHA-256 `39b261045907c0ec118d237a528664f6e1db984b065868bf99cb98a5d4cecf97`，6,876,074 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.16 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.16/taiwan-exam-hosted-2026.09.22.16.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.16) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.15：國寫版面依官方 111～115 重做：楷體材料、12pt／20pt 行距、問題懸掛縮排、說明全文

使用者交來 Claude 出的 116 國寫（W116A）：難度與選材可，但版面與官方不同。逐頁量官方 111～115 國寫題本：正文 12pt、行距 20pt；說明框與閱讀材料用標楷體（DFKai-SB，數字 Times），材料首行縮排兩字（x 87.9 對邊界 63.9），甲／乙標記獨占一行；「一、」「二、」明體 12.96pt 獨占一行；「請分項回答下列問題：」與問題（一）（二）為明體 12pt 靠邊界，續行懸掛至 135.9pt（六字）；第二大題題目為縮排兩字的段落。該卷材料用明體 11pt、「一、」與首行擠同一行、問題（一）與（二）縮排不一致、兩句「請…回答下列問題：」都沒印、說明只印前半。

修正：預檢新增第二個固定字型下載——LXGW WenKai TC Regular（OFL 1.1，unmodified，重掛於本專案 Release `fonts-lxgw-wenkai-tc-1`，固定 SHA-256），全科說明框與國寫材料改用楷體，下載失敗退回明體；渲染器新增國寫模式（`_writing_stem`）：不印題號欄，「一、」獨占一行，材料段落楷體縮排兩字、甲乙標記不縮排、「請…問題：」靠邊界、問題（一）（二）懸掛六字、第二大題題目縮排兩字；國寫改為 12pt／20pt。plan、build、proof 帶 `--kai-font`（預設讀預檢紀錄），渲染身分含楷體字型摘要。契約新增：說明框須為官方 115 全文；「請分項回答下列問題：」「請回答下列問題：」兩句必印。時間機制：國寫只有兩大題三筆紀錄，存批即檢（印刷契約、來源驗證）與 plan 先算分頁都已涵蓋，這份卷無須重寫。

新 ZIP（SHA-256 `b35ec53a30d26a39461db62041f787c8daf993ddae0c1372c6ec9bda02ad11d3`，6,875,174 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.15 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.15/taiwan-exam-hosted-2026.09.22.15.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.15) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.14：修正國寫兩支檢查互相矛盾（大題數 vs 題目筆數）

hosted Claude 出 116 國寫（W116M1）時在命題前停下：.11 新增的 `validate_writing_layout_contract` 要求第一大題拆成問題（一）（4 分）與問題（二）（21 分）兩筆紀錄，整卷三筆；而舊的 `validate_writing_source_grounding` 第 46 行仍寫 `len(questions) != 2`，三筆就報「當代國寫完整卷必須有兩大題」，兩筆又被前者退件，最終檢查不可能通過。來源驗證改為以題號計大題：同題號的子題合併材料與來源對應（問題（二）不必重複來源紀錄），大題數須恰為 2。新增兩個回歸測試：三筆紀錄同時通過兩支檢查、第三大題仍退件。

同類問題順便清查其他科：社會 .12 的形式區間也是按「紀錄」計數，而 115 剖面把第 44、46、52 題各存成勾選＋說明兩筆，官方形狀本身會被算成第貳部分 30 題、非選 14 題而退件，改為按題號計數（同題號有任一非選紀錄即算非選）；社會主題廣度改為只計該科自己的內容碼（跨科題先列他科代碼不再誤計）；數B 單元對照補上 D-10-1（集合與文氏圖），先列該碼的題目不再被判「不在數B範圍」，本機發布用的課綱驗證單元上限與 hosted 一致改為 5。自然 .11 的區間本來就按題號計、英文混合題 47–50 與 115 剖面（填充 2＋2、多選 4、簡答 2）相符，不用改。

新 ZIP（SHA-256 `8cca22bde4cdb3d5c52aaa7f4eda8a48b06a6d836d95ab9a1e825dca1ffa73d6`，6,871,838 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.14 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.14/taiwan-exam-hosted-2026.09.22.14.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.14) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.13：內建大考中心高中英文參考詞彙表，詞彙題與文意選填用字依官方 111～115 校準

使用者指出英文詞彙題與文意選填的用字大多來自大考中心的[高中英文參考詞彙表](https://www.ceec.edu.tw/SourceUse/ce37/4.pdf)。原本 `validate_english_vocabulary_scope.py` 需要這份 PDF 卻從未放進硬碟，hosted 端因此完全沒有查過單字等級。這版把 PDF 解析成 6,474 個詞條（六級各約 1,080）隨 ZIP 內建，存批時就檢查。

拿官方 111～115 五卷對照詞彙表後發現原規則會把每一年官方卷都退件：五十個詞彙題答案的等級是 1 級 1、2 級 7、3 級 11、4 級 20、5 級 6、6 級 2（113 randomly、115 consumption），另有 supposedly、compulsory 兩個衍生字不在表內；錯項每年有 1～6 個第六級字；第 1～34 題扣掉專有名詞、縮寫、連字號複合詞後表外字 1.9～3.1%、第六級字 2.2～5.4%，閱讀測驗 4.5～7.3%、2.1～4.5%。改為：十題標的詞至少 6 題在 1～4 級、至少 1 題在 5～6 級、第六級與表外衍生字各至多 1 個；文意選填 (A)–(J) 表外字至多 1 個、第四級以上至少 2 個；第 1～34 題表外字上限 5%、第六級上限 7%，每個表外字列出供審閱並可在 lexical_scope 宣告為專有名詞或已註解字；閱讀表外字超過 10% 提示。另補 366 個不規則、比較級、複合代名詞與衍生形的對照，避免 brought、teeth、happiness 這類字被當表外字。

新 ZIP（SHA-256 `b609c59511806027f74a8af1657501e733bbe0483b776656fad255ea5911da5e`，6,870,943 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.13 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.13/taiwan-exam-hosted-2026.09.22.13.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.13) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.12：社會依官方 111～115 校正形式與命題範圍，自然、社會補章節分布規則

使用者問三件事：各科有沒有像國綜那樣把 111～115 的命題章節分析寫進 Skill、國綜那次「跑太久」的修正其他科是否適用、社會要不要照做。答覆與修正如下：

- 社會：抽出五份官方題本逐題讀。第壹部分單選 46/45/35/42/38 題（每題 2 分）、第貳部分 21/21/29/22/27 題、題組 9/8/9/8/11、單選 11/11/19/12/16、非選 10/10/10/10/11、全卷 64～67 題；選擇題一律四選一 (A)–(D)，五年沒有多選。原契約只鎖 115 剖面且不查這些數字，現在 `validate_social_item_design` 對印出兩部分的卷子檢查上述區間、禁止多選與非 A–D 標記。命題範圍逐題分類：歷史 臺灣史 8/9/8/7/10、中國與東亞 5/7/7/6/8、世界史 7/6/10/9/5；地理 技能 6/3/1/3/5、自然 3/4/4/1/3、人口都市 1/4/1/2/1、產業 3/3/4/5/5、區域地緣 2/1/3/4/4、文化 1/2/1/1/1；公民 政治 3～5、法律 4～7、經濟 5～7、社會文化 4～5。契約以 108 學習內容碼的主題字母檢查廣度：歷A–F／G–J／K–O 各至少 2 題、地A ≥1、地B ≥3、地C ≥2、公B ≥4 且公民至少三個主題。
- 自然：把第壹部分 36 題逐題歸章節（表列於 `subject-form-envelopes-111-115.json` 與 current-gsat-chinese-natural-form.md）：每科每年分布在 4～7 章、單一章最多 5 題，細胞／遺傳／演化、運動與力、熱學每年皆有。契約改以內容碼主題字母檢查：每科至少 3 個主題、單一主題不超過 6 題。
- 數B 的單元範圍在 .11 已做；英文與國寫不是章節型科目（英文範圍是詞彙表等級與篇章題型，國寫是材料類型），.11 已依量測校正題型與材料規則。
- 時間問題：國綜那次的修正（存批即檢、稽核紀錄繼承、plan 先算分頁、proof 只抽查、evidence 重算）都在共用模組，七科一體適用；今天再把數A、數B（scope_codes 單元範圍）與國寫（印刷形式）的檢查也提前到存批時，原本這些只在最終檢查或發布時才會發現。剩下最花時間的是自然、社會的 16／10 張答案相關圖與照片門檻，每張圖缺陷仍需一次重畫，`check-figures` 已可在存批後立即檢查。

新 ZIP（SHA-256 `29ee032a88a1d4a479dc757181c12fce0281f065ba55a414aeaf5ea33c037909`，6,830,572 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.22.12 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.12/taiwan-exam-hosted-2026.09.22.12.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.12) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.11：自然、數B、英文、國寫依官方 111～115 逐卷量測校正形式與範圍

使用者要求把國綜、數A 的做法套到剩下四科。從硬碟上的官方 111～115 二十份題本抽出全文逐卷量測（表格存於 `exam_packs/學測/shared-data/subject-form-envelopes-111-115.json`），修正下列與官方不符或只盯 115 一年的規則：

- 自然：契約原本寫死 115 的「24 單選＋12 多選」與第貳部分 6/6/8，但官方 111～115 第壹部分多選為 18、15、19、18、12 題，第貳部分編號至 60、60、56、57、56，單選 6/9/5/3/6、多選 10/5/7/9/6、非選 8/8/8/9/8。改為區間（多選 12～19；末題 56～60；單選 3～9、多選 5～10、非選 8～9），`natural_choice_form_contract` 改記實際數量並與題目核對；第貳部分須恰六個題組、每組 3～6 題且至少一題非選；應選項數只能是 2 或 3（官方五年約百題多選無一題應選 4 項）。九題一科的學科區塊經逐題核對五年皆成立，保留。
- 數B：逐題分類五卷單元：矩陣、球面／空間、多項式、直線與圓、三角、指對數、排列組合、機率、數據每年至少各 1 題；數列 ≤2、排列組合 ≤2、機率 ≤3、單一單元最多 5 題（115 直線與圓）；帶 11B 專屬代碼者 6～8 題。原本只在本機發布檢查的課綱驗證從未在 hosted 執行，現在 `validate_math_layout_contract` 在存批與最終檢查讀 `item_spec.scope_codes` 直接套用上述範圍，缺代碼或用到 11A 代碼即退件；題目骨架新增 `scope_codes` 欄位。難度決策數的「章節首兩題可為 2 步」原本沿用數A 的 1、2、7、8、18，數B 改為 1、2、8、9、18。
- 英文：新增量測規則——詞彙題幹 13～24 字（允許 12～26）；篇章結構候選句 111～114 為四句、115 五句；閱讀測驗每年 2～4 題字詞／指涉題、至少 1 題全文題、細節核對題最多 4 題；混合題五年皆為填充／簡答 4 分＋多選 4 分＋簡答 2 分且無單選；中譯英每句 18～28 字（允許 16～32）；作文五年皆看圖寫作，提示 108～174 字（上限 220）且須附圖。
- 國寫：原本存批時沒有任何形式檢查。新增 `validate_writing_layout_contract`：兩大題；問題（一）「文長限80字以內（至多4行）」（占4分）並依據上文；問題（二）「文長限400字以內（至多19行）」（占21分）；第二大題（占25分）「請以「題目」為題」且為情意寫作；第一大題材料 331～606 字、第二大題 226～443 字（允許 280～700、180～520）；至少一篇材料印出（改寫自 作者《書名》）；材料不得為文言或自擬。
- 前置說明（`authoring_requirements`）對數A、數B、國寫新增條目，自然與英文補上上述區間。

新 ZIP（SHA-256 `21b5e39967c4a53a5aa41d0fcea5774ad44ff71c78a8e22a94b6a97a67eb1c15`，6,824,882 位元組，97 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.22.11 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.11/taiwan-exam-hosted-2026.09.22.11.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.11) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.10：國綜第貳部分材料須白話框架文搭配文言案例

逐年查官方 111～115 第貳部分：每年都是一篇白話論述或評論文本統攝文言／韻文案例（113 為回憶文學論述、記憶科普配琦君〈髻〉與李煜詞；115 為歸有光自述框架、柯慶明評論配〈出師表〉、〈陳損益表〉）。使用者的 116 卷第貳部分是〈師說〉、〈學記〉、《顏氏家訓》三篇全文言，變成純文言閱讀。契約新增 `part_two_material_errors`：甲乙丙（丁）須分別標示，至少一篇文言或韻文，至少一篇 60 字以上的白話文本；純文言或純白話皆退件。另依使用者判斷，「最長選項即答案」只是巧合，不加規則。文言偵測補上古典韻文（短句、無白話助詞），官方偵測值改為 111 18、112 12、113 12、114 8、115 13，下限由 10 改為 15、目標 16～18。

新 ZIP（SHA-256 `3b4aee6feaaca1ff561662d7d05c54210b81ce8e5e65496f1da051764cbda508`，6,811,006 位元組，96 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.10 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.10/taiwan-exam-hosted-2026.09.22.10.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.10) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.9：密度門檻寫死並三處共用、分頁平均、字型全科寫死明體＋Times、國綜材料種類與文言下限

使用者提早結束的 116 國綜卷卡在「plan 綠燈、build 紅燈、finalize 再紅燈」：`plan` 用 0.28 且放過末頁、inspector 用 0.32 且不放過末頁、最終檢查改用校準值（官方最大留白＋0.10，國綜約 0.23），三處互不一致。逐頁量官方 111～115：中間頁留白國綜 ≤ 0.13、社會 ≤ 0.26、自然 ≤ 0.22、數A ≤ 0.26、英文 ≤ 0.40（節與節換頁），末頁 0～0.69。新增 `scripts/hosted_density.py` 作唯一規則：中間頁 0.32（英文 0.42）、末頁 0.60、封面與公式頁不量；plan、inspector、build 審閱準備與最終檢查全部改用，官方頁面量測只留作參考，任何處置、參考 PDF 或文字說明都不能豁免。渲染器分頁改為兩段：貪心排完後若有頁超限，用同樣頁數平均重排並取超限頁最少、最大留白最小的一版。

字型依使用者要求七科（國綜、國寫、英文、數A、數B、社會、自然）一律寫死：CJK 一律用預檢下載的明體風格 Noto Serif TC（下載失敗才用模型提供的字型，最後才是內建無襯線），數字、拉丁字母與 √ 一律用 Times 系拉丁字型（官方五科皆如此，量測 115 各科）。

國綜逐題比對該卷：九個題組有六組取自著作權法第 65 條、標點符號手冊、台語辭典用字原則、區公所調解說明、徵文辦法（官方每卷最多一組），研判題用 ➀➁ dingbat 且選項寫成「皆與文中資訊相符」，第 1 題仍是一字多音，填詞題自撰；文言／古典材料題以字統計偵測（含韻文）為 14 題（官方 111 18、112 12、113 12、114 8、115 13）。契約新增：法規、手冊、辭典、公告類材料每卷最多 1 組；第 1～31 題文言／古典材料題下限 15、目標 16～18（依使用者要求高於 112～115，已揭露）；禁止 ➀➁ 圈號。

新 ZIP（SHA-256 `3269a1c39443fe832eef61ef506091b5da3ab56b13c76f2a13591f9e3a0f3be5`，6,809,478 位元組，96 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.22.9 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.9/taiwan-exam-hosted-2026.09.22.9.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.9) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.8：數A 印刷形式與題幹修辭契約、根號改用拉丁字型、存批時擋住五類重工

使用者以 ChatGPT（1 小時 12 分）與 Claude（82 分）各出一份 116 數A，並附兩份計時。逐題對照官方 111～115 數A：兩卷結構（20 題、單選 6／多選 6／選填 5／混合 3、配分）都對，問題在形式與敘述。ChatGPT 卷題幹寫出解法（「先利用對數律合併左式，再依 x 的正負限制選取可行值」、「判斷時應同時利用代數分解…」）、混合題印出「下列數值與流程為本題的模擬資料，並非報告所列的實際稽核作法」、沒有「第壹部分、選擇（填）題（占85分）」等標題、正文是內建無襯線字型。Claude 卷題幹過長（單題最長 230 字，官方中位數 83～123、上限 340），三題共用「物價指數年增率」情境，全卷 9 頁對官方 8 頁。兩卷都把 √ 用 CJK 字型印成全形，「√5」中間留空。

修正：新增 `scripts/validate_math_layout_contract.py`（官方五個標題逐字、五個選項 (1)–(5)、題幹不得寫解法指示、不得印模擬資料等聲明、選擇（填）題題幹 ≤ 340 字且中位數 ≤ 150、同一現實情境不得出現於三題以上），hosted 存批與最終檢查都執行，官方十份卷 0 誤判；渲染器對數學科自動把數字、拉丁字母與 √ 改用拉丁字型（官方為 Times 系），`{{answer}}` 等符記不受影響。依 Claude 自己列的五項重工：`append_items` 現在拒收缺選項的選擇題（數學須恰五個）、拒收 `y_{i+1}`／`a^{2}` 等 LaTeX 上下標、拒收高於正文 60% 的圖（要求先縮）、回報與 `paper-plan.json` 規劃位置不同的答案（`answer_position_drift`）；`plan` 回報 `page_budget`（數A 官方 6 頁正文，僅提示不擋）。難度方面：數學難度驗證器新增「至少兩個錯誤選項必須恰為所列誤解路徑的預測結果」，讀一眼就能排除的選項不再過關。

新 ZIP（SHA-256 `13deee72dca12d83391ef42683493e4c906fd580da755cd0944b07a6d63dc399`，6,803,344 位元組，95 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.8 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.8/taiwan-exam-hosted-2026.09.22.8.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.8) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.7：退件提前到存批、題組共用稽核紀錄、CLI 一致

使用者的 Claude 出題跑了 3.1 小時後中斷，模型自己讀 `generation-timing.json` 的結論：Skill 工具只跑了 78 秒，其餘都是「太晚才退件」造成的重工——30 題寫完才被來源綁定退件（52 分鐘重綁全部材料）、40 題全缺 curriculum_codes 到卷級才發現、第 32 題子題標籤撞到 specs 才知道官方是 (1)＋(2)①②、每題 3 個候選草圖＋8 組稽核欄位共約 1,600 欄、以及第 32 題問「乙、丙二文的『久』」而丙文根本沒有「久」字。

修正：(1) 預檢回傳 `authoring_requirements`，把每題必備欄位與該科形式規則在第一批之前列出；(2) `append_items.py` 存批時逐題執行來源綁定規則（材料須有 `literacy.source_ids` 與 `source_grounding` verified／proposition_map／material_mode）與「引文須存在於材料」檢查（題幹引自甲乙丙上文的「…」必須是材料印出的文字），有任何訊息即回 `items-saved-fix-before-next-batch` 並要求先 `--replace` 再寫下一批；(3) 同一題組的題目可用 `item_spec.inherits_audit_from` 繼承組長的 originality_record、subject_innovation_audit、literacy、source_grounding（難度設計、課綱代碼、答案仍逐題），約省下三分之二的稽核欄位；(4) `emit_item_skeleton.py` 依官方 slot 直接寫好 (1)、(2)①、(2)② 的 `answer_label`；(5) `difficulty_balance_plan` 與 `paper_difficulty_plan` 兩個名字都被讀取，首批自動放 `mixed_group_originality_records` 空清單；(6) CLI：`check_paper_plan.py --plan`、`hosted_blind_review.py --exam/--output`、`run_hosted_workflow.py specs` 兩個輸出檔有預設名。「」後接全形標點的字距問題是 MuPDF 排版器的行為，這版沒有可調的開關，先不處理。

新 ZIP（SHA-256 `1ca949534749236c4559722e4a7b842b5b5a1b3150237d3aba346b37f8fe3c64`，6,795,985 位元組，94 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.22.7 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.7/taiwan-exam-hosted-2026.09.22.7.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.7) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.6：國綜選項寬度與行距修正、出處與古文排序規則、明體字型自動下載

使用者以 ChatGPT 出的 116 國綜卷（上一版 Skill）版面明顯有誤：每題選項只用到題幹的寬度就換行（右側 40% 空白），選項行距 23 pt、題距 42 pt，全卷 17 頁對官方 12 頁；正文是內建無襯線字型。逐頁量測官方 111～115 後定案：官方選項行距 16～17 pt、題距 19～20 pt、每頁 45～55 行；短選項兩兩並排。

修正：(1) 渲染器不再把選項表格嵌在題幹的表格格子內（ChatGPT 執行環境的 MuPDF 會把巢狀表格縮到題幹寬度），選項改為題幹下方的獨立區塊，單欄用段落、多欄用頂層表格並指定 pt 欄寬；(2) 行距改為按科量測：國綜、國寫、英文 1.5 行、社會與自然 1.6 行，數學維持 1.65，選項格與段落間距同步收緊，題距 4 pt；(3) `inspect_hosted_pdf.py` 新增 `narrow-wrap-column` 硬性失敗：換行的文字行右側留白超過正文四分之一且同列沒有其他文字、表格或圖時退件（同列有第二欄、表格框線、圖片、詩行標點、甲乙丙丁清單皆排除；官方 30 份卷 0 誤判，該卷 17 頁中 10 頁命中），`check_hosted_run.py` 同步檢查；(4) `compose_hosted_pdf.py` 在 PDF 中寫入 creator 戳記，最終檢查沒有戳記即拒收，其他方式排出來的正文交付不了；(5) 預檢在沒有臺灣繁體襯線字型時，先從本專案 Release `fonts-noto-serif-tc-1` 下載固定雜湊的 Noto Serif TC Regular（OFL 1.1），下載不到才用內建無襯線並記錄原因；(6) 國綜契約新增：題組材料須印出處（官方每卷 17～42 處，該卷只有 3 處、六個題組全是自撰說明文）、排序題須為古文（113、115）。另依維護者要求逐題比對難度：該卷 139 個選項有 22% 含絕對化字眼（完全、必然、唯一、所有、只會），70% 的題目至少一個，官方五年為 6～12% 與最多 36%，這些選項不讀文本就能排除；①②研判題被寫成多選成對敘述而非官方「皆符合／①符合，②不符合／無法判斷」單選；字形題每句只有 14～15 字（官方 18～23）；全卷出處與篇名標記 16 處（官方 43～68）；混合題材料印出「甲、丙、丁由編者依題組脈絡撰成」。契約新增這五項退件規則（絕對化選項比例 ≤ 12%、含絕對化選項的題數 ≤ 40%、研判題官方選項形式、字形句 ≥ 16 字、出處標記 ≥ 30、禁止自撰聲明）。七科版型預覽以新渲染器重建為 `layout-examples/2026.09.22.6`（27 頁，其中 8 頁逐頁目視、7 頁封面依固定模板逐位元驗證）。

新 ZIP（SHA-256 `fcd6f5d095d920da76440cf08330ae2ee47d612ffa205a690f22b07830e0e5ae`，6,791,603 位元組，94 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.22.6 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.6/taiwan-exam-hosted-2026.09.22.6.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.6) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.5：國綜第 1 題改為官方的「兩個不同形近字比讀音」，短選項兩兩並排

使用者出 116 國綜卷時發現第 1 題雖然形式漂亮，卻變成同一個字的異讀（「屬」客／桑竹之「屬」、陟罰臧「否」／「否」則）。逐字比對官方 111～115 第 1 題：每年四個選項都是**兩個不同的形近字**（同部件或同聲符）各放在一個四字文言或成語短語裡比讀音：111 痺／髀、忮／庋、攢／鑽、剜／腕；112 笳／袈、鬩／睨、踣／掊、吁／迂；113 闥／撻、篙／蒿、棹／踔、逡／悛；114 舁／臾、啗／諂、迤／弛、畛／殄；115 攲／旖、諳／喑、枇／毗、遏／謁，生僻字是常態，從未出現一字多音。`validate_chinese_layout_contract.py` 現在退掉引號內兩字相同、每邊未各引一字、每邊不在三至六字的第 1 題選項；`chinese-item-type-envelope.json` 與 `references/current-gsat-chinese-natural-form.md` 記下五年的字對。

同一份卷的第 3 題填詞題也離形式：自撰一句白話挖三格，四個選項各用四個互不相干的詞（輕率／全面／草率／徹底），逐格就能排除。官方三題（111 杜甫詩、112〈補江總白猿傳〉、114 聶華苓〈月光•枯井•三腳貓〉；113、115 無此題型）都是摘錄真實作品並印出處，三格各二至四字，每格恰兩個近義候選詞交錯組成四個選項（破海綿／舊報紙、皎潔／青蒼、貪婪／貧血），任兩選項至少兩格不同。契約現在退掉沒有出處、每格候選詞不是兩個、或兩選項只差一格的填詞題；字對與填詞形式都記進 `chinese-item-type-envelope.json`。

同時修正上一版寫錯的版面規則：量遍五年每一行 (A)～(E) 選項，四選項且每項不超過 16 字（含標記 19 字）時官方兩兩並排一行（152 行，第 1 題與短填詞題每年如此），較長選項與所有五選項題才逐項直排。渲染器的 `option_columns` 與版面契約改為此規則（`grid-2` 僅在此長度內接受），2026.09.22.1 的「國綜選項一律逐行」不再適用。

新 ZIP（SHA-256 `6e4bb16b9dc4023c2d5a6f21ed877c428fd032f11cc8822a6969341e2d433b39`，6,786,601 位元組，94 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.22.5 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.5/taiwan-exam-hosted-2026.09.22.5.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.5) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.4：ZIP 檔案數壓到 100 個以下，Claude 上傳恢復

Claude 的 Skill 上傳器對 2026.09.22.3 ZIP 回「Zip contains too many files (maximum 200)」：該版 222 個檔案，2026.09.22.1、2026.09.22.2 也分別為 208、221 個，皆超過 200；ChatGPT 沒有這個限制。因此前兩版更新紀錄裡的「Claude 上傳成功」對應的是上傳器尚未套用此限制或紀錄有誤，以本版為準。

維護者提議把檔案整合。做法是把 ZIP 當成傳輸格式：倉庫原檔不動，`scripts/build_hosted_skill.py` 打包時把所有參考文件（41 個 .md）、schema、版面模板 JSON、exam_packs 資料等文字檔合併成 `resources/bundles/references.json` 與 `resources/bundles/data.json` 兩個成員（`scripts/hosted_bundles.py`，內容為「原路徑 → 原文」，位元組不變）；SKILL.md、LICENSE、NOTICE、AGENTS.md、`references/hosted-execution.md`、47 個 Python 腳本、23 個固定模板 PDF 與 14 個版型預覽仍是獨立檔案。`read_web_knowledge.py --source-dir` 讀取時展開並逐檔核對 PACKAGE_MANIFEST 的雜湊，再還原成原路徑，所以出卷時的參考目錄、各個腳本與階段閱讀視圖完全不變，模型也不必在數十個小檔之間切換；`scan_skill_release.py` 同樣先展開再核對與掃描。建置腳本現在會拒絕超過 200 個成員的 ZIP，並回報 `member_count`。

新 ZIP（SHA-256 `4814bb222cfc78d8fac5d4860efcd528e151fb8fc1bae34174691245e61173c4`，6,781,592 位元組，94 個檔案）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.4 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.4/taiwan-exam-hosted-2026.09.22.4.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.4) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.3：checkpoint 即時回報過期閘門、refresh-evidence 草稿、check-figures 圖片自檢

接續 2026.09.22.2，補上三份模型自我分析提到但上一版只以文件說明的三項：finalize 才發現閘門報告過期（自然卷失敗 5 次）、內容一改九份報告全部作廢得重寫、圖片缺字／標籤壓線／只靠顏色區分要等出完整本 PDF 才用眼睛發現。

新增 `scripts/hosted_evidence_refresh.py`：`checkpoint` 每次回傳 `evidence_ready` 與 `evidence_attention`，用最終檢查器同一套用語列出九個閘門哪些缺、哪些過期（含該次審閱後改了哪幾題）、哪些格式不完整（狀態非 pass、觀察空白、題列缺漏或 pending、盲審包不符）；並寫入 `exam-history.json` 記錄每次存檔的逐題摘要。新子指令 `refresh-evidence --state`：重新登錄機械紀錄，並為每份過期報告寫 `<gate>.draft.json`，未改動題目的列照抄原審閱、改動或新增題目與整卷狀態設 pending、難度盲審包重新產生；審閱者補完 pending 後另存為 `<gate>.json`。檢查器不讀草稿，整份照抄也會因 pending 列被退。新子指令 `check-figures --state`：出 PDF 前打開每張引用圖片，回報檔案遺失或改名、雜湊與存檔紀錄不符、0 位元組、被擋下載後存成圖片名的 HTML、無法開啟、替代字元，以及警告：上下標字元（CJK 字型會印成方框）、帶顏色像素比例、標籤壓在筆劃上、同一內容存成多個路徑。虛線是否看得出、圖例是否對得上仍由 proof 裁切用眼確認。

新 ZIP（SHA-256 `f275dabcaaedf8ee46f38a1ee8add4bf6ace1cf2d511976f88d18c7bf3ec0f6b`，6,854,173 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者確認 Chrome 下載正常並在 ChatGPT 上傳成功，但 Claude 上傳器以「Zip contains too many files (maximum 200)」拒收（222 個檔案），由 2026.09.22.4 修正。[下載 2026.09.22.3 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.3/taiwan-exam-hosted-2026.09.22.3.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.3) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.2：鎖定後才能 build、回合預算、社會圖片與五科時事門檻再提高

使用者以 Claude 出完 116 自然（2 小時 26 分）與社會（2 小時 04 分）模擬卷，並附三份模型自我分析：時間主要耗在重複的 proof／plan／build（自然 24 次 plan、11 次 build、18 次 proof；社會 20 次 proof、7 次 plan、3 次 build；國綜 9 次 plan、6 輪 proof），且都在鎖定內容前就 build，一改題目整本作廢；社會卷圖片題把「最少 2 張照片」當成剛好 2 張；近一年、近幾個月的時事仍偏少；5 題詳解引用改序前的選項編號；finalize 因過期閘門報告失敗 5 次；頁尾總頁數一變就讓全部頁面重審；references 提到的 50 個腳本不在 ZIP 內。

這版的修正：`build` 沒有 `content-lock.json` 就拒絕執行，改用 `plan` 看分頁；`plan --compare <上次 plan>` 直接回報每頁底部留白差值與頁數變化；plan／proof／build 每次回傳 `iteration_budget`（預算 3／4／2，超出即提示「改一次圖或拆一次段，不要再憑眼調提示」）；`specs` 拒絕印出重複子題標籤；存題時退掉 U+2060／U+FEFF／U+200B 等隱形字元與題號欄內的全形空格；詳解引用不存在的「選項（X）」即退件；頁面審閱改比對「內文區像素」，頁尾「共 N 頁」變動不再作廢全部頁面審閱。門檻方面：社會圖片題下限由 6 張／3 類／2 張照片提高為 **10 張／4 類／4 張照片**（官方 111～115 每年 8～17 個標示圖，照片 3～7 處），自然為 16 張／3 張照片，並在 hosted 最終檢查執行 `validate_visual_item_contract.py`；社會一年內時事由 3 題提高為 **6 題，其中 2 題在 180 天內**；自然由 4 來源／6 題／1 個 120 天內提高為 **5 來源／8 題／2 個 180 天內**；英文 2 篇近事文章 6 題；國綜 2 個近事題組 4 題。ZIP 補齊 13 個 references 提到但未打包的驗證腳本。`references/hosted-execution.md` 新增強制順序（出題→解題審閱→鎖定→plan ≤3→build ≤2→審閱一次）、渲染器規則（選項表寬度隨題幹、欄數依最長選項、長標籤置於題幹前）與環境陷阱（圖片下載被擋、隱形字元、過期閘門報告）。所有門檻都高於任何一個官方年份，`references/current-form-topicality.md` 的表格已如實揭露。

新 ZIP（SHA-256 `ae0facf30cd19dbc88169edb44e110658afa18ff699ce1c2ddd0e07352e4192f`，6,845,796 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.2 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.2/taiwan-exam-hosted-2026.09.22.2.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.2) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.22.1：hosted 最終檢查改跑五科全部驗證器；英文題本形式目錄

使用者以 ChatGPT 出的 116 英文卷對照 111～115 正式卷後，問題集中在三處：標題與選項標記不是官方形式（缺「第壹部分、選擇題（占62分）」等十個標題，選項印 (1)–(4)，中譯英標籤直排）、篇章太短（綜合測驗 134～150 字對官方 180～231，篇章結構 130 字 3 句對官方 224～303 字 9～16 句，閱讀四篇各 110 字對官方三篇各 291～368 字）、作文提示變成英文段落（官方為中文「說明＋提示」），詳解 46 題共用同一句話。根本原因與上一版自然科相同：hosted 最終檢查器沒有執行各科驗證器。

這版新增 `scripts/hosted_subject_gates.py`，把英文版面契約、英文難度設計、國綜／自然範圍與推理契約、社會設計、國寫來源池、五科閱讀量下限，以及詳解合理性（答案鍵須為印出標記、詳解須提到所選選項、三題以上共用同一段詳解即退件）全部接進 `check_hosted_run.py`；`append_items.py` 每批存題即回報該批題目的訊息。英文版面契約新增十個官方標題與順序、選項標記 A–D、作文提示須含中文「提示／第一段／第二段」且不得以英文開頭、中譯英題號「1.」「2.」；渲染器讓超過三字的任務標籤置於題幹前而非題號欄。該卷的答案鍵也是機械式的（詞彙 1-4-3-2 循環、文意選填 A～J 依序、三篇閱讀全是 3-2-1-4），新增 `scripts/answer_key_patterns.py` 在發布閘門、hosted 檢查器與每批存題時退掉連四同位、循環、選項庫依序、連五題遞增、題組同序列與位置不均的答案鍵，適用所有科目。`references/current-gsat-english-form.md` 新增 111～115 印刷形式目錄（標題、說明行、選項版面、各節字數與句長、作文提示結構）與該卷的逐項對照；詳見 [docs/english-form-audit-2026-09-22.md](english-form-audit-2026-09-22.md)。

同一位使用者的 116 國綜卷問題同類：沒有「第壹部分、選擇題（占76分）」等四個標題，第 1、2 題不是官方每年固定的字音、字形題而是白話題組，第 3～5 題與多選 25～31 全部成組、多選沒有任何語文知識題還印「（應選3項）」，選項 (1)–(5) 擠成兩欄或四欄，頁首「國語文綜合能力測驗」斷成兩行，答案鍵 1-3-2-4 輪替無任何相鄰重複。新增 `scripts/validate_chinese_layout_contract.py`（四個標題、第 1 題字音、第 2 題字形、第 1～5 題與多選各自獨立、多選至少兩題語文知識、不印應選 n 項、選項 A–E 逐行直排、混合題 32～36 一組）；投影固定國綜單欄；答案鍵新增「16 題以上無相鄰重複」規則；版型 HTML 的頁首欄改為依內容自動寬度並禁止換行，重建七科挖空版元件（雜湊隨之更新，`hosted-web-template-assets.json`、模板資源 PDF 與七科版型預覽 `layout-examples/2026.09.22.1` 一併重建；預覽以 Noto Serif TC 排版）。`references/current-gsat-chinese-natural-form.md` 新增國綜印刷形式目錄；詳見 [docs/chinese-form-audit-2026-09-22.md](chinese-form-audit-2026-09-22.md)。

新 ZIP（SHA-256 `418192fc7f04f0567fa28f49a1b381d6ce033eff874b8f7ebba97133953bb1db`，6,797,554 位元組；版型預覽改以字型子集化後體積縮小）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.22.1 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.22.1/taiwan-exam-hosted-2026.09.22.1.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.22.1) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.21.6：純文字題改在頁面圖上審閱，批次放寬到六題

接續 2026.09.21.5，目標是在不增加 token、不漏看任何一題的前提下再壓縮時間。最終 build 時，凡是題目與詳解都只印段落文字（沒有圖、公式圖、上下標、答題格、填空、表格、答題欄）的題目，其裁切改標 `review_via: page`：不列入待審佇列，該頁通過審閱時自動視為通過（觀察文字會註明「在第 N 頁讀過」）；含圖表等的題目仍逐張開 2 px/pt 裁切；proof 曾記錄缺失的題目一律保留裁切。判定由 `scripts/hosted_item_triage.py` 從 exam.json 重算，最終檢查器會再算一次並確認該頁確實通過，審閱紀錄無法自行改標。以 67 題項的自然卷估算，少開約 80 張圖、約 2 萬 token、20–25 分鐘。

同時 `append_items.py` 允許純文字題一批最多六題（含圖題維持四題），減少來回；build／proof 回傳仍只列待審項目。每一頁仍逐頁開圖，每一題仍被完整讀過。

新 ZIP（SHA-256 `7b85a4822dd96190067460634ba321229010b47706ad3b8b5ac5fd51fdee5d0c`，9,319,115 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.21.6 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.6/taiwan-exam-hosted-2026.09.21.6.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.21.6) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.21.5：五科時事門檻改為預設，出卷時間修正

使用者以 Claude 出完 116 自然模擬卷（67 題項、實際工作 189 分）：難度合適，但近一年時事情境為 0、颱風題為 0。逐題普查 111～115 五年正式卷（自然、社會、英文、國綜、國寫）後發現：自然每年 0～5 個可定年近事情境（多為考前 3.5 個月的諾貝爾獎），颱風五年出現四年；社會近事 12%，颱風只在選項帶過、地震全無；英文五年只有兩處近事、作文四年扣當前風潮；國綜每年恰一個近事題組；國寫無可定年事件但四年扣當代風潮。根本原因是 hosted 最終檢查器沒有執行自然科既有的時事驗證，SKILL.md 又把時事寫成「使用者要求時才做」。

這版新增 `references/current-form-topicality.md`、`exam_packs/學測/shared-data/current-form-topicality-envelope.json` 與 `scripts/validate_current_context.py`：自然、英文、國綜、國寫完整卷各有預設近事門檻（自然 ≥ 4 個一年內來源、≥ 6 題、兩部分皆有、其中一個來源在 120 天內，並須有臺灣災害、氣候／能源與臺灣本土情境；英文一篇近事文章加作文扣趨勢；國綜一個近事題組加臺灣錨點；國寫一題扣趨勢），每題須有內部來源紀錄與「刪掉來源後為何不可解」的說明；發布閘門與 hosted 最終檢查器都會執行，存題時回報進度。社會維持原規則，數 A／數 B 不變。

時間面依使用者計時修正：新增 `run_hosted_workflow.py plan`（只跑分頁、不產 PDF 與圖，60 題合成卷 3.6 秒對 build 13.9 秒）；存題時回傳 `proof_recommended`／`proof_optional`（純文字題不必逐批 proof，最終仍逐題逐頁審）、`layout_risks`（過高的圖）、`absolute_claim_options`（含「必定／只／無關」的選項提醒）、`plan_hint`；共用題號的 `subpart_id` 必須以印出序號開頭，杜絕小題倒置；`scripts/normalize_figure_asset.py` 讓同一張圖重畫後雜湊不變；build／proof／plan 回傳暫停提醒。最終逐頁逐題複檢一項未減。詳見 [docs/topicality-and-time-2026-09-21.md](topicality-and-time-2026-09-21.md)。

新 ZIP（SHA-256 `37ee185d065db11e4df8ea772898ca579ccb4db70385b0b25cecf80ead73a325`，9,315,929 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查。[下載 2026.09.21.5 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.5/taiwan-exam-hosted-2026.09.21.5.zip)；security.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.21.5) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.21.4：缺 PyMuPDF 時 Skill 自己下載 wheel

接續 2026.09.21.3：使用者問能不能不用手動上傳。`scripts/ensure_pymupdf.py` 現在依序做三件事：先用磁碟上已有的 wheel（內建、上傳資料夾或 `--wheel`）；沒有就從本專案固定網址的 Release [wheels-pymupdf-1.26.0](https://github.com/niansia/taiwan-exam/releases/tag/wheels-pymupdf-1.26.0) 下載，比對固定的 SHA-256 與大小後才安裝，不符即丟棄；連這個也被網路政策擋掉，才請使用者下載同一個檔案上傳到對話。安裝一律是 `pip install --no-index` 本機檔案，不改代理或政策設定，也不換用其他 PDF 程式庫；上傳檔被改名時會先復原正式檔名再安裝。`--no-download` 可停用下載。等價的一行指令 `python -m pip install "<wheel 網址>"` 也寫在執行路線與 README。

wheel 改放在獨立、固定網址的 Release，之後每個 Skill 版本不必再附一次；README 疑難排解已改為「通常不需動作，被擋時才三步」。ZIP 維持約 9.3 MB。

新 ZIP（SHA-256 `0b2ea6b3fefa9e7dac1de706a6072b0273a54f94b81eb4e11685f1076fa1d8b5`，9,292,170 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.21.4 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.4/taiwan-exam-hosted-2026.09.21.4.zip)；security.json 與 browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.21.4) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.21.3：缺 PyMuPDF 的環境改用上傳 wheel 離線安裝

使用者實跑時，AI 回報執行環境沒有 PyMuPDF，而且組織的網路政策擋掉 pypi，於是 10 個 hosted 工具在預檢第一步就停下（這是正確行為，沒有自畫版面）。PyMuPDF 是編譯過的二進位套件，本來就不在 ZIP 裡。

這版新增 `scripts/ensure_pymupdf.py`：先檢查能不能 `import pymupdf`，不行就用 `pip install --no-index` 從 wheel 檔離線安裝（先裝 site-packages，失敗再裝使用者目錄），完全不連網、不碰代理或政策設定；預檢會自動先跑這一步。wheel（PyMuPDF 1.26.0，cp39-abi3、manylinux x86_64，適用 Linux 容器上的 Python 3.9 以上，無其他相依）不放進 ZIP，改為每個 Release 的獨立附件，ZIP 維持約 9 MB。遇到缺套件時，AI 會請使用者下載該 wheel 上傳到對話，再以 `--wheel` 安裝後從存檔接著做；README 疑難排解有下載連結與三步說明。打包程式保留 `--bundle-wheels` 選項可把 wheel 包進 ZIP，預設關閉。

已在關閉網路的 `python:3.11-slim` 容器實測：解壓 ZIP、以 wheel 檔離線安裝 PyMuPDF、`--source-dir` 讀取、自然科預檢到 `ready-for-authoring`，全程沒有網路。

新 ZIP（SHA-256 `5694fe65cf61805882191acfdcacc3457c9027d2e6112adaa003d50b23e737ab`，9,290,802 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.21.3 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.3/taiwan-exam-hosted-2026.09.21.3.zip)；wheel 附件與 security.json、browser.json 在 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.21.3) 頁面。已安裝的舊 Skill 請重新下載替換。

## 2026.09.21.2：以大考中心〈試題特色〉交叉核對自然、社會、英文

把專案內建的 111～115 量測值，逐項對照大考中心各年〈學科能力測驗試題特色〉（自然、社會、英文）與磁碟上的正式試卷。磁碟上的 PDF 與大考中心目錄網址的檔案雜湊一致（114 自然為更正後定稿：規模 9.0、2011/3/11，不是考當天版本）；`analyze_current_form_literacy.py` 重跑後與內建 envelope 完全相同。

核對相符：自然第壹部分 36 題固定 物理／化學／生物／地科各 9 題成段、第貳部分 6 個題組（111～112 選擇 16 題＋非選 8 題、113～115 選擇 12 題＋非選 8～9 題）；社會五年的兩部分題數與配分（46／45／35／42／38 題單選，第貳部分 9／8／9／8／11 組）、第壹部分題組數（10／10／6／6／5）皆與官方一致；英文題型固定 10／10／10／4／12／4＋中譯英＋作文，官方明言文意選填、篇章結構、閱讀、混合題「皆為 300 字以上長文」、標的詞彙一至五級。難度校準沿用官方逐題 P／D（英文 235 題、自然 248 題、社會 275 題）。

兩處門檻與官方實卷不符，已修正：

- **英文篇章字數區間。** 以驗證器同一套「只算文章正文」規則重量五年正式試卷：篇章結構 224～305、閱讀 291～376、混合題材料 394～473 字。原本的 250／320／460 邊界會退掉 111 篇章結構、111～112 三篇閱讀與 112 混合題材料。改為篇章結構 220～315、閱讀 285～390、混合題 340～480；綜合測驗 175～235 與文意選填 265～325 維持（實測 179～233、269～313）。
- **自然跨科題組下限由 3 改為 2。** 大考中心每年〈試題特色〉表 1 都只列 2 個合科題組（111：37–42、49–54；112：51–54、55–60；113：40–43、50–53；114：40–43、50–54；115：40–43、50–53）。驗證器的判準（刪掉第二科就解不出）就是大考中心標示合科的定義，門檻設 3 會退掉每一份官方卷。維護者較寬的判讀（每年 3～5 組）保留為觀察範圍，資料檔加上 `ceec_declared` 標記與各年〈試題特色〉網址，測試改為綁定官方宣告數。

新 ZIP（SHA-256 `651f626b2965a5a1863e043037b05efcd23d7c40a73482dacdb215cd980c0a6e`，9,286,935 位元組）與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 上傳成功。[下載 2026.09.21.2 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.21.2/taiwan-exam-hosted-2026.09.21.2.zip)；紀錄見 [Release](https://github.com/niansia/taiwan-exam/releases/tag/hosted-2026.09.21.2) 的 security.json 與 browser.json。已安裝的舊 Skill 請重新下載替換。

未改動但值得知道：自然選擇題型鎖定 115 年版（第壹部分 24 單選＋12 多選；111～114 多選約占一半），社會單題分科段落每年題數不同（公民 3～6、歷史 9～13、地理 5～11），命題時仍須以所選年度為準。

## 2026.09.21.1：國寫、國綜、社會、自然、英文的閱讀量與難度下限

使用者實測回報：兩科數學大致可用，但國寫、國綜、社會、自然、英文出現三個問題——難度偏低、常可直接套公式；字數遠少於大考；自然混合題沒有跨科結合。經量測本機 111～115 學測官方試卷後確認這三點都成立，並補上這五科原本缺少的命題前門檻（數學早就有 `math-difficulty-design.md` 與對應驗證，所以兩科數學才通過）。

量測結果（去掉頁首頁尾與簽名欄後的實質字數）：國綜 12 頁 11,926～12,871 字、國寫 3～4 頁 1,528～1,908 字、英文 12 頁 3,321～3,550 英文字、社會 18～20 頁 13,446～15,269 字、自然 19～20 頁 13,517～15,243 字。字數下限另以「題目內容」為基準（不含封面與各部分說明，因為那是版型印的、不在出題紀錄裡）：國綜 10,727～11,794、國寫 1,109～1,460、英文 3,004～3,238 英文字、社會 12,709～14,630、自然 12,573～14,690。更關鍵的是結構：官方大多數題目放在共用材料的**題組**裡，連第壹部分也是——自然第壹部分有 3～6 個題組（涵蓋 6～12 題），社會 5～10 個，國綜 7～9 個。自然第貳部分固定 6 個題組，其中 3～5 個（中位數 4）真正跨 物理／化學／生物／地科。

對照送審的 116 自然模擬卷：實質字數 7,853（官方最低年的 58%）、第壹部分題組 0 個、第貳部分材料中位數 77 字（官方各年 188～365）、六個題組全部低於 120 字、跨科題組 0 個。題目本身沒錯，但短、單科、一步代入。

這次新增 `references/current-form-literacy-load.md` 與 `scripts/validate_literacy_load.py`，在排版**之前**檢查整卷實質字數、題組數量、共用材料長度，以及自然的跨科題組數；所有下限都取在官方最弱年之下，不會誤退任何一份官方卷。

最關鍵的一處是接線：新門檻檔已加入 `scripts/read_web_knowledge.py` 的 `SUBJECT_REFERENCES`，五科的 hosted 每科閱讀計畫才會真的載入它——這正是數學載 `math-difficulty-design.md` 而其他五科什麼都沒載的差別。

既有檢查同步收緊：社會共用材料中位數門檻 120 字約為官方最弱年（203 字）的一半，已改為 170 字，短材料比例上限由 40% 收為 30%；社會逐題推理步驟在標示中／中偏難／難時須有 3 步（原本一律 2 步）。國綜原本沒有任何逐題難度下限，新增 `chinese_reasoning_contract`：必須否定「只考定義／字詞記憶」與「單一線索辨認」，指出須用到的文本證據範圍與材料依賴，並在中以上標示時列出 3 個推理步驟。各科命題參考檔也補上量測數據與下限。

下限是防塌陷用的，不是寫作目標，更不是把字數灌水、放大圖表或加大作答區的理由。程式通過不等於內容通過，仍須人工確認推理鏈、證據橋接與跨科依賴真的印在題目上。848 項測試中 846 項通過、2 項因環境相依（本機 Chromium／Node）略過，沒有失敗。

## 2026.09.20.3：統一各科題本與詳解檔名

所有科目的正式下載檔案統一為 `{考試}_{科目}_{paper_id}_題本.pdf` 與 `{考試}_{科目}_{paper_id}_詳解.pdf`，例如 `學測_數學A_20260920-01_題本.pdf`。同卷兩份檔案共用卷號，續作保持一致，新卷使用新卷號。使用者明確指定檔名時仍以其要求為準；瀏覽器遇到同名下載自行加上的 `(1)` 不由 Skill 控制。

一般 Skill、原生 Skill ZIP、網頁知識檔與實際交付程式同步更新。內部檢查檔案保留原有路徑，最終下載使用已檢查的交付副本。74 項相關測試通過，包含學測／會考各科命名、同卷重跑、PDF 文字與逐頁像素一致性，以及知識檔與打包測試。題目、答案與版面品質規則不變。

新 ZIP 的掃描與瀏覽器檢查分別留有紀錄，不沿用舊版的帳號上傳成功宣告。[下載 2026.09.20.3 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.20.3/taiwan-exam-hosted-2026.09.20.3.zip)。已安裝的舊 Skill 請重新下載替換，GitHub 更新不會自動更換帳號內附件。

## 2026.09.20.2：分開等待時間，減少重複排版與審閱

針對數 A 實跑的長時間與反覆修版，這次保留原有的命題、解題、難度與視覺品質檢查，改善工作流程：

- **計時可以暫停與續接。** 總歷時、估計工作時間、等待與有紀錄的工具時間分開列出；工具事件也會更新活動判定。超過十分鐘未記錄活動的空檔，在下一次操作時標為「推估等待」，不宣稱是精確思考時間。舊紀錄不事後猜測拆分。
- **完整組卷前鎖定內容。** 早期仍做小批樣張，全部題目、答案與難度審查完成後再鎖定。排版時調整配置；題目或圖檔真的需要改動，須記錄原因並更新相關審查。
- **重用量測好的區塊。** 正式放置文字與圖形時不再重跑 HTML 貼合計算；建置會保存實測頁面配置，列出各頁題號、區塊高度、連接條件與底部剩餘空間。
- **排版停滯有逾時保護。** 正文在獨立子程序中執行，單次操作二十秒沒有進展便終止並回報題號與高度，不會縮字、漏題或把失敗 PDF 當成完成。
- **局部修改只重看受影響部分。** 明確續接最新審閱狀態，保留同一份試卷中未變更內容的實際檢查紀錄；最後仍檢查兩份完整試卷。

七科占位樣板的頁數、題目位置與文字比對一致；數 A 兩頁在 144 DPI 比對下逐像素相同。本機單次數 A 正文核心測量為 0.564 秒 → 0.446 秒（約減少 21%），不含子程序啟動、命題、解題或人工視覺檢查，不能外推整卷節省 21%，也不是完整出卷二十分鐘的實測證明。

知識檔與 Skill ZIP 同步更新為 2026.09.20.2。[下載新版 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.20.2/taiwan-exam-hosted-2026.09.20.2.zip)。本版的安全掃描與瀏覽器下載紀錄隨 Release 附件提供；沒有沿用舊版的帳號上傳成功宣告。已安裝的 Skill、Project 或 Gem 仍需重新下載替換，GitHub 更新不會自動改動帳號內的舊附件。

## 2026.09.20.1：把時間花在存下來的題目上

使用者實跑回報：Claude 連續兩輪（約 80 個指令）都還沒把題目存進檔案，ChatGPT 跑了 48 分鐘後用完額度。兩邊都先把整份考卷設計、驗算、畫圖做完才打算存檔，所以每一輪結束時能接續的進度很少。這一版把力氣導回「已經存下來的題目」。

- **先存再往下做。** Skill 入口與執行說明改成：每 2～4 題一批，只畫這批要用的圖，存檔後做這批的排版預覽與審閱，然後才寫下一批。只有 `exam.json` 能跨輪保存，寫在回覆裡的題目不算進度。
- **續做不重讀。** 同一個對話續做時，不再重讀已經讀過的規範。
- **字型集合自動挑繁中字面。** 系統常把 Noto CJK 裝成一個集合檔，PyMuPDF 只讀得到裡面第一個（通常是日文）字面，正文會印成日文字形卻沒有任何警告。預檢現在會自動取出繁體中文字面；若集合裡只有日、韓或簡體字面，會記錄下來，請 AI 在交付時一併說明。
- **向量圖不再模糊。** SVG 圖以前由排版引擎以約 96 dpi 轉成點陣，現在和 PDF 圖一樣以三倍解析度處理，畫面完全相同。
- **圖檔問題存題時就擋下。** 行內公式圖超過一行（18 pt）會壓到上一行，點陣圖解析度不足會印得糊；這兩項現在存題時就列出並要求修正，不必等到逐頁審閱。
- **逐題審閱一次看六張。** 排版預覽的待審圖片改成一次最多六張，同一題的題目與詳解一定在同一批，減少開圖次數。
- README 寫明：完整考卷通常要 2～3 輪，平台跑到單輪上限就會停在存檔點，回覆「繼續」即可接著做。

原生 Skill ZIP 同步發布 2026.09.20.1（約 9.3 MB）。ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 實際上傳成功。已安裝的舊 Skill 請重新下載替換。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.20.1/taiwan-exam-hosted-2026.09.20.1.zip)

## 2026.09.19.4：預檢後不再停下，一路做到交付

使用者以 2026.09.19.3 在 ChatGPT 出數 A：預檢通過，改用內建字型也正常，但 AI 做完預檢就結束回覆，說命題、解題驗證、逐頁檢查與最終檢查都還沒做，也沒有開始命題。推測原因是預檢結果要 AI「告訴使用者正文是黑體」，而在 ChatGPT 裡，AI 一對使用者說話，這一輪就結束了。Skill 說明裡另有「沒完成就說明剩下什麼」「回報進度」等字句，也會讓 AI 提早停下。

- Skill 入口、執行說明與預檢結果都改成：一份考卷是一件連續的工作，從預檢一路做到交付兩份 PDF。不會為了回報預檢、字型、存檔或批次進度而結束回覆；只有需要使用者處理的問題（例如缺模板）才停下。正文用黑體這件事，改在交付時一併告知。
- 平台真的中斷時，已存的進度照舊保留，回覆「繼續」就從中斷處接著做。
- ChatGPT 上傳 Skill 後，可能會在輸入框自動放一段英文（Let's explore … make up a realistic user prompt）。AI 會以使用者自己的出卷需求為準，示範也照正式流程，不會用 LaTeX 另做一份。README 也提醒先刪掉這段文字。
- 省掉重複步驟：原生 Skill 不再把同一份執行說明讀兩次；預檢已自動開始計時，不必另外啟動計時器；各階段怎麼切換計時也寫清楚了。
- 每存一批題目，就列出這批題目在最終檢查前還缺的難度設計欄位，不必等到最後才一次補。這些欄位不印在考卷上，補填不影響已完成的版面審閱。
- 審閱紀錄的觀察可以寫成多行清單，不會再被拒收。
- README 的出卷文字加上「過程中不要停下來回報進度，一路做到交付兩份 PDF」；專案與 Gem 的設定文字也加上「其他情況不要中途停下來回報進度」。

原生 Skill ZIP 同步發布 2026.09.19.4（約 9.3 MB）。ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 實際上傳成功。已安裝的舊 Skill 請重新下載替換。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.19.4/taiwan-exam-hosted-2026.09.19.4.zip)

## 2026.09.19.3：沒有中文字型也能繼續出卷

使用者以 ChatGPT 出數 A 時，AI 找到了內建模板，也依規則沒有重畫，但停在預檢：執行環境沒有繁體中文字型，封面欄位「116學年度學科能力測驗模擬試題」缺字，也沒有權限安裝系統字型套件。

- Skill 本來就需要的 PyMuPDF 內建一套中文字型（Droid Sans Fallback，約 5 萬個字形，涵蓋繁體中文）。預檢沒有指定字型，或指定的字型缺少封面、頁首用字時，會自動改用它，並記錄在 `body_font`；之後的 proof、build 預設沿用同一個字型。
- 內建字型是黑體（無襯線）：正文，以及封面標題、頁首填入的文字都會是黑體，和明體略有不同；封面、頁首頁尾與公式頁的版面仍是原始模板。想要明體效果，可以附上繁體中文明體字型檔（例如 Noto Serif CJK TC）。
- README 新增「AI 說缺少繁體中文字型」的處理方式，舊版 Skill 也能照著貼上文字繼續。

原生 Skill ZIP 同步發布 2026.09.19.3（約 9.3 MB）。ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 實際上傳成功。已安裝的舊 Skill 請重新下載替換。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.19.3/taiwan-exam-hosted-2026.09.19.3.zip)

## 2026.09.19.2：Skill ZIP 內建七科版型，出卷不必再附檔案

原生 Skill ZIP 內建七科的題本與詳解版型（14 份，共約 6.7 MB）。載入時只取出當科的 2 份，AI 需要時才打開。用 Claude 或 ChatGPT Skill 的人，出卷時不必再附任何檔案，開新對話貼上出卷文字即可。

- 每次附上的 PDF 會整份進入對話，之後每一輪都要重新處理。Skill 內附的檔案在打開前不占對話空間（[Claude 官方說明](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)），可以減少每輪的負擔。
- ZIP 內的版型只合併重複字型，14 份的每一頁都和下載頁公開的版型畫面、文字完全相同。ZIP 約 9.3 MB，解壓後約 11.7 MB，低於 Claude 官方列出的 30 MB 上限。
- 用專案或 Gem（知識檔 MD）的人照舊：出卷時附上當科 2 份版型和離線模板資源 PDF。README 的第 2 步改為只給這些人看。

原生 Skill ZIP 同步發布 2026.09.19.2（約 9.3 MB）。ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 實際上傳成功。已安裝的舊 Skill 請重新下載替換。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.19.2/taiwan-exam-hosted-2026.09.19.2.zip)

## 2026.09.19.1：提早抓出排版問題，PDF 從 40 MB 縮到約 1 MB

使用者以 Claude 出一份數 A，成品漂亮，但分三輪完成，交付的兩份 PDF 各約 40 MB。最後一輪主要在修正逐頁審閱才發現的問題：LaTeX 殘留、印出「$」、流程圖超出欄寬、詳解末頁只剩兩行。這些多半可以更早用程式發現。

- 存題時就檢查會印出的文字：LaTeX 指令、當作數學符號的「$」、未配對的上下標標記、未宣告的公式圖與雜湊不符的圖檔，會一次全部列出，修好再存。
- 圖寬超過題號旁的文字欄時，自動以欄寬印出，不再報錯重排。
- 最後一頁只剩一兩行時，自動稍微縮小題間距重排；字級、行距不變。
- 審閱清單改用絕對路徑，每張圖附紀錄鍵值與待填範本，一次寫入審閱結果。
- 組版時字型只嵌入一份；最終檢查通過後，交付版再去掉沒用到的字形，逐頁比對畫面與文字完全相同才採用。以使用者交付的兩份 PDF 實測，從 40.8 MB 縮到約 0.9 MB。

逐頁與逐題審閱、難度與最終檢查全部保留。原生 Skill ZIP 同步發布 2026.09.19.1，ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 實際上傳成功。已安裝的舊 Skill 請重新下載替換。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.19.1/taiwan-exam-hosted-2026.09.19.1.zip) · [分析與測試範圍](hosted-claude-run-2026-09-19.md)

## 2026.09.18.1：Skill ZIP 內建模板，禁止重畫封面

使用者以 ChatGPT 出一份數 A，約 13 分鐘完成，但封面與頁首和版型不同。檢查兩份 PDF，全部由 XeTeX 產生，頁面中沒有任何原始模板內容。也就是說，模型跳過了 Skill 的套版工具與最終檢查，改用 LaTeX 仿照重畫，還自行加上「非官方試題」字樣。這種輸出原本就違反固定模板規則，最終檢查也不會通過。

- 原生 Skill ZIP 內建七科正式組版用的 23 份模板 PDF（約 2.3 MB），前置工具直接離線使用並核對 SHA-256，不再依賴網路。
- Skill 入口、執行指南開頭與工具錯誤訊息都寫明：正式 PDF 只能由內附工具疊在原始模板上產生，並須通過最終檢查；不得用 LaTeX、HTML、Word 或繪圖工具重畫封面、頁首頁尾、劃記範例或公式頁，加註「模擬」也不行。取不到模板時要停下，並請使用者附上離線模板資源 PDF。
- README 的出卷文字明確要求套用原始模板，並回報最終檢查結果。新增「封面跟版型不一樣」的判斷方法與重做文字；用專案或 Gem 的人出卷時，一併附上離線模板資源 PDF。

原生 Skill ZIP 同步發布 2026.09.18.1（約 2.8 MB）。ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常，並在 Claude 與 ChatGPT 實際上傳成功。已安裝的舊 Skill 請重新下載替換。Skill 無法強迫模型呼叫工具；這次修正移除了「取不到模板」這個缺口，並把禁止事項放在最先讀到的位置。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.18.1/taiwan-exam-hosted-2026.09.18.1.zip) · [調查紀錄](hosted-template-bypass-2026-09-18.md)

## 2026.09.17.1：縮短排版修正循環，不減少審閱

使用者實測一份數 A 約 65 分 41 秒，其中排版與修正約 38 分，占 58%；逐頁與逐題共 55 個檢查單位，修正第 3 題圖文配置與第 11 題 T² 上標後需要重新產生並核對。檢查程式後確認四個可改善的原因：題本與詳解版面規格須把題目再手打一次；修一題會讓後面所有逐題審閱失效；正文表格中的 `<sup>` 被排在基線上，T² 印成像 T₂；頁尾留白警示須手動查官方頁面數據。

- 新增 `run_hosted_workflow.py specs`：由已存的 exam.json 直接產生兩本版面規格，文字只來自題目與詳解；特殊版面寫在 hints，不再重打題目。
- 新增 `proof`：每批題目存檔後立刻排出該批題本與詳解裁切，趁題目還在腦中時審閱，先修上標、分數、圖文配置。
- 審閱沿用改為逐題判斷：題目內容未變，且新裁切像素相同，或字形、線條、圖片位置在 0.02 pt 內一致，才沿用先前的實際審閱。有記錄缺失的舊審閱不會被沿用；改過的題目與頁面一律重審。最終兩本 PDF 仍重新產生每頁與每題裁切並逐一檢查。
- 修正正文表格的上標／下標位置，並加入回歸測試。
- 組版結果直接列出待審圖片、依頁分組，並附上同角色官方頁面留白數據；無任何可比頁面可合理化的頁面會先要求重排。`record-review` 寫入審閱者自己的觀察並更新雜湊，不會自動給通過。
- 其他六科也逐一檢查，同類問題一併修正：
  - `specs` 依各科題目格式產生版面：英文空格、斜體、選項庫只印一次、綜合測驗選項列對齊；自然「應選n項」由 `required_selection_count` 產生；社會作答格式表；國寫與國綜的長材料與子題；題組標示。
  - 英文 11–34 題、只印在共用文章或同號題目裡的子題，改由印出它的區塊涵蓋，不必為最終檢查硬造空白區塊。
  - 題幹已寫出配分（含整題合計）時不再重複印分數。
  - H₂O、SO₄²⁻、x⁴ 這類 Unicode 上下標改成正式上下標，避免常見中文字型缺字時混入別的字型。
  - 圖文題保留題號縮排，配分放在圖前；英文題幹與選項使用英文字型。
  - 長篇材料、題幹與詳解可在段落處接續到下一頁，減少國綜、社會、國寫等頁尾大片留白。

本機以合成資料測試：七科版型在重排後未變動的題塊，實際固定模板合成下向量比對全數判定為未變更；句點、小數點、上標、減號、選項標籤、圖片、選填格列數與鄰題侵入等改動全數判定為已變更。七科合成版面均能由 `specs` 產生並完整涵蓋每一題。這些是程式與合成版面測試，不是網頁模型實際出卷時間；平台單輪時限仍不由 Skill 控制。

原生 Skill 工具 ZIP 同步發布 2026.09.17.1，並含 2026.09.15.1 的路徑修正。ZIP 與解壓內容通過 Windows Defender 與 Windows 附件檢查；維護者已確認 Chrome 下載正常、檔案雜湊一致，並在 Claude Skills 實際上傳儲存成功。已安裝的舊 Skill，以及 Project、Gem、知識區裡的舊知識檔，都要重新下載替換。[下載 ZIP](https://github.com/niansia/taiwan-exam/releases/download/hosted-2026.09.17.1/taiwan-exam-hosted-2026.09.17.1.zip) · [調查與測試範圍](hosted-efficiency-2026-09-17.md)

## 2026.09.15.1：修正 Claude ZIP 路徑相容性

使用者實測 2026.09.14.1 在 Claude Skills 被拒收，訊息為「Zip file contains path with invalid characters」。舊版雖能正確解壓、通過防毒且正常下載，封包內仍有中文與全形括號路徑；先前檢查未涵蓋上傳端的字元相容性。

新版 ZIP 的所有檔名與資料夾路徑僅使用英數字、點、底線、連字號與斜線。原始內容不改寫：載入工具依公開對照表驗證雜湊，再把當科資料放回工作目錄的原始路徑。另加入封裝路徑檢查與七科實際載入測試。這是本專案採用的保守相容格式，不宣稱是 Claude 官方公開的完整字元規則。

此版停在草稿、未正式發布，修正已併入 2026.09.17.1 ZIP；請以該版替換舊版，不需自行解壓、改名或編輯內容。下載、防毒、格式檢查與 Claude 儲存／掃描各自是不同驗證；只有帳號內實際儲存成功，才代表安裝完成。[Claude 官方封裝說明](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

## 2026.09.14.1：減少重讀、分批存檔與修正選填位置

- 原生 Skill 改用短入口 ZIP，規則與工具分檔；聚合 MD 保留給專案／Gem 知識。
- 閱讀分段不超過 12,000 字元，JSON 紀錄留在檔案中；已內嵌全文會明確標示，避免截斷重讀。
- 新增題目欄位骨架、命題前計畫檢查，以及每批 2–4 題連同詳解的可恢復存檔；延續原考卷不必重新命題。
- 前置驗證與組版可沿用未變動的結果，兩本 PDF 的組版及待審圖片一次準備。實際審閱仍不可省略。
- 選填欄接在題幹的答案位置，避免三欄排版或圈圈偏離文字；數學正文阻擋「第15題圖：」等製作標籤。公式素材可用在選項、表格、段落及詳解。
- 高風險頁面預備較高解析度圖片，保留全部逐頁與逐題檢查；沒有風險旗標不等於已通過審閱。

使用者提供的紀錄顯示，993.7 秒前置階段中模板處理僅 6.2 秒，主要浪費在讀規則與工具往返。這次修正對準該瓶頸與存檔缺口，不承諾所有平台能在單輪時限內完成。[調查與測試範圍](hosted-workflow-audit-2026-09-14.md)

## 2026.09.13.9：Claude 上傳格式與入口說明

修正知識檔缺少外層 YAML 名稱與描述，造成 Claude 的 `.md` Skill 上傳框拒收的問題；同一檔案仍可作為 Project Knowledge，內嵌原始規則與逐檔驗證保持不變。平台若將檔案改名為 `SKILL.md`，讀取工具仍可使用。

README、安裝與使用說明分開列出 Chat 專案、Customize → Skills、Cowork 與 Word 外掛，並保留可複製的出卷文字。已驗證本機格式與資源抽取；尚未在使用者帳號實際執行 Claude 上傳／安全掃描，不宣稱通過平台驗收或縮短完整出卷時間。

## 2026.09.13.8：按階段讀取，減少重複找工具

前置、命題、排版與驗收分成四份閱讀資料；原始工具與資料仍一次完整解出，驗證輸入不變。跨科來源表只將當科紀錄放入閱讀資料，題目與答案格式提前到命題階段。已附的離線資源直接用於模板前置檢查，版型 PDF 只看排版角色，不重建占位題或排版引擎。

本機數 A 首份閱讀資料約 177 KB；離線模板前置測試約 1.81 秒。這是載入與小型組版測試，不是網頁完整出卷時間，也無法僅憑逾時截圖確定平台中斷原因。[調查與測量範圍](hosted-loading-audit-2026-09-13.md)

## 2026.09.13.7：七科專用版型

- 國綜、英文、數 A、數 B、自然、社會、國寫各有題本與詳解版型，共 14 份示範 PDF。
- 各科分別提供段落、選項、選填、圖表、混合題與評分格式；出卷只載入當科兩份來源。
- 範例僅含占位內容，不得照抄題目、題號、配分或稀疏留白。正式命題與驗收仍須另外完成。
- 補上英文段落內空格、共用選項庫、資料表、相鄰區塊共同換頁，以及中文字距異常檢查。

[查看七科版型](https://niansia.github.io/taiwan-exam/layout-examples/2026.09.13.7/index.html) · [正文元件使用方式](../references/hosted-body-workflow.md)

## 2026.09.13.6：重用排版與預留審閱時間

- 新增可執行正文元件，保留原始固定 PDF；選填欄先保留高度，編號置於圈內。
- 一次整理兩冊整頁圖、逐題裁圖與待審紀錄；只有同卷、同頁／題且像素完全相同，才可沿用先前實際審閱。
- 最初數題先試排，建議約第 17 分鐘進入最終 QA、預留約 8 分鐘；這是工作目標，不保證平台單輪完成。
- 數 A／數 B 加強難度預設：簡單低於 10 分，中偏難加難至少 70 分，其中難至少 30 分。須由實際解法與複核支持，課綱及 80–92 分鐘手算目標維持；這不是官方難度統計。

## 2026.09.13.5：單一工作階段也可複核

有第二個審閱工作階段時優先獨立審查；一般網頁版沒有此工具時，從不附答案與作者難度標籤的題目檔重新解題，再核對答案、捷徑、配分與難度。完成所有檢查後可交付，但須明示「單一工作階段複核，未經第二個審閱者獨立審查」。使用者明確要求獨立審查時，仍須安排實際第二個審閱者。

## 2026.09.13.4：提前排除離線阻塞

命題前先確認當科模板、內附校準與小型組版測試。離線資源只解出當科附件；連線取得模板預設整段最多 45 秒並保留成功部分。最後檢查可使用經核對的內附校準與原卷留白量測，不再臨時要求下載官方原卷。中斷時保存同一份工作與實際計時。

[卡點與驗證範圍](hosted-offline-preflight-2026-09-13.md)

## 2026.09.13.3 與先前修正

- 七科題本與詳解在交付時重新比對原始固定 PDF，數學公式頁保留原始圖層。
- 直接檢查最終 PDF 的碰撞、可讀裁圖與版面區塊；難度依最短解法、前題提示與複核結果判斷，不能只填高難度標籤。
- 完整數 A／數 B 預設 2–4 題取材自命題日前一年內事件或成果，轉為課綱內推理。查證留在內部紀錄，數學題本與一般詳解不列資料來源行或網址。

[固定模板修正](fixed-template-web-regression-2026-09-13.md) · [品質檢查修正](hosted-quality-regression-2026-09-13.md) · [數學近期事件規則](../references/math-current-events-and-sourcing.md)

上述更新由最新知識檔及 GitHub 原始碼提供。已發布的 v0.7.1 ZIP 保持原先通過下載驗證的內容，未包含後續修正。軟體測試通過不代表某份考卷通過內容、難度或逐頁驗收。
