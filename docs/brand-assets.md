# Taiwan Exam 主視覺

主視覺採使用者選定的「日系輕小說／校園番片名」方向，以字形與排版
構成標誌，不放角色插畫。Taiwan 與 Exam 上下交錯排列，深梅色為主，
霧玫瑰色的細長筆畫穿過 x，旁邊保留一個小型勾選符號。
繁體中文「學測模擬考」直接說明台灣考試情境。

英文字形以本機 Cooper Black 的文字輪廓為基礎，採圓潤軟襯線、
較飽滿的字腹與柔和收尾，微調字距並獨立調整 T／E 的高度，保留
原先兩行的大小關係、位置與留白。加入獨立繪製的答題筆畫及勾選圖形；不將既有
字型宣稱為自行創作的字型。字標的中文副標使用細明體輪廓，
分享圖的功能說明使用微軟正黑體 Bold 輪廓。
保留 Taiwan Exam 名稱及原有來源、授權與作者聲明。

相關官方品牌研究見 [brand-research.md](brand-research.md)。

## 檔案與用途

| 檔案 | 用途 |
| --- | --- |
| [wordmark-light.svg](assets/readme/wordmark-light.svg) | README 淺色背景，透明底，920 × 470 |
| [wordmark-dark.svg](assets/readme/wordmark-dark.svg) | README 深色背景，透明底，920 × 470 |
| [social-preview.png](assets/readme/social-preview.png) | 分享預覽圖，1280 × 640，實色背景 |
| [social-preview.svg](assets/readme/social-preview.svg) | 分享預覽圖向量原稿，1280 × 640 |

README 使用 `<picture>` 隨明暗模式切換字標。所有正式 SVG 均由向量
路徑組成，不內嵌點陣圖、不載入外部字型、圖片或程式。讀者不需要
安裝字型，專案也不散布字型檔。

## 分享連結的設定

網站首頁與下載頁已加入 Open Graph 和 Twitter 大圖標記，圖片網址為：
`https://niansia.github.io/taiwan-exam/assets/readme/social-preview.png`。
網站發佈後才會有對外效果；各平台可能保留舊的分享快取。

**GitHub 儲存庫連結的 Social preview 有獨立設定，不會自動讀取 README。**
管理者可到儲存庫 **Settings → Social preview → Edit → Upload an image**，
選擇 `social-preview.png`。日後更新圖片時，也須另行更新此設定。

GitHub 建議 PNG、JPG 或 GIF，1280 × 640，檔案小於 1 MB。
詳見 [GitHub 官方說明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)。

## 修改與重新輸出

設計來源：[build_brand_assets.py](../scripts/build_brand_assets.py)。

```text
python scripts/build_brand_assets.py
```

需要 Python、fontTools、PyMuPDF。預設使用本機 Windows 字型；
其他系統可用 `--latin-font`、`--caption-font`、`--cjk-font` 指定本機字型。
字型更換後應重新檢查字寬、光學間距、中文字形、明暗模式及縮圖。

## 概念探索

使用內建 imagegen 進行片名構圖探索，正式成品則以原生 SVG 重建、
調整間距並去除點陣概念中的光暈。未使用 CLI 或外部 API 金鑰。
最終概念提示詞：

> ONE ORIGINAL TYPOGRAPHIC LOGO, like a beautifully art-directed Japanese slice-of-life school anime / light novel TITLE, for the Taiwanese educational project 'Taiwan Exam'. Exact title text only: 'Taiwan Exam'. Small Traditional Chinese descriptor: '學測模擬考'. User explicitly chose TYPOGRAPHY AND COMPOSITION with ALMOST NO CHARACTER. NO FACES, NO EYES, NO RIBBON, NO ANIMAL, NO MASCOT, NO decorative paper or pencil. Avoid children's cartoons, video-game bubble lettering, heavy outlines, stickers, sparkles, shiny gradients. Sophisticated quietly cute school-romance title art: custom high-contrast Mincho-inspired serif English lettering with rounded terminals, thin graceful details, generous counters, hand-tuned kerning and imaginative baseline relationships. 'Taiwan' delicately set smaller above-left, 'Exam' large as the visual anchor, both words clear and correctly spelled; subtly interlock the two lines while retaining plenty of breathing room. Tiny answer-choice circle with a check as a SINGLE deliberate accent integrated near the x, NOT a separate icon. Traditional Chinese descriptor in 5 well-spaced characters below. Two-color ink palette only: deep plum #392F46 and dusty rose #CC7893, on clean opaque warm-white background #FFFCF8. One fine curved rose answer line can tie the composition together. Overall compact title lockup in 3:2 landscape canvas, high-end Japanese graphic designer craftsmanship, playful but mature, clean restrained true flat vector look, no glow, no 3D, no texture, no dropshadow, no extra text. This is title lettering, not a generic font name typed next to a symbol. Make distinctive, original letterform composition and charming soft rhythm the main visual idea.
