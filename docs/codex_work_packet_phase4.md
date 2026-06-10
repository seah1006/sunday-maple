# Codex Work Packet — Phase 4 (보상 정규화·카테고리·강도 + 파워업 위크 흡수)

> 입력 설계: `docs/phase4_normalization_design.md`. 사용자가 §4 열린 결정 4건을 확정함(아래 "작업 배경"). 본 packet이 그 결정을 사양으로 확정한다.

## 작업 배경

Phase 3에서 `data/interim/reward_inventory.csv`(by_date 기준 고유 보상 113개)와 교차검증을 완료했고, 2023-01 "파워업 위크" 7줄이 `YYYY.MM.DD(요일) - 보상` 형식이라 `parse_by_date`에서 누락됨을 확인했다(보상 자체는 by_type에 보존). Phase 4는 보상명을 정규화해 분석 가능한 tidy를 산출하고, 파워업 위크를 흡수한다.

### 사용자 확정 결정 (§4)

| # | 결정 | 선택 | 사양 반영 |
|---|---|---|---|
| 1 | 스페셜 처리 | **플래그만(`is_special`)** | 별도 `스페셜` 카테고리 없음. 모든 보상은 benefit 카테고리. `is_special`로만 표시 |
| 2 | 환생의 불꽃 | **분리** | `환생의불꽃_강력한` / `환생의불꽃_영원한` |
| 3 | 솔 에르다 | **분리** | `솔에르다_사냥` / `솔에르다_접속지급` |
| 4 | 파워업 위크 7줄 | **tidy 포함** | by_date 파서가 흡수, 총 8 관측치(01.14 = 2건) |

### Claude 직접 조사 사실 (원문 출처: `data/raw/view_by_type.txt`, `view_by_date.txt`)

1. **by_type 헤더(`- ` 라인) = 99개 보상 원형.** by_date 113개와의 차이는 중간 명칭변경 변형(예: `폴로와 프리토의 현상금…` → `폴로와 프리토, 에스페시아의 현상금…`)이 by_date에서 별개 문자열로 등장하기 때문. 모두 같은 norm으로 통합된다.
2. **§2 설계 누락**: `[HEXA 스탯] 메인 스탯이 5레벨 이상일 때, 메인 스탯의 강화 확률 20% 증가`(view_by_type.txt:1)가 §2 norm 표에 없다. → 신규 norm `HEXA스탯_강화확률`(카테고리 강화) 추가. 나머지 98개는 §2로 매핑된다.
3. **파워업 위크 원문**(view_by_date.txt:896–903):
   ```
   2023.01.12~2023.01.18[[B]] [[/B]][[B]]<요정 웡키의 웡스토랑 - 마이크의 파워업 위크>[[/B]]
   2023.01.12(목) - 10성 이하에서 스타포스 강화 성공 시 1+1 강화
   2023.01.13(금) - 소울 조각 사용 시 위대한 소울 획득 확률 5배
   2023.01.14(토) - 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%(샤이닝 스타포스 타임), 스타포스 강화 비용 30% 할인(샤이닝 스타포스 타임)
   2023.01.15(일) - 미라클 타임(오전 8시~오후 11시 30분)
   2023.01.16(월) - 주문의 흔적 강화 비용 50% 할인
   2023.01.17(화) - 어빌리티 재설정 비용 50% 할인
   2023.01.18(수) - 스타포스 강화 비용 30% 할인
   ```
   - 보상명 콤마 분리 주의: 보상명 자체에 `5, 10, 15성`처럼 콤마가 있음. 보상 구분 콤마는 **`,` + 공백 + 비숫자**로만 발생(`100%(샤이닝 스타포스 타임), 스타포스…`). 규칙 `,\s+(?=[^\d])`로 분리하면 안전(아래 Task 2에 정답 8행 고정).
   - 일별 보상명은 접미 `(샤이닝 스타포스 타임)` / `(오전 8시~오후 11시 30분)` 분리 후 by_type 정규 헤더와 **정확히 일치**(예: `스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%` = view_by_type.txt:690) → 정규화 dict가 그대로 매핑한다.
