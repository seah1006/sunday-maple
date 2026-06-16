# Codex Work Packet — Phase 17 (Prophet 재등장-주기 방식 "무엇" 예측 + 분류기와 공정 비교)

> Phase 16 후속·의존. 발표 핵심이 "다음 선데이가 *무엇*인지"로 확정됐고, 강의(C:\Jupyter unit 8 "주식 시세 미래 예측", Prophet)의 시계열 예측 기법을 우리 문제에 적용한다. Phase 16이 분류기로 "무엇"을 예측한다면, Phase 17은 **Prophet 재등장-주기 모델**로 같은 질문을 풀고, **동일 게이트·동일 date_hit_rate로 공정 비교**한다. 두 방법 중 어느 것도 압도하지 않으며 둘 다 단종 게이트가 필요하다는 것이 이번 분석의 결론(아래 PoC 사실).

## 작업 배경

### 사실 1 — Prophet PoC (Claude 직접 실행, prophet 1.3.0)

각 보상의 주(일요일)별 등장 0/1 시계열에 Prophet(`yearly_seasonality=True`, weekly/daily off, `add_seasonality('cycle28', period=28, fourier_order=5)`)을 적합하고 2026-06-21 `yhat`로 순위:

| 순위 | 보상 | 등장 | 마지막 | yhat | 비고 |
|---:|---|---:|---|---:|---|
| 1 | 몬스터파크_경험치 | 82 | 2026-05-24 | 0.370 | **06-14 실제 정답** (분류기는 9위로 놓침) |
| 2 | 룬_경험치버프 | 88 | 2026-06-07 | 0.344 | 활성 |
| 3 | 현상금_경험치 | 77 | 2025-06-08 | 0.321 | **단종인데 상위** |
| 4 | 불꽃늑대_경험치 | 74 | 2025-06-08 | 0.310 | **단종인데 상위** |
| 5 | 스타포스_1+1강화 | 42 | 2026-01-11 | 0.308 | 단종(도메인) |
| 6 | 콤보킬_경험치 | 87 | 2026-06-07 | 0.307 | 활성 |
| 7 | 몬스터컬렉션 | 40 | 2026-02-22 | 0.109 | |
| 8 | 스타포스_성공확률 | 55 | 2025-07-20 | 0.029 | Prophet이 잘 눌렀음 |

**해석(정직)**: Prophet은 (a) 몬스터파크(06-14 실제)를 1위로 올려 분류기보다 나은 면이 있고, (b) 스타포스_성공확률(11개월 휴면)은 잘 눌렀지만, (c) **현상금·불꽃늑대(단종)는 강한 28일 시즈널리티가 학습돼 12개월 쉬어도 추세가 안 꺾여 여전히 3·4위로 추천**한다. 즉 Prophet도 단종 문제를 못 피하므로 **Phase 16과 동일 게이트가 필요**하다. 두 방법은 상호 보완적이며 어느 쪽도 압도하지 않는다 — 이 비교 자체가 발표 소재다.

### 사실 2 — 환경·데이터
- `prophet` 1.3.0 설치 확인. cmdstanpy 로그 다수 출력 → 노트북에서 억제 필요.
- 관측 회차 459개(2017-03-12 ~ 2026-06-07), 일요일 단위. 보상별 0/1 시계열 구성 가능.
- 분류기 백테스트 date_hit_rate = 0.449(랜덤포레스트, Phase 14/16). Prophet도 **같은 분할·같은 지표**로 비교해야 공정.

## 제약 조건

