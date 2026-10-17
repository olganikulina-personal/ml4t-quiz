(() => {
  const EXAM_PER_CATEGORY = 20;
  const bank = window.QUESTION_BANK;
  const $ = (id) => document.getElementById(id);
  const CAT_LABEL = { ML: "Machine Learning", QF: "Quantitative Finance (Trading)" };

  if (!bank || !Array.isArray(bank.questions)) {
    $("pool-info").textContent = "Could not load questions.js. Run parse_questions.py first.";
    $("setup").hidden = true;
    return;
  }

  const all = bank.questions;
  const counts = all.reduce((m, q) => ((m[q.category] = (m[q.category] || 0) + 1), m), {});
  $("pool-info").textContent =
    `${bank.exam} · ${all.length} questions (${Object.entries(counts).map(([k, v]) => `${v} ${k}`).join(", ")}) · 5 statements each`;

  const domainSel = $("domain");
  const domains = [...new Map(all.map((q) => [`${q.category}-D${q.domain}`, q])).values()];
  for (const q of domains) {
    const opt = document.createElement("option");
    opt.value = `${q.category}-D${q.domain}`;
    opt.textContent = `${q.category} D${q.domain}: ${q.domainName || ""}`;
    domainSel.append(opt);
  }

  document.querySelectorAll("input[name=mode]").forEach((r) =>
    r.addEventListener("change", () => ($("custom-opts").disabled = r.value !== "custom" || !r.checked))
  );

  const shuffle = (arr) => {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };

  let quiz = [], idx = 0, results = [];

  function buildQuiz() {
    const mode = document.querySelector("input[name=mode]:checked").value;
    if (mode === "all") return shuffle(all);
    if (mode === "exam") {
      const pick = (c) => shuffle(all.filter((q) => q.category === c)).slice(0, EXAM_PER_CATEGORY);
      return shuffle([...pick("ML"), ...pick("QF")]);
    }
    const cat = $("cat").value, dom = domainSel.value;
    const pool = all.filter(
      (q) => (cat === "both" || q.category === cat) && (dom === "all" || `${q.category}-D${q.domain}` === dom)
    );
    return shuffle(pool).slice(0, Math.max(1, parseInt($("count").value, 10) || 1));
  }

  function el(tag, props = {}, ...children) {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...children);
    return e;
  }

  const paragraphs = (text) => text.split("\n\n").map((t) => el("p", {}, t));

  function render() {
    const q = quiz[idx];
    $("pos").textContent = `${idx + 1} of ${quiz.length}`;
    $("qid").textContent = q.id;
    $("topic").textContent = `${CAT_LABEL[q.category] || q.category} · D${q.domain} ${q.domainName || ""} · G${q.group} ${q.groupName || ""}`;
    updateRunning();

    const inv = $("inverted");
    inv.hidden = !q.inverted;
    inv.textContent = q.inverted ? "Reversed question: mark True if the statement is INCORRECT, False if it is accurate." : "";

    $("stem").replaceChildren(...q.stem.map((p) => el("p", {}, p)));

    const form = $("form");
    form.replaceChildren(
      ...q.statements.map((s) => {
        const name = `s-${s.letter}`;
        const opt = (val, label) =>
          el("label", {}, el("input", { type: "radio", name, value: val }), el("span", {}, label));
        return el(
          "div",
          { className: "stmt", id: `stmt-${s.letter}` },
          el("div", { className: "stmt-text" }, `${s.letter}. ${s.text}`),
          el("div", { className: "tf", role: "radiogroup", ariaLabel: `Statement ${s.letter}` }, opt("T", "True"), opt("F", "False"))
        );
      })
    );
    const keyHeader = el("p", { className: "key-header", id: "key-header", hidden: true }, q.answerKeyHeader);
    form.prepend(keyHeader);

    $("submit").hidden = false;
    $("next").hidden = true;
    form.querySelector("input")?.focus();
  }

  function submit() {
    const q = quiz[idx];
    const form = $("form");
    let correct = 0, graded = 0;
    for (const s of q.statements) {
      const chosen = form.querySelector(`input[name=s-${s.letter}]:checked`)?.value;
      const box = $(`stmt-${s.letter}`);
      box.querySelectorAll("input").forEach((i) => (i.disabled = true));
      let cls, head;
      if (s.answer === null) {
        cls = "na";
        head = "Not graded - answer missing in source";
      } else {
        graded++;
        const user = chosen === undefined ? null : chosen === "T";
        const ok = user === s.answer;
        if (ok) correct++;
        cls = ok ? "ok" : "bad";
        const ans = s.answer ? "True" : "False";
        head = ok ? `✓ Correct - ${ans}` : `✗ ${user === null ? "Unanswered" : "Incorrect"} - answer is ${ans}`;
      }
      const res = el("div", { className: `result ${cls}` }, el("strong", {}, head), ...paragraphs(s.explanation || ""));
      if (s.note) res.append(el("div", { className: "note" }, `⚠ ${s.note}`));
      box.append(res);
    }
    $("key-header").hidden = false;
    results.push({ id: q.id, correct, graded });
    updateRunning();
    $("submit").hidden = true;
    $("next").hidden = false;
    $("next").textContent = idx + 1 < quiz.length ? "Next question" : "See results";
    $("next").focus();
  }

  function updateRunning() {
    const c = results.reduce((a, r) => a + r.correct, 0);
    const g = results.reduce((a, r) => a + r.graded, 0);
    $("running").textContent = g ? `${c}/${g} statements correct (${Math.round((100 * c) / g)}%)` : "";
  }

  function showSummary() {
    $("quiz").hidden = true;
    $("summary").hidden = false;
    const c = results.reduce((a, r) => a + r.correct, 0);
    const g = results.reduce((a, r) => a + r.graded, 0);
    const perfect = results.filter((r) => r.graded && r.correct === r.graded).length;
    const missed = results.filter((r) => r.correct < r.graded);
    const body = $("summary-body");
    body.replaceChildren(
      el("p", { className: "score" }, g ? `${c}/${g} statements correct (${Math.round((100 * c) / g)}%)` : "No questions submitted."),
      el("p", {}, `${perfect} of ${results.length} questions fully correct.`)
    );
    if (missed.length) {
      body.append(
        el("p", {}, "Questions with mistakes:"),
        el("ul", { className: "missed" }, ...missed.map((r) => el("li", {}, `${r.id} - ${r.correct}/${r.graded}`)))
      );
    }
    $("restart").focus();
  }

  $("start").addEventListener("click", () => {
    quiz = buildQuiz();
    idx = 0;
    results = [];
    if (!quiz.length) {
      alert("No questions match those filters.");
      return;
    }
    $("setup").hidden = true;
    $("summary").hidden = true;
    $("quiz").hidden = false;
    render();
  });
  $("submit").addEventListener("click", submit);
  $("next").addEventListener("click", () => (++idx < quiz.length ? render() : showSummary()));
  $("finish").addEventListener("click", showSummary);
  $("restart").addEventListener("click", () => {
    $("summary").hidden = true;
    $("setup").hidden = false;
  });
})();