4. **decision-1 파급**: 기존 `is_special`(notebooks/02_parse_clean.ipynb, `is_special` 함수)은 `reward_trailing`·`event_context`의 "타임"만 검사해, standalone `미라클 타임`/`샤이닝 스타포스 타임` 같은 **보상명 자체가 타임**인 행을 놓친다. decision-1(플래그만)에서는 이 행들이 핵심이므로 `reward_raw`까지 "타임" 검사를 확장해야 한다. "타임"을 포함하는 보상은 전부 특별시간 이벤트뿐임을 확인(미라클/코디/헤어/펫/샤이닝 스타포스/솔 에르다/익스트림 레벨업 타임). 오탐 없음.

## 제약 조건

- `data/raw/` **불변**. 절대 수정/재크롤 금지.
- 기존 `python -m pytest -q`(tests/test_parse.py) **전부 통과 유지**. `src/parse.py`의 기존 공개 함수 시그니처(`parse_by_type`, `parse_by_date`, `parse_type_date_line`, `parse_date_header`, `split_reward_trailing`)·반환 스키마 유지. Task 2는 **추가**만, 기존 정상 경로 회귀 금지.
- 노트북 01→02 커널 재시작 후 순차 재실행 성공 유지. (`data/interim`는 gitignore → 재생성 전제)
- tidy 기존 컬럼/의미 유지. Phase 4는 **컬럼 추가** + `is_special` 의미 확장(decision-1 필수) + 파워업 위크 행 추가만.
- 한 행 = 한 관측치(특정 날짜의 한 보상) 원칙 유지.
- 범위 밖(cycle_days 계산, is_discontinued by_type 병합, 모델링)은 손대지 않는다(§이번 범위 제외).

---

## 작업 1 — `src/normalize.py` 신규 생성 (정규화·카테고리·강도)

**수정 대상**: `src/normalize.py`(신규), `tests/test_normalize.py`(신규).

### 1-A. 공개 API

```python
def normalize_reward(reward_raw: str) -> str | None
def categorize(reward_norm: str) -> str
def extract_magnitude(reward_raw: str) -> str | None
```

- `normalize_reward`: 정제된 `reward_raw`(접미 trailing 분리 후 본문, `[[..]]` 마커·`(단종)` 없음)를 받아 `reward_norm` 반환. 매핑 불가 시 `None` 반환(예외 던지지 말 것 — 커버리지 테스트가 None을 잡는다).
- `categorize`: `reward_norm` → 카테고리 5분류 중 하나(`강화/성장/사냥효율/수집기타/스페셜` 중 **스페셜 미사용**, 즉 4개만 산출). 미정의 norm은 `KeyError` 대신 `"미분류"` 반환.
- `extract_magnitude`: 통합으로 사라지는 강도 토큰 1개를 문자열로 반환(아래 우선순위). 없으면 `None`.

### 1-B. reward_norm 매핑 (결정적 규칙)

구현 방식은 자유(정확 문자열 dict 또는 우선순위 substring 규칙). **단, 결과는 결정적이어야 하고 아래 표의 모든 보상이 정확히 하나의 norm으로 매핑되어야 한다.** substring 규칙 사용 시 아래 "분리 주의" 항목 때문에 **더 구체적인 조건을 먼저** 적용할 것.

#### 강화 (category=강화)
| reward_norm | 매핑 조건(원문 식별) |
|---|---|
| `HEXA스탯_강화확률` | `[HEXA 스탯]` + `강화 확률` 포함 |
| `스타포스_성공확률` | `스타포스` + `성공확률 100%` / **`샤이닝 스타포스 타임`(standalone, 별칭)** |
| `스타포스_비용할인` | `스타포스 강화 비용` + `할인` |
| `스타포스_1+1강화` | `1+1 강화` |
| `스타포스_파괴방지` | `파괴 확률` + `감소` |
| `주문의흔적_비용할인` | `주문의 흔적 강화 비용` + `할인` |
| `흔적복구_비용할인` | `흔적 복구 비용` + `할인` |
| `어빌리티_재설정할인` | `어빌리티 재설정 비용` + `할인` |
| `잠재능력_재설정할인` | `잠재능력` + `재설정 비용` + `할인` |
| `환생의불꽃_강력한` | `강력한 환생의 불꽃` |
| `환생의불꽃_영원한` | `영원한 환생의 불꽃` |
| `미라클타임` | `미라클 타임` |

