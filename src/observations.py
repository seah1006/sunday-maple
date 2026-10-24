from pathlib import Path

import pandas as pd


def load_manual_observations(path: str | Path = "data/interim/manual_obs_20260614.csv") -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])


def append_observations(tidy: pd.DataFrame, observations: pd.DataFrame) -> pd.DataFrame:
    category_lookup = tidy.dropna(subset=["reward_norm", "category"]).groupby("reward_norm")["category"].agg(lambda s: s.mode().iloc[0])
    added = observations.copy()
    added["date"] = pd.to_datetime(added["date"])
    added["category"] = added["reward_norm"].map(category_lookup)
    added["is_future"] = False
    added["no_event_week"] = False
    return pd.concat([tidy, added], ignore_index=True, sort=False)
