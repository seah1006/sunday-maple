from pathlib import Path

import pandas as pd

from src.normalize import categorize, extract_magnitude, normalize_reward
from src.parse import parse_by_date


KNOWN_REWARDS = {
    "[HEXA 스탯] 메인 스탯이 5레벨 이상일 때, 메인 스탯의 강화 확률 20% 증가": "HEXA스탯_강화확률",
    "10성 이하에서 스타포스 강화 성공 시 1+1 강화": "스타포스_1+1강화",
    "스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%": "스타포스_성공확률",
    "스타포스 강화 비용 30% 할인": "스타포스_비용할인",
    "21성 이하에서 스타포스 강화 시 파괴 확률 30% 감소": "스타포스_파괴방지",
    "주문의 흔적 강화 비용 50% 할인": "주문의흔적_비용할인",
    "흔적 복구 비용 20% 할인": "흔적복구_비용할인",
    "어빌리티 재설정 비용 50% 할인": "어빌리티_재설정할인",
    "잠재능력 감정 및 재설정 비용 50% 할인": "잠재능력_재설정할인",
    "강력한 환생의 불꽃 5개 사용 시마다 1개 지급(월드 당 최대 10개)": "환생의불꽃_강력한",
    "영원한 환생의 불꽃 5개 사용 시마다 1개 지급(월드 당 최대 10개)": "환생의불꽃_영원한",
    "미라클 타임": "미라클타임",
    "경험치 2배": "경험치_배수버프",
    "몬스터 사냥 시 경험치 3배 혜택": "경험치_배수버프",
    "경험치 3배 쿠폰(30분) 4장 지급": "경험치쿠폰_지급",
    "룬 경험치 버프 효과 +100%": "룬_경험치버프",
    "룬 재등장 및 재사용 대기시간 감소": "룬_재등장감소",
    "콤보킬 경험치 획득량 +300%": "콤보킬_경험치",
    "99콤보 마다 콤보킬 구슬 추가 생성": "콤보킬_경험치",
    "몬스터 파크 클리어 경험치 추가 250%": "몬스터파크_경험치",
    "몬스터파크 클리어 시 성장의 일요일 상자 지급량 2배": "몬스터파크_경험치",
    "버닝 필드 최고 15단계까지 상승": "버닝",
    "테라 버닝 부스터 지급": "버닝",
    "익스트림 성장의 비약 10개 지급": "성장의비약_지급",
    "메이플 유니온 일일퀘스트 코인 지급량 7배": "유니온_코인",
    "우르스 하루 종일 메소 보상 2배": "우르스",
    "폴로와 프리토, 에스페시아의 현상금 사냥 경험치 5배": "현상금_경험치",
    "불꽃늑대 퇴장 시 획득하는 경험치 5배": "불꽃늑대_경험치",
    "사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리)": "엘리트몬스터_증가",
    "사냥을 통해 획득할 수 있는 솔 에르다 3배로 증가": "솔에르다_사냥",
    "트레져 헌터 경험치 3배": "트레져헌터_경험치",
    "아케인리버 1~6지역 일일 컨텐츠 획득 보상 2배": "아케인리버_보상",
    "돌발미션 일일 클리어 가능 횟수 5배(3회→15회)": "돌발미션",
    "필드 몬스터를 통해 얻을 수 있는 명예의 훈장 명성치 획득량 5배": "명예의훈장",
    "보스파티 결성 버프 효과 증가(10%→30%)": "보스파티_버프",
    "월드 통합 파티퀘스트 파티 포인트 획득량 5배(10→50)": "파티퀘스트",
    "심신수련관 입장용 부적(12시간) 1장 지급": "심신수련관",
    "엘리트 몬스터 마일리지 꾸러미 일일 사용 가능 횟수 4배(5회→20회)": "엘리트마일리지",
    "몬스터 컬렉션 신규 몬스터 등록 확률 추가 100%": "몬스터컬렉션",
    "소울 조각 사용 시 위대한 소울 획득 확률 5배": "위대한소울_확률",
    "선택 아케인심볼 교환권 50개 지급": "심볼교환권_지급",
    "접속 시 '솔 에르다' 1개 지급": "솔에르다_접속지급",
    "접속 시 'VIP 부스터' 10개 지급": "VIP부스터_지급",
    "캐릭터 슬롯 증가 쿠폰 1개 지급": "캐릭터슬롯_지급",
    "데미지 스킨 선택 지급": "데미지스킨_지급",
    "메이플 유니온 프리셋 쿠폰 2개 지급": "유니온프리셋_지급",
    "프리미엄 PC방 접속 시간 2배 누적": "프리미엄PC방",
    "(리부트, 리부트2월드 : 하루 종일 드롭률 2배)": "리부트_드롭률",
    "레이디 블레어의 코디 타임": "코디타임",
    "로드 블레이의 헤어 타임": "헤어타임",
    "쁘띠 펫 타임": "펫타임",
    "썬데이메이플 선물 지급": "선물_기타지급",
}


