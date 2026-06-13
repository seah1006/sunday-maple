# Claude Handoff Phase 13

## 구현 요약

- `src/predict_dataset.py`의 `build_prediction_frame`과 `write_prediction_frame`에 `candidate_cutoff` 인자를 추가했다.
- `candidate_cutoff`가 `None`이면 기존처럼 전체 eligible 행 빈도로 후보를 고른다.
- `candidate_cutoff`가 있으면 `date < candidate_cutoff`인 eligible 행 빈도로만 top N 후보를 고른다.
- 컷오프는 후보 universe 고정에만 사용한다. 행 생성 대상 회차, 피처 계산, 타깃 계산은 전 구간을 유지한다.
- 컷오프 이전 eligible 행이 없으면 `ValueError`를 낸다.
- `notebooks/06_predict.ipynb`는 `SPLIT_CUTOFF = 2025-01-01` 하나를 후보 컷오프와 시간순 분할에 같이 사용한다.
- 노트북은 기존 `predict_dataset.csv` 캐시를 조건부로 재사용하지 않고 매 실행 재생성한다.
- 사용자 모델 셀은 계속 비어 있다.

## 테스트 추가

- 컷오프 이후 데이터가 바뀌어도 후보 집합이 고정되는지 확인한다.
- 같은 데이터에서 `candidate_cutoff=None`과 컷오프 적용 결과의 후보 집합이 달라지는 케이스를 확인한다.
- 컷오프가 전체 데이터보다 앞서면 `ValueError`가 나는지 확인한다.

## 노트북 가정 명시

- 후보 상위 N개는 train 구간(`< 2025-01-01`) 빈도로만 선정한다.
- `category`는 보상의 정적 속성으로 보고 전체 이력 최빈값을 사용한다.
- `date_hit_rate`에서 점수 동점은 `nlargest` 선택에 따르며 베이스라인 비교용 근사 지표로 해석한다.

## 새 예측 데이터 요약

- 행 수: 9,180
- 회차 수: 459
- 후보 수: 20
- 양성 비율: 0.100763
- 기간: `2017-03-12` ~ `2026-06-07`
- 후보 컷오프: `2025-01-01`
- 후보 목록: 룬_경험치버프, 현상금_경험치, 콤보킬_경험치, 불꽃늑대_경험치, 주문의흔적_비용할인, 몬스터파크_경험치, 스타포스_비용할인, 어빌리티_재설정할인, 스타포스_성공확률, 위대한소울_확률, 스타포스_1+1강화, 몬스터컬렉션, 경험치쿠폰_지급, 심볼교환권_지급, 성장의비약_지급, 아케인리버_보상, 엘리트몬스터_증가, 미라클타임, 돌발미션, 경험치_배수버프

## 노트북 실행 결과

- train: `2017-03-12` ~ `2024-12-29`, 7,680행, 양성 비율 0.098568
- test: `2025-01-05` ~ `2026-06-07`, 1,500행, 양성 비율 0.112000
- 분할 검증: `train date max < test date min` true

| 기준선 | accuracy | f1 | roc_auc | date_hit_rate |
|---|---:|---:|---:|---:|
| 간격규칙 | 0.416000 | 0.200730 | 0.520324 | 0.347826 |
| 사전확률 | 0.888000 | 0.000000 | 0.700723 | 0.362319 |

## 검증

- `python -m pytest -q`: 40 passed
- `jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb --output 06_predict.executed.ipynb --output-dir notebooks`: 성공
- 실행 확인용 `notebooks/06_predict.executed.ipynb`는 삭제했다.
- `notebooks/06_predict.ipynb`의 사용자 모델 코드 셀은 비어 있다.
- 노트북 코드 셀 주석 라인: 0
