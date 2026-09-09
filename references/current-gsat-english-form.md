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
| non-selected | Chinese-to-English translation | two sentences, one scored unit | 8 |
| non-selected | English composition | one scored unit | 20 |

This yields 50 Arabic-numbered items and 52 scored units. The 115 discourse-structure section is one passage with four gaps and five options. Do not reuse the older two-passage arrangement when the simulated paper claims the 115-onward form.

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

- `target_word`, `target_pos`, and four-entry `option_pos`;
- two or more `disambiguating_evidence` cues, normally including a collocation/selectional restriction and a sentence-level semantic relation;
- exactly three `distractor_confusion_basis` records explaining why each wrong option initially fits and what evidence defeats it;
- CEEC level and morphology resolution for every option.

All four choices should normally share the slot's usable part of speech. Meaning competition may exploit collocation, polysemy, argument structure, register, semantic prosody, or a familiar word used in a less familiar but in-scope sense. Same-spelling noun/verb conversion is welcome when the sentence genuinely tests usage; it must not become a fixed yearly trick.

Reject an item when the answer follows from article choice, singular/plural form, a unique suffix, or one obviously unrelated option. Also reject four near-synonyms if the sentence supplies no decisive contextual evidence.

## Other sections

- **Cloze:** distribute lexical, phrase, discourse-marker, referential, syntactic, and paragraph-function decisions. The passage, not one local grammar clue, should decide a meaningful share of items.
- **Text completion:** ten options for ten gaps. Balance part of speech and semantic role so that early placements constrain later ones without reducing the task to suffix matching.
- **Discourse structure:** each option must have a plausible local attachment; global topic flow, reference chains, chronology, contrast, or cause must resolve the four placements.
- **Reading:** vary purpose, inference, reference, organization, attitude, vocabulary-in-context, evidence integration, and visual-text synthesis. Do not let every passage end in the same four question templates.
- **Mixed:** combine at least two response modes and require transformation or synthesis, not sentence copying. Any supplied image, chart, notice, or map must be necessary evidence.
- **Translation and composition:** use separate rubrics and recent official task forms. The composition prompt may use photos or other noncontinuous material; the question booklet does not become a ruled workbook.

Translation and composition remain the two subparts of the final non-selected section in the same English booklet. The composition must state the minimum 120-word requirement and follow one verified current task form (for example, visual comparison, letter, or guided thematic writing); it is not the separate Chinese writing paper.

## Source ecology and originality

Find fresh source material independently after the simulated editorial lock date is set. Suitable routes include reputable news, public-interest magazines, books, museum or research pages, first-party reports, notices, correspondence, and everyday documents. A source supplies facts and discourse affordances, not wording to copy.

Create a fact ledger, close the source text, and compose a new passage with a different rhetorical sequence. A passage derived mainly by sentence-level paraphrase fails. Topic novelty alone is also insufficient: the questions must depend on relations in the newly written passage.

Keep a paper-level mix of humanities, social life, science/technology, environment, culture, and everyday experience. Do not let a single fashionable domain dominate. Current events are candidates, not quotas.

For requests to increase recent examples, use the audited baseline and source-date
windows in `evidence-backed-editorial-audit.md`. Count verified source-dependent
passages separately from generic life-themed prose; avoid repeating one
sharing/repair/public-service theme throughout the paper. Internal sources do not
become automatic printed bibliography lines.

## Layout contract

The verified 115 paper has a cover plus eleven numbered body pages. Body pages use a one-column A4 frame, running page/total-page labels, the centered signature reminder, subject/year header, and bottom page number. Major section headings and their bordered instruction boxes appear once at each section start.

Vocabulary and cloze choices are normally one four-column row. Reading-comprehension and mixed-section choices are normally stacked one per line beneath the stem; do not reuse the vocabulary row merely because there are four alternatives. Longer choices use measured two-column or stacked arrangements. Never squeeze long alternatives into four equal cells. Passage paragraphs are justified with first-line indentation; item groups are underlined labels such as `第35至38題為題組`. Keep the question, all options, and any necessary figure together when feasible, and apply the full fixed-page overflow gate.

Render real paragraphs as paragraphs. Do not encode a blank source line between every paragraph and then preserve it with `white-space: pre-wrap`; that produces artificial vertical holes. Use one first-line indent, normal inter-paragraph spacing, and measured line height. A deliberate block document (notice, schedule, form, or table) may use compact block spacing without paragraph indentation.

The mixed section may use bordered text cards or visual panels. Grayscale photos and illustrations must pass the evidence-preservation rules in [visual-generation.md](visual-generation.md). The final non-selected page contains translation and composition prompts; do not add answer lines unless the selected official profile shows them in the question booklet.

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
