"""Check that a proposed solution design actually covers every acceptance criterion.

Reads:
- ``.ai/context/work-items/<WI>/acceptance-criteria.md`` (primary) or the
  ``Acceptance Criteria`` section of ``work-item-summary.md``.
- ``specs/proposed/<WI>.solution-design.md`` (or the approved sibling).

Emits:
- ``.ai/context/work-items/<WI>/ac-coverage.md`` — human-readable per-AC table.
- ``.ai/context/work-items/<WI>/traceability.json`` — machine-readable AC ↔
  knowledge ↔ design ↔ metadata ↔ test traceability rows.

Each AC is classified ``covered | partial | missing``. ``missing`` rows are
escalated to a blocking finding by ``precheck_work_item`` so promote-to-approved
refuses incomplete designs.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AC_TABLE_ROW_RE = re.compile(r"^\|\s*(AC[-\s]?\d+)\s*\|\s*(.+?)\s*(?:\|.*)?\|\s*$")
AC_BULLET_RE = re.compile(r"^\s*[-*]\s*(AC[-\s]?\d+)[:.\s]+(.+)$", re.IGNORECASE)
GIVEN_WHEN_THEN_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(given|when|then)\s+(.+)$",
    re.IGNORECASE,
)
KNOWLEDGE_REF_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
COVERAGE_TABLE_HEADER_RE = re.compile(r"^\|\s*AC[\s-]*\|", re.IGNORECASE)
SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check AC coverage in a Work Item's solution design.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--work-item-dir")
    parser.add_argument("--design")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-md", help="Override path for ac-coverage.md.")
    parser.add_argument("--out-json", help="Override path for traceability.json.")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    work_item_dir = Path(args.work_item_dir or f".ai/context/work-items/{args.work_item}")
    design_path = _resolve_design(args.design, args.work_item, repo_root)

    ac_rows = _read_acceptance_criteria(work_item_dir)
    design_text = design_path.read_text(encoding="utf-8", errors="replace") if design_path and design_path.exists() else ""
    knowledge_refs = _extract_knowledge_references(design_text)
    coverage_table = _extract_coverage_table(design_text)
    design_sections = _section_map(design_text)
    metadata_components = _extract_metadata_components(design_text)
    test_cases = _read_qa_tests(repo_root, args.work_item)

    rows = []
    for ac_id, ac_text in ac_rows:
        coverage_entry = coverage_table.get(_ac_id_key(ac_id), {})
        cited_knowledge_slugs = _slugs_from_refs(coverage_entry.get("knowledge_refs", []) + knowledge_refs)
        cited_metadata = _metadata_in_entry(coverage_entry.get("metadata_refs", []), metadata_components)
        verdict = _verdict(ac_id, ac_text, coverage_entry, cited_knowledge_slugs, cited_metadata)
        rows.append({
            "ac_id": ac_id,
            "ac_text": ac_text,
            "verdict": verdict["status"],
            "rationale": verdict["rationale"],
            "knowledge_slugs": sorted(cited_knowledge_slugs),
            "metadata_components": sorted(cited_metadata),
            "design_sections": _design_sections_for(ac_id, design_sections, ac_text),
            "test_cases": _test_cases_for(ac_id, test_cases),
        })

    summary = _summary(rows)
    generated_at = datetime.now(timezone.utc).isoformat()
    md = _render_md(args.work_item, design_path, rows, summary, generated_at)
    traceability = {
        "work_item": args.work_item,
        "design_path": design_path.as_posix() if design_path else None,
        "generated_at": generated_at,
        "summary": summary,
        "rows": rows,
    }

    out_md = Path(args.out_md) if args.out_md else work_item_dir / "ac-coverage.md"
    out_json = Path(args.out_json) if args.out_json else work_item_dir / "traceability.json"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    out_json.write_text(json.dumps(traceability, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wrote {out_md}")
    print(f"Wrote {out_json}")
    if args.print_summary:
        print(f"AC coverage: covered={summary['covered']} partial={summary['partial']} missing={summary['missing']} (total={summary['total']})")
    return 1 if summary["missing"] > 0 else 0


# ---------- AC extraction ----------


def _read_acceptance_criteria(work_item_dir: Path) -> list[tuple[str, str]]:
    """Return ordered ``[(ac_id, ac_text), ...]`` from any supported AC format."""

    candidates: list[Path] = [
        work_item_dir / "acceptance-criteria.md",
        work_item_dir / "work-item-summary.md",
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rows = _parse_acceptance_criteria_text(text)
        if rows:
            return rows
    return []


def _parse_acceptance_criteria_text(text: str) -> list[tuple[str, str]]:
    sections = re.split(r"(?m)^## +", text)
    relevant_text = text
    for section in sections:
        head, _, body = section.partition("\n")
        if "acceptance" in head.lower() and "criter" in head.lower():
            relevant_text = body
            break
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in relevant_text.splitlines():
        line = line.rstrip()
        table_match = AC_TABLE_ROW_RE.match(line)
        if table_match:
            ac_id = _normalize_ac_id(table_match.group(1))
            ac_text = _strip_inline_markdown(table_match.group(2))
            if ac_id and ac_id not in seen:
                rows.append((ac_id, ac_text))
                seen.add(ac_id)
            continue
        bullet_match = AC_BULLET_RE.match(line)
        if bullet_match:
            ac_id = _normalize_ac_id(bullet_match.group(1))
            ac_text = _strip_inline_markdown(bullet_match.group(2))
            if ac_id and ac_id not in seen:
                rows.append((ac_id, ac_text))
                seen.add(ac_id)
            continue
    if not rows:
        # Try Given/When/Then triplets as an AC fallback.
        synthetic_id = 0
        buffer: list[str] = []
        for line in relevant_text.splitlines():
            gwt_match = GIVEN_WHEN_THEN_RE.match(line)
            if gwt_match:
                buffer.append(f"{gwt_match.group(1).title()} {gwt_match.group(2).strip()}")
                if gwt_match.group(1).lower() == "then":
                    synthetic_id += 1
                    rows.append((f"AC-{synthetic_id}", " ".join(buffer)))
                    buffer = []
    return rows


def _normalize_ac_id(raw: str) -> str:
    cleaned = re.sub(r"\s+", "-", raw.strip().upper())
    return cleaned.replace("ACID", "AC-").replace("AC--", "AC-")


def _ac_id_key(ac_id: str) -> str:
    return ac_id.upper().replace(" ", "")


def _strip_inline_markdown(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"\1", text).strip()


# ---------- Design parsing ----------


def _resolve_design(explicit: str | None, work_item: str, repo_root: Path) -> Path | None:
    if explicit:
        return Path(explicit)
    for candidate in (
        repo_root / "specs" / "approved" / f"{work_item}.solution-design.md",
        repo_root / "specs" / "proposed" / f"{work_item}.solution-design.md",
    ):
        if candidate.exists():
            return candidate
    return None


def _extract_knowledge_references(design_text: str) -> list[dict[str, str]]:
    if not design_text:
        return []
    section = _find_section(design_text, ("knowledge references",))
    if section is None:
        return []
    return [{"label": label, "path": path} for label, path in KNOWLEDGE_REF_LINK_RE.findall(section)]


def _extract_coverage_table(design_text: str) -> dict[str, dict[str, list[str]]]:
    if not design_text:
        return {}
    section = _find_section(design_text, ("coverage table", "acceptance criteria coverage", "acceptance criteria mapping"))
    if section is None:
        return {}
    table: dict[str, dict[str, list[str]]] = {}
    for line in section.splitlines():
        line = line.rstrip()
        if not line.startswith("|"):
            continue
        if _is_separator_row(line):
            continue
        if COVERAGE_TABLE_HEADER_RE.match(line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        ac_id_raw = re.sub(r"`", "", cells[0])
        ac_id = _normalize_ac_id(ac_id_raw)
        if not ac_id.upper().startswith("AC"):
            continue
        knowledge_refs = [{"label": label, "path": path} for label, path in KNOWLEDGE_REF_LINK_RE.findall(" ".join(cells[1:]))]
        metadata_refs = _metadata_tokens(" ".join(cells[1:]))
        table[_ac_id_key(ac_id)] = {
            "row": cells,
            "knowledge_refs": knowledge_refs,
            "metadata_refs": metadata_refs,
        }
    return table


def _extract_metadata_components(design_text: str) -> set[str]:
    if not design_text:
        return set()
    section = _find_section(design_text, ("impacted metadata", "impacted salesforce metadata"))
    if section is None:
        return set()
    tokens = re.findall(r"`([A-Za-z0-9_]+(?:__c)?(?:\.[A-Za-z0-9_]+__c)?)`", section)
    return {token for token in tokens if "__" in token or token[:1].isupper()}


def _metadata_tokens(text: str) -> list[str]:
    return list({token for token in re.findall(r"`([A-Za-z0-9_]+(?:__c)?)`", text)})


def _metadata_in_entry(refs: list[str], available: set[str]) -> set[str]:
    if not refs:
        return set()
    return {ref for ref in refs if ref in available or "__" in ref}


def _find_section(design_text: str, headings: tuple[str, ...]) -> str | None:
    """Find the first section whose title contains any needle, in needle-priority order.

    Iterating by needle (rather than document order) means an explicit "Coverage
    Table" section wins over a generic "Acceptance Criteria Mapping" section
    that simply references it.
    """

    sections = list(SECTION_RE.finditer(design_text))
    for needle in headings:
        for index, match in enumerate(sections):
            title = match.group(1).lower()
            if needle in title:
                start = match.end()
                end = sections[index + 1].start() if index + 1 < len(sections) else len(design_text)
                return design_text[start:end]
    return None


def _section_map(design_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    sections = list(SECTION_RE.finditer(design_text))
    for index, match in enumerate(sections):
        title = match.group(1).strip()
        start = match.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(design_text)
        out[title] = design_text[start:end]
    return out


def _design_sections_for(ac_id: str, sections: dict[str, str], ac_text: str) -> list[str]:
    needles = {ac_id.upper(), ac_id.lower(), ac_id.replace("-", "").upper()}
    matches: list[str] = []
    keywords = [w for w in re.findall(r"[A-Za-z0-9_]{4,}", ac_text)[:4] if not w.startswith("AC")]
    for title, body in sections.items():
        if any(needle in body for needle in needles):
            matches.append(title)
        elif keywords and all(k.lower() in body.lower() for k in keywords[:2]):
            matches.append(title)
    return matches


def _is_separator_row(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell)


def _slugs_from_refs(refs: list[dict[str, str]]) -> set[str]:
    slugs: set[str] = set()
    for ref in refs:
        path = ref.get("path") or ""
        if path:
            slugs.add(Path(path).stem)
    return slugs


# ---------- Test plan + verdict ----------


def _read_qa_tests(repo_root: Path, work_item: str) -> list[str]:
    path = repo_root / "docs" / "qa-how-to-test" / f"{work_item}.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return [match.group(1).strip() for match in SECTION_RE.finditer(text)]


def _test_cases_for(ac_id: str, test_cases: list[str]) -> list[str]:
    needles = {ac_id.upper(), ac_id.lower()}
    return [title for title in test_cases if any(needle in title for needle in needles)]


def _verdict(
    ac_id: str,
    ac_text: str,
    coverage_entry: dict[str, list[str]],
    knowledge_slugs: set[str],
    metadata: set[str],
) -> dict[str, str]:
    if not coverage_entry:
        return {"status": "missing", "rationale": f"{ac_id} is not present in the design's Coverage Table."}
    cells = coverage_entry.get("row") or []
    knowledge_count = len(coverage_entry.get("knowledge_refs") or [])
    metadata_count = len(coverage_entry.get("metadata_refs") or [])
    if knowledge_count == 0 and metadata_count == 0 and len(cells) <= 2:
        return {"status": "missing", "rationale": f"{ac_id} row exists but cites no knowledge or metadata."}
    if knowledge_count and not knowledge_slugs:
        return {"status": "partial", "rationale": f"{ac_id} cites knowledge but slugs could not be resolved."}
    if knowledge_count == 0:
        return {"status": "partial", "rationale": f"{ac_id} cites metadata but no knowledge support."}
    return {
        "status": "covered",
        "rationale": f"{ac_id} cites {knowledge_count} knowledge entr(y/ies) and {metadata_count} metadata reference(s).",
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"covered": 0, "partial": 0, "missing": 0, "total": len(rows)}
    for row in rows:
        verdict = row.get("verdict") or "missing"
        if verdict in counts:
            counts[verdict] += 1
    return counts


def _render_md(work_item: str, design_path: Path | None, rows: list[dict[str, Any]], summary: dict[str, int], generated_at: str) -> str:
    lines = [
        f"# AC Coverage — {work_item}",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Design: `{design_path.as_posix() if design_path else 'missing'}`",
        f"- Summary: covered={summary['covered']} partial={summary['partial']} missing={summary['missing']} (total={summary['total']})",
        "",
    ]
    if not rows:
        lines.append("No acceptance criteria were found for this Work Item.")
        return "\n".join(lines).rstrip() + "\n"
    lines.append("| AC | Verdict | Knowledge | Metadata | Sections | Tests | Rationale |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        lines.append(
            "| {ac} | {verdict} | {knowledge} | {metadata} | {sections} | {tests} | {rationale} |".format(
                ac=row["ac_id"],
                verdict=row["verdict"],
                knowledge=", ".join(row["knowledge_slugs"]) or "—",
                metadata=", ".join(row["metadata_components"]) or "—",
                sections=", ".join(row["design_sections"]) or "—",
                tests=", ".join(row["test_cases"]) or "—",
                rationale=row["rationale"].replace("|", "\\|"),
            )
        )
    lines.extend(["", "## ACs", ""])
    for row in rows:
        lines.append(f"- **{row['ac_id']}**: {row['ac_text']}")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