#### 성장 (category=성장)
| reward_norm | 매핑 조건 |
|---|---|
| `경험치_배수버프` | 정확히 `경험치 2배` / **`익스트림 레벨업 타임`(별칭)** |
| `경험치쿠폰_지급` | `경험치` + `쿠폰` + `지급` (2·3배, 15·30분, N장 전부) |
| `룬_경험치버프` | `룬 경험치 버프` |
| `룬_재등장감소` | `룬 재등장` |
| `콤보킬_경험치` | `콤보킬 경험치` / `99콤보` + `콤보킬 구슬` |
| `몬스터파크_경험치` | `몬스터 파크 클리어 경험치` / `몬스터파크` + `성장의 일요일 상자` |
| `버닝` | `버닝 필드` / `버닝 부스터`(테라·메가) |
| `성장의비약_지급` | `성장의 비약` (익스트림·폭풍) |
| `유니온_코인` | `유니온 일일퀘스트 코인` |
| `우르스` | `우르스` |

#### 사냥효율 (category=사냥효율)
| reward_norm | 매핑 조건 |
|---|---|
| `현상금_경험치` | `현상금 사냥 경험치` (폴로와 프리토 / +에스페시아, 1.5~5배 전부) |
| `불꽃늑대_경험치` | `불꽃늑대 퇴장` |
| `엘리트몬스터_증가` | `엘리트 몬스터 수 증가` |
| `솔에르다_사냥` | `사냥을 통해 획득` + `솔 에르다` / **`솔 에르다 타임`(standalone, 별칭)** |
| `트레져헌터_경험치` | `트레져 헌터 경험치` |
| `아케인리버_보상` | `아케인리버` + `보상 2배` |
| `돌발미션` | `돌발미션` |
| `명예의훈장` | `명예의 훈장` |
| `보스파티_버프` | `보스파티 결성 버프` |
| `파티퀘스트` | `파티퀘스트` |
| `심신수련관` | `심신수련관` |
| `엘리트마일리지` | `엘리트 몬스터 마일리지` |

#### 수집기타 (category=수집기타)
| reward_norm | 매핑 조건 |
|---|---|
| `몬스터컬렉션` | `몬스터 컬렉션` (모몽/신규 등록/탐험 시간) |
| `위대한소울_확률` | `위대한 소울` |
| `심볼교환권_지급` | `심볼 교환권` (아케인 20/30/50, 선택 심볼) |
| `솔에르다_접속지급` | `솔 에르다` + (`접속` / `누적 접속`) |
| `VIP부스터_지급` | `VIP 부스터` |
| `캐릭터슬롯_지급` | `캐릭터 슬롯` |
| `데미지스킨_지급` | `데미지 스킨` |
| `유니온프리셋_지급` | `유니온 프리셋 쿠폰` |
| `프리미엄PC방` | `프리미엄 PC방` |
| `리부트_드롭률` | `리부트` + `드롭률` |
| `코디타임` | `코디 타임` |
| `헤어타임` | `헤어 타임` |
| `펫타임` | `펫 타임` |
| `선물_기타지급` | `썬데이메이플 선물` / `운영자의 특별한 선물` / `메생역전 머니 상자` / `솜사탕 핑크빈 교환권` / `마스터 라벨` |

> **분리 주의 (substring 규칙 순서)**: ① `환생의 불꽃`은 `강력한`/`영원한`으로 분기. ② `솔 에르다`는 `사냥을 통해 획득`(→사냥) / `솔 에르다 타임`(→사냥, 별칭) / `접속`·`누적 접속`(→접속지급)으로 분기 — `사냥`·`타임` 조건을 `접속`보다 먼저. ③ `룬`은 `경험치 버프`(→경험치버프) / `재등장`(→재등장감소) 분기.

> **별칭(standalone "X 타임") 매핑 근거**: `샤이닝 스타포스 타임`→`스타포스_성공확률`, `익스트림 레벨업 타임`→`경험치_배수버프`는 설계 §2 확정. `솔 에르다 타임`→`솔에르다_사냥`은 본 packet 판단(해당 타임 이벤트가 사냥 솔 에르다 증가를 헤드라인으로 함; 같은 날짜의 사냥 3배 행과 norm 일치). 이 별칭 행들은 `is_special=True`로 분류된다(Task 3). **(date, reward_norm) 중복 가능성**(별칭 행 + 같은 날 benefit 행)은 Task 3 무결성 체크에서 카운트해 리포트할 것 — 침묵 제거 금지, 발견 시 Claude 리뷰로.