def test_normalize_known_rewards():
    for reward_raw, expected_norm in KNOWN_REWARDS.items():
        assert normalize_reward(reward_raw) == expected_norm


def test_split_decisions():
    assert normalize_reward("강력한 환생의 불꽃 5개 사용 시마다 1개 지급") == "환생의불꽃_강력한"
    assert normalize_reward("영원한 환생의 불꽃 5개 사용 시마다 1개 지급") == "환생의불꽃_영원한"
    assert normalize_reward("사냥을 통해 획득할 수 있는 솔 에르다 2배로 증가") == "솔에르다_사냥"
    assert normalize_reward("솔 에르다 타임") == "솔에르다_사냥"
    assert normalize_reward("접속 시 '솔 에르다' 1개 지급") == "솔에르다_접속지급"
    assert normalize_reward("접속 시간 2분마다 솔 에르다 조각 교환권 1개 누적") == "솔에르다_접속지급"


def test_alias_norms():
    assert normalize_reward("샤이닝 스타포스 타임") == "스타포스_성공확률"
    assert normalize_reward("익스트림 레벨업 타임") == "경험치_배수버프"
    assert normalize_reward("솔 에르다 타임") == "솔에르다_사냥"


def test_category_no_special():
    norms = ["미라클타임", "코디타임", "헤어타임", "펫타임"]
    assert [categorize(norm) for norm in norms] == ["강화", "수집기타", "수집기타", "수집기타"]
    assert all(categorize(norm) != "스페셜" for norm in KNOWN_REWARDS.values())


def test_magnitude_examples():
    assert extract_magnitude("경험치 2배") == "2배"
    assert extract_magnitude("콤보킬 경험치 획득량 +300%") == "+300%"
    assert extract_magnitude("[HEXA 스탯] 메인 스탯이 5레벨 이상일 때, 메인 스탯의 강화 확률 20% 증가") == "20%"
    assert extract_magnitude("선택 아케인심볼 교환권 50개 지급") == "50개"
    assert extract_magnitude("쿠폰 4장 지급") == "4장"
    assert extract_magnitude("보상 15분 지급") == "15분"
    assert extract_magnitude("심신수련관 입장용 부적(12시간) 1장 지급") == "1장"
    assert extract_magnitude("경험치 2배 쿠폰(15분)") == "2배"
    assert extract_magnitude("미라클 타임") is None
    assert extract_magnitude("룬 재등장 및 재사용 대기시간 감소") is None


def test_coverage_all_rewards():
    inventory = _load_reward_inventory()
    unmapped = []
    uncategorized = []
    for reward_raw in inventory["reward_raw"].dropna().drop_duplicates().sort_values():
        reward_norm = normalize_reward(reward_raw)
        if reward_norm is None:
            unmapped.append(reward_raw)
            continue
        if categorize(reward_norm) == "미분류":
            uncategorized.append((reward_raw, reward_norm))

    assert unmapped == []
    assert uncategorized == []


def _load_reward_inventory() -> pd.DataFrame:
    inventory_path = Path("data/interim/reward_inventory.csv")
    if inventory_path.exists():
        return pd.read_csv(inventory_path, encoding="utf-8")

    by_date_path = Path("data/raw/view_by_date.txt")
    records = parse_by_date(by_date_path.read_text(encoding="utf-8"))
    return pd.DataFrame(records, columns=["reward_raw"])
