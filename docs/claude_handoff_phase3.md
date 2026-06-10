## 작업 범위

Phase 3 Work Packet(`docs/codex_work_packet_phase3.md`)에 따라 파서 보정, 테스트 보강, Phase 2 노트북 재실행, 교차검증 노트북 신규 생성을 수행했다.

- `src/parse.py`: 단종 헤더 변형 탐지, 빈 날짜 블록의 `no_event_week` 의미 보정
- `tests/test_parse.py`: 단종 변형과 센티넬 없는 빈 블록 케이스 추가
- `notebooks/02_parse_clean.ipynb`: 보정된 파서 기준으로 재실행
- `notebooks/03_crossval.ipynb`: 교차검증 A/B 및 보상 인벤토리 생성

정규화, 카테고리 매핑, 최종 `cycle_days` 컬럼 생성, `data/processed/` 산출물 생성은 수행하지 않았다.

## 구현 요약

- 단종 탐지 보정
  - `_parse_type_header()`에서 `[[B]]`/`[[/B]]` 마커를 먼저 제거한 뒤 `(단종)` prefix를 검사하도록 변경.
  - `[[B]](단종)[[/B]]...`와 `([[B]]단종)[[/B]]...` 두 형식을 모두 `is_discontinued=True`로 파싱.

- no-event 의미 보정
  - `parse_by_date()`에서 보상 줄 없는 날짜 블록은 `reward_raw=None`, `no_event_week=False`로 유지.
  - `no_event_week=True`는 `없음`/`아예 없음` 센티넬 줄이 명시된 경우에만 생성.

- `03_crossval.ipynb`
  - `parsed_by_type.csv` 내부에서 보상별 실제 날짜 diff와 `stated_cycle_days` 비교.
  - `reward_raw` exact match 기준 by_type/by_date 등장 횟수 비교.
  - `data/interim/reward_inventory.csv` 생성.

## 검증 결과

- `python -m pytest -q`: `14 passed in 0.06s`
- `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_parse_clean.ipynb`: 실행 완료
- `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/03_crossval.ipynb`: 실행 완료

산출물:

| 파일 | 존재 | 바이트 수 |
|---|---:|---:|
| `data/interim/parsed_by_type.csv` | True | 84712 |
| `data/interim/parsed_by_date.csv` | True | 109771 |
| `data/interim/tidy_prenorm.csv` | True | 125301 |
| `data/interim/reward_inventory.csv` | True | 9603 |

파서 보정 후 수치:

| 항목 | 값 |
|---|---:|
| `parsed_by_type` 행 수 | 1140 |
| `parsed_by_date` 행 수 | 1160 |
| `tidy_prenorm` 행 수 | 1160 |
| 단종 고유 보상 수 | 71 |
| `no_event_week=True` 행 수 | 30 |
| `no_event_week=True` 중 미래 행 수 | 0 |
| 미래 빈 블록 수 | 12 |
| 과거 빈 블록 수(센티넬 없음) | 8 |
| 날짜 범위 | 2017-03-12 ~ 2026-08-30 |
| 고유 날짜 수 | 501 |

과거 빈 블록 날짜:

- 2023-01-12
- 2023-01-12
- 2023-01-13
- 2023-01-14
- 2023-01-15
- 2023-01-16
- 2023-01-17
- 2023-01-18

교차검증 A — by_type 내부 주기:

| 항목 | 값 |
|---|---:|
| 주기 검증 대상 행 수 | 1041 |
| `stated_cycle_days` 불일치 행 수 | 0 |

대표 예시:

- 불일치 행 없음.

교차검증 B — by_type/by_date exact `reward_raw` 등장 횟수:

| 항목 | 값 |
|---|---:|
| exact reward 고유값 수 | 113 |
| 등장 횟수 일치 보상 수 | 75 |
| 등장 횟수 불일치 보상 수 | 38 |
| exact count match rate | 0.6637168141592921 |

미스매치 예시 10건:

| reward_raw | freq_by_type | freq_by_date |
|---|---:|---:|
| 스타포스 강화 비용 30% 할인 | 73 | 71 |
| 어빌리티 재설정 비용 50% 할인 | 69 | 68 |
| 주문의 흔적 강화 비용 50% 할인 | 68 | 67 |
| 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100% | 55 | 54 |
| 소울 조각 사용 시 위대한 소울 획득 확률 5배 | 53 | 52 |
| 10성 이하에서 스타포스 강화 성공 시 1+1 강화 | 42 | 41 |
| 폴로와 프리토의 현상금 사냥 경험치 2배 | 53 | 31 |
| 폴로와 프리토, 에스페시아의 현상금 사냥 경험치 2배 | 0 | 22 |
| 사냥 시 소환되는 엘리트 몬스터 수 증가 | 0 | 19 |
| 미라클 타임 | 16 | 15 |

보상 인벤토리:

| 항목 | 값 |
|---|---:|
| `reward_inventory.csv` 행 수 | 113 |
| `reward_inventory.csv` 단종 보상 수 | 71 |

## 데이터 상태

`data/interim/reward_inventory.csv` 컬럼:

- `reward_raw`
- `freq_by_date`
- `freq_by_type`
- `first_date`
- `last_date`
- `is_discontinued`

`data/processed/`에는 새 산출물을 만들지 않았다. 기존 `.gitkeep`만 확인됨.

## Claude 리뷰 요청

Critical:

- 없음.

Major:

- 과거 빈 블록 8행의 의미 검토.
- exact-match 기준 등장 횟수 불일치 38개 보상의 Phase 4 정규화 설계 검토.

Minor:

- `2023-01-12`가 과거 빈 블록에 2회 포함됨. 중복 날짜 헤더 이슈는 Phase 4 범위 제외 항목에 남아 있음.
