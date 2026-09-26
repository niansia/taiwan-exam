# 參與 Taiwan Exam

謝謝你願意幫忙！不會寫程式也能參與：回報問題、分享出卷結果、提出建議，對這個專案都很有幫助。

## 回報問題（Issue）

到 [Issues](https://github.com/niansia/taiwan-exam/issues/new/choose) 選「出卷問題」或「功能建議」，照表單填寫。需要免費的 GitHub 帳號。

回報出卷問題時，請盡量附上：

- 你用的 AI 平台（Claude、ChatGPT、Gemini…）和方式（Skill ZIP、專案、Gem）
- Skill 版本（例如 `2026.09.22.25`，看你下載的 ZIP 檔名）
- 科目與出卷文字
- AI 的錯誤訊息，或有問題那一頁的截圖

請不要上傳大考中心或出版社的完整試卷、個人資料或帳號資訊。

## 提交修改（Pull Request）

1. 先 fork 本倉庫，在自己的分支修改。
2. 改程式請一起更新或新增測試，並在本機執行：

   ```sh
   python -m pip install -r requirements-test.txt
   python -m pytest -q
   ```

3. 發 PR 時照範本說明改了什麼、為什麼改、怎麼驗證。
4. **每個 PR 都由維護者審核後才會合併**；自動測試通過不代表已經同意合併。維護者可能請你修改，或說明為什麼不採用。

修改前請先讀 [AGENTS.md](AGENTS.md)、[NOTICE](NOTICE) 與[改作說明](references/attribution-and-forks.md)：

- 不要加入受著作權保護的試卷、文章、圖片或字型檔。
- 題目必須原創，不得照抄歷屆試題或出版社題目。
- 保留原作者與授權標示；改作版本不得宣稱是官方或原專案發布。

## 行為準則

請友善、就事論事地討論。對事不對人，也歡迎新手發問。
