---
name: unslop
description: Cut AI tells from any writing without weakening technical or scientific meaning. Preserve evidence, citations, numbers, uncertainty, scope, and claim strength. Use whenever drafting or revising prose, including engineering documentation, papers, theses, reports, literature reviews, peer reviews, rebuttals, proposals, research notes, abstracts, methods, results, discussions, and conclusions. Must always apply.
---

# Unslop

Edit text to remove AI patterns and add human voice.

## Process

1. Scan for the patterns below.
2. Rewrite. Preserve meaning, match intended tone.
3. Add soul (see next section).
4. Self-audit: "What makes this obviously AI generated?" Fix remaining tells.

## Adding soul

Removing patterns is half the job. Sterile, voiceless writing is just as obvious.

- **Have opinions.** React to facts instead of neutrally listing pros and cons.
- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.
- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."
- **Use "I" when it fits.** First person isn't unprofessional.
- **Let some mess in.** Perfect structure looks machine-made.
- **Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am."

## Patterns to detect and fix

### Content

1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". Cut puffery, state what happened.
2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.
3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.
4. **Promotional language.** "nestled", "vibrant", "breathtaking", "groundbreaking", "renowned", "stunning", "must-visit". Use neutral descriptions.
5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.
6. **Formulaic challenges.** "Despite challenges... continues to thrive." Replace with specific facts.

### Language

7. **AI vocabulary.** Additionally, crucial, delve, enduring, enhance, fostering, garner, interplay, intricate, landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore, vibrant. Replace with plain words.
8. **Fancy ways to say "is".** "serves as", "stands as", "boasts", "features". Just say "is" or "has".
9. **"Not just X, but Y."** State the point directly instead.
10. **Rule of three.** Forcing ideas into groups of three. Use the natural number.
11. **Synonym cycling.** Protagonist, main character, central figure, hero all in one paragraph. Pick one, repeat it.
12. **False ranges.** "from X to Y" where X and Y aren't on a meaningful scale. List topics directly.

### Style

13. **Em dash overuse.** Avoid em dashes entirely. Use periods or commas only (no parentheses, no en dashes, no hyphen-as-dash substitutes). Em dashes are an AI tell, and reaching for parentheses instead just trades one tell for another. If a thought needs separation, end the sentence or use a comma.
14. **Colon overuse.** Colons are fine before a list or example. Not as mid-sentence connectors. "If you're coming from traditional automation: instead of registering event handlers, you describe conditions" adds nothing with the colon. Rewrite to let the point stand on its own without comparison framing. "Describing when the scheduler should fire works best as plain English." Same meaning, no crutch punctuation.
15. **Boldface overuse.** Don't bold every proper noun or acronym.
16. **Inline-header lists.** The tell is a bold label and colon that restates the line: "**Performance:** Performance improved...". Convert those to prose. A bold lead-in that ends in a period, names the item, and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one file.") is fine, not a tell.
17. **Title case headings.** Use sentence case.
18. **Decorative emojis.** Remove from headings and bullets.
19. **Curly quotes.** Replace with straight quotes.

### Communication artifacts

20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.
21. **Cutoff disclaimers.** "While specific details are limited..." Find sources or remove.
22. **Sycophantic tone.** "Great question! You're absolutely right!" Respond directly.

### Filler

23. **Filler phrases.** "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
24. **Excessive hedging.** "could potentially possibly be argued that it might" becomes "may".
25. **Generic conclusions.** "The future looks bright." State specific plans or facts.

### Jargon

26. **Abstract metaphor nouns.** Substrate, wedge, vector, locus, vantage, nexus, primitive (as noun), harness (as metaphor), surface (as in "API surface"), bedrock, scaffolding (as metaphor), modality, paradigm, gold-plating, ratchet (as metaphor), evacuate (for moving code), endgame, north star, flywheel. These read as technical but usually have a plainer concrete word. "Substrate" becomes "base". "Wedge in" becomes "add". "Vector" becomes "way" or "method". "Gold-plating" becomes "more than the job needs". "Ratchet" becomes the mechanism's real name or "a limit that only tightens". "Evacuate" becomes "move out". "Endgame" becomes "the last phase". Pick the concrete word.

