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


def test_disc_body_form_match():
    tidy = pd.DataFrame(
        {
            "reward_raw": ["데미지 스킨 선택 지급"],
            "reward_trailing": ["(샤방샤방/샤방샤방(Ver.2)/샤방샤방(Ver.3))"],
        }
    )
    parsed_by_type = pd.DataFrame(
        {
            "reward_raw": ["데미지 스킨 선택 지급"],
            "is_discontinued": [True],
        }
    )

    result = merge_is_discontinued(tidy, parsed_by_type)

    assert result.tolist() == [True]


def test_disc_fullstring_match():
    tidy = pd.DataFrame(
        {
            "reward_raw": ["돌발미션 일일 클리어 가능 횟수 2배"],
            "reward_trailing": ["(3회→6회)"],
        }
    )
    parsed_by_type = pd.DataFrame(
        {
            "reward_raw": ["돌발미션 일일 클리어 가능 횟수 2배(3회→6회)"],
            "is_discontinued": [True],
        }
    )

    result = merge_is_discontinued(tidy, parsed_by_type)

    assert result.tolist() == [True]


def test_disc_same_raw_split_by_trailing():
    tidy = pd.DataFrame(
        {
            "reward_raw": [
                "사냥 시 소환되는 엘리트 몬스터 수 증가",
                "사냥 시 소환되는 엘리트 몬스터 수 증가",
            ],
            "reward_trailing": ["(1마리→2마리)", "(1마리→3마리)"],
        }
    )
    parsed_by_type = pd.DataFrame(
        {
            "reward_raw": [
                "사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리)",
                "사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리)",
            ],
            "is_discontinued": [True, False],
        }
    )

    result = merge_is_discontinued(tidy, parsed_by_type)

    assert result.tolist() == [True, False]


def test_disc_null_and_active():
    tidy = pd.DataFrame(
        {
            "reward_raw": [None, "현행 보상"],
            "reward_trailing": [None, None],
        }
    )
    parsed_by_type = pd.DataFrame(
        {
            "reward_raw": ["단종 보상"],
            "is_discontinued": [True],
        }
    )

    result = merge_is_discontinued(tidy, parsed_by_type)

    assert result.tolist() == [pd.NA, False]
