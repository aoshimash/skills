#!/usr/bin/env python3
"""Assert this repository's mechanical invariants.

Each check has a stable name. A skill author cites that name as the check that
covers a change (see AGENTS.md "Repository Checks"):

  evals-json      every evals/evals.json parses and is well-formed
  frontmatter     every SKILL.md frontmatter meets the Agent Skills spec caps
  skill-md-lines  every SKILL.md is under 500 lines
  links           every relative markdown link and heading anchor resolves
  claude-paths    no `.claude/` path in skill instructions outside an
                  "On Claude Code, ..." note or a Claude Code-bound skill

Standard library only, no network, no clock: the same tree always gives the
same result. This is what lets the workflow serve as the merge gate's
post-merge verification signal on integration branches.

Usage:
  python3 scripts/check-invariants.py [--root DIR] [--only NAME ...]
  python3 scripts/check-invariants.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import unquote

SKILL_MD_MAX_LINES = 500  # SKILL.md must stay strictly under this
NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Over-cap descriptions already on main when this check landed, as a ratchet:
# skill -> the length recorded then. The description may shrink, never grow, and
# the entry must be deleted once it is back under the cap (a stale entry fails).
# A waived violation is printed but does not fail the run.
DESCRIPTION_WAIVERS: dict[str, int] = {
    "merge-renovate-prs": 1074,
}
WAIVED = "waived: "  # prefix of a reported, non-failing violation


# --------------------------------------------------------------------------
# File discovery
# --------------------------------------------------------------------------

def walk_files(root: Path, suffix: str) -> list[Path]:
    """Every file with `suffix` under root, skipping dot-directories.

    Dot-directories (.git, .github, .claude, .worktrees, ...) hold no tracked
    markdown here, and skipping them keeps local worktrees out of the scan.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.endswith(suffix):
                found.append(Path(dirpath) / name)
    return found


def skill_dirs(root: Path) -> list[Path]:
    """plugins/<plugin>/skills/<skill>/ directories."""
    return sorted(p for p in root.glob("plugins/*/skills/*") if p.is_dir())


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


# --------------------------------------------------------------------------
# Frontmatter (the YAML subset SKILL.md files use; no PyYAML dependency)
# --------------------------------------------------------------------------

def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def parse_frontmatter(lines: list[str]) -> dict[str, str]:
    """Top-level `key: value` pairs with plain, quoted, and block scalars.

    Block scalars (`>`, `|`, with optional chomping indicator) are folded or
    joined as YAML does; the measured value excludes the trailing newline.
    Nested mappings (e.g. `metadata:`) are recorded as an empty string.
    """
    out: dict[str, str] = {}
    i = 0
    key_re = re.compile(r"^([A-Za-z0-9_-]+):(?:\s+(.*))?$")
    while i < len(lines):
        m = key_re.match(lines[i])
        if not m:
            i += 1
            continue
        key, value = m.group(1), (m.group(2) or "").strip()
        i += 1
        cont = []
        while i < len(lines) and (lines[i].strip() == "" or lines[i][:1] in (" ", "\t")):
            cont.append(lines[i])
            i += 1
        while cont and cont[-1].strip() == "":
            cont.pop()
        if value[:1] in (">", "|"):
            indents = [len(c) - len(c.lstrip()) for c in cont if c.strip()]
            ind = min(indents) if indents else 0
            body = [c[ind:] if c.strip() else "" for c in cont]
            if value[0] == "|":
                out[key] = "\n".join(body).rstrip("\n")
            else:
                folded, para = [], []
                for b in body:
                    if b == "":
                        folded.append(" ".join(para))
                        para = []
                    else:
                        para.append(b.rstrip())
                folded.append(" ".join(para))
                out[key] = "\n".join(folded).strip("\n")
        elif value[:1] in ('"', "'") and value[-1:] == value[:1] and len(value) > 1:
            inner = value[1:-1]
            out[key] = inner.replace("''", "'") if value[0] == "'" else json.loads(value)
        else:
            out[key] = " ".join([value] + [c.strip() for c in cont if c.strip()]).strip()
    return out


