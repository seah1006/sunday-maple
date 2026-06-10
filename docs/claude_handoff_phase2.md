## 작업 범위

Phase 2 Work Packet(`docs/codex_work_packet_phase2.md`)에 따라 Phase 1 원시 텍스트를 구조화했다.

- `src/parse.py`: `view_by_type.txt`, `view_by_date.txt` 정규식 파싱 함수 구현
- `tests/test_parse.py`: 실제 원문 라인 기반 파서 단위 테스트 추가
- `notebooks/02_parse_clean.ipynb`: raw 텍스트 로드, `data/interim/` CSV 3개 생성, 검증 출력

`data/raw/`는 읽기만 했다. 정규화, 카테고리 매핑, 계산 cycle, by_type/by_date 교차검증, tidy로의 단종 merge는 수행하지 않았다.

## 구현 요약

- `src/parse.py`
  - `to_date(s)`: `YYYY.MM.DD`를 `YYYY-MM-DD`로 변환.
  - `parse_by_type(text)`: 보상 헤더와 날짜 줄을 파싱해 `reward_raw`, `date`, `stated_cycle_days`, `is_discontinued`, `trailing` 레코드 생성.
  - `parse_by_date(text)`: 날짜 헤더, 이벤트 맥락, 대형 이벤트 여부, 보상 줄, no-event 센티넬을 파싱.
  - `[[B]]`/`[[S]]` 마커는 신호로 사용한 뒤 컬럼 값에서는 제거.
  - 보상 줄 끝의 trailing 괄호는 분리하되, 줄 전체가 괄호 하나인 조건부 주석은 `reward_raw` 원문으로 유지.

- `tests/test_parse.py`
  - Work Packet 필수 케이스 포함: by_type 주기/첫 등장/단종/trailing, by_date 대형/소형/없음 맥락/no-event, 스페셜 trailing, 다중 trailing, 비일요일 표기.

- `notebooks/02_parse_clean.ipynb`
  - `data/raw/view_by_type.txt`, `data/raw/view_by_date.txt`를 UTF-8로 읽음.
  - `data/interim/parsed_by_type.csv`, `parsed_by_date.csv`, `tidy_prenorm.csv` 저장.
  - `tidy_prenorm.csv`는 by_date 기준으로 `is_special`, `time_limited`, `is_future`, `no_event_week`를 포함.

## 검증 결과

- `python -m pytest -q`: `12 passed in 0.06s`
- `python -c "import src.parse"`: 실행 완료, 출력 없음
- `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_parse_clean.ipynb`: 실행 완료

생성 산출물:

| 파일 | 존재 | 바이트 수 |
|---|---:|---:|
| `data/interim/parsed_by_type.csv` | True | 84793 |
| `data/interim/parsed_by_date.csv` | True | 109751 |
| `data/interim/tidy_prenorm.csv` | True | 125281 |

행 수:

| 데이터 | 행 수 |
|---|---:|
| `parsed_by_type` | 1140 |
| `parsed_by_date` | 1160 |
| `tidy_prenorm` | 1160 |

무결성 출력:

| 항목 | 값 |
|---|---:|
| `tidy_prenorm` 고유 날짜 수 | 501 |
| `parsed_by_date` 고유 날짜 수 | 501 |
| by_date 날짜 헤더 수 | 502 |
| by_date 날짜 패턴 수 | 503 |
| 날짜 min | 2017-03-12 |
| 날짜 max | 2026-08-30 |
| `is_future=True` 행 수 | 12 |
| future 최소 날짜 | 2026-06-14 |
| future 행 전체 `date > 2026-06-10` | True |
| `no_event_week=True` 행 수 | 50 |
| `is_major_event` 비율 | 0.7232758620689655 |
| `parsed_by_type` 단종 고유 보상 수 | 68 |
| `is_special=True` 행 수 | 68 |
| `time_limited` non-null 행 수 | 19 |

Work Packet 요청 관찰:

- 다중 괄호 trailing 행 수: 1
- `[[S]]아예 없음[[/S]]` 원문 센티넬 수: 1
- `[[B]]없음[[/B]]` 원문 센티넬 수: 29
- `no_event_week=True` 총 50행 중 나머지는 보상 줄 없는 날짜 블록을 날짜 spine 보존용 행으로 생성했다.
- 보상 줄로 오인될 수 있는 독립 괄호 주석 행 수: 7
- 독립 괄호 주석은 `reward_raw`에 원문 그대로 넣고 `reward_trailing`으로 분리하지 않았다.
- `reward_raw`가 비어 있는 행 수: 50. 모두 `no_event_week=True` 행이다.

## 데이터 상태

`data/interim/parsed_by_type.csv` 컬럼:

- `reward_raw`
- `date`
- `stated_cycle_days`
- `is_discontinued`
- `trailing`

`data/interim/parsed_by_date.csv` 컬럼:

- `date`
- `event_context`
- `is_major_event`
- `no_event_week`
- `reward_raw`
- `reward_trailing`

`data/interim/tidy_prenorm.csv` 컬럼:

- `date`
- `reward_raw`
- `reward_trailing`
- `event_context`
- `is_major_event`
- `is_special`
- `time_limited`
- `is_future`
- `no_event_week`

`data/processed/` 산출물은 생성하지 않았다.

## Claude 리뷰 요청

Critical:

- 없음.

Major:

- by_date 날짜 헤더 수 502, 고유 날짜 수 501, 날짜 패턴 수 503으로 서로 다름.
- `parsed_by_type` 단종 고유 보상 수가 Work Packet 예상 약 71 대비 68로 집계됨.
- 보상 줄 없는 미래 날짜 블록을 `no_event_week=True` 행으로 보존한 처리 검토.

Minor:

- 독립 괄호 주석 7행을 `reward_raw`로 유지한 처리 검토.
- `is_special`은 Work Packet 문구대로 `reward_trailing` 또는 `event_context`에 `타임`이 포함된 경우만 True로 계산했다.
