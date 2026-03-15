from __future__ import annotations

import argparse
from pathlib import Path

from . import export as exporter
from . import postprocess


def _read_cookie_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").replace("\r", " ").replace("\n", " ").strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qzone-text-exporter")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_export = sub.add_parser("export", help="Export Qzone blog posts to text files.")
    p_export.add_argument("--uin", required=True, help="QQ number (no default).")
    p_export.add_argument("--cookie-file", required=True, help="Local cookie header file path.")
    p_export.add_argument("--out-dir", required=True, help="Output directory.")
    p_export.add_argument("--resume", action="store_true", help="Skip already-exported posts if file exists.")
    p_export.add_argument("--rate-limit-ms", type=int, default=500, help="Delay between requests (ms).")
    p_export.add_argument("--retry", type=int, default=3, help="Retries per endpoint.")
    p_export.add_argument("--max-posts", type=int, help="Export at most N posts (debug).")
    p_export.add_argument("--timeout-s", type=int, default=30, help="HTTP timeout seconds.")

    p_post = sub.add_parser("postprocess", help="Merge/dedupe/quality-bucket exports.")
    p_post.add_argument("--out-dir", required=True, help="Output directory.")
    p_post.add_argument("--merge-dirs", required=True, help="Comma-separated list of export dirs.")
    p_post.add_argument("--dedupe", action="store_true", help="Dedupe by blog_id when possible.")
    p_post.add_argument("--quality-buckets", action="store_true", help="Compute quality buckets.")
    p_post.add_argument("--rename-prefix", action="store_true", help="Prefix rename 1-/2-/3-/4- (idempotent).")

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.cmd == "export":
        cookie_text = _read_cookie_file(Path(args.cookie_file))
        cookies = exporter.parse_cookie_header(cookie_text)
        cookie_header = exporter.cookie_header_from_dict(cookies)
        exporter.export(
            cookie_header=cookie_header,
            uin=exporter.normalize_uin(args.uin),
            out_dir=Path(args.out_dir),
            resume=args.resume,
            rate_limit_ms=args.rate_limit_ms,
            retries=args.retry,
            max_posts=args.max_posts,
            timeout_s=args.timeout_s,
        )
        return

    if args.cmd == "postprocess":
        out_dir = Path(args.out_dir)
        merge_dirs = [Path(p.strip()) for p in args.merge_dirs.split(",") if p.strip()]
        postprocess.merge_and_dedupe(merge_dirs=merge_dirs, out_dir=out_dir, dedupe=args.dedupe)
        if args.quality_buckets:
            postprocess.quality_buckets_and_rename(dir_path=out_dir, rename_prefix=args.rename_prefix)
        return

    raise SystemExit("Unknown command.")

