import pandas as pd

from src.features import compute_cycle_days, merge_is_discontinued


def test_cycle_days_basic():
    tidy = pd.DataFrame(
        {
            "date": ["2024-01-07", "2024-01-21", "2024-02-04"],
            "reward_norm": ["스타포스_비용할인", "스타포스_비용할인", "스타포스_비용할인"],
        }
    )

    result = compute_cycle_days(tidy)

    assert result.tolist() == [pd.NA, 14, 14]
    assert str(result.dtype) == "Int64"


def test_cycle_days_bundled_same_day():
    tidy = pd.DataFrame(
        {
            "date": ["2024-01-07", "2024-01-21", "2024-01-21", "2024-02-04"],
            "reward_norm": [
                "몬스터컬렉션",
                "몬스터컬렉션",
                "몬스터컬렉션",
                "몬스터컬렉션",
            ],
            "reward_raw": ["a", "b", "c", "d"],
        }
    )

    result = compute_cycle_days(tidy)

    assert result.tolist() == [pd.NA, 14, 14, 14]


def test_cycle_days_null_norm():
    tidy = pd.DataFrame(
        {
            "date": ["2024-01-07", "2024-01-14", "2024-01-21"],
            "reward_norm": ["경험치_배수버프", None, "경험치_배수버프"],
        }
    )

    result = compute_cycle_days(tidy)

    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == 14


def test_cycle_days_first_occurrence_nan():
    tidy = pd.DataFrame(
        {
            "date": ["2024-01-07", "2024-01-07", "2024-01-14", "2024-01-21"],
            "reward_norm": ["A", "B", "B", "A"],
        }
    )

    result = compute_cycle_days(tidy)

    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == 7
    assert result.iloc[3] == 14


def test_merge_is_discontinued_basic_flags_and_missing_policy():
    tidy = pd.DataFrame(
        {
            "reward_raw": [
                "단종 보상",
                "현행 보상",
                None,
                "by_type에 없는 보상",
            ]
        }
    )
    parsed_by_type = pd.DataFrame(
        {
            "reward_raw": ["단종 보상", "현행 보상"],
            "is_discontinued": [True, False],
        }
    )

    result = merge_is_discontinued(tidy, parsed_by_type)

    assert result.tolist() == [True, False, pd.NA, False]
    assert str(result.dtype) == "boolean"


def test_merge_is_discontinued_rejects_conflicting_raw_flags():
    tidy = pd.DataFrame({"reward_raw": ["혼재 보상"]})
    parsed_by_type = pd.DataFrame(
        {
            "reward_raw": ["혼재 보상", "혼재 보상"],
            "is_discontinued": [True, False],
        }
    )

    try:
        merge_is_discontinued(tidy, parsed_by_type)
    except ValueError as exc:
        assert "conflicting is_discontinued flags" in str(exc)
    else:
        raise AssertionError("expected ValueError for conflicting raw flags")
