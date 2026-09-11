# Current GSAT 國綜 and 自然 Form Envelope

The corpus measurements in this file are derived from the official ROC 111–115 question PDFs. Separately labelled editorial constraints govern new generated papers; they are not claims that every official year follows an identical rule. No historical question text is supplied to the writing pass.

## Release-blocking implications

- A page whose body ends unusually early is not acceptable merely because the PDF has the official page count. Compare every non-terminal page against the subject envelope below and inspect it visually.
- New materials must be traceable to a frozen source record. Originality means a new selection, evidence combination, representation, and question mechanism; it does not authorize unattributed model-authored reading passages.
- A source title or distinctive phrase must be screened against the full local official/mock corpus before selection. A source previously used in a supplied paper is ineligible unless the new excerpt and operation are independently approved.
- Student-facing wording must not contain `自擬`, `本卷自擬`, or a fabricated-source label. Derived values require an audit-only transformation record tied to published input data.
- Do not append a `來源補充` block automatically. Keep only evidence required by the questions, integrated into the stimulus with a conventional end-of-passage attribution. Editorial interpretations, paraphrases of the intended answer, redundant background, and rights/audit notes belong outside the student booklet. Apply the removal test to each proposed addition; a source citation does not make an unnecessary paragraph exam material.
- Keep literary author/title attributions conventional and brief. Do not print copyright-status commentary, source-verification procedures, long technical bibliography, or statements such as “不含虛構觀測值” in the student paper. For natural science, retain source identity/date only where the task or the selected official reference pattern requires it; keep the complete provenance in the audit record. Figure captions explain the figure, not the intended inference or its whole bibliography.

## Typography and geometry checks (measured 2026-09-09)

The 111–115 PDFs are not typographically identical to one another. Select one controlling same-subject year, record actual differences, and do not promise exact equality with every publisher. The 115 references use a roughly 22.5 mm lateral margin; 國綜 main type is 11.04 pt with Ming for questions and Kai for reading materials, while 自然 main type is 10.98 pt (111–114 predominantly 11.04 pt). Latin text uses Times New Roman. Measure line rhythm, cover, headings and small figure labels separately; do not apply one body font to every role. CID-only font names are unidentified until independently resolved, not evidence of a known font.

- Compare actual PDF font spans and rendered output, not just CSS declarations. Record fallbacks, final scaled figure-label sizes, superscripts and subscripts.
- Restore alternating running heads, unnumbered cover and correctly counted content-page numbers; test that cover-only marks do not fragment onto an empty second page.
- Count actual groups after final assembly; printed group counts must match. Number figures in order of first appearance, and repeat a diagram only when it is needed at that location. Keep end-of-passage attribution with preceding text, and keep answer-summary column headings aligned with their body columns.
- Do not combine `white-space:pre-wrap` with inserted `<br>` plus retained newlines: this can double paragraph gaps.
- Keep the required answer instructions and scoring formula readable inside the cover box. Do not omit them to fit a generic cover.
- Question-booklet answer lines require evidence from the selected reference. Do not allocate fifteen lines for a seventy-character response merely to pass a density check. Neither enlarged figures nor answer lines may compensate for inadequate material or item length.
- SVG text must clear stroked edges and other labels, not merely fit its outer viewBox. Run `scripts/validate_svg_text_geometry.py <svg-directory> <report.json>` and inspect each figure in the final PDF. A passing geometry report is not a complete visual pass. Quantitative bars must also preserve their numeric proportions.
- Save a hash-bound page-review record covering every delivered page, with explicit unresolved defects. A `--visual-reviewed` flag or copied `pass` string alone is not review evidence. Source removal invalidates prior answerability sign-off; recheck the affected items.
- When revising inherited papers, revoke stale originality and comprehensive-release assertions in their metadata. Do not label an inherited item “freshly generated” or promote one successful calculation check into complete answer/content verification.
- If removing filler exposes a deficient substantive page/length contract, mark full-form release as failed and revise the content plan. A shorter readable proof may show typography repairs, but cannot be relabelled a fully faithful complete paper.