### 1-C. extract_magnitude 우선순위

`reward_raw`에서 아래 순서로 **첫 매치 1개**를 반환(문자열 그대로). 강도 보존이 목적이며 분석은 `reward_norm` 집계를 권장(주석으로 명시).

1. 배수: `(\d+(?:\.\d+)?)배` → 예 `2배`, `1.5배`, `5배`
2. 퍼센트(증감): `\+?\d+%` → 예 `+300%`, `100%`, `20%`
3. 개수/장수: `\d+개` / `\d+장` → 예 `50개`, `4장`
4. 분: `\d+분` → 예 `15분`, `30분`
5. 비율/횟수 괄호: `\d+회|\d+성|\d+단계` → 예 `5회`, `15성`
6. 위 모두 없으면 `None`

> magnitude는 best-effort. trailing(`(샤이닝 스타포스 타임)` 등)·`(단종)`은 제외된 본문에서 추출. 다중 수치 보상은 첫 매치만(예 `경험치 2배 쿠폰(30분) 4장` → `2배`).

### 1-D. 검증 요구사항 (tests/test_normalize.py)

- `test_normalize_known_rewards`: by_type 헤더 대표 케이스(각 norm 최소 1개, 총 ~40 케이스) → 기대 norm 일치.
- `test_split_decisions`: `강력한/영원한 환생의 불꽃` → 분리 norm. `사냥…솔 에르다`/`솔 에르다 타임`/`접속 시 솔 에르다`/`접속 시간 2분마다 솔 에르다` → 사냥·사냥·접속·접속.
- `test_alias_norms`: `샤이닝 스타포스 타임`→`스타포스_성공확률`, `익스트림 레벨업 타임`→`경험치_배수버프`, `솔 에르다 타임`→`솔에르다_사냥`.
- `test_category_no_special`: `categorize`가 어떤 norm에도 `스페셜`을 반환하지 않음(decision-1). 미라클/코디/헤어/펫타임 → 각 강화/수집기타/수집기타/수집기타.
- `test_magnitude_examples`: `2배`,`+300%`,`20%`,`50개`,`4장`,`15분` 추출 및 강도 없는 보상(`미라클 타임`, `룬 재등장…`) → `None`.
- `test_coverage_all_rewards`(**필수 안전망**): `data/interim/reward_inventory.csv`의 모든 `reward_raw`(정제본)에 대해 `normalize_reward(...)`가 `None`이 아니고 `categorize(...)`가 `"미분류"`가 아님을 단언. 실패 시 미매핑 문자열을 출력하고 Claude에게 리포트(규칙 보강은 다음 packet에서).

---

## 작업 2 — `parse_by_date` 인라인 일별/주간 형식 흡수 (파워업 위크)

**수정 대상**: `src/parse.py`(`parse_by_date` + 신규 헬퍼/정규식), `tests/test_parse.py`(케이스 추가).

### 2-A. 현재 동작(문제)

`parse_by_date`는 라인이 `\d{4}\.\d{2}\.\d{2}`로 시작하면 전부 단일 날짜 헤더로 처리한다. 따라서:
- 주간 배너 `2023.01.12~2023.01.18 …<파워업 위크>` → `2023-01-12` 빈 헤더로 오인.
- 일별 라인 `2023.01.12(목) - 보상…` → 각각 **새 빈 날짜 헤더**로 오인되어 보상 본문이 `event_context`로 흡수·소실. 결과: 해당 8 관측치 누락(현재 by_type에만 존재).

### 2-B. 목표 동작

`parse_by_date` 루프에서 **단일 날짜 헤더 판정보다 먼저** 다음 두 형식을 처리:

1. **주간 배너** `WEEK_HEADER_RE = ^(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})(.*)$`
   - 매치 시: 배너의 이벤트명·major 여부를 추출해 **활성 주간 컨텍스트**로 저장(`event_context`, `is_major_event`). 보상 행은 emit하지 않음. `current`(일반 spine) 갱신하지 않음.
   - 이벤트명 추출은 기존 `_parse_date_header`의 major 정규식 재사용(`[[B]]<...>[[/B]]` → major). `<>` 없으면 소형 컨텍스트로.
