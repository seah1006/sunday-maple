import numpy as np
import pandas as pd
import pytest

from src.predict_dataset import DOMAIN_DISCONTINUED, FEATURE_COLUMNS, build_inference_frame, build_prediction_frame


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


def test_prediction_features_do_not_change_when_future_rows_are_removed():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "B", "cat2"),
            ("2024-01-21", "A", "cat1"),
            ("2024-01-28", "B", "cat2"),
            ("2024-02-04", "A", "cat1"),
            ("2024-02-11", "B", "cat2"),
            ("2024-02-18", "A", "cat1"),
            ("2024-02-25", "B", "cat2"),
        ]
    )
    full = build_prediction_frame(tidy, top_n=2, roll_k=2)
    truncated = build_prediction_frame(tidy[tidy["date"] <= "2024-02-04"], top_n=2, roll_k=2)

    columns = [
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
    full_row = full.loc[
        (full["date"] == pd.Timestamp("2024-02-04")) & (full["reward_norm"] == "B"),
        columns,
    ].reset_index(drop=True)
    truncated_row = truncated.loc[
        (truncated["date"] == pd.Timestamp("2024-02-04")) & (truncated["reward_norm"] == "B"),
        columns,
    ].reset_index(drop=True)

    pd.testing.assert_frame_equal(full_row, truncated_row)


def test_prediction_target_matches_same_date_reward_membership():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-07", "B", "cat2"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-21", "B", "cat2"),
        ]
    )

    result = build_prediction_frame(tidy, top_n=2)

    target = result.loc[result["date"] == pd.Timestamp("2024-01-14"), ["reward_norm", "y"]]
    assert target.set_index("reward_norm")["y"].to_dict() == {"A": 1, "B": 0}


def test_prediction_first_occurrence_rules_are_numeric():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-21", "B", "cat2"),
        ]
    )

    result = build_prediction_frame(tidy, top_n=2)
    first_b = result.loc[
        (result["date"] == pd.Timestamp("2024-01-07")) & (result["reward_norm"] == "B")
    ].iloc[0]
    later_b = result.loc[
        (result["date"] == pd.Timestamp("2024-01-14")) & (result["reward_norm"] == "B")
    ].iloc[0]

    assert first_b["days_since_last"] == 0
    assert first_b["past_count"] == 0
    assert later_b["days_since_last"] == 7
    assert later_b["past_count"] == 0
    assert pd.isna(first_b["roll_gap_mean"])


def test_candidate_set_is_stable_under_future_rows():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-07", "B", "cat2"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-14", "B", "cat2"),
            ("2024-01-21", "A", "cat1"),
            ("2024-01-28", "C", "cat3"),
            ("2024-02-04", "C", "cat3"),
            ("2024-02-11", "C", "cat3"),
            ("2024-02-18", "C", "cat3"),
        ]
    )

    full = build_prediction_frame(tidy, top_n=2, candidate_cutoff="2024-01-22")
    changed_future = tidy.loc[tidy["date"] <= "2024-02-04"].copy()
    truncated = build_prediction_frame(changed_future, top_n=2, candidate_cutoff="2024-01-22")

    assert set(full["reward_norm"].unique()) == {"A", "B"}
    assert set(truncated["reward_norm"].unique()) == {"A", "B"}


def test_candidate_cutoff_changes_selection_vs_full():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-07", "B", "cat2"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-14", "B", "cat2"),
            ("2024-01-21", "A", "cat1"),
            ("2024-01-28", "C", "cat3"),
            ("2024-02-04", "C", "cat3"),
            ("2024-02-11", "C", "cat3"),
            ("2024-02-18", "C", "cat3"),
        ]
    )

    full = build_prediction_frame(tidy, top_n=2)
    cutoff = build_prediction_frame(tidy, top_n=2, candidate_cutoff="2024-01-22")

    assert set(full["reward_norm"].unique()) == {"A", "C"}
    assert set(cutoff["reward_norm"].unique()) == {"A", "B"}


def test_candidate_cutoff_before_data_raises():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "B", "cat2"),
        ]
    )

    with pytest.raises(ValueError):
        build_prediction_frame(tidy, top_n=1, candidate_cutoff="2024-01-01")


def test_inference_frame_shape_and_no_target():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "B", "cat2"),
            ("2024-01-21", "A", "cat1"),
            ("2024-01-28", "C", "cat3"),
        ]
    )

    result = build_inference_frame(tidy, target_date="2024-02-04", top_n=3, recency_gate_days=None)

    assert len(result) == 3
    assert list(result.columns) == ["date", "reward_norm", *FEATURE_COLUMNS]
    assert "y" not in result.columns
    assert result["date"].eq(pd.Timestamp("2024-02-04")).all()


