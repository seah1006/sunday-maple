# Codex Work Packet — Phase 19 (발표 노트북을 강의식 자족형 단일 흐름으로 재작성)

> Phase 18 후속. 사용자가 발표 노트북을 강의(C:\Jupyter) 노트북들과 같은 흐름 — **데이터 수집 → 데이터 전처리 → 시각화 → 예측** — 으로, 한 노트북 안에서 **라이브로 실행**되게 바꾸길 원한다(사용자 결정). 위치는 프로젝트 `notebooks/`에 유지한다(상대경로·그림·데이터 그대로 동작). 따라서 Phase 18에서 만든 "로드 전용" `08_presentation.ipynb`를 **자족형 강의식 노트북으로 전면 재작성**하고, 그 노트북에만 필요했던 06/07의 발표용 export 셀과 `pres_*.csv`는 더 이상 쓰지 않으므로 정리한다.

## 작업 배경

### 사실 1 — 강의 노트북 구조 (Claude 직접 확인, C:\Jupyter)

- unit 3·6·8 모두 **코드 셀 100%, 마크다운 0, 주석 0**. 한 노트북이 `pd.read_csv(...)`(수집/로드) → groupby·filter·join(전처리) → `folium`·`.plot.line()`(시각화) → Prophet `make_future_dataframe`/`predict`/`plot`(예측)을 **선형으로 직접 실행**한다. unit 8 "주식 시세 미래 예측"이 우리 Prophet과 정확히 대응한다.
- 즉 강의식은 중간 산출물을 로드하는 게 아니라 한 노트북이 수집~예측을 라이브 수행하는 자족형이다. **다만 우리 프로젝트는 마크다운 한글 서술을 유지**(발표 평가 기준)하므로, 코드 100%가 아니라 "강의식 4단계 라이브 흐름 + 간결한 한글 마크다운 섹션"으로 한다.

### 사실 2 — 02_parse_clean의 raw→tidy 생성 시퀀스 (재사용 대상, Claude 직접 확인)

`notebooks/02_parse_clean.ipynb`가 tidy를 만드는 핵심 코드는 셀 1~5이며 전부 `src/` 함수를 호출한다(빠름, Prophet·모델 없음):

```
from src.features import compute_cycle_days, merge_is_discontinued
from src.normalize import categorize, extract_magnitude, normalize_reward
from src.parse import parse_by_type, parse_by_date

by_type_text = (raw_dir / 'view_by_type.txt').read_text(encoding='utf-8')
by_date_text = (raw_dir / 'view_by_date.txt').read_text(encoding='utf-8')
by_type_records = parse_by_type(by_type_text)
by_date_records = parse_by_date(by_date_text)
parsed_by_type = pd.DataFrame(by_type_records, columns=['reward_raw','date','stated_cycle_days','is_discontinued','trailing'])
parsed_by_date = pd.DataFrame(by_date_records, columns=['date','event_context','is_major_event','no_event_week','reward_raw','reward_trailing'])
# is_special / time_limited / is_future(=date > TODAY) 파생  → tidy_prenorm
# reward_norm/category/reward_magnitude/cycle_days/is_discontinued 부여 → tidy_rewards (14컬럼)
```

- `TODAY = pd.Timestamp('2026-06-10')`가 `is_future`를 가른다. **08도 동일 TODAY를 써야** 02와 같은 tidy(전체 1160행, 분석 1118행, 단종 고유 71, 비일요일 11)가 재현된다.
- 02 셀 8은 약 40줄짜리 무결성 점검 출력이다. **발표 노트북에는 이 전체를 복제하지 말 것** — 핵심 수치 몇 개(전체/분석 행, 단종 고유, (date,reward_raw) 중복 0, 비일요일 11)만 간결히 보여준다.
- 02 셀 3의 `is_special`/`time_limited` 같은 작은 파생 함수는 08에서 동일하게 인라인 정의해도 되고(주석 없이), 핵심은 src 호출 시퀀스 재사용.

