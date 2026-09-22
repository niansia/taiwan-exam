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

### 國綜 printed form catalogue, ROC 111–115 (measured 2026-09-22)

Every official booklet prints these headings, in order, each with one bordered
說明 line; `validate_chinese_layout_contract.py` rejects a paper that omits them:

| Heading (verbatim) | Direction | Items |
|---|---|---|
| 第壹部分、選擇題（占76分） | — | 1–31 |
| 一、單選題（占48分） | 說明：第1題至第24題，每題2分。 | 1–24 |
| 二、多選題（占28分） | 說明：第25題至第31題，每題4分。 | 25–31 |
| 第貳部分、混合題或非選擇題（占24分） | 說明：本部分共有1題組，選擇題每題2分，非選擇題配分標於題末。… | 32–36 (32–37 in 111–112) |

Option columns, measured on every (A)–(E) line of the five booklets: a four-option
item whose options are at most 16 characters (19 with the label) prints them two
abreast at x = 82 pt and 298–303 pt (152 such lines; item 1 and short 填詞 items
every year); longer options and every five-option item print one per line. The
renderer's `option_columns` applies exactly this rule for 國綜; `grid-2` is the only
multi-column layout the contract accepts, and only within that length.

The item-by-item reading of all five papers is recorded in
`exam_packs/學測/shared-data/chinese-item-type-envelope.json`. What holds every
year (111–115), and is therefore enforced:

- Item 1 is 字音 (`下列「」內的字，讀音前後相同的是：`): every option pairs two
  **different** characters that share a component or phonetic, each quoted inside
  its own classical four-character phrase and joined by ／ (111 痺／髀, 忮／庋, 攢／鑽,
  剜／腕; 112 笳／袈, 鬩／睨, 踣／掊, 吁／迂; 113 闥／撻, 篙／蒿, 棹／踔, 逡／悛; 114 舁／臾,
  啗／諂, 迤／弛, 畛／殄; 115 攲／旖, 諳／喑, 枇／毗, 遏／謁). Obscure characters are the
  norm and the phrases come from 文言 or 成語. Testing one character's two readings
  (「屬」客／桑竹之「屬」) is a different exercise that never appears as item 1;
  `validate_chinese_layout_contract.py` rejects identical quoted characters, halves
  without one quoted character each, and halves outside three to six characters.
  Item 2 is 字形 (`下列文句，完全沒有錯別字的是：`).
- Every 題組 (items 6–24, 30–31, 32–36) prints its material's source: modern prose
  as `（改寫自 作者〈篇名〉）`, 文言 as `（〈篇名〉）` or `（《書名》）`; the five official
  papers carry 17–42 such attributions each. A generated paper with three
  attributions and six self-written expository passages read markedly easier than
  any official year: the contract now rejects a group without an attribution.
- 排序題 is 文言 when it appears (113 Q5 `下列是一段古文`, 115 Q5 with 甲–戊); a
  白話 sentence reorder is not the form and is rejected.
- Material kinds: official 白話 groups are essays, science and culture writing,
  criticism and literary prose; 文言 groups are 核心古文, 文言小說 and 古典韻文; at most
  one group a year comes from a regulation, manual, dictionary entry, notice or
  application form (法條、辦法、手冊、辭典條目、公告、公所說明、簡章). A generated paper
  built six of nine groups from such documents (著作權法第65條, 標點符號手冊, 台語辭典
  用字原則, 區公所調解說明, 徵文辦法) and read like a civics test; the contract caps
  those groups at one. 文言／古典 material (detected from character statistics) covers
  11, 9, 9, 4 and 4 of items 1–31 in 111–115; the maintainer set the floor at 10 with a
  target of 12–14 because 文言 is the curriculum's weight, so a paper meeting it is more
  classical than 113–115. Judgement items print ①②, never ➀➁ dingbats.
