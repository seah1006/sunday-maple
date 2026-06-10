from __future__ import annotations

import pandas as pd


def compute_cycle_days(tidy: pd.DataFrame) -> pd.Series:
    """Return norm-level recurrence gaps aligned to the input tidy index.

    The feature is computed on unique (date, reward_norm) observations, then
    merged back so same-day bundles sharing a norm receive the same value.
    Rows with null reward_norm keep NA.
    """
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
    """Return raw-level discontinued flags aligned to the input tidy index.

    `reward_raw` null rows stay missing. Non-null raw rewards absent from
    parsed_by_type default to False, with the notebook reporting those misses.
    Conflicting by_type flags for the same raw reward are rejected.
    """
    for frame_name, frame in [("tidy", tidy), ("parsed_by_type", parsed_by_type)]:
        if "reward_raw" not in frame.columns:
            raise KeyError(f"{frame_name} missing required column: reward_raw")
    if "is_discontinued" not in parsed_by_type.columns:
        raise KeyError("parsed_by_type missing required column: is_discontinued")

    result = pd.Series(pd.NA, index=tidy.index, dtype="boolean", name="is_discontinued")
    mapping_source = parsed_by_type.loc[
        parsed_by_type["reward_raw"].notna(), ["reward_raw", "is_discontinued"]
    ].copy()
    mapping_source["is_discontinued"] = mapping_source["is_discontinued"].astype("boolean")

    mixed = mapping_source.groupby("reward_raw")["is_discontinued"].nunique(dropna=True)
    mixed = mixed[mixed > 1]
    if not mixed.empty:
        raise ValueError(f"conflicting is_discontinued flags for reward_raw: {mixed.index.tolist()}")

    mapping = mapping_source.drop_duplicates("reward_raw").set_index("reward_raw")["is_discontinued"]
    non_null_raw = tidy["reward_raw"].notna()
    merged = tidy.loc[non_null_raw, "reward_raw"].map(mapping)
    result.loc[non_null_raw] = merged.fillna(False).astype("boolean").to_numpy()
    return result
