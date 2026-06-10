# Claude Handoff — Phase 5

## 작업 범위

- Phase 5 구현·셀프검증만 수행.
- `data/raw/`는 수정하지 않음. `git status --short data/raw` 출력 없음.
- 범위 밖으로 지정된 `is_discontinued` 병합, EDA, 모델링, `(date, reward_norm)` dedup은 수행하지 않음.
- `src/parse.py`, `src/normalize.py` 공개 시그니처는 변경하지 않음.

## 구현 요약

### 작업 1 — cycle_days 피처

수정 파일:
- `src/features.py`
  - `compute_cycle_days(tidy: pd.DataFrame) -> pd.Series` 신규 추가.
  - 고유 `(date, reward_norm)` 기준으로 norm별 `date.diff().dt.days` 산출 후 원본 index에 merge.
  - null norm 행은 `pd.NA`, 같은 날 같은 norm 묶음은 같은 값을 공유.
- `tests/test_features.py`
  - basic, same-day bundle, null norm, first occurrence NaN 테스트 추가.
- `notebooks/02_parse_clean.ipynb`
  - `compute_cycle_days()`를 통합해 `tidy_rewards.csv`에 `cycle_days` 컬럼 append.
  - by_type `stated_cycle_days`와 tidy raw-cycle 대조 출력 추가. 저장은 하지 않음.
- `data/processed/tidy_rewards.csv`
  - 기존 1160행 유지, `cycle_days` 컬럼 추가.

Claude 검토 포인트:
- `cycle_days`는 raw가 아니라 norm 단위 분석 피처다. raw 단위 gap은 by_type 대조 출력으로만 사용했다.
- 1500일 초과 cycle 2건은 출력만 했고 정책 판단은 하지 않았다.

### 작업 2 — 무결성 기준 정리

수정 파일:
- `notebooks/02_parse_clean.ipynb`
  - `(date, reward_raw)` 중복 0 assert.
  - `reward_norm` 결측 = `no_event_week` + future empty assert.
  - `cycle_days` 음수 0 assert.
  - `(date, reward_norm)` 중복은 상위 norm까지 출력만 하고 제거하지 않음.
- `data_dictionary.md`
  - `cycle_days` 정의 추가.
  - decision-1 기록: 관측 단위 = `reward_raw`, 무결성 키 = `(date, reward_raw)`, norm 중복 허용.
  - decision-2 기록: 미래 빈 블록 12행 유지.
  - `CLAUDE.md`의 `(date, reward_norm)` 중복 기준은 Phase 5부터 `(date, reward_raw)`로 재해석한다고 정정 기록. `CLAUDE.md` 자체는 수정하지 않음.

Claude 검토 포인트:
- `reward_norm`은 라벨이므로 `(date, reward_norm)` 56 pair 중복을 허용하는 문서화가 충분한지.

### 작업 3 — 01 재현성 문서화

수정 파일:
- `notebooks/01_collect.ipynb`
  - 마크다운 셀만 수정.
  - `collect_main()`/`save_raw_html()`의 skip-if-exists 동작과 raw 재실행 안전성을 문서화.

Claude 검토 포인트:
- 코드/원본은 변경하지 않았다.

### 작업 4 — 03 교차검증 재실행

수정 파일:
- `notebooks/03_crossval.ipynb`
  - 재실행 output 갱신.
  - 코드 의도 변경 없음.

교차검증 변화:
- Phase 3 handoff: exact count match rate `0.6637168141592921` = 75/113 matched, 38 mismatched.
- Phase 5 재실행: exact count match rate `0.7256637168141593` = 82/113 matched, 31 mismatched.
- 파워업 위크 8행 편입 후 exact count matched rewards가 7개 증가했고 mismatched rewards가 7개 감소했다.

## 검증 결과

### pytest

```text
python -m pytest -q
............................                                             [100%]
28 passed in 0.64s
```

### Notebook 02 실행

