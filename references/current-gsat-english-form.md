# Current GSAT English form and lexical design

Read this reference for current-form GSAT English analysis, generation, or rendering. The controlling scope document is the CEEC **115-onward English examination specification**; the CEEC 111-onward vocabulary list is a reference boundary, not a difficulty scale.

## Current paper contract

Select an exact verified Paper Profile. The verified 115 profile has 100 minutes and 100 points:

| Part | Section | Numbered items | Score |
|---|---|---:|---:|
| selected response | vocabulary | 1–10 | 10 |
| selected response | cloze | 11–20 | 10 |
| selected response | text completion | 21–30 | 10 |
| selected response | discourse structure | 31–34 | 8 |
| selected response | reading | 35–46 | 24 |
| mixed | mixed group | 47–50 | 10 |
| non-selected | Chinese-to-English translation | two separately scored sentences (4 points each) | 8 |
| non-selected | English composition | one scored unit | 20 |

This yields 50 Arabic-numbered items and 53 scored units. Items 1–20 print their four options four abreast, or two by two at the half-width tab when one overruns its 120 pt tab (115: 17, 20); the renderer decides this from the measured widths and never stacks them one per line unless even two abreast overflow. Reading and mixed items (35 onward) stack. Text completion is selected response with a shared ten-option bank; mixed items 47–48 are free-response word blanks. The 115 discourse-structure section is one passage with four gaps and five options. Do not reuse the older two-passage arrangement when the simulated paper claims the 115-onward form.

The official 115-onward specification describes group passages of roughly 180–400 words, primarily continuous text, with diverse genres and topics and occasional images or tables. It also states that the same booklet must contain selected response, mixed response, Chinese-to-English translation, and English composition. Never split translation/composition into a separate paper or omit them from a “complete English paper.” Preserve the selected profile's grouping and task operations; do not turn every section into unrelated one-sentence blanks.

### Empirical passage-length bands

The broad 180–400-word specification is not a license to put every passage near its lower edge. Direct counts from all five official 111–115 papers, re-measured on 2026-09-21 with the same prose-only rule the validator applies (cloze 179–233, text completion 269–313, discourse structure 224–305, reading 291–376, mixed stimulus 394–473 words), produce the following working bands for a current-form full paper. Each band's lower edge sits below the shortest official passage and its upper edge above the longest, so no official passage is rejected; the earlier 250/320/460 edges had excluded the 111 discourse passage, three 111–112 reading passages and the 112 mixed stimulus. Count passage prose only—not directions, group labels, questions, or the printed option bank.

| Current-form group | Release band |
|---|---:|
| cloze 11–15 | 175–235 words |
| cloze 16–20 | 175–235 words |
| text completion 21–30 | 265–325 words |
| discourse structure 31–34 | 220–315 words |
| each reading passage (35–38, 39–42, 43–46) | 285–390 words |
| mixed stimulus 47–50 | 340–480 words |

### Item-form rules measured on 111–115 (enforced)

- Vocabulary stems 1–10 are 13–24 words (contract 12–26).
- 篇章結構 prints four candidate sentences (A)–(D) in 111–114 and five (A)–(E) in 115; never more.
- 閱讀測驗 35–46 mixes, every year, 2–4 word/reference-in-context items (refer to, closest in
  meaning, mean by, idiom), at least one global item (mainly about, purpose, what question, can we
  learn, inferred, how the author develops/concludes) and at most four "which statement is
  true / NOT" detail checks; a booklet of twelve detail checks is not the form.