def read_frontmatter(skill_md: Path) -> dict[str, str] | None:
    lines, _ = split_frontmatter(skill_md.read_text(encoding="utf-8"))
    return None if lines is None else parse_frontmatter(lines)


# --------------------------------------------------------------------------
# Check: evals-json
# --------------------------------------------------------------------------

def check_evals_json(root: Path) -> list[str]:
    errors = []
    for path in sorted(root.glob("plugins/*/skills/*/evals/evals.json")):
        where = rel(root, path)
        skill = path.parent.parent.name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            errors.append(f"{where}: not valid JSON: {e}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{where}: top level is not an object")
            continue
        if data.get("skill_name") != skill:
            errors.append(f"{where}: skill_name {data.get('skill_name')!r} != directory {skill!r}")
        evals = data.get("evals")
        if not isinstance(evals, list) or not evals:
            errors.append(f"{where}: `evals` is missing or not a non-empty list")
            continue
        prev_id, names = 0, set()
        for n, ev in enumerate(evals):
            if not isinstance(ev, dict):
                errors.append(f"{where}: evals[{n}] is not an object")
                continue
            eid, name = ev.get("id"), ev.get("name")
            # Ids must be unique and ascending. Gaps are allowed: a skill may
            # key its ids to the case numbers in eval-cases.md (respond-to-pr-review
            # runs cases 1, 2, 9), so contiguity is not an invariant here.
            if not isinstance(eid, int) or isinstance(eid, bool) or eid <= prev_id:
                errors.append(f"{where}: evals[{n}].id {eid!r} is not an integer greater than {prev_id}")
            else:
                prev_id = eid
            if not isinstance(name, str) or not name:
                errors.append(f"{where}: evals[{n}].name is missing or empty")
            elif name in names:
                errors.append(f"{where}: evals[{n}].name {name!r} is a duplicate")
            else:
                names.add(name)
            if not isinstance(ev.get("prompt"), str) or not ev.get("prompt"):
                errors.append(f"{where}: evals[{n}].prompt is missing or empty")
        triggers = data.get("trigger_evals")
        if triggers is not None:
            if not isinstance(triggers, list):
                errors.append(f"{where}: `trigger_evals` is not a list")
            else:
                for n, t in enumerate(triggers):
                    if not (isinstance(t, dict) and isinstance(t.get("query"), str) and t.get("query")
                            and isinstance(t.get("should_trigger"), bool)):
                        errors.append(f"{where}: trigger_evals[{n}] needs a non-empty `query` and a boolean `should_trigger`")
    return errors


# --------------------------------------------------------------------------
# Check: frontmatter
# --------------------------------------------------------------------------

def check_frontmatter(root: Path) -> list[str]:
    errors = []
    dirs = skill_dirs(root)
    for stale in sorted(set(DESCRIPTION_WAIVERS) - {d.name for d in dirs}):
        errors.append(f"DESCRIPTION_WAIVERS: no skill named {stale!r}; delete the entry")
    for d in dirs:
        skill_md = d / "SKILL.md"
        where = rel(root, skill_md)
        if not skill_md.is_file():
            errors.append(f"{rel(root, d)}: skill directory has no SKILL.md")
            continue
        fm = read_frontmatter(skill_md)
        if fm is None:
            errors.append(f"{where}: no `---` delimited YAML frontmatter")
            continue
        name = fm.get("name", "")
        if not name:
            errors.append(f"{where}: `name` is missing or empty")
        else:
            if len(name) > NAME_MAX:
                errors.append(f"{where}: `name` is {len(name)} characters (max {NAME_MAX})")
            if not NAME_RE.match(name):
                errors.append(f"{where}: `name` {name!r} must be lowercase a-z, 0-9 and single inner hyphens")
            if name != d.name:
                errors.append(f"{where}: `name` {name!r} does not match directory {d.name!r}")
        desc = fm.get("description", "")
        waiver = DESCRIPTION_WAIVERS.get(d.name)
        if not desc:
            errors.append(f"{where}: `description` is missing or empty")
        elif len(desc) > DESCRIPTION_MAX:
            msg = f"{where}: `description` is {len(desc)} characters (max {DESCRIPTION_MAX})"
            if waiver is not None and len(desc) <= waiver:
                errors.append(f"{WAIVED}{msg}; recorded at {waiver} in DESCRIPTION_WAIVERS, may only shrink")
            else:
                errors.append(msg + (f"; grew past its waiver of {waiver}" if waiver is not None else ""))
        elif waiver is not None:
            errors.append(f"{where}: `description` is back under {DESCRIPTION_MAX}; delete its DESCRIPTION_WAIVERS entry")
        if "compatibility" in fm:
            compat = fm["compatibility"]
            if not compat or len(compat) > COMPATIBILITY_MAX:
                errors.append(f"{where}: `compatibility` is {len(compat)} characters (must be 1-{COMPATIBILITY_MAX})")
    return errors


