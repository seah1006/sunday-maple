from __future__ import annotations

import pandas as pd

from src.predict_dataset import (
    DEFAULT_RECENCY_GATE_DAYS,
    DOMAIN_DISCONTINUED,
    _candidate_rewards,
    _eligible_rows,
    gate_candidates,
)


def build_weekly_series(tidy: pd.DataFrame, reward_norm: str, as_of: pd.Timestamp | str) -> pd.DataFrame:
    target = pd.to_datetime(as_of)
    eligible = _eligible_rows(tidy)
    history = eligible.loc[eligible["date"] < target].copy()
    history = history.loc[history["date"].dt.dayofweek == 6]
    if history.empty:
        return pd.DataFrame(columns=["ds", "y"])

    dates = pd.date_range(history["date"].min(), history["date"].max(), freq="W-SUN")
    appeared = set(history.loc[history["reward_norm"] == reward_norm, "date"])
    return pd.DataFrame(
        {
            "ds": dates,
            "y": [1 if date in appeared else 0 for date in dates],
        }
    )


def fit_predict_reward(series_df: pd.DataFrame, target_dates: list[pd.Timestamp] | pd.DatetimeIndex) -> pd.DataFrame:
    from prophet import Prophet

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        uncertainty_samples=0,
    )
    model.add_seasonality(name="cycle28", period=28, fourier_order=5)
    model.fit(series_df)
    future = pd.DataFrame({"ds": pd.to_datetime(target_dates)})
    forecast = model.predict(future)
    return forecast[["ds", "yhat"]].copy()


def rank_candidates(
    tidy: pd.DataFrame,
    candidates: list[str] | None,
    as_of: pd.Timestamp | str,
    target_date: pd.Timestamp | str,
    gate_fn=gate_candidates,
    top_n: int = 20,
    candidate_cutoff: pd.Timestamp | str | None = None,
    recency_gate_days: int | None = DEFAULT_RECENCY_GATE_DAYS,
    domain_discontinued: set[str] | frozenset[str] | None = None,
    predict_func=fit_predict_reward,
) -> pd.DataFrame:
    eligible = _eligible_rows(tidy)
    candidate_source = eligible
    if candidate_cutoff is not None:
        candidate_source = eligible.loc[eligible["date"] < pd.to_datetime(candidate_cutoff)]
        if candidate_source.empty:
            raise ValueError("candidate_cutoff leaves no eligible rows for candidate selection")

    base_candidates = _candidate_rewards(candidate_source, top_n) if candidates is None else list(candidates)
    gated = gate_fn(
        eligible,
        base_candidates,
        as_of,
        recency_gate_days=recency_gate_days,
        domain_discontinued=DOMAIN_DISCONTINUED if domain_discontinued is None else domain_discontinued,
    )
    rows = []
    target = pd.to_datetime(target_date)

    for reward in gated:
        series = build_weekly_series(tidy, reward, as_of)
        if series.empty:
            yhat = float("nan")
        else:
            forecast = predict_func(series, [target])
            yhat = float(forecast.loc[forecast["ds"] == target, "yhat"].iloc[0])
        rows.append({"reward_norm": reward, "yhat": yhat})

    result = pd.DataFrame(rows, columns=["reward_norm", "yhat"])
    if result.empty:
        return pd.DataFrame(columns=["reward_norm", "yhat", "rank"])
    result = result.sort_values(["yhat", "reward_norm"], ascending=[False, True]).reset_index(drop=True)
    result["rank"] = range(1, len(result) + 1)
    return result[["reward_norm", "yhat", "rank"]]
