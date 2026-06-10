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