## 國綜

- Corpus: 5 papers / 60 pages.
- Compact characters per page: `{'min': 556.0, 'p10': 911.0, 'p25': 1046.0, 'median': 1164.0, 'p75': 1242.5, 'p90': 1350.2, 'max': 1551.0}`.
- Used-bottom ratio, all pages: `{'min': 0.522, 'p10': 0.937, 'p25': 0.944, 'median': 0.973, 'p75': 1.0, 'p90': 1.0, 'max': 1.0}`.
- Used-bottom ratio, excluding each paper's final page: `{'min': 0.909, 'p10': 0.942, 'p25': 0.947, 'median': 0.983, 'p75': 1.0, 'p90': 1.0, 'max': 1.0}`.
- Heuristic item surface length: `{'min': 55.0, 'p10': 94.8, 'p25': 128.0, 'median': 163.0, 'p75': 307.5, 'p90': 600.7, 'max': 1116.0}`.
- Item starts per page: `{'min': 0.0, 'p10': 1.4, 'p25': 2.5, 'median': 3.0, 'p75': 4.0, 'p90': 5.0, 'max': 6.0}`.
- Pages with a visual signal: `0.964`.
- Prompt cue totals: `{'依據／根據': 72, '最適當': 71, '可推知': 16, '證據評估': 47, '實驗設計': 5, '計算／估算': 13, '跨文本': 53}`.

### 國綜創新命題硬規則

每個計分題都必須存放共通格式的 `item_spec.subject_innovation_audit`。來源未曾出現在題庫，只能證明來源候選的新穎性，不能證明題目機制新穎。`mechanism_family` 必須描述真正的語文操作，例如語境中的語義轉折、形式與效果的關係、論證與證據、敘事視角、跨文本張力、古今語用比較、非連續文本整合或短答證據綜整；不得只寫作品名、作者、文體或主題。

`new_subject_mechanism` 要指出學生必須建立的全新語文／詮釋關係，`evidence_or_reasoning_architecture` 要列出從哪些字句、段落、圖表或文本差異走到判斷，`nearest_neighbor_difference` 要具體比較最近鄰題的材料組合、問法功能、證據依賴、誘答誤讀或短答評分決策。只換未見過的選文、另截同一作品、重排選項、換成生活情境、把單篇理解包成跨文本版面，均不算創新。

選擇題的錯誤選項須對應新的語境誤讀、指涉錯置、論證跳躍、修辭功能混淆或跨文本關係誤判；短答題須有新的證據選擇／整合任務與可判別評分點。整卷 `metadata.subject_innovation_review` 必須分別檢查語文知識、白話／文言閱讀、跨文本、非連續材料及短答的機制與表徵重複，拒絕一整卷反覆使用「依據本文何者正確」而只換文章。由 `scripts/validate_chinese_natural_scope.py` 做結構退件，來源比對、實際解題與人工判讀仍不可省略。

Per-year density checks:

- ROC 111: 12 pages; 12202 compact characters; 37 item starts; 1 pages below 60% used; 10 pages with visual signal.
- ROC 112: 12 pages; 12885 compact characters; 35 item starts; 0 pages below 60% used; 12 pages with visual signal.
- ROC 113: 12 pages; 13268 compact characters; 36 item starts; 0 pages below 60% used; 12 pages with visual signal.
- ROC 114: 12 pages; 13034 compact characters; 36 item starts; 0 pages below 60% used; 12 pages with visual signal.
- ROC 115: 12 pages; 13319 compact characters; 36 item starts; 0 pages below 60% used; 12 pages with visual signal.

### 國綜短答與核心古文：命題及驗收硬規則

以下為使用者指定的新卷命題規則，與上方歷年量測資料分開處理；只適用國綜，不得套用到國寫或回寫官方歷史資料。

**短答：每個獨立作答小題最多40字、最高4分。**