### 사실 3 — 예측 단계 재사용 (Claude 직접 확인)

- 분류기 경로: `src.predict_dataset`의 `build_prediction_frame`/`build_inference_frame`/`gate_candidates` + 06_predict의 학습·평가·06-14검증·06-21예보 로직.
- Prophet 경로: `src.prophet_cycle`의 `build_weekly_series`/`fit_predict_reward`/`rank_candidates` + 07_prophet의 백테스트·비교 로직.
- 게이트·도메인 단종: `DEFAULT_RECENCY_GATE_DAYS`, `DOMAIN_DISCONTINUED`. `SPLIT_CUTOFF=2025-01-01`, `RANDOM_SEED=42`.
- 06-21 예보는 `data/interim/manual_obs_20260614.csv`(2행)를 기준일 이전 이력으로 포함해 산출(06/07과 동일).

### 사실 4 — 시각화 자산

`src.viz.set_korean_font()`(Malgun Gothic 설정), `outputs/figures/`에 저장 그림 7개 존재. 강의식 라이브 흐름이므로 08은 **tidy에서 직접 인라인 플롯**(matplotlib/pandas `.plot`)을 그린다(저장 PNG 로드가 아니라). 무거운 04 로직 전체 복제는 금지하고, 핵심 3~4개만 간단히 그린다.

## 제약 조건

- **위치**: `notebooks/08_presentation.ipynb`를 그 자리에서 재작성(전면 교체). 새 파일·다른 경로 금지.
- **자족·재현성**: 커널 재시작 후 위에서 아래로 한 번에 실행되어야 한다. raw(`data/raw/`)에서 시작해 tidy를 라이브 생성하고, 시각화·예측까지 한 노트북에서 끝낸다. 외부에서 만든 `pres_*.csv`에 의존하지 않는다. 난수 시드 고정(`RANDOM_SEED=42`), `TODAY=2026-06-10`, `SPLIT_CUTOFF=2025-01-01` 고정.
- **재크롤링 금지**: "수집" 단계는 `data/raw/`의 수집물(`view_by_type.txt`, `view_by_date.txt`, `inven_20563_meta.json`)을 로드해 제시한다. 네트워크 요청·`src.collect` 실행 금지(크롤링 예절·재현성).
- **원본 불변**: `data/raw/`·`data/processed/`에 쓰지 않는다. 08은 tidy를 메모리에서 만들어 쓰되 `data/processed/tidy_rewards.csv`를 덮어쓰지 않는다(저장 셀 없음).
- **로직 재사용**: parse/normalize/features/predict_dataset/prophet_cycle/viz의 기존 함수를 import해 쓴다. 동일 로직을 재구현하지 않는다(불가피한 오케스트레이션·플롯 코드만 08에 둔다).
- **언어·주석**: 모든 비코드 텍스트(마크다운, `print`/`display` 라벨)는 한글. 코드 주석·docstring 금지([[no-code-comments]]).
- **분량**: 강의식 4단계지만 발표용이므로 간결하게. 전체 30셀 이하 목표, 각 단계 코드 셀 6개 이하. 02 셀 8 같은 장황한 점검 출력 복제 금지.
- **기존 결과 일관성**: 08의 백테스트·06-14·06-21 수치는 06/07 노트북 및 `final_report.md` §6과 일치해야 한다(같은 함수·같은 분할·같은 시드이므로 자동 일치, 육안 확인).
- **테스트**: `python -m pytest -q` 기존 51개 통과 유지(이번 Phase는 `src/`·`tests/` 변경 없음).

## 작업 1 — 06/07 발표용 export 셀 제거 및 pres CSV 정리

Phase 18에서 추가한 "로드 전용 08"용 export는 자족형 08에서 불필요하다.

