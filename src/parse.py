from __future__ import annotations

import re
from datetime import date
from typing import Any


DATE_RE = re.compile(r"\d{4}\.\d{2}\.\d{2}")
TYPE_DATE_RE = re.compile(r"^(?:\(\+(\d+)일\))?(\d{4}\.\d{2}\.\d{2})(.*)$")
DATE_HEADER_RE = re.compile(r"^(\d{4}\.\d{2}\.\d{2})\s*(.*)$")
WEEK_HEADER_RE = re.compile(r"^(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})(.*)$")
INLINE_DAILY_RE = re.compile(r"^(\d{4}\.\d{2}\.\d{2})\([가-힣]\)\s*-\s*(.+)$")
INLINE_REWARD_SPLIT_RE = re.compile(r",\s+(?=[^\d])")
MARKER_RE = re.compile(r"\[\[/?[BS]\]\]")
TRAILING_RE = re.compile(r"(\([^()]*\))+$")


def to_date(s: str) -> str:
    year, month, day = map(int, s.split("."))
    return date(year, month, day).isoformat()


def parse_by_type(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current_reward: str | None = None
    current_discontinued = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("- "):
            current_reward, current_discontinued = _parse_type_header(line)
            continue

        if current_reward is None:
            continue

        parsed = _parse_type_date_line(line)
        if parsed is None:
            continue

        records.append(
            {
                "reward_raw": current_reward,
                "date": parsed["date"],
                "stated_cycle_days": parsed["stated_cycle_days"],
                "is_discontinued": current_discontinued,
                "trailing": parsed["trailing"],
            }
        )

    return records


def parse_by_date(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_has_rows = False
    active_week_context: dict[str, Any] | None = None

    def finish_current() -> None:
        nonlocal current_has_rows
        if current is not None and not current_has_rows:
            records.append(
                {
                    **current,
                    "no_event_week": False,
                    "reward_raw": None,
                    "reward_trailing": None,
                }
            )
            current_has_rows = True

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        week_context = _parse_week_header(line)
        if week_context is not None:
            finish_current()
            active_week_context = week_context
            continue

        inline_daily = _parse_inline_daily(line, active_week_context)
        if inline_daily is not None:
            records.extend(inline_daily)
            continue

        header = _parse_date_header(line)
        if header is not None:
            finish_current()
            current = header
            current_has_rows = False
            active_week_context = None
            continue

        if current is None:
            continue

        if _is_no_event_sentinel(line):
            records.append(
                {
                    **current,
                    "no_event_week": True,
                    "reward_raw": None,
                    "reward_trailing": None,
                }
            )
            current_has_rows = True
            continue

        reward_raw, reward_trailing = _split_trailing(_strip_markers(line))
        records.append(
            {
                **current,
                "no_event_week": False,
                "reward_raw": reward_raw,
                "reward_trailing": reward_trailing,
            }
        )
        current_has_rows = True

    finish_current()
    return records


def parse_type_date_line(line: str) -> dict[str, Any] | None:
    return _parse_type_date_line(line)


def parse_date_header(line: str) -> dict[str, Any] | None:
    return _parse_date_header(line)


def split_reward_trailing(line: str) -> tuple[str, str | None]:
    return _split_trailing(_strip_markers(line))


def _parse_type_header(line: str) -> tuple[str, bool]:
    header = line[2:].strip()
    clean_header = _strip_markers(header)
    is_discontinued = clean_header.startswith("(단종)")
    if is_discontinued:
        clean_header = clean_header.replace("(단종)", "", 1)
    return clean_header.strip(), is_discontinued


def _parse_type_date_line(line: str) -> dict[str, Any] | None:
    match = TYPE_DATE_RE.match(line)
    if not match:
        return None

    cycle, raw_date, trailing = match.groups()
    trailing = trailing.strip() or None
    return {
        "date": to_date(raw_date),
        "stated_cycle_days": int(cycle) if cycle is not None else None,
        "trailing": _strip_markers(trailing) if trailing else None,
    }


def _parse_date_header(line: str) -> dict[str, Any] | None:
    clean = _strip_markers(line)
    match = DATE_HEADER_RE.match(clean)
    if not match:
        return None

    raw_date, context_text = match.groups()
    context_text = context_text.strip()
    event_context: str | None = None
    is_major_event = False

    major = re.search(r"\[\[B\]\]\s*<([^<>]+)>\s*\[\[/B\]\]", line)
    if major:
        event_context = major.group(1).strip()
        is_major_event = True
    elif context_text == "(-)" or context_text == "":
        event_context = None
    else:
        small = re.fullmatch(r"\((.*)\)", context_text)
        event_context = small.group(1).strip() if small else context_text

    return {
        "date": to_date(raw_date),
        "event_context": event_context,
        "is_major_event": is_major_event,
    }


def _parse_week_header(line: str) -> dict[str, Any] | None:
    match = WEEK_HEADER_RE.match(line)
    if not match:
        return None

    _start_date, _end_date, context_text = match.groups()
    event_context: str | None = None
    is_major_event = False

    major = re.search(r"\[\[B\]\]\s*<([^<>]+)>\s*\[\[/B\]\]", line)
    if major:
        event_context = major.group(1).strip()
        is_major_event = True
    else:
        clean_context = _strip_markers(context_text).strip()
        small = re.search(r"<([^<>]+)>", clean_context)
        if small:
            event_context = small.group(1).strip()
        elif clean_context:
            event_context = clean_context

    return {
        "event_context": event_context,
        "is_major_event": is_major_event,
    }


def _parse_inline_daily(
    line: str, active_week_context: dict[str, Any] | None
) -> list[dict[str, Any]] | None:
    match = INLINE_DAILY_RE.match(line)
    if not match:
        return None

    raw_date, reward_text = match.groups()
    context = active_week_context or {"event_context": None, "is_major_event": False}
    records: list[dict[str, Any]] = []

    for reward_part in INLINE_REWARD_SPLIT_RE.split(reward_text):
        reward_raw, reward_trailing = _split_trailing(_strip_markers(reward_part))
        records.append(
            {
                "date": to_date(raw_date),
                **context,
                "no_event_week": False,
                "reward_raw": reward_raw,
                "reward_trailing": reward_trailing,
            }
        )

    return records


def _is_no_event_sentinel(line: str) -> bool:
    return _strip_markers(line).strip() in {"아예 없음", "없음"}


def _split_trailing(line: str) -> tuple[str, str | None]:
    match = TRAILING_RE.search(line)
    if not match:
        return line.strip(), None

    if match.start() == 0:
        return line.strip(), None

    trailing = match.group(0)
    body = line[: match.start()].strip()
    return body, trailing


def _strip_markers(text: str | None) -> str:
    if text is None:
        return ""
    return MARKER_RE.sub("", text).strip()
