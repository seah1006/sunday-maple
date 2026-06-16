import pandas as pd

from src.prophet_cycle import build_weekly_series, rank_candidates


def _tidy(rows):
    return pd.DataFrame(
        [
            {
                "date": date,
                "reward_norm": reward,
                "category": category,
                "is_future": False,
                "no_event_week": False,
            }
            for date, reward, category in rows
        ]
    )


def test_build_weekly_series_uses_only_before_as_of():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-21", "A", "cat1"),
            ("2024-01-28", "B", "cat2"),
            ("2024-02-04", "A", "cat1"),
        ]
    )

    result = build_weekly_series(tidy, "A", "2024-02-04")

    assert result["ds"].max() == pd.Timestamp("2024-01-28")
    assert result.set_index("ds")["y"].to_dict() == {
        pd.Timestamp("2024-01-07"): 1,
        pd.Timestamp("2024-01-14"): 0,
        pd.Timestamp("2024-01-21"): 1,
        pd.Timestamp("2024-01-28"): 0,
    }


def test_rank_candidates_applies_recency_gate_without_prophet_fit():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "A", "cat1"),
            ("2025-05-04", "B", "cat2"),
            ("2025-05-11", "B", "cat2"),
        ]
    )

    def fake_predict(series_df, target_dates):
        return pd.DataFrame({"ds": pd.to_datetime(target_dates), "yhat": [series_df["y"].sum()]})

    result = rank_candidates(
        tidy,
        ["A", "B"],
        as_of="2025-06-29",
        target_date="2025-06-29",
        recency_gate_days=180,
        predict_func=fake_predict,
    )

    assert set(result["reward_norm"]) == {"B"}


def test_rank_candidates_applies_domain_discontinued_without_prophet_fit():
    tidy = _tidy(
        [
            ("2025-05-04", "스타포스_1+1강화", "cat1"),
            ("2025-05-11", "스타포스_1+1강화", "cat1"),
            ("2025-05-18", "A", "cat2"),
        ]
    )

    def fake_predict(series_df, target_dates):
        return pd.DataFrame({"ds": pd.to_datetime(target_dates), "yhat": [1.0]})

    result = rank_candidates(
        tidy,
        ["스타포스_1+1강화", "A"],
        as_of="2025-06-29",
        target_date="2025-06-29",
        recency_gate_days=180,
        predict_func=fake_predict,
    )

    assert set(result["reward_norm"]) == {"A"}
