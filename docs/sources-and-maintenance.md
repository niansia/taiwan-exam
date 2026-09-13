# 來源資料與維護

[返回首頁](../README.md)

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
[`source-pack-manifest.json`](../exam_packs/學測/source-pack-manifest.json)。

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

## 維護者與進階使用者

基本環境為 Python 3.10+。PDF 讀取與排版依賴列在 `requirements.txt`；舊式 Excel 統計匯入才需要 `requirements-statistics.txt`。Chrome／Chromium／Edge、繁體中文字型與其他排版工具只在相關工作需要時準備。
Linux 的 HTML 轉 PDF 環境需安裝繁體中文字型；Debian／Ubuntu 使用 `fonts-noto-cjk`，排版器已加入 `Noto Serif CJK TC`。驗證時同時檢查畫面與擷取文字，避免字型替代造成漏字。

```sh
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
python scripts/validate_attribution.py .
```

正式封裝必須通過 [SOFTWARE_RELEASE_STATUS.json](../SOFTWARE_RELEASE_STATUS.json) 與[軟體發布安全流程](../references/software-release-security.md)；不得自行改名、換網址或沿用舊掃描紀錄。原始碼發布與預先封裝安裝檔是兩個不同的發布面。