2. **인라인 일별** `INLINE_DAILY_RE = ^(\d{4}\.\d{2}\.\d{2})\([가-힣]\)\s*-\s*(.+)$`
   - 매치 시: 우변을 `,\s+(?=[^\d])`로 보상 분리 → 각 보상에 기존 `split_reward_trailing` 적용(본문+trailing) → **활성 주간 컨텍스트**(없으면 None/False)를 붙여 행 emit. `date`=해당 일.
   - 산출 행 스키마는 기존 by_date 레코드와 동일: `{date, event_context, is_major_event, no_event_week:False, reward_raw, reward_trailing}`.
   - `current_has_rows`/`finish_current` 로직과 충돌하지 않게: 인라인 행은 `current` spine과 독립적으로 append하되, 직전 `current`가 빈 헤더로 잘못 닫히지 않도록 처리(인라인 블록은 자체 emit).
- 일반 단일 날짜 헤더(`2023.01.22 …`)를 만나면 활성 주간 컨텍스트를 **해제**(`None`).

> 체크 순서: `WEEK_HEADER_RE` → `INLINE_DAILY_RE` → 기존 `_parse_date_header` → no_event 센티넬 → 일반 보상 행. (인라인·주간이 단일 날짜 정규식에 먼저 걸리지 않도록 순서 엄수.)

### 2-C. 정답 고정 (파워업 위크 8 관측치)

Task 2 통과 기준은 아래 8행이 정확히 생성됨(`event_context="요정 웡키의 웡스토랑 - 마이크의 파워업 위크"`, `is_major_event=True` 전부):

| date | reward_raw | reward_trailing |
|---|---|---|
| 2023-01-12 | 10성 이하에서 스타포스 강화 성공 시 1+1 강화 | None |
| 2023-01-13 | 소울 조각 사용 시 위대한 소울 획득 확률 5배 | None |
| 2023-01-14 | 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100% | (샤이닝 스타포스 타임) |
| 2023-01-14 | 스타포스 강화 비용 30% 할인 | (샤이닝 스타포스 타임) |
| 2023-01-15 | 미라클 타임 | (오전 8시~오후 11시 30분) |
| 2023-01-16 | 주문의 흔적 강화 비용 50% 할인 | None |
| 2023-01-17 | 어빌리티 재설정 비용 50% 할인 | None |
| 2023-01-18 | 스타포스 강화 비용 30% 할인 | None |

### 2-D. 검증 요구사항 (tests/test_parse.py 추가)

- `test_week_banner_sets_context`: 주간 배너 라인이 보상 행을 만들지 않고 이벤트명/ major를 컨텍스트로 보유.
- `test_inline_daily_rewards`: 위 픽스처(주간 배너 + 7 일별 라인) 입력 → 정확히 8행, 위 표와 일치(date/reward_raw/reward_trailing/event_context/is_major_event).
- `test_inline_multi_reward_comma_split`: 01.14 라인 단독 → 2행(`5, 10, 15성` 콤마는 분리 안 됨).
- `test_existing_by_date_unchanged`(회귀): 기존 정상 포맷 입력이 종전과 동일 결과(행 수·필드) — 기존 케이스 유지/보강.

---

## 작업 3 — 노트북 02 통합 + processed tidy 산출

**수정 대상**: `notebooks/02_parse_clean.ipynb`(셀 추가/수정), `data/processed/tidy_rewards.csv`(신규 산출).

### 3-A. is_special 확장 (decision-1 필수)

기존 `is_special`(reward_trailing·event_context의 "타임" 검사)을 **reward_raw 포함**으로 확장:
```python
def is_special(row):
    text = ' '.join(str(x) for x in [row.get('reward_raw'), row.get('reward_trailing'), row.get('event_context')] if pd.notna(x))
    return '타임' in text
```
근거: standalone `미라클 타임`·`샤이닝 스타포스 타임`·`솔 에르다 타임` 등 보상명 자체가 특별시간인 행을 포착(작업 배경 4). "타임"은 특별시간 이벤트에만 등장(오탐 없음 확인).