- 完整的簡短說明題以「40字以內、4分」設計；摘錄、填表、辨識等較短作答可依所需證據與控制年度的配分給較少字數、較低分數。40字是上限，不是要求考生寫滿的下限。禁止國綜出現要求80字或近似小作文的單一作答。
- 先寫出符合字數限制、可獲滿分的學生示範答案，再定稿題幹與評分規準。保守地將可見文字、數字及標點均計入字數，忽略空白與格式標籤；不要把教師詳解當成學生須寫的答案。4分短答應有少量明確可判的得分要點與部分給分方式，不能要求在40字內同時完成多層比較、逐項論證及完整長結論。
- 若原設計需80字才能答完，必須刪減考查任務、縮小證據範圍或重設問題；禁止只把題幹的「80」改為「40」而保留過量要求。短答的難度來自精準擷取、推論及整合，不靠增加書寫負擔。
- 區分「大題總分」與「獨立短答小題」。若選定且已查驗的官方結構有6分或8分大題，新卷可在不改變大題總分的前提下，設計真正獨立的短答小題，例如2分＋4分或4分＋4分；各有清楚標號、問題、字數上限及評分規準。不得把同一篇80字長答硬切成兩格，也不得把同一證據重複計分。若無法合理拆分，重設該題，不得竄改官方 profile 或偷偷減少整卷總分。
- 答題空間須配合短答字數與實際題型，並依 `exam_packs` 中選定年度的真實答題卷／版面核對；不得配置作文式長橫線或大面積留白。縮短短答不代表縮短閱讀材料，材料篇幅、題組資訊量及整卷密度仍須通過原有檢查。

**核心古文：占整卷總配分20–25%，不是篇數或閱讀字數。**

- 在選材與題目配置階段先列配分預算；100分國綜須有20至25分真正考查核心古文。最終以「可歸屬核心古文的得分合計 ÷ 整卷總分」重新計算，兩個端點均可接受，不得用四捨五入掩飾不足或超標。
- 以適用課綱及已確認的核心選文名單認定作品，記錄作品名與名單依據；不能把任意文言文、同作者其他作品或只提到篇名的題目算作核心古文。未確認名單時不得宣稱比例已達標。核心古文占比與「全部文言／白話材料占比」是兩個不同指標，必須分別檢查。
- 逐題／逐個有明確配分的子題記錄核心作品、對應文本證據、考查概念與可計入分數。只有作答真正需要該核心文本的語意、論證、人物、修辭或相關語文知識時才計入；移除核心文本及其必要知識後仍不影響解題的裝飾性引用，不計入。
- 同一題涉及兩篇核心古文也只能計分一次。題組中僅部分小題依賴核心文本，就只計那些小題的分數；混合評分題只能按既有評分要點歸屬，不得把整個題組分數全部灌入，也不得為湊比例杜撰子配分。跨文本比較若確實必須理解核心文本才能得分，可計入相應分數。
- 分散核心作品與考查操作，避免單篇或反覆字義記憶題填滿配額。可把核心古文與未見的新材料、生活情境或真實議題配對，考查觀點比較、語境判讀與證據推論；仍須高中課綱內可解。核心篇目可以是熟悉的課內作品，但不可照搬歷年截段、題幹、選項或解題機制；原有全資料集相似性檢查及已用來源的新截段／新操作審查仍適用。

定稿前在既有命題藍圖及 `curriculum_semantics` 審查中保留逐題配分明細、核心占比，以及每個短答的字數上限、示範答案實際字數與評分要點。印成試題後再次對照題幹、答案、答題格與總分；超長、超分、比例不足／超標或缺少可核對依據均不得通過國綜內容驗收。這是內容審查要求；課綱代碼檢查程式通過，不等於已驗證核心文本依賴或短答負擔。

## 自然

