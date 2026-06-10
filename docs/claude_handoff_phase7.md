# Claude Handoff — Phase 7

## 작업 범위

- Phase 7 구현·셀프검증만 수행.
- `data/raw/`는 수정하지 않음. `git status --short data/raw` 출력 없음.
- `tidy_rewards.csv` 1160행과 기존 컬럼을 유지하고 `is_discontinued` 값만 정정.
- `src/parse.py`, `src/normalize.py`, `src/features.py` 공개 시그니처는 유지.
- 노트북 01·02·03의 마크다운과 출력 라벨을 한글로 수정. 코드 식별자, 컬럼명, 원문 데이터 값은 유지.

## 구현 요약

### 작업 1 — is_discontinued 정확성 수정

수정 파일:
- `src/features.py`
  - `merge_is_discontinued(tidy, parsed_by_type)` 로직 수정.
  - by_type 단종 원문 집합에 대해 `reward_raw` 또는 `reward_raw + reward_trailing` 중 하나라도 매칭되면 True.
  - `reward_raw` null 행은 NA, 그 외는 False.
- `tests/test_features.py`
  - body 매칭: `데미지 스킨 선택 지급` True.
  - 전체 문자열 매칭: `돌발미션 일일 클리어 가능 횟수 2배` + `(3회→6회)` True.
  - 같은 raw의 trailing별 분기: `사냥 시 소환되는 엘리트 몬스터 수 증가` `(1마리→2마리)` True, `(1마리→3마리)` False.
  - null/active 경계 테스트 추가.
- `notebooks/02_parse_clean.ipynb`
  - 단종 무결성 출력 수정.
  - by_type 단종 원문 수 71, 매칭된 단종 원문 수 71 assert.
  - 동일 raw 혼재 목록이 `사냥 시 소환되는 엘리트 몬스터 수 증가` 1건인지 assert.
- `data/processed/tidy_rewards.csv`
  - 단종 11종을 True로 정정.
  - True 행 수 286 → 311.

Claude 검토 포인트:
- Work Packet은 “단종 True `(reward_raw, reward_trailing)` 조합 수 = 71”을 요구했으나, 수정 규칙을 그대로 적용하면 조합 수는 72다. 이유는 by_type 단종 원문 `경험치 2배`가 body 매칭으로 tidy의 시간대 접미 2개 조합에 모두 적용되기 때문이다. by_type 단종 원문 매칭 수는 71로 정확히 맞다.

### 작업 2 — 노트북 한글화

수정 파일:
- `notebooks/01_collect.ipynb`
  - 마크다운 전면 한글화.
  - print 출력 라벨 한글화.
- `notebooks/02_parse_clean.ipynb`
  - 마크다운 전면 한글화.
  - 깨진 `## ?? ??` 셀을 `## 저장 결과 요약`으로 복구.
  - print 출력 라벨 한글화.
- `notebooks/03_crossval.ipynb`
  - 마크다운 전면 한글화.
  - print 출력 라벨 한글화.
- `data_dictionary.md`
  - `is_discontinued` 정의를 원문 전체 문자열 단위로 정정.
  - 엘리트 몬스터 수 증가의 정상 혼재 사례 문서화.

Claude 검토 포인트:
- 파일명, 컬럼명, 변수명, 원문 데이터 값은 그대로 유지했다. 따라서 출력 표의 컬럼명(`reward_raw`, `cycle_days` 등)과 원문 내 `Like`, `?` 등은 남아 있다.

## 검증 결과

### pytest

```text
python -m pytest -q
.................................                                        [100%]
33 passed in 0.65s
```

### 노트북 재실행

```text
jupyter nbconvert --to notebook --execute notebooks/01_collect.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/01_collect.ipynb to notebook
[NbConvertApp] Writing 7738 bytes to notebooks\01_collect.ipynb
```

```text
jupyter nbconvert --to notebook --execute notebooks/02_parse_clean.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/02_parse_clean.ipynb to notebook
[NbConvertApp] Writing 36711 bytes to notebooks\02_parse_clean.ipynb
```

