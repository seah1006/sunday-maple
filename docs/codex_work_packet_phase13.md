# Codex Work Packet — Phase 13 (예측 후보 선정 누수 차단 + 가정 문서화)

> Phase 12 후속. Phase 12는 "누수 없는 예측 스캐폴드"를 목표로 했고 피처 엔지니어링 자체는 누수가 없음을 Claude가 독립 재검증으로 확인했다. 그러나 **후보 보상 집합(top_n)을 전체 이력(테스트 구간 포함) 빈도로 선정**해 실험 설계가 미래 정보를 엿보는 문제가 남아 있다. 본 Phase는 이 누수를 차단하고 남은 설계 가정을 노트북에 명시한다. 모델 셀은 계속 사용자 몫(비움)이다.

## 작업 배경

### Claude의 Phase 12 독립 재검증 결과 (사실)
- `python -m pytest -q` → 37 passed.
- `build_prediction_frame(tidy)` 재실행 수치: 9,180행 / 459회차 / 후보 20 / 양성비율 0.1036. handoff 보고와 일치.
- `days_since_last`·`past_count` 음수 0건, `past_rate` ∈ [0,1].
- **피처값 누수 없음 확인**: tidy를 임의 회차 `mid`(2021-07-25)까지 truncate해 재생성한 뒤, `mid` 회차의 공통 후보 보상에 대한 `days_since_last/past_count/past_rate/roll_gap_mean/roll_gap_median/lag1_appeared`가 전부 동일함을 대조로 확인. 피처는 모두 `< d`만 사용한다.
- 노트북 `06_predict.ipynb` end-to-end 재실행 성공(nbconvert EXIT 0). 코드 주석 0, 사용자 모델 셀 비어 있음, 라벨 한글.

### 발견된 문제 (본 Phase가 다룸)
- **[Major] 후보 집합 선정 누수**: `_candidate_rewards`가 `_eligible_rows(tidy)` 전체(= train+test 전 구간)의 빈도로 상위 `top_n`을 고른다. tidy를 `mid`까지 truncate하면 상위 20 중 4개가 교체됨을 확인했다(전체에만 있던 4개 ↔ truncate에만 있던 4개). 즉 "어떤 보상을 예측 대상으로 삼을지"라는 표본 설계가 테스트 구간의 빈도를 본다. 모델이 후보 선정 사실을 피처로 받지는 않지만, 시간순 holdout의 엄밀성("예측 시점에 알 수 있는 정보만 사용")을 위반한다.
- **[Major-보강] 누수 테스트의 사각지대**: `tests/test_predict_dataset.py::test_prediction_features_do_not_change_when_future_rows_are_removed`는 `top_n=2`에 보상이 정확히 2개(A,B)뿐이라 후보 집합이 절대 바뀌지 않는다. 따라서 후보 선정 누수를 구조적으로 탐지하지 못한다. 회귀 테스트로 이 사각지대를 메워야 한다.
- **[Minor] `category` 정적 매핑의 전체 이력 사용**: `_category_map`이 전체 이력의 최빈 카테고리를 쓴다. 카테고리는 보상의 정적 속성이라 실무상 허용되나, 미래 행을 포함해 산출한다는 점은 가정으로 명시할 가치가 있다.
- **[Minor] `evaluate`의 `date_hit` 동점 처리**: B1처럼 점수가 이진(0/1)이면 `nlargest(k, "score")`의 동점이 임의로 끊긴다. `date_hit_rate`에 약한 임의성이 생긴다. 베이스라인 지표라 허용하되 노트북에 한 줄로 명시.

## 제약 조건

- `data/raw/` 불변. `data/processed/tidy_rewards.csv` 읽기 전용·스키마 14컬럼 유지.
- **피처는 계속 `< d`만 사용**(Phase 12 불변식 유지). 본 Phase는 후보 선정 단계에만 컷오프를 도입한다.
- 시간순 분할만. 랜덤 split 금지.
- 코드 주석·docstring 금지(발표자료 규칙). 설명은 노트북 마크다운 셀에.
- 보조 목표 꼬리표 유지. **모델 학습 코드는 사용자 몫 — 모델 셀은 계속 비운다.**
- 기존 `python -m pytest -q` 37 passed 유지(테스트는 추가/보강만, 기존 통과 테스트 의미 보존).
- **오버엔지니어링 금지**: 후보 선정에 train 컷오프 한 개만 도입한다. 새 모델·새 피처·새 평가지표를 추가하지 않는다.

