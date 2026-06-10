from src.parse import (
    parse_by_date,
    parse_by_type,
    parse_date_header,
    parse_type_date_line,
    split_reward_trailing,
    to_date,
)


def test_to_date_converts_dot_date():
    assert to_date("2017.03.12") == "2017-03-12"


def test_by_type_cycle_line():
    parsed = parse_type_date_line("(+84일)2024.10.13")
    assert parsed == {
        "date": "2024-10-13",
        "stated_cycle_days": 84,
        "trailing": None,
    }


def test_by_type_first_seen_line():
    parsed = parse_type_date_line("2024.07.21")
    assert parsed == {
        "date": "2024-07-21",
        "stated_cycle_days": None,
        "trailing": None,
    }


def test_by_type_discontinued_header():
    text = "- [[B]](단종)[[/B]]경험치 2배\n2018.12.16"
    records = parse_by_type(text)
    assert records[0]["reward_raw"] == "경험치 2배"
    assert records[0]["is_discontinued"] is True


def test_by_type_discontinued_header_with_bold_inside_parentheses():
    text = "- ([[B]]단종)[[/B]]경험치 3배 쿠폰(30분) 4장 지급\n2017.04.16"
    records = parse_by_type(text)
    assert records[0]["reward_raw"] == "경험치 3배 쿠폰(30분) 4장 지급"
    assert records[0]["is_discontinued"] is True


def test_by_type_trailing_line():
    parsed = parse_type_date_line("(+35일)2026.05.31(샤이닝 스타포스 타임)")
    assert parsed == {
        "date": "2026-05-31",
        "stated_cycle_days": 35,
        "trailing": "(샤이닝 스타포스 타임)",
    }


def test_by_date_major_event_header():
    parsed = parse_date_header("2017.04.30[[B]] <우주 Like 메이플?>[[/B]]")
    assert parsed == {
        "date": "2017-04-30",
        "event_context": "우주 Like 메이플?",
        "is_major_event": True,
    }


def test_by_date_small_event_header():
    parsed = parse_date_header("2017.03.26 (도전! 메이플 레인보우!)")
    assert parsed == {
        "date": "2017-03-26",
        "event_context": "도전! 메이플 레인보우!",
        "is_major_event": False,
    }


def test_by_date_no_context_header():
    parsed = parse_date_header("2017.03.12 (-)")
    assert parsed == {
        "date": "2017-03-12",
        "event_context": None,
        "is_major_event": False,
    }


def test_by_date_no_event_week_sentinel():
    records = parse_by_date("[[S]]2017.03.19[[/S]]\n[[S]]아예 없음[[/S]]")
    assert records == [
        {
            "date": "2017-03-19",
            "event_context": None,
            "is_major_event": False,
            "no_event_week": True,
            "reward_raw": None,
            "reward_trailing": None,
        }
    ]


def test_by_date_empty_block_is_not_no_event_without_sentinel():
    records = parse_by_date("2026.06.21\n2026.06.28")
    assert records[0] == {
        "date": "2026-06-21",
        "event_context": None,
        "is_major_event": False,
        "no_event_week": False,
        "reward_raw": None,
        "reward_trailing": None,
    }


def test_reward_special_trailing_split():
    reward, trailing = split_reward_trailing("스타포스 강화 비용 30% 할인(샤이닝 스타포스 타임)")
    assert reward == "스타포스 강화 비용 30% 할인"
    assert trailing == "(샤이닝 스타포스 타임)"


def test_multiple_reward_trailing_split():
    reward, trailing = split_reward_trailing(
        "몬스터 사냥 시 경험치 3배 혜택(오전 10시~오후 10시)(=익스트림 레벨업 타임)"
    )
    assert reward == "몬스터 사냥 시 경험치 3배 혜택"
    assert trailing == "(오전 10시~오후 10시)(=익스트림 레벨업 타임)"


