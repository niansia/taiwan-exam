# Current GSAT social-studies form and evidence design

Read this reference for current-form GSAT social-studies analysis, generation, or rendering. Scope is controlled jointly by the CEEC social-studies examination specification and the selected official Paper Profile.

## Structure is annual, not frozen

The verified current-regime profiles show real variation:

| ROC year | Objective items / score | Mixed or constructed items / score | Total numbered items |
|---:|---:|---:|---:|
| 111 | 46 / 92 | 21 / 52 | 67 |
| 112 | 45 / 90 | 21 / 54 | 66 |
| 113 | 35 / 70 | 29 / 74 | 64 |
| 114 | 42 / 84 | 22 / 60 | 64 |
| 115 | 38 / 76 | 27 / 68 | 65 |

Every profile is 110 minutes and 144 points. Select one verified year before writing. Do not average these counts or declare 65 items universal. For the observed 115 paper, the official feature report further groups the objective section into five groups and the latter section into eleven mixed groups; reproduce that only when using the 115 profile.

## 單題按科集中，題組保留跨科

第一部分的**獨立單題**依公民、歷史、地理等科別各自連續成段，不得逐題輪替科目。實際先後順序、各段題數及單題／題組分界，先核對所選年度的正式試卷與架構表，再寫入命題計畫；不能把某一年的排列寫成所有年度的固定規則。這是科別層級的組卷約束，不是照搬歷屆的單元、情境或解題機制順序。