```text
jupyter nbconvert --to notebook --execute notebooks/02_parse_clean.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/02_parse_clean.ipynb to notebook
[NbConvertApp] Writing 34088 bytes to notebooks\02_parse_clean.ipynb
```

### Notebook 02 무결성 출력 원문

```text
parsed_by_type.csv: exists=True bytes=84712
parsed_by_date.csv: exists=True bytes=110137
tidy_prenorm.csv: exists=True bytes=125675
tidy_rewards.csv: exists=True bytes=170432

parsed_by_type rows: 1140
parsed_by_date rows: 1160
tidy_prenorm rows: 1160
tidy_prenorm unique dates: 501
tidy_prenorm min date: 2017-03-12
tidy_prenorm max date: 2026-08-30
is_future rows: 12
future min date: 2026-06-14
no_event_week rows: 30
is_major_event ratio: 0.7293103448275862
parsed_by_type discontinued unique rewards: 71

total rows: 1160
date_reward_raw duplicate rows: 0
reward_norm missing rows: 42
no_event_week rows: 30
future empty rows: 12
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
top bundled reward_norm pair counts:
reward_norm
몬스터컬렉션       38
돌발미션          7
룬_경험치버프       2
버닝            2
솔에르다_접속지급     2
우르스           2
몬스터파크_경험치     1
선물_기타지급       1
파티퀘스트         1
cycle_days non-null rows: 1063
cycle_days negative rows: 0
cycle_days > 1500 rows: 2
      date             reward_raw reward_norm  cycle_days
2023-07-09           테라 버닝 부스터 지급          버닝        2030
2024-12-15 사냥 시 소환되는 엘리트 몬스터 수 증가   엘리트몬스터_증가        1911
raw cycle mismatch rows: 0
raw cycle missing computed rows: 67
                     reward_raw       date  stated_cycle_days  computed_raw_cycle_days
                   데미지 스킨 선택 지급 2019-06-16              210.0                     <NA>
    돌발미션 일일 클리어 가능 횟수 2배(3회→6회) 2017-06-25              105.0                     <NA>
    돌발미션 일일 클리어 가능 횟수 2배(3회→6회) 2017-09-03               70.0                     <NA>
    돌발미션 일일 클리어 가능 횟수 2배(3회→6회) 2017-11-12               70.0                     <NA>
    돌발미션 일일 클리어 가능 횟수 3배(3회→9회) 2019-07-07              224.0                     <NA>
        룬 경험치 버프 지속시간 2배(3분→6분) 2017-07-02               98.0                     <NA>
        룬 경험치 버프 지속시간 2배(3분→6분) 2017-08-27               56.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2017-09-03              133.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2017-11-19               77.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2018-03-04              105.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2018-12-02              273.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2019-04-07              126.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2019-06-23               77.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2019-08-11               49.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리) 2019-09-22               42.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리) 2025-01-12               28.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리) 2025-04-13               91.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리) 2025-05-11               28.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리) 2025-06-15               35.0                     <NA>
사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→3마리) 2025-07-06               21.0                     <NA>
unique reward_norm count: 48
powerup week rows: 8
      date                          reward_raw    reward_trailing reward_norm category  is_special  cycle_days
2023-01-12        10성 이하에서 스타포스 강화 성공 시 1+1 강화                NaN  스타포스_1+1강화       강화       False          60
2023-01-13          소울 조각 사용 시 위대한 소울 획득 확률 5배                NaN    위대한소울_확률     수집기타       False          54
2023-01-14 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%      (샤이닝 스타포스 타임)   스타포스_성공확률       강화        True          27
2023-01-14                   스타포스 강화 비용 30% 할인      (샤이닝 스타포스 타임)   스타포스_비용할인       강화        True          90
2023-01-15                              미라클 타임 (오전 8시~오후 11시 30분)       미라클타임       강화        True         182
2023-01-16                 주문의 흔적 강화 비용 50% 할인                NaN  주문의흔적_비용할인       강화       False          29
2023-01-17                  어빌리티 재설정 비용 50% 할인                NaN  어빌리티_재설정할인       강화       False          30
2023-01-18                   스타포스 강화 비용 30% 할인                NaN   스타포스_비용할인       강화       False           4
date min: 2017-03-12
date max: 2026-08-30
non-sunday date count: 7
non-sunday dates: ['2023-01-12', '2023-01-13', '2023-01-14', '2023-01-16', '2023-01-17', '2023-01-18', '2024-04-01']
```

