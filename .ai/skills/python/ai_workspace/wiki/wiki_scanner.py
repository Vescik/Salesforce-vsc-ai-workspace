"""Scan a local Azure DevOps Wiki Git repository."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

MAX_TEXT_FILE_BYTES = 1024 * 1024


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a local Azure DevOps Wiki repository.")
    parser.add_argument("--wiki-dir", required=True)
    parser.add_argument("--out", default=".ai/outputs/wiki/wiki-index.json")
    args = parser.parse_args(argv)

    index = scan_wiki(Path(args.wiki_dir))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Indexed {len(index['pages'])} wiki page(s).")
    print(f"Wrote {out_path}")
    return 0


def scan_wiki(wiki_dir: str | Path) -> dict[str, Any]:
    """Return a deterministic index of markdown pages and folders."""

    root = Path(wiki_dir).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Wiki directory does not exist: {root}")
    orders = read_order_files(root)
    pages = build_page_index(root, orders)
    folders = _build_folder_index(root, pages, orders)
    return {
        "wiki_dir": root.as_posix(),
        "pages": pages,
        "folders": folders,
        "order_files": orders,
    }


def read_order_files(wiki_dir: str | Path) -> dict[str, list[str]]:
    root = Path(wiki_dir).resolve()
    orders: dict[str, list[str]] = {}
    for order_file in sorted(root.rglob(".order")):
        if _skip_path(order_file, root):
            continue
        folder = "/" + order_file.parent.relative_to(root).as_posix()
        if folder == "/.":
            folder = "/"
        entries = [
            line.strip()
            for line in order_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]
        orders[normalize_wiki_path(folder)] = entries
    return orders


def build_page_index(wiki_dir: str | Path, orders: dict[str, list[str]] | None = None) -> list[dict[str, Any]]:
    root = Path(wiki_dir).resolve()
    orders = orders or read_order_files(root)
    pages: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        if _skip_path(path, root) or not _safe_text_file(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        wiki_path = infer_page_path(path, root)
        folder = normalize_wiki_path("/" + path.parent.relative_to(root).as_posix())
        if folder == "/.":
            folder = "/"
        title = extract_markdown_title(path, text)
        headings = extract_headings(path, text)
        order_entries = orders.get(folder, [])
        order_key = path.stem
        order_position = order_entries.index(order_key) + 1 if order_key in order_entries else None
        pages.append(
            {
                "path": wiki_path,
                "file_path": path.relative_to(root).as_posix(),
                "title": title,
                "headings": headings,
                "folder": folder,
                "keywords": sorted(tokenize_text(" ".join([wiki_path, title, " ".join(headings)]))),
                "order_position": order_position,
            }
        )
    return pages


def extract_markdown_title(path: str | Path, text: str | None = None) -> str:
    source = Path(path)
    text = text if text is not None else source.read_text(encoding="utf-8", errors="replace")
    front_matter_title = _front_matter_title(text)
    if front_matter_title:
        return front_matter_title
    for line in text.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return source.stem.replace("-", " ")


def extract_headings(path: str | Path, text: str | None = None) -> list[str]:
    source = Path(path)
    text = text if text is not None else source.read_text(encoding="utf-8", errors="replace")
    headings: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(2).strip())
    return headings[:40]


def infer_page_path(file_path: str | Path, wiki_dir: str | Path | None = None) -> str:
    file_path = Path(file_path)
    if wiki_dir is not None:
        relative = file_path.resolve().relative_to(Path(wiki_dir).resolve())
    else:
        relative = file_path
    without_suffix = relative.with_suffix("").as_posix()
    return normalize_wiki_path("/" + without_suffix)


def normalize_wiki_path(path: str | Path) -> str:
    text = str(path).replace("\\", "/").strip()
    if not text:
        return "/"
    while "//" in text:
        text = text.replace("//", "/")
    if not text.startswith("/"):
        text = "/" + text
    if len(text) > 1:
        text = text.rstrip("/")
    return text


def tokenize_text(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]+", text)
        if len(token) >= 3
    }


def _build_folder_index(root: Path, pages: list[dict[str, Any]], orders: dict[str, list[str]]) -> list[dict[str, Any]]:
    folders: dict[str, set[str]] = {}
    for page in pages:
        folder = str(page["folder"])
        folders.setdefault(folder, set()).add(str(page["path"]))
        parent = folder
        while parent and parent != "/":
            parent = normalize_wiki_path(str(Path(parent).parent))
            folders.setdefault(parent, set()).add(folder)
    for order_folder in orders:
        folders.setdefault(order_folder, set())
    return [
        {
            "path": folder,
            "children": sorted(children),
            "has_order_file": folder in orders,
        }
        for folder, children in sorted(folders.items())
    ]


def _front_matter_title(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:40]:
        if line.strip() == "---":
            break
        match = re.match(r"^\s*title:\s*[\"']?(.+?)[\"']?\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def _skip_path(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return True
    return ".git" in relative.parts


def _safe_text_file(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_TEXT_FILE_BYTES:
            return False
        sample = path.read_bytes()[:2048]
    except OSError:
        return False
    return b"\x00" not in sample


if __name__ == "__main__":
    raise SystemExit(main())
