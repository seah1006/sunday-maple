from pathlib import Path
import re

import pandas as pd

from src.parse import parse_by_type, parse_by_date
from src.normalize import normalize_reward, categorize, extract_magnitude
from src.features import compute_cycle_days, merge_is_discontinued


def load_raw_views(raw_dir: str | Path = "data/raw") -> tuple[str, str]:
    root = Path(raw_dir)
    return tuple((root / name).read_text(encoding="utf-8") for name in ["view_by_type.txt", "view_by_date.txt"])


def _is_special(row):
    text = " ".join(
        str(x)
        for x in [row.get("reward_raw"), row.get("reward_trailing"), row.get("event_context")]
        if pd.notna(x)
    )
    return "타임" in text

def _time_limited(trailing):
    if pd.isna(trailing) or trailing is None:
        return None
    text = str(trailing)
    if "하루 종일" in text or "하루종일" in text:
        return "하루 종일"
    if "오전" in text or "오후" in text or "~" in text:
        return text
    if re.search(r"\d+분", text):
        return text
    return None


def build_tidy(by_type_text: str, by_date_text: str, as_of: pd.Timestamp | str) -> tuple[pd.DataFrame, pd.DataFrame]:
    by_type_records = parse_by_type(by_type_text)
    by_date_records = parse_by_date(by_date_text)
    parsed_by_type = pd.DataFrame(
        by_type_records,
        columns=["reward_raw", "date", "stated_cycle_days", "is_discontinued", "trailing"],
    )
    parsed_by_date = pd.DataFrame(
        by_date_records,
        columns=["date", "event_context", "is_major_event", "no_event_week", "reward_raw", "reward_trailing"],
    )

    tidy_prenorm = parsed_by_date.copy()
    tidy_prenorm["is_special"] = tidy_prenorm.apply(_is_special, axis=1)
    tidy_prenorm["time_limited"] = tidy_prenorm["reward_trailing"].apply(_time_limited)
    tidy_prenorm["is_future"] = pd.to_datetime(tidy_prenorm["date"]) > pd.Timestamp(as_of)
    tidy_prenorm = tidy_prenorm[
        [
            "date",
            "reward_raw",
            "reward_trailing",
            "event_context",
            "is_major_event",
            "is_special",
            "time_limited",
            "is_future",
            "no_event_week",
        ]
    ]

    tidy = tidy_prenorm.copy()
    tidy["reward_norm"] = tidy["reward_raw"].apply(lambda value: normalize_reward(str(value)) if pd.notna(value) else None)
    tidy["category"] = tidy["reward_norm"].apply(lambda value: categorize(value) if pd.notna(value) else None)
    tidy["reward_magnitude"] = tidy["reward_raw"].apply(lambda value: extract_magnitude(str(value)) if pd.notna(value) else None)
    tidy["cycle_days"] = compute_cycle_days(tidy)
    tidy["is_discontinued"] = merge_is_discontinued(tidy, parsed_by_type)
    tidy = tidy[
        [
            "date",
            "reward_raw",
            "reward_trailing",
            "reward_norm",
            "category",
            "reward_magnitude",
            "event_context",
            "is_major_event",
            "is_special",
            "time_limited",
            "is_discontinued",
            "is_future",
            "no_event_week",
            "cycle_days",
        ]
    ]
    tidy["date"] = pd.to_datetime(tidy["date"])
    return tidy, parsed_by_type