- Corpus: 5 papers / 99 pages.
- Compact characters per page: `{'min': 278.0, 'p10': 540.9, 'p25': 676.5, 'median': 789.5, 'p75': 894.25, 'p90': 966.9, 'max': 1168.0}`.
- Used-bottom ratio, all pages: `{'min': 0.338, 'p10': 0.851, 'p25': 0.94, 'median': 0.952, 'p75': 0.989, 'p90': 1.0, 'max': 1.0}`.
- Used-bottom ratio, excluding each paper's final page: `{'min': 0.815, 'p10': 0.869, 'p25': 0.941, 'median': 0.952, 'p75': 0.991, 'p90': 1.0, 'max': 1.0}`.
- Heuristic item surface length: `{'min': 29.0, 'p10': 94.0, 'p25': 131.5, 'median': 182.0, 'p75': 264.75, 'p90': 353.0, 'max': 702.0}`.
- Item starts per page: `{'min': 0.0, 'p10': 2.0, 'p25': 2.0, 'median': 3.0, 'p75': 4.0, 'p90': 4.0, 'max': 6.0}`.
- Pages with a visual signal: `1.0`.
- Prompt cue totals: `{'依據／根據': 64, '最適當': 15, '可推知': 29, '證據評估': 27, '實驗設計': 75, '計算／估算': 85, '跨文本': 70}`.

### 自然科創新命題硬規則

每個計分題都必須存放共通格式的 `item_spec.subject_innovation_audit`，選擇題、複選題、混合題與非選擇題皆同。新近事件、罕見生物、太空任務、儀器照片、新圖表、黑白轉換或不同數值都只是表面材料；若可把名稱與數字換回既有題而不改變解題流程，就必須退件。

`mechanism_family` 與 `new_subject_mechanism` 必須描述學生實際操作的新科學關係，例如模型與證據互修、變因控制、競爭解釋、限制條件、誤差／不確定性、極端情況、實驗重設、多層表徵轉換或真正跨物理／化學／生物／地科的系統連結。`evidence_or_reasoning_architecture` 必須列出觀察／資料、課綱概念、推論、檢核的順序；`nearest_neighbor_difference` 必須具體指出最近鄰題在變因、控制組、因果結構、資料關係、模型假設、圖形拓樸、選項錯誤路徑或跨科依賴上的差異。

單純換一張圖後讀取同一個標示值、把公式代入包成新聞、重畫同一裝置、把同一實驗換物種、或讓五個選項重複同一機械判斷，都不算創新。完整卷的 `metadata.subject_innovation_review` 必須分別檢查四科、探究實作、兩大部分與混合題的機制及表徵飽和，並與九題分科區塊和整卷難度平衡共同驗收。由 `scripts/validate_chinese_natural_scope.py` 做結構退件；欄位通過不表示科學事實、課綱、答案或實際新穎性已通過。

### Discipline order and reasoning floor

