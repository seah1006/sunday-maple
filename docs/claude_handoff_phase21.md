# Phase 21 구현 인계

## 작업 범위

`docs/codex_work_packet_phase21.md` 작업 1~4: raw→tidy, 추가 관측 결합, 학습·백테스트·예보, 사이트 JSON CLI 및 각 테스트. 커밋·재크롤링·배포·노트북 실행/수정은 하지 않았다.

## 구현 요약

- 작업 1: `src/build_tidy.py`, `tests/test_build_tidy.py`. 삭제된 08 셀 4를 이식했다. 헬퍼 `_is_special`, `_time_limited`와 14컬럼 순서·기존 계산을 유지했다. CSV 비교는 nullable boolean/Int64로 로드해 결측 표현만 통일했다. 값 차이는 없다.
- 작업 2: `src/observations.py`, `tests/test_observations.py`. 날짜 변환, tidy 보상별 최빈 category 매핑, 두 플래그 False, concat. 입력의 source/reward_raw 등 부가 컬럼을 보존한다.
- 작업 3: `src/forecast.py`, `tests/test_forecast.py`. 제안 함수명과 3필드 ClassifierBundle을 채택했다. 08의 학습 분할, 전체 prediction_frame 기준 dummy 컬럼, 평가 및 Prophet 게이트를 유지했다. per_date 실제 보상은 후보 내 보상이며 RF nlargest(k) 및 동일한 적중 정의를 사용한다.
- 작업 4: `src/site_data.py`, `tests/test_site_data.py`, `data/site/*.json`. CLI·직렬화·메타·예보·백테스트·날짜별 이력·보상 집계 구현. `_clean`으로 재귀 변환하여 날짜 YYYY-MM-DD, 숫자 3자리, NaN/NA null, UTF-8 한글을 보존한다.
- 메시지 합의: **학습·백테스트는 raw tidy만 사용**, 결합 관측은 예보/history/rewards에만 사용한다. 08과 같은 불변 지표를 보존하기 위한 사양 정정이다. meta에 `backtest_data_through=2026-06-07`을 추가했다. 함수들은 입력 tidy를 그대로 받는다.
- CLI as_of 규칙: raw 날짜별 파싱 결과 중 reward_raw가 있는 마지막 날짜(현재 2026-06-07). 이후 빈 블록은 미래이며, 현재 입력에서 2026-06-10 기준과 같은 tidy·분석 결과다. data_through는 관측 결합 후 보상이 있는 마지막 날짜다.
- rewards의 is_discontinued는 분석 대상 해당 보상 행 중 하나라도 True이면 True이다. 수동 관측의 결측은 False 취급한다. cycle_days는 기존 tidy 계산값의 중앙값이며 추가 관측에 새 주기를 계산하지 않는다(08 concat 유지).

### 환경 차이로 기준값 갱신

Claude가 원본 08 코드를 현재 환경에서 별도 재실행하여 동일한 RF 차이를 확인했고, 현재 환경 값을 기준으로 갱신하도록 메시지로 승인했다. date_hit_rate 5개는 종전 값을 유지했다. final_report는 범위 밖이므로 수정하지 않았다.

| 항목 | 6월 기준 | 현재 환경 |
|---|---:|---:|
| RF 예보 몬스터컬렉션 | 41.7% | 66.7% |
| RF 예보 스타포스_비용할인 | 39.3% | 57.7% |
| RF 예보 주문의흔적_비용할인 | 36.7% | 45.3% |
| RF 예보 어빌리티_재설정할인 | 34.3% | 44.7% |
| RF 예보 엘리트몬스터_증가 | 27.7% | 46.3% |
| RF accuracy | 0.8607 | 0.754667 |
| RF f1 | 0.1255 | 0.278431 |
| RF roc_auc | 0.7350 | 0.731209 |
| Prophet 예보 1위 yhat | 0.402 | 0.402 |

Claude 승인으로 requirements.txt 불변 제약을 이번에 해제하여 새 의존성 없이 직접 의존성 12개를 설치 버전으로 고정했다. `py -m pip show` 확인값: requests 2.34.2, beautifulsoup4 4.15.0, lxml 6.1.1, pandas 3.1.0, numpy 2.5.4, matplotlib 3.11.2, seaborn 0.13.2, scikit-learn 1.9.1, mlxtend 0.25.0, jupyter 1.1.1, pytest 9.1.1, prophet 1.5.0.

