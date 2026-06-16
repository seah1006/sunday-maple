from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "days_since_last",
    "past_count",
    "past_rate",
    "roll_gap_mean",
    "roll_gap_median",
    "lag1_appeared",
    "category",
    "month",
    "quarter",
    "weekofyear",
]

DEFAULT_RECENCY_GATE_DAYS = 180
DOMAIN_DISCONTINUED = {"스타포스_1+1강화"}


def _eligible_rows(tidy: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "reward_norm", "category", "is_future", "no_event_week"}
    missing = required - set(tidy.columns)
    if missing:
        raise KeyError(f"missing required columns: {sorted(missing)}")

    frame = tidy.loc[
        ~tidy["is_future"].astype("boolean").fillna(False)
        & ~tidy["no_event_week"].astype("boolean").fillna(False),
        ["date", "reward_norm", "category"],
    ].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.loc[frame["reward_norm"].notna()].copy()


def _candidate_rewards(eligible: pd.DataFrame, top_n: int) -> list[str]:
    if top_n < 1:
        raise ValueError("top_n must be >= 1")

    counts = (
        eligible.drop_duplicates(["date", "reward_norm"])["reward_norm"]
        .value_counts()
        .rename_axis("reward_norm")
        .reset_index(name="count")
        .sort_values(["count", "reward_norm"], ascending=[False, True], kind="mergesort")
    )
    return counts["reward_norm"].head(top_n).tolist()


def gate_candidates(
    eligible: pd.DataFrame,
    candidates: list[str],
    target_date: pd.Timestamp | str,
    recency_gate_days: int | None = DEFAULT_RECENCY_GATE_DAYS,
    domain_discontinued: set[str] | frozenset[str] | None = None,
) -> list[str]:
    target = pd.to_datetime(target_date)
    discontinued = DOMAIN_DISCONTINUED if domain_discontinued is None else set(domain_discontinued)
    observed = eligible.drop_duplicates(["date", "reward_norm"])
    result = []

    for reward in candidates:
        if reward in discontinued:
            continue
        if recency_gate_days is None:
            result.append(reward)
            continue
        prior_dates = observed.loc[
            (observed["reward_norm"] == reward) & (observed["date"] < target),
            "date",
        ]
        if prior_dates.empty:
            continue
        days_since_last = int((target - prior_dates.max()).days)
        if days_since_last <= recency_gate_days:
            result.append(reward)

    return result


def _category_map(eligible: pd.DataFrame) -> dict[str, object]:
    values = {}
    for reward, group in eligible.dropna(subset=["category"]).groupby("reward_norm"):
        mode = group["category"].mode()
        values[reward] = mode.iloc[0] if not mode.empty else pd.NA
    return values


def build_prediction_frame(
    tidy: pd.DataFrame,
    top_n: int = 20,
    roll_k: int = 5,
    candidate_cutoff: pd.Timestamp | str | None = None,
) -> pd.DataFrame:
    if roll_k < 1:
        raise ValueError("roll_k must be >= 1")

    eligible = _eligible_rows(tidy)
    if eligible.empty:
        columns = ["date", "reward_norm", "y", *FEATURE_COLUMNS]
        return pd.DataFrame(columns=columns)

    dates = pd.Index(sorted(eligible["date"].drop_duplicates()), name="date")
    candidate_source = eligible
    if candidate_cutoff is not None:
        cutoff = pd.to_datetime(candidate_cutoff)
        candidate_source = eligible.loc[eligible["date"] < cutoff]
        if candidate_source.empty:
            raise ValueError("candidate_cutoff leaves no eligible rows for candidate selection")
    candidates = _candidate_rewards(candidate_source, top_n)
    categories = _category_map(eligible)
    observed = eligible.drop_duplicates(["date", "reward_norm"])
    rewards_by_date = {
        date: set(group["reward_norm"])
        for date, group in observed.groupby("date", sort=False)
    }
    dates_by_reward = {
        reward: list(group["date"].sort_values())
        for reward, group in observed.groupby("reward_norm", sort=False)
    }
    first_date = dates.min()
    rows = []

    for date_pos, date in enumerate(dates):
        previous_date = dates[date_pos - 1] if date_pos else None
        current_rewards = rewards_by_date.get(date, set())
        previous_rewards = rewards_by_date.get(previous_date, set()) if previous_date is not None else set()

        for reward in candidates:
            reward_dates = dates_by_reward.get(reward, [])
            prior_dates = [seen for seen in reward_dates if seen < date]
            past_count = len(prior_dates)
            if prior_dates:
                days_since_last = int((date - prior_dates[-1]).days)
            else:
                days_since_last = int((date - first_date).days)

            gaps = pd.Series(prior_dates).diff().dropna().dt.days.to_numpy() if len(prior_dates) >= 2 else np.array([])
            recent_gaps = gaps[-roll_k:]

            rows.append(
                {
                    "date": date,
                    "reward_norm": reward,
                    "y": int(reward in current_rewards),
                    "days_since_last": days_since_last,
                    "past_count": past_count,
                    "past_rate": past_count / date_pos if date_pos else 0.0,
                    "roll_gap_mean": float(np.mean(recent_gaps)) if len(recent_gaps) else np.nan,
                    "roll_gap_median": float(np.median(recent_gaps)) if len(recent_gaps) else np.nan,
                    "lag1_appeared": int(reward in previous_rewards),
                    "category": categories.get(reward, pd.NA),
                    "month": int(date.month),
                    "quarter": int(date.quarter),
                    "weekofyear": int(date.isocalendar().week),
                }
            )

    return pd.DataFrame(rows, columns=["date", "reward_norm", "y", *FEATURE_COLUMNS])


