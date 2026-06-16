# Codex Work Packet — Phase 18 (발표용 단일 노트북 신규 + 06/07 결과표 export)

> Phase 16/17 후속. 발표 핵심이 "다음 선데이가 *무엇*인지"로 확정됐고, 파이프라인이 노트북 7개(01~07, 셀 합계 약 88개)로 커졌다. 발표 자리에서 88셀을 라이브로 넘기긴 길다. **기존 7개 파이프라인은 그대로 두고**(단계 분리·재현성은 평가 대상이라 합치지 않는다), 그 산출물(`data/processed/tidy_rewards.csv` + `outputs/figures/*.png` + 06/07이 계산한 예측 표)을 **로드만** 해서 스토리를 15~18셀로 압축하는 발표용 노트북 `notebooks/08_presentation.ipynb`를 새로 만든다. 발표 중 무거운 연산(특히 Prophet 적합 20회)을 다시 돌리지 않도록, 06/07은 이미 계산해 둔 표를 작은 CSV로 내보내고 08은 그것을 읽기만 한다.

## 작업 배경

### 사실 1 — 노트북 현황 (Claude 직접 확인)

| 노트북 | 셀 | 코드/MD | 역할 |
|---|---:|---|---|
| 01_collect | 7 | 5/2 | 수집 |
| 02_parse_clean | 12 | 9/3 | 파싱·정제(핵심) |
| 03_crossval | 12 | 6/6 | 교차검증 |
| 04_eda | 15 | 5/10 | EDA·그림 |
| 05_model | 7 | 3/4 | 회귀(보조) |
| 06_predict | 22 | 11/11 | 분류 "무엇" 예측 |
| 07_prophet | 13 | 6/7 | Prophet 비교 |

`outputs/figures/`의 그림 7개: `q1_category_share_by_year.png`, `q8_rewards_per_session.png`, `q2_cycle_by_norm.png`, `q2_cycle_hist.png`, `q3_discontinued_by_category.png`, `q3_last_seen_year.png`, `model_pred_vs_actual.png`.

### 사실 2 — 06/07이 이미 계산하는 표 (Claude 직접 확인, 발표에 쓸 것)

- **06_predict.ipynb**
  - 셀 13 `comparison_results` — 4방법(간격규칙·사전확률·로지스틱·랜덤포레스트) × `accuracy/f1/roc_auc/date_hit_rate`.
  - 셀 18 `verification_0614`(구분=게이트 전/후, 상위5_적중수, 후보수), `actual_rank_0614`(구분, reward_norm, 후보포함, 순위, 적중확률(%)).
  - 셀 20 `forecast_0621_top5`(순위, 보상, 적중확률(%)).
- **07_prophet.ipynb**
  - 셀 7 `method_comparison` — 4방법(간격규칙·사전확률·랜덤포레스트·Prophet) × `date_hit_rate`.
  - 셀 11 `comparison_0621`(순위, 랜덤포레스트_보상, 랜덤포레스트_확률(%), Prophet_보상, Prophet_yhat).

### 사실 3 — 내러티브 원본

`outputs/report/final_report.md`가 이미 완성된 발표 내러티브다(§1 개요 ~ §8 결론). 발표 노트북의 마크다운은 이 리포트의 흐름·표현을 따른다(새 해석을 지어내지 않는다). 인용할 헤드라인 수치는 리포트에 있는 값을 그대로 쓴다(예: 분석 1118행, 단종 311행/고유 71개, 회차당 보상 2017년 1.972→2025년 3.519, 중앙 주기 42일, 백테스트 date_hit_rate 랜덤포레스트 0.4493 / Prophet 0.4203).

## 제약 조건

