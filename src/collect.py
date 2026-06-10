from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Final
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


MAIN_URL: Final[str] = "https://www.inven.co.kr/board/maple/2304/20563"
DEFAULT_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36 SundayMapleAnalysis/1.0"
)


def fetch_inven_post(url: str, *, user_agent: str, timeout: int = 10) -> requests.Response:
    robots_url = urljoin(url, "/robots.txt")
    robots = RobotFileParser()
    robots.set_url(robots_url)
    robots.read()
    if not robots.can_fetch(user_agent, url):
        raise PermissionError(f"robots.txt disallows fetching {url}")

    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    resp.raise_for_status()
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp


def save_raw_html(resp: requests.Response, out_dir: str, slug: str) -> dict:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    html_path = out_path / f"{slug}.html"
    meta_path = out_path / f"{slug}_meta.json"

    if html_path.exists():
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))
        raise FileExistsError(f"{html_path} exists but {meta_path} is missing")

    meta = {
        "url": resp.url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "status_code": resp.status_code,
        "content_length": len(resp.content),
        "encoding": resp.encoding,
        "robots_url": urljoin(resp.url, "/robots.txt"),
        "robots_allowed": True,
        "user_agent": resp.request.headers.get("User-Agent", ""),
    }
    html_path.write_text(resp.text, encoding="utf-8")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def extract_views(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one("#powerbbsContent")
    if content is None:
        raise ValueError("Article body selector #powerbbsContent was not found")

    lines = _clean_lines(_marked_text(content).splitlines())
    by_type_start = _find_exact_line(lines, "종류별(가나다순)")
    by_date_start = _find_exact_line(lines, "[[B]]날짜별[[/B]]")

    by_type = "\n".join(lines[by_type_start + 1 : by_date_start]).strip() + "\n"
    by_date = "\n".join(lines[by_date_start + 1 :]).strip() + "\n"
    return {"by_type": by_type, "by_date": by_date}


def collect_main(out_dir: str = "data/raw") -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    slug = "inven_20563"
    html_path = out_path / f"{slug}.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
    else:
        resp = fetch_inven_post(MAIN_URL, user_agent=DEFAULT_USER_AGENT)
        save_raw_html(resp, str(out_path), slug)
        html = html_path.read_text(encoding="utf-8")

    views = extract_views(html)
    targets = {
        "by_type": out_path / "view_by_type.txt",
        "by_date": out_path / "view_by_date.txt",
    }
    for key, path in targets.items():
        if not path.exists():
            path.write_text(views[key], encoding="utf-8")


def _marked_text(node: Tag | NavigableString) -> str:
    if isinstance(node, NavigableString):
        return str(node).replace("\xa0", " ")
    if not isinstance(node, Tag):
        return ""
    if node.name == "br":
        return "\n"

    inner = "".join(_marked_text(child) for child in node.children)
    style = node.get("style") or ""
    if node.name in {"b", "strong"} or "font-weight: 700" in style:
        inner = f"[[B]]{inner}[[/B]]"
    if node.name in {"s", "strike", "del"}:
        inner = f"[[S]]{inner}[[/S]]"
    if node.name in {"div", "p", "li"}:
        return inner + "\n"
    return inner


def _clean_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        text = " ".join(line.strip().split())
        markerless = text.replace("[[B]]", "").replace("[[/B]]", "")
        markerless = markerless.replace("[[S]]", "").replace("[[/S]]", "").strip()
        if markerless:
            cleaned.append(text)
    return cleaned


def _find_line(lines: list[str], needle: str) -> int:
    for idx, line in enumerate(lines):
        if needle in line:
            return idx
    raise ValueError(f"Could not find line containing {needle!r}")


def _find_exact_line(lines: list[str], needle: str) -> int:
    for idx, line in enumerate(lines):
        if line == needle:
            return idx
    raise ValueError(f"Could not find exact line {needle!r}")
