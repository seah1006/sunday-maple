# Claude Handoff — Phase 6

## 작업 범위

- Phase 6 구현·셀프검증만 수행.
- `data/raw/`는 수정하지 않음. `git status --short data/raw` 출력 없음.
- 기존 tidy 1160행은 유지하고 `is_discontinued` 컬럼만 추가.
- `src/parse.py`, `src/normalize.py` 공개 시그니처는 변경하지 않음. `src/features.py`는 함수 추가만 수행.
- `(date, reward_norm)` 중복 제거는 수행하지 않음.
- `CLAUDE.md`는 수정하지 않고 `data_dictionary.md`에 정정·매핑을 기록.

## 구현 요약

### 작업 1 — is_discontinued 병합

수정 파일:
- `src/features.py`
  - `merge_is_discontinued(tidy, parsed_by_type) -> pd.Series` 추가.
  - exact `reward_raw` 기준으로 by_type `is_discontinued`를 tidy index에 정렬해 반환.
  - `reward_raw` null 행은 `pd.NA`.
  - by_type에 없는 non-null raw는 `False` 기본값.
  - 같은 by_type `reward_raw`에 True/False 혼재가 있으면 `ValueError`.
- `tests/test_features.py`
  - 단종 raw=True, 비단종=False, raw null=NA, by_type 누락=False 테스트 추가.
  - by_type 동일 raw 혼재 에러 테스트 추가.
- `notebooks/02_parse_clean.ipynb`
  - `merge_is_discontinued()` 통합.
  - `tidy_rewards.csv`에 `is_discontinued` 컬럼 추가.
  - by_type 단종 source 71개 확인, 동일 raw 내 혼재 0 assert, 매칭 실패 목록 출력 추가.
- `data/processed/tidy_rewards.csv`
  - 1160행 유지, 14컬럼으로 확장.

Claude 검토 포인트:
- Work Packet은 exact raw 병합과 by_type 미매칭 raw=False를 지시하면서 동시에 tidy True 고유 raw=71을 완료 기준으로 둔다. 실제 exact raw 병합 결과는 tidy True 고유 raw=60이다. by_type 단종 source는 71개이며, 차이 11개는 by_date에서 괄호 접미 제거 등 다른 exact raw로 등장한다. 임의 alias 보정은 하지 않았다.

### 작업 2 — 스키마 문서화

수정 파일:
- `data_dictionary.md`
  - `is_discontinued` 정의 추가.
  - CLAUDE.md 목표 스키마 대비 tidy 컬럼 매핑표 추가.
  - Phase 5 특이질문 2건 종결 기록:
    - `cycle_days > 1500`은 장기휴면/단종 후 부활 정상값으로 원값 유지.
    - raw-cycle missing 67건은 출력-only 유지.
  - Phase 6 exact raw 병합 결과 및 71→60 차이 기록.

Claude 검토 포인트:
- `is_discontinued`를 norm 단위로 보정하지 않고 raw exact 병합만 적용한 것이 decision-1에 맞는지 확인 필요.

## 검증 결과

### pytest

```text
python -m pytest -q
..............................                                           [100%]
30 passed in 0.64s
```

### Notebook 02 실행

```text
jupyter nbconvert --to notebook --execute notebooks/02_parse_clean.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/02_parse_clean.ipynb to notebook
[NbConvertApp] Writing 38259 bytes to notebooks\02_parse_clean.ipynb
```

### Notebook 02 무결성 출력 원문

```text
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
is_discontinued counts:
is_discontinued
False    832
True     286
<NA>      42
by_type discontinued unique reward_raw: 71
tidy discontinued unique reward_raw: 60
by_type mixed is_discontinued reward_raw: 0
tidy mixed is_discontinued reward_raw: 0
missing discontinued reward_raw from tidy: ['강력한 환생의 불꽃 5개 사용 시마다 1개 지급(월드 당 최대 10개)', '돌발미션 일일 클리어 가능 횟수 2배(3회→6회)', '돌발미션 일일 클리어 가능 횟수 3배(3회→9회)', '돌발미션 일일 클리어 가능 횟수 5배(3회→15회)', '룬 경험치 버프 지속시간 2배(3분→6분)', '보스파티 결성 버프 효과 증가(10%→30%)', '사냥 시 소환되는 엘리트 몬스터 수 증가(1마리→2마리)', '엘리트 몬스터 마일리지 꾸러미 일일 사용 가능 횟수 4배(5회→20회)', '영원한 환생의 불꽃 5개 사용 시마다 1개 지급(월드 당 최대 10개)', '월드 통합 파티퀘스트 일일 입장 횟수 2배(5회→10회)', '월드 통합 파티퀘스트 파티 포인트 획득량 5배(10→50)']
extra discontinued reward_raw in tidy: []
by_type unmatched reward_raw rows filled False: 59
by_type unmatched reward_raw unique count: 14
by_type unmatched reward_raw values: ['강력한 환생의 불꽃 5개 사용 시마다 1개 지급', '데미지 스킨 선택 지급(샤방샤방/샤방샤방(Ver.2)/샤방샤방(Ver.3))', '돌발미션 일일 클리어 가능 횟수 2배', '돌발미션 일일 클리어 가능 횟수 3배', '돌발미션 일일 클리어 가능 횟수 5배', '룬 경험치 버프 지속시간 2배', '몬스터 사냥 시 경험치 3배 혜택', '보스파티 결성 버프 효과 증가', '사냥 시 소환되는 엘리트 몬스터 수 증가', '엘리트 몬스터 마일리지 꾸러미 일일 사용 가능 횟수 4배', '영원한 환생의 불꽃 5개 사용 시마다 1개 지급', '월드 통합 파티퀘스트 일일 입장 횟수 2배', '월드 통합 파티퀘스트 파티 포인트 획득량 5배', '폴로와 프리토, 에스페시아의 현상금 사냥 경험치 2배']
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
      date                          reward_raw    reward_trailing reward_norm category  is_special  is_discontinued  cycle_days
2023-01-12        10성 이하에서 스타포스 강화 성공 시 1+1 강화                NaN  스타포스_1+1강화       강화       False            False          60
2023-01-13          소울 조각 사용 시 위대한 소울 획득 확률 5배                NaN    위대한소울_확률     수집기타       False            False          54
2023-01-14 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%      (샤이닝 스타포스 타임)   스타포스_성공확률       강화        True            False          27
2023-01-14                   스타포스 강화 비용 30% 할인      (샤이닝 스타포스 타임)   스타포스_비용할인       강화        True            False          90
2023-01-15                              미라클 타임 (오전 8시~오후 11시 30분)       미라클타임       강화        True            False         182
2023-01-16                 주문의 흔적 강화 비용 50% 할인                NaN  주문의흔적_비용할인       강화       False            False          29
2023-01-17                  어빌리티 재설정 비용 50% 할인                NaN  어빌리티_재설정할인       강화       False            False          30
2023-01-18                   스타포스 강화 비용 30% 할인                NaN   스타포스_비용할인       강화       False            False           4
date min: 2017-03-12
date max: 2026-08-30
non-sunday date count: 7
non-sunday dates: ['2023-01-12', '2023-01-13', '2023-01-14', '2023-01-16', '2023-01-17', '2023-01-18', '2024-04-01']
```

