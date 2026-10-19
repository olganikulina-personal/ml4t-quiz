# ML4T T/F Quiz

Open `index.html` in a browser (double-click works; no server needed). The app
defaults to Exam 2 and lets you switch to Exam 1 from the question-pool
selector.

## Files
- `questions-exam1.json` / `questions-exam1.js` – generated Exam 1 bank
- `questions-exam2.json` / `questions-exam2.js` – generated Exam 2 bank
- `parse_questions.py` – markdown → JSON converter with validation
- `index.html`, `app.js` – the quiz UI

## Regenerating the banks

Preserve the Exam 1 bank:

```
python3 parse_questions.py ML4TExamQuestionPoolExam1.md "Exam 1" "questions-exam1"
```

Generate the Exam 2 bank:

```
python3 parse_questions.py "../Exam 2/ML4TExamQuestionPool2.md" "Exam 2" "questions-exam2"
```

Review any "problem(s)" the parser prints. Statements whose answer cannot be
found in the source are kept but left **ungraded** (`answer: null`) rather than
guessed. The current Exam 2 source has no ungraded statements.

The optional output stem controls the generated filenames. Omitting it retains
the legacy `questions.json` / `questions.js` output behavior, but the quiz page
loads the two named bank files above.

## JSON shape
```json
{ "exam": "Exam 1", "source": "...md", "questions": [{
  "id": "ML-D1G4Q2", "category": "ML" | "QF", "domain": 1, "domainName": "...",
  "group": 4, "groupName": "...", "stem": ["paragraph", "..."],
  "inverted": true, "answerKeyHeader": "Answer Key (True = incorrect; False = accurate):",
  "statements": [{ "letter": "A", "text": "...", "answer": false,
                   "explanation": "...", "note": "optional source-quality warning" }]
}]}
```