### Plain speech

27. **Say what it does, not how it feels.** "the database stays close at hand", "SQL you can read", "types that follow your schema" name a feeling. The fix names the mechanism or a number: "`.toSQL()` returns the exact string sent to the database", "a column rename fails the build". Ask what the sentence tells the reader to do or know, then write that. If you can't restate it as a concrete instruction, fact, or number, cut it. One more check: if the sentence could appear unchanged in another project's docs, it says nothing about this one. Cut it.
28. **Shorten or split dense sentences.** If the reader has to backtrack to parse a sentence, break it in two or drop clauses. One idea per sentence.
29. **Active voice.** Prefer it. Catch "is/are/was/were + past participle" and name the actor: "queries are validated" becomes "the compiler validates queries", "the file is parsed by the loader" becomes "the loader parses the file". Passive is fine only when the actor is unknown or genuinely doesn't matter.
30. **Cut adverbs, or use a stronger verb.** "runs quickly" becomes "is fast" or the number. "significantly improves" becomes the measured delta. An adverb propping up a weak verb means the verb is wrong.
31. **Prefer the plain word.** "utilize" becomes "use", "leverage" becomes "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if". The fancier synonym is rarely clearer.

## Research writing

Apply this section before the generic preferences above whenever the text reports, interprets, reviews, or proposes research. Research integrity takes priority over stylistic cleanup. Do not make prose sound more human by making it less accurate.

### Protect the scientific content

- Preserve the meaning and epistemic strength of every claim.
- Preserve citations, citation keys, quotations, numbers, units, equations, symbols, statistical results, and confidence language unless correcting a confirmed error.
- Preserve the distinction between observation, result, interpretation, hypothesis, and speculation.
- Preserve the population, dataset, device, task, experimental setting, and assumptions that bound a claim.
- Preserve precise technical terms. Replace decorative jargon, not vocabulary that carries domain meaning.
- Follow the requested venue, discipline, and document conventions when they conflict with generic style preferences.
- Never invent a citation, fact, result, mechanism, limitation, methodological detail, or source-backed interpretation.
- Flag a factual or citation problem instead of silently repairing it when the evidence is unavailable.

Parentheses are valid for citations, abbreviations, units, statistical values, and necessary qualifications. Passive voice is valid when the actor is unknown, irrelevant, or less important than the procedure or object, especially in methods. Preserve punctuation, capitalization, spelling, and notation required by a style guide or technical convention.

Interpret "add soul" as restoring an identifiable line of reasoning, concrete choices, and an honest authorial stance. Do not add emotional reactions, unsupported opinions, deliberate mess, or first person that the genre does not support. Use "I" or "we" only when it matches the authorship and venue.

### Research process

1. Identify the genre and audience: abstract, introduction, related work, methods, results, discussion, conclusion, review, rebuttal, proposal, thesis, or research note.
2. Mark protected content before editing: claims, citations, quotations, numbers, units, notation, terminology, qualifications, and scope conditions.
3. Trace each claim to its stated evidence. Keep citations attached to the claims they support.
4. Apply the generic checklist and the research patterns below. Resolve conflicts in favor of scientific accuracy.
5. Compare the revision with the source sentence by sentence. Restore any lost meaning, uncertainty, scope, or reproducibility detail.
6. Self-audit twice: "What still makes this sound AI-generated?" and "What scientific meaning did this edit change?" Fix both.

### Research patterns to detect and fix

