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

This yields 50 Arabic-numbered items and 53 scored units. Text completion is selected response with a shared ten-option bank; mixed items 47–48 are free-response word blanks. The 115 discourse-structure section is one passage with four gaps and five options. Do not reuse the older two-passage arrangement when the simulated paper claims the 115-onward form.

The official 115-onward specification describes group passages of roughly 180–400 words, primarily continuous text, with diverse genres and topics and occasional images or tables. It also states that the same booklet must contain selected response, mixed response, Chinese-to-English translation, and English composition. Never split translation/composition into a separate paper or omit them from a “complete English paper.” Preserve the selected profile's grouping and task operations; do not turn every section into unrelated one-sentence blanks.

### Empirical passage-length bands

The broad 180–400-word specification is not a license to put every passage near its lower edge. Direct counts from the official 111 and 113–115 papers, cross-checked against CEEC's published 112 paper analysis, produce the following working bands for a current-form full paper. Count passage prose only—not directions, group labels, questions, or the printed option bank.

| Current-form group | Release band |
|---|---:|
| cloze 11–15 | 175–235 words |
| cloze 16–20 | 175–235 words |
| text completion 21–30 | 265–325 words |
| discourse structure 31–34 | 250–315 words |
| each reading passage (35–38, 39–42, 43–46) | 320–390 words |
| mixed stimulus 47–50 | 340–460 words |

These are current empirical layout-and-reading-load bands, not targets to hit mechanically. A passage must still have a defensible genre, rhetorical arc, and question affordances. Reject padding that merely repeats facts. If a later verified official profile changes materially, replace these bands with newly measured values and record the evidence.

## Vocabulary boundary

The CEEC specification says the paper is based mainly on the 4,500 common high-school words and points to levels 1–5 of the reference list, while allowing occasional level-6-or-higher language for authentic use. Apply that distinction as follows:

- vocabulary answers and answer-bearing alternatives: levels 1–5 only;
- at least 70% of the ten vocabulary targets: levels 1–4; use the current multi-year profile when it supplies a stronger target;
- non-reading sections: every unlisted or level-6 word must be explicitly justified as a defined term, transparent proper noun, or indispensable authentic expression; otherwise reject it;
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
- **Mixed:** combine at least two response modes and require transformation or synthesis, not sentence copying. Any supplied image, chart, notice, or map must be necessary evidence.
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

Keep a paper-level mix of humanities, social life, science/technology, environment, culture, and everyday experience. Do not let a single fashionable domain dominate. Current events are candidates, not quotas.

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

## Layout contract

The verified 115 paper has a cover plus eleven numbered body pages. Body pages use a one-column A4 frame, running page/total-page labels, the centered signature reminder, subject/year header, and bottom page number. Major section headings and their bordered instruction boxes appear once at each section start.

Those twelve physical pages describe the verified 115 reference, not permission to shrink a new paper until it fits twelve pages. Keep the measured Times New Roman body role at approximately 11.04 pt, the verified Chinese heading/instruction fonts, printable width, and line rhythm. Let new passages repaginate naturally when needed. Remove redundant forced breaks and orphaned headings before changing any typography. A candidate with twelve pages but visibly smaller text or compressed leading fails; a longer candidate may pass when its page roles, density, and typography remain faithful.

Vocabulary and cloze choices are normally one four-column row. Reading-comprehension and mixed-section choices are normally stacked one per line beneath the stem; do not reuse the vocabulary row merely because there are four alternatives. Longer choices use measured two-column or stacked arrangements. Never squeeze long alternatives into four equal cells. Passage paragraphs are justified with first-line indentation; item groups are underlined labels such as `第35至38題為題組`. Keep the question, all options, and any necessary figure together when feasible, and apply the full fixed-page overflow gate.

Render real paragraphs as paragraphs. Do not encode a blank source line between every paragraph and then preserve it with `white-space: pre-wrap`; that produces artificial vertical holes. Use one first-line indent, normal inter-paragraph spacing, and measured line height. A deliberate block document (notice, schedule, form, or table) may use compact block spacing without paragraph indentation.

The mixed section may use bordered text cards or visual panels. Grayscale photos and illustrations must pass the evidence-preservation rules in [visual-generation.md](visual-generation.md). The final non-selected page contains translation and composition prompts; do not add answer lines unless the selected official profile shows them in the question booklet.

Pending complete item-level annotation, a full internal English paper must contain at least three answer-bearing visuals across at least two sections and at least two visual kinds. Count the mixed noncontinuous material and a visual composition task only when the questions genuinely depend on them; include at least one further reading or evidence-synthesis visual when those two alone would make the paper visually predictable. All necessary English outside the reference vocabulary envelope must be locally supported. If the visual is removed and the same answer or writing task remains, replace the item rather than treating the picture as decoration.

For the verified 115 profile, the following section-level display rules are release-blocking:

- `第壹部分、選擇題` is 62 points, followed by the 10-point mixed part and 28-point non-selected part; never print 72 points for Part I.
- Cloze gaps 11–20 are numbered underlined slots inside two passages. Print each passage's four-choice rows together after that passage; do not repeat ten standalone prompts such as “Choose the best answer for blank.” Both cloze groups occupy the same official-style body page when the measured profile does.
- Text completion prints the passage first with ten numbered underlined slots, then exactly ten lettered options for ten gaps. Each option is used once. Do not prepend a worksheet word bank, invent two unused options, or repeat ten `Blank (...)` rows.
- Discourse structure prints one passage with four numbered underlined slots, followed by five candidate sentences. Do not print the options before the passage or repeat the gaps as standalone questions.
- An underlined group label such as `第 11 至 15 題為題組` is printed once when the passage begins. Do not add an invented `（續）` label after a page break.
- A long mixed stimulus should be split at a semantic boundary across the two verified mixed-section pages. Store the complete stimulus for content validation and explicit page segments for rendering; never print all material on the first page and leave only two short questions on the second.
- If a section heading and its bordered direction line are placed at the bottom of the preceding page in the selected profile, treat that placement as a page contract and do not repeat the heading on the next page.
- Before release, visually compare every section start, inline blank, option block, underline, paragraph rhythm, passage word count, content-used height, and page transition with the selected official profile. Reject unexplained large lower-page voids; accept planned white space only when the corresponding official page role (large evidence graphic, mixed continuation, or final writing prompt) supports it. A globally plausible English layout is not enough.
- After PDF export, run `scripts/validate_reference_page_density.py` against the verified official booklet. The mixed section must receive a genuinely useful map, chart, form, notice panel, or other noncontinuous evidence when the matching official page role depends on one; prose alone must not leave the first mixed page half empty.
