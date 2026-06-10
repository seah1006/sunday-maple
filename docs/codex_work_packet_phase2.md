# Work Packet — Phase 2: 텍스트 파싱 & tidy(pre-norm) 구축

## 작업 배경

Phase 1에서 인벤 게시글 원본과 두 뷰의 원시 텍스트(`data/raw/view_by_type.txt`, `view_by_date.txt`)를 확보했다. Phase 2는 이 두 뷰를 정규식으로 파싱해 구조화하고, 분석용 long-format tidy 테이블(정규화 전)을 만든다.

**정규화(`reward_norm`)·카테고리 매핑·cycle_days 계산·두 소스 교차검증은 Phase 3 범위다.** Phase 2는 "원문을 손실 없이 구조화"까지만 한다.

### Phase 1 리뷰에서 확정된 사실 (이 packet의 근거)

실제 `data/raw/` 텍스트를 직접 확인해 아래 포맷을 확정했다. **추측이 아니라 관측된 사실이다.**

**`view_by_type.txt` (보상별 그룹)**
```
- [HEXA 스탯] 메인 스탯이 5레벨 이상일 때, 메인 스탯의 강화 확률 20% 증가   ← 보상 헤더 "- "
2024.07.21                                                                ← 첫 등장(주기 없음)
(+84일)2024.10.13                                                         ← (+N일)직전 등장 대비 경과 + 날짜
(+91일)2025.01.12
- [[B]](단종)[[/B]]경험치 2배                                              ← 단종 보상 헤더
2018.12.16
(+35일)2026.05.31(샤이닝 스타포스 타임)                                    ← 날짜 뒤 trailing (시간제/스페셜)
2018.04.29(하루 종일)                                                     ← trailing (운영시간)
(+903일)2022.05.01(오전 10시~오후 10시)
```
- 보상 헤더: `^- (.*)`. **단종 보상은 헤더가 `[[B]](단종)[[/B]]`로 시작** (총 71건). → `is_discontinued`.
- 날짜 줄: `(?:\(\+(\d+)일\))?(\d{4}\.\d{2}\.\d{2})(\(.*\))?` — 선택적 `(+N일)` 주기, 날짜, 선택적 trailing `(...)`(운영시간/스페셜타임).
- 첫 등장 날짜는 주기 없음(None), 이후는 직전 등장 대비 경과일.

**`view_by_date.txt` (날짜별 그룹)**
```
2017.03.12 (-)                              ← 날짜 + 이벤트맥락. "(-)" = 이벤트 없음
주문의 흔적 강화 비용 30% 할인               ← 그 주 보상들
돌발미션 클리어 경험치 2배
[[S]]2017.03.19[[/S]]                        ← 취소선 날짜 = 그 주 선데이 없음
[[S]]아예 없음[[/S]]                         ← "아예 없음" 센티넬
2017.03.26 (도전! 메이플 레인보우!)          ← 소형 이벤트(괄호, 볼드 아님)
2017.04.30[[B]] <우주 Like 메이플?>[[/B]]    ← 대형 이벤트(볼드 + <...>) → is_major_event
스타포스 ... 성공확률 100%(샤이닝 스타포스 타임) ← 보상 줄 trailing 스페셜
몬스터 사냥 시 경험치 3배 혜택(오전 10시~오후 10시)(=익스트림 레벨업 타임)
```
- 날짜 헤더: `^(\d{4}\.\d{2}\.\d{2})\s*(.*)$`. 뒤따르는 맥락:
  - `[[B]] <이벤트명>[[/B]]` → 대형 이벤트, **is_major_event=True**, event_context=이벤트명.
  - `(이벤트명)`(볼드 아님) → 소형 이벤트, is_major_event=False.
  - `(-)` → 이벤트 없음(event_context=None).
- `[[S]]날짜[[/S]]` + `[[S]]아예 없음[[/S]]` 또는 `[[B]]없음[[/B]]` → **그 주 선데이 없음**(no_event_week). 보상 줄 없음.
- 보상 줄: 날짜 헤더가 아닌 줄. trailing `(...타임)`/`(오전~오후)`/`(하루 종일)`/`(N분)` = 스페셜/운영시간.

**중요 — 미래(예정) 날짜 포함**: by_date 날짜 범위가 `2017.03.12 ~ 2026.08.30`이다. 오늘(2026-06-10) 이후 날짜는 **실제 관측이 아니라 게시글 작성자의 예정/예측치**다. 반드시 `is_future` 플래그로 분리해야 Phase 5 모델링에서 누수가 없고, 관측치와 예측치를 혼동하지 않는다.

