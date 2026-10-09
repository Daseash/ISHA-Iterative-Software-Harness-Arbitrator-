"""
ISHA Localizer — turn an issue report into a ranked list of code locations.

Hierarchy: repository -> file -> class/function -> line range.

Four retrieval signals are fused so no single one has to be right:

  seed      explicit evidence in the issue text (traceback frames, file
            paths, exception names, quoted code, identifiers)
  defs      the file that *declares* a symbol named in the issue
  lexical   BM25-style token overlap over the parsed chunks
  vector    the deterministic hashing embedder's cosine similarity

The fused score is then multiplied by a file-kind prior so documentation and
test files — which describe the bug as vividly as the source does — do not
outrank the file that has to change.  ``src.bench.loc_eval`` scores the whole
thing against the gold patches; the weights above are knobs, not facts.

Every candidate carries its per-signal scores so a human (or a later phase)
can see *why* a file was ranked where it was.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.ingestion.parser import SKIP_DIRS

# Fusion weights.  Each signal is normalised to 0..1, so these are the only
# knobs; ``src.bench.loc_eval`` measures every combination it is given.
W_SEED = float(os.getenv("ISHA_LOC_W_SEED", "0.35"))
W_BM25 = float(os.getenv("ISHA_LOC_W_BM25", "0.25"))
W_VECTOR = float(os.getenv("ISHA_LOC_W_VECTOR", "0.12"))
W_DEFS = float(os.getenv("ISHA_LOC_W_DEFS", "0.25"))
# A file the model can actually edit is worth more than the prose about it.
PRIOR_DOC = float(os.getenv("ISHA_LOC_PRIOR_DOC", "0.45"))
PRIOR_TEST = float(os.getenv("ISHA_LOC_PRIOR_TEST", "0.7"))

_TRACE_FILE_RE = re.compile(
    r'(?:File "(?P<path>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>[A-Za-z_][\w.]*))?)'
    r'|(?:File \'(?P<path_sq>[^\']+)\', line (?P<line_sq>\d+)(?:, in (?P<func_sq>[A-Za-z_][\w.]*))?)'
    r'|(?:\b(?P<path_colon>[\w./\\-]+\.(?:py|pyx|c|h|cpp)):(?P<line_colon>\d+)(?::\s*in\s*(?P<func_colon>[A-Za-z_][\w.]*))?)'
)
_MODULE_RE = re.compile(r"\b([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*){1,5})\b")
_PATH_RE = re.compile(
    r"(?<![\w/])(?:(?:[\w.\-]+/)+[\w.\-]+|\b[\w.\-]+\b)\.(?:py|pyx|pyi|js|ts|c|h|cpp|go|rs)\b"
)
_DEF_RE = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)")
_FUNC_IN_RE = re.compile(r"^\s*in\s+([A-Za-z_][\w.]*)")
_EXC_RE = re.compile(
    r"^([A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning|Fault|NotFound|Interrupt))"
)
_IDENT_RE = re.compile(r"\b([a-z_][a-z0-9_]{3,})\b")

_STOPWORDS = {
    "self", "none", "true", "false", "the", "and", "for", "with", "this",
    "that", "from", "when", "not", "does", "should", "would", "could",
    "into", "been", "have", "has", "will", "can", "may", "use", "using",
    "case", "test", "tests", "value", "values", "returns", "return",
    "error", "errors", "raise", "raises", "expected", "actual",
}


@dataclass
class IssueSeeds:
    """Everything worth seeding a search with, extracted from the issue."""

    traceback_files: list[tuple[str, int]] = field(default_factory=list)
    traceback_funcs: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    snippets: list[str] = field(default_factory=list)
    identifiers: list[str] = field(default_factory=list)
    headline: str = ""

    @property
    def strong_files(self) -> list[str]:
        """Files named directly in a traceback, in priority order (leaf frames first)."""
        out: list[str] = []
        for path, _ in reversed(self.traceback_files):
            if path not in out:
                out.append(path)
        for path in self.paths:
            if path not in out:
                out.append(path)
        return out

    @property
    def query(self) -> str:
        return " ".join(
            [self.headline] + self.symbols + self.exceptions + self.identifiers[:12]
        )


def parse_issue(issue_text: str) -> IssueSeeds:
    """Extract localization seeds from a raw issue / problem statement."""
    seeds = IssueSeeds()
    text = issue_text or ""

    for match in _TRACE_FILE_RE.finditer(text):
        path = match.group("path") or match.group("path_sq") or match.group("path_colon")
        line_str = match.group("line") or match.group("line_sq") or match.group("line_colon")
        func = match.group("func") or match.group("func_sq") or match.group("func_colon")
        if path and line_str:
            seeds.traceback_files.append((path, int(line_str)))
        if func:
            name = func.split(".")[-1]
            if name not in seeds.traceback_funcs:
                seeds.traceback_funcs.append(name)
            if name not in seeds.symbols:
                seeds.symbols.append(name)

    # Dotted module candidates (e.g. django.db.models.fields -> django/db/models/fields.py)
    for mod in _MODULE_RE.findall(text):
        parts = mod.split(".")
        if len(parts) >= 2 and all(p.isidentifier() for p in parts):
            as_path = "/".join(parts) + ".py"
            if as_path not in seeds.paths:
                seeds.paths.append(as_path)
            as_pkg = "/".join(parts) + "/__init__.py"
            if as_pkg not in seeds.paths:
                seeds.paths.append(as_pkg)
            # Add trailing symbol name
            tail_sym = parts[-1]
            if tail_sym not in seeds.symbols:
                seeds.symbols.append(tail_sym)

    for line in text.splitlines():
        fn = _FUNC_IN_RE.match(line)
        if fn:
            name = fn.group(1).split(".")[-1]
            if name not in seeds.traceback_funcs:
                seeds.traceback_funcs.append(name)

    for match in _PATH_RE.finditer(text):
        path = match.group(0)
        if path not in seeds.paths:
            seeds.paths.append(path)

    for match in re.finditer(r"```(?:\w+)?\n(.*?)```", text, re.S):
        block = match.group(1).strip()
        if block and len(block) < 4000:
            seeds.snippets.append(block)
            for line in block.splitlines():
                dm = _DEF_RE.match(line)
                if dm and dm.group(1) not in seeds.symbols:
                    seeds.symbols.append(dm.group(1))

    # Lines that look like bare code / signatures in the report body.
    for line in text.splitlines()[:200]:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-", "*", "|", ">")):
            continue
        dm = _DEF_RE.match(line)
        if dm and dm.group(1) not in seeds.symbols:
            seeds.symbols.append(dm.group(1))

    for line in text.splitlines():
        em = _EXC_RE.match(line.strip())
        if em and em.group(1) not in seeds.exceptions:
            seeds.exceptions.append(em.group(1))

    # ``NameError: name 'foo' is not defined`` style references.
    for match in re.finditer(
        r"(?:name|attribute|object) ['\"]([\w.]+)['\"]", text
    ):
        for part in match.group(1).split("."):
            if part and part not in seeds.symbols:
                seeds.symbols.append(part)

    for match in re.finditer(r"`([A-Za-z_][\w.]*)`", text):
        name = match.group(1).split(".")[-1]
        if name not in seeds.symbols:
            seeds.symbols.append(name)

    # System check codes like models.W042, admin.E108, E028, W042
    for match in re.finditer(r"\b([a-zA-Z_]\w*\.[EWCIS]\d{3})\b", text):
        code = match.group(1)
        if code not in seeds.symbols:
            seeds.symbols.append(code)
        tail = code.split(".")[-1]
        if tail not in seeds.symbols:
            seeds.symbols.append(tail)

    for match in re.finditer(r"\b([EWCIS]\d{3})\b", text):
        code = match.group(1)
        if code not in seeds.symbols:
            seeds.symbols.append(code)

    # Uppercase constants & settings like DEFAULT_AUTO_FIELD, SCRIPT_NAME
    for match in re.finditer(r"\b([A-Z][A-Z0-9_]{3,})\b", text):
        const_name = match.group(1)
        if const_name not in seeds.symbols and const_name.lower() not in _STOPWORDS:
            seeds.symbols.append(const_name)

    seen: list[str] = []
    for ident in _IDENT_RE.findall(text.lower()):
        if ident in _STOPWORDS or ident in seen:
            continue
        seen.append(ident)
    seeds.identifiers = seen[:40]

    first_line = next((l.strip() for l in text.splitlines() if l.strip()), "")
    seeds.headline = first_line[:300]
    return seeds


@dataclass
class Candidate:
    file: str
    score: float
    symbol: str = ""
    symbols: list[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    scores: dict = field(default_factory=dict)
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "file": self.file,
            "symbol": self.symbol,
            "symbols": self.symbols,
            "line_range": [self.line_start, self.line_end] if self.symbol else [],
            "score": round(self.score, 4),
            "signals": {k: round(v, 4) for k, v in self.scores.items()},
            "reason": self.reason,
        }


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _shorten(path: str) -> str:
    """'django/db/models/fields/__init__.py' -> tail that survives matching."""
    return path


def _find_symbol_span(repo_path: str, rel: str, names: list[str]) -> tuple[str, int, int]:
    """Return (qualified_name, start_line, end_line) for the best symbol in file."""
    path = Path(repo_path) / rel
    if not path.is_file() or not names:
        return "", 0, 0
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "", 0, 0

    lowered = {n.lower() for n in names}
    best: tuple[int, str, int, int] = (-1, "", 0, 0)
    for idx, line in enumerate(lines):
        m = _DEF_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        base = name.split(".")[-1]
        score = 0
        if base.lower() in lowered:
            score = 3
        elif any(base.lower().endswith(n) or n in base.lower() for n in lowered):
            score = 1
        if score <= 0:
            continue
        indent = len(line) - len(line.lstrip())
        end = len(lines)
        for j in range(idx + 1, len(lines)):
            other = lines[j]
            if not other.strip():
                continue
            if (len(other) - len(other.lstrip())) <= indent:
                if _DEF_RE.match(other) or other.lstrip().startswith(
                    ("class ", "@")
                ):
                    end = j
                    break
        if score > best[0]:
            qualified = name
            if rel not in qualified:
                qualified = f"{rel}::{name}"
            best = (score, qualified, idx + 1, end)
    if best[1]:
        return best[1], best[2], best[3]
    return "", 0, 0


def _bm25_scores(query_tokens: set[str], chunks: list[dict]) -> dict[str, float]:
    """Rank files by BM25 over their concatenated chunks."""
    import math
    from collections import Counter

    docs: dict[str, list[str]] = {}
    for chunk in chunks:
        docs.setdefault(chunk.get("file_path", ""), []).extend(
            str(chunk.get("content", "")).split()
        )
    if not docs:
        return {}

    avgdl = sum(len(d) for d in docs.values()) / max(len(docs), 1)
    df: Counter = Counter()
    for tokens in docs.values():
        for term in set(t.lower() for t in tokens):
            if term in query_tokens:
                df[term] += 1
    n = len(docs)
    k1, b = 1.5, 0.75
    out: dict[str, float] = {}
    for path, tokens in docs.items():
        tf = Counter(t.lower() for t in tokens)
        score = 0.0
        for term in query_tokens:
            f = tf.get(term, 0)
            if not f:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * len(tokens) / avgdl))
        if score:
            out[path] = score
    if out:
        top = max(out.values())
        out = {k: v / top for k, v in out.items()}
    return out


def _vector_scores(query: str, chunks: list[dict]) -> dict[str, float]:
    from src.rag.indexer import cosine, embed_text

    qv = embed_text(query)
    best: dict[str, float] = {}
    for chunk in chunks:
        path = chunk.get("file_path", "")
        hay = f"{chunk.get('name', '')} {chunk.get('content', '')}"
        score = max(cosine(qv, embed_text(hay)), 0.0)
        if score > best.get(path, -1.0):
            best[path] = score
    if best:
        top = max(best.values()) or 1.0
        best = {k: v / top for k, v in best.items()}
    return best


def _seed_score(path: str, seeds: IssueSeeds) -> float:
    """1.0 for a traceback file, 0.7 for a mentioned path, 0.3 for a name hit."""
    norm = _norm(path)
    tail = norm.split("/")[-1]
    for tf, _ in seeds.traceback_files:
        if norm.endswith(tf) or tf.endswith(norm) or tf.split("/")[-1] == tail:
            return 1.0
    for p in seeds.paths:
        if norm.endswith(p) or p.endswith(norm) or p.split("/")[-1] == tail:
            return 0.7
    stem = tail[:-3] if tail.endswith(".py") else tail
    for sym in seeds.symbols + seeds.traceback_funcs:
        if sym == stem or stem in sym or sym in stem:
            return 0.45
    for exc in seeds.exceptions:
        if exc.lower().replace("error", "") in stem.lower():
            return 0.4
    return 0.0


_DOC_DIRS = {"docs", "doc", "documentation", "news", "examples", "example",
             "benchmarks", "tools", "scripts", "debian", "misc"}
_NON_CODE_EXT = (".txt", ".rst", ".md", ".po", ".pot", ".html", ".css",
                 ".json", ".yml", ".yaml", ".cfg", ".ini", ".in")


def _file_prior(path: str) -> float:
    """Multiplier for what kind of file this is.

    Documentation and tests talk about the code as fluently as the code does,
    so BM25 alone ranks them above the file that has to change.  The prior is a
    soft penalty — a traceback that names a test file still wins through seed.
    """
    parts = _norm(path).lower().split("/")
    name = parts[-1]
    prior = 1.0
    if any(seg in _DOC_DIRS for seg in parts[:-1]):
        prior *= PRIOR_DOC
    elif name.endswith(_NON_CODE_EXT):
        prior *= PRIOR_DOC
    if "tests" in parts or "test" in parts or name.startswith("test_") \
            or name.endswith("_test.py"):
        prior *= PRIOR_TEST
    return prior


def _def_scores(chunks: list[dict], seeds: IssueSeeds) -> dict[str, float]:
    """Where a symbol named in the issue is actually *defined*.

    ``MediaOrderConflictWarning`` appears in a dozen docs pages, but only one
    file declares it; that file is almost always the file to edit.
    """
    wanted = {
        s.lower() for s in
        seeds.symbols + seeds.traceback_funcs + seeds.exceptions
        + seeds.identifiers[:12]
        if len(s) > 2
    }
    if not wanted:
        return {}
    out: dict[str, float] = {}
    for chunk in chunks:
        if chunk.get("chunk_type") not in ("class", "function", "method",
                                           "staticmethod"):
            continue
        name = str(chunk.get("name") or "").split(".")[-1].lower()
        if not name or name not in wanted:
            continue
        path = _norm(chunk.get("file_path", ""))
        out[path] = max(out.get(path, 0.0), 1.0)
    if out:
        top = max(out.values()) or 1.0
        out = {k: v / top for k, v in out.items()}
    return out


def localize(
    issue_text: str,
    repo_path: str,
    top_k: int = 8,
    chunks: list[dict] | None = None,
) -> list[Candidate]:
    """Return the top-k (file, symbol, line-range) candidates for an issue."""
    from src.ingestion.parser import RepoParser

    seeds = parse_issue(issue_text)
    if chunks is None:
        chunks = RepoParser().parse(repo_path)

    token_query = " ".join(
        seeds.symbols + seeds.exceptions + seeds.identifiers + [seeds.headline]
    ).lower()
    query_tokens = {
        t for t in re.findall(r"[a-z0-9_]+", token_query) if len(t) > 2
    } - _STOPWORDS

    seed_scores = {}
    for chunk in chunks:
        path = _norm(chunk.get("file_path", ""))
        seed_scores[path] = max(seed_scores.get(path, 0.0), _seed_score(path, seeds))

    # Fast literal grep for exact check codes (e.g. models.W042, W042, admin.E108)
    check_codes = [s for s in seeds.symbols if re.match(r"^(?:[A-Za-z_]+\.)?[EWCIS]\d{3}$", s)]
    if check_codes and repo_path:
        root_path = Path(repo_path)
        for cand_file in root_path.glob("**/*.py"):
            parts = [p.lower() for p in cand_file.parts]
            if any(ign in parts for ign in ("test", "tests", "docs", "doc", "venv", ".venv", "__pycache__")):
                continue
            try:
                txt = cand_file.read_text(encoding="utf-8", errors="ignore")
                if any(code in txt for code in check_codes):
                    rel = _norm(str(cand_file.relative_to(root_path)))
                    seed_scores[rel] = max(seed_scores.get(rel, 0.0), 0.95)
            except Exception:
                pass
    bm25 = _bm25_scores(query_tokens, chunks)
    vec = _vector_scores(seeds.query, chunks)
    defs = _def_scores(chunks, seeds)

    files = set(seed_scores) | set(bm25) | set(vec) | set(defs)
    ranked: list[Candidate] = []
    for path in files:
        s = {
            "seed": seed_scores.get(path, 0.0),
            "bm25": bm25.get(path, 0.0),
            "vector": vec.get(path, 0.0),
            "defs": defs.get(path, 0.0),
        }
        # Seed evidence dominates; retrieval breaks ties; the file that
        # declares the symbol gets a bonus; prose and tests are discounted.
        score = (
            W_SEED * s["seed"]
            + W_BM25 * s["bm25"]
            + W_VECTOR * s["vector"]
            + W_DEFS * s["defs"]
        ) * _file_prior(path)
        if score <= 0.02:
            continue
        ranked.append(Candidate(file=path, score=score, scores=s))

    ranked.sort(key=lambda c: c.score, reverse=True)

    # Hierarchy step: file -> symbol -> line range for the top files.
    focus = seeds.symbols + seeds.traceback_funcs + list(seeds.exceptions)
    for cand in ranked[: max(top_k * 2, top_k)]:
        symbol_found = False
        try:
            from src.tools.symbol_target import target_file
            st_targets = target_file(repo_path, cand.file, issue_text)
            if st_targets:
                best_st = st_targets[0]
                cand.symbol = f"{cand.file}::{best_st['symbol']}"
                cand.symbols = [t["symbol"] for t in st_targets]
                cand.line_start = best_st["start"]
                cand.line_end = best_st["end"]
                cand.score = min(1.0, cand.score + 0.2)
                cand.reason = best_st.get("reason", "symbol target")
                symbol_found = True
        except Exception:
            pass

        if not symbol_found:
            symbol, start, end = _find_symbol_span(repo_path, cand.file, focus)
            if symbol:
                cand.symbol = symbol
                cand.line_start, cand.line_end = start, end
                cand.score = min(1.0, cand.score + 0.15)
                cand.reason = "symbol match"
            elif cand.scores.get("seed", 0) >= 0.7:
                cand.reason = "named in traceback"
            elif cand.scores.get("seed", 0) > 0:
                cand.reason = "named in issue"
            else:
                cand.reason = "retrieval"
    ranked.sort(key=lambda c: c.score, reverse=True)
    if os.getenv("ISHA_LOC_ENABLE_LLM_RERANK", "1") == "1":
        ranked = llm_rerank(issue_text, ranked, top_n=min(len(ranked), max(top_k, 6)))
    return ranked[:top_k]


def llm_rerank(
    issue_text: str,
    candidates: list[Candidate],
    top_n: int = 8,
) -> list[Candidate]:
    """Re-rank top candidates using a cheap, structured LLM call."""
    if not candidates or len(candidates) <= 1:
        return candidates

    pool = candidates[:top_n]
    rest = candidates[top_n:]

    # Fast short-circuit: if the top candidate is already uniquely strong from stack traces
    if pool[0].scores.get("seed", 0) >= 0.9 and (len(pool) == 1 or pool[1].scores.get("seed", 0) < 0.5):
        return candidates

    cand_lines = []
    for i, c in enumerate(pool, 1):
        sym_desc = f" (symbol: {c.symbol}, lines {c.line_start}-{c.line_end})" if c.symbol else ""
        cand_lines.append(f"{i}. {c.file}{sym_desc}")

    prompt = (
        "You are an expert software engineer localizing a bug in a codebase.\n"
        "Given the bug report and candidate files retrieved from the codebase, "
        "re-rank the candidates so that the file most likely to contain the actual defect "
        "(root cause code that must be edited) appears first.\n"
        "Exclude tests, docs, and example files unless the bug specifically targets them.\n\n"
        f"BUG REPORT:\n{issue_text[:1800]}\n\n"
        f"CANDIDATES:\n" + "\n".join(cand_lines) + "\n\n"
        "Return ONLY a JSON array of the candidate file paths in ranked order, from most likely to least likely:\n"
        '["path/to/file1.py", "path/to/file2.py", ...]'
    )

    try:
        from src.config import OFFLINE_MODE, call_planner
        if OFFLINE_MODE:
            return candidates

        reply = call_planner(prompt)
        if not reply:
            return candidates

        import json
        cleaned = re.sub(r"^```(?:json)?\s*", "", reply.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE).strip()
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        order = json.loads(cleaned)
        if isinstance(order, list) and order:
            by_file = {c.file: c for c in pool}
            reranked = []
            seen = set()
            for path_str in order:
                target_str = str(path_str).replace("\\", "/").strip()
                cand = by_file.get(target_str)
                if not cand:
                    for f, c in by_file.items():
                        if f.endswith(target_str) or target_str.endswith(f):
                            cand = c
                            break
                if cand and cand.file not in seen:
                    seen.add(cand.file)
                    cand.reason = f"llm_rerank #{len(reranked)+1} ({cand.reason})"
                    reranked.append(cand)
            for c in pool:
                if c.file not in seen:
                    reranked.append(c)
            return reranked + rest
    except Exception:
        return candidates
    return candidates


def find_test_files(
    repo_path: str, target_files: list[str], top_k: int = 4
) -> list[tuple[str, str]]:
    """Most relevant existing test files for the suspect source files.

    Returns [(relative_path, why)] ordered by relevance — a test that already
    exercises the suspect module tells the coder exactly what behaviour is
    pinned down today.
    """
    root = Path(repo_path)
    all_tests: list[str] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            rel = str(path.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        name = path.name.lower()
        parts = [p.lower() for p in rel.split("/")]
        if name.startswith("test_") or name.endswith("_test.py") or "tests" in parts[:-1]:
            all_tests.append(rel)

    scored: list[tuple[int, str, str]] = []
    for target in target_files:
        tail = Path(target).name
        stem = tail[:-3] if tail.endswith(".py") else tail
        candidates = stem.replace("test_", "").replace("_test", "")
        for test in all_tests:
            score, why = 0, ""
            tname = Path(test).name.lower()
            if stem and (stem.lower().replace("test_", "") in tname or tname.replace("test_", "") in stem.lower()):
                score, why = 3, f"module name matches {tail}"
            elif any(part in test.lower() for part in Path(target).parts[:-1]):
                score, why = 2, "same package as " + tail
            if candidates and candidates.lower() in test.lower():
                score = max(score, 2)
                why = why or f"exercises {stem}"
            if score:
                scored.append((score, test, why))

    scored.sort(key=lambda t: (-t[0], t[1]))
    out: list[tuple[str, str]] = []
    for _, test, why in scored:
        if (test, why) not in out:
            out.append((test, why))
        if len(out) >= top_k:
            break
    return out
