# Codex Work Packet — Phase 21 (파이프라인 모듈화 + 사이트용 JSON 내보내기)

> Phase 20 후속. 프로젝트가 발표용 분석에서 **포트폴리오용 정적 웹사이트**로 전환됐다(2026-10-24, `docs/website_roadmap.md`). 사이트는 Python이 만든 JSON을 React가 읽는 구조다. 이번 Phase는 노트북에 흩어진 raw→tidy→학습→예보 흐름을 `src` 모듈로 옮기고, 기준일을 인자로 받게 바꾼 뒤, 사이트가 읽을 JSON을 만드는 CLI를 추가한다. **프론트엔드와 신규 회차 수집은 이번 범위가 아니다.**

## 작업 배경

### 사실 1 — 발표 노트북 삭제 (Claude, 사용자 승인)

- `notebooks/08_presentation.ipynb`와 `outputs/report/presentation_script.html`을 `git rm`으로 삭제했다(커밋 전 작업 트리 상태).
- 08은 raw→tidy→백테스트→06-14 검증→06-21 예보를 **한 번에 실행하는 유일한 코드**였다. 이번 작업의 기준 코드이며, 삭제 전 내용은 `git show 49f7626:notebooks/08_presentation.ipynb`로 볼 수 있다.
- 08에서 옮길 셀:
  - 셀 4: `parse_by_type`/`parse_by_date` → `is_special`, `time_limited` 로컬 함수 → `normalize_reward`, `categorize`, `extract_magnitude`, `compute_cycle_days`, `merge_is_discontinued` → 14컬럼 tidy. `is_future = date > TODAY`.
  - 셀 7: `build_prediction_frame(tidy, candidate_cutoff=SPLIT_CUTOFF)` → 시간 분할 → `pd.get_dummies(..., columns=["category"], dummy_na=True).fillna(-1)` → 간격규칙·사전확률·로지스틱·랜덤포레스트(`n_estimators=300, class_weight="balanced", random_state=42`) 평가(`evaluate`의 `date_hit_rate`) + Prophet 백테스트 루프.
  - 셀 8: `predict_classifier(tidy_source, target_date, gate)` (`build_inference_frame` + `X_all.columns`로 reindex + `tree_model.predict_proba`).
  - 셀 9: 수동 관측을 tidy에 붙이는 코드(`category_lookup` 최빈값, `is_future=False`, `no_event_week=False`) + 06-21 RF/Prophet 예보.

### 사실 2 — 고정 기준일

- 08과 06/07 노트북은 `TODAY = 2026-06-10`, `SPLIT_CUTOFF = 2025-01-01`, `RANDOM_SEED = 42`를 상수로 쓴다. 사이트는 매주 기준일이 바뀌므로 `as_of`/`target_date`를 인자로 받아야 한다. `SPLIT_CUTOFF`와 시드는 이번 Phase에서 **그대로 유지**한다(재학습 정책은 미결정, 로드맵 §5-2).

### 사실 3 — 데이터 현황 (Claude 2026-10-24 확인)

- 인벤 원글은 2026-06-07 회차 이후 갱신이 멈췄다. 이번 Phase 입력은 기존 `data/raw/view_by_type.txt`, `data/raw/view_by_date.txt`, `data/interim/manual_obs_20260614.csv`뿐이다. 재크롤링 금지.
- `data/processed/tidy_rewards.csv` 헤더: `date,reward_raw,reward_trailing,reward_norm,category,reward_magnitude,event_context,is_major_event,is_special,time_limited,is_discontinued,is_future,no_event_week,cycle_days` (1160행).
- 이 PC 실행 환경: `py` 런처(Python 3.13). 명령은 `py -m pytest -q`, `py -m src.site_data` 형식.

## 제약 조건