## 데이터 상태

- 산출 경로: `C:\Users\my\Desktop\프로젝트\sunday-maple\data\processed\tidy_rewards.csv`
- 파일 크기: 176912 bytes
- 행 수: 1160
- 컬럼 수: 14
- 컬럼: `date`, `reward_raw`, `reward_trailing`, `reward_norm`, `category`, `reward_magnitude`, `event_context`, `is_major_event`, `is_special`, `time_limited`, `is_discontinued`, `is_future`, `no_event_week`, `cycle_days`

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
is_discontinued       42
is_future              0
no_event_week          0
cycle_days            97
```

`is_discontinued` 분포:

```text
False    832
True     286
NaN       42
```

매칭 상태:
- by_type discontinued unique `reward_raw`: 71
- tidy discontinued unique `reward_raw`: 60
- 동일 tidy raw 내 `is_discontinued` 혼재: 0
- by_type unmatched reward_raw rows filled False: 59
- by_type unmatched reward_raw unique count: 14
- unmatched list:
  - `강력한 환생의 불꽃 5개 사용 시마다 1개 지급`
  - `데미지 스킨 선택 지급(샤방샤방/샤방샤방(Ver.2)/샤방샤방(Ver.3))`
  - `돌발미션 일일 클리어 가능 횟수 2배`
  - `돌발미션 일일 클리어 가능 횟수 3배`
  - `돌발미션 일일 클리어 가능 횟수 5배`
  - `룬 경험치 버프 지속시간 2배`
  - `몬스터 사냥 시 경험치 3배 혜택`
  - `보스파티 결성 버프 효과 증가`
  - `사냥 시 소환되는 엘리트 몬스터 수 증가`
  - `엘리트 몬스터 마일리지 꾸러미 일일 사용 가능 횟수 4배`
  - `영원한 환생의 불꽃 5개 사용 시마다 1개 지급`
  - `월드 통합 파티퀘스트 일일 입장 횟수 2배`
  - `월드 통합 파티퀘스트 파티 포인트 획득량 5배`
  - `폴로와 프리토, 에스페시아의 현상금 사냥 경험치 2배`

## Claude 리뷰 요청

### Critical

- Work Packet의 “exact `reward_raw` 병합 + by_type에 없는 raw는 False”와 “tidy 단종 True 고유 raw=71” 완료 기준이 실제 데이터에서 동시에 만족되지 않는다. exact raw 병합 결과 tidy True 고유 raw는 60이다. 임의 alias/정규화 기반 보정을 적용하지 않고 차이를 출력했다. 판정 또는 다음 Phase 정책 결정 필요.

### Major

- by_type 단종 11개는 tidy exact raw와 다르다. 예: by_type `강력한 환생의 불꽃 5개 사용 시마다 1개 지급(월드 당 최대 10개)` vs tidy `강력한 환생의 불꽃 5개 사용 시마다 1개 지급`. 이 차이를 단종 병합에서 alias로 보정할지 결정 필요.
- unmatched non-null tidy raw 14개/59행은 현재 `False`로 채웠다. 일부는 by_type 단종 문자열의 정제 변형이므로 false negative 가능성이 있다.

### Minor

- `jupyter nbconvert` 실행 시 Windows/ZMQ 경고가 출력됐지만 실행은 완료됐다.
- `data_dictionary.md`에는 목표 스키마 완성 매핑을 추가했지만, 위 Critical 때문에 `is_discontinued`의 exact raw 정책 한계도 같이 기록했다.

### 특이 질문

- `is_discontinued`를 strict raw exact 속성으로 유지할지, Phase 7에서 정제/alias 매핑을 적용해 단종 True 고유 raw 71 목표를 맞출지 결정 필요.
