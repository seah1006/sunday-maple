from __future__ import annotations

import pandas as pd


def compute_cycle_days(tidy: pd.DataFrame) -> pd.Series:
    required = {"date", "reward_norm"}
    missing = required - set(tidy.columns)
    if missing:
        raise KeyError(f"missing required columns: {sorted(missing)}")

    result = pd.Series(pd.NA, index=tidy.index, dtype="Int64", name="cycle_days")
    scored = tidy.loc[tidy["reward_norm"].notna(), ["date", "reward_norm"]].copy()
    if scored.empty:
        return result

    scored["date"] = pd.to_datetime(scored["date"])
    unique_days = (
        scored.drop_duplicates(["date", "reward_norm"])
        .sort_values(["reward_norm", "date"])
        .copy()
    )
    unique_days["cycle_days"] = (
        unique_days.groupby("reward_norm")["date"].diff().dt.days.astype("Int64")
    )

    merged = scored.merge(unique_days, on=["date", "reward_norm"], how="left")["cycle_days"]
    result.loc[scored.index] = merged.to_numpy()
    return result


def merge_is_discontinued(tidy: pd.DataFrame, parsed_by_type: pd.DataFrame) -> pd.Series:
    for frame_name, frame in [("tidy", tidy), ("parsed_by_type", parsed_by_type)]:
        if "reward_raw" not in frame.columns:
            raise KeyError(f"{frame_name} missing required column: reward_raw")
    if "is_discontinued" not in parsed_by_type.columns:
        raise KeyError("parsed_by_type missing required column: is_discontinued")

    discontinued = set(
        parsed_by_type.loc[
            parsed_by_type["is_discontinued"].astype("boolean").fillna(False),
            "reward_raw",
        ]
        .dropna()
        .unique()
    )

    result = pd.Series(pd.NA, index=tidy.index, dtype="boolean", name="is_discontinued")
    non_null_raw = tidy["reward_raw"].notna()
    trailing = tidy.get("reward_trailing", pd.Series(pd.NA, index=tidy.index))

    body = tidy.loc[non_null_raw, "reward_raw"].astype(str)
    full = body + trailing.loc[non_null_raw].fillna("").astype(str)
    flags = body.isin(discontinued) | full.isin(discontinued)
    result.loc[non_null_raw] = flags.astype("boolean").to_numpy()
    return result