32. **Novelty inflation.** Remove unsupported "novel", "first", "unprecedented", "groundbreaking", and "state-of-the-art" claims. Keep a novelty or priority claim only when its comparison set, scope, and evidence are explicit.
33. **Contribution boilerplate.** Replace "This work makes three key contributions" and forced contribution lists with the actual contributions. Keep a numbered list when the venue requires it or the contributions are genuinely distinct.
34. **Causal inflation.** Do not turn an association, prediction, ablation, or observational result into a causal claim. Name the design or evidence that supports causality.
35. **Generalization inflation.** Keep conclusions within the tested datasets, populations, devices, conditions, tasks, and time periods. State the boundary when readers could otherwise infer a broader claim.
36. **Uncertainty stripping.** Preserve meaningful words such as "may", "suggests", "is consistent with", and "we hypothesize". Compress redundant hedge stacks without strengthening the claim.
37. **False certainty from null results.** Do not rewrite "we found no evidence of an effect" as "there was no effect". Distinguish absence of evidence from evidence of absence, and reserve equivalence claims for an appropriate design and analysis.
38. **Statistical misstatement.** Preserve sample sizes, effect sizes, intervals, exact comparisons, multiplicity qualifications, and test assumptions. Do not alter statistical notation or convert a reported statistic into a different claim.
39. **Significance as importance.** Do not use "significant" to imply a large, useful, or practically important effect. State statistical and practical importance separately.
40. **Citation drift.** Keep each citation next to the claim it supports. Do not leave one citation to appear to support several unrelated claims or move a citation across a changed claim.
41. **Citation pileups.** Replace unexplained citation clusters with a synthesis of what the relevant sources establish, differ on, or leave unresolved. Do not drop sources merely to make the sentence cleaner.
42. **Invented evidence or precision.** Never fabricate references, paper metadata, numerical values, dataset properties, quotations, implementation details, or experimental outcomes. Preserve an explicit placeholder or flag the missing evidence.
43. **Related-work catalogues.** Avoid a paper-by-paper list when comparison by method, assumption, evidence, or disagreement would explain the literature better. Preserve source-specific differences.
44. **Method vagueness.** Replace "standard preprocessing", "appropriate parameters", "careful tuning", and similar phrases with reproducible details when the source provides them. Do not guess missing details.
45. **Reproducibility erosion.** Do not remove versions, thresholds, parameters, preprocessing steps, inclusion criteria, stopping rules, seeds, splits, or evaluation protocols merely to shorten the prose.
46. **Results and interpretation blending.** State what was measured and observed before explaining what it may mean. Do not smuggle a mechanism or judgment into a result sentence.
47. **Metric and term substitution.** Do not replace the technical name of a metric, construct, method, variable, or population with a friendlier but inaccurate synonym. Define it when the audience needs help.
48. **Anthropomorphic systems.** Replace claims that a model "understands", "knows", "believes", "wants", or "decides" with the operation or observed behavior unless the term is explicitly defined.
49. **Data or model reification.** Data do not automatically "prove" a theory, and a model is not the phenomenon it represents. State what the analysis supports under which assumptions.
50. **Unsupported mechanism stories.** Do not add a plausible explanation when the experiment establishes only an outcome. Label a proposed mechanism as a hypothesis and connect it to evidence.
51. **Generic rigor claims.** Replace "robust", "comprehensive", "rigorous", "extensive", and "thorough" with the tests, coverage, sensitivity analyses, comparisons, or quantities that justify the description.
52. **Limitation boilerplate.** Replace generic calls for larger datasets or more research with the specific threat to validity, its likely consequence, and the evidence needed to address it.
53. **Reviewer-proofing clutter.** Consolidate defensive qualifications and repeated caveats. Keep assumptions, boundary conditions, and limitations that change how the result should be read.
54. **Structural repetition.** Avoid repeating the same stock claim in the abstract, introduction, discussion, and conclusion. Give each section its own job while preserving required standalone context.
55. **Genre flattening.** Do not give every section the same voice. Keep methods reproducible, results factual, discussion interpretive, related work comparative, rebuttals direct, and abstracts compact.
56. **Inappropriate personality injection.** In formal research, express judgment through evidence selection, reasoning, and explicit interpretation. Do not add banter, emotional color, false informality, or unsupported conviction.

### Final research audit

Before returning the revision, verify that:

- Every claim is no stronger or broader than the source allows.
- Every citation still supports the claim beside it.
- Every number, unit, symbol, and statistical qualification is intact.
- No observation became a cause, mechanism, or universal conclusion.
- No method detail needed for reproduction disappeared.
- No technical term lost its precise meaning.
- The prose fits its research genre and still sounds like one author making deliberate choices.
