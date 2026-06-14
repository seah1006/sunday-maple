# Codex Work Packet — Phase 14 (예측 중심 발표 전환: 분류 모델 + 다음 회차 예측)

> Phase 13 후속. Phase 12~13에서 누수 없는 분류 스캐폴드(06_predict)를 완성했고, 모델 셀은 "사용자 몫"으로 비워 두었다. **사용자 결정(2026-06-14): 발표 방향을 "다음 선데이 예측" 중심(풀스케일)으로 전환.** 따라서 이번 Phase는 비워 둔 모델 셀을 채우고, 학습된 모델로 **다음 미관측 회차(2026-06-14)의 보상 등장 확률을 추론**하는 기능을 추가한다.

## 작업 배경

### 방향 전환의 의미 (사용자 결정, 사실)
- 기존 CLAUDE.md 규칙 "예측 모델은 보조 목표이며 오버엔지니어링을 피한다", "모델 셀은 사용자 몫(비움)"을 **이번 Phase에 한해 완화**한다. 발표 후 해당 규칙 문구는 별도로 업데이트한다(이번 범위 밖).
- "풀스케일"은 모델을 많이 늘어놓는 것이 아니라 **예측을 발표 중심에 두고 시간순 백테스트로 정직하게 평가**하는 것이다. 모델은 **2종(로지스틱 회귀 + 트리 앙상블)으로 상한**을 둔다. 데이터 천장이 낮아 모델을 더 늘려도 가치가 없다.

### 조사한 데이터 사실 (Claude 직접 확인, 사실)
- `data/processed/tidy_rewards.csv`: 14컬럼, 날짜 범위 2017-03-12 ~ 2026-08-30.
- **관측(eligible: `is_future=False` & `no_event_week=False`) 최종 회차 = 2026-06-07(일요일).**
- **미래 스캐폴드: `is_future=True` 12행, 날짜 2026-06-14 ~ 2026-08-30 (매주 일요일).** 보상 없음(추론 대상 빈 슬롯).
- 오늘 = 2026-06-14(일요일). **다음 미관측 회차 = 2026-06-14** (관측 최종 06-07의 다음 일요일).
- `06_predict.ipynb` 현재: `SPLIT_CUTOFF = 2025-01-01`로 후보 컷오프·시간순 분할 통일. train 7,680행(2017-03-12~2024-12-29, 양성 0.0986) / test 1,500행(2025-01-05~2026-06-07, 양성 0.1120). 후보 20종. 베이스라인 2종(간격규칙 B1, 사전확률 B2). `evaluate()`는 accuracy/f1/roc_auc/date_hit_rate 반환. 모델 셀(`user-model-empty`) 비어 있음.
- `src/predict_dataset.py`: `build_prediction_frame(tidy, top_n=20, roll_k=5, candidate_cutoff=None)` 존재. `_eligible_rows`, `_candidate_rewards`, `_category_map` 헬퍼 존재. **`build_inference_frame`은 없음**(중복 아님).
- `FEATURE_COLUMNS = [days_since_last, past_count, past_rate, roll_gap_mean, roll_gap_median, lag1_appeared, category, month, quarter, weekofyear]`.
- `05_model.ipynb`: Task B(주기/등장임박)의 베이스라인 이미 존재 — 보상별 과거 cycle 중앙값 MAE **74.49** vs 전역 중앙값 93.65 (등장 3회↑ reward_norm 34종). **이번 Phase에서 건드리지 않는다**(중복 방지). 발표에서 "주기는 어느 정도, 구체 선택은 외생" 근거로 인용만.
- 현재 테스트: `python -m pytest -q` → **40 passed**.

## 제약 조건