### Notebook 03 실행 및 출력

```text
jupyter nbconvert --to notebook --execute notebooks/03_crossval.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/03_crossval.ipynb to notebook
[NbConvertApp] Writing 27326 bytes to notebooks\03_crossval.ipynb
```

```text
parsed_by_type rows: 1140
parsed_by_date rows: 1160
tidy_prenorm rows: 1160

cycle checked rows: 1041
cycle mismatch rows: 0

exact reward unique total: 113
exact count matched rewards: 82
exact count mismatched rewards: 31
exact count match rate: 0.7256637168141593

reward_inventory rows: 113
reward_inventory discontinued rewards: 71
reward_inventory bytes: 9603

discontinued unique rewards in parsed_by_type: 71
no_event_week rows: 30
no_event_week future rows: 0
future empty blocks: 12
past empty blocks without sentinel: 0
date min: 2017-03-12
date max: 2026-08-30
unique dates: 501
```

## 데이터 상태

- 산출 경로: `C:\Users\my\Desktop\프로젝트\sunday-maple\data\processed\tidy_rewards.csv`
- 파일 크기: 170432 bytes
- 행 수: 1160
- 컬럼 수: 13
- 컬럼: `date`, `reward_raw`, `reward_trailing`, `reward_norm`, `category`, `reward_magnitude`, `event_context`, `is_major_event`, `is_special`, `time_limited`, `is_future`, `no_event_week`, `cycle_days`
- 고유 `reward_norm` 개수: 48
- `(date, reward_raw)` 중복: 0
- `(date, reward_norm)` 중복: pair 56개, row 117개
- `cycle_days` non-null: 1063
- `cycle_days` null: 97
- `cycle_days` 음수: 0
- `cycle_days` > 1500: 2

결측:

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
cycle_days            97
```

`cycle_days` 분포:

```text
count    1063.000000
mean       65.232361
std       109.705682
min         4.000000
25%        28.000000
50%        42.000000
75%        70.000000
max      2030.000000
```

## Claude 리뷰 요청

### Critical

- 없음.

### Major

- `raw cycle missing computed rows`가 67건이다. by_type에는 stated cycle이 있으나 by_date raw 기준으로 같은 문자열의 이전 등장이 계산되지 않은 케이스다. 명칭변경·정확 문자열 차이·by_date/by_type 범위 차이로 보이며 저장하지 않고 출력만 했다.
- `cycle_days > 1500` 2건: `버닝` 2030일, `엘리트몬스터_증가` 1911일. 단종 후 부활/명칭 통합의 결과일 수 있어 정책 판단을 요청한다.

### Minor

- `jupyter nbconvert` 실행 시 Windows/ZMQ 경고가 출력됐지만 실행은 완료됐다.
- `notebooks/01_collect.ipynb`는 마크다운만 수정했다. raw idempotency 검증 근거는 `src/collect.py`의 skip-if-exists 구현과 `git status --short data/raw` 무출력이다.

### 특이 질문

- raw-cycle 대조에서 missing computed 67건을 다음 Phase에서 별도 교차검증 이슈로 다룰지, 현재처럼 출력-only로 유지할지 결정 필요.
- 1500일 초과 `cycle_days`를 이상치로 별도 플래그 처리할지, 현 `cycle_days` 원값 유지로 충분한지 결정 필요.
