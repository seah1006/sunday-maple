from __future__ import annotations

import re


CATEGORY_BY_NORM = {
    "HEXA스탯_강화확률": "강화",
    "스타포스_성공확률": "강화",
    "스타포스_비용할인": "강화",
    "스타포스_1+1강화": "강화",
    "스타포스_파괴방지": "강화",
    "주문의흔적_비용할인": "강화",
    "흔적복구_비용할인": "강화",
    "어빌리티_재설정할인": "강화",
    "잠재능력_재설정할인": "강화",
    "환생의불꽃_강력한": "강화",
    "환생의불꽃_영원한": "강화",
    "미라클타임": "강화",
    "경험치_배수버프": "성장",
    "경험치쿠폰_지급": "성장",
    "룬_경험치버프": "성장",
    "룬_재등장감소": "성장",
    "콤보킬_경험치": "성장",
    "몬스터파크_경험치": "성장",
    "버닝": "성장",
    "성장의비약_지급": "성장",
    "유니온_코인": "성장",
    "우르스": "성장",
    "현상금_경험치": "사냥효율",
    "불꽃늑대_경험치": "사냥효율",
    "엘리트몬스터_증가": "사냥효율",
    "솔에르다_사냥": "사냥효율",
    "트레져헌터_경험치": "사냥효율",
    "아케인리버_보상": "사냥효율",
    "돌발미션": "사냥효율",
    "명예의훈장": "사냥효율",
    "보스파티_버프": "사냥효율",
    "파티퀘스트": "사냥효율",
    "심신수련관": "사냥효율",
    "엘리트마일리지": "사냥효율",
    "몬스터컬렉션": "수집기타",
    "위대한소울_확률": "수집기타",
    "심볼교환권_지급": "수집기타",
    "솔에르다_접속지급": "수집기타",
    "VIP부스터_지급": "수집기타",
    "캐릭터슬롯_지급": "수집기타",
    "데미지스킨_지급": "수집기타",
    "유니온프리셋_지급": "수집기타",
    "프리미엄PC방": "수집기타",
    "리부트_드롭률": "수집기타",
    "코디타임": "수집기타",
    "헤어타임": "수집기타",
    "펫타임": "수집기타",
    "선물_기타지급": "수집기타",
}


MARKER_RE = re.compile(r"\[\[/?[BS]\]\]")
DISCONTINUED_RE = re.compile(r"^\(?단종\)?")
MAGNITUDE_PATTERNS = [
    re.compile(r"\d+(?:\.\d+)?배"),
    re.compile(r"\+?\d+%"),
    re.compile(r"\d+(?:개|장)"),
    re.compile(r"\d+분"),
    re.compile(r"\d+(?:회|성|단계)"),
]