- `data/raw/` 불변. `data/processed/tidy_rewards.csv` 읽기 전용·14컬럼 유지.
- **피처는 계속 `< target_date`(엄격 미만)만 사용** — 누수 불변식 유지(Phase 12~13 핵심). 추론 프레임도 동일.
- 시간순 분할/백테스트만. **랜덤 split 금지.** 난수 사용 모델은 `random_state` 고정(기존 관례 `RANDOM_SEED = 42`).
- **코드 주석·docstring 금지**(발표자료 규칙, [[no-code-comments]]). 설명은 노트북 마크다운 셀에.
- 노트북 비코드 텍스트(마크다운·`print`/`display` 라벨) **한글**. 데이터 값 원문은 변경 금지.
- 후보 universe는 train 컷오프(`SPLIT_CUTOFF = 2025-01-01`)로 고정한 **20종 그대로**. 추론도 같은 후보집합·같은 컷오프를 써야 학습/추론 피처 정의가 일치한다.
- 기존 `python -m pytest -q` 40 passed 유지(테스트는 추가만, 기존 의미 보존).
- **모델은 2종 상한**(로지스틱 + 트리 앙상블 1종). 하이퍼파라미터 그리드서치·모델 추가 금지(오버엔지니어링).
- 리포트(`outputs/report/`)·HTML 재생성은 **이번 범위 밖**(Phase 15).

---

## 작업 1 — 추론 프레임 추가 (`src/predict_dataset.py`)

**수정 대상**: `src/predict_dataset.py`에 신규 함수 `build_inference_frame` 추가. 기존 함수 시그니처·동작 변경 금지(하위호환).

**목표 함수 (설명)**:
```
def build_inference_frame(
    tidy: pd.DataFrame,
    target_date: pd.Timestamp | str,
    top_n: int = 20,
    roll_k: int = 5,
    candidate_cutoff: pd.Timestamp | str | None = None,
) -> pd.DataFrame
```
- 반환: **후보 1종당 1행**, 컬럼 = `["date", "reward_norm", *FEATURE_COLUMNS]`. **`y` 컬럼 없음**(미관측이라 타깃 미정).
- 모든 행의 `date` = `pd.to_datetime(target_date)`.
- 후보 집합: `_candidate_rewards`를 **`candidate_cutoff` 적용된 eligible**로 산출(=`build_prediction_frame`과 동일 규칙). `candidate_cutoff`가 컷오프 이전 eligible을 비우면 `ValueError`(기존과 동일 정책).
- 피처는 **eligible 중 `date < target_date`인 등장만** 사용(엄격 미만):
  - `prior_dates` = 해당 보상의 `target_date` 이전 등장일 리스트.
  - `past_count = len(prior_dates)`.
  - `days_since_last = (target_date - prior_dates[-1]).days`, 없으면 `(target_date - 최초 eligible일).days`.
  - `past_rate = past_count / n_prior_dates`, 여기서 `n_prior_dates` = `target_date`보다 앞선 **고유 eligible 회차 수**. `n_prior_dates == 0`이면 `0.0`.
  - `roll_gap_mean/median` = `prior_dates` 연속 간격(diff, days)의 최근 `roll_k`개 평균/중앙값. 간격 <1개면 `np.nan`.
  - `lag1_appeared` = 직전 eligible 회차(= `target_date`보다 앞선 가장 최근 eligible일)에 해당 보상이 있었으면 1, 아니면 0.
  - `category` = `_category_map(eligible)`의 값(정적 속성, 기존과 동일).
  - `month/quarter/weekofyear` = `target_date` 기준.
- **재사용**: `_eligible_rows`, `_candidate_rewards`, `_category_map`를 그대로 호출해 로직 중복을 피한다. `build_prediction_frame`의 피처 계산식과 정의가 일치해야 한다.

**구현 전략 및 대안**:
- 대안 A(채택): 별도 함수 `build_inference_frame`. 학습 프레임과 피처 정의를 공유하되 `y` 없이 단일 날짜만 생성. → 책임 분리 명확, 기존 함수 무변경.
- 대안 B(미채택): `build_prediction_frame`에 `extra_dates` 인자로 미래일 끼워넣기. → `y` 의미 모호(미래는 0이 아님), 기존 함수 복잡화. 채택 안 함.

**검증 요구사항** (`tests/test_predict_dataset.py`에 추가):
- `test_inference_frame_shape_and_no_target`: 추론 프레임이 후보 수만큼 행, 컬럼에 `y` 없음, 모든 `date == target_date` 확인.
- `test_inference_matches_training_features_at_same_asof`: 동일 tidy에서 `build_prediction_frame(...)`의 **마지막 eligible 회차 `d_last`** 행 피처와, `build_inference_frame(..., target_date=d_last, candidate_cutoff=동일)`의 같은 보상 행 피처가 **`y` 제외 전부 동일**함을 확인(피처 정의 일치 + 누수 없음 증명). 비교 컬럼 = `FEATURE_COLUMNS`.
- `test_inference_uses_only_past_of_target`: `target_date`를 모든 데이터 이후로 두면 `days_since_last`·`past_count` 음수 0, `past_rate ∈ [0,1]`, 행 수 = 후보 수 확인.
- `test_inference_candidate_cutoff_consistency`: 같은 `candidate_cutoff`에서 추론 후보집합(`reward_norm` 고유값) == `build_prediction_frame` 후보집합.