- **Phase 16 선행 필수**: 재증 게이트(`recency_gate_days`)·도메인 단종 목록(`DOMAIN_DISCONTINUED`)은 Phase 16에서 `src/predict_dataset.py`에 구현된 것을 **재사용**한다. 중복 정의 금지.
- `data/raw/` 불변. 06-14 보조 관측은 Phase 16에서 만든 `data/interim/manual_obs_20260614.csv`를 재사용.
- 코드 주석·docstring 금지([[no-code-comments]]). 비코드 텍스트 한글.
- `python -m pytest -q` 기존 통과 유지 + 신규 테스트 추가 후 전체 통과. **Prophet 적합은 느리고 외부 의존**이므로 단위 테스트는 결정적 헬퍼(시계열 구성·게이트·yhat 순위)만 검증하고, 실제 Prophet 적합은 테스트에서 1회 스모크 이하로 최소화하거나 제외한다.
- **누수 금지**: Prophet 적합·백테스트는 기준일(추론은 target_date, 백테스트는 각 test 날짜) 미만 이력만 학습에 사용. 백테스트는 train(<2025-01-01)에서 적합 후 test 구간 yhat 예측(미래 정보 미사용).
- **사후조정 금지**: 게이트 임계값·시즈널리티 설정은 06-14/06-21 정답을 보고 조정하지 않는다. PoC 설정(period=28, fourier_order=5, yearly on)을 기본으로 고정하고, 변경 시 근거를 노트북에 명시.
- 모델 비교는 **정직하게**: Prophet이 분류기보다 나쁘게 나와도 그대로 보고. 결론을 "Prophet 우월"로 과장하지 않는다.

## 작업 1 — Prophet 재등장-주기 모듈 (`src/prophet_cycle.py` 신규)

**목표 함수(주석/독스트링 없이)**:
- `build_weekly_series(tidy, reward_norm, as_of)` → 기준일 미만 eligible 일요일 인덱스에 대한 0/1 `DataFrame(ds, y)`.
- `fit_predict_reward(series_df, target_dates)` → Prophet(PoC 설정, `uncertainty_samples=0`으로 결정적·고속) 적합 후 `target_dates`의 `yhat` 반환.
- `rank_candidates(tidy, candidates, as_of, target_date, gate_fn)` → 후보별 yhat 계산 → **Phase 16 게이트 함수 적용** → yhat 내림차순 순위 `DataFrame(reward_norm, yhat, rank)`.
- 후보 universe·게이트는 Phase 16 `predict_dataset`의 것을 import해 재사용(빈도 top-N 후보 → 게이트 → Prophet 순위).

**구현 전략**: 후보 top-N(기본 20)만 Prophet 적합(런타임 상한). cmdstanpy 로깅은 모듈 import 시 억제하지 말고 호출부(노트북)에서 억제. yhat은 확률이 아니라 상대 강도 점수임을 노트북·리포트에 명시.

**검증(`tests/test_prophet_cycle.py` 신규)**:
- `build_weekly_series`가 기준일 미만만 포함하고 등장일에 1, 그 외 0인지(누수 금지 케이스 포함).
- `rank_candidates`가 게이트로 단종 보상(예: 마지막 등장 371일 전, 또는 `DOMAIN_DISCONTINUED`)을 순위에서 제외하는지 — yhat은 더미/모킹으로 주입해 Prophet 적합 없이 검증.
- (선택) Prophet 적합 1회 스모크: 작은 시리즈로 `fit_predict_reward`가 길이 맞는 yhat 반환.

## 작업 2 — Prophet 공정 백테스트 + "무엇" 예측 (`notebooks/07_prophet.ipynb` 신규)

**목표**: 분류기와 같은 분할·지표로 Prophet을 평가하고 06-14/06-21을 예측한다. 우리식 노트북 스타일(한글 마크다운 셀 + 코드 셀, 주석 0) 유지.

### 2-1. Prophet 백테스트 (date_hit_rate 공정 비교)
- 후보별 Prophet을 **train(<2025-01-01)** 에서 적합 → test 일요일(2025-01-05~2026-06-07) 전체 `yhat` 예측.
- 각 test 날짜에서 게이트 적용 후 yhat 상위 k를 뽑아 실제 등장과 대조 → **date_hit_rate** 계산(분류기와 동일 정의·동일 k).
- 분류기 0.449·베이스라인과 한 표로 비교. 결과 그대로 보고.
- 런타임 상한: 후보 top-N개만 적합(N=20). 적합 1회/보상(test 전체를 한 번에 예측)이라 총 ~20회 적합.