- 混合題 is the same shape in 112–115 (111 used the same three task types as 47/48/49):
  - **「47-48」** is one printed item worth 4 points: a Chinese instruction (找出單詞、視句型結構需要
    做適當的字形變化、<u>每格限填一個單詞</u>（word）) closed by 「（填充題，4分）」, then one English
    summary sentence of the material holding the numbered gaps `[[47]]` and `[[48]]`. Save item 47
    with `number_display: "47-48"`, both instructions and the summary sentence in its `prompt`, and
    item 48 with `suppress_question_display: true`. Each answer is one word taken from the material,
    usually with a form change (innovation, blended; 114 entertaining, kept). Not a table lookup.
  - **49** is 「（多選題，4分）」: which of the lettered cards/posts/options satisfy a condition that
    needs the whole material. The stem never states how many are right (「which ONES」, not
    「Choose TWO」).
  - **50** is 「（簡答題，2分）」 answered with a word or phrase printed in the material that matches
    a given meaning (one of a kind, does the trick, fostering empathy); 113–115 print one ruled
    answer line under it. Not an open sentence or explanation.
  - Official scoring for each blank and 50: 完全正確 2 分；字形或拼字錯誤 1 分；空白或錯誤 0 分.
  - The whole material prints first; a table, map or card set belongs to the material and prints
    after its last paragraph, before 47-48. Never split the material with questions.
  - Never a 單選.
- 中譯英 sentences are 18–28 CJK characters each (contract 16–32) on one shared theme. They print
  `1.` in Times and the sentence in 標楷體 at 11 pt, with no score (the 說明 box already says
  每題4分). Official rubric: 每題4分，原則上每個錯誤扣0.5分，相同的錯誤只扣一次; list the target
  words and structures, not invented 2+2 semantic-block points.
- 英文作文 is picture-based every year (兩張圖, emoji, 三張圖, 對比圖, 多張圖); the 提示 is
  108–174 CJK characters (contract ≤ 220) and the composition item carries `visual_asset`. The
  prompt starts with 「提示︰」 (the 說明 box above already says 依提示寫一篇英文作文…; do not add a
  second 說明 line) and prints in 標楷體 with its lines hanging under the text, with no score. Let
  the pictures carry the details: 「描述圖片中所呈現的現象」, not a sentence that already tells the
  student what the two pictures differ in. Official rubric: 依內容、組織、文法句構、字彙拼字整體評分
  (holistic score); 字數明顯不足扣總分1分，未分段亦扣總分1分 — not an invented 8/4/6/2 split.
- Measured item-writing floors the contract enforces (111–115, 2026-09-23): at least five cloze
  items a year offer phrases or structures (had yet to develop, as such, in that, what is more), so
  a paper needs at least four; vocabulary keys mix nouns, verbs, adjectives and one adverb, so
  declare `item_spec.target_part_of_speech` on 1–10 (at least three classes, none above five);
  every word class in the 文意選填 bank has at least two members, so declare
  `item_spec.bank_parts_of_speech` on item 21 (A–J → adjective, noun, verb-base, verb-past…);
  save the bank (A)–(J) once in the passage (`group_stimulus`) and give each of 21–30 the same
  ten options A–J so its key is one of its labels (篇章結構 31–34 likewise share A–E); the bank
  prints once, never per item;
  the key of at most four reading items is the strictly longest option. Printed passages never
  say "invented data" or point at "Question 39".

The measured table is `exam_packs/學測/shared-data/subject-form-envelopes-111-115.json`.

### Whole-booklet word budget

The per-passage bands above govern passage prose. Independently, measure the
whole question booklet. Official ROC 111–115 papers print 3,321–3,550 English
words across 12 pages, distributed as follows (every English word in the
section, directions, stems and options included):

| Section | Official min–max |
|---|---:|
| 詞彙題 | 256 – 265 |
| 綜合測驗 | 487 – 535 |
| 文意選填 | 291 – 334 |
| 篇章結構 | 295 – 364 |
| 閱讀測驗 | 1,456 – 1,587 |
| 混合題 | 430 – 523 |

The floor is measured on a narrower basis than that table, because the gate
reads the authored exam record rather than the printed booklet: passages, item
stems and option text, with the cover page and the section directions excluded.
Official papers print 3,004–3,238 English words on that basis, so the release
floor is **2,553 English words**, 0.85 of the weakest year.

