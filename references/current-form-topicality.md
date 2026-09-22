# Current-form topicality: recent events, Taiwan hazards and living contexts

Read this before planning any full 自然, 社會, 英文, 國綜 or 國寫 paper. Math A/B keep
[math-current-events-and-sourcing.md](math-current-events-and-sourcing.md); 社會 keeps the
per-item dating rules in [current-gsat-social-form.md](current-gsat-social-form.md) and
`validate_social_item_design.py`. The other four subjects had no measured floor for
"how recent is a real GSAT paper", so generated papers drifted to timeless textbook
scenarios: a ROC 116 自然 paper reviewed on 2026-09-21 had zero datable contexts and
no typhoon, while the official form carries both. This reference records what the
official papers actually do and turns it into a default gate enforced by
`scripts/validate_current_context.py`.

## Measured envelope, ROC 111–115

`exam_packs/學測/shared-data/current-form-topicality-envelope.json` is the maintainer's
item-by-item reading of the supplied official booklets (2026-09-21). "Recent" means
the printed context names a real event, discovery, policy, report, product, disaster
or dataset datable to within 24 months before that January administration.

| Subject | Recent contexts per year (111→115) | Recent scored items | Where they sit | Freshness |
|---|---|---|---|---|
| 自然 | 5, 4, 1, 3, 0 (13 in five years) | 10, 12, 1, 7, 0 (10% of items) | 11 in 第壹部分, 19 in 第貳部分 | 7 of 13 are the October Nobel prizes (≈3.5 months before the exam); 康芮颱風 2.5 months |
| 社會 | 7, 7, 9, 6, 10 strict items (12%) | same | 29 objective, 19 mixed; since 114 mostly mixed | 1–23 months; 敘利亞 2024-12-08 one month before the exam |
| 英文 | 1, 0, 0, 1, 0 passage units of 20 | 3, 0, 0, 10, 0 | closing sentence of a 混合題 or 文意選填 passage | 5 months (難民奧運隊), 6 weeks (聖母院) |
| 國綜 | exactly 1 group every year | 3, 3, 3, 2, 3 (5–8%) | 第貳部分 in 111, 第壹部分 since 112 | 2–3 months (COP26, 周處除三害), up to 25 months |
| 國寫 | 0 datable tasks | — | — | trend-tied tasks in 4 of 5 years, material itself older |

Three shapes recur and are the model for generated papers:

- **自然** carries recency through a shared stimulus (Nobel result, mission, disaster warning)
  whose measurement, structure or time series the items must use; the arithmetic itself
  is timeless. Four of five years include an autumn Nobel prize.
- **英文 and 國綜** attach one recent element (a news list, a film synopsis, a side box, a
  closing sentence) to an otherwise older main text. Recency never appears through a
  printed 改寫自 year.
- **國寫 and the English composition** name a current social trend with generic wording
  (「隨著…普及」「近年來」「每逢…」) rather than one event: 颱風假, 養寵物風氣, emoji,
  AI 小幫手, 擬社會互動, 高齡出遊, 世代標籤.

### Taiwan hazards and living-context themes

The complaint "typhoons are in the news every day but never in the paper" is right for
自然 and wrong for the others:

| Theme | 自然 | 社會 | 英文 | 國綜／國寫 |
|---|---|---|---|---|
| 颱風 | 4 of 5 years (6 contexts; 康芮 2024 is the only recent one) | options or one clause in 113–115 | 112 詞彙, 114 作文 颱風假 | none |
| 地震／火山／海嘯 | 3 of 5 years (6 contexts, incl. 311 預警 in 115) | none in five years | 113 海嘯 only | one classical passage |
| 氣候／碳／能源 | 6–13 items every year | 2→13 items, rising | absent | 1–2 passages in 3 years |
| 臺灣本土地名或機構 | 3–5 items every year (mostly 地科) | 23–28 items every year | 2–3 units (詞彙, 中譯英, 作文); no reading passage | 2–4 passages every year |
| 疫情 | 1–6 items, falling since 113 | 4–6 items, 0 in 114 | one clause | 1 classical/literary echo |
| AI／科技 | 0–6 (six in 114) | 5–7 | 2–4 units | 1–3 passages |

So a 自然 paper without a Taiwan hazard context, without a climate/energy strand and with
no Taiwan place or agency is outside the official envelope even before recency is
counted. For the other subjects the typhoon is a composition or option motif, not a
required item.

## Default floors (editorial targets, not CEEC statistics)

The maintainer asked for markedly more recent material than the weakest official years,
so these floors sit at the official median or above and are stated with the official
years they would reject. They apply to every full paper by default; a user may lower
them explicitly for a themed or historical simulation.

| Subject | Floor | Official years failing it |
|---|---|---|
| 自然 | ≥ 5 verified recent sources carrying ≥ 8 scored items, in both 第壹部分 and 第貳部分; ≥ 2 sources within 180 days of the lock; ≥ 1 Taiwan hazard item (颱風／地震／豪雨／寒害 tagged `taiwan` plus the hazard); ≥ 4 items tagged `climate_energy`; ≥ 3 tagged `taiwan` | every official year on recency (111 and 112 reach 4–5 contexts, none reaches 5 sources with 8 items); none for the theme tags |
| 英文 | ≥ 2 verified recent sources carrying ≥ 6 items (passages, not vocabulary sentences); the composition prompt declares a verified `current_trend` | every official year on recency (no year has two recent passages); 111 (composition) |
| 國綜 | ≥ 2 verified recent sources carrying ≥ 4 items; ≥ 2 passages tagged `taiwan` | every official year (each has exactly one recent group) |
| 國寫 | ≥ 1 task tied to a verified `current_trend` source | 112 |
| 社會 | ≥ 6 items within the year, ≥ 2 of them within 180 days, per `validate_social_item_design.py` | every official year (about 12% strict recent items, few within six months) |

