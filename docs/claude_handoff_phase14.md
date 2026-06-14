# Claude Handoff Phase 14

## 구현 요약

- `src/predict_dataset.py`에 `build_inference_frame`을 추가했다.
- 기존 `build_prediction_frame`, `write_prediction_frame`의 시그니처와 동작은 변경하지 않았다.
- 추론 프레임은 `["date", "reward_norm", *FEATURE_COLUMNS]`만 반환하며 `y` 컬럼을 만들지 않는다.
- 모든 추론 피처는 `target_date` 미만의 eligible 이력만 사용한다.
- 후보 universe는 `candidate_cutoff`가 있을 때 기존 학습 프레임과 같은 방식으로 cutoff 이전 eligible 행에서 선정한다.
- `tests/test_predict_dataset.py`에 추론 프레임 테스트 4개를 추가했다.
- `notebooks/06_predict.ipynb`의 빈 모델 셀을 로지스틱 회귀와 랜덤포레스트 2종으로 채웠다.
- 같은 노트북에 `TARGET_DATE = 2026-06-14` 추론 셀을 추가했고, `X_infer`는 `X_all.columns`로 `reindex`해 학습 입력 컬럼과 순서를 맞췄다.
- 리포트와 HTML 산출물은 건드리지 않았다.

## 검증 결과

`python -m pytest -q`

```text
............................................                             [100%]
44 passed in 0.84s
```

`jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb`

```text
[NbConvertApp] Converting notebook notebooks/06_predict.ipynb to notebook
C:\Users\my\AppData\Local\Programs\Python\Python313\Lib\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 25602 bytes to notebooks\06_predict.nbconvert.ipynb
```

- nbconvert 실행은 성공했다.
- Windows/ZMQ 런타임 경고만 있었고 실행 실패는 없었다.
- 검증용 `notebooks/06_predict.nbconvert.ipynb`는 삭제했다.

## 데이터 상태

- 학습 구간: 7,680행, 2017-03-12 ~ 2024-12-29, 양성비율 0.0985677083
- 테스트 구간: 1,500행, 2025-01-05 ~ 2026-06-07, 양성비율 0.112
- 추론 대상일: 2026-06-14
- 추론 후보 수: 20
- `X_infer.columns == X_all.columns`: True
- 추론 확률 범위: 0.000000 ~ 0.533333

### 백테스트 비교표

| 방법 | accuracy | f1 | roc_auc | date_hit_rate |
|---|---:|---:|---:|---:|
| 간격규칙 | 0.416000 | 0.200730 | 0.520324 | 0.347826 |
| 사전확률 | 0.888000 | 0.000000 | 0.700723 | 0.362319 |
| 로지스틱 | 0.532000 | 0.298000 | 0.748494 | 0.391304 |
| 랜덤포레스트 | 0.860667 | 0.125523 | 0.734951 | 0.449275 |

### 2026-06-14 추론표

| 순위 | date | reward_norm | 상장확률 | 구분 |
|---:|---|---|---:|---|
| 1 | 2026-06-14 | 현상금_경험치 | 0.533333 | 고신뢰 |
| 2 | 2026-06-14 | 불꽃늑대_경험치 | 0.533333 | 고신뢰 |
| 3 | 2026-06-14 | 스타포스_성공확률 | 0.483333 | 고신뢰 |
| 4 | 2026-06-14 | 스타포스_1+1강화 | 0.470000 | 고신뢰 |
| 5 | 2026-06-14 | 몬스터컬렉션 | 0.420000 | 고신뢰 |
| 6 | 2026-06-14 | 주문의흔적_비용할인 | 0.370000 | 불확실 |
| 7 | 2026-06-14 | 어빌리티_재설정할인 | 0.350000 | 불확실 |
| 8 | 2026-06-14 | 엘리트몬스터_증가 | 0.253333 | 불확실 |
| 9 | 2026-06-14 | 몬스터파크_경험치 | 0.240000 | 불확실 |
| 10 | 2026-06-14 | 위대한소울_확률 | 0.226667 | 불확실 |
| 11 | 2026-06-14 | 미라클타임 | 0.153333 | 불확실 |
| 12 | 2026-06-14 | 룬_경험치버프 | 0.133333 | 불확실 |
| 13 | 2026-06-14 | 콤보킬_경험치 | 0.133333 | 불확실 |
| 14 | 2026-06-14 | 스타포스_비용할인 | 0.123333 | 불확실 |
| 15 | 2026-06-14 | 경험치쿠폰_지급 | 0.116667 | 불확실 |
| 16 | 2026-06-14 | 심볼교환권_지급 | 0.116667 | 불확실 |
| 17 | 2026-06-14 | 성장의비약_지급 | 0.086667 | 불확실 |
| 18 | 2026-06-14 | 경험치_배수버프 | 0.080000 | 불확실 |
| 19 | 2026-06-14 | 아케인리버_보상 | 0.006667 | 불확실 |
| 20 | 2026-06-14 | 돌발미션 | 0.000000 | 불확실 |

## 선택한 트리 모델과 사유

트리 모델은 `RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42)`를 선택했다.

선택 이유:

- 작은 tabular feature set에서 비선형 조합과 결측 대체값 `-1`을 별도 스케일링 없이 처리하기 쉽다.
- 단일 결정트리보다 분산을 줄일 수 있다.
- `class_weight="balanced"`로 낮은 양성비율을 최소한 반영한다.
- 하이퍼파라미터 탐색 없이 고정 파라미터 1개 모델로 유지할 수 있다.

## Claude 리뷰 요청

Critical:

- `build_inference_frame`이 모든 feature에서 `target_date` 미만 이력만 사용하는지 검토해 달라.
- `candidate_cutoff` 적용이 학습 프레임과 완전히 같은 후보 universe를 만드는지 확인해 달라.
- 노트북 추론 셀의 `X_infer.reindex(columns=X_all.columns, fill_value=0).fillna(-1)` 순서가 학습 입력과 불일치나 결측 누수를 만들지 않는지 확인해 달라.

Major:

- `build_inference_frame(target_date=d_last)`와 `build_prediction_frame`의 같은 as-of feature 일치 테스트가 충분한지 봐 달라.
- 랜덤포레스트를 최종 추론 모델로 쓰는 해석이 과장되지 않았는지, `date_hit_rate` 우선 해석이 발표 메시지와 맞는지 검토해 달라.
- 고신뢰 기준을 상위 5개로 둔 것이 임의 절단선임을 충분히 명시했는지 확인해 달라.

Minor:

- 노트북 마크다운의 한국어 표현이 발표 자료 톤과 맞는지 봐 달라.
- 비교표 컬럼명과 추론표 컬럼명이 리포트 Phase 15에 옮기기 쉬운 형태인지 확인해 달라.
- 코드 주석과 docstring이 새로 추가되지 않았는지 한 번 더 확인해 달라.