- **기존 노트북 로직 불변**: 06/07의 모델·피처·분할·기존 셀 출력은 바꾸지 않는다. 두 노트북에는 **이미 계산된 DataFrame을 CSV로 저장하는 export 셀만 추가**한다(끝부분에). 기존 셀을 리팩토링하지 않는다.
- **08은 로드 전용**: 모델 적합·Prophet 적합·무거운 재계산 금지. `tidy_rewards.csv`에서의 가벼운 집계(`value_counts`, groupby 평균 등)와 그림·표 로드만 허용.
- `data/raw/`·`data/processed/` 불변. export 산출물은 `data/interim/`에 쓴다(파이프라인 중간 산출물 규약, 06이 이미 `data/interim/predict_dataset.csv`를 쓰는 것과 동일 위치).
- 코드 주석·docstring 금지([[no-code-comments]]). 노트북의 모든 비코드 텍스트(마크다운, `print`/`display` 라벨)는 한글.
- `python -m pytest -q` 기존 통과 유지(이번 Phase는 테스트 추가 없음 — 노트북·export만). 06/07/08 nbconvert 재실행 성공.
- **분량 상한**: 08은 코드 셀 8개 이하 + 마크다운 셀로 구성, 전체 18셀 이하. 발표용이므로 한 화면에 들어오는 표·그림 위주, 장황한 코드 금지.
- 재현성: 08은 01~07을 순서대로 실행해 산출물이 만들어진 뒤 실행되는 마지막 단계다. export CSV가 없으면 명확히 실패해도 좋다(파이프라인 순서 가정). 방어 코드로 우회하지 않는다.

## 작업 1 — 06/07에 결과표 export 셀 추가

### 1-1. `notebooks/06_predict.ipynb`

마지막 마크다운 셀(`## 결론 프레임`) **앞**에, 또는 노트북 맨 끝에 코드 셀 1개를 추가해 아래 4개 DataFrame을 `data/interim/`에 저장한다(이미 계산된 변수 그대로 사용, 재계산 금지):

```
pres_dir = ROOT / "data" / "interim"
comparison_results.to_csv(pres_dir / "pres_backtest_full.csv", index=False, encoding="utf-8")
verification_0614.to_csv(pres_dir / "pres_0614_gate.csv", index=False, encoding="utf-8")
actual_rank_0614.to_csv(pres_dir / "pres_0614_actual.csv", index=False, encoding="utf-8")
forecast_0621_top5.to_csv(pres_dir / "pres_0621_rf.csv", index=False, encoding="utf-8")
```

- 변수명은 위 사실 2 기준. 노트북 내 실제 변수명과 다르면 노트북 변수명을 따른다(중요: 새로 계산하지 말 것).
- 추가 셀은 마크다운 헤더 1줄(예: `## 발표용 표 저장`)을 동반한다.

### 1-2. `notebooks/07_prophet.ipynb`

노트북 맨 끝(또는 `## 결론 프레임` 앞)에 코드 셀 1개를 추가:

```
pres_dir = ROOT / "data" / "interim"
method_comparison.to_csv(pres_dir / "pres_method_compare.csv", index=False, encoding="utf-8")
comparison_0621.to_csv(pres_dir / "pres_0621_compare.csv", index=False, encoding="utf-8")
```

- 마찬가지로 마크다운 헤더 1줄 동반, 재계산 금지.

**검증**: 06/07 nbconvert 재실행 후 위 6개 CSV가 `data/interim/`에 생성되고, 내용이 노트북 화면 출력과 일치.

## 작업 2 — `notebooks/08_presentation.ipynb` 신규 (발표용 단일 노트북)

우리식 스타일 유지(한글 마크다운 셀 + 최소 코드 셀, 코드 주석 0). 아래 셀 구성을 권장(마크다운은 리포트 흐름 따름):