These floors were raised on 2026-09-22 after the maintainer judged the 2026-09-21 floors
(自然 4/6/120 days, 英文 1/3, 國綜 1/2, 社會 3) still too thin: the generated 自然 and 社會
papers stopped exactly at the minimum. Every floor now sits above the official range, so a
paper meeting it is deliberately more topical than any official year; the reference
disclosure above is the honest statement of that gap. Targets above the floor: 自然 6–7
contexts with 9–12 items; 英文 2–3 recent passages; 國綜 2 groups; 社會 8–10 items. Do not exceed the official share by turning the paper
into a news quiz: every recent item still passes the source-relation and removal tests in
[current-source-transformation.md](current-source-transformation.md), and the discipline,
difficulty and reading-load balances are unchanged.

"Recent" is measured from the editorial lock: event date **and** publication date within
365 days before it (`current_event`, `recent_context`), or within 730 days for a social
trend (`current_trend`). "Fresh" means within 180 days of the lock (`FRESH_DAYS`). Use Asia/Taipei calendar dates. A refreshed page date, an
anniversary retelling or a forecast of an unresolved outcome does not qualify. When the
simulated exam is dated (for example 116 學測, January 2027) but the lock is today,
today's lock still governs; never backfill later news into an earlier lock.

## Records the validator reads

```json
"metadata": {
  "current_context_plan": {
    "editorial_lock_date": "2026-09-21",
    "sources": [{
      "source_id": "cwa-typhoon-2026-08",
      "publisher": "中央氣象署", "title": "…颱風警報單…", "canonical_url": "https://…",
      "source_family": "government_data", "authority_class": "primary",
      "event_date": "2026-08-18", "published_at": "2026-08-18", "accessed_at": "2026-09-20",
      "fact_check_status": "verified", "rights_status": "facts_only_synthesis",
      "verified_facts": ["中心氣壓 …", "…"]
    }]
  }
},
"questions": [{
  "id": "q44", "number": 44,
  "item_spec": {
    "current_context": {
      "source_id": "cwa-typhoon-2026-08", "freshness_class": "current_event",
      "relation": "警報單的氣壓與風向時間序列決定登陸側判斷",
      "removal_counterfactual": "刪去序列後只能背定義，題目不可解",
      "outside_knowledge_required": false
    },
    "context_tags": ["typhoon", "taiwan", "weather_hazard"]
  }
}]
```

`context_tags` come from: `typhoon`, `earthquake`, `weather_hazard`, `climate_energy`,
`epidemic`, `space`, `taiwan`, `technology`, `society_trend`, `health`, `conflict`,
`population`, `environment`. Tag every item whose printed context genuinely belongs to
the theme, recent or not; the tag floors count themes, not news. A record with an
unverifiable date or a non-https source is not counted, and a missing `relation` or
`removal_counterfactual` fails the item. For 自然, every number in
`natural_source_ecology_plan.recent_item_numbers` must also carry a verified
`current_context`; numbers alone are not evidence.

`append_items.py` prints `current_context_progress` after every batch so the recent
items are planned while the paper is being written. `validate_current_context.py` runs
inside the release gate and the hosted final checker; it checks dates, records and
floors, not whether the source is true or whether the relation really changes the
reasoning. Those remain editorial review under
[evidence-backed-editorial-audit.md](evidence-backed-editorial-audit.md).

## How to find the material

1. Freeze the lock date first. Then run one bounded discovery pass per paper using
   primary announcements (中央氣象署, 中央地質調查所, 環境部, NASA/ESA, Nobel Foundation,
   journals, agency statistics) and a few reputable secondary reports. Where the surface
   has web access, use it; where it does not, use the frozen facts the user supplies or
   choose sources whose facts you can state with dates, and mark anything uncertain
   as pending instead of inventing a date.
2. Prefer sources that supply a measurement, a series, an image feature, a procedure or a
   constraint. A name, a headline or a prize alone is decoration and fails the
   source-relation test.
3. For 自然 plan the autumn Nobel prizes when the lock date allows, and one in-season Taiwan
   hazard (a named typhoon warning, an earthquake report, a cold surge or a rainfall
   event) as a shared stimulus with real printed data.
4. For 英文 and 國綜 write the older main text first, then add the recent element the way
   the official papers do: a closing sentence, a side box, a quoted list, a synopsis.
5. For 國寫 and the English composition choose a trend that students live inside and can
   write about from experience; source it to a real report or survey, keep the prompt's
   wording generic, and keep the affective task free of policy argument.
6. Keep publisher, URL, dates and verified facts in the internal record. Print only what
   the official form prints: 自然 stems may name the agency and date when the data need
   it; 國綜 and 英文 print no bibliography year; 國寫 prints its adapted-source note as in
   [current-gsat-writing-form.md](current-gsat-writing-form.md).