# --------------------------------------------------------------------------
# Check: skill-md-lines
# --------------------------------------------------------------------------

def check_skill_md_lines(root: Path) -> list[str]:
    errors = []
    for skill_md in sorted(root.glob("plugins/*/skills/*/SKILL.md")):
        n = len(skill_md.read_text(encoding="utf-8").splitlines())
        if n >= SKILL_MD_MAX_LINES:
            errors.append(f"{rel(root, skill_md)}: {n} lines (must be under {SKILL_MD_MAX_LINES})")
    return errors


# --------------------------------------------------------------------------
# Markdown scanning shared by links and claude-paths
# --------------------------------------------------------------------------

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")  # any indent: fences nested in list items are common here


def prose_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) for lines outside fenced code blocks and frontmatter."""
    lines = text.split("\n")
    start = 0
    fm, _ = split_frontmatter(text)
    if fm is not None:
        start = len(fm) + 2
    out, fence = [], None
    for i in range(start, len(lines)):
        line = lines[i]
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                continue
            out.append((i + 1, line))
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):].strip():
            fence = None
    return out


CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")


def strip_code_spans(line: str) -> str:
    return CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), line)


# --------------------------------------------------------------------------
# Check: links
# --------------------------------------------------------------------------

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*$")
INLINE_LINK_RE = re.compile(r"!?\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
REF_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
HTML_ID_RE = re.compile(r"<a\s+[^>]*(?:name|id)=[\"']([^\"']+)[\"']", re.I)


def heading_text(raw: str) -> str:
    """Approximate the rendered text of an ATX heading."""
    raw = re.sub(r"\s+#+\s*$", "", raw)
    if re.fullmatch(r"#+", raw):
        raw = ""
    parts, last = [], 0
    for m in CODE_SPAN_RE.finditer(raw):
        parts.append(("text", raw[last:m.start()]))
        parts.append(("code", m.group(2)))
        last = m.end()
    parts.append(("text", raw[last:]))
    out = []
    for kind, s in parts:
        if kind == "code":
            out.append(s)
            continue
        s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)  # [text](url) -> text
        s = re.sub(r"<[^>]+>", "", s)                      # inline HTML
        s = s.replace("*", "")
        s = re.sub(r"(?<![A-Za-z0-9])_+|_+(?![A-Za-z0-9])", "", s)  # _emphasis_
        out.append(s)
    return "".join(out)


def github_slug(text: str) -> str:
    """GitHub's heading anchor: lowercase, drop punctuation/symbols, spaces to '-'."""
    kept = []
    for ch in text.lower():
        cat = unicodedata.category(ch)
        if ch in (" ", "-") or cat[0] in ("L", "M", "N") or cat == "Pc":
            kept.append(ch)
    return "".join(kept).replace(" ", "-")