- `notebooks/06_predict.ipynb`: Phase 18에서 추가한 `## 발표용 표 저장` 마크다운 셀과 그 export 코드 셀(맨 끝 2셀)을 **제거**해 Phase 17 시점 상태로 되돌린다. 그 외 셀 불변.
- `notebooks/07_prophet.ipynb`: 동일하게 맨 끝 `## 발표용 표 저장` + export 코드 셀 2개 제거.
- `data/interim/pres_*.csv` 6개 삭제(`pres_backtest_full.csv`, `pres_0614_gate.csv`, `pres_0614_actual.csv`, `pres_0621_rf.csv`, `pres_method_compare.csv`, `pres_0621_compare.csv`). (gitignore 대상이라 git에는 안 잡히지만 실제 파일 삭제.)
- `data/interim/manual_obs_20260614.csv`는 **삭제 금지**(예측 단계에서 사용).

**검증**: 06/07 nbconvert 재실행 성공(export 셀 없이도 기존 출력 유지), 06/07 셀 수가 Phase 17 시점으로 복귀.

## 작업 2 — `notebooks/08_presentation.ipynb` 강의식 자족형 재작성

아래 4단계 구조. 각 단계는 한글 마크다운 헤더 1개 + 라이브 코드 셀 몇 개.

### (0) 표지 마크다운
- 제목 "선데이메이플 보상 패턴 분석 · 다음 선데이는 무엇인가", 한 줄 문제 정의와 흐름 안내(수집→전처리→시각화→예측, 이 노트북 하나로 라이브 실행).

### (1) 데이터 수집
- 마크다운: 인벤 게시글 1건을 1회 수집해 "종류별 뷰"·"날짜별 뷰" 2종 원시 텍스트로 보관했음. 재크롤링 없이 보관본을 로드.
- 코드: `data/raw/`에서 `inven_20563_meta.json`(출처 URL 등) 로드해 출처 출력, `view_by_type.txt`·`view_by_date.txt` 로드해 각 앞부분 몇 줄과 문자수를 보여줌.

### (2) 데이터 전처리
- 마크다운: 두 뷰를 정규식 파싱(`(+N일)`·`(단종)`·`<이벤트>`/`(이벤트)`·요일표기 충돌 처리) → 보상명 정규화·카테고리 매핑 → cycle_days·is_discontinued 부여로 tidy 14컬럼 생성. 관측 단위는 (date, reward_raw).
- 코드: 사실 2의 시퀀스를 `src` 함수로 라이브 실행해 `parsed_by_type`/`parsed_by_date`→`tidy_prenorm`→`tidy` 생성(`TODAY=2026-06-10`). `data/processed`에 저장하지 않음.
- 코드: 간결한 결과·무결성 — `tidy.head()`, 14컬럼 스키마, 전체 1160행/분석 1118행, 고유 reward_norm 수, 단종 고유 71, (date,reward_raw) 중복 0, 비일요일 11(목록). 02 셀 8 전체 복제 금지, 위 항목만.

### (3) 시각화
- 마크다운: 각 그림이 답하는 질문 한 줄씩(카테고리 구성 변화 / 회차당 보상 수 / 재등장 주기 / 단종 분포).
- 코드: `src.viz.set_korean_font()` 호출 후 tidy(분석 1118행)에서 **인라인 플롯 3~4개**를 직접 그림:
  - 연도별 카테고리 비중(누적/그룹 막대), 연도별 회차당 평균 보상 수(라인/막대), cycle_days 분포(히스토그램, 365일 초과는 마지막 구간 합산), (선택) 카테고리별 단종 고유 보상 수.
  - 무거운 04 로직 전체 복제 금지. `plt.show()`로 표시(파일 저장 안 함).