1. **(MD) 표지** — 제목 "선데이메이플 보상 패턴 분석 · 다음 선데이는 무엇인가", 한 줄 문제 정의와 데이터 범위(2017-03 ~ 2026-06, 분석 1118행).
2. **(MD) 1. 데이터와 파이프라인** — 수집→파싱→교차검증→EDA→예측 5단계, tidy 스키마 한 줄 요약, "이 발표 노트북은 산출물을 로드만 한다" 명시.
3. **(CODE) 로드** — ROOT 탐색(06/07과 동일 패턴), `tidy = pd.read_csv(ROOT/"data"/"processed"/"tidy_rewards.csv", parse_dates=["date"])`, 헤드라인 수치 dict 출력(전체행/분석행/회차수/날짜범위). `IPython.display.Image` import.
4. **(MD) 2. 데이터 신뢰성** — 교차검증 일치율 0.726, 스팟체크 3회차 결과 한 줄(리포트 §3 요약).
5. **(MD) 3. EDA 하이라이트** — 아래 그림들이 답하는 질문 한 줄씩.
6. **(CODE) EDA 그림 표시** — `outputs/figures/`의 핵심 그림을 `Image(...)`로 표시: `q1_category_share_by_year.png`, `q8_rewards_per_session.png`, `q2_cycle_by_norm.png`, `q3_discontinued_by_category.png`. (그림 4개로 압축; 나머지 q2_cycle_hist·q3_last_seen·model_pred는 발표 분량상 생략하되 부록 노트북에 있다고 마크다운에 한 줄.)
7. **(CODE) EDA 헤드라인 집계(가벼운 라이브)** — tidy에서 카테고리 분포(`value_counts`)와 연도별 회차당 보상 수(groupby 평균) 정도만 계산해 표로. 무거운 연산 금지.
8. **(MD) 4. 다음 선데이 예측 — 방법** — 분류기(경과일·주기 피처)와 Prophet(28일 시즈널리티) 두 방법을 같은 date_hit_rate로 비교한다는 프레임.
9. **(CODE) 백테스트 비교표 로드** — `pres_method_compare.csv` 로드해 display(4방법 date_hit_rate). 랜덤포레스트 0.4493 최고 한 줄 마크다운은 셀 8 또는 다음 MD에서.
10. **(MD) 5. 이번 주(2026-06-14) 예측 vs 실제** — 단종 보상이 상위에 섞이던 버그와 재증 게이트, 실제 보상(몬스터파크_경험치·선물_기타지급).
11. **(CODE) 06-14 검증 표 로드** — `pres_0614_gate.csv`(게이트 전/후 상위5 적중수)와 `pres_0614_actual.csv`(실제 보상 순위) display.
12. **(MD) 6. 다음 주(2026-06-21) 예보** — 두 방법 나란히, 확률은 점수의 백분율이지 보정 확률이 아님, 상위 5는 검토 우선순위지 확정 아님.
13. **(CODE) 06-21 예보 비교표 로드** — `pres_0621_compare.csv` display(RF vs Prophet 1~5위).
14. **(MD) 7. 결론** — 회차당 보상 증가·강화/성장 축, 단종 집중(성장·사냥효율·수집기타), 두 예측 방법 단일 승자 없음·둘 다 단종 게이트 필요(리포트 §8 요약).

- 그림 경로는 ROOT 기반(`ROOT/"outputs"/"figures"/...`).
- 표 CSV는 `ROOT/"data"/"interim"/...`에서 로드.
- 코드 셀은 로드·display 위주로 짧게. `print` 라벨은 한글.

**검증**: 08 nbconvert 재실행 성공(06/07이 먼저 실행돼 CSV가 있는 상태 가정), 표·그림이 정상 렌더, 전체 18셀 이하·코드 주석 0·한글 텍스트.

## 작업 3 — 없음 (리포트·HTML·requirements 변경 없음)

이번 Phase는 발표 노트북과 결과 export에 한정한다. `final_report.md`/`build_html.py`/`requirements.txt`/`src/`/`tests/`는 건드리지 않는다.

## 검증 기준

- `python -m pytest -q`: 기존 테스트 그대로 통과(추가·변경 없음).
- `python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb` 및 `07_prophet.ipynb` 성공 → `data/interim/pres_*.csv` 6개 생성.
- `python -m jupyter nbconvert --to notebook --execute notebooks/08_presentation.ipynb` 성공(검증 산출물 삭제).
- 08의 표 수치 = 06/07 실제 출력과 일치(전재 없이 CSV 로드이므로 자동 일치, 육안 확인).
- 08 전체 셀 18 이하, 코드 셀 8 이하, 코드 주석 0, 비코드 텍스트 한글.
- `data/raw/`·`data/processed/` 불변, 기존 노트북 모델 로직·기존 셀 출력 불변.

## 작업 우선순위 요약

| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1-1 | `06_predict.ipynb` export 셀 +1 | ~6줄 | 기존 변수 |
| 1-2 | `07_prophet.ipynb` export 셀 +1 | ~3줄 | 기존 변수 |
| 2 | `08_presentation.ipynb` 신규 | 코드 6~8 + MD, 18셀 이하 | 작업 1 산출 CSV, figures |

## 이번 범위 제외 항목

- 7개 파이프라인 노트북 통합 — **하지 않음**. 단계 분리·재현성이 평가 대상이라 유지하고, 발표 압축은 별도 노트북으로 해결.
- 슬라이드(PPT)·발표 스크립트 생성 — 이번 범위 아님.
- 08에서의 모델 라이브 재계산 — 제외(로드 전용, 발표 속도 우선).
- 그림 7개 전부 표시 — 제외(핵심 4개로 압축, 나머지는 부록 노트북 참조 표기).
- 리포트/HTML/requirements 수정 — 제외(변경 없음).