def anchors_of(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if path not in cache:
        seen: dict[str, int] = {}
        anchors = set()
        text = path.read_text(encoding="utf-8")
        for _, line in prose_lines(text):
            m = HEADING_RE.match(line)
            if m:
                base = github_slug(heading_text(m.group(2)))
                n = seen.get(base, 0)
                anchors.add(base if n == 0 else f"{base}-{n}")
                seen[base] = n + 1
            for hid in HTML_ID_RE.findall(line):
                anchors.add(hid)
        cache[path] = anchors
    return cache[path]


def exists_exact_case(root: Path, target: Path) -> bool:
    """Path exists with this exact case (CI runs on a case-sensitive filesystem)."""
    try:
        parts = target.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return target.exists()
    cur = root.resolve()
    for part in parts:
        if not cur.is_dir() or part not in os.listdir(cur):
            return False
        cur = cur / part
    return True


def check_links(root: Path) -> list[str]:
    errors = []
    cache: dict[Path, set[str]] = {}
    for md in walk_files(root, ".md"):
        where = rel(root, md)
        for lineno, line in prose_lines(md.read_text(encoding="utf-8")):
            scan = strip_code_spans(line)
            targets = [m.group(1) for m in INLINE_LINK_RE.finditer(scan)]
            m = REF_DEF_RE.match(scan)
            if m:
                targets.append(m.group(1))
            for target in targets:
                target = target.strip("<>")
                if not target or SCHEME_RE.match(target) or target.startswith("//"):
                    continue
                path_part, _, frag = target.partition("#")
                path_part = unquote(path_part)
                if path_part.startswith("/"):
                    dest = root / path_part.lstrip("/")
                elif path_part:
                    dest = md.parent / path_part
                else:
                    dest = md
                if not exists_exact_case(root, dest):
                    errors.append(f"{where}:{lineno}: link target not found: {target}")
                    continue
                if frag and dest.is_file() and dest.suffix == ".md":
                    if unquote(frag) not in anchors_of(dest.resolve(), cache):
                        errors.append(f"{where}:{lineno}: anchor #{frag} not found in {os.path.relpath(dest, root)}")
    return errors


# --------------------------------------------------------------------------
# Check: claude-paths
# --------------------------------------------------------------------------

CLAUDE_PATH_RE = re.compile(r"\.claude/")
ON_CLAUDE_CODE_RE = re.compile(r"\b[Oo]n Claude Code\b")
BLOCK_START_RE = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|\||#{1,6}\s)")


def blocks(text: str) -> list[tuple[int, str]]:
    """Split markdown into (first line number, block text).

    A block is a paragraph, a list item, a table row, or a heading. Fenced
    code is its own block, so a code block never inherits a neighbouring
    note's exemption.
    """
    out, cur, cur_start, fence = [], [], 0, None

    def flush():
        nonlocal cur
        if cur:
            out.append((cur_start, "\n".join(cur)))
        cur = []

    for i, line in enumerate(text.split("\n"), start=1):
        m = FENCE_RE.match(line)
        if fence is not None:
            cur.append(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
                flush()
            continue
        if m:
            flush()
            fence, cur_start, cur = m.group(1), i, [line]
            continue
        if not line.strip():
            flush()
            continue
        if BLOCK_START_RE.match(line) or not cur:
            flush()
            cur_start = i
        cur.append(line)
    flush()
    return out


def check_claude_paths(root: Path) -> list[str]:
    errors = []
    for d in skill_dirs(root):
        fm = read_frontmatter(d / "SKILL.md") if (d / "SKILL.md").is_file() else None
        if fm and "Claude Code" in fm.get("compatibility", ""):
            continue  # product-bound skill: AGENTS.md exception (b)
        for md in walk_files(d, ".md"):
            if md.name == "eval-cases.md":
                continue  # evaluation records, not instructions an agent executes
            text = md.read_text(encoding="utf-8")
            fm_lines, _ = split_frontmatter(text)
            skip_until = len(fm_lines) + 2 if fm_lines is not None else 0
            for start, block in blocks(text):
                if start <= skip_until or not CLAUDE_PATH_RE.search(block):
                    continue
                if ON_CLAUDE_CODE_RE.search(block):
                    continue  # inside an "On Claude Code, ..." note: exception (a)
                for off, line in enumerate(block.split("\n")):
                    if CLAUDE_PATH_RE.search(line):
                        errors.append(f"{rel(root, md)}:{start + off}: `.claude/` path outside an \"On Claude Code, ...\" note")
    return errors


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

CHECKS = {
    "evals-json": check_evals_json,
    "frontmatter": check_frontmatter,
    "skill-md-lines": check_skill_md_lines,
    "links": check_links,
    "claude-paths": check_claude_paths,
}


def failures(found: list[str]) -> list[str]:
    return [e for e in found if not e.startswith(WAIVED)]


def run(root: Path, only: list[str] | None, out=sys.stdout) -> int:
    failed = 0
    for name, fn in CHECKS.items():
        if only and name not in only:
            continue
        found = fn(root)
        status = "FAIL" if failures(found) else "ok"
        print(f"[{status}] {name}", file=out)
        for e in found:
            print(f"    {e}", file=out)
        failed += bool(failures(found))
    return 1 if failed else 0


# --------------------------------------------------------------------------
# Self-test: every check must fail on a deliberate violation
# --------------------------------------------------------------------------

GOOD_SKILL = """---
name: demo
description: >
  A demo skill used only by the self-test.
---

# Demo

See [the reference](references/guide.md#the-section) and [below](#usage).

## Usage

On Claude Code, settings live in `.claude/settings.json`.
"""

GOOD_GUIDE = """# Guide

## The Section

Back to [the skill](../SKILL.md#demo).
"""

GOOD_EVALS = {
    "skill_name": "demo",
    "evals": [
        {"id": 1, "name": "one", "prompt": "p"},
        {"id": 3, "name": "three", "prompt": "p"},
    ],
    "trigger_evals": [{"query": "q", "should_trigger": True}],
}

# name -> (check that must fail, mutation applied to a clean tree[, waivers in force])
VIOLATIONS = {
    "evals.json does not parse": ("evals-json", lambda r: (r / "S/evals/evals.json").write_text("{", encoding="utf-8")),
    "evals.json duplicate id": ("evals-json", lambda r: _evals(r, ids=[1, 1])),
    "evals.json descending id": ("evals-json", lambda r: _evals(r, ids=[2, 1])),
    "evals.json duplicate name": ("evals-json", lambda r: _evals(r, names=["x", "x"])),
    "evals.json skill_name mismatch": ("evals-json", lambda r: _evals(r, skill="other")),
    "name over 64 chars": ("frontmatter", lambda r: _skill(r, "name: demo", "name: " + "a" * 65)),
    "name not matching directory": ("frontmatter", lambda r: _skill(r, "name: demo", "name: demo-two")),
    "name with uppercase": ("frontmatter", lambda r: _skill(r, "name: demo", "name: Demo")),
    "description missing": ("frontmatter", lambda r: _skill(r, "description: >\n  A demo skill used only by the self-test.\n", "")),
    "description over 1024 chars": ("frontmatter", lambda r: _skill(r, "  A demo skill used only by the self-test.", "\n".join(["  " + "word " * 20] * 11))),
    "compatibility over 500 chars": ("frontmatter", lambda r: _skill(r, "---\n\n", "compatibility: " + "x" * 501 + "\n---\n\n")),
    "waived description grows": ("frontmatter", lambda r: _skill(r, "  A demo skill used only by the self-test.", "\n".join(["  " + "word " * 20] * 11)), {"demo": 1030}),
    "stale description waiver": ("frontmatter", lambda r: None, {"demo": 1030}),
    "waiver for a missing skill": ("frontmatter", lambda r: None, {"gone": 1030}),
    "SKILL.md at 500 lines": ("skill-md-lines", lambda r: _skill(r, "## Usage\n", "## Usage\n" + "filler\n" * 490)),
    "broken relative link": ("links", lambda r: _guide(r, "../SKILL.md#demo", "../MISSING.md")),
    "wrong-case link": ("links", lambda r: _guide(r, "../SKILL.md#demo", "../skill.md")),
    "broken cross-file anchor": ("links", lambda r: _guide(r, "../SKILL.md#demo", "../SKILL.md#nope")),
    "broken same-file anchor": ("links", lambda r: _skill(r, "(#usage)", "(#usages)")),
    ".claude/ path outside a note": ("claude-paths", lambda r: _guide(r, "Back to", "Edit `.claude/settings.json`. Back to")),
    ".claude/ path in code after a note": ("claude-paths", lambda r: _skill(r, "`.claude/settings.json`.\n", "`.claude/settings.json`:\n\n```\ncat .claude/x\n```\n")),
}


def _skill(root: Path, old: str, new: str) -> None:
    p = root / "S/SKILL.md"
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def _guide(root: Path, old: str, new: str) -> None:
    p = root / "S/references/guide.md"
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def _evals(root: Path, ids=(1, 2), names=("a", "b"), skill="demo") -> None:
    data = {"skill_name": skill, "evals": [{"id": i, "name": n, "prompt": "p"} for i, n in zip(ids, names)]}
    (root / "S/evals/evals.json").write_text(json.dumps(data), encoding="utf-8")


def build_clean_tree(root: Path) -> None:
    skill = root / "plugins/p/skills/demo"
    (skill / "references").mkdir(parents=True)
    (skill / "evals").mkdir()
    (skill / "SKILL.md").write_text(GOOD_SKILL, encoding="utf-8")
    (skill / "references/guide.md").write_text(GOOD_GUIDE, encoding="utf-8")
    (skill / "evals/evals.json").write_text(json.dumps(GOOD_EVALS), encoding="utf-8")
    (root / "S").symlink_to(skill, target_is_directory=True)


def self_test() -> int:
    import io

    global DESCRIPTION_WAIVERS
    saved, bad = DESCRIPTION_WAIVERS, 0
    try:
        DESCRIPTION_WAIVERS = {}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / "clean"
            build_clean_tree(root)
            (root / "S").unlink()  # the alias is for mutations only; keep it out of the scan
            buf = io.StringIO()
            if run(root, None, out=buf) != 0:
                print("[FAIL] self-test: the clean fixture tree does not pass:\n" + buf.getvalue())
                bad += 1
            else:
                print("[ok] self-test: clean fixture passes every check")
        for label, (check, mutate, *waivers) in VIOLATIONS.items():
            DESCRIPTION_WAIVERS = waivers[0] if waivers else {}
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve() / "t"
                build_clean_tree(root)
                mutate(root)
                (root / "S").unlink()
                results = {name: bool(failures(fn(root))) for name, fn in CHECKS.items()}
                others = [n for n, failed in results.items() if failed and n != check]
                if results[check] and not others:
                    print(f"[ok] self-test: {check} catches: {label}")
                else:
                    why = "did not fail" if not results[check] else f"other checks also failed: {others}"
                    print(f"[FAIL] self-test: {check} on '{label}': {why}")
                    bad += 1
        # A waiver holds an over-cap description that has not grown: reported, not failed.
        DESCRIPTION_WAIVERS = {"demo": 1200}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / "w"
            build_clean_tree(root)
            _skill(root, "  A demo skill used only by the self-test.", "\n".join(["  " + "word " * 20] * 11))
            (root / "S").unlink()
            found = check_frontmatter(root)
            if found and not failures(found):
                print("[ok] self-test: frontmatter waives an over-cap description within its waiver")
            else:
                print(f"[FAIL] self-test: waiver not honoured as a non-failing report: {found}")
                bad += 1
    finally:
        DESCRIPTION_WAIVERS = saved
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--only", nargs="+", choices=list(CHECKS), metavar="NAME")
    ap.add_argument("--self-test", action="store_true", help="prove each check fails on a deliberate violation")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return run(args.root.resolve(), args.only)


if __name__ == "__main__":
    sys.exit(main())