**[[S]] 마커 의미 확정**: by_date의 `[[S]]`(2건)는 단종이 아니라 "아예 없음"(선데이 미진행) 주 표시다. 단종은 by_type 헤더의 `[[B]](단종)[[/B]]`로만 표기된다. → Phase 1의 "[[S]]=0" 우려는 정상으로 판정됨.

---

## 제약 조건

- `data/raw/`는 읽기 전용. 절대 수정하지 않는다. Phase 2 산출물은 `data/interim/`에만 쓴다.
- 입출력 UTF-8 명시.
- **정규화/카테고리/cycle 계산/교차검증 금지** (Phase 3). 이번엔 원문 보존 구조화까지.
- 보상 텍스트 원문(`reward_raw`)은 trailing 스페셜/시간 표기를 **분리하되 원문도 함께 보존**한다(손실 금지).
- 마커(`[[B]]`/`[[S]]`)는 파싱 후 최종 컬럼 값에는 남기지 않는다(플래그로 변환). 단, 파싱 입력에서는 신호로 사용.
- 날짜는 `YYYY-MM-DD`로 변환(`2017.03.12` → `2017-03-12`).

---

## 작업 1 — `src/parse.py`

원시 텍스트 → 구조화 레코드 변환 함수 모듈. 정규식 기반.

**요구 함수 (제안 시그니처, 구현 재량)**
```python
def parse_by_type(text: str) -> list[dict]
    # 보상 블록 단위 파싱. 각 (보상, 등장) 레코드 반환:
    # {reward_raw, date(YYYY-MM-DD), stated_cycle_days(int|None),
    #  is_discontinued(bool), trailing(str|None)}
    # - 헤더 "- " 제거, "[[B]](단종)[[/B]]" 감지 -> is_discontinued + 마커 제거
    # - 날짜 줄 정규식으로 (+N일)·날짜·trailing 분리

def parse_by_date(text: str) -> list[dict]
    # 날짜 블록 단위 파싱. 각 (날짜, 보상) 레코드 + no_event 행 반환:
    # {date, event_context(str|None), is_major_event(bool),
    #  no_event_week(bool), reward_raw(str|None), reward_trailing(str|None)}
    # - 날짜 헤더: 볼드<>=대형, ()=소형, (-)=없음
    # - "아예 없음"/"없음" 센티넬 -> no_event_week=True, reward_raw=None
    # - 보상 줄 trailing "(...)" 분리(원문도 보존)

def to_date(s: str) -> str   # "2017.03.12" -> "2017-03-12"
```
> trailing `(...)`은 여러 개 붙을 수 있다(`(오전 10시~오후 10시)(=익스트림 레벨업 타임)`). 마지막 닫는 괄호까지 모두 trailing으로 본다.

---

## 작업 2 — `notebooks/02_parse_clean.ipynb`

`src/parse.py`를 호출해 구조화하고 `data/interim/` 산출물과 tidy(pre-norm)를 만드는 노트북. 단계 분리 원칙(`data/raw` 로드 → `data/interim` 저장).

**산출물 (`data/interim/`)**
1. `parsed_by_type.csv` — 컬럼: `reward_raw, date, stated_cycle_days, is_discontinued, trailing`
2. `parsed_by_date.csv` — 컬럼: `date, event_context, is_major_event, no_event_week, reward_raw, reward_trailing`
3. `tidy_prenorm.csv` — **분석 spine. by_date 보상 행 기준**, 한 행 = (날짜, 보상). 컬럼:
   | 컬럼 | 출처 |
   |---|---|
   | `date` | by_date 헤더 (YYYY-MM-DD) |
   | `reward_raw` | by_date 보상 줄 (trailing 제외 본문) |
   | `reward_trailing` | by_date 보상 줄 trailing 원문 |
   | `event_context` | by_date 헤더 맥락 ("(-)"→null) |
   | `is_major_event` | by_date 헤더 볼드<> 여부 |
   | `is_special` | reward_trailing/이벤트에 "타임" 포함 여부(미라클/샤이닝스타포스/솔에르다 등) |
   | `time_limited` | trailing의 운영시간 표기("하루 종일"/"오전~오후"/"N분")에서 도출, 없으면 "하루종일" 기본 가정은 하지 말고 null |
   | `is_future` | `date > 2026-06-10`(오늘) |
   | `no_event_week` | 그 주 선데이 없음(보상 없는 행) |

> `reward_norm`, `category`, `cycle_days`(계산), `is_discontinued`(merge)는 **이 단계에서 만들지 않는다**. Phase 3에서 `tidy_prenorm.csv` + `parsed_by_type.csv`를 입력으로 정규화·매핑·교차검증 후 `data/processed/sunday_maple_tidy.csv` 완성.

