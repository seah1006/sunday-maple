# Codex Work Packet — Phase 12 (보조 예측 확장: 등장 확률 분류 스캐폴드)

> 입력: 사용자가 직접 예측을 실험하고 싶다는 요청 + Claude의 maplessunday.com 조사 + `sunday_maple_project_plan.md` 6절. **본 Phase는 "모델 완성"이 아니라 "사용자가 모델을 끼워 실험할 누수 없는 스캐폴드"를 만든다.** 모델 셀은 비워서 사용자가 채운다.

## 작업 배경

### maplessunday.com 조사 (Claude, WebFetch+WebSearch)
- 예측 방법·모델·피처를 **전혀 공개하지 않는 블랙박스**. 적중 기록 메뉴는 있으나 수치 비노출.
- 데이터 출처는 "Data Based on NEXON OPEN API"(우리 인벤 2차 자료와 다름). 기능: 캐릭터 검색·썬데이 달력·썬데이 예측·적중 기록.
- 시사점: 그들의 내부를 모르므로 모방 불가. 우리는 계획서 2.2절 차별점(**투명성·재현성**)을 살린 "재현 가능한 최소판"을 만든다. 1번 조사로 얻은 개선점은 **회차별 적중률(시간순 holdout)을 평가에 포함**해 "적중 기록"을 투명하게 재현하는 것.

### 계획서 6절 (sunday_maple_project_plan.md)
- 목표: 다음 회차 보상(또는 카테고리) 등장 여부 예측. 베이스라인 ① 최빈 ② "경과일 ≥ 평균주기면 등장" 규칙 ③ 인벤 투표. 모델: 로지스틱/결정트리 등 해석 가능 단순 모델. 평가: **시간순 분할(누수 방지), 정확도·F1을 베이스라인과 비교**. 결론: 정확도 낮으면 "넥슨 외부 의사결정 의존성 → 과거 패턴만으론 한계"로 프레이밍.

### 예측 프레이밍 (확정)
- 단위: **(회차 date d, 후보 보상 reward_norm r) 한 쌍 = 1행**, 타깃 = "그 회차에 r이 등장했는가(0/1)". 출력은 확률(`predict_proba`).
- 후보 집합: 등장 빈도 **상위 N개 reward_norm**(기본 N=20, 파라미터). 희귀 보상은 신호 부족·극심한 불균형이라 제외. 카테고리 단위가 필요하면 예측을 category로 집계해 본다(선택).
- 인벤 투표 베이스라인(③)은 **데이터 없음 → 제외하고 노트북에 사유 명시**.

## 제약 조건

- `data/raw/` 불변, `tidy_rewards.csv` 읽기 전용·스키마 14컬럼 유지.
- **누수 차단(이 Phase의 핵심)**: 모든 피처는 예측 시점 `d` **이전(< d)** 정보만 사용한다. 다음은 피처 금지: `is_discontinued`(원문 전체 기반 결과 라벨), `is_future`, 같은 회차 동반 보상, 그리고 미래를 포함해 산출된 기존 `cycle_days` 컬럼(피처는 d 이전만으로 새로 계산). `event_context`/`is_major_event`는 "해당 회차에 사전 공지로 알려진다"는 가정 하에 사용 가능하나 **기본은 제외**하고, 쓰려면 별도 플래그로 분리하고 가정을 마크다운에 명시.
- **시간순 분할만**(랜덤 split 금지).
- 코드 주석·docstring 금지(발표자료 규칙). 설명은 마크다운 셀에.
- 보조 목표 꼬리표 유지(평가 핵심은 EDA). **모델 학습 코드는 사용자 몫 — 모델 셀은 비운다.**
- 기존 `python -m pytest -q` 통과 유지(테스트는 추가만).

---

## 작업 1 — 예측 데이터셋 빌더 (`src/predict_dataset.py` 신규)

**수정 대상**: `src/predict_dataset.py`(신규), `tests/test_predict_dataset.py`(신규).

함수 `build_prediction_frame(tidy: pd.DataFrame, top_n: int = 20, roll_k: int = 5) -> pd.DataFrame`:
- 회차 목록 = `is_future==False & no_event_week==False`인 고유 `date`(시간순).
- 후보 = 분석대상에서 등장 빈도 상위 `top_n` `reward_norm`.
- 각 (d, r)마다 1행, 타깃 `y` = 그 회차에 r 등장 여부.
- **누수 없는 피처(전부 `< d`)**:
  - `days_since_last`: d 이전 r 마지막 등장으로부터 경과일(미등장 시 규칙 정해 명시: 예) 전체 관측 시작일~d 경과일 또는 큰 상수)
  - `past_count`: d 이전 r 등장 횟수
  - `past_rate`: `past_count / (d 이전 회차 수)`
  - `roll_gap_mean`, `roll_gap_median`: d 이전 r의 최근 `roll_k`개 등장 간격 통계(부족 시 결측 규칙 명시)
  - `lag1_appeared`: 직전 회차에 r 등장 여부
  - `category`: r의 카테고리(정적, 누수 아님)
  - `month`, `quarter`, `weekofyear`: d의 계절성
