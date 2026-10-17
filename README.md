# ML4T T/F Quiz

Open `index.html` in a browser (double-click works; no server needed).

## Files
- `questions.json` – canonical question bank (generated)
- `questions.js` – same data wrapped for `file://` loading (generated)
- `parse_questions.py` – markdown → JSON converter with validation
- `index.html`, `app.js` – the quiz UI

## Swapping in a new pool (e.g. Exam 2)
```
python3 parse_questions.py path/to/ExamQuestionPool.md "Exam 2"
```
This overwrites `questions.json` / `questions.js`. Review any "problem(s)" it prints:
statements whose answer can't be found in the source are kept but left **ungraded**
(answer `null`) rather than guessed.

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
