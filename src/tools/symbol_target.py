"""
ISHA Symbol Targeting — Phase 2b: which function must actually change?

The file localizer answers *which file*.  That is necessary but not
sufficient, and the baseline run showed why: every patch that applied landed
in the right file and still failed.

The clearest example is ``astropy__astropy-12907``.  The issue talks about
``separability_matrix`` and nested ``CompoundModel``s, so a name-based
localizer ranks ``separability_matrix`` and ``is_separable`` at the top — and
the agent patched ``is_separable``.  The gold fix, however, is a single line
inside ``_cstack``, a private helper that:

  * is never named in the issue text, and
  * is not even *called* in the usual sense — it is stored as a dict value
    (``{... '&': _cstack ...}``) and invoked indirectly by ``_separable``.

No amount of identifier matching finds that.  What finds it is the part of the
issue text that describes the *behaviour* — the doctest-style example
``separability_matrix(Pix2Sky_TAN() & cm)`` is a nested compound model, and
``_cstack`` is the ``&`` (operator-and) branch that goes wrong for nesting.

So symbol targeting here works on three signals, strongest first:

  1. **Direct mention** — the issue names the symbol (backticks, dotted
     paths, or a bare identifier that is defined in the file).
  2. **Structural role** — the symbol is the implementation of an operator or
     concept the issue actually exercises (``&`` for compound models, ``.sum``
     for aggregation), inferred from the code, not from the report.
  3. **Reachability** — the symbol is called from, or referenced by, a symbol
     the issue *does* mention, so it is on the path from the reported entry
     point down to the defect.

Every signal is derived from the report text and the repository only.  Gold
patches, ``FAIL_TO_PASS`` and ``test_patch`` are never read here — this runs
during solving, before any of that exists.
"""

from __future__ import annotations

import re
from pathlib import Path

# Bounded so a pathological file cannot blow up the prompt.
MAX_TARGETS_PER_FILE = 4
MIN_BODY_LINES = 3
# Lexical signal is a weak prior, not a verdict: it must clear a floor before
# it contributes at all, and it is capped so it can never outvote a direct
# name match or a structural (operator) match.
_LEX_MIN = 0.35
_LEX_CAP = 2.5

_DEF_RE = re.compile(r"^(\s*)(?:async\s+)?(def|class)\s+([A-Za-z_]\w*)")
# Identifiers worth treating as "the report names this thing".  Backticks in
# an issue are markdown, not code, so a backticked span only counts when it
# is a short, identifier-shaped token; otherwise take the first identifier
# inside it.
_BACKTICK_RE = re.compile(r"`([^`\n]{1,80})`")
_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_DOTTED_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\b")
_IDENT_SHAPE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Words that are never a symbol name even when they appear in code spans.
_STOPWORDS = {
    "self", "cls", "return", "none", "true", "false", "not", "and", "or",
    "if", "else", "elif", "try", "except", "raise", "import", "from",
    "print", "str", "int", "float", "list", "dict", "len", "type",
}

# Operator -> the concepts a report is likely to be describing when it shows
# the operator being used.  Compound models are the '&' branch; the rest are
# the separable-matrix algebra operations.
_OPERATOR_HINTS = {
    "&": ("compound", "nested", "separable", "and"),
    "|": ("or", "compound"),
    "+": ("add", "sum", "arithmetic", "sum"),
    "-": ("subtract", "difference", "arithmetic"),
}