```text
jupyter nbconvert --to notebook --execute notebooks/03_crossval.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/03_crossval.ipynb to notebook
[NbConvertApp] Writing 26869 bytes to notebooks\03_crossval.ipynb
```

01 실행 중 `Assertion failed: Connection reset by peer [10054]` 메시지가 한 번 출력됐지만 프로세스 종료 코드는 0이었고 노트북은 저장됐다. `data/raw/` 변경은 없었다.

### 한글화 검사

```text
노트북 비코드 텍스트 검사 이슈 수: 0
```

검사 대상:
- 01·02·03 마크다운 셀의 `?` 및 영문 문장 후보
- 01·02·03 코드 셀의 깨진 `??` 출력 라벨 후보

### 02 무결성 출력 원문

```text
전체 행 수: 1160
date와 reward_raw 중복 행 수: 0
reward_norm 결측 행 수: 42
no_event_week 행 수: 30
미래 빈 블록 행 수: 12
미매핑 reward_raw 행 수: 0
카테고리 분포:
category
강화      357
성장      337
사냥효율    234
수집기타    190
NaN      42
Name: count, dtype: int64
스페셜 카테고리 행 수: 0
미분류 카테고리 행 수: 0
date와 reward_norm 중복 조합 수: 56
date와 reward_norm 중복 행 수: 117
상위 묶음 reward_norm 조합 수:
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
cycle_days 비결측 행 수: 1063
cycle_days 음수 행 수: 0
cycle_days 1500일 초과 행 수: 2
      date             reward_raw reward_norm  cycle_days
2023-07-09           테라 버닝 부스터 지급          버닝        2030
2024-12-15 사냥 시 소환되는 엘리트 몬스터 수 증가   엘리트몬스터_증가        1911
is_discontinued 분포:
is_discontinued
False    807
True     311
<NA>      42
by_type 단종 원문 수: 71
매칭된 단종 원문 수: 71
단종 True reward_raw와 reward_trailing 조합 수: 72
단종 원문 매칭 누락 목록: []
단종 원문 초과 매칭 목록: []
동일 reward_raw 안에서 단종 상태가 혼재한 목록: ['사냥 시 소환되는 엘리트 몬스터 수 증가']
예상 밖 혼재 reward_raw 목록: []
누락된 예상 혼재 reward_raw 목록: []
raw 주기 불일치 행 수: 0
raw 주기 계산 누락 행 수: 67
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
고유 reward_norm 수: 48
파워업 위크 행 수: 8
      date                          reward_raw    reward_trailing reward_norm category  is_special  is_discontinued  cycle_days
2023-01-12        10성 이하에서 스타포스 강화 성공 시 1+1 강화                NaN  스타포스_1+1강화       강화       False            False          60
2023-01-13          소울 조각 사용 시 위대한 소울 획득 확률 5배                NaN    위대한소울_확률     수집기타       False            False          54
2023-01-14 스타포스 5, 10, 15성에서 강화 시도 시 성공확률 100%      (샤이닝 스타포스 타임)   스타포스_성공확률       강화        True            False          27
2023-01-14                   스타포스 강화 비용 30% 할인      (샤이닝 스타포스 타임)   스타포스_비용할인       강화        True            False          90
2023-01-15                              미라클 타임 (오전 8시~오후 11시 30분)       미라클타임       강화        True            False         182
2023-01-16                 주문의 흔적 강화 비용 50% 할인                NaN  주문의흔적_비용할인       강화       False            False          29
2023-01-17                  어빌리티 재설정 비용 50% 할인                NaN  어빌리티_재설정할인       강화       False            False          30
2023-01-18                   스타포스 강화 비용 30% 할인                NaN   스타포스_비용할인       강화       False            False           4
최소 날짜: 2017-03-12
최대 날짜: 2026-08-30
일요일이 아닌 날짜 수: 7
일요일이 아닌 날짜 목록: ['2023-01-12', '2023-01-13', '2023-01-14', '2023-01-16', '2023-01-17', '2023-01-18', '2024-04-01']
```

### 03 출력 요약