---

## 작업 1 — 후보 선정에 train 컷오프 도입 (`src/predict_dataset.py`)

**수정 대상**: `src/predict_dataset.py`의 `build_prediction_frame`, `write_prediction_frame`.

**현재 코드 (발췌)**:
```python
def build_prediction_frame(tidy: pd.DataFrame, top_n: int = 20, roll_k: int = 5) -> pd.DataFrame:
    ...
    eligible = _eligible_rows(tidy)
    ...
    candidates = _candidate_rewards(eligible, top_n)
```
`_candidate_rewards`가 `eligible` 전체(train+test) 빈도로 후보를 고른다.

**변경 목표**:
- `build_prediction_frame`에 선택 인자 `candidate_cutoff: pd.Timestamp | str | None = None`를 추가한다.
- `candidate_cutoff`가 주어지면 후보 빈도는 **`date < candidate_cutoff`인 eligible 행만으로** 계산한다. `None`이면 기존처럼 전체로 계산(하위호환).
- 후보 선정에만 컷오프를 적용한다. **행 생성 대상 회차(`dates`)와 피처/타깃 계산은 전 구간 그대로** 유지한다(테스트 구간에도 같은 후보 집합으로 행을 만들어 평가). 즉 컷오프는 "후보 universe를 train 정보로 고정"하는 용도이지, 테스트 행을 잘라내는 용도가 아니다.
- 구현 방식 예: `_candidate_rewards(eligible, top_n)` 호출 직전에 컷오프가 있으면 `eligible.loc[eligible["date"] < pd.to_datetime(candidate_cutoff)]`를 후보 산출 입력으로 쓰되, 컷오프 이전 데이터가 비면 안전하게 전체로 폴백하거나 명시적 에러를 낸다(둘 중 하나를 선택하고 handoff에 사유 기재). **권장: 컷오프 이전이 비면 `ValueError`로 명확히 실패**(조용한 폴백은 누수 회귀를 숨길 수 있음).
- `write_prediction_frame`에도 동일 인자 `candidate_cutoff`를 추가해 CLI/캐시 생성 시 전달 가능하게 한다. 기본값 `None` 유지.

**구현 전략 및 대안**:
- 대안 A(채택): 후보 universe만 train으로 고정. 테스트 행은 같은 후보로 생성·평가. → 시간순 holdout 엄밀성 충족, 평가 표본 안정.
- 대안 B(미채택): 컷오프 이후 행 자체를 제거. → 그러면 테스트셋이 사라져 평가 불가. 채택 안 함.
- 대안 C(미채택): 후보를 회차별 rolling top_n으로 동적 선정. → 오버엔지니어링, 범위 밖.

**검증 요구사항** (`tests/test_predict_dataset.py`에 추가):
- `test_candidate_set_is_stable_under_future_rows`: 후보가 3개 이상 경쟁하도록 보상 ≥4종·빈도 차이가 있는 tidy를 구성. `candidate_cutoff`를 중간 회차로 주고 `build_prediction_frame(full, top_n=2, candidate_cutoff=C)`와 `build_prediction_frame(full[date < later], top_n=2, candidate_cutoff=C)`의 **후보 집합(`reward_norm` 고유값)이 동일**함을 확인. 즉 컷오프 이후 데이터가 바뀌어도 후보가 불변임을 증명.
- `test_candidate_cutoff_changes_selection_vs_full`: 같은 tidy에서 `candidate_cutoff=None`과 특정 컷오프가 **서로 다른 후보 집합**을 낼 수 있음을 한 케이스로 확인(컷오프가 실제로 작동함을 증명). 단, 데이터에 따라 같을 수도 있으니 케이스를 의도적으로 구성.
- `test_candidate_cutoff_before_data_raises`(대안 채택 시): 컷오프가 모든 데이터보다 앞서면 `ValueError`.
- 기존 누수 테스트(`...do_not_change_when_future_rows_are_removed`)는 **그대로 통과 유지**. 가능하면 이 테스트도 보상 ≥3종으로 확장해 후보 경쟁이 실제로 일어나는 상황에서 피처 불변을 재확인(선택, 여력 되면).

**기존 결과 영향 여부**:
- 기본 호출(`candidate_cutoff=None`)은 동작 불변 → 기존 `predict_dataset.csv` 재생성 시 동일.
- 노트북에서 컷오프를 적용하면(작업 2) 후보 20 중 최대 수 개가 바뀔 수 있다. 행 수(9,180)는 후보 수 20 × 회차 459로 동일하게 유지되어야 한다(후보 집합 구성만 바뀌고 개수는 그대로). handoff에 새 후보 목록과 양성비율 변화를 보고할 것.