- Difficulty signals measured on the five booklets and enforced by the contract:
  options containing absolute words (完全、必然、唯一、所有、只會…) are 6–12% of all
  options and appear in at most 36% of items; the generated paper had 22% and 70%,
  so most distractors could be eliminated without reading. Official distractors are
  plausible misreadings that fail on one inference (a wrong scope, a reversed
  cause, a claim the text does not make); an option that is off-topic, absurd or
  absolutist is not a distractor. 字形 sentences run 18–23 characters with the
  錯別字 hidden in a 成語 or literary word. The ①②研判題 is a single-choice item
  whose options are 皆符合／皆不符合／①符合，②不符合／①不符合，②無法判斷. The
  booklet as a whole prints 43–68 source and title tokens (改寫自／〈篇名〉／《書名》);
  the contract floor is 30. A student-facing material must never declare itself
  自擬, 自撰, 編者撰成 or 本題情境.
- 詞語填空 (111 Q6, 112 Q6, 114 Q3; none in 113 and 115) always quotes a real work
  with its printed attribution: 杜甫〈灩澦〉and〈絕句漫興九首〉(`依據詩意與格律`),
  〈補江總白猿傳〉(文言), 聶華苓〈月光•枯井•三腳貓〉(現代散文). Three □ slots of two to
  four characters; the four options use exactly **two** candidate words per slot,
  each appearing in two options, so any two options differ in at least two slots
  (破海綿／舊報紙, 皎潔／青蒼, 貪婪／貧血). The difficulty is the near-synonym pair
  judged from context or 格律, not vocabulary breadth. A self-written sentence
  with four unrelated words per slot (輕率／全面／草率／徹底) is eliminated slot by
  slot and is not the form; the contract rejects a missing attribution, a slot
  with more or fewer than two candidates, and options differing in one slot. Items 1–5 stand alone (詞語運用, 填詞, 文言排序,
  稱謂, a boxed table, a 70–200-character passage); shared-stimulus 題組 start at
  item 6 (9 and 8 in 111–112) and carry items 6–24 in 6–8 groups of two or three
  (one group of 4 or 5 at most).
- The first multiple-choice item (25) is 文言字義 `下列各組「」內的詞，意義前後相同的是`,
  its five options quoting 核心古文 (鴻門宴, 燭之武退秦師, 勞山道士, 項脊軒志, 出師表,
  虯髯客傳, 諫逐客書, 畫菊自序, 鹿港乘桴記, 赤壁賦 recur). Items 25–29 stand alone with
  their own material; items 30–31 are one closing two-item group containing 文言 or
  韻文. No 國綜 multiple-choice stem prints （應選n項）.
- Every year has one 成語／畫底線詞語運用 item (single-choice 3 in 111–112, multiple
  choice 25–26 since 113), at least one 語法／虛詞 item (「以」表目的, 「則」, 程度副詞,
  量詞, 條件句), at least one ①②研判題 (皆符合／皆不符合／①符合②不符合／無法判斷;
  two or three a year since 113), at least one 古典詩詞曲 item, at least one
  Taiwan-themed group, and at least three items whose options quote 核心古文.
- 第貳部分 is one group 32–36 on three or four related texts 甲乙丙(丁) that always
  include 文言 or 韻文: an abstract framing text applied to case texts. It holds
  exactly two 2-point single-choice subparts and three constructed items each with
  (1)(2); 2-point subparts allow 10–20 characters, 4-point subparts 30–40 (or two
  parts of 10–15); constructed points per item are 6, 6 and 8 (or 6, 8, 6).

Measured 113–115 distribution of the 24 single-choice items: 白話說明文閱讀 9–15,
文言閱讀 0–5, 白話文學閱讀 0–3, 跨文本比較 1–2, 圖表或非連續文本 0–3, 古典韻文 0–2,
plus the fixed 字音, 字形 and one or two language-knowledge items. Of the seven
multiple-choice items: 文言字義 1, 成語運用 1, 語法 0–1, 文學常識 0–1, 文言閱讀 0–2,
白話說明文 0–2, 跨文本 0–2. Modern non-fiction prints 改寫自 with author and
title; 文言 prints its source; rare words get side notes. The paper is short and
many-textured rather than long: standalone 文言 70–200 characters, groups 250–700,
only the 第貳部分 packet and one or two literary-criticism groups exceed 1,000.