```text
parsed_by_type 행 수: 1140
parsed_by_date 행 수: 1160
tidy_prenorm 행 수: 1160
주기 검증 대상 행 수: 1041
주기 불일치 행 수: 0
고유 reward_raw 전체 수: 113
등장 횟수 일치 보상 수: 82
등장 횟수 불일치 보상 수: 31
등장 횟수 일치율: 0.7256637168141593
reward_inventory 행 수: 113
reward_inventory 단종 보상 수: 71
reward_inventory 바이트: 9603
parsed_by_type 단종 고유 보상 수: 71
no_event_week 행 수: 30
no_event_week 중 미래 행 수: 0
미래 빈 블록 수: 12
센티넬 없는 과거 빈 블록 수: 0
최소 날짜: 2017-03-12
최대 날짜: 2026-08-30
고유 날짜 수: 501
```

## 데이터 상태

- 산출 경로: `C:\Users\my\Desktop\프로젝트\sunday-maple\data\processed\tidy_rewards.csv`
- 파일 크기: 176887 bytes
- 행 수: 1160
- 컬럼 수: 14
- `is_discontinued` 분포:

```text
False    807
True     311
NaN       42
```

- `is_discontinued=True` 고유 `reward_raw`: 71
- `is_discontinued=True` `(reward_raw, reward_trailing)` 조합: 72
- 단종 원문 매칭 수: 71
- 단종 원문 매칭 누락: 0
- 단종 원문 초과 매칭: 0
- 동일 `reward_raw` 안에서 단종 상태가 혼재한 목록: `['사냥 시 소환되는 엘리트 몬스터 수 증가']`

Phase 7에서 True로 정정된 11개 조합:

```text
                     reward_raw reward_trailing
     강력한 환생의 불꽃 5개 사용 시마다 1개 지급   (월드 당 최대 10개)
           돌발미션 일일 클리어 가능 횟수 2배         (3회→6회)
           돌발미션 일일 클리어 가능 횟수 3배         (3회→9회)
           돌발미션 일일 클리어 가능 횟수 5배        (3회→15회)
               룬 경험치 버프 지속시간 2배         (3분→6분)
               보스파티 결성 버프 효과 증가       (10%→30%)
         사냥 시 소환되는 엘리트 몬스터 수 증가       (1마리→2마리)
엘리트 몬스터 마일리지 꾸러미 일일 사용 가능 횟수 4배        (5회→20회)
     영원한 환생의 불꽃 5개 사용 시마다 1개 지급   (월드 당 최대 10개)
        월드 통합 파티퀘스트 일일 입장 횟수 2배        (5회→10회)
      월드 통합 파티퀘스트 파티 포인트 획득량 5배         (10→50)
```

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

## Claude 리뷰 요청

### Critical

- Work Packet의 “단종 True `(reward_raw, reward_trailing)` 조합 수 = 71”은 구현 규칙과 실제 데이터 기준으로는 72가 된다. by_type 단종 원문 `경험치 2배`가 body 매칭으로 tidy의 `(오전 10시~오후 10시)`와 `(하루 종일)` 두 조합에 모두 True를 부여하기 때문이다. 단종 원문 매칭 수는 71로 정확히 일치한다. 어느 수치를 완료 기준으로 삼을지 판정 필요.

### Major

- 발표자료 한글화에서 파일명, 컬럼명, 변수명, 원문 데이터 값은 유지했다. 출력 표의 pandas 기본 문자열(`Name: count`, `dtype`)과 원문 데이터 안의 `Like`, `?`는 데이터/표현 객체의 일부로 남아 있다.

### Minor

- 01 노트북 실행 중 `Assertion failed: Connection reset by peer [10054]` 메시지가 출력됐지만 종료 코드는 0이었고 raw 변경은 없었다.
- `jupyter nbconvert` 실행 시 Windows/ZMQ 경고가 출력됐지만 01·02·03 모두 실행 완료됐다.

### 특이 질문

- `경험치 2배`처럼 by_type 단종 원문이 body 형태이고 tidy에 여러 시간대 trailing이 존재하는 경우, 조합 수 기준을 72로 정정할지, 별도 집계 기준을 “매칭된 by_type 단종 원문 수 71”로 둘지 결정 필요.