- `data/raw/`, `data/processed/`, `data/interim/manual_obs_20260614.csv` 수정 금지.
- 노트북 01~07 수정 금지. 기존 `src` 함수(`parse`, `normalize`, `features`, `predict_dataset`, `prophet_cycle`)의 시그니처와 동작 변경 금지. 새 모듈에서 import해서 재사용한다.
- 기존 51개 테스트 통과 유지.
- **수치 불변** (Phase 19/20과 동일해야 함):
  - tidy 전체 1160행, 분석 1118행, 14컬럼, `(date, reward_raw)` 중복 0, 비일요일 11행
  - 백테스트 `date_hit_rate`: 간격규칙 0.3478, 사전확률 0.3623, 로지스틱 0.3913, 랜덤포레스트 0.4493, Prophet 0.4203
  - 06-21 예보(06-14 수동 관측 포함): RF 1위 몬스터컬렉션 41.7%, Prophet 1위 몬스터파크_경험치 yhat 0.402. 현상금_경험치, 불꽃늑대_경험치, 스타포스_1+1강화, 스타포스_성공확률은 후보에 없음
- 코드 주석·docstring 금지(기존 규칙). 새 의존성 추가 금지(`requirements.txt` 불변).
- JSON 키는 영어 snake_case. 사람이 읽는 라벨 문자열은 한글.

## 작업 1 — `src/build_tidy.py` (raw → tidy)

- 새 파일. 08 셀 4 로직을 옮긴다.
- 함수:
  - `load_raw_views(raw_dir: str | Path = "data/raw") -> tuple[str, str]` : `view_by_type.txt`, `view_by_date.txt`를 UTF-8로 읽어 반환.
  - `build_tidy(by_type_text: str, by_date_text: str, as_of: pd.Timestamp | str) -> tuple[pd.DataFrame, pd.DataFrame]` : `(tidy, parsed_by_type)` 반환. `is_future = date > as_of`. 컬럼 순서는 위 14컬럼과 동일, `date`는 datetime.
  - `is_special`, `time_limited`는 모듈 내부 함수(`_is_special`, `_time_limited`)로 옮긴다. 로직 변경 금지.
- 검증: `tests/test_build_tidy.py`
  - `test_build_tidy_matches_processed_counts`: 실제 raw + `as_of="2026-06-10"` → 1160행, 14컬럼, 분석 1118행, `(date, reward_raw)` 중복 0, 비일요일 11행.
  - `test_build_tidy_matches_processed_csv`: `data/processed/tidy_rewards.csv`와 `date, reward_raw, reward_norm, category, cycle_days, is_discontinued` 컬럼 값이 같다(결측 비교 포함). **불일치가 나오면 고치지 말고 handoff에 차이를 보고**한다.
  - `test_is_future_follows_as_of`: `as_of`를 2026-06-01로 주면 06-07 행의 `is_future`가 True.

## 작업 2 — `src/observations.py` (수동/추가 관측 결합)

- 새 파일. 08 셀 9 앞부분을 옮긴다.
- `load_manual_observations(path: str | Path = "data/interim/manual_obs_20260614.csv") -> pd.DataFrame`
- `append_observations(tidy: pd.DataFrame, observations: pd.DataFrame) -> pd.DataFrame` : `category`는 tidy의 `reward_norm`별 최빈 카테고리로 채우고, `is_future=False`, `no_event_week=False`. 08과 같은 방식(`pd.concat(..., ignore_index=True, sort=False)`).
- Phase 23에서 공식 공지 관측 CSV가 같은 함수로 들어올 예정이므로, 입력은 최소 `date`, `reward_norm` 컬럼만 요구한다(`source`, `reward_raw`는 있으면 보존).
- 검증: `tests/test_observations.py` — 합성 tidy 3행 + 관측 1행으로 행 수 +1, 카테고리 채움, 플래그 값 확인.

## 작업 3 — `src/forecast.py` (학습·백테스트·예보)

