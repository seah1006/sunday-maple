# Work Packet — Phase 3: 파서 보정 + 교차검증 + 보상 인벤토리

## 작업 배경

Phase 2 리뷰 결과 구조화는 견고하나(테스트 12 green, tidy 1160행), **2건의 데이터 정확성 문제**가 확인됐다. Phase 3는 이를 보정하고, 두 소스 교차검증을 수행하며, 정규화·카테고리 설계의 입력이 될 **보상 인벤토리**를 산출한다.

> **정규화(`reward_norm`)·카테고리 매핑은 Phase 4 범위다.** 99개 고유 보상명의 통합·분류는 설계 결정이므로 Claude가 인벤토리를 보고 사전을 설계한 뒤 별도 packet으로 넘긴다. Phase 3는 그 입력 데이터를 만든다.

### Phase 2 리뷰에서 확인된 사실 (직접 검증)

**버그 1 — 단종 미탐지 3건 (Major, 수정 필수)**
`src/parse.py:_parse_type_header`가 `header.startswith("[[B]](단종)[[/B]]")`로만 검사하는데, 실제 원문에 **괄호가 볼드 바깥**인 변형이 3건 존재한다:
```
- ([[B]]단종)[[/B]]경험치 3배 쿠폰(30분) 4장 지급
- ([[B]]단종)[[/B]]접속 시 '메생역전 머니 상자' 1개 지급
- ([[B]]단종)[[/B]]접속 시 '솔 에르다' 1개 지급
```
이 3개가 `is_discontinued=False`로 오분류됨(68 대신 71이 정답). 마커를 먼저 제거한 뒤 `(단종)`으로 시작하는지 검사하면 두 형식 모두 잡힌다.

**버그 2 — no_event_week 미래 오염 (Major, 수정 필수)**
`tidy_prenorm`의 `no_event_week=True` 50행 = 비-미래 38 + **미래 12**. 미래 12건은 "선데이 미진행"이 아니라 **아직 보상 미발표**인 예정 날짜다. `parse_by_date`의 `finish_current()`가 보상 줄 없는 모든 블록을 no_event로 처리해 생긴 혼동.
- 올바른 의미: `no_event_week=True`는 **명시적 센티넬(`없음`/`아예 없음`)이 있는 주에만**.
- 미래 빈 블록(`is_future=True`, 센티넬 없음)은 `no_event_week=False`, `reward_raw=None`(보상 미발표)로 1행 유지.
- 과거인데 보상 줄도 센티넬도 없는 블록이 있으면(현재 ~8건 추정) → 별도로 카운트해 보고(파서 누락 가능성). 임의로 no_event 처리하지 말 것.

---

## 제약 조건

- `data/raw/`는 읽기 전용. 산출물은 `data/interim/`에만.
- 입출력 UTF-8. 콘솔 출력도 UTF-8(`-X utf8`) 권장.
- **정규화·카테고리 매핑·최종 cycle_days 컬럼·`data/processed/` 생성 금지** (Phase 4).
- 기존 통과 테스트(12건)를 깨지 않는다. 보정으로 값이 바뀌는 테스트(단종/no_event)는 기대값을 갱신한다.

---

## 작업 1 — `src/parse.py` 보정

1. **단종 탐지 robust화** (`_parse_type_header`): 헤더에서 마커(`[[B]]`/`[[/B]]` 등)를 먼저 제거한 뒤 `(단종)`으로 시작하면 `is_discontinued=True`로 판정하고 `(단종)`을 제거한 본문을 `reward_raw`로. 두 형식(`[[B]](단종)[[/B]]`, `([[B]]단종)[[/B]]`) 모두 처리.
2. **no_event_week 의미 교정** (`parse_by_date`): 위 "버그 2" 규칙대로. 센티넬 기반만 `True`. 미래 빈 블록은 `no_event_week=False`. 과거 빈 블록은 처리 방식 결정 후 handoff에 명시.

---

## 작업 2 — `tests/test_parse.py` 보강

- 단종 변형 케이스 **2종** 추가: `"- [[B]](단종)[[/B]]경험치 2배"`와 `"- ([[B]]단종)[[/B]]경험치 3배 쿠폰(30분) 4장 지급"` 모두 `is_discontinued=True`, `reward_raw`에 `(단종)`/마커 없음.
- no_event 케이스: 센티넬 줄 → `no_event_week=True`. (미래 블록 분리는 노트북 레벨 검증으로 충분.)
- 기존 12건 유지. 보정으로 기대값 바뀌면 갱신.