- 출력 컬럼: `date, reward_norm, y, <features...>`. `data/interim/predict_dataset.csv`로 캐시.

**검증 요구사항** (`tests/test_predict_dataset.py`):
- **누수 테스트**: 특정 회차 d의 행 피처가 d 이후 데이터에 불변임을 확인 — 예) tidy에서 마지막 회차 행들을 제거해도 그 이전 회차 (d,r) 피처값이 동일.
- 타깃 정합: 임의 (d,r) 표본의 `y`가 tidy의 실제 등장과 일치.
- `days_since_last`·`past_count` 음수 없음, 첫 등장 이전 처리 규칙대로.

## 작업 2 — `notebooks/06_predict.ipynb` 스캐폴드

**수정 대상**: `notebooks/06_predict.ipynb`(신규).

구성(질문→코드→해석 패턴, 전부 한글, 주석 없음):
1. 서두 마크다운: **보조 목표** 명시 + maplessunday 블랙박스 대비 "투명·재현판" 취지 + 계획서 6절 근거.
2. 작업1 산출(`predict_dataset.csv`) 로드 + 구성 출력(행 수, 후보 수, 양성 비율).
3. **시간순 분할**: 경계 파라미터(기본 `train: date < 2025-01-01`, `test: ≥`). train/test의 date 범위와 양성 비율 출력.
4. **베이스라인 2종(채워서 제공)**:
   - B1 규칙: `days_since_last >= roll_gap_median` 이면 등장(계획서 ②).
   - B2 사전확률: `past_rate`를 점수로(또는 카테고리 최빈).
   - (인벤 투표 ③은 데이터 없음 → 마크다운에 제외 사유.)
5. **평가 함수 제공**: `evaluate(y_true, y_score, dates) -> dict` — accuracy, F1, ROC-AUC + **회차별 적중률**(maplessunday "적중 기록" 미러). 베이스라인 결과를 표로 출력.
6. **사용자 모델 셀(비움)**: 마크다운 `### 여기에 직접 모델을 작성하세요` + 힌트(준비된 `X_train/y_train/X_test`, 로지스틱·트리 권장, `predict_proba` → `evaluate()`로 베이스라인과 비교) + **빈 코드 셀 1개**.
7. (선택) 그림 1개: 베이스라인 회차별 적중률 추이 또는 ROC → `outputs/figures/`.
8. 마지막 마크다운: **결론 프레이밍 자리** — 모델이 베이스라인을 못 넘으면 "운영 외부 의존성으로 과거 패턴만으론 한계"로 해석(계획서 결론과 연결).

**검증 요구사항**:
- 커널 재시작 후 재실행 성공, `tidy`/`predict_dataset.csv`만 의존.
- 분할 검증: `train date max < test date min` 출력.
- 베이스라인 ROC-AUC가 0.5(무작위)보다 큰지 출력(작아도 결과로 인정, 해석에 반영).

## 검증 기준

- `python -m pytest -q` 전체 통과(기존 + 신규 누수·정합 테스트).
- `06_predict.ipynb` 재실행 성공, 코드 주석 0, 한글 라벨.
- 누수 테스트 통과(피처가 미래 미사용), 시간순 분할 보장.
- 모델 셀은 **비어 있고** 사용자 작성 안내 마크다운이 있을 것.

## 작업 우선순위 요약

| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1 | `src/predict_dataset.py` + 테스트 | ~80줄 | tidy(읽기) |
| 2 | `06_predict.ipynb` 스캐폴드 | ~100줄 | 작업1 |

## 이번 범위 제외 항목

- **실제 모델 선택·학습·튜닝 — 사용자 몫**(스캐폴드만 제공, 모델 셀 비움).
- 딥러닝·앙상블·하이퍼파라미터 탐색 — 범위 밖(보조 목표, 오버엔지니어링 금지).
- Nexon Open API 등 외부 데이터 도입 — 범위 밖(본 프로젝트는 인벤 2차 자료 스코프).
- 리포트에 예측 확장 절 추가 — 사용자가 모델을 완성한 뒤 별도 Phase에서.
- `event_context`/`is_major_event` 피처 정식 도입 — 누수 가정 검토 후 후속(기본 제외).