## 작업 2 — 노트북 컷오프 적용 + 가정 문서화 (`notebooks/06_predict.ipynb`)

**수정 대상**: `06_predict.ipynb`의 데이터 로드 셀, 베이스라인 마크다운 셀, 평가 마크다운 셀(없으면 인접 마크다운에 문장 추가).

**변경 목표**:
1. 데이터 로드 셀에서 `write_prediction_frame(...)` 호출 시 **`candidate_cutoff`를 시간순 분할 컷오프(`2025-01-01`)와 동일하게 전달**한다. 즉 후보 선정과 train/test 경계를 같은 날짜로 맞춘다. 캐시(`predict_dataset.csv`)가 이미 있으면 삭제 후 재생성되도록 하거나, 컷오프를 반영해 항상 재생성하도록 한다(조용히 옛 캐시를 쓰지 않게 할 것 — 이 점을 handoff에 명시).
   - 주의: 분할 컷오프 상수와 후보 컷오프가 **한 곳에서 정의되어 일치**하도록 한다(둘이 어긋나면 다시 누수). 변수 하나로 묶어 양쪽에 쓰는 구성을 권장.
2. 데이터 로드/후보 관련 마크다운에 **후보 선정 가정**을 한 단락으로 명시: "후보 상위 N개는 train 구간(`< 2025-01-01`) 빈도로만 선정해, 테스트 구간 정보가 표본 설계에 새지 않게 했다."
3. 베이스라인/피처 마크다운에 **`category` 정적 가정** 한 문장 추가: 카테고리는 보상의 정적 속성으로 보고 전체 이력 최빈값을 사용하며, 예측 시점에 알려진 값으로 간주한다.
4. 평가 마크다운에 **`date_hit` 동점 처리** 한 문장 추가: 점수가 동점인 경우 상위 k 선택이 임의로 끊기며, 이는 베이스라인 비교용 근사 지표임을 명시.
5. 모델 셀은 **계속 비운다**. 사용자 작성 안내 마크다운 유지.

**검증 요구사항**:
- 커널 재시작 후 재실행 성공(nbconvert). `tidy`/`predict_dataset.csv`만 의존.
- 분할 검증 출력 유지: `train date max < test date min`.
- 후보 선정 컷오프와 분할 컷오프가 같은 날짜임이 코드/출력에서 드러날 것.
- 코드 주석 0, 라벨 한글, 사용자 모델 셀 비어 있음.

**기존 결과 영향 여부**:
- 베이스라인 수치(accuracy/f1/roc_auc/date_hit_rate)가 후보 집합 변화로 소폭 달라질 수 있다. 달라진 표를 handoff에 보고하고, 해석(결론 프레이밍)은 기존 방향 유지.

## 검증 기준

- `python -m pytest -q` 전체 통과(기존 37 + 신규 후보 안정성/컷오프 테스트). 신규 테스트가 **Phase 12 코드(컷오프 미적용)에서는 실패**할 성질의 것이어야 한다(회귀 가드로 의미 있음).
- `06_predict.ipynb` 재실행 성공, 코드 주석 0, 한글 라벨, 모델 셀 빈 상태.
- 후보 선정이 train 컷오프 기준으로 고정됨을 테스트로 증명.
- 데이터 무결성: 행 수 = 후보 수 × 회차 수 관계 유지, `days_since_last`·`past_count` 음수 없음 재확인.

## 작업 우선순위 요약

| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1 | `src/predict_dataset.py` + `tests/test_predict_dataset.py` | ~25–35줄 | tidy(읽기) |
| 2 | `06_predict.ipynb` 컷오프 적용 + 마크다운 3문단 | ~15–20줄 | 작업1 |

## 이번 범위 제외 항목

- **실제 모델 선택·학습·튜닝 — 사용자 몫**(모델 셀 계속 비움).
- 회차별 동적(rolling) 후보 재선정 — 오버엔지니어링, 범위 밖(컷오프 1개로 충분).
- `event_context`/`is_major_event` 피처 도입 — 여전히 보류(누수 가정 검토 후 후속).
- 리포트에 예측 절 추가 — 사용자가 모델을 완성한 뒤 별도 Phase.
- 새 평가지표·시각화 추가 — 범위 밖.
