import pandas as pd
import pytest

from src.build_tidy import build_tidy, load_raw_views


@pytest.fixture(scope="module")
def tidy():
    return build_tidy(*load_raw_views(), as_of="2026-06-10")[0]


def test_build_tidy_matches_processed_counts(tidy):
    assert tidy.shape == (1160, 14)
    assert len(tidy.loc[tidy.reward_norm.notna() & ~tidy.is_future]) == 1118
    assert tidy.duplicated(["date", "reward_raw"]).sum() == 0
    assert (tidy.date.dt.dayofweek != 6).sum() == 11


def test_build_tidy_matches_processed_csv(tidy):
    expected = pd.read_csv("data/processed/tidy_rewards.csv", parse_dates=["date"], dtype={"is_discontinued": "boolean", "cycle_days": "Int64"})
    columns = ["date", "reward_raw", "reward_norm", "category", "cycle_days", "is_discontinued"]
    pd.testing.assert_frame_equal(tidy[columns], expected[columns], check_dtype=False)


def test_is_future_follows_as_of():
    tidy, _ = build_tidy(*load_raw_views(), as_of="2026-06-01")
    assert tidy.loc[tidy.date == "2026-06-07", "is_future"].all()