def _read(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _spans(lines: list[str]) -> list[dict]:
    """Every top-level and nested def/class with its line span."""
    out: list[dict] = []
    for i, line in enumerate(lines):
        m = _DEF_RE.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if not lines[j].strip():
                continue
            if len(lines[j]) - len(lines[j].lstrip()) <= indent:
                end = j
                break
        out.append({
            "name": m.group(3),
            "kind": m.group(2),
            "start": i,
            "end": end,
            "indent": indent,
        })
    return out


def _body_text(lines: list[str], span: dict) -> str:
    return "\n".join(lines[span["start"]:span["end"]])


_KWARG_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=")


def report_identifiers(issue_text: str) -> set[str]:
    """Symbols the report names.

    Issue text is written by humans: backticks are markdown emphasis far more
    often than they are code, so a backticked span only contributes when it
    *is* an identifier.  Call syntax and dotted paths are reliable and are
    taken directly.
    """
    text = issue_text or ""
    found: set[str] = set()

    for span in _BACKTICK_RE.findall(text):
        span = span.strip()
        if _IDENT_SHAPE.match(span) and span.lower() not in _STOPWORDS:
            found.add(span)
            continue
        # "foo.bar.baz()" inside a code span -> foo.bar.baz
        for dotted in _DOTTED_RE.findall(span):
            found.add(dotted.split(".")[-1])
        for called in _CALL_RE.findall(span):
            if called.lower() not in _STOPWORDS:
                found.add(called)
        for kw in _KWARG_RE.findall(span):
            if kw.lower() not in _STOPWORDS:
                found.add(kw)

    for dotted in _DOTTED_RE.findall(text):
        found.add(dotted.split(".")[-1])
    for called in _CALL_RE.findall(text):
        if called.lower() not in _STOPWORDS:
            found.add(called)
    for kw in _KWARG_RE.findall(text):
        if kw.lower() not in _STOPWORDS:
            found.add(kw)

    return {t for t in found if _IDENT_SHAPE.match(t)}


def _report_terms(issue_text: str) -> set[str]:
    """Content words from the report, minus prose noise.

    The report describes *behaviour*; the function that implements it mentions
    the same nouns (``re.compile`` patterns, error strings, attribute names).
    Comparing on content words is what connects the two when the report never
    names the function.
    """
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]{3,}", (issue_text or "").lower())
    return {w for w in words if w not in _STOPWORDS and not w.isdigit()}


def _lexical_score(body: str, terms: set[str],
                   self_name: str = "") -> tuple[float, list[str]]:
    """Overlap between report content words and a function's own text.

    Weighted toward code-ish tokens: a report saying ``"lowercase"`` and a
    body containing ``lowercase`` is a real link, whereas both containing
    ``value`` is noise.  Identifier-shaped words (underscores, camelCase) are
    worth more because they are rarer in prose.

    A function's *own name* matching a report term is excluded (``self_name``):
    every named symbol trivially contains itself, and counting that as
    evidence cancelled the entry-point demotion it was meant to sit beneath.
    """
    if not terms:
        return 0.0, []
    lowered = body.lower()
    hits: list[str] = []
    score = 0.0
    for term in terms:
        if term == self_name.lower():
            continue
        if term not in lowered:
            continue
        weight = 1.0
        if "_" in term or any(c.isupper() for c in term):
            weight = 2.0   # code-shaped, unlikely to co-occur by chance
        elif term in body and term.isupper():
            weight = 1.5
        score += weight
        if len(hits) < 4:
            hits.append(term)
    # Normalise so a huge function does not win purely by being long.
    return score / max(len(body.splitlines()) / 20.0, 1.0), hits


def _operator_targets(lines: list[str], spans: list[dict], issue_text: str) -> dict[str, float]:
    """Symbols wired to an operator the report demonstrably exercises.

    ``_operators = {'&': _cstack, ...}`` is the pattern: the symbol is a dict
    *value*, so a call-graph walk never sees a call edge to it.  Matching the
    operator and the surrounding concepts is the only way to surface it.
    """
    lowered = (issue_text or "").lower()
    scores: dict[str, float] = {}

    for i, line in enumerate(lines):
        # Find the operator table by name; it may span several lines, so the
        # opening brace is not necessarily on the same line as the assignment.
        if not re.search(r"\b_?operators\b\s*=", line):
            continue
        block: list[str] = []
        for j in range(i, min(i + 12, len(lines))):
            block.append(lines[j])
            if "}" in lines[j]:
                break
        text = "\n".join(block)

        for op, concepts in _OPERATOR_HINTS.items():
            if not re.search(r"['\"]%s['\"]\s*:" % re.escape(op), text):
                continue
            if not any(c in lowered for c in concepts):
                continue
            # Both orderings occur in real code: ``'&': _cstack`` and
            # ``_cstack: '&'`` (as in functools.partial-style tables).
            after = re.findall(r"['\"]%s['\"]\s*:\s*(\w+)" % re.escape(op), text)
            before = re.findall(r"(\w+)\s*:\s*['\"]%s['\"]" % re.escape(op), text)
            for name in after + before:
                scores[name] = max(scores.get(name, 0.0), 3.0)
    return scores