def build_inference_frame(
    tidy: pd.DataFrame,
    target_date: pd.Timestamp | str,
    top_n: int = 20,
    roll_k: int = 5,
    candidate_cutoff: pd.Timestamp | str | None = None,
    recency_gate_days: int | None = DEFAULT_RECENCY_GATE_DAYS,
    domain_discontinued: set[str] | frozenset[str] | None = None,
) -> pd.DataFrame:
    if roll_k < 1:
        raise ValueError("roll_k must be >= 1")

    target = pd.to_datetime(target_date)
    eligible = _eligible_rows(tidy)
    columns = ["date", "reward_norm", *FEATURE_COLUMNS]
    if eligible.empty:
        return pd.DataFrame(columns=columns)

    candidate_source = eligible
    if candidate_cutoff is not None:
        cutoff = pd.to_datetime(candidate_cutoff)
        candidate_source = eligible.loc[eligible["date"] < cutoff]
        if candidate_source.empty:
            raise ValueError("candidate_cutoff leaves no eligible rows for candidate selection")

    candidates = gate_candidates(
        eligible,
        _candidate_rewards(candidate_source, top_n),
        target,
        recency_gate_days=recency_gate_days,
        domain_discontinued=domain_discontinued,
    )
    categories = _category_map(eligible)
    observed = eligible.drop_duplicates(["date", "reward_norm"])
    prior_dates_index = pd.Index(sorted(observed.loc[observed["date"] < target, "date"].drop_duplicates()), name="date")
    previous_date = prior_dates_index[-1] if len(prior_dates_index) else None
    previous_rewards = (
        set(observed.loc[observed["date"] == previous_date, "reward_norm"])
        if previous_date is not None
        else set()
    )
    dates_by_reward = {
        reward: list(group["date"].sort_values())
        for reward, group in observed.groupby("reward_norm", sort=False)
    }
    first_date = pd.Index(sorted(observed["date"].drop_duplicates())).min()
    rows = []

    for reward in candidates:
        reward_dates = dates_by_reward.get(reward, [])
        prior_dates = [seen for seen in reward_dates if seen < target]
        past_count = len(prior_dates)
        if prior_dates:
            days_since_last = int((target - prior_dates[-1]).days)
        else:
            days_since_last = int((target - first_date).days)

        gaps = pd.Series(prior_dates).diff().dropna().dt.days.to_numpy() if len(prior_dates) >= 2 else np.array([])
        recent_gaps = gaps[-roll_k:]

        rows.append(
            {
                "date": target,
                "reward_norm": reward,
                "days_since_last": days_since_last,
                "past_count": past_count,
                "past_rate": past_count / len(prior_dates_index) if len(prior_dates_index) else 0.0,
                "roll_gap_mean": float(np.mean(recent_gaps)) if len(recent_gaps) else np.nan,
                "roll_gap_median": float(np.median(recent_gaps)) if len(recent_gaps) else np.nan,
                "lag1_appeared": int(reward in previous_rewards),
                "category": categories.get(reward, pd.NA),
                "month": int(target.month),
                "quarter": int(target.quarter),
                "weekofyear": int(target.isocalendar().week),
            }
        )

    return pd.DataFrame(rows, columns=columns)


def write_prediction_frame(
    tidy_path: str | Path = "data/processed/tidy_rewards.csv",
    output_path: str | Path = "data/interim/predict_dataset.csv",
    top_n: int = 20,
    roll_k: int = 5,
    candidate_cutoff: pd.Timestamp | str | None = None,
) -> pd.DataFrame:
    frame = build_prediction_frame(
        pd.read_csv(tidy_path),
        top_n=top_n,
        roll_k=roll_k,
        candidate_cutoff=candidate_cutoff,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    return frame


if __name__ == "__main__":
    write_prediction_frame()
