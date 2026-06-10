# Claude Handoff — Phase 4

## 작업 범위

- Phase 4 구현·셀프검증만 수행.
- `data/raw/`는 수정하지 않음. `01_collect.ipynb`는 `collect_main()`으로 raw 재수집/재쓰기 가능성이 있어 실행하지 않음.
- 범위 밖으로 지정된 `cycle_days`, `is_discontinued` tidy 병합, 모델/EDA, `(date, reward_norm)` dedup은 구현하지 않음.

## 구현 요약

### 작업 2 — `parse_by_date` 파워업 위크 흡수

수정 파일:
- `src/parse.py`
  - `WEEK_HEADER_RE`, `INLINE_DAILY_RE`, `INLINE_REWARD_SPLIT_RE` 추가.
  - `parse_by_date()`에서 일반 날짜 헤더보다 먼저 주간 배너와 인라인 일별 보상을 처리.
  - 주간 배너는 active context만 저장하고 행을 emit하지 않음.
  - 인라인 일별 보상은 `,\s+(?=[^\d])`로 분리하고 기존 trailing splitter를 적용.
- `tests/test_parse.py`
  - 주간 배너 context 보존, 인라인 8행 정답표, 01.14 콤마 split, 기존 by_date 회귀 테스트 추가.

Claude 검토 포인트:
- 주간 배너가 직전 빈 `current`를 `finish_current()`로 닫는 동작이 기존 spine 의미와 충돌하지 않는지.
- 인라인 일별 라인이 active weekly context 없이 등장할 경우 `event_context=None`, `is_major_event=False`로 emit하는 것이 허용 가능한지.

### 작업 1 — `src/normalize.py`

수정 파일:
- `src/normalize.py`
  - `normalize_reward(reward_raw) -> str | None`
  - `categorize(reward_norm) -> str`
  - `extract_magnitude(reward_raw) -> str | None`
  - Phase 4 매핑표와 별칭 규칙 구현.
  - 카테고리는 `강화/성장/사냥효율/수집기타`만 반환. 미정의 norm은 `미분류`.
- `tests/test_normalize.py`
  - 대표 보상 매핑, 분리 결정, 별칭, no-special category, magnitude, 전체 보상 커버리지 테스트 추가.
  - `data/interim/reward_inventory.csv`가 있으면 사용하고, 없으면 raw by_date를 파싱해 커버리지 테스트를 수행.

Claude 검토 포인트:
- substring 규칙 우선순위가 새 원문 변형에 대해 과매칭하지 않는지.
- `미라클타임`을 `강화`, `코디/헤어/펫타임`을 `수집기타`로 둔 결정이 decision-1 의도와 맞는지.

### 작업 3 — `02_parse_clean.ipynb` 통합

수정 파일:
- `notebooks/02_parse_clean.ipynb`
  - `is_special` 입력을 `reward_raw`, `reward_trailing`, `event_context`로 확장.
  - `reward_norm`, `category`, `reward_magnitude` 추가.
  - `data/processed/tidy_rewards.csv` 저장.
  - Phase 4 무결성 출력 셀 추가.
- `data/processed/tidy_rewards.csv`
  - 신규 산출.
- `data_dictionary.md`
  - 신규 컬럼 정의, Phase 4 결정 4건, 별칭 매핑 근거 문서화.

Claude 검토 포인트:
- Work Packet 내 “기존 컬럼 유지”와 “최종 컬럼 순서”가 충돌해 `reward_trailing`을 최종 CSV에 유지했음.
- `notebooks/03_crossval.ipynb`는 `reward_inventory.csv` 재생성을 위해 실행했으며 코드 변경 의도는 없음.

## 검증 결과

### pytest

```text
python -m pytest -q
........................                                                 [100%]
24 passed in 0.61s
```

### 노트북

```text
jupyter nbconvert --to notebook --execute notebooks/02_parse_clean.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/02_parse_clean.ipynb to notebook
[NbConvertApp] Writing 29759 bytes to notebooks\02_parse_clean.ipynb
```