A paper that meets every passage band but falls short of the total has lost
material somewhere else — usually thin option text, or a 混合題 stimulus written
as a prompt rather than a source. 中譯英 and 英文作文 print Chinese directions and
are outside this count; they remain governed by the task contract below.
`validate_literacy_load.py --subject 英文` checks the total.

These are current empirical layout-and-reading-load bands, not targets to hit mechanically. A passage must still have a defensible genre, rhetorical arc, and question affordances. Reject padding that merely repeats facts. If a later verified official profile changes materially, replace these bands with newly measured values and record the evidence.

## Vocabulary boundary

The CEEC specification says the paper is based mainly on the 4,500 common high-school words and points to levels 1–5 of the reference list, while allowing occasional level-6-or-higher language for authentic use. Apply that distinction as follows:

- the list itself is the CEEC 高中英文參考詞彙表 (https://www.ceec.edu.tw/SourceUse/ce37/4.pdf, 6,474 headwords in six levels of about 1,080 each), which the maintainer identifies as the source of 詞彙題 and 文意選填 words; it ships as `exam_packs/學測/shared-data/ceec-english-vocabulary-list.json` and `validate_english_vocabulary_scope.py` now runs when a hosted batch is saved;
- measured on the official 111–115 booklets (2026-09-23): the fifty 詞彙題 answers sit at levels 1:1, 2:7, 3:11, 4:20, 5:6, 6:2 with two derived forms not in the list (supposedly, compulsory); per year 7–9 of the ten targets are at levels 1–4 and 1–3 at levels 5–6 (potentially, quest, blurring, vacancy, assaulted, randomly, consumption); distractors include 1–6 level-6 words a year; the 文意選填 bank has 2–4 words at level 4 or above and at most two words outside the list (risky, absorption, fateful);
- items 1–34 carry 1.9–3.1% off-list tokens and 2.2–5.4% level-6 tokens once proper nouns, contractions, hyphenated compounds and inflected forms are set aside; the reading passages 4.5–7.3% and 2.1–4.5%;
- contract: at least six of the ten targets at levels 1–4 and at least one at levels 5–6, at most one level-6 target and one derived off-list target; bank words from the list (≤1 unresolved) with at least two at level 4+; non-reading sections at most 5% off-list and 7% level-6 tokens, every off-list word listed for review and declarable as `allowed_proper_nouns`/`glossed_terms`; reading passages warn above 10% off-list. The earlier rules (no off-list or level-6 word outside reading, every target at most level 5, 70% at levels 1–4) rejected every official year and are retired;
- reading and mixed stimuli: an unfamiliar word may occur only when it is nonessential, glossed, or inferable from the immediate text. Never make outside vocabulary knowledge the hidden answer key;
- do not judge difficulty from a word's list level alone. CEEC states that frequency and learning difficulty are not the same.

Run:

```text
python scripts/validate_english_vocabulary_scope.py EXAM_JSON CEEC_VOCABULARY_PDF --report REPORT_JSON
```

The reference PDF is private input and is not bundled in the distributable Skill.

## Vocabulary-item construction

The opening ten items are short context sentences, not definitions. In the locally verified official 111–115 sample, their stems contain 13–25 English word tokens (mean 18.5), 80% of correct targets are levels 1–4, and the remaining 20% are level 5. In 45 of 50 items, all four options can serve the target syntactic part of speech; therefore grammatical mismatch is normally too weak for a distractor.

For each item, store `item_spec.lexical_scope` with:

- `target_word` (lemma), `target_surface_form` (the exact printed correct option), `target_pos`, and four-entry `option_pos`;
- two or more `disambiguating_evidence` cues, normally including a collocation/selectional restriction and a sentence-level semantic relation;
- exactly three structured `distractor_confusion_basis` records. Each record names the wrong option label and exact printed `surface_form`, sets `slot_feasible: true`, gives `initial_fit`, `defeating_evidence`, `plausibility_after_local_read` (`high` or `medium` for a real near miss), and one `competition_type` from `near_synonym`, `collocation`, `polysemy`, `argument_structure`, `register`, `semantic_prosody`, `word_family_or_form`, or `discourse_relation`;
- CEEC level and morphology resolution for every option.

All four choices should normally share the slot's usable part of speech. Meaning competition may exploit collocation, polysemy, argument structure, register, semantic prosody, or a familiar word used in a less familiar but in-scope sense. Controlled word-form or word-family competition may use inflectional or derivational relations only when every option remains syntactically plausible at first reading and the full sentence supplies the deciding semantic or discourse evidence; a suffix-recognition or agreement-only item is too easy and fails. Same-spelling noun/verb conversion is welcome when the sentence genuinely tests usage; it must not become a fixed yearly trick.

Reject an item when the answer follows from article choice, singular/plural form, a unique suffix, or one obviously unrelated option. Also reject four near-synonyms if the sentence supplies no decisive contextual evidence.

Do not confuse grammatical sameness with good competition. All four alternatives normally remain usable in the slot, while their meanings or usages fail for different evidence-based reasons. Across ten items, use at least five of the competition families above, including at least one word-family/form near miss, at least one near-synonym or polysemy contrast, and at least one collocation or argument-structure contrast. At least eight items must leave two plausible wrong choices after a quick local read; the broader clause relation, semantic selection, or precise collocation should resolve them. Never satisfy this mix by placing a visibly wrong part of speech beside the answer.

### Vocabulary answer binding

For every vocabulary item, the answer record must contain `lexical_explanation` with `selected_option_label`, the exact printed `selected_surface_form`, at least two `evidence_cues`, and a concise `context_fit`. The rendered `reasoning` must explicitly use that same surface form. A lemma may be added in parentheses, but an explanation may not silently replace the selected word with a different derivation or near-synonym. For example, if the printed answer is *disrupted*, writing only “the delay interrupted the plan” fails even though the idea is close; the explanation must first state why *disrupted* fits. Bind all three distractor verdicts to their exact printed forms as well.

### Higher-demand vocabulary profile

The internal product profile intentionally keeps the opening section more demanding than a generic worksheet while remaining inside levels 1–5. Each item stores `item_spec.vocabulary_challenge` with `band`, `one_cue_shortcut_rejected: true`, `surface_only_elimination: false`, `two_plausible_distractors_after_local_read: true`, a concrete `decisive_relation`, and `reviewed_against_recent_ceec: true`. At least six items depend on a cross-clause relation, no more than one is a simple anchor, and at least five are medium-hard or hard by pre-pilot design. These are internal product floors responding to repeated under-difficulty, not claims about an official fixed quota; the labels remain estimates until pilot data exist. Within the ten vocabulary items, use all A–D positions and keep the largest/smallest counts within one. Across the complete homogeneous four-option single-choice population, the same near-even rule applies; also reject four identical positions in succession or a short cycle repeated three times. This is an anti-pattern gate, not a target sequence. Reordering requires exact surface-form, distractor, explanation, independent-solve, and hash remapping before both PDFs are regenerated.

## Other sections

- **Cloze:** distribute lexical, phrase, discourse-marker, referential, syntactic, and paragraph-function decisions. The passage, not one local grammar clue, should decide a meaningful share of items.
- **Text completion:** ten options for ten gaps. Balance part of speech and semantic role so that early placements constrain later ones without reducing the task to suffix matching.
- **Discourse structure:** each option must have a plausible local attachment; global topic flow, reference chains, chronology, contrast, or cause must resolve the four placements.
- **Reading:** vary purpose, inference, reference, organization, attitude, vocabulary-in-context, evidence integration, and visual-text synthesis. Do not let every passage end in the same four question templates.
- **Mixed:** combine at least two response modes and require transformation or synthesis, not sentence copying. Any supplied image, chart, notice, or map must be necessary evidence. The three synthesis items are 47 and 48 (a word from the material transformed to fit a new summary sentence) and 49 (conditions checked across the whole material); 50 locates a phrase by its meaning. None of them is answered by reading one table cell.
- **Translation and composition:** use separate rubrics and recent official task forms. The composition prompt may use photos or other noncontinuous material; the question booklet does not become a ruled workbook. Student-facing composition directions are written in Traditional Chinese, including the minimum 120-word requirement. English may appear as authentic input, labels, names, or a quoted phrase, but not as a substitute for the Chinese task explanation.

### Whole-paper difficulty floor

The 7,000-word reference list is a scope boundary, not a source of difficulty. Raise demand through relations inside the paper:

- every numbered item records `item_spec.english_difficulty_contract` with at least two linked operations, `direct_lookup_or_copy_only: false`, `outside_vocabulary_required: false`, an evidence span, and option-specific distractor competition;
- discourse-structure, reading, and mixed items require at least three linked operations. A long passage plus a locally copied sentence is still easy and fails;
- across cloze, text completion, and discourse structure, at least twelve items must depend on cross-sentence or cross-paragraph cohesion rather than a single nearby grammar cue;
- at least eight of the twelve reading items must require cross-sentence, cross-paragraph, or text–visual evidence, and every reading group must contain a cross-paragraph or text–visual inference;
- at least three mixed items must synthesize prose with a second representation or transform evidence into a new conclusion. Direct transcription is not synthesis;
- every wrong option must be initially plausible before full context and defeated by named textual evidence. Difficulty cannot come from off-list vocabulary, rare world knowledge, malformed grammar, or three absurd distractors.

Run `scripts/validate_english_difficulty_design.py`. Its pass is structural; human review must still verify the claimed evidence spans and option competition.

Translation and composition remain the two subparts of the final non-selected section in the same English booklet. The composition must state the minimum 120-word requirement and follow one verified current task form (for example, visual comparison, letter, or guided thematic writing); it is not the separate Chinese writing paper.

The composition is not made difficult by an abrupt philosophical leap. Store `item_spec.composition_contract` with `directions_language: zh-TW`, `minimum_words: 120`, `student_accessible_context: true`, and a `prompt_coherence_review`. That review must record `status: pass`, `forced_moral_or_abstract_jump: false`, `multiple_valid_angles: true`, a concrete `task_bridge`, and, for a visual task, `visible_evidence_boundary: true`. The first and later writing moves must arise naturally from the same situation; a photograph cannot be used merely as a pretext for an unrelated moral, and students may not be required to invent supposedly visible facts. Review the prompt for authentic writing affordance, not merely grammatical correctness.

## Source ecology and originality

Find fresh source material independently after the simulated editorial lock date is set. Suitable routes include reputable news, public-interest magazines, books, museum or research pages, first-party reports, notices, correspondence, and everyday documents. A source supplies facts and discourse affordances, not wording to copy.

Create a fact ledger, close the source text, and compose a new passage with a different rhetorical sequence. A passage derived mainly by sentence-level paraphrase fails. Topic novelty alone is also insufficient: the questions must depend on relations in the newly written passage.

Keep a paper-level mix of humanities, social life, science/technology, environment, culture, and everyday experience. Do not let a single fashionable domain dominate. Current events are candidates, not quotas, but a full paper is not timeless either: the measured official form ([current-form-topicality.md](current-form-topicality.md)) places one datable recent element in the closing sentence of a 文意選填 or 混合題 passage in two of five years and ties the composition prompt to a current social trend (社群媒體, AI 小幫手, 颱風假, 養寵物) in four of five. The default floor is one verified recent passage (event within 365 days of the lock) and a composition prompt with a verified `current_trend` source; `validate_current_context.py` enforces it. Vocabulary sentences stay invented scenarios, and no reading passage needs to be recent.

### English-specific innovation gate

Apply the shared `subject_innovation_audit` to every scored task, including translation and composition. A new source, topic, proper noun, picture, vocabulary target, or option order is not sufficient. The audit's `mechanism_family` and `new_subject_mechanism` must match what the student actually does:

- vocabulary: resolve a newly constructed semantic/usage competition through decisive clause or discourse evidence, not a definition shell with replaced words;
- cloze and text completion: use a new dependency among meaning, reference, cohesion, syntax, or paragraph function; do not preserve a previous blank pattern and merely paraphrase the passage;
- discourse structure and reading: require a new rhetorical sequence, evidence conflict, reference chain, comparison, inference, or text–visual relation; a fresh passage followed by the same purpose/detail/inference template in the same order fails;
- mixed tasks: transform or synthesize evidence across response modes or representations; copying a phrase into a different answer box is not a new mechanism;
- translation: create a new bundle of meaning, register, reference, information structure, and syntactic constraints. Replacing nouns inside a canonical Chinese-to-English sentence shell fails;
- composition: create a coherent new writing decision with multiple defensible directions and a material-dependent bridge. A new photo or situation attached to a generic two-paragraph moral/reflection prompt fails.

For grouped passage items, review both the passage's rhetorical architecture and each subquestion's operation. Two questions may share the same passage but must not be near-duplicate local lookups. In `metadata.subject_innovation_review`, inspect repetition separately across vocabulary, passage-based sections, mixed tasks, translation, and composition; explicitly reject repeated question-template sequences and a paper dominated by one evidence-span or rhetorical move. Run `scripts/validate_english_difficulty_design.py`; its structural pass does not replace comparison with the printed questions.

For requests to increase recent examples, use the audited baseline and source-date
windows in `evidence-backed-editorial-audit.md`. Count verified source-dependent
passages separately from generic life-themed prose; avoid repeating one
sharing/repair/public-service theme throughout the paper. Internal sources do not
become automatic printed bibliography lines.

## Printed form catalogue, ROC 111–115 (measured 2026-09-22)

Every one of the five official booklets prints exactly these headings, in this
order, each followed by one bordered 說明 line; `validate_english_layout_contract.py`
now rejects a paper that omits or reorders any of them:

| Heading (verbatim) | Direction line | Items |
|---|---|---|
| 第壹部分、選擇題（占62分） | — | 1–46 |
| 一、詞彙題（占10分） | 說明：第1題至第10題為單選題，每題1分。 | 1–10 |
| 二、綜合測驗（占10分） | 說明：第11題至第20題為單選題，每題1分。 | 11–20 |
| 三、文意選填（占10分） | 說明：第21題至第30題為單選題，每題1分。 | 21–30 |
| 四、篇章結構（占8分） | 說明：第31題至第34題為單選題，每題2分。 | 31–34 |
| 五、閱讀測驗（占24分） | 說明：第35題至第46題為單選題，每題2分。 | 35–46 (three passages, four items each) |
| 第貳部分、混合題（占10分） | 說明：本部分共有1題組，每一子題配分標於題末。限在答題卷標示題號的作答區內作答，並以規定用筆作答。 | 47–50 |
| 第參部分、非選擇題（占28分） | 說明：本部分共有二大題，請依各題指示作答，答案必須寫在「答題卷」標示題號之作答區內，作答時不必抄題。 | — |
| 一、中譯英（占8分） | 說明：依題號將以下中文句子譯成正確、通順、達意的英文。每題4分，共8分。 | printed `1.` `2.` |
| 二、英文作文（占20分） | 說明：依提示寫一篇英文作文，文長至少120個單詞（words）。 | one 提示 |

Option labels are `(A)`–`(D)` everywhere (`(A)`–`(E)` for discourse structure,
`(A)`–`(J)` for the completion bank); a paper printed with `(1)`–`(4)` is not
the GSAT English form. Vocabulary and cloze options sit on one row of four
equal columns; when one option is long the row breaks into two columns of two
(115 items 17 and 20), never into narrow cells that wrap a single word. Reading
and mixed options are stacked one per line. Cloze passages print first, then
the five option rows `11. (A) … (B) … (C) … (D) …` together after the passage.

Measured sentence structure of the passages (prose only):

| Section | Words | Sentences | Words per sentence | Longest sentence |
|---|---:|---:|---:|---:|
| Vocabulary stem (each) | 13–24 | 1 | 13–24 | — |
| Cloze passage (each) | 180–231 | 9–13 | 15–21 | 24–53 |
| Text completion | 269–312 | 14–20 | 13–22 | 19–49 |
| Discourse structure | 224–303 | 9–16 | 17–25 | 34–58 |
| Reading passage (each) | 291–368 | 14–20 | 16–22 | 26–55 |
| Mixed stimulus | 348–467 | 16–34 | 12–22 | 32–46 |

Whole booklet: 3,333–3,548 English words on 11 body pages plus the cover; no
body page except the last of a section leaves more than a quarter of its
height empty.

The composition prompt is Chinese throughout: 說明 (the 120-word line), then
`提示：` naming a lived situation in one or two sentences, `請以此為主題，並依據下列
圖片／參照下列圖片，寫一篇英文作文，文分兩段。第一段…；第二段…`. English appears
only as a quoted topic word (emoji, AI). Pictures, when used, are drawn scenes
with captions, not stick figures, and are printed under the prompt.

Translation prints two numbered Chinese sentences `1.` `2.`, each a complete
sentence of 18–30 characters, on the same page as the composition.

### Measured counter-example: a hosted English paper reviewed on 2026-09-22

| Defect | That paper | Official 111–115 |
|---|---|---|
| Headings | 詞彙題 / 綜合測驗 … with no 第壹部分／第參部分 and no scores | the ten headings above, every year |
| Option labels | `(1)`–`(4)` for vocabulary and reading, `(A)`–`(D)` for cloze | `(A)`–`(D)` throughout |
| Option layout | two options crammed into a 120 pt cell, a single word wrapping to the next line | one four-column row |
| Vocabulary distractors | appealing／avoidable／fragile／temporary: three visibly wrong meanings | four same-POS candidates that each fit locally |
| Cloze passages | 134–150 words | 180–231 |
| Text completion | 170 words | 269–312 |
| Discourse structure | 130 words in 3 sentences (43 words each) | 224–303 words in 9–16 sentences |
| Reading | four passages of 107–134 words, three items each | three passages of 291–368 words, four items each |
| Mixed stimulus | a 50-word notice | 348–467 words with a map, cards or chart |
| Composition prompt | English paragraph, "Write a two-paragraph English composition…" | Chinese 說明 + 提示 |
| Translation labels | 中譯英 1 stacked vertically in the number column | `1.` `2.` |
| Explanations | "Choice N is the only option consistent with all grammatical and contextual clues." on 46 items | each item's own evidence |
| Pages | 13, three of them more than 40% empty | 12 |

The same paper's answer key was mechanical: vocabulary 1-4-3-2-1-4-3-2-1-4,
cloze D-A-C-B-A-D-C-B-A-D, completion A–J in order, discourse A-B-C-D, every
reading group 3-2-1-4. Official keys show no such order; a candidate who
notices the pattern answers without reading. `answer_key_patterns.py` rejects,
on every surface and for every subject: a position used four times in a row,
a period-2/3/4 cycle continuing over two full repeats plus a partial third, an
option bank keyed in label order, five consecutive answers stepping through the
labels, two item groups with the same answer sequence, and uneven position
counts (each label within one of the others). Shuffle option order after
writing, then re-derive the key; never assign the key first.

Root cause: the hosted final checker did not execute the English validators
(only the mathematics and balance checks), so none of this blocked delivery.
`hosted_subject_gates.py` now runs every subject's validators inside
`check_hosted_run.py`, and `append_items.py` reports their per-item messages
after each batch.

## Layout contract

The verified 115 paper has a cover plus eleven numbered body pages. Body pages use a one-column A4 frame, running page/total-page labels, the centered signature reminder, subject/year header, and bottom page number. Major section headings and their bordered instruction boxes appear once at each section start.

Those twelve physical pages describe the verified 115 reference, not permission to shrink a new paper until it fits twelve pages. Keep the measured Times New Roman body role at approximately 11.04 pt, the verified Chinese heading/instruction fonts, printable width, and line rhythm. Let new passages repaginate naturally when needed. Remove redundant forced breaks and orphaned headings before changing any typography. A candidate with twelve pages but visibly smaller text or compressed leading fails; a longer candidate may pass when its page roles, density, and typography remain faithful.

Vocabulary and cloze choices are normally one four-column row. Reading-comprehension and mixed-section choices are normally stacked one per line beneath the stem; do not reuse the vocabulary row merely because there are four alternatives. Longer choices use measured two-column or stacked arrangements. Never squeeze long alternatives into four equal cells. Passage paragraphs are justified with first-line indentation; item groups are underlined labels such as `第35至38題為題組`. Keep the question, all options, and any necessary figure together when feasible, and apply the full fixed-page overflow gate.

Render real paragraphs as paragraphs. Do not encode a blank source line between every paragraph and then preserve it with `white-space: pre-wrap`; that produces artificial vertical holes. Use one first-line indent, normal inter-paragraph spacing, and measured line height. A deliberate block document (notice, schedule, form, or table) may use compact block spacing without paragraph indentation.

The mixed section may use bordered text cards or visual panels. Grayscale photos and illustrations must pass the evidence-preservation rules in [visual-generation.md](visual-generation.md). The final non-selected page contains translation and composition prompts without answer lines; the only ruled line in the booklet is the one under 簡答 50, which the renderer prints for a `short_answer` item in the mixed part.

Pending complete item-level annotation, a full internal English paper must contain at least three answer-bearing visuals across at least two sections and at least two visual kinds. Count the mixed noncontinuous material and a visual composition task only when the questions genuinely depend on them; include at least one further reading or evidence-synthesis visual when those two alone would make the paper visually predictable. All necessary English outside the reference vocabulary envelope must be locally supported. If the visual is removed and the same answer or writing task remains, replace the item rather than treating the picture as decoration.

For the verified 115 profile, the following section-level display rules are release-blocking:

- `第壹部分、選擇題` is 62 points, followed by the 10-point mixed part and 28-point non-selected part; never print 72 points for Part I.
- Cloze gaps 11–20 are numbered underlined slots inside two passages. Print each passage's four-choice rows together after that passage; do not repeat ten standalone prompts such as “Choose the best answer for blank.” Both cloze groups occupy the same official-style body page when the measured profile does.
- Text completion prints the passage first with ten numbered underlined slots, then exactly ten lettered options for ten gaps. Each option is used once. Do not prepend a worksheet word bank, invent two unused options, or repeat ten `Blank (...)` rows.
- Discourse structure prints one passage with four numbered underlined slots, followed by five candidate sentences. Do not print the options before the passage or repeat the gaps as standalone questions.
- An underlined group label such as `第 11 至 15 題為題組` is printed once when the passage begins. Do not add an invented `（續）` label after a page break.
- A long mixed stimulus simply continues onto the next page at a paragraph boundary; 47-48, 49 and 50 follow the complete material (111–115 print them on the second mixed page). Do not use `group_stimulus_page_splits` to force questions between paragraphs: a hosted paper printed 47 and 48 between the third and fourth paragraphs, and another printed its chart between 47 and 48.
- If a section heading and its bordered direction line are placed at the bottom of the preceding page in the selected profile, treat that placement as a page contract and do not repeat the heading on the next page.
- Before release, visually compare every section start, inline blank, option block, underline, paragraph rhythm, passage word count, content-used height, and page transition with the selected official profile. Reject unexplained large lower-page voids; accept planned white space only when the corresponding official page role (large evidence graphic, mixed continuation, or final writing prompt) supports it. A globally plausible English layout is not enough.
- After PDF export, run `scripts/validate_reference_page_density.py` against the verified official booklet. The mixed section must receive a genuinely useful map, chart, form, notice panel, or other noncontinuous evidence when the matching official page role depends on one; prose alone must not leave the first mixed page half empty.