### (4) 예측 — 다음 선데이는 무엇인가
- 마크다운: 두 방법(분류기=경과일·주기 피처, Prophet=28일 시즈널리티)을 같은 후보·같은 date_hit_rate로 비교한다는 프레임. 확률/yhat은 보정 확률이 아니라 상대 점수. 단종·휴면은 재증 게이트(180일)+도메인 목록으로 제외.
- 코드 4-1 (백테스트): `build_prediction_frame`(또는 `write_prediction_frame`로 interim 생성 후 로드 — 단 `data/processed`는 불변) → train(<2025-01-01)/test 분할 → 베이스라인 2종 + 로지스틱 + 랜덤포레스트 학습·평가 → date_hit_rate 비교표(06_predict 셀 7~13 로직 재사용). Prophet 백테스트(07 셀 7 로직, 후보 20개 적합)까지 더해 4방법+Prophet 한 표로. **이 셀이 가장 느림(Prophet ~20 적합)** — 마크다운에 "실행에 수십 초 걸릴 수 있음" 한 줄.
- 코드 4-2 (2026-06-14 검증): 게이트 전/후 분류기 상위5 적중수 + 실제 보상(몬스터파크_경험치·선물_기타지급) 순위. Prophet 06-14 순위도 나란히(선택). 실제값은 `manual_obs_20260614.csv`.
- 코드 4-3 (2026-06-21 예보): manual_obs 포함해 기준일 이전 이력으로, 분류기 상위5와 Prophet 상위5를 나란히 비교표. 단종(현상금_경험치·불꽃늑대_경험치·스타포스_1+1강화·스타포스_성공확률) 부재 assert.

### (5) 결론 마크다운
- 회차당 보상 증가·강화/성장 축, 단종 집중(성장·사냥효율·수집기타), 두 예측 방법 단일 승자 없음·둘 다 단종 게이트 필요(리포트 §8 요약). 새 해석 창작 금지, 리포트 흐름 따름.

## 검증 기준

- `python -m pytest -q`: 기존 51개 통과(불변).
- `python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb` 및 `07_prophet.ipynb` 성공(export 셀 제거 후에도).
- `python -m jupyter nbconvert --to notebook --execute notebooks/08_presentation.ipynb` 성공(검증 산출물 삭제). 커널 처음부터 끝까지 한 번에 실행됨.
- 08의 전처리 결과: 전체 1160행·분석 1118행·단종 고유 71·비일요일 11이 02와 일치.
- 08의 백테스트 date_hit_rate(랜덤포레스트 0.4493/Prophet 0.4203 등)·06-14(0/2→1/2, 몬스터파크 9위→5위)·06-21(RF 몬스터컬렉션 41.7%… / Prophet 몬스터파크 0.402…)이 06/07·리포트와 일치.
- 08 전체 30셀 이하, 코드 주석 0, 비코드 텍스트 한글, `data/raw/`·`data/processed/` 불변.
- `data/interim/pres_*.csv` 6개 삭제됨, `manual_obs_20260614.csv` 잔존.

## 작업 우선순위 요약

| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1 | 06/07 export 셀 제거 + pres CSV 삭제 | 4셀 제거 + 6파일 | - |
| 2 | `08_presentation.ipynb` 자족형 재작성 | 4단계, 30셀 이하 | src 전 모듈, raw, manual_obs |

## 이번 범위 제외 항목

- 7개 파이프라인 노트북(01~07) 통합·삭제 — **하지 않음**. 단계 분리는 평가 대상이라 유지하고, 08만 강의식 발표 워크스루로 둔다.
- 08을 `C:\Jupyter`로 이동/복제 — 제외(사용자 결정: 프로젝트 notebooks/ 유지).
- 코드 100% 강의식(마크다운 0) — 제외. 우리 프로젝트는 한글 마크다운 서술 유지가 평가 기준.
- `final_report.md`/HTML/`requirements.txt`/`src/`/`tests/` 수정 — 제외(이번 Phase 변경 없음).
- 04_eda의 모든 그림을 08에 재현 — 제외(핵심 3~4개만 인라인).