**기존 결과 영향 여부**: 신규 함수만 추가 → 기존 테스트·`predict_dataset.csv` 무영향.

## 작업 2 — 노트북 모델 학습 + 시간순 백테스트 (`notebooks/06_predict.ipynb`)

**수정 대상**: `model-input` 셀 이후의 빈 모델 셀(`user-model-empty`) 및 인접 마크다운. 기존 데이터 로드·분할·베이스라인 셀은 유지.

**변경 목표**:
1. `user-model-title`/빈 셀을 **실제 모델 학습 셀**로 교체:
   - 모델 2종, `random_state=RANDOM_SEED` 고정:
     - `LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED)`
     - 트리 앙상블 1종: `RandomForestClassifier(n_estimators=..., class_weight="balanced", random_state=RANDOM_SEED)` **또는** `GradientBoostingClassifier(random_state=RANDOM_SEED)` 중 하나(택1, handoff에 선택·사유 기재).
   - `X_train, y_train`으로 학습, `X_test`에 `predict_proba(...)[:, 1]` 점수 산출.
   - 기존 `evaluate(test["y"], 점수, test["date"])`로 **베이스라인 2종과 같은 표에 합쳐** 비교(행: 간격규칙/사전확률/로지스틱/트리). accuracy·f1·roc_auc·date_hit_rate.
   - `RANDOM_SEED`는 imports 셀 또는 모델 셀 상단에 정의(05_model와 동일 관례).
2. **백테스트 해석 마크다운** 추가: 이 비교가 train(<2025-01-01)으로 학습해 test(2025-01-05~2026-06-07)를 예측한 **시간순 백테스트**임을 명시. 모델이 베이스라인을 넘는지/못 넘는지를 정직하게 서술(수치는 Codex가 실행 결과로 채움).
3. 클래스 불균형(양성 ~10%) 주의 마크다운 한 줄: 임계 0.5 정확도보다 **순위 지표(date_hit_rate, roc_auc)**로 해석.

**구현 전략**:
- 입력 정렬: 기존 `model-input` 셀이 `X_all = pd.get_dummies(df[feature_columns], columns=["category"], dummy_na=True).fillna(-1)` 후 `train.index`/`test.index`로 분할 중. 이 구조 유지.

**검증 요구사항**:
- 베이스라인+모델 4행 비교표가 출력되고, 모든 점수가 유한값.
- 커널 재시작 후 재실행 동일 결과(seed 고정).
- 코드 주석 0, 라벨 한글.

**기존 결과 영향**: 베이스라인 셀 출력 불변. 모델 셀만 신규.

## 작업 3 — 다음 회차(2026-06-14) 예측 + 정직 해석 (`notebooks/06_predict.ipynb`)

**수정 대상**: 모델 셀 이후 신규 셀들 + `conclusion` 마크다운 보강.

**변경 목표**:
1. **추론 셀**:
   - `TARGET_DATE = pd.Timestamp("2026-06-14")` 정의(마크다운에 "관측 최종 2026-06-07의 다음 일요일"임을 명시. 그 다음 회차 2026-06-21도 같은 방식으로 바꿔 볼 수 있음을 한 줄 안내).
   - `from src.predict_dataset import build_inference_frame`.
   - `infer = build_inference_frame(pd.read_csv(tidy_path), TARGET_DATE, candidate_cutoff=SPLIT_CUTOFF)`.
   - **컬럼 정렬(중요)**: 추론 피처를 학습 더미 컬럼에 맞춘다.
     `X_infer = pd.get_dummies(infer[feature_columns], columns=["category"], dummy_na=True)` 후 **`X_infer = X_infer.reindex(columns=X_all.columns, fill_value=0)`**, 그 뒤 `.fillna(-1)`. (학습에 없던 카테고리 더미는 0, 학습에 있던 컬럼 누락은 0으로 채워 모양 일치.)
   - 작업 2에서 더 나은(또는 대표) 모델로 `proba = model.predict_proba(X_infer)[:, 1]`.
   - 결과표: `reward_norm`, `등장확률`(proba)을 확률 내림차순 정렬해 `display`.