- 새 파일. 08 셀 7~9의 모델 부분을 옮긴다. 상수 `SPLIT_CUTOFF = pd.Timestamp("2025-01-01")`, `RANDOM_SEED = 42`, `FEATURE_COLUMNS`는 `src.predict_dataset.FEATURE_COLUMNS` 재사용.
- 함수(이름은 제안이며, 더 단순한 구성이 있으면 handoff에 근거와 함께 설명):
  - `train_classifier(tidy, split_cutoff=SPLIT_CUTOFF, seed=RANDOM_SEED)` → `ClassifierBundle`(dataclass: `model`, `feature_columns`(dummies 후 컬럼 목록), `prediction_frame`). 08과 같이 `split_cutoff` 이전 날짜로 학습.
  - `backtest(tidy, bundle, split_cutoff=SPLIT_CUTOFF, seed=RANDOM_SEED, include_prophet=True)` → `(metrics: pd.DataFrame, per_date: pd.DataFrame)`
    - `metrics`: 방법별 `accuracy, f1, roc_auc, date_hit_rate` (Prophet은 `date_hit_rate`만).
    - `per_date`: test 날짜별 `date`, `actual`(후보 안의 실제 보상 목록), `rf_top`(RF 점수 상위 k, k=후보 안 실제 보상 수), `rf_hit`(0/1/NaN). 사이트의 "적중 기록" 화면용. 정의는 08의 `date_hit`과 같아야 한다.
  - `predict_next(tidy, bundle, target_date, gate=True)` → 08 `predict_classifier`와 같은 표(`date, reward_norm, score, rank, score_pct`).
  - `prophet_next(tidy, target_date, split_cutoff=SPLIT_CUTOFF)` → `rank_candidates` 결과(후보 = `split_cutoff` 이전 상위 20). 08 셀 9와 같이 `as_of = target_date`.
  - `next_sunday_after(date)` → 주어진 날짜 **다음** 일요일.
- 검증: `tests/test_forecast.py`
  - `test_next_sunday_after`: 2026-06-14(일) → 2026-06-21, 2026-06-17(수) → 2026-06-21.
  - `test_predict_next_matches_phase20_forecast`: 실제 raw + 06-14 수동 관측 → 06-21 RF 1위 몬스터컬렉션, `score_pct` 41.7, 제외 4종 미포함. (RF 300트리 학습이라 수 초 걸려도 허용. Prophet은 테스트에서 제외)
  - `test_backtest_rf_date_hit_rate`: `include_prophet=False`로 RF 0.4493, 간격규칙 0.3478, 사전확률 0.3623, 로지스틱 0.3913 (소수 4자리 반올림 비교).

## 작업 4 — `src/site_data.py` (사이트용 JSON 내보내기 CLI)

- 새 파일. `py -m src.site_data [--out data/site] [--target-date YYYY-MM-DD] [--skip-prophet]`.
- 흐름: raw 로드 → `build_tidy(as_of=마지막 관측일)` → 수동 관측 결합 → 학습 → 백테스트 → 예보 → JSON 쓰기.
  - `data_through` = 결합된 데이터에서 보상이 있는 마지막 날짜(현재 2026-06-14).
  - `--target-date` 기본값 = `next_sunday_after(data_through)` (현재 2026-06-21).
  - `build_tidy`의 `as_of`는 원본 raw 기준 마지막 실제 회차 이후 빈 블록을 미래로 처리하도록 정한다. 현재 데이터에서는 `2026-06-10`과 같은 결과(1160/1118)가 나와야 한다. 정하는 규칙을 handoff에 설명.
- 출력 파일 (`ensure_ascii=False`, `indent=2`, UTF-8). 날짜는 `YYYY-MM-DD` 문자열, 점수는 소수 3자리, NaN은 `null`.

`meta.json`
```json
{
  "generated_at": "ISO8601 UTC",
  "data_through": "2026-06-14",
  "target_date": "2026-06-21",
  "sources": [
    {"name": "인벤 역대 썬데이메이플 정리", "url": "https://www.inven.co.kr/board/maple/2304/20563", "fetched_at": "<raw meta의 fetched_at>"},
    {"name": "수동 관측(공식 공지 확인)", "path": "data/interim/manual_obs_20260614.csv"}
  ],
  "split_cutoff": "2025-01-01",
  "random_seed": 42
}
```

`forecast.json`
```json
{
  "target_date": "2026-06-21",
  "classifier": [
    {"rank": 1, "reward_norm": "몬스터컬렉션", "category": "...", "score": 0.417, "days_since_last": 0, "last_seen": "YYYY-MM-DD"}
  ],
  "prophet": [
    {"rank": 1, "reward_norm": "몬스터파크_경험치", "yhat": 0.402}
  ],
  "excluded": [
    {"reward_norm": "현상금_경험치", "reason": "recency_gate"},
    {"reward_norm": "스타포스_1+1강화", "reason": "domain_discontinued"}
  ]
}
```
- `classifier`는 게이트 후 전체 후보(06-14 기준 10개였음, 06-21 개수는 handoff에 기록), `excluded`는 원 후보 20개 중 게이트로 빠진 것과 사유.
- `--skip-prophet`이면 `"prophet": null`.

