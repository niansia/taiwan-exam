# GitHub 協作安排（保護規則尚未啟用）

維護者已於 2026-09-09 指定公開倉庫 `niansia/taiwan-exam`，同意 MIT 授權及首次推送測試版。
這不等於完整考卷品質已驗收，也不等於下列分支保護／合併規則已啟用。
本文件記錄後續治理需求；設定與實際權限需另行核對，不以文件存在宣稱保護生效。

- 其他人可提出 Issue、討論解法，並在自己的 fork／分支製作 commit、提出 PR。
- 他人在自己的 fork 中提交 commit，不需要維護者逐筆許可。
- 把更動納入本專案的受保護分支，必須取得維護者審核同意；不直接給一般貢獻者主分支寫入權。
- 不因 PR 通過自動測試就視為維護者已同意合併，也不啟用無人審核的自動合併。
- 後續依實際帳號、個人／組織倉庫及可用功能設定受保護分支或 ruleset：要求 PR、維護者 code-owner 審核、必要測試、新增提交後重新審核；檢查直接推送、強制推送、刪除及 bypass 權限。
- CODEOWNERS 指向維護者實際帳號，並保護治理檔案本身。單放 CODEOWNERS 不會自動強制審核，必須啟用對應規則。
- 若維護者本人提出 PR，另確認可行的審核／合併流程，避免要求自己批准自己造成無法合併。
- Issue 可提出、協作處理；關閉、標籤、指派等管理能力仍依 GitHub 實際權限，不為了方便處理 Issue 就授予主分支寫入權。
- 以一般貢獻者情境測試「可提 Issue／PR、不可直接改主分支、未經維護者同意不可合併」後，才宣稱設定有效。

官方參考：

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