def test_weekday_exception_does_not_break_date_parse():
    parsed = parse_type_date_line("(+60일)2023.01.12(목)")
    assert parsed == {
        "date": "2023-01-12",
        "stated_cycle_days": 60,
        "trailing": "(목)",
    }


POWER_UP_WEEK_TEXT = """\
2023.01.12~2023.01.18[[B]] [[/B]][[B]]<요정 웡키의 웡스토랑 - 마이크의 파워업 위크>[[/B]]
2023.01.12(목) - 10성 이하에서 스타포스 강화 성공 시 1+1 강화
2023.01.13(금) - 소울 조각 사용 시 위대한 소울 획득 확률 5배
2023.01.14(토) - 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%(샤이닝 스타포스 타임), 스타포스 강화 비용 30% 할인(샤이닝 스타포스 타임)
2023.01.15(일) - 미라클 타임(오전 8시~오후 11시 30분)
2023.01.16(월) - 주문의 흔적 강화 비용 50% 할인
2023.01.17(화) - 어빌리티 재설정 비용 50% 할인
2023.01.18(수) - 스타포스 강화 비용 30% 할인
"""


def test_week_banner_sets_context():
    records = parse_by_date(
        "2023.01.12~2023.01.18[[B]] [[/B]][[B]]<요정 웡키의 웡스토랑 - 마이크의 파워업 위크>[[/B]]"
    )
    assert records == []


def test_inline_daily_rewards():
    records = parse_by_date(POWER_UP_WEEK_TEXT)
    assert records == [
        {
            "date": "2023-01-12",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "10성 이하에서 스타포스 강화 성공 시 1+1 강화",
            "reward_trailing": None,
        },
        {
            "date": "2023-01-13",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "소울 조각 사용 시 위대한 소울 획득 확률 5배",
            "reward_trailing": None,
        },
        {
            "date": "2023-01-14",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%",
            "reward_trailing": "(샤이닝 스타포스 타임)",
        },
        {
            "date": "2023-01-14",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "스타포스 강화 비용 30% 할인",
            "reward_trailing": "(샤이닝 스타포스 타임)",
        },
        {
            "date": "2023-01-15",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "미라클 타임",
            "reward_trailing": "(오전 8시~오후 11시 30분)",
        },
        {
            "date": "2023-01-16",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "주문의 흔적 강화 비용 50% 할인",
            "reward_trailing": None,
        },
        {
            "date": "2023-01-17",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "어빌리티 재설정 비용 50% 할인",
            "reward_trailing": None,
        },
        {
            "date": "2023-01-18",
            "event_context": "요정 웡키의 웡스토랑 - 마이크의 파워업 위크",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "스타포스 강화 비용 30% 할인",
            "reward_trailing": None,
        },
    ]


def test_inline_multi_reward_comma_split():
    records = parse_by_date(
        "2023.01.14(토) - 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%(샤이닝 스타포스 타임), 스타포스 강화 비용 30% 할인(샤이닝 스타포스 타임)"
    )
    assert [record["reward_raw"] for record in records] == [
        "스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%",
        "스타포스 강화 비용 30% 할인",
    ]


def test_existing_by_date_unchanged():
    text = """\
2017.04.30[[B]] <우주 Like 메이플?>[[/B]]
스타포스 강화 비용 30% 할인(샤이닝 스타포스 타임)
2017.05.07 (도전! 메이플 레인보우!)
경험치 2배
"""
    assert parse_by_date(text) == [
        {
            "date": "2017-04-30",
            "event_context": "우주 Like 메이플?",
            "is_major_event": True,
            "no_event_week": False,
            "reward_raw": "스타포스 강화 비용 30% 할인",
            "reward_trailing": "(샤이닝 스타포스 타임)",
        },
        {
            "date": "2017-05-07",
            "event_context": "도전! 메이플 레인보우!",
            "is_major_event": False,
            "no_event_week": False,
            "reward_raw": "경험치 2배",
            "reward_trailing": None,
        },
    ]
