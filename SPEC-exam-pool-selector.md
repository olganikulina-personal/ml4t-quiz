# Spec: Exam 1 and Exam 2 Quiz Pools

## Objective

Extend the existing ML4T true/false quiz so the learner can choose between the
Exam 1 and Exam 2 question pools, while loading Exam 2 by default. Exam 1 must
remain available and retain the question text, answers, explanations, and
source-quality fixes already present in the app.

The Exam 2 markdown is authoritative. The import process may normalize
formatting required for parsing, but must not infer, rewrite, editorialize, or
reverse question meaning. Explicit inverted-question instructions and
answer-key values must be preserved exactly as represented by the source.

## Tech Stack

- Static HTML, CSS, and browser JavaScript
- Python 3 standard library parser
- Generated JSON and JavaScript question-bank files
- No server or third-party runtime dependencies

## Commands

Generate the preserved Exam 1 bank:

```sh
python3 quiz/parse_questions.py "quiz/ML4TExamQuestionPoolExam1.md" "Exam 1" "questions-exam1"
```

Generate the Exam 2 bank:

```sh
python3 quiz/parse_questions.py "Exam 2/ML4TExamQuestionPool2.md" "Exam 2" "questions-exam2"
```

Open the app directly:

```sh
open quiz/index.html
```

Validate parser output:

```sh
python3 -m py_compile quiz/parse_questions.py
```

## Project Structure

- `quiz/index.html` — quiz setup, pool selector, and page structure
- `quiz/app.js` — pool selection, filtering, quiz flow, and scoring
- `quiz/parse_questions.py` — source markdown parser and validation
- `quiz/questions-exam1.json` / `.js` — generated Exam 1 bank
- `quiz/questions-exam2.json` / `.js` — generated Exam 2 bank
- `quiz/README.md` — local usage and regeneration instructions

## Code Style

Keep the existing vanilla JavaScript style: small functions, direct DOM
lookups through the existing `$` helper, and no framework or build step.
Question-bank generation remains data-only:

```python
data = {"exam": exam, "source": src.name, "questions": questions}
output_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

Parser changes should accept source-layout variations only when the source
still clearly identifies the statement letter and its full text. Any
unrecognized structure must be reported as a validation problem rather than
reconstructed.

## Testing Strategy

- Parser validation must confirm the expected question count, category counts,
  five statements per question, one answer per statement, unique IDs, and no
  unreported parsing problems for both pools.
- Generated files must load from `file://` through `index.html`.
- Browser verification must confirm Exam 2 is selected by default, switching to
  Exam 1 updates the displayed pool and filters, and starting a quiz scores
  against the selected pool.
- Existing Exam 1 source-quality behavior, including explicit inverted
  questions and notes for source gaps, must remain intact.

## Boundaries

- **Always:** Preserve source wording and answer values; report parsing
  anomalies explicitly; keep Exam 1 selectable; keep direct-file opening
  functional.
- **Ask first:** Any unclear formula or question text; any answer-key mismatch
  that cannot be resolved from the markdown; adding dependencies; changing the
  quiz's scoring semantics.
- **Never:** Guess missing answers; reinterpret a question as inverted because
  it seems unusual; silently drop statements or questions; replace source
  wording with inferred or AI-generated text.

## Success Criteria

1. Exam 2 imports as 420 questions: 210 Machine Learning and 210 Quantitative
   Finance, with 2,100 total statements and a corresponding answer for every
   statement.
2. Exam 1 remains available with its existing 518-question bank and source
   corrections.
3. The quiz offers an Exam 1 / Exam 2 selector and defaults to Exam 2 on every
   fresh page load.
4. Changing the selected exam refreshes pool counts, domain choices, exam-mode
   sampling, and custom-mode filtering without stale data from the other pool.
5. No question or answer is editorialized during import; source-layout fixes
   are limited to unambiguous parsing of the existing text.
6. The app works when `quiz/index.html` is opened directly from disk.

## Open Questions

None currently. The Exam 2 source contains two formatting cases that require
parser support rather than content interpretation: two answer statements share
a source line, and one answer key is represented as a Markdown table. If any
formula or question text is found to be semantically unclear during the
implementation validation, stop and request the original PDF or clarification
before generating that content.