```text
jupyter nbconvert --to notebook --execute notebooks/03_crossval.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/03_crossval.ipynb to notebook
[NbConvertApp] Writing 27326 bytes to notebooks\03_crossval.ipynb
```

`01_collect.ipynb`는 `data/raw/` 불변 제약 때문에 실행하지 않음.

### 3-C 무결성 출력 원문

```text
total rows: 1160
reward_norm missing rows: 42
no_event_week rows: 30
unmapped reward_raw rows: 0
category counts:
category
강화      357
성장      337
사냥효율    234
수집기타    190
NaN      42
Name: count, dtype: int64
special category rows: 0
uncategorized rows: 0
duplicate (date, reward_norm) pair count: 56
duplicate (date, reward_norm) row count: 117
      date reward_norm
2017-03-12        돌발미션
2017-03-26     룬_경험치버프
2017-04-09          버닝
2017-06-25        돌발미션
2017-07-02     룬_경험치버프
2017-07-02          버닝
2017-09-03        돌발미션
2017-11-12        돌발미션
2017-12-10      몬스터컬렉션
2018-04-01         우르스
2018-04-08       파티퀘스트
2018-04-15        돌발미션
2018-04-15      몬스터컬렉션
2018-10-21      몬스터컬렉션
2018-10-28         우르스
2018-11-25        돌발미션
2018-12-23   몬스터파크_경험치
2019-04-07      몬스터컬렉션
2019-07-07        돌발미션
2019-10-20      몬스터컬렉션
2019-12-01      몬스터컬렉션
2020-04-12      몬스터컬렉션
2020-10-04      몬스터컬렉션
2020-11-15      몬스터컬렉션
2021-03-14      몬스터컬렉션
2021-08-08      몬스터컬렉션
2021-09-26      몬스터컬렉션
2021-10-17      몬스터컬렉션
2021-12-12      몬스터컬렉션
2022-03-27      몬스터컬렉션
2022-05-29      몬스터컬렉션
2022-09-18     선물_기타지급
2022-10-23      몬스터컬렉션
2022-11-27      몬스터컬렉션
2023-03-12      몬스터컬렉션
2023-06-04      몬스터컬렉션
2023-09-17      몬스터컬렉션
2023-10-15      몬스터컬렉션
2023-11-19      몬스터컬렉션
2023-12-10      몬스터컬렉션
2024-03-10      몬스터컬렉션
2024-06-02      몬스터컬렉션
2024-08-04      몬스터컬렉션
2024-10-06      몬스터컬렉션
2024-12-15      몬스터컬렉션
2025-01-12      몬스터컬렉션
2025-04-13      몬스터컬렉션
2025-05-11      몬스터컬렉션
2025-06-15      몬스터컬렉션
2025-07-06      몬스터컬렉션
2025-08-10      몬스터컬렉션
2025-11-09      몬스터컬렉션
2026-01-11      몬스터컬렉션
2026-01-25   솔에르다_접속지급
2026-02-08   솔에르다_접속지급
2026-02-22      몬스터컬렉션
unique reward_norm count: 48
powerup week rows: 8
      date                          reward_raw    reward_trailing reward_norm category  is_special
2023-01-12        10성 이하에서 스타포스 강화 성공 시 1+1 강화                NaN  스타포스_1+1강화       강화       False
2023-01-13          소울 조각 사용 시 위대한 소울 획득 확률 5배                NaN    위대한소울_확률     수집기타       False
2023-01-14 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%      (샤이닝 스타포스 타임)   스타포스_성공확률       강화        True
2023-01-14                   스타포스 강화 비용 30% 할인      (샤이닝 스타포스 타임)   스타포스_비용할인       강화        True
2023-01-15                              미라클 타임 (오전 8시~오후 11시 30분)       미라클타임       강화        True
2023-01-16                 주문의 흔적 강화 비용 50% 할인                NaN  주문의흔적_비용할인       강화       False
2023-01-17                  어빌리티 재설정 비용 50% 할인                NaN  어빌리티_재설정할인       강화       False
2023-01-18                   스타포스 강화 비용 30% 할인                NaN   스타포스_비용할인       강화       False
date min: 2017-03-12
date max: 2026-08-30
non-sunday date count: 7
non-sunday dates: ['2023-01-12', '2023-01-13', '2023-01-14', '2023-01-16', '2023-01-17', '2023-01-18', '2024-04-01']
```