- The first-part contract is visible, not metadata-only: print `第壹部分、選擇題（占72分）`, followed by the bordered direction `說明：第1題至第36題，含單選題及多選題，每題2分。` Questions 1–36 therefore total 72 points and contain both single- and multiple-choice items. Under the measured 115 profile the item-level mix is 24 single-choice plus 12 multiple-choice; do not replace this with 36 generic or single-choice items.
- Every Natural Science selected-response item has five options labelled `A`–`E`. Print `（應選 n 項）` in every multiple-choice stem, including multiple-choice subparts in `第貳部分`; derive `n` from the independently verified key and fail if the cue and key disagree. Do not ask candidates to infer how many choices are correct. The cover must reproduce both scoring rules: single-choice is all-or-zero, while multiple-choice judges all options independently and applies the selected official partial-credit formula. A generic scoring note or answer-key-only type marker does not satisfy this contract.
- Questions 1–36 of a complete current-form paper are four uninterrupted selected-response blocks of nine items. Physics, chemistry, biology, and earth science must each occupy one block; record their actual order in `metadata.natural_objective_block_order`. Do not interleave disciplines or meet balance only after the mixed section is counted.
- That block-order rule stops at Question 36. Mixed/constructed groups may be single-discipline or genuinely cross-disciplinary. Prefer a cross-disciplinary group when one coherent observation, experiment, installation, or decision naturally requires evidence from two or more disciplines; never split a coherent group merely to preserve four subject silos. Each subpart still has one primary scored domain, valid codes for every required discipline, and a non-ornamental evidence bridge recorded in `metadata.natural_mixed_group_designs`. A passage that merely mentions a second discipline without changing the solution remains single-discipline.
- Every complete-paper item records `item_spec.natural_reasoning_contract`. It must reject pure recall and one-step formula substitution, name a `core` or `high_frequency` curriculum anchor, list at least two genuinely linked reasoning operations, and state why the printed material/model/experiment is needed. A material that can be removed without changing the answer is decorative and fails.
- `簡單` means the evidence chain is short and transparent, not that the item asks for a definition. Medium and harder items should normally require at least three linked operations. Use variable control, competing explanations, graph/table/photograph integration, uncertainty, limiting cases, experimental redesign, or constraint reconciliation to increase demand.
- Do not imitate depth with peripheral facts, advanced terminology, unattractive arithmetic, or excessive reading. The assessed science remains a central 108-curriculum operation even when the context is novel.
- For a current-affairs-emphasis paper, freeze `as_of_date` and the editorial lock date before searching. Recent means that the event or measurement—not merely a later profile page—falls within the preceding 12 months. Let recent material form a visible plurality of the truly dated source groups while preserving discipline, difficulty, section, and time balance. Draw older dated material by stratified random selection across different years and source families, and track evergreen models separately. Record the adopted items, event dates, publication/update dates, lead times, disciplines, and section spread in `metadata.natural_source_ecology_plan`.
- Current context is not a shortcut around literacy. A recent name, mission, disaster, disease, or technology counts only if its source-specific image, measurement, experimental method, temporal comparison, or operational constraint changes the solution. Prefer more than the minimum number of answer-bearing figures when they improve representation variety; reject screenshots, ornamental photos, and one-value lookup graphics.

Per-year density checks:

- ROC 111: 20 pages; 13909 compact characters; 60 item starts; 0 pages below 60% used; 20 pages with visual signal.
- ROC 112: 20 pages; 15970 compact characters; 57 item starts; 1 pages below 60% used; 20 pages with visual signal.
- ROC 113: 19 pages; 14995 compact characters; 56 item starts; 0 pages below 60% used; 19 pages with visual signal.
- ROC 114: 20 pages; 14478 compact characters; 57 item starts; 0 pages below 60% used; 20 pages with visual signal.
- ROC 115: 20 pages; 15495 compact characters; 56 item starts; 0 pages below 60% used; 20 pages with visual signal.

### Natural-science visual-item floor

The page-level visual signal above includes tables, formulas, and drawing operators; it is not a count of semantically audited image questions. Pending complete item-level annotation, a full internal Natural Science paper must contain at least eight answer-bearing visual items across both major sections, at least four visual kinds, and visible coverage of physics, chemistry, biology, and earth science. At least one visual should require integrating two representational layers or variables rather than reading a single labeled value. A precise state surface, apparatus, circuit, graph, cross-section, orbital/sky model, or biological structure must be deterministically drawn from semantic data. Each counted item must fail when the figure is removed, remain legible in grayscale at final print size, and stay wholly within the 108 curriculum. If the floor is missed, replace existing items; do not attach decorative diagrams to short recall stems.

The visual-kind count is based on rendered topology, not filenames or declared labels. Reusing a bordered one-column label/value panel for a profile, map, graph, spectrum, apparatus, flowchart, or cross-section is a hard rejection. A real table needs row and column variables whose cross-cell relationship is necessary to solve the item; a boxed list that repeats the stem does not count. For the measured Natural Science contract, require the representation-topology audit described in `visual-generation.md`, visually compare all deterministic assets at final size, and reject prompt–figure duplication that lets the item remain answerable after the figure is removed.

## How to use this envelope

