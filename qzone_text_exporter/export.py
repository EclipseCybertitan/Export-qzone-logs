from __future__ import annotations

import csv
import re
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import extract, net


BLOG_LIST_URLS = [
    "https://rc.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_abs",
    "https://rc.qzone.qq.com/proxy/domain/b11.qzone.qq.com/cgi-bin/blognew/get_abs",
    "https://user.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_abs",
    "https://user.qzone.qq.com/proxy/domain/b11.qzone.qq.com/cgi-bin/blognew/get_abs",
    "https://h5.qzone.qq.com/proxy/domain/b11.qzone.qq.com/cgi-bin/blognew/get_abs",
]

BLOG_OUTPUT_URLS = [
    "https://rc.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/blog_output_data",
    "https://rc.qzone.qq.com/proxy/domain/b11.qzone.qq.com/cgi-bin/blognew/blog_output_data",
    "https://user.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/blog_output_data",
]

BLOG_LIST_REFERER_URL = (
    "https://rc.qzone.qq.com/proxy/domain/"
    "qzonestyle.gtimg.cn/qzone/app/blog/v6/bloglist.html#nojump=1&page=1&catalog=list"
)


@dataclass
class BlogEntry:
    blog_id: str
    title: str
    published_date: str


def parse_cookie_header(cookie_header: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies[name.strip()] = value.strip()
    return cookies


def cookie_header_from_dict(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def normalize_uin(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("o") and raw[1:].isdigit():
        return raw[1:]
    return raw


def get_g_tk(skey: str) -> int:
    h = 5381
    for c in skey:
        h += (h << 5) + ord(c)
    return h & 0x7FFFFFFF


def sanitize_filename(text: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
    return cleaned[:120] or "untitled"


def unique_output_path(folder: Path, base_name: str, suffix: str, blog_id: str) -> Path:
    candidate = folder / f"{base_name}{suffix}"
    if not candidate.exists():
        return candidate
    candidate = folder / f"{base_name} ({blog_id}){suffix}"
    if not candidate.exists():
        return candidate
    counter = 2
    while True:
        candidate = folder / f"{base_name} ({blog_id}-{counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def fetch_list_page(
    cookie_header: str,
    uin: str,
    g_tk: int,
    *,
    pos: int,
    num: int,
    retries: int,
    rate_limit_ms: int,
    timeout_s: int,
) -> dict:
    headers = {
        "Cookie": cookie_header,
        "Referer": BLOG_LIST_REFERER_URL,
        "User-Agent": "Mozilla/5.0",
    }
    params = {
        "hostUin": uin,
        "uin": uin,
        "blogType": 0,
        "cateName": "",
        "cateHex": "",
        "statYear": "",
        "reqInfo": 1,
        "pos": pos,
        "num": num,
        "sortType": 0,
        "absType": 0,
        "startTime": "",
        "endTime": "",
        "source": 0,
        "rand": f"{time.time():.6f}",
        "ref": "qzone",
        "g_tk": g_tk,
        "format": "jsonp",
        "iNotice": "0",
        "inCharset": "utf-8",
        "outCharset": "utf-8",
    }
    resp = net.try_get_json(
        BLOG_LIST_URLS,
        params,
        headers,
        timeout_s=timeout_s,
        retries=retries,
        rate_limit_ms=rate_limit_ms,
    )
    return resp.get("data") or {}


def fetch_blog_output(
    cookie_header: str,
    uin: str,
    blog_id: str,
    *,
    retries: int,
    rate_limit_ms: int,
    timeout_s: int,
) -> bytes:
    headers = {
        "Cookie": cookie_header,
        "Referer": BLOG_LIST_REFERER_URL,
        "User-Agent": "Mozilla/5.0",
    }
    params = {
        "uin": uin,
        "blogid": blog_id,
        "styledm": "qzonestyle.gtimg.cn",
        "imgdm": "qzs.qq.com",
        "bdm": "b.qzone.qq.com",
        "mode": 2,
        "numperpage": 15,
        "timestamp": int(datetime.now().timestamp()),
        "dprefix": "",
        "inCharset": "gb2312",
        "outCharset": "gb2312",
        "ref": "qzone",
        "page": 1,
        "refererurl": BLOG_LIST_REFERER_URL,
        "g_iframeUser": 1,
    }
    return net.try_get_bytes(
        BLOG_OUTPUT_URLS,
        params,
        headers,
        timeout_s=timeout_s,
        retries=retries,
        rate_limit_ms=rate_limit_ms,
    )


def collect_all_entries(
    cookie_header: str,
    uin: str,
    *,
    max_posts: int | None,
    retries: int,
    rate_limit_ms: int,
    timeout_s: int,
) -> list[BlogEntry]:
    parsed = parse_cookie_header(cookie_header)
    skey = urllib.parse.unquote(parsed.get("skey") or parsed.get("p_skey") or "")
    if not skey:
        raise ValueError("Cookie is missing skey or p_skey.")
    g_tk = get_g_tk(skey)

    entries: list[BlogEntry] = []
    pos = 0
    page_size = 15
    while True:
        data = fetch_list_page(
            cookie_header,
            uin,
            g_tk,
            pos=pos,
            num=page_size,
            retries=retries,
            rate_limit_ms=rate_limit_ms,
            timeout_s=timeout_s,
        )
        items = data.get("list") or []
        if not items:
            break
        for item in items:
            bid = str(item.get("blogId") or "")
            if not bid:
                continue
            title = (item.get("title") or "").strip()
            pub_time = str(item.get("pubTime") or "").strip()
            published_date = pub_time.split(" ")[0] if pub_time else ""
            entries.append(BlogEntry(blog_id=bid, title=title, published_date=published_date))
            if max_posts is not None and max_posts > 0 and len(entries) >= max_posts:
                return entries
        pos += len(items)
        total = int(data.get("totalNum") or 0)
        if total and pos >= total:
            break
    return entries


def export(
    *,
    cookie_header: str,
    uin: str,
    out_dir: Path,
    resume: bool,
    rate_limit_ms: int,
    retries: int,
    max_posts: int | None,
    timeout_s: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = collect_all_entries(
        cookie_header,
        uin,
        max_posts=max_posts,
        retries=retries,
        rate_limit_ms=rate_limit_ms,
        timeout_s=timeout_s,
    )

    csv_path = out_dir / "qzone_logs_all.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["title", "published_date", "blog_id"])
        for e in entries:
            w.writerow([e.title, e.published_date, e.blog_id])

    index_path = out_dir / "index.csv"
    with index_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["title", "published_date", "blog_id", "filename", "status", "note"])

        for i, e in enumerate(entries, start=1):
            title = e.title or "untitled"
            date = e.published_date or "undated"
            base_name = sanitize_filename(f"{title} - {date}")
            out_path = unique_output_path(out_dir, base_name, ".txt", e.blog_id)

            if resume and out_path.exists() and out_path.stat().st_size > 16:
                w.writerow([e.title, e.published_date, e.blog_id, out_path.name, "skipped", "resume"])
                continue

            status = "ok"
            note = ""
            try:
                raw = fetch_blog_output(
                    cookie_header,
                    uin,
                    e.blog_id,
                    retries=retries,
                    rate_limit_ms=rate_limit_ms,
                    timeout_s=timeout_s,
                )
                body = extract.html_to_text(raw)
                text = "\n".join([f"标题：{e.title}", f"日期：{e.published_date}", "分类：日志", "", body]).strip() + "\n"
                out_path.write_text(text, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                status = "failed"
                note = str(exc)
            w.writerow([e.title, e.published_date, e.blog_id, out_path.name, status, note])

            if i % 50 == 0 or i == len(entries):
                print(f"Post export progress: {i}/{len(entries)}", flush=True)