## 검증 결과

- `py -m pytest -q -p no:cacheprovider`: **59 passed, 9 warnings in 17.78s** (기존 51 + 신규 8).
- `py -m src.site_data --out data/site`: 종료 코드 0, Prophet 포함 **22.3216초**.
- `py -m src.site_data --out <session tmp>/site-skip --skip-prophet`: 종료 코드 0, **11.2652초**. Prophet 값 null 확인.
- 추가 전체 export 재실행에서 반올림 전 수치 확인:

| 방법 | date_hit_rate |
|---|---:|
| 간격규칙 | 0.34782608695652173 |
| 사전확률 | 0.36231884057971014 |
| 로지스틱 | 0.391304347826087 |
| 랜덤포레스트 | 0.4492753623188406 |
| Prophet | 0.42028985507246375 |

- meta: data_through **2026-06-14**, backtest_data_through **2026-06-07**, target_date **2026-06-21**.
- RF 상위 5: 몬스터컬렉션 **66.7%**, 스타포스_비용할인 **57.7%**, 엘리트몬스터_증가 **46.3%**, 주문의흔적_비용할인 **45.3%**, 어빌리티_재설정할인 **44.7%**. JSON score는 각각 0.667/0.577/0.463/0.453/0.447(3자리 반올림).
- Prophet 1위: 몬스터파크_경험치 **0.402**.
- 게이트 후 후보 **10개**, 원 후보 20개 중 제외 **10개**. 사양의 제외 4종이 포함되지 않는 테스트 유지.
- tidy **1160행 ×14컬럼**, 분석 **1118행**, (date,reward_raw) 중복 **0**, 비일요일 **11행**. 기존 CSV 지정 6컬럼 값/결측 동일.
- 실행시간은 현재 PC 단일 실행 측정이다. 주간 CI 판단 자료로 남기며 실제 Actions 시간은 미측정이다.
- 경고: 기존 로지스틱 1000회 수렴 경고, pandas dayofweek deprecated, Prophet의 선택적 plotly import 안내. 종전 파라미터·기존 모듈을 변경하지 않았다.
- `git diff -- data/raw data/processed data/interim/manual_obs_20260614.csv notebooks` 출력 없음. notebooks/01~07 불변. staged notebooks/08 삭제와 presentation_script.html 삭제, CLAUDE.md 수정 및 roadmap/work packet은 작업 시작 전부터 존재한 상위 세션 변경이다.

## 데이터 상태

- raw/processed/manual observations 불변. 결합 tidy **1162행**, 분석+관측 **1120행**, 날짜 이력 **460개**, 보상 **48종**.
- raw tidy 결측 수: date 0, reward_raw 42, reward_trailing 1055, reward_norm 42, category 42, reward_magnitude 122, event_context 26, is_major_event 0, is_special 0, time_limited 1140, is_discontinued 42, is_future 0, no_event_week 0, cycle_days 97.
- 수동 관측 2행은 source/date/reward_norm/category/플래그를 보존하며 원문과 맥락·주기 등 없는 값은 JSON null(스페셜 날짜 요약은 False)이다.

| 산출물 | 바이트 |
|---|---:|
| data/site/meta.json | 559 |
| data/site/forecast.json | 4056 |
| data/site/backtest.json | 22092 |
| data/site/history.json | 258888 |
| data/site/rewards.json | 11304 |

## Claude 리뷰 요청

- **Critical**: 없음. 작업 1~4 구현·검증 완료. 미해결 질문 없음.
- **Major**: 합의된 현재 환경 RF 기준 갱신 및 직접 의존성 버전 고정을 검토해 주세요. 종전 final_report/과거 문서는 갱신하지 않았습니다. 운영 시 모델 재학습 범위·지난 예측의 저장 정책은 후속 Phase 범위입니다.
- **Minor**: JSON 점수 3자리 반올림으로 RF 66.7%를 프론트가 표시할 때 0.667을 사용합니다. JSON 지표도 3자리이므로 정밀 검증은 위 원수치/테스트를 기준으로 해 주세요. 실행 경고는 위와 같습니다.