**노트북 검증 셀(출력만, 판정 금지)**
- 각 산출물 행 수.
- `tidy_prenorm`: 고유 날짜 수(예상 ~503), `is_future=True` 행 수, `no_event_week=True` 행 수, `is_major_event` 비율.
- 날짜 범위(min/max) 출력 → 2017-03-12 ~ 2026-08-30 확인.
- `parsed_by_type`: `is_discontinued=True` 고유 보상 수(예상 ~71).

---

## 작업 3 — `tests/test_parse.py`

`src/parse.py`의 정규식 분리를 실제 원문 라인 픽스처로 검증. **Phase 1에서 비어 있던 pytest를 여기서 채운다.**

필수 케이스(실제 관측 라인 사용):
- by_type 주기 줄: `"(+84일)2024.10.13"` → cycle=84, date="2024-10-13", trailing=None
- by_type 첫 등장: `"2024.07.21"` → cycle=None
- by_type 단종 헤더: `"- [[B]](단종)[[/B]]경험치 2배"` → reward_raw="경험치 2배", is_discontinued=True
- by_type trailing: `"(+35일)2026.05.31(샤이닝 스타포스 타임)"` → cycle=35, date="2026-05-31", trailing="(샤이닝 스타포스 타임)"
- by_date 대형: `"2017.04.30[[B]] <우주 Like 메이플?>[[/B]]"` → date, event_context="우주 Like 메이플?", is_major_event=True
- by_date 소형: `"2017.03.26 (도전! 메이플 레인보우!)"` → event_context="도전! 메이플 레인보우!", is_major_event=False
- by_date 없음 맥락: `"2017.03.12 (-)"` → event_context=None
- by_date 선데이 없음: `"[[S]]아예 없음[[/S]]"` → no_event_week=True
- 보상 스페셜 trailing: `"스타포스 강화 비용 30% 할인(샤이닝 스타포스 타임)"` → reward_raw="스타포스 강화 비용 30% 할인", is_special 신호 trailing 분리
- 비일요일 예외: by_date에 `(월)`/`(토)` 등 7건 존재 → 날짜 파싱이 깨지지 않는지(파싱은 되되 요일 표기는 Phase 3에서 검토) 1건 케이스 포함

---

## 검증 기준

- `python -m pytest -q` **통과**(테스트 존재, 모두 green).
- `python -c "import src.parse"` 성공.
- `notebooks/02_parse_clean.ipynb` 커널 재시작 후 전체 실행 성공.
- `data/interim/`에 3개 CSV 생성.
- 데이터 무결성 출력:
  - `tidy_prenorm` 고유 날짜 수가 by_date 날짜 헤더 수와 일치.
  - `is_future=True` 행 수 > 0 이고 모든 future 행 date > 2026-06-10.
  - 날짜 min=2017-03-12, max=2026-08-30.
  - `parsed_by_type`의 단종 고유 보상 수 ≈ 71.

---

## 작업 우선순위 요약

| 순위 | 작업 | 산출물 | 예상 규모 |
|---|---|---|---|
| 1 | `src/parse.py` | 파싱 함수 3개 + 헬퍼 | ~150줄 |
| 2 | `tests/test_parse.py` | 10케이스 단위 테스트 | ~90줄 |
| 3 | `notebooks/02_parse_clean.ipynb` | 구조화·tidy·검증 | ~8셀 |

---

## 이번 범위 제외 항목 (→ Phase 3)

- `reward_norm` 정규화(띄어쓰기·어순·표기 통합).
- `category` 대분류 매핑.
- `cycle_days` **계산**(정규화 보상 기준 날짜 diff) 및 by_type `stated_cycle_days`와의 **교차검증**.
- `is_discontinued`를 tidy로 merge.
- by_type ↔ by_date 보상 등장 횟수 교차검증.
- 비일요일 예외·표기 변화의 의사결정 기록(`data_dictionary.md` 로그).

---

## Codex 보고 요청 (claude_handoff_phase2.md)

- 두 뷰 trailing `(...)` 다중 괄호 분리가 깨진 케이스 유무(예: `(=익스트림 레벨업 타임)`).
- `no_event_week` 행이 `[[S]]아예 없음[[/S]]`과 `[[B]]없음[[/B]]` 둘 다에서 잡혔는지(둘의 개수).
- 보상 줄로 오인될 수 있는 비-보상 텍스트(예: `(리부트, 리부트2월드 : ...)` 같은 조건부 주석)를 어떻게 처리했는지 — 보상 행으로 넣었는지/분리했는지(판정은 Claude가 함).
- 무결성 출력 실제 수치.
