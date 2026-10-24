import pandas as pd

from src.observations import append_observations


def test_append_observations():
    tidy = pd.DataFrame({"date": pd.to_datetime(["2026-05-03"] * 3), "reward_norm": ["A"] * 3, "category": ["성장", "성장", "강화"], "is_future": [False] * 3, "no_event_week": [False] * 3})
    obs = pd.DataFrame({"date": ["2026-06-14"], "reward_norm": ["A"], "source": ["공식"]})
    result = append_observations(tidy, obs)
    assert len(result) == 4
    assert result.iloc[-1]["category"] == "성장"
    assert not result.iloc[-1]["is_future"]
    assert not result.iloc[-1]["no_event_week"]
    assert result.iloc[-1]["source"] == "공식"
    assert "category" not in obs