def normalize_reward(reward_raw: str) -> str | None:
    text = _clean_reward(reward_raw)
    if not text:
        return None

    if "[HEXA 스탯]" in text and "강화 확률" in text:
        return "HEXA스탯_강화확률"
    if "강력한 환생의 불꽃" in text:
        return "환생의불꽃_강력한"
    if "영원한 환생의 불꽃" in text:
        return "환생의불꽃_영원한"
    if "샤이닝 스타포스 타임" in text:
        return "스타포스_성공확률"
    if "스타포스" in text and "성공확률 100%" in text:
        return "스타포스_성공확률"
    if "스타포스 강화 비용" in text and "할인" in text:
        return "스타포스_비용할인"
    if "1+1 강화" in text:
        return "스타포스_1+1강화"
    if "파괴 확률" in text and "감소" in text:
        return "스타포스_파괴방지"
    if "주문의 흔적 강화 비용" in text and "할인" in text:
        return "주문의흔적_비용할인"
    if "흔적 복구 비용" in text and "할인" in text:
        return "흔적복구_비용할인"
    if "어빌리티 재설정 비용" in text and "할인" in text:
        return "어빌리티_재설정할인"
    if "잠재능력" in text and "재설정 비용" in text and "할인" in text:
        return "잠재능력_재설정할인"
    if "미라클 타임" in text:
        return "미라클타임"

    if "익스트림 레벨업 타임" in text:
        return "경험치_배수버프"
    if text == "경험치 2배" or ("몬스터 사냥 시 경험치" in text and "혜택" in text):
        return "경험치_배수버프"
    if "경험치" in text and "쿠폰" in text and "지급" in text:
        return "경험치쿠폰_지급"
    if "룬 경험치 버프" in text:
        return "룬_경험치버프"
    if "룬 재등장" in text:
        return "룬_재등장감소"
    if "콤보킬 경험치" in text or ("99콤보" in text and "콤보킬 구슬" in text):
        return "콤보킬_경험치"
    if "몬스터 파크 클리어 경험치" in text or (
        "몬스터파크" in text and "성장의 일요일 상자" in text
    ):
        return "몬스터파크_경험치"
    if "버닝 필드" in text or "버닝 부스터" in text:
        return "버닝"
    if "성장의 비약" in text:
        return "성장의비약_지급"
    if "유니온 일일퀘스트 코인" in text:
        return "유니온_코인"
    if "우르스" in text:
        return "우르스"

    if "현상금 사냥 경험치" in text:
        return "현상금_경험치"
    if "불꽃늑대 퇴장" in text:
        return "불꽃늑대_경험치"
    if "엘리트 몬스터 수 증가" in text:
        return "엘리트몬스터_증가"
    if "솔 에르다 타임" in text:
        return "솔에르다_사냥"
    if "사냥을 통해" in text and "솔 에르다" in text:
        return "솔에르다_사냥"
    if "트레져 헌터 경험치" in text:
        return "트레져헌터_경험치"
    if "아케인리버" in text and "보상 2배" in text:
        return "아케인리버_보상"
    if "돌발미션" in text:
        return "돌발미션"
    if "명예의 훈장" in text:
        return "명예의훈장"
    if "보스파티 결성 버프" in text:
        return "보스파티_버프"
    if "파티퀘스트" in text:
        return "파티퀘스트"
    if "심신수련관" in text:
        return "심신수련관"
    if "엘리트 몬스터 마일리지" in text:
        return "엘리트마일리지"

    if "몬스터 컬렉션" in text:
        return "몬스터컬렉션"
    if "위대한 소울" in text:
        return "위대한소울_확률"
    if "심볼 교환권" in text:
        return "심볼교환권_지급"
    if "솔 에르다" in text and ("접속" in text or "누적" in text):
        return "솔에르다_접속지급"
    if "VIP 부스터" in text:
        return "VIP부스터_지급"
    if "캐릭터 슬롯" in text:
        return "캐릭터슬롯_지급"
    if "데미지 스킨" in text:
        return "데미지스킨_지급"
    if "유니온 프리셋 쿠폰" in text:
        return "유니온프리셋_지급"
    if "프리미엄 PC방" in text:
        return "프리미엄PC방"
    if "리부트" in text and "드롭률" in text:
        return "리부트_드롭률"
    if "코디 타임" in text:
        return "코디타임"
    if "헤어 타임" in text:
        return "헤어타임"
    if "펫 타임" in text:
        return "펫타임"
    if any(
        token in text
        for token in [
            "썬데이메이플 선물",
            "운영자의 특별한 선물",
            "운영자 특별 선물",
            "메생역전 머니 상자",
            "메생역전 머니상자",
            "솜사탕 핑크빈 교환권",
            "마스터 라벨",
        ]
    ):
        return "선물_기타지급"

    return None


def categorize(reward_norm: str) -> str:
    return CATEGORY_BY_NORM.get(reward_norm, "미분류")


def extract_magnitude(reward_raw: str) -> str | None:
    text = _clean_reward(reward_raw)
    if not text:
        return None

    for pattern in MAGNITUDE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def _clean_reward(reward_raw: str | None) -> str:
    if reward_raw is None:
        return ""
    text = MARKER_RE.sub("", str(reward_raw)).strip()
    text = DISCONTINUED_RE.sub("", text).strip()
    return re.sub(r"\s+", " ", text)