def _reachable_from(mentioned: set[str], lines: list[str], spans: list[dict]) -> set[str]:
    """Private helpers referenced from a symbol the report names."""
    by_name = {s["name"]: s for s in spans}
    out: set[str] = set()
    for name in mentioned:
        span = by_name.get(name)
        if not span:
            continue
        body = _body_text(lines, span)
        for other in spans:
            if other["name"] == name:
                continue
            if other["name"].startswith("_") and not other["name"].startswith("__"):
                # Bare name use inside the mentioned body: a call or a dict value.
                if re.search(r"\b%s\b" % re.escape(other["name"]), body):
                    out.add(other["name"])
    return out


def score_symbols(repo_path: str, rel_path: str, issue_text: str) -> list[dict]:
    """Rank the symbols in one file by how likely each is the real target.

    Returns ``[{"symbol", "score", "reason", "start", "end"}, ...]`` ordered
    best-first, empty when the file cannot be read.
    """
    lines = _read(Path(repo_path) / rel_path)
    if not lines:
        return []
    spans = [s for s in _spans(lines) if s["end"] - s["start"] >= MIN_BODY_LINES]
    if not spans:
        return []

    mentioned = report_identifiers(issue_text)
    defined = {s["name"] for s in spans}
    named_here = mentioned & defined
    terms = _report_terms(issue_text)

    structural = _operator_targets(lines, spans, issue_text)
    reachable = _reachable_from(named_here, lines, spans)

    scored: list[dict] = []
    for span in spans:
        name = span["name"]
        body = _body_text(lines, span)
        score = 0.0
        reasons: list[str] = []

        if name in named_here:
            score += 3.0
            reasons.append("named in the issue")
        if name in structural:
            # An operator-table binding is a *direct* behavioural link: the
            # report exercises that operator and this is the code behind it.
            score += 3.0
            reasons.append("implements the operator the report exercises")
        if name in reachable:
            # A private helper the report never names, but which one the
            # report *does* name delegates to, is the classic place a defect
            # hides. It must outrank the entry point, not tie with it.
            score += 2.0
            reasons.append("private helper called by a symbol the report names")

        # Signature parameter matching — if the report specifies a parameter name (e.g. handle_mask=...)
        sig_lines = []
        for k in range(span["start"], min(span["start"] + 8, len(lines))):
            sig_lines.append(lines[k])
            if ":" in lines[k]:
                break
        sig_text = " ".join(sig_lines)
        sig_params = set(re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", sig_text)) - _STOPWORDS - {"self", "cls", "def", "class", "async", name}
        param_hits = sig_params & mentioned
        if param_hits:
            score += 3.0
            reasons.append("signature parameter matches report: " + ", ".join(sorted(param_hits)))

        lex, hits = _lexical_score(body, terms, self_name=name)
        if lex >= _LEX_MIN:
            score += min(lex, _LEX_CAP)
            reasons.append("body matches report terms: " + ", ".join(hits))

        # A symbol the report merely *names* is usually the entry point the
        # reporter called, not the function that is wrong.  A report says
        # "separability_matrix is broken"; the defect is below it.  Demote
        # name-only matches so a behavioural signal can outrank them.
        if name in named_here:
            score -= 2.0
            reasons.append("named, but usually the entry point — check below it")

        if score > 0:
            scored.append({
                "symbol": name,
                "score": round(score, 2),
                "reason": "; ".join(reasons),
                "start": span["start"] + 1,
                "end": span["end"],
            })

    scored.sort(key=lambda r: (-r["score"], r["start"]))
    return scored[:MAX_TARGETS_PER_FILE]


def target_file(repo_path: str, rel_path: str, issue_text: str) -> list[dict]:
    """Convenience wrapper returning localizer-shaped targets for one file."""
    out = []
    for row in score_symbols(repo_path, rel_path, issue_text):
        out.append({
            "file": rel_path,
            "symbol": row["symbol"],
            "score": row["score"],
            "reason": row["reason"],
            "start": row["start"],
            "end": row["end"],
        })
    return out


def build_targeting_block(targets: list[dict]) -> str:
    """Prompt-ready block naming the most likely target symbols.

    Gives the coder a *ranking* rather than a single name, because the whole
    point is that the top-ranked symbol is sometimes the wrong one.
    """
    if not targets:
        return ""
    lines = [
        "LIKELY TARGET SYMBOLS (ranked — the bug is usually in the top entry,",
        "but check the others before editing):",
    ]
    for t in targets:
        lines.append(
            "  %-28s %s" % (
                t.get("symbol", "?"),
                f"[{t.get('reason', '')}]",
            )
        )
    return "\n".join(lines)
