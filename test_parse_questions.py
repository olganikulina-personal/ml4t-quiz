import sys
import unittest
from pathlib import Path


QUIZ_DIR = Path(__file__).parent
sys.path.insert(0, str(QUIZ_DIR))

import parse_questions


EXAM_1_SOURCE = QUIZ_DIR / "ML4TExamQuestionPoolExam1.md"
EXAM_2_SOURCE = QUIZ_DIR.parent / "Exam 2" / "ML4TExamQuestionPool2.md"


class ParseQuestionsTests(unittest.TestCase):
    def test_exam_1_source_keeps_existing_question_bank_shape(self):
        questions, problems = parse_questions.parse(EXAM_1_SOURCE.read_text(encoding="utf-8"))

        self.assertEqual(len(questions), 518)
        self.assertEqual(len(problems), 2)
        self.assertTrue(all("answers appeared above the Answer Key header" in p for p in problems))
        self.assertTrue(any(q["inverted"] for q in questions))

    def test_exam_2_source_has_five_answered_statements_per_question(self):
        questions, problems = parse_questions.parse(EXAM_2_SOURCE.read_text(encoding="utf-8"))

        self.assertEqual(len(questions), 420)
        self.assertEqual({q["category"] for q in questions}, {"ML", "QF"})
        self.assertEqual(sum(q["category"] == "ML" for q in questions), 210)
        self.assertEqual(sum(q["category"] == "QF" for q in questions), 210)
        self.assertEqual(sum(len(q["statements"]) for q in questions), 2100)
        self.assertTrue(all(len(q["statements"]) == 5 for q in questions))
        self.assertTrue(all(s["answer"] is not None for q in questions for s in q["statements"]))
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