Option labels are `(A)`–`(D)` (`(A)`–`(E)` for multiple choice) and every option
prints on its own line; the projection now forces one column for 國綜. Boxed
side notes (詞語注釋, 資料框) sit beside the passage. The booklet is a cover plus
11 body pages, 11,900–12,900 substantive characters.

Measured counter-example, a hosted 國綜 paper reviewed on 2026-09-22: no part
headings or scores; items 1–2 were a white-text 題組 about a museum label, so
the paper had no 字音, 字形, 成語 or 文言排序 item at all; every multiple-choice
item was paired into a 題組 and printed （應選3項）; options were `(1)`–`(5)` in
two or four narrow columns wrapping into three-line stacks; 15 pages with three
pages more than 20% empty; the single-choice key rotated 1-3-2-4 without a single
adjacent repeat. Each of these is now a named error.

### 國綜 shared-stimulus floor

Measured ROC 111–115: 12 pages, 11,926–12,871 substantive characters, 9–10 題組
per paper (7–9 in 第壹部分 carrying 19–21 items), with a per-year group-stimulus
median of 365–572 characters. Release floors: at least **8 題組**, a group-stimulus
median of at least **300 characters**, and at least **9,117 characters** of item
content (stimuli, stems and options; the cover and 說明 blocks are the Layout
Profile's, not the writer's). Restore length with genuine reading material — a longer excerpt, a
second paired text, a real document — never with directions boilerplate or
repeated framing sentences.

Every scored item in a complete 國綜 paper also records
`item_spec.chinese_reasoning_contract`, the reading-evidence counterpart of the
自然 contract below. It must set `recall_or_definition_only: false` and
`single_cue_recognition_only: false`, name the `textual_evidence_span` a
candidate must use, state the `material_dependency` that fails when the passage
is removed, and list at least two linked reasoning operations — three when the
declared band is 中, 中偏難 or 難. Recognising one 通同字, matching a 成語 to its
gloss, or picking the option that repeats a nearby sentence is one cue, not a
reasoning chain. `validate_chinese_natural_scope.py` rejects a missing or
collapsed contract.

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

### 自然: shared stimulus and cross-disciplinary mixed groups

Measured ROC 111–115
(`exam_packs/學測/shared-data/current-form-literacy-envelope.json`): the booklet
runs 19–20 pages and 13,517–15,243 substantive characters and carries 9–12 題組.
**Three to six of those sit inside 第壹部分**, carrying 6–12 of questions 1–36;
第貳部分 prints exactly 6. Group stimuli run to a per-year median of 100–198
characters in 第壹部分 and 188–365 in 第貳部分.

A paper written as 36 standalone one- or two-sentence items plus six thin mixed
groups is not this form. It is the observed failure mode, and it produces the
short-paper and easy-paper defects together, because the shared stimulus is
where the reading load and the multi-step inference live.

Release floors, all below the weakest official year: at least **3 第壹部分 題組
carrying at least 6 items**; exactly **6 第貳部分 題組**; a 第貳部分 stimulus median
of at least **175 characters** with at most **2 groups under 120**; a 第壹部分
stimulus median of at least **90**; and at least **10,687 characters** of item
content (stimuli, stems and options, excluding the cover and 說明 blocks). ROC 113 is the binding case at a 188-character
median with two short groups.

