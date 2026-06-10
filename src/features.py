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
