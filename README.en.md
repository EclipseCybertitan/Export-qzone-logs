# qzone-text-exporter

Export QQ Qzone blog posts into auditable, searchable, offline-friendly plain text files, with a privacy-first postprocessing pipeline (merge, dedupe, quality buckets, indexes).

One-line positioning: this is a prep tool that turns "blog posts" into "local private AI diary/log (RAG/knowledge base) ready inputs".

Signature: 月蚀之夜

Contact: tasks-09swapper@icloud.com

## What This Is (and Isn't)

- Scope: Qzone blog posts only (no photos/albums/messages/statuses).
- Privacy: cookies are read from a local `--cookie-file` (never pass cookies via CLI args).
- Robustness: endpoint fallback + loose JSONP parsing + HTML body extraction that avoids nested-`div` truncation.
- Postprocess built-in: merge multiple export runs, dedupe, bucket by body length, idempotent prefix renaming, and CSV indexes.

## Install

```bash
python -m pip install .
```

Or via `pipx`:

```bash
pipx install .
```

## Usage

1) Create a local cookie file (never commit it):

```text
p_skey=...; skey=...; uin=o<UIN>; p_uin=o<UIN>; pt4_token=...;
```

2) Export:

```bash
qzone-text-exporter export \
  --uin <UIN> \
  --cookie-file /path/to/cookie.txt \
  --out-dir /path/to/exports
```

Outputs:

- `qzone_logs_all.csv` (title, published_date, blog_id)
- one `.txt` per post: `<title> - <YYYY-MM-DD>.txt`
- `index.csv` (status/errors for resume and troubleshooting)

3) Postprocess:

```bash
qzone-text-exporter postprocess \
  --out-dir /path/to/merged \
  --merge-dirs /path/to/exports1,/path/to/exports2 \
  --dedupe --quality-buckets --rename-prefix
```

## Security Notes

Read `SECURITY.md`. Do not paste cookies into issues/PRs/logs/screenshots. Do not commit your exported diary/log texts.

## Why Another Tool?

Related projects exist, for example:

- [ShunCai/QZoneExport](https://github.com/ShunCai/QZoneExport) (browser extension, broader "full backup" scope)
- Python API wrappers such as [aioqzone](https://pypi.org/project/aioqzone/)

This project is intentionally narrower: text-first export + postprocess pipeline as a first-class workflow, specifically for building local-private diary/log assets.

