# Claude Handoff Phase 12

## 구현 요약

- `src/predict_dataset.py`를 추가해 `(date, reward_norm)` 후보 행렬을 생성했다.
- 후보는 `is_future == False`, `no_event_week == False`인 회차에서 출현 빈도 상위 `top_n` 보상으로 잡는다.
- 타깃 `y`는 해당 회차에 후보 보상이 실제 상장됐는지로 계산한다.
- 피처는 예측 시점 `date`보다 이전 회차 정보만 사용한다.
- `is_discontinued`, `is_future`, `event_context`, `is_major_event`, 기존 `cycle_days`는 피처에 넣지 않았다.
- `data/interim/predict_dataset.csv`를 생성했다.
- `notebooks/06_predict.ipynb`를 추가해 시간순 분할, 베이스라인 2종, 평가 함수, 사용자 모델용 빈 코드 셀을 제공했다.

## 피처 규칙

- `days_since_last`: 과거 출현이 있으면 마지막 출현일부터 현재 회차까지의 일수, 없으면 관측 시작일부터 현재 회차까지의 일수
- `past_count`: 현재 회차 이전 출현 횟수
- `past_rate`: 현재 회차 이전 eligible 회차 수 대비 출현 비율
- `roll_gap_mean`, `roll_gap_median`: 현재 회차 이전 출현 간격 중 최근 `roll_k`개의 평균과 중앙값
- `lag1_appeared`: 직전 eligible 회차 출현 여부
- `category`: 후보 보상의 대표 카테고리
- `month`, `quarter`, `weekofyear`: 예측 대상 날짜의 계절성 값

## 테스트

- `tests/test_predict_dataset.py`를 추가했다.
- 미래 행 제거 전후 같은 과거 `(date, reward_norm)` 피처가 동일한지 확인한다.
- 타깃 `y`가 같은 회차의 실제 보상 출현과 일치하는지 확인한다.
- 첫 출현 전 `days_since_last`, `past_count`, 간격 통계 규칙을 확인한다.

## 노트북 결과

- 데이터 행 수: 9,180
- 회차 수: 459
- 후보 수: 20
- 전체 양성 비율: 0.1036
- 시간순 분할: train `2017-03-12` ~ `2024-12-29`, test `2025-01-05` ~ `2026-06-07`
- 분할 검증: `train date max < test date min`

| baseline | accuracy | f1 | roc_auc | date_hit_rate |
|---|---:|---:|---:|---:|
| rule_gap | 0.519333 | 0.282587 | 0.576757 | 0.432432 |
| prior_rate | 0.856000 | 0.000000 | 0.560681 | 0.337838 |

## 검증

- `python -m pytest -q`: 37 passed
- `jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb --output 06_predict.executed.ipynb --output-dir notebooks`: 성공
- 실행 확인용 `notebooks/06_predict.executed.ipynb`는 삭제했다.
- 원본 `notebooks/06_predict.ipynb`의 사용자 모델 코드 셀은 비어 있다.
- 원본 노트북 코드 셀에 주석 라인은 없다.
