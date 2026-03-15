from __future__ import annotations

import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


def _strip_prefix(name: str) -> str:
    return re.sub(r"^[1-4]-", "", name)


def _parse_header_title_date(text: str) -> tuple[str, str]:
    title = ""
    date = ""
    for line in text.splitlines()[:12]:
        if line.startswith("标题："):
            title = line.split("：", 1)[1].strip()
        elif line.startswith("日期："):
            date = line.split("：", 1)[1].strip()
    return title, date


def _body_len(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    body = "\n".join(lines[4:]) if len(lines) >= 4 else ""
    return len(re.sub(r"\s+", "", body))


@dataclass
class PostRecord:
    blog_id: str
    title: str
    published_date: str
    filename: str


def _load_index(dir_path: Path) -> dict[str, PostRecord]:
    index = dir_path / "index.csv"
    if not index.exists():
        return {}
    out: dict[str, PostRecord] = {}
    with index.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            blog_id = (row.get("blog_id") or "").strip()
            if not blog_id:
                continue
            out[blog_id] = PostRecord(
                blog_id=blog_id,
                title=(row.get("title") or "").strip(),
                published_date=(row.get("published_date") or "").strip(),
                filename=(row.get("filename") or "").strip(),
            )
    return out


def _index_by_filename(index_by_blog_id: dict[str, PostRecord]) -> dict[str, PostRecord]:
    out: dict[str, PostRecord] = {}
    for rec in index_by_blog_id.values():
        if rec.filename:
            out[rec.filename] = rec
    return out


def merge_and_dedupe(
    *,
    merge_dirs: list[Path],
    out_dir: Path,
    dedupe: bool,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # blog_id -> (src_path, body_len, record)
    chosen: dict[str, tuple[Path, int, PostRecord]] = {}
    fallback_by_key: dict[tuple[str, str], tuple[Path, int, str]] = {}

    for d in merge_dirs:
        idx = _load_index(d)
        by_fname = _index_by_filename(idx)
        for txt in d.glob("*.txt"):
            name = txt.name
            # Prefer blog_id mapping when available.
            rec = by_fname.get(name)
            blog_id = rec.blog_id if rec else ""
            blen = _body_len(txt)
            if blog_id:
                rec = rec or PostRecord(blog_id=blog_id, title="", published_date="", filename=name)
                if not dedupe or blog_id not in chosen or blen > chosen[blog_id][1]:
                    chosen[blog_id] = (txt, blen, rec)
                continue

            # Fallback: (title, date) from header.
            text = txt.read_text(encoding="utf-8", errors="ignore")
            title, date = _parse_header_title_date(text)
            key = (title, date)
            if key not in fallback_by_key or blen > fallback_by_key[key][1]:
                fallback_by_key[key] = (txt, blen, name)

    # Copy chosen posts.
    copied = 0
    merged_records: list[PostRecord] = []
    for _, (src, _, rec) in chosen.items():
        dst_name = _strip_prefix(rec.filename or src.name)
        dst = out_dir / dst_name
        if dst.exists() and _body_len(dst) >= _body_len(src):
            # Keep the better (longer) body if already merged before.
            merged_records.append(
                PostRecord(
                    blog_id=rec.blog_id,
                    title=rec.title,
                    published_date=rec.published_date,
                    filename=dst.name,
                )
            )
            continue
        shutil.copy2(src, dst)
        merged_records.append(
            PostRecord(
                blog_id=rec.blog_id,
                title=rec.title,
                published_date=rec.published_date,
                filename=dst.name,
            )
        )
        copied += 1

    for _, (src, _, name) in fallback_by_key.items():
        dst_name = _strip_prefix(name)
        dst = out_dir / dst_name
        if dst.exists() and _body_len(dst) >= _body_len(src):
            continue
        shutil.copy2(src, dst)
        text = dst.read_text(encoding="utf-8", errors="ignore")
        title, date = _parse_header_title_date(text)
        merged_records.append(PostRecord(blog_id="", title=title, published_date=date, filename=dst.name))
        copied += 1

    # Write merge index
    with (out_dir / "index_merge.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["copied_posts", copied])

    # Best-effort merged index.csv (keeps blog_id for deduped posts).
    with (out_dir / "index.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["title", "published_date", "blog_id", "filename", "status", "note"])
        for rec in merged_records:
            w.writerow([rec.title, rec.published_date, rec.blog_id, rec.filename, "merged", ""])


def quality_buckets_and_rename(
    *,
    dir_path: Path,
    rename_prefix: bool,
) -> Path:
    # Map filename -> blog_id when index.csv exists (for index_quality.csv).
    blog_id_by_base_filename: dict[str, str] = {}
    idx_path = dir_path / "index.csv"
    if idx_path.exists():
        with idx_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                bid = (row.get("blog_id") or "").strip()
                fname = (row.get("filename") or "").strip()
                if not fname:
                    continue
                blog_id_by_base_filename[_strip_prefix(fname)] = bid

    files = sorted(dir_path.glob("*.txt"))
    items = [(p, _body_len(p)) for p in files]
    empty = [it for it in items if it[1] < 3]
    non_empty = [it for it in items if it[1] >= 3]
    non_empty.sort(key=lambda x: x[1])

    if non_empty:
        n = len(non_empty)
        q1 = non_empty[(n + 2) // 3 - 1][1]
        q2 = non_empty[(2 * n + 2) // 3 - 1][1]
    else:
        q1 = q2 = 0

    rows: list[dict[str, str]] = []
    for p, blen in items:
        base = _strip_prefix(p.name)
        if blen < 3:
            cls = "4"
        elif blen <= q1:
            cls = "3"
        elif blen <= q2:
            cls = "2"
        else:
            cls = "1"

        new_name = f"{cls}-{base}"
        new_path = p.with_name(new_name)
        if rename_prefix and new_path != p:
            p.rename(new_path)
            p = new_path
        rows.append(
            {
                "class": cls,
                "body_len": str(blen),
                "filename": p.name,
                "blog_id": blog_id_by_base_filename.get(base, ""),
            }
        )

    out = dir_path / "index_quality.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["class", "body_len", "filename", "blog_id"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["class"], -int(r["body_len"]), r["filename"])))
    return out