During drafting, use only these aggregates plus the subject blueprint and source registry. During QA, render the candidate, measure it with the companion density validator, then inspect every page. Density is a rejection signal, not permission to cram or shrink type.

## Final-assembly regression checks

- **Real-event literacy, not anonymous scenario wallpaper:** when the user requests current-affairs integration, major 自然 inquiry groups must start from independently found, dated events, actual research methods/results or official datasets. Record the event date separately from publication/update dates. A 2025 researcher profile cannot relabel a 2012 experiment as a 2025 study. Generic「某研究／某校」models, even correctly labelled hypothetical, do not satisfy this request by themselves.
- Preserve a source-specific relation students must use: contrasting measured indicators, an actual experimental control, the instrument's detection window, or the constraints of a real installation. Replacing names/years while keeping a generic calculation is a failed revision. Test both source removal and source-relation removal. Retain basic concept questions where the corpus warrants them; do not make the entire paper a news quiz.
- Do not invent empirical response counts, temperatures, capacities or thresholds to complete a real case. Derivations from reported figures are allowed; a hypothetical counterexample or ideal-limit calculation must be labelled locally and must not be attributed to the real researchers. Never treat failure to detect as proof of absence, number fraction as mass fraction, or a different measurement window as a time trend.
- Student-facing text includes the date, named object and factual conditions needed for reasoning, not an appended bibliography or defensive source disclaimer. Put full URLs, frozen factual notes, transformations and uncertainty limits in a separate editorial ledger. A source cited in that ledger is not permission to paraphrase an authentic 國綜 excerpt into fabricated original prose.

- Authentic 國綜 excerpts must match the frozen source between visible omission marks. Normalize only punctuation, whitespace and explicitly documented variants; strip retrieval link wrappers before comparing. A genuine author/title does not legitimize rewritten sentences. Re-solve items after shortening; preserve the antecedent of phrases such as「這一問」and every tested quotation.
- Typography includes paragraph rhythm: the 115 國綜 reference uses approximately 17 pt baseline spacing, versus approximately 18 pt in 自然. Do not indent or space a continuation chunk as a new paragraph. These values are role-specific measurements, not universal specifications for all years.
- A page-packing estimate is not the acceptance measurement. The fixed-page renderer may use a provisional 77% atom-height threshold while accounting for bounded normal inter-item spacing, but must reject the FINAL rendered question page below 78% or with overflow. Never use figure enlargement, explanatory padding or answer-revealing additions to close a gap.
- Keep a figure-dependent stem with its figure. If options continue onto an adjacent page, preserve their labels and order, prohibit orphan single labels, and inspect the page pair. No additional「第X題續」diagram is needed merely to consume space.
- Treat point labels such as「（2分）」as indivisible inline units. Check the rendered line ending, not just the presence of the score string. Whole-paper re-solving must also find repeated mechanisms: a mixed group's new control question can invalidate a retained standalone question testing the identical control.
- Check answer-position skew and distractor truth after final assembly. All multiple-select keys containing A, mechanically recurring key patterns, or a topic name with context-free reasoning require editorial review. Reordering options requires remapping the answer key AND every option reference in the explanation; it cannot change which statements are true.
- Validate scope-code existence separately from semantic alignment. Accept「地球科學」as the domain alias of「地科」; never add inquiry codes solely to meet a count. Record what data interpretation, experimental design or model revision actually occurs in that item.
- A final PDF's source, answer, geometry, grayscale and visual-review results are separate evidence. Bind each review to its hash. Metadata such as `editorial-solved` is a work record, not an empirical difficulty/discrimination result. Do not claim student pilot calibration or complete scan-corpus novelty when neither was performed.
- After a difficulty revision, reconcile every diagram label with the new conditions; stale frequencies, phases or quantities must not remain as a second conflicting premise. Store the asset hash with the item review. Keep short five-column numerical options on one row: a long stem does not justify splitting that row into two partial grids. Remove glossary entries whose terms no longer occur in the selected passage.
