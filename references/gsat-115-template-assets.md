# 115 學測版型資產

這是一套**只處理版面**的確定性模板，不是題目產生器，也不是可重複抽換題幹的題庫。

## 固定與可變欄位

- 固定：各科封面階層、科目名稱、考試時間、作答方式、計分方式、簽名提示、頁首頁尾位置、數學參考公式。
- 可變：學年度、測驗名稱、目前頁碼、總頁數。封面使用完整測驗名稱；頁首會把「學科能力測驗…」正規化為短稱「學測」，其他自訂名稱則原樣使用。
- 正文題目、材料、選項、圖表及答案不存放在模板中，仍須由當次命題資料提供並通過原有驗收。
- 顯示品牌固定使用 `Taiwan Exam 模擬試題`；115 正式題本只作版型量測依據，不得把模板輸出標成大考中心正式試題。

## 使用方式

網頁版不可假設本儲存庫已掛載。先讀取
`exam_packs/學測/templates/115/hosted-web-template-assets.json`，依當科元件的
`download_url` 取得 PDF 並核對 SHA-256。正式輸出必須將這些 PDF 原始位元組
當作不可重排的底層，只覆疊年份、測驗名稱、頁碼與當次正文。不得將
模板 OCR、重打、轉成 HTML/Word、截圖、重畫或依外觀仿製。平台無法將
原始 PDF 交給檔案工具或無法合併 PDF 圖層時，不得宣稱正式套版；只能
回報缺口，或在使用者同意後交付通用版面草稿。

建立七科挖空版 PDF 資產：

```text
python scripts/render_gsat_template_assets.py --build-all
```

填入一個科目的動態欄位，例如：

```text
python scripts/render_gsat_template_assets.py --subject 社會 --component packet --year 116 --exam-name 學科能力測驗模擬試題 --current-page 1 --total-pages 19 --output output/social-template-preview.pdf
```

可用元件為 `cover`、`inner-odd`、`inner-even`、`formula`、`packet`；`formula` 只適用數學 A、B。`packet` 是檢視與拆頁用的版型封包，不代表正式試卷應只有這幾頁。

## 正式套用順序

1. 選定各科 115 measured layout profile。
2. 用固定封面模板，不讓 LLM 重寫作答注意事項。
3. 依當次正文自然分頁。
4. 得到實際內頁總數後，套用奇偶頁首、頁碼與頁尾。
5. 數學最後一頁載入相應公式版本；數學 B 不得誤用數學 A 的和角公式版本。
6. 重新輸出 PDF，逐頁檢查文字、框線、頁首、頁尾、截斷及異常留白。