已核對的例子：[大考中心〈115學年度學科能力測驗試題特色－社會〉表1](https://www.ceec.edu.tw/xcepaper/cont?sid=0Q105616965176736879&sq=&xsmsid=0J066588036013658199)（2026-04-15）：

| 第一部分範圍 | 結構 |
|---|---|
| 1–6 | 公民單題 |
| 7–15 | 歷史單題 |
| 16–25 | 地理單題 |
| 26–27、28–29 | 分別為公民、地理題組 |
| 30–33、34–35、36–38 | 分別為史地公、地公、史地公合科題組 |

- 上述115年實例是 **25道獨立單題＋13道題組內單選題**，不是38道單題排成三段。其他年度須重新確認，不能據此宣稱111–115全部同序、同數。
- **共用材料的選擇題組不受單題分科連續限制**；整組保持連續、完整，不能為湊科別區塊拆散題組，也不能替互不相關的單題掛同一組名來規避排序。
- **第二部分混合題／非選擇題完全不受上述分科連續限制**，包括其中的單選小題。判別依所在部分及共用材料，不是看到 `single_choice` 就一律搬到第一部分分科排序。
- `sections` 按正式印刷順序記錄兩大部分；題目以 `section_id` 歸屬、`number` 排序。同組小題使用相同的非空 `group_stimulus`；只有一題引用的材料仍屬單題。出卷前用 `validate_social_item_design.py` 檢查獨立單題是否回頭交錯科別、是否出現在題組後、共用題組是否被拆開。所選年度的精確區塊題數及跨科組合，另外與 `exam_packs` 參考架構人工核對，程式通過不等於已完成這項比對。

### 混合題的跨科素養與新穎性

同一大題可以同時涵蓋**歷史、地理、公民與社會**，也可以合理結合其中兩科或保留單科題組；不強迫每大題三科齊全，也不要求每個小題同時考三科。材料適合時，優先設計有共同證據問題的跨科題組，不因第一部分的分科排序而拆成三份小考卷。

- 先確立同一真實問題及可追溯材料，再讓歷史的時序／變遷／史料、地理的空間／尺度／環境、公民的制度／權利／經濟機制各自提供解題所需證據。新穎可以來自不同年代與空間尺度的對照、多來源矛盾的判讀、圖文整合或制度條件下的推論，不是只有新聞名稱新。
- 宣稱三科合科時，三科都必須進入至少一個小題的實際推理或評分規準，並說明跨材料、跨觀點的關聯；刪除其中一科的證據／概念後，至少一項判斷應失去依據或改變。只附一張地圖、補一個年份、提到法律名詞，或把三道無關題共用一個標題，都不算跨科素養。
- 每小題仍只歸一個主要計分科別，附上真正用到的次要科別及有效課綱代碼；科目占分不可因跨科標籤重複計算。完整解法限於指定必修課綱，陌生專業背景須由材料完整提供。保留合理難易梯度，不以長篇堆字、艱澀術語或課外知識製造難度。
- 沿用 `metadata.mixed_group_originality_records`，在每組紀錄中以 `question_ids` 對應實際小題，於 `integration` 寫明各科的證據位置、課綱操作、相互關聯與刪除測試；`subpart_dependency` 說明共用材料的必要性，`answer_leakage` 檢查前後小題不互洩答案、不因前題答錯連鎖失分。不要另造一套批次出題器或以欄位宣告代替實際解題審查。

### 全題型的社會科創新命題硬規則

上述跨科新穎性只是其中一種形式。完整卷的每個計分題——包含基本取向的獨立單題、選擇題、題組小題與非選擇題——都必須另存共通格式的 `item_spec.subject_innovation_audit`。未使用時事或圖像的題目也不能豁免。

- 歷史的新機制可建立在史料來源／立場張力、時間序列與變遷、因果競合、證據適切性或跨材料互證；只換朝代、人名、年份或史料句子而保留同一問法不算。
- 地理的新機制可建立在尺度切換、空間分布、地圖／遙測／統計整合、人地系統回饋、區域比較或政策限制；只換地名、底圖、圖例或數值不算。
- 公民與社會的新機制可建立在權利衝突、制度程序、法律層級、媒體證據、市場／外部性、分配效果或政策條件推論；只換法條名稱、案例角色或政策議題不算。
- 跨科題必須產生刪除任一必要學科證據便會改變判斷的共同問題；三道獨立例題共用一段材料不算。

`new_subject_mechanism` 必須說明材料中的哪個關係使課綱概念產生新的證據工作；`evidence_or_reasoning_architecture` 必須列出實際的取證、比較、限制與判斷順序；`nearest_neighbor_difference` 必須指出最近鄰題在史料組合、空間尺度、制度條件、因果結構、選項錯誤模型或作答要求上的具體差異。來源剛發布、照片第一次使用或課綱代碼不同，都不能單獨構成差異。

整卷的 `metadata.subject_innovation_review` 必須分別檢查歷史、地理、公民與跨科題組的機制與證據表徵是否飽和，並拒絕「新聞摘要＋定義辨識」、同一比較表反覆換標題、同一政策案例四處換名，以及同一張圖只讀單值的連續題。由 `scripts/validate_social_item_design.py` 做結構退件，再由審查者核對實題；欄位宣告不能取代解題。

## Three disciplinary lenses

History, geography, and civics remain identifiable even inside cross-disciplinary groups. Every item records one primary domain, any secondary domains, curriculum codes, evidence operations, and score. The controlling CEEC specification limits assessed knowledge to the Grade 10–11 required history, geography, and civics learning-content codes; an extension topic may provide a situation, but it may not silently introduce an out-of-scope rule. Use the chosen profile and current multi-year envelope to balance score; a convenient 25%–42% per-domain band is a review warning, not a replacement for annual evidence.

- **History:** chronology and continuity/change, contextualization, source provenance, comparison of accounts, historical causation, and judgment about evidence fitness.
- **Geography:** location and scale, map/remote-image reading, spatial pattern, human–environment systems, data interpretation, regional comparison, and policy implications.
- **Civics:** rights and institutions, law and procedure, media/public opinion, markets and externalities, distribution/fairness, competing values, and warranted policy judgment.
- **Cross-disciplinary:** one shared object must genuinely require more than one lens. Merely placing a historical date beside a map does not make an integrated item.

### Official scope binding: content is not performance

The CEEC 111-onward Social Studies examination specification controls the paper. It defines four goal levels (foundation, analysis/interpretation, judgment/reflection, and integrated inquiry), limits tested knowledge to the Grade 10–11 required curriculum, states that extension-inquiry notes may supply a situation but not extra assessed knowledge, and requires balanced History, Geography, and Civics scoring. Read its sections `測驗目標`, `測驗內容`, `題型、配分`, and the examples before writing.

Keep three layers separate in every item:

1. `curriculum_codes` contains only Grade 10–11 required **learning-content codes**, such as `歷Db-Ⅴ-3`, `地Ab-Ⅴ-2`, or `公Ac-Ⅴ-3`. Validate against [social-required-content-codes.json](social-required-content-codes.json), which excludes elective courses.
2. `ceec_assessment_targets` contains one or more CEEC paper targets: `H1–H9`, `G1–G9`, `C1–C7`, or genuinely cross-disciplinary `S1–S5`.
3. Optional learning-performance codes such as `歷1b-Ⅴ-2`, `地1b-Ⅴ-1`, and `公1c-Ⅴ-1` belong in a separate `learning_performance_codes` field. They never prove that the assessed knowledge is in scope and must not appear in `curriculum_codes`.

For each learning-content code, add one `curriculum_alignment` record with `content_code`, `assessed_relation`, `stimulus_evidence`, and `centrality_reason`. The record must explain what the student actually does with the required-course content, where the necessary evidence appears, and why this is a core or high-frequency target rather than a technically related footnote. A broad label such as “法律”, “人口”, or “現代化” is not an alignment argument.

A complete paper also stores `metadata.social_scope_contract` with the CEEC specification and NAER curriculum URLs, retrieval dates, hashes, and the four reviewed CEEC sections. The validator confirms exact code membership, domain fit, target-code validity, and alignment-record completeness; a human reviewer must still compare the prompt and solution with the official content statement. Any paper that uses only performance codes, an elective code, an invented code, or a content code from the wrong primary discipline is release-blocking.

## Current issues without current-affairs trivia

Typhoons, AI labor, public health, elections, platform governance, migration, energy, war, disasters, conservation, trade, or any other current issue may inspire a group. They are examples, never mandatory topic-to-unit mappings.

A current source may advance only if:

1. it predates the simulated editorial lock and has a stable URL/date;
2. factual claims are checked against a primary source, dataset, law, judgment, research release, or archive; news alone is not the factual authority;
3. all facts needed to solve are printed in the stimulus;
4. the question requires a disciplinary operation, not recognition of the event;
5. a source-derived relation changes the reasoning when removed; merely anonymizing a famous name is allowed and is not a failure;
6. contested claims are separated from facts and follow the party-stance-free editorial rules below; neutral wording does not excuse false balance or unsupported claims.

Keep both basic anchors and competence-oriented groups. A paper made entirely of long topical passages is as distorted as a paper made entirely of recall questions.

`Basic` means a central required-course anchor, not a bare definition prompt. No scored item may ask only which option restates a term, article heading, person, date, or memorized textbook sentence. Every item must require at least two linked operations such as extracting material evidence and applying a concept, comparing relations, reconstructing cause and constraint, checking scale or procedure, or evaluating what a source can support. If the supplied material can be deleted and the same answer follows from recalling one definition, reject the item rather than relabelling it competence-oriented.

Scope membership alone is not enough. Every item must record a specific `core_curriculum_anchor`, classify `curriculum_centrality` as `core` or `high-frequency`, and state why the tested operation is central to Grade 10–11 learning and the current GSAT evidence model. Peripheral subclauses, specialist taxonomy, obscure institutional trivia, and technically in-scope but rarely assessed details may appear only as fully defined context; they may not be the knowledge being rewarded. A full paper is released only after a reviewer can explain the curriculum priority of every scored item, not merely attach a plausible code.

### Prevent short-material collapse

The printed evidence must be rich enough to support the claimed operations. Reject a full paper whose apparent literacy is created by attaching a 60–100-character mini-scenario to nearly every question while leaving most pages sparsely occupied. Short items remain valid only as a deliberate minority matching a short current-form role. Across the paper, use substantial historical excerpts, paired accounts, maps, statistical displays, life documents, policy or legal excerpts, photographs, and multi-source groups so that students must locate relations rather than infer the intended textbook term from one cue.

Before item review, measure each unique printed stimulus once, the prompt and all options, and the final student PDF's compact interior text. Compare the rendered paper with the selected official question booklet using `validate_reference_page_density.py`; the whole-paper substantive-text floor is 80% of the reference and does not include invisible metadata, answer explanations, duplicated shared material, oversized headings, blank answer lines, or decorative captions. An answer-bearing photograph, map, or chart may legitimately replace some prose on its page, but its observed features and reasoning role must be stated in the page review. Passing the numeric floor does not excuse repetitive one-paragraph scenarios, and failing it may not be repaired by smaller type, wider text blocks, padded options, or irrelevant prose.

For a full current-form paper, include a few scored questions that genuinely depend on verified events or substantive updates within the year before the editorial lock. Interpret this as a small default allocation: normally 3–5 questions, with a minimum of 3 in the default full-paper check, not a required percentage or an upper limit. This operational default is not a user-specified exact number or a CEEC statistic. Retire the previous seven-cluster / 24-item / 24-point quota and the mandatory objective-section cluster count. Arrange the remaining questions and section placement freely within the curriculum, discipline balance, evidence quality and solving-time contract; older and evergreen sources are equally eligible. Count only source-verified, task-reviewed items using `evidence-backed-editorial-audit.md`. Several distinct scored tasks may share one well-designed group, but duplicate tasks or decorative dates do not count; report unique source objects separately from question count.

Current clusters should make students perform operations such as reconstructing a hazard–exposure–vulnerability chain, correcting a denominator, comparing policy defaults and exceptions, identifying scale mismatch, weighing rights or incentives, relating current change to historical evidence, or testing what a source cannot establish. Plausible distractors must fail on one of these operations; three absurd alternatives do not create literacy. “More current” never means asking who, when, or where as news trivia: all event-specific facts needed for the answer must appear in the material, while the assessed operation remains within a required-course code.

### 一年內安排幾題，其餘彈性選材

- 每份完整卷安排上述數題一年內的真實時事即可；不再要求近6個月優先，也不必刻意追近90天新聞。其餘依課綱、題型、資料品質與整卷節奏安排，沒有額外的新舊比例或時事配分要求。沒有指定模擬截稿日時以本次出卷日期為準，全卷共用同一截稿日；指定歷史年份時不得偷用其後新聞。
- 「一年內」為截稿日往前一個曆年起至截稿日止，含兩端；閏日對應前一年2月28日。用實際事件或實質更新日期判定，不用網站更新日或今年重刊舊聞充數。既有 `item_spec` 記錄 `event_date`，或確有新內容時記錄 `substantive_update_date`，並保留 `published_at` 與 `editorial_lock_date`；均使用 `YYYY-MM-DD`。來源須已在截稿日前公開，日期不明不計入一年內的題數。審查仍須分清事件、發布、資料期間與法規生效日期，程式比較日期不證明內容真的有更新。
- 一年內與較舊材料均須有來源、真正支撐課綱推論，不能只換年份。仍在發展的新聞只考查已凍結的事實，不問未確定結果；不能核實就換來源。沿用既有審查明細列出一年內的實際題數、來源及必要證據，其他選材不受新鮮度偏好綁住；政治中立、圖片品質、素養與學科平衡規則不變。

### 政治中立與爭議議題

- 題幹、選項、圖片、圖說及詳解不得呈現或暗示特定現實政黨支持／反對某政策的立場、政黨攻防、候選人宣傳或投票勸說；也不能以黨徽、口號、代表色或影射式稱呼繞過。政黨制度本身及必要的歷史事實仍可中性考查，但不把當代政黨立場當成答題線索或正確答案。
- 保留解題必要的真實年份、地點、制度及證據，省略不必要的政黨與政治人物識別；完整來源留在內部紀錄。若原文或照片的核心就是政黨宣傳，改選制度文件、統計、判決或其他合適材料，不偽造引文、替真實人士編造立場，或靠裁切掩飾史料原意。
- 可以比較政策理由與價值衝突，但正誤及給分依題附證據、課綱概念與明確評分規準決定，不依學生贊成／反對政策的立場。不同立場若同樣滿足開放題的證據要求，應按同一規準給分；客觀法規與已證實事實則不因「兩邊平衡」而被寫成任意意見。
- 刑罰制度等爭議可以作為候選；使用者提到的「鞭刑」是題材例，不是固定必出題。採用時查明司法管轄區與「公共討論／提案／通過／已施行」狀態，不能把倡議當現行法，或把外國規則直接套到本地。只考課綱內的人權、法律保留、比例原則、程序或證據推論等適切概念；題目須提供超出課綱的必要背景，不要求專業刑法知識、感官刺激描述或受刑影像。

## Source and task ecology

Build source candidates from multiple families: historical primary and secondary sources, archives, maps, aerial/satellite images, photographs, artifacts, statistical charts, open data, laws/judgments, policy documents, research, news used with a primary source, literature, and authentic life documents. Avoid repeating the same newspaper-summary-plus-definition pattern.

For every competence item, record:

- `orientation: competence`, primary/secondary domain, and curriculum codes;
- `source_family`, `source_ids`, dates, rights and fact-check status;
- exact `evidence_targets` and `reasoning_operations`;
- `stimulus_required: true`, `stimulus_removal_test: fail_without_stimulus`, and `external_knowledge_required: false`;
- current-context items: `editorial_lock_date`, `published_at`, and `proper_noun_substitution_test: mechanism_changes`;
- a rubric evidence unit for every constructed response.

For **every** scored item, including `orientation: basic`, also record `social_reasoning_contract` with `recall_only: false`, `core_curriculum_anchor`, `curriculum_centrality`, an allowed non-recall `cognitive_demand`, and at least two `reasoning_operations`. The material or scenario dependency must identify what evidence, relation, constraint, or procedure prevents the item from collapsing into one-line definition recall.

Run:

```text
python scripts/validate_social_item_design.py EXAM_JSON --report REPORT_JSON
```

The validator checks metadata and evidence contracts. It does not replace solving the item, legal/date verification, or human review for contested interpretations.

## Distractors and constructed responses

Social-studies distractors should be reasonable claims defeated by a specific flaw: wrong time/space, reversed causality, overgeneralization, evidence-source mismatch, category confusion, legal hierarchy error, denominator error, or an unsupported value judgment. Avoid three absurd choices around one textbook phrase.

After the final option order is frozen, audit the complete selected-response key rather than checking items one at a time. For the four-option full-paper single-choice population, all A–D positions must occur and the largest and smallest counts may differ by at most one; also reject four identical answers in succession or a short mechanical cycle repeated three times. This is a product regression gate, not a claimed CEEC quota and not a reason to change item truth. If options are reordered, remap the key, the independent solve, every option verdict, every label mentioned in the explanation, and any distractor/lexical binding; then recompute all content and answer hashes and re-render both PDFs. A balanced count by itself does not prove randomness or distractor quality.

Constructed responses must state the evidence units and permissible equivalents before prose is written. The prompt should bound length and response form exactly as the selected official profile does. Score evidence selection, interpretation, comparison, or justification; do not reward generic opinion unsupported by the supplied material.

## Visual evidence and grayscale photographs

Maps, tables, charts, timelines, document fragments, aerial images, artifacts, and real photographs are central evidence forms. Real photos may be used only with traceable rights and provenance. Convert to grayscale only after identifying the answer-bearing features.

Keep photograph credit, license, crop, and transformation records in the internal provenance ledger. Do not print a photo-source credit in the student question booklet unless the selected official profile explicitly places one there. This does not remove the obligation to print a textual material/source attribution when that attribution is part of the selected profile.

Every visual item must pass the color-independence and evidence-survival tests in [visual-generation.md](visual-generation.md). A question about color is invalid after monochrome conversion unless the decisive categories are redundantly encoded by labels, shape, pattern, position, or measured value. Do not repair a failed image by relying on the answer explanation.

Pending complete item-level annotation, a full internal Social Studies paper must contain at least six answer-bearing visuals across both objective and mixed parts, with at least three visual kinds and visual evidence serving history, geography, and civics. A map, chart, timeline, document fragment, photograph, or artifact counts only when removing it changes the evidence search or reasoning. If the floor is missed, replace the text-only item with a newly designed visual mechanism and re-solve it; an ornamental skyline, portrait, flag, or map silhouette does not count.

For a more visual-rich new paper, use **8–10 independent answer-bearing visual materials and at least four kinds as the planning target**, not a measured CEEC quota or a rigid maximum. The existing six-visual / three-kind release floor remains a minimum, not the drafting target; also retain the shared requirement for at least two traceable real photographs or authentic observation/archival images. If source quality, the controlling layout or realistic solving time prevents the higher target, explain the trade-off in the existing editorial review rather than silently stopping at the floor. Do not grow the official item count or squeeze type to fit more images.

Prefer a purposeful mix of photographs/artifacts, maps or remote images, charts, timelines and source-document images across the three disciplines and both parts. Do not fill the increase solely with text tables or screenshots of paragraphs. Count one shared image once in the material inventory, separately from the number of questions using it; duplicated crops and recolored copies are not new evidence. Require students to observe, compare or integrate something actually visible with a curriculum concept, rather than identify a place/person by memory. Preserve a sensible mix of text-only and visual items.

Accurate maps, graphs and schematic relationships may be self-drawn from verified semantic data. Image models may supply non-exact context only, never fabricate a purported news photograph, historical artifact, empirical pattern or answer-bearing boundary. Freeze the final grayscale version, check it at printed size and re-solve from it; keep labels, patterns, line styles and contrast readable without color. The political-neutrality review applies to the images as well as their captions. Record the adopted visual count, kinds and evidence-removal findings in the existing literacy/layout review; a machine count alone does not establish visual quality or neutrality.

## Layout contract

Current official papers use a cover plus densely composed one-column A4 body pages, running page/total-page and subject/year headers, a centered signature reminder, and bottom page number. The 115 paper has nineteen numbered body pages plus the cover. The part heading and bordered instruction line appear once at the part start, not after every page break.

For the measured 115 role, odd-numbered inner pages place `第 n 頁／共 N 頁` at left and the year plus `社會考科` at right; even-numbered inner pages swap those outer blocks. The centered gray strip reads `請記得在答題卷簽名欄位以正楷簽全名`, and the footer contains only the official-style `- n -` page number on the outer side. Here `N` is the actual number of inner pages in the generated student booklet, excluding the cover—not the reference value 19 and not `target_page_count - 1` unless that is what was really rendered. Do not print `第三份`, a profile id, source hash, calibration status, internal audit trace, or teacher label in the student-page header/footer.

The 20-page count describes that administration. Preserve its PMingLiU/MingLiU body role at approximately 11.04 pt, the DFKai-SB instruction role, printable width, line pitch, and option spacing; never reduce them to fit a new 20-page target. New material may flow to more pages. Remove artificial breaks and orphan headings, then compare every resulting page with the closest official page role. Matching 20 pages with smaller glyphs or thinly written material is a layout failure.

Options are normally stacked beneath the stem. Figures sit close to the exact paragraph or question that invokes them and use sequential labels (`圖`, `表`, `照片`) with captions. Mixed groups may include bordered answer-format tables that describe what belongs on the separate answer sheet; reproduce their cell sizes, word limits, and checkboxes only when present in the selected profile. Never add generic ruled lines to every constructed item.

For the measured 115 terminal mixed-item role, the supported device is a captioned bordered inference/completion table whose labeled slots are part of the question. A new table must likewise give every row a scoring or reasoning function, be represented as structured `response_format_table` content, and be covered by the question content hash. It must not be a blank grid, an unlabeled writing box, or a layout filler.

The measured question row uses an Arabic number plus period in a narrow hanging column at the body-left edge, with the prompt beginning at a stable prose-column inset; wrapped prompt and option lines align with their own text column rather than the number or option label. Objective items do not repeat a right-edge score because the section instruction gives the common two-point value. A constructed-response score appears once in the wording/position supported by the selected page role—never once inline and again at the right margin.

The 115 student booklet sends constructed responses to the separate answer sheet. Therefore a new full-paper Social Studies question booklet must not render generic `answer_space_lines`; it may render only a specifically profiled response-format table, graphing frame, checkbox, or other answer device whose same-role official geometry has been measured. In particular, do not append three horizontal lines below the last constructed response simply because the page has room.

Pagination must protect maps, captions, legends, question continuations, and response-format tables from clipping or separation. Rasterize every page in grayscale and inspect at target print size before release.

Use keep-together only for a short block that actually fits in the remaining measured body area. A long shared stimulus may split at a paragraph or semantic boundary with widow/orphan protection, as current official papers do; do not push an entire long group to the next page and create a large blank lower half. Keep the group label with meaningful following material and keep each question with its own options.

An explicit `page_break_before` in Social Studies must carry a `page_break_basis` naming the measured official page role or a necessary figure/table containment reason. Ignore or reject an ungrounded manual break; it may not be used to make a page count look tidy while leaving the preceding page half empty.

When a long final shared stimulus would otherwise fill the penultimate page but leave only a short question block on the last page, divide it only at an existing sentence or paragraph boundary. Both fragments must retain meaningful evidence, and the latter fragment may be kept with the first question that uses it. Never split inside a sentence, repeat the group label, move answer-bearing evidence away from its questions, or manufacture response lines to fill the last page.

Run `scripts/validate_reference_page_density.py` against the selected official paper after PDF export. Overflow-free but half-empty pages fail. First restore authentic evidence and item length; then distribute the remaining small amount of white space between complete items. Do not push all unused space below the last item, stretch a single gap unnaturally, repeat headings, enlarge type, or add content-free filler merely to reach a percentage.