2. **고신뢰/불확실 분리 마크다운 + 셀**: 예측표를 "상시 뼈대(고확률)"와 "불확실 슬롯"으로 나눠 제시. 분리 기준은 한 가지로 명시(예: 회차 평균 보상 수만큼 상위 절단, 또는 확률 임계 1개). 기준을 마크다운에 한 줄로 못박는다(임의 절단이 아님을 밝힘).
3. **정직 해석 마크다운**(발표 핵심): 
   - 예측 가능한 부분 = 상시 핵심 보상(거의 매주 등장). 
   - 예측 불가능한 부분 = 스페셜·이벤트 연동 보상은 넥슨 운영 결정이라 과거 패턴 밖. 
   - 주기 측면 근거로 05_model의 보상별 중앙값 MAE 74.49(전역 93.65 대비) 인용 — "주기는 부분적으로만, 구체 선택은 외생".
   - 결론: 낮은 예측 천장은 데이터 한계를 이해한 결과이며, 블랙박스(maplessunday) 대비 **투명·재현 가능**이 본 프로젝트의 차별점.
4. `conclusion` 마크다운을 위 해석과 정합되게 보강(기존 "누수 없는 비교 환경" 프레임 유지하되 예측 중심 서사로 확장).

**검증 요구사항**:
- 추론 결과표가 **후보 20행**, `등장확률 ∈ [0,1]`, `TARGET_DATE`가 출력에 드러남.
- `X_infer.columns`가 `X_train.columns`와 정렬 일치(추론 셀에서 shape/컬럼 일치 확인 출력 권장).
- nbconvert 재실행 성공. 코드 주석 0, 라벨 한글, 시드 고정.

**기존 결과 영향**: 신규 셀 추가. 분할 검증(`train date max < test date min`) 유지.

## 검증 기준

- `python -m pytest -q` 전체 통과(기존 40 + 신규 추론 테스트 4종). 신규 테스트는 `build_inference_frame` 부재 시 ImportError로 실패할 성질(회귀 가드).
- `jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb` 성공(검증용 산출물은 삭제).
- 베이스라인 2 + 모델 2 비교표 출력, 다음 회차(2026-06-14) 예측표 20행 출력.
- 데이터 무결성: 추론 프레임 `days_since_last`·`past_count` 음수 0, `past_rate ∈ [0,1]`, 학습/추론 피처 정의 일치 테스트 통과.
- 코드 주석 0, 노트북 라벨 한글, 모델 난수 시드 고정, 랜덤 split 없음.

## 작업 우선순위 요약

| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1 | `src/predict_dataset.py`(신규 함수) + `tests/test_predict_dataset.py`(테스트 4) | ~60–80줄 | tidy(읽기) |
| 2 | `06_predict.ipynb` 모델 2종 + 백테스트 표/해석 | ~30–40줄 | 작업1 불필요(독립) |
| 3 | `06_predict.ipynb` 추론 셀 + 고신뢰/불확실 분리 + 정직 해석 | ~30–40줄 | 작업1·2 |

## 이번 범위 제외 항목

- **리포트 예측 절 + HTML 재생성 — Phase 15**(모델 결과 확정 후 `outputs/report/final_report.md`에 예측 절 추가, `build_html.py` 재생성). 현재 리포트 구조: §5 보조 베이스라인 / §6 한계 / §7 결론 → 예측 절은 새 §6으로 삽입 예정.
- **05_model 회귀(주기) 모델 확장** — 이미 베이스라인 존재. 발표에서 인용만, 모델 추가는 보류(오버엔지니어링 회피).
- **하이퍼파라미터 튜닝·모델 3종 이상** — 데이터 천장 낮아 가치 없음. 2종 상한 유지.
- **CLAUDE.md "예측=보조목표/오버엔지니어링 금지" 문구 갱신** — 발표 방향 확정 후 별도 처리.
- `event_context`/`is_major_event` 피처 도입 — 누수 가정 검토 필요, 후속.