---

## 작업 3 — `notebooks/03_crossval.ipynb` (신규)

`data/interim/`의 파싱 결과를 입력으로 교차검증과 인벤토리를 생성. (정규화 없이 수행 가능한 객관 분석만.)

**교차검증 A — by_type 내부 주기 일관성**
- `parsed_by_type`를 보상별로 날짜 정렬 후 연속 등장 간 실제 경과일을 계산.
- 작성자 표기 `stated_cycle_days`와 대조 → 불일치 행 수·예시 출력.
- 첫 등장(주기 None) 제외.

**교차검증 B — 두 뷰 보상 등장 횟수 (정규화 전, exact match)**
- by_type: 보상별 등장 횟수(=날짜 수). by_date: 동일 `reward_raw` 문자열 등장 횟수.
- `reward_raw` **완전일치** 기준으로 대조. 일치/불일치 건수와 매치율 출력.
- 불일치는 표기 차이(정규화 필요)를 정량화하는 자료다 → Phase 4 입력. 여기서 통합하지 말 것.

**산출물 — 보상 인벤토리 (Phase 4 설계 입력)**
- `data/interim/reward_inventory.csv` 생성. 컬럼:
  | 컬럼 | 설명 |
  |---|---|
  | `reward_raw` | 고유 보상 원문 (by_type ∪ by_date) |
  | `freq_by_date` | by_date 등장 횟수 |
  | `freq_by_type` | by_type 등장 횟수 |
  | `first_date` | 최초 등장일 |
  | `last_date` | 최종 등장일 |
  | `is_discontinued` | by_type 단종 여부(보정 후) |
- 빈도 내림차순 정렬. (예상 고유 보상 ~99개 + by_type 측 추가분)

**검증 출력(판정 금지, 수치만)**
- 교차검증 A 불일치 건수.
- 교차검증 B 매치율, 미스매치 예시 10건.
- `reward_inventory.csv` 행 수, 단종 보상 수(=71 기대).
- 보정 후 `tidy_prenorm`의 `no_event_week=True` 수(미래 제외돼 50→약 38 기대), 미래 빈 블록 수(12).

---

## 검증 기준

- `python -m pytest -q` 통과(단종 변형 케이스 포함).
- `notebooks/02_parse_clean.ipynb` 재실행 → 보정된 `data/interim/` 재생성. 단종 고유 보상 **71** 확인.
- `notebooks/03_crossval.ipynb` 재실행 성공, `reward_inventory.csv` 생성.
- 보정 후 `tidy_prenorm`: `no_event_week=True` 행이 모두 비-미래(`is_future=False`)이고 센티넬 기반.
- 데이터 무결성: 날짜 범위 2017-03-12 ~ 2026-08-30 유지, 고유 날짜 수 불변.

---

## 작업 우선순위 요약

| 순위 | 작업 | 산출물 | 예상 규모 |
|---|---|---|---|
| 1 | `src/parse.py` 보정 (단종·no_event) | 함수 2개 수정 | ~25줄 |
| 2 | `tests/test_parse.py` 보강 | +3 케이스 | ~30줄 |
| 3 | `02_parse_clean.ipynb` 재실행 | interim 재생성 | 실행 |
| 4 | `notebooks/03_crossval.ipynb` | 교차검증 + 인벤토리 | ~10셀 |

---

## 이번 범위 제외 항목 (→ Phase 4)

- `reward_norm` 정규화(99개 통합) — Claude가 `reward_inventory.csv` 보고 사전 설계.
- `category` 대분류 매핑 — 동일.
- 최종 tidy(`data/processed/sunday_maple_tidy.csv`) 조립 + `is_discontinued`/`cycle_days` 컬럼 병합.
- `time_limited` 정제(현재 버프 지속시간 `(3분→6분)` 등 오캡처 혼재 — Phase 4에서 운영시간만 분리).
- `is_special` 입도 재검토(현재 event_context에 "타임" 있으면 그날 전체 보상에 전파).
- 502 헤더 vs 501 고유날짜 중복 1건 조사.

---

## Codex 보고 요청 (claude_handoff_phase3.md)

- 단종 보정 후 고유 단종 보상 수(71 확인 여부).
- no_event 교정 후 비-미래 no_event 수, 과거 빈 블록(센티넬 없음) 수와 그 날짜들.
- 교차검증 A 불일치 건수와 대표 예시.
- 교차검증 B 매치율과 미스매치 예시 — 정규화 필요 규모.
- `reward_inventory.csv` 행 수.