## 데이터 상태

- 산출 경로: `data/processed/tidy_rewards.csv`
- 파일 크기: 167040 bytes
- 행 수: 1160
- 컬럼: `date`, `reward_raw`, `reward_trailing`, `reward_norm`, `category`, `reward_magnitude`, `event_context`, `is_major_event`, `is_special`, `time_limited`, `is_future`, `no_event_week`
- 고유 `reward_norm` 개수: 48
- `(date, reward_norm)` 중복: pair 56개, row 117개
- 결측:

```text
date                   0
reward_raw            42
reward_trailing     1055
reward_norm           42
category              42
reward_magnitude     122
event_context         26
is_major_event         0
is_special             0
time_limited        1140
is_future              0
no_event_week          0
```

`reward_raw/reward_norm/category` 결측 42건 구성:

```text
is_future  no_event_week
False      True             30
True       False            12
```

미래 빈 블록 12건:

```text
      date  is_future  no_event_week event_context
2026-06-14       True          False       메이플 어택!
2026-06-21       True          False           NaN
2026-06-28       True          False           NaN
2026-07-05       True          False           NaN
2026-07-12       True          False           NaN
2026-07-19       True          False           NaN
2026-07-26       True          False           NaN
2026-08-02       True          False           NaN
2026-08-09       True          False           NaN
2026-08-16       True          False           NaN
2026-08-23       True          False           NaN
2026-08-30       True          False           NaN
```

## Claude 리뷰 요청

### Critical

- `01_collect.ipynb` 실행 요구와 `data/raw/` 절대 수정·재크롤 금지 제약이 충돌한다. `01_collect.ipynb`는 `collect_main(str(raw_dir))`를 호출하므로 이번 구현에서는 실행하지 않았다. Phase 4 판정 시 01 실행을 요구할지, raw 불변을 우선할지 결정 필요.
- Work Packet 3-C는 `reward_norm` 결측 수가 `no_event_week` 30행과 일치해야 한다고 적었지만, 현재 기존 Phase 3 의미를 유지한 미래 빈 블록 12행 때문에 결측은 42행이다. 범위 밖 변경을 피하려고 future empty row 처리는 건드리지 않았다.

### Major

- Work Packet의 “기존 컬럼 유지”와 “최종 컬럼 순서”가 충돌한다. 최종 CSV에는 기존 컬럼 유지 원칙에 따라 `reward_trailing`을 포함했다.
- `(date, reward_norm)` 중복 56 pair / 117 row가 존재한다. 사양대로 제거하지 않고 리포트만 했다.
- `notebooks/03_crossval.ipynb`는 `reward_inventory.csv` 재생성을 위해 실행되어 output diff가 생겼다. 코드 의도 변경은 없다.

### Minor

- `jupyter nbconvert` 실행 시 Windows/ZMQ 경고와 notebook cell id 경고가 출력됐지만 실행은 완료됐다.
- `test_coverage_all_rewards`는 `data/interim/reward_inventory.csv`가 없을 경우 raw by_date fallback으로 커버리지를 계산한다. gitignored interim 의존으로 테스트가 깨지는 것을 피하기 위한 보강이다.

### 특이 질문

- 미래 빈 블록 12행을 `tidy_rewards.csv`에 유지할지, processed 산출에서는 제외할지, 별도 상태 컬럼으로 분리할지 다음 packet에서 결정이 필요하다.
- 파워업 위크 흡수 후 총 행 수가 1160으로 유지된다. 파워업 8행이 추가되는 대신 기존에 잘못 생성되던 인라인 날짜 빈 행 8개가 제거되어 순증은 0이다. 이 해석으로 충분한지 확인 필요.