At least **two of the six 第貳部分 題組** must genuinely require two or more of
物理／化學／生物／地科. CEEC declares exactly 2 合科 groups in every official
111–115 paper; the maintainer's wider reading finds 3–5 (median 4); the per-group
classification is recorded in
`exam_packs/學測/shared-data/natural-mixed-group-cross-discipline.json`. Declare
each such group in `metadata.natural_mixed_group_designs` using the existing
record shape — `question_numbers`, `required_domains`, `evidence_bridge` — plus
`second_discipline_removable: false`. At least one subpart must also record the
second discipline in `item_spec.domain` or `item_spec.secondary_domains`; a
declaration by itself never establishes the crossing. A group
counts only when deleting the second discipline changes the solution: the
official pattern is a shared object or measurement that forces the crossing, as
in 115's printed 苄丙酮／尼古丁 structural formulas driving a pollination argument,
114's band-gap excitation producing the radicals that do the decomposition
chemistry, or 111's Doppler frequency shift serving as the instrument for a
circulatory measurement. Naming a second field, or setting a biology item in a
laboratory, does not qualify.

Run `scripts/validate_literacy_load.py generated-exam.json --subject 自然` before
layout. See [current-form-literacy-load.md](current-form-literacy-load.md).

### Discipline order and reasoning floor

- The first-part contract is visible, not metadata-only: print `第壹部分、選擇題（占72分）`, followed by the bordered direction `說明：第1題至第36題，含單選題及多選題，每題2分。` Questions 1–36 therefore total 72 points and contain both single- and multiple-choice items. Under the measured 115 profile the item-level mix is 24 single-choice plus 12 multiple-choice; do not replace this with 36 generic or single-choice items.
- Every Natural Science selected-response item has five options labelled `A`–`E`. Print `（應選 n 項）` in every multiple-choice stem, including multiple-choice subparts in `第貳部分`; derive `n` from the independently verified key and fail if the cue and key disagree. Do not ask candidates to infer how many choices are correct. The cover must reproduce both scoring rules: single-choice is all-or-zero, while multiple-choice judges all options independently and applies the selected official partial-credit formula. A generic scoring note or answer-key-only type marker does not satisfy this contract.
- Questions 1–36 of a complete current-form paper are four uninterrupted selected-response blocks of nine items. Physics, chemistry, biology, and earth science must each occupy one block; record their actual order in `metadata.natural_objective_block_order`. Do not interleave disciplines or meet balance only after the mixed section is counted.
- That block-order rule stops at Question 36. Mixed/constructed groups may be single-discipline or genuinely cross-disciplinary. Prefer a cross-disciplinary group when one coherent observation, experiment, installation, or decision naturally requires evidence from two or more disciplines; never split a coherent group merely to preserve four subject silos. Each subpart still has one primary scored domain, valid codes for every required discipline, and a non-ornamental evidence bridge recorded in `metadata.natural_mixed_group_designs`. A passage that merely mentions a second discipline without changing the solution remains single-discipline.
- Every complete-paper item records `item_spec.natural_reasoning_contract`. It must reject pure recall and one-step formula substitution, name a `core` or `high_frequency` curriculum anchor, list at least two genuinely linked reasoning operations, and state why the printed material/model/experiment is needed. A material that can be removed without changing the answer is decorative and fails.
- `簡單` means the evidence chain is short and transparent, not that the item asks for a definition. Medium and harder items should normally require at least three linked operations. Use variable control, competing explanations, graph/table/photograph integration, uncertainty, limiting cases, experimental redesign, or constraint reconciliation to increase demand.
- Do not imitate depth with peripheral facts, advanced terminology, unattractive arithmetic, or excessive reading. The assessed science remains a central 108-curriculum operation even when the context is novel.
- Every full paper is current-affairs-aware by default; see [current-form-topicality.md](current-form-topicality.md) for the measured ROC 111–115 envelope (0–5 recent contexts a year, a typhoon context in four of five years, 6–13 climate/energy items every year) and the floor `validate_current_context.py` enforces. Freeze `as_of_date` and the editorial lock date before searching. Recent means that the event or measurement—not merely a later profile page—falls within the preceding 12 months. Let recent material form a visible plurality of the truly dated source groups while preserving discipline, difficulty, section, and time balance. Draw older dated material by stratified random selection across different years and source families, and track evergreen models separately. Record the adopted items, event dates, publication/update dates, lead times, disciplines, and section spread in `metadata.natural_source_ecology_plan`.
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