### 2-2. 06-14 검증 (Prophet)
- Prophet을 06-07까지로 적합 → 06-14 yhat 순위(게이트 전·후) → 실제 {몬스터파크_경험치, 선물_기타지급}와 대조. 분류기 06-14 결과와 나란히 표시. Prophet은 몬스터파크를 상위로 올렸는지, 선물류는 못 잡는지 실제값으로 보고.

### 2-3. 06-21 예보 (Prophet, 게이트 적용)
- 06-14 보조 관측 포함해 06-14까지로 적합 → 06-21 yhat 순위 상위 5(게이트 적용). 분류기 06-21 예보와 **나란히 비교표**(순위·보상·점수). 두 방법 합의/불일치 표시.

### 2-4. 마크다운
- Prophet이 무엇을 하는지(보상별 등장 시계열의 추세+28일 시즈널리티), yhat이 확률 아님, 단종을 못 거르는 이유(끈질긴 시즈널리티)와 게이트 필요성, 두 방법 비교 결론(어느 쪽도 압도 못 함)을 한글로.

**검증**: nbconvert 재실행 성공(cmdstanpy 로그 억제), 06-21 Prophet 후보에 현상금·불꽃늑대·스타포스1+1강화·(게이트 임계 초과)스타포스성공확률 부재, 비교표가 실제 산출값과 일치, 코드 주석 0.

## 작업 3 — 리포트 비교 절 + HTML 재생성

**수정 대상**: `outputs/report/final_report.md` §6(Phase 16에서 재작성된 절)에 **Prophet 비교 하위 절** 추가, 이후 `outputs/report/build_html.py` 재실행.

**변경 목표**:
- "두 방법으로 무엇을 예측한다" 프레임: 분류기(경과일·주기 피처) vs Prophet(시계열 시즈널리티).
- date_hit_rate 공정 비교표(분류기 vs Prophet vs 베이스라인).
- 06-14 검증·06-21 예보 양쪽에서 두 방법 비교표.
- 정직한 결론: Prophet은 몬스터파크(06-14 실제)를 더 잘 잡았으나 단종은 못 거름 → 둘 다 게이트 필요, 단일 승자 없음.
- (선택) 그림 1개: Prophet 한 보상의 forecast/components 또는 두 방법 date_hit_rate 막대. figure 상한 +1, 링크 검증.
- 전재 수치 = 노트북 출력 일치. HTML 재생성, 기존 그림 내장 유지.

## 작업 4 — 의존성 기록 (`requirements.txt`)
- `prophet` 추가(설치 버전 1.3.0). 기존 의존성 변경 금지.

## 검증 기준
- `python -m pytest -q`: 기존 + 신규 테스트 통과.
- `python -m jupyter nbconvert --to notebook --execute notebooks/07_prophet.ipynb` 성공(검증 산출물 삭제).
- Prophet 06-21 순위에 단종 보상(현상금·불꽃늑대·스타포스1+1강화) 부재.
- date_hit_rate 비교표가 노트북 실제 출력과 일치.
- 리포트·HTML 재생성, 코드 주석 0, 한글 텍스트, `data/raw/` 불변.

## 작업 우선순위 요약

| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1 | `src/prophet_cycle.py` + 테스트 | ~60–90줄 | Phase 16 게이트 |
| 2 | `notebooks/07_prophet.ipynb` 백테스트+06-14검증+06-21예보 | 코드 셀 6~10 + md | 작업 1, Phase 16 |
| 3 | `final_report.md` Prophet 비교 절 + HTML | ~40줄/스크립트 | 작업 2 |
| 4 | `requirements.txt` prophet 추가 | 1줄 | - |

## 이번 범위 제외 항목
- Prophet 하이퍼파라미터 탐색(fourier_order·period 스윕) — 제외. PoC 고정값 사용, 사후조정 금지.
- 회차당 보상 수(수치 추세) Prophet 예측 — **사용자 결정으로 제외**(핵심은 "무엇"이지 "몇 개"가 아님).
- 보상별 불확실 구간(yhat_lower/upper) 시각화 — 제외, 단순함 우선.
- 분류기·Prophet 앙상블 — 보류(비교까지가 이번 범위).
- 회귀(05_model) 확장 — 제외.
