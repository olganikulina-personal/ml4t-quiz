#!/usr/bin/env python3
"""Parse an ML4T question-pool markdown file into generated JSON and JS banks.

Usage: python3 parse_questions.py <pool.md> [exam_name] [output_stem]

Only formatting is normalized (whitespace, HTML entities, the PDF "Ư" = "ff"
ligature). Question text, statements, answers and explanations are copied
verbatim. Anything that fails validation is reported, never guessed.
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
ID_RE = re.compile(r"^(?:#+\s*)?\[((ML|QF)(?:\d+)?-D(\d+)G(\d+)Q(\d+))\]\s*$")
PART_RE = re.compile(r"^#+\s*(Machine Learning|Quantitative Finance) - Part \d+\s*$")
DOMAIN_RE = re.compile(r"^#+\s*Domain (\d+):\s*(.+)$")
GROUP_RE = re.compile(r"^#+\s*G(\d+):\s*(.+)$")
KEY_RE = re.compile(r"^(?:#+\s*)?Answer Key\b(.*)$", re.I)
STMT_START_RE = re.compile(r"(?<!\w)([A-E])\.\s+")
ANS_RE = re.compile(r"^(True|False)\b\s*[-–—:]?\s*(.*)$", re.S)
INVERT_STEM = "true if it is incorrect"
INVERT_KEY = "true = incorrect"
FORMULA_GAP = "<!-- formula-not-decoded -->"
GAP_TEXT = "[formula not rendered in source]"
UNVERIFIED = "[unverified formula:"


def clean(s):
    s = html.unescape(s).replace("Ư", "ff").replace("\\_", "_").replace(FORMULA_GAP, GAP_TEXT)
    s = re.sub(r"!\[[^\]]*\]\(data:image/[^)]*\)", GAP_TEXT, s)
    return re.sub(r"[ \t]+", " ", s).strip()


def statement_chunks(line):
    """Return unambiguously lettered statement chunks found on one source line."""
    s = line.strip()
    s = re.sub(r"^#+\s*", "", s)
    s = re.sub(r"^[-*]\s+", "", s)
    if s.startswith("|"):
        s = s[1:].lstrip()
    if s.endswith("|"):
        s = s[:-1].rstrip()
    matches = list(STMT_START_RE.finditer(s))
    if not matches or matches[0].start() != 0:
        return []
    letters = [m.group(1) for m in matches]
    if letters != sorted(letters) or len(set(letters)) != len(letters):
        return []
    return [
        (letter, s[start:end].strip())
        for letter, start, end in zip(
            letters,
            (m.end() for m in matches),
            [m.start() for m in matches[1:]] + [len(s)],
        )
    ]


def is_table_separator(line):
    return bool(re.fullmatch(r"\|?[\s|:-]+\|?", line.strip()))


def lettered_items(lines):
    """Return [(letter, text)] while preserving continuation lines and paragraphs."""
    items = []
    for ln in lines:
        s = ln.strip()
        chunks = statement_chunks(s)
        if chunks:
            for letter, text in chunks:
                items.append([letter, [text]])
        elif is_table_separator(s):
            continue
        elif items:
            items[-1][1].append(GAP_TEXT if s == FORMULA_GAP else s)
    out = []
    for letter, parts in items:
        paras, cur = [], []
        for part in parts:
            if part:
                cur.append(part)
            elif cur:
                paras.append(clean(" ".join(cur)))
                cur = []
        if cur:
            paras.append(clean(" ".join(cur)))
        out.append((letter, "\n\n".join(paras)))
    return out


def parse(md_text):
    part = domain = group = None
    blocks, cur = [], None
    for ln in md_text.splitlines():
        s = ln.strip()
        if m := PART_RE.match(s):
            part = "ML" if m.group(1).startswith("Machine") else "QF"
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if m := DOMAIN_RE.match(s):
            domain = clean(m.group(2))
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if m := GROUP_RE.match(s):
            group = clean(m.group(2))
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if m := ID_RE.match(s):
            if cur:
                blocks.append(cur)
            cur = {"m": m, "part": part, "domain": domain, "group": group, "lines": []}
            continue
        if cur is not None:
            cur["lines"].append(ln)
    if cur:
        blocks.append(cur)

    questions, problems = [], []
    for b in blocks:
        m = b["m"]
        qid = m.group(1)
        body = b["lines"]
        key_idx = next((i for i, l in enumerate(body) if KEY_RE.match(l.strip())), None)
        if key_idx is None:
            problems.append(f"{qid}: no Answer Key line")
            continue
        key_header = clean(body[key_idx].lstrip("#"))
        pre, post = body[:key_idx], body[key_idx + 1:]

        first_stmt = next((i for i, l in enumerate(pre) if statement_chunks(l)), None)
        if first_stmt is None:
            problems.append(f"{qid}: no lettered statements")
            continue
        stem_paras, para = [], []
        for l in pre[:first_stmt]:
            t = l.strip()
            if t.startswith("- ") and para:
                stem_paras.append(clean(" ".join(para)))
                para = []
            if t:
                para.append(t)
            elif para:
                stem_paras.append(clean(" ".join(para)))
                para = []
        if para:
            stem_paras.append(clean(" ".join(para)))
        stem_paras = [re.sub(r"^-\s+(?:\uf0b7\s*)?", "• ", p) for p in stem_paras]

        s_items = lettered_items(pre[first_stmt:])
        a_items = lettered_items(post)
        # Layout quirk: answer lines placed above the "Answer Key" header.
        s_letters = [x[0] for x in s_items]
        if not a_items and s_letters.count("A") == 2:
            split_at = s_letters.index("A", 1)
            if all(ANS_RE.match(t) for _, t in s_items[split_at:]):
                s_items, a_items = s_items[:split_at], s_items[split_at:]
                problems.append(f"{qid}: note - answers appeared above the Answer Key header (handled)")
        s_order, a_order = [x[0] for x in s_items], [x[0] for x in a_items]
        stmts, answers = dict(s_items), dict(a_items)

        letters = list("ABCDE")
        if s_order != letters:
            problems.append(f"{qid}: statements are {s_order}, expected A-E")
        if a_order != letters:
            missing = [L for L in letters if L not in answers]
            problems.append(f"{qid}: answer key in source is missing {missing} - left ungraded")

        inv_stem = INVERT_STEM in " ".join(stem_paras).lower()
        inv_key = INVERT_KEY in key_header.lower()
        if inv_stem != inv_key:
            problems.append(
                f"{qid}: inverted-instruction mismatch (in stem: {inv_stem}, "
                f"in answer key header: {inv_key}) - flagged for review"
            )

        statements = []
        for L in letters:
            if L not in stmts:
                continue
            st = {"letter": L, "text": stmts[L], "answer": None, "explanation": ""}
            if L in answers:
                am = ANS_RE.match(answers[L])
                if am:
                    st["answer"] = am.group(1) == "True"
                    st["explanation"] = am.group(2).strip()
                else:
                    problems.append(f"{qid}.{L}: answer doesn't start with True/False: {answers[L][:60]!r}")
            if st["answer"] is None:
                st["note"] = "Answer missing from the source markdown - check the original PDF."
            else:
                notes = []
                both = st["text"] + st["explanation"]
                if UNVERIFIED in both:
                    notes.append("Formulas marked 'unverified' came from a non-verbatim paste, not the PDF.")
                if GAP_TEXT in both:
                    notes.append("A formula was lost when the PDF was converted - check the original PDF.")
                if notes:
                    st["note"] = " ".join(notes)
            statements.append(st)

        q = {
            "id": qid,
            "category": m.group(2),
            "domain": int(m.group(3)),
            "domainName": b["domain"],
            "group": int(m.group(4)),
            "groupName": b["group"],
            "stem": stem_paras,
            "inverted": inv_stem or inv_key,
            "answerKeyHeader": key_header,
            "statements": statements,
        }
        if inv_stem != inv_key:
            q["needsReview"] = "Inverted instruction appears in only one of: question stem / answer key header."
        if b["part"] and b["part"] != q["category"]:
            problems.append(f"{qid}: ID prefix {q['category']} is under a {b['part']} section")
        questions.append(q)

    ids = [q["id"] for q in questions]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"{d}: duplicate ID")
    return questions, problems


def main():
    src = Path(sys.argv[1])
    exam = sys.argv[2] if len(sys.argv) > 2 else "Exam 1"
    output_stem = sys.argv[3] if len(sys.argv) > 3 else "questions"
    questions, problems = parse(src.read_text(encoding="utf-8"))
    data = {"exam": exam, "source": src.name, "questions": questions}

    output_json = HERE / f"{output_stem}.json"
    output_js = HERE / f"{output_stem}.js"
    output_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # Same data wrapped as JS so index.html works when opened directly from disk (file://).
    output_js.write_text(
        "window.QUESTION_BANKS = window.QUESTION_BANKS || {};\n"
        f"window.QUESTION_BANKS[{json.dumps(exam)}] = "
        + json.dumps(data, ensure_ascii=False)
        + ";\n"
        f"window.QUESTION_BANK = window.QUESTION_BANKS[{json.dumps(exam)}];\n",
        encoding="utf-8",
    )

    by_cat = {}
    for q in questions:
        by_cat[q["category"]] = by_cat.get(q["category"], 0) + 1
    print(f"Parsed {len(questions)} questions {by_cat}; "
          f"{sum(q['inverted'] for q in questions)} inverted; "
          f"{sum(len(q['statements']) for q in questions)} statements; "
          f"{sum(s['answer'] is None for q in questions for s in q['statements'])} ungraded; "
          f"{sum('note' in s for q in questions for s in q['statements'])} with notes")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)


if __name__ == "__main__":
    main()
