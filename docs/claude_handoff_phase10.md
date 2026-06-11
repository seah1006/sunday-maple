# Claude Handoff - Phase 10

## 구현 요약

- `src/parse.py`
  - 날짜별 뷰 헤더의 선행 `(요일)` 토큰을 제거한 뒤 소형 이벤트 괄호를 파싱하도록 수정했다.
  - `2024.04.01(월) (유니온 릴레이)` 계열 헤더가 `event_context='유니온 릴레이'`로 저장된다.
- `tests/test_parse.py`
  - `test_by_date_weekday_prefixed_small_event_header`를 추가했다.
- `notebooks/04_eda.ipynb`
  - Q3 단종 마지막 등장 연도 집계를 `groupby('reward_raw')` 기준으로 수정했다.
  - Q3 카테고리별 차트도 고유 `reward_raw` 단위로 정정했다.
  - Q2 히스토그램은 365일 초과 장기 gap을 마지막 구간으로 묶어 표시하고, 원값 유지 주석을 추가했다.
- `notebooks/05_model.ipynb`
  - 모델 로직과 MAE 계산은 그대로 두고 산점도 표시 범위만 420일로 제한했다.
  - 장기 gap 원값이 MAE에는 그대로 반영된다는 주석을 추가했다.
- `data_dictionary.md`
  - `03_crossval.ipynb`, `04_eda.ipynb`, `05_model.ipynb`, `outputs/figures/` 산출물 설명을 추가했다.
  - 비일요일 11행 예외, Q3 집계 단위, `(요일)` 헤더 파싱 결정을 기록했다.

## 검증 결과

- `python -m pytest -q`
  - `34 passed`
  - 경고: `.pytest_cache` 권한 문제로 cache 쓰기 경고 1건. 테스트 결과에는 영향 없음.
- 노트북 커널 재시작 순차 재실행
  - `02_parse_clean.ipynb`: 성공
  - `03_crossval.ipynb`: 성공
  - `04_eda.ipynb`: 성공
  - `05_model.ipynb`: 성공
  - Windows/Python 3.13 환경의 `zmq` selector thread 런타임 경고가 각 실행에서 출력됐지만 실행은 완료됐다.
- Q3 독립 계산
  - 단종 고유 `reward_raw` 마지막 등장 연도 분포:
    - 2017: 11
    - 2018: 21
    - 2019: 9
    - 2020: 5
    - 2021: 2
    - 2022: 10
    - 2023: 4
    - 2024: 8
    - 2025: 1
  - 합계: 71
- 재생성 그림 확인
  - `outputs/figures/q3_last_seen_year.png`
  - `outputs/figures/q3_discontinued_by_category.png`
  - `outputs/figures/q2_cycle_hist.png`
  - `outputs/figures/model_pred_vs_actual.png`

## 데이터 상태

- `data/raw/`는 수정하지 않았다.
- `data/processed/tidy_rewards.csv`
  - 행 수: 1160
  - 컬럼 수: 14
  - 컬럼 목록 변경 없음
  - 재생성 diff는 `event_context` 4행만 변경됐다.
- 변경된 4행
  - 날짜: `2024-04-01`
  - 기존: `월) (유니온 릴레이`
  - 변경: `유니온 릴레이`
  - 해당 보상 4개:
    - `메이플 운영자의 특별한 선물 받기!`
    - `폴로와 프리토, 에스페시아의 현상금 사냥 경험치 2배`
    - `불꽃늑대 퇴장 시 획득하는 경험치 2배`
    - `몬스터 파크 클리어 경험치 추가 250%`

## Claude 리뷰 요청

- Q3 수정 검토
  - `reward_raw` 고유 단위 집계가 Phase 10 요구와 발표 질문 의도에 맞는지 확인해 달라.
  - `q3_last_seen_year.png`의 합계 71과 연도 분포가 기대값과 일치하는지 재확인해 달라.
- 파서 수정 검토
  - `_parse_date_header`에서 선행 `(요일)`만 제거하는 방식이 다른 소형 이벤트 헤더에 부작용이 없는지 확인해 달라.
  - `view_by_type.txt`의 `2024.04.01(월)` 계열 trailing 처리가 기존 단종 매칭 및 교차검증 결과를 흔들지 않는지 확인해 달라.
- 표시 개선 검토
  - Q2 히스토그램과 05 모델 산점도의 축 제한/주석이 장기 gap 원값 유지 결정을 충분히 전달하는지 확인해 달라.