### 3-B. 정규화 컬럼 추가

`tidy_prenorm`(이미 파워업 위크 8행 포함된 상태) → `tidy_rewards`:
- `reward_norm = normalize_reward(reward_raw 정제본)` — `reward_raw`가 None(no_event_week 행)이면 None.
- `category = categorize(reward_norm)` — reward_norm None이면 None.
- `reward_magnitude = extract_magnitude(reward_raw)`.
- 기존 컬럼 유지: `date, reward_raw, reward_trailing, event_context, is_major_event, is_special, time_limited, is_future, no_event_week`.
- 최종 컬럼 순서: `date, reward_raw, reward_norm, category, reward_magnitude, event_context, is_major_event, is_special, time_limited, is_discontinued?(범위밖→제외), is_future, no_event_week`. (is_discontinued/cycle_days는 이번 범위 제외.)
- `data/processed/tidy_rewards.csv`로 UTF-8 저장. `data/interim`의 중간물은 기존대로.

### 3-C. 데이터 무결성 체크 셀 (출력 필수)

다음을 출력(판정은 Claude):
1. 총 행 수, `reward_norm` 결측 수(= no_event_week 행 수 30과 일치해야 함), `reward_norm`이 None인데 reward_raw가 not None인 행 수(= **미매핑, 0이어야 함**, 0 아니면 문자열 목록 출력).
2. `category` 분포(`value_counts`), `스페셜`/`미분류` 카테고리가 0인지.
3. **(date, reward_norm) 중복 건수**(별칭 행 ↔ 같은 날 benefit 행 충돌 가능 — 카운트·해당 (date,norm) 목록 출력, 제거하지 말 것).
4. 고유 `reward_norm` 개수(설계 기대 ~46개 norm 안팎; 정확값은 결과로 보고).
5. 파워업 위크 8행 존재 확인(2023-01-12~18, 위 표와 대조).
6. 날짜 범위(2017 첫 회차~최신), 일요일 아닌 date 목록이 기존 알려진 예외와 일치하는지.

### 3-D. 의사결정 문서화

- `data_dictionary.md`에 신규 컬럼(`reward_norm`, `category`, `reward_magnitude`) 정의와 §4 결정 4건·별칭 매핑·미라클/코디/헤어/펫 재배치 근거를 추가(전처리 평가 핵심).
- 노트북 마크다운 셀에 decision-1~4 적용 요약.

---

## 검증 기준

- `python -m pytest -q` 전부 통과(기존 + `test_normalize.py` + `test_parse.py` 추가분). 특히 `test_coverage_all_rewards` 통과(미매핑 0).
- 노트북 01→02 커널 재시작 후 순차 재실행 성공, 3-C 무결성 출력이 위 기대와 일치.
- `data/processed/tidy_rewards.csv` 생성, 파워업 위크 8행 포함, `스페셜`·`미분류` 카테고리 0.

## 작업 우선순위 요약

| 작업 | 대상 | 규모(예상) | 의존 |
|---|---|---|---|
| 1 | `src/normalize.py` + `tests/test_normalize.py` | 신규 ~180줄 | reward_inventory.csv(02 재실행) |
| 2 | `src/parse.py` 인라인/주간 파서 + 테스트 | +60줄 | 없음 |
| 3 | `02_parse_clean.ipynb` 통합 + processed 산출 + data_dictionary | +40줄 | 작업1·2 |

> 작업 2를 먼저(파워업 위크가 inventory에 반영돼야 작업1 커버리지 테스트가 8행을 포함) → 그 다음 작업1 → 작업3 순서 권장.

## 이번 범위 제외 항목

- `cycle_days`(직전 동일 reward_norm 경과일) 계산 — reward_norm 확정 후 별도 Phase.
- `is_discontinued`(by_type) → tidy 병합 — 별도 Phase(by_type/by_date 키 정합 필요).
- 예측 모델·EDA 시각화(03/04) — Phase 4 이후.
- (date, reward_norm) 별칭 중복의 최종 해소 정책 — 3-C에서 **카운트·리포트만**. 실제 dedup 여부는 결과 확인 후 Claude가 다음 packet에서 결정(섣부른 제거 금지).
- magnitude 다중값·정밀 파싱 — 첫 매치 1개로 충분.