`backtest.json`
```json
{
  "split_cutoff": "2025-01-01",
  "metrics": [{"method": "random_forest", "label": "랜덤포레스트", "accuracy": 0.861, "f1": 0.126, "roc_auc": 0.735, "date_hit_rate": 0.449}],
  "per_date": [{"date": "2025-01-05", "actual": ["..."], "predicted": ["..."], "hit": 1}]
}
```
- `method` 값: `gap_rule`, `prior_rate`, `logistic`, `random_forest`, `prophet`. 라벨: 간격규칙, 사전확률, 로지스틱, 랜덤포레스트, Prophet.

`history.json`
```json
[
  {"date": "2026-06-07", "event_context": "메이플 어택!", "is_special": false,
   "rewards": [{"reward_raw": "...", "reward_norm": "룬_경험치버프", "category": "성장"}]}
]
```
- 분석 대상 행(보상 있음, 미래 아님) + 수동 관측을 날짜별로 묶고 날짜 내림차순. 수동 관측의 `reward_raw`가 없으면 `null`.

`rewards.json`
```json
[
  {"reward_norm": "몬스터컬렉션", "category": "...", "appearances": 0, "first_seen": "YYYY-MM-DD", "last_seen": "YYYY-MM-DD", "median_cycle_days": 42.0, "is_discontinued": false}
]
```
- `is_discontinued`는 해당 `reward_norm` 행 중 하나라도 True면 True로 하되, 집계 규칙을 handoff에 적는다.

- 검증: `tests/test_site_data.py` — 임시 디렉터리에 `--skip-prophet`으로 실행해 5개 파일 생성, 필수 키 존재, `forecast.json.target_date == "2026-06-21"`, `classifier[0].reward_norm == "몬스터컬렉션"`, `history.json` 첫 날짜 `2026-06-14`.

## 검증 기준

1. `py -m pytest -q` : 기존 51개 + 신규 테스트 모두 통과.
2. `py -m src.site_data --out data/site` (Prophet 포함) 실행 성공. handoff에 다음 값 기록:
   - `meta.data_through`, `meta.target_date`
   - `forecast.classifier` 상위 5 (06-21: 몬스터컬렉션 41.7, 스타포스_비용할인 39.3, 주문의흔적_비용할인 36.7, 어빌리티_재설정할인 34.3, 엘리트몬스터_증가 27.7)
   - `forecast.prophet` 1위 몬스터파크_경험치 0.402
   - `backtest.metrics`의 `date_hit_rate` 5개
   - 각 JSON 파일 크기
3. `git status`로 `data/raw/`, `data/processed/`, `notebooks/` 변경 없음 확인.
4. 실행 시간(Prophet 포함/제외)을 기록. 주간 Actions에서 돌릴 수 있는 수준인지 판단 자료.

## 작업 우선순위 요약

| 작업 | 대상 | 예상 규모 | 의존 |
|---|---|---|---|
| 1 | `src/build_tidy.py` + 테스트 | 약 80줄 + 테스트 40줄 | - |
| 2 | `src/observations.py` + 테스트 | 약 30줄 + 테스트 20줄 | 1 |
| 3 | `src/forecast.py` + 테스트 | 약 150줄 + 테스트 40줄 | 1, 2 |
| 4 | `src/site_data.py` + 테스트 + `data/site/*.json` | 약 150줄 + 테스트 30줄 | 1~3 |

## 이번 범위 제외 항목

- 프론트엔드(`web/`) — Phase 22.
- 신규 회차 수집(공식 공지 탐지·이미지 보상 추출·백필), 정규화 사전 신규 보상 추가 — Phase 23. 추출 방식은 사용자 결정 대기.
- GitHub Actions, 배포 — Phase 24.
- 모델 재학습 정책 변경, 하이퍼파라미터·게이트 변경 — 미결정(로드맵 §5-2).
- 보상 표시명 사전 — Phase 22에서 결정.
- 01~07 노트북을 새 모듈로 바꾸는 리팩터링 — 하지 않는다(재현 기록으로 유지).