def test_inference_matches_training_features_at_same_asof():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-07", "B", "cat2"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-21", "B", "cat2"),
            ("2024-01-28", "A", "cat1"),
            ("2024-01-28", "C", "cat3"),
        ]
    )
    d_last = pd.Timestamp("2024-01-28")

    training = build_prediction_frame(tidy, top_n=3, roll_k=2, candidate_cutoff="2024-01-22")
    inference = build_inference_frame(
        tidy,
        target_date=d_last,
        top_n=3,
        roll_k=2,
        candidate_cutoff="2024-01-22",
        recency_gate_days=None,
    )
    training_last = (
        training.loc[training["date"] == d_last, ["reward_norm", *FEATURE_COLUMNS]]
        .sort_values("reward_norm")
        .reset_index(drop=True)
    )
    inference_last = (
        inference[["reward_norm", *FEATURE_COLUMNS]]
        .sort_values("reward_norm")
        .reset_index(drop=True)
    )

    pd.testing.assert_frame_equal(training_last, inference_last)


def test_inference_uses_only_past_of_target():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-21", "B", "cat2"),
            ("2024-01-28", "A", "cat1"),
            ("2024-02-04", "B", "cat2"),
        ]
    )

    result = build_inference_frame(tidy, target_date="2024-01-21", top_n=2, recency_gate_days=None)
    a_row = result.loc[result["reward_norm"] == "A"].iloc[0]
    b_row = result.loc[result["reward_norm"] == "B"].iloc[0]

    assert a_row["days_since_last"] == 7
    assert a_row["past_count"] == 2
    assert b_row["days_since_last"] == 14
    assert b_row["past_count"] == 0
    assert result["past_rate"].between(0, 1).all()
    assert np.isfinite(result["days_since_last"]).all()


def test_inference_candidate_cutoff_consistency():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-07", "B", "cat2"),
            ("2024-01-14", "A", "cat1"),
            ("2024-01-14", "B", "cat2"),
            ("2024-01-21", "A", "cat1"),
            ("2024-01-28", "C", "cat3"),
            ("2024-02-04", "C", "cat3"),
            ("2024-02-11", "C", "cat3"),
            ("2024-02-18", "C", "cat3"),
        ]
    )

    training = build_prediction_frame(tidy, top_n=2, candidate_cutoff="2024-01-22")
    inference = build_inference_frame(
        tidy,
        target_date="2024-02-25",
        top_n=2,
        candidate_cutoff="2024-01-22",
        recency_gate_days=None,
    )

    assert set(inference["reward_norm"].unique()) == set(training["reward_norm"].unique())


def test_inference_recency_gate_excludes_stale_candidate():
    tidy = _tidy(
        [
            ("2023-01-01", "A", "cat1"),
            ("2023-01-08", "A", "cat1"),
            ("2024-12-01", "B", "cat2"),
            ("2024-12-08", "B", "cat2"),
        ]
    )

    result = build_inference_frame(tidy, target_date="2025-05-18", top_n=2, recency_gate_days=180)

    assert "A" not in set(result["reward_norm"])
    assert "B" in set(result["reward_norm"])


def test_inference_recency_gate_keeps_recent_candidate():
    tidy = _tidy(
        [
            ("2025-01-05", "A", "cat1"),
            ("2025-01-12", "A", "cat1"),
            ("2025-05-04", "B", "cat2"),
        ]
    )

    result = build_inference_frame(tidy, target_date="2025-06-29", top_n=2, recency_gate_days=180)

    assert "B" in set(result["reward_norm"])


def test_inference_domain_discontinued_excludes_candidate():
    reward = next(iter(DOMAIN_DISCONTINUED))
    tidy = _tidy(
        [
            ("2025-05-04", reward, "cat1"),
            ("2025-05-11", reward, "cat1"),
            ("2025-05-18", "A", "cat2"),
        ]
    )

    result = build_inference_frame(tidy, target_date="2025-06-29", top_n=2, recency_gate_days=180)

    assert reward not in set(result["reward_norm"])


def test_inference_recency_gate_uses_only_before_target():
    tidy = _tidy(
        [
            ("2024-01-07", "A", "cat1"),
            ("2024-01-14", "A", "cat1"),
            ("2025-06-29", "A", "cat1"),
            ("2025-07-06", "A", "cat1"),
            ("2025-05-04", "B", "cat2"),
        ]
    )

    result = build_inference_frame(tidy, target_date="2025-06-29", top_n=2, recency_gate_days=180)

    assert "A" not in set(result["reward_norm"])
    assert "B" in set(result["reward_norm"])
