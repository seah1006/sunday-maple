# Phase 5 설계 초안 (Phase 4 리뷰 후속 — 사용자 결정 대기)

> Phase 4 handoff(`docs/claude_handoff_phase4.md`) 리뷰 결과 도출된 후속 작업. **열린 결정(§1)**을 확정하면 `docs/codex_work_packet_phase5.md`로 확정한다. (Phase 3→4와 동일 절차: 설계 초안 → 사용자 결정 → Work Packet.)

## Phase 4 판정: 통과(PASS)

- `python -m pytest -q` → 24 passed (Claude 직접 재실행 확인).
- 미매핑 0, `스페셜`/`미분류` 카테고리 0, 파워업 위크 8행 정확, 고유 norm 48개.
- `(date, reward_raw)` 전역 유일(중복 0) — 데이터 무결성 양호.
- handoff가 보고한 Critical/Major 항목은 **Phase 4 결함이 아니라** 사양 모호점 또는 Phase 5 결정 사항으로 이관(아래).

## 리뷰에서 확정한 사실

1. **(date, reward_norm) 중복 56쌍 = 100% norm-묶음.** 진짜 (date,raw) 중복은 0. 원인은 §2 "수치 통합" norm이 같은 날 공존하는 *서로 다른 보상*까지 한 norm으로 묶기 때문. 기여도:
   | norm | 묶인 날짜 수 | 묶인 원본 보상 |
   |---|---|---|
   | 몬스터컬렉션 | 38 | 신규 등록 확률 100% + 의문의 모몽 N개 (+탐험 시간 단축) |
   | 돌발미션 | 7 | 일일 횟수 N배 + 클리어 경험치 N배 (+더 자주 발생) |
   | 룬_경험치버프 | 2 | 효과 +100% + 지속시간 2배 |
   | 버닝 | 2 | 필드 단계상승 + 최고 15단계 |
   | 우르스 | 2 | 입장 2배 + 메소 2배 |
   | 솔에르다_접속지급 | 2 | 누적 2시간 + 누적 3시간 + 2분마다 조각 |
   | 몬스터파크_경험치·파티퀘스트·선물_기타지급 | 각 1 | (경험치+상자 / 입장+포인트 / 솜사탕+마스터라벨) |
2. **01_collect.ipynb는 raw를 무조건 재수집·덮어쓴다**(`collect_main(str(raw_dir))`). "원본 불변" + "노트북 순차 재실행 재현성"과 충돌. Codex가 raw 보호 위해 01 실행 생략한 것은 올바른 판단. → 가드 필요.
3. **reward_norm 결측 42 = no_event_week 30 + 미래 빈 블록 12.** 내 Phase 4 packet의 "결측=30 일치" 기대가 미래 블록 12행을 누락한 사양 오류였음. 42는 정상 분해됨.
4. 03_crossval는 inventory 재생성 위해 재실행되어 output diff 발생(코드 변경 의도 없음). 파워업 8행이 by_date에 편입되어 by_type-only 불일치가 줄었을 것으로 예상 → Phase 5에서 재집계·재확인 필요.

## §1. 열린 결정 (사용자 확정 필요)

### 결정 1 (핵심) — 관측 단위 / norm 입도

`(date, reward_norm)` 중복 56쌍을 어떻게 다룰지. 분석 목표("보상 등장 패턴")와 cycle_days(향후) 계산에 직접 영향.

- **(A) reward_raw = 관측 단위, norm = 집계 라벨 (권장)**
  - 무결성 기준을 `(date, reward_raw)` 유일로 채택(현재 통과). norm 중복은 "같은 슬롯에 동반 지급된 별개 보상"으로 정당하게 허용·문서화.
  - 장점: 데이터 무손실, 단순, §2 입도 유지, 오버엔지니어링 회피. EDA는 norm으로 group.
  - 단점: norm 단위 cycle_days는 같은 날 2건 → 0일 간격 발생 → cycle 계산 시 norm·date 중복 제거 후 산출(문서화).
  - 작업: CLAUDE.md/data_dictionary의 무결성 기준 `(date,reward_norm)`→`(date,reward_raw)`로 갱신.
- **(B) 과묶음 norm 세분화**
  - 몬스터컬렉션→{등록/모몽/탐험}, 돌발미션→{횟수/경험치/빈도}, 룬→{효과/지속시간}, 버닝→{필드/부스터}, 우르스→{입장/메소}, 파티퀘스트→{입장/포인트}, 몬파→{경험치/상자}, 솔에르다_접속→{누적시간/조각}, 선물→{종류별} 등 분리 → `(date,norm)` 유일 달성.
  - 장점: norm별 보상이 1:1, 동반/단독 패턴·cycle 명확.
  - 단점: norm ~12–15개 증가, §2 "수치 통합" 단순성과 상충, 거의 항상 동반 지급되는 쌍을 굳이 분리.
- **(C) (date,norm) dedup** — 관측 손실. 비권장.

> Claude 권장: **(A)**. 데이터를 잃지 않고, 무결성 기준만 raw 단위로 정정하면 됨. norm은 분석 라벨로 충분. 단, cycle_days 계산 시점에 norm 중복 처리 규칙을 명시.

### 결정 2 (경량) — 미래 빈 블록 12행

2026-06-14~08-30 미래 일요일(announced, 보상 미정, `is_future=True`, reward_raw null).

- **(A) 유지 + 플래그 (권장)**: 이미 `is_future`로 구분 가능. processed에 두되 EDA/모델은 `is_future==False`로 필터. 발표 일정 정보 보존.
- **(B) processed에서 제외**: 분석 입력을 과거 확정분으로 한정. 미래 행은 interim에만.

> Claude 권장: **(A)** (구분 컬럼 이미 존재, 무손실).

## §2. 결정 무관 확정 작업 (Work Packet에 포함 예정)

1. **01_collect raw 불변 가드**: raw 파일 존재 시 재수집 skip(또는 재크롤을 `src/collect.py` 별도 함수/스크립트로 분리, 노트북은 skip-if-exists). "노트북 순차 재실행 = 02부터" 재현성 명문화.
2. **무결성 기준 문서 정정**: 결정 1 채택안에 맞춰 CLAUDE.md "데이터 무결성 체크" + `data_dictionary.md` 갱신. reward_norm 결측 = 30(no_event) + 12(future) 분해를 명시.
3. **교차검증 재확인**: 파워업 8행 편입 후 by_type vs by_date 보상 등장 횟수 재집계, Phase 3 대비 불일치 변화 리포트.

## §3. 이번 범위 제외 (Phase 6 이후)

- `cycle_days` 산출(결정 1 입도 확정 후), `is_discontinued` by_type→tidy 병합.
- EDA(03)·예측 모델(04).
