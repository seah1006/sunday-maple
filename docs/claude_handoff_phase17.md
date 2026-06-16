# Claude Handoff Phase 17

## 구현 요약

### 작업 1. Prophet 재등장-주기 모듈

- `src/prophet_cycle.py`를 새로 추가했다.
- `build_weekly_series`는 기준일 미만 이력만 사용해 보상별 주간 0/1 시계열을 만든다.
- `fit_predict_reward`는 Prophet PoC 설정을 고정 사용한다.
- Prophet 설정은 `yearly_seasonality=True`, weekly/daily off, `cycle28` period 28, `fourier_order=5`, `uncertainty_samples=0`이다.
- `rank_candidates`는 Phase 16의 `_candidate_rewards`, `gate_candidates`, `DEFAULT_RECENCY_GATE_DAYS`, `DOMAIN_DISCONTINUED`를 재사용한다.
- 도메인 단종 목록과 재증 게이트를 중복 정의하지 않았다.
- `tests/test_prophet_cycle.py`를 추가해 시계열 누수 방지와 게이트 적용 순위를 Prophet 적합 없이 검증했다.

### 작업 2. Prophet 노트북

- `notebooks/07_prophet.ipynb`를 새로 추가했다.
- train 구간(`<2025-01-01`)으로 후보별 Prophet을 적합하고, test 구간 `2025-01-05`~`2026-06-07`의 `yhat`을 예측했다.
- `date_hit_rate`는 분류기와 같은 정의로 계산했다.
- 06-14 검증은 Phase 16의 `data/interim/manual_obs_20260614.csv`를 재사용했다.
- 06-21 예보는 06-14 보조 관측을 기준일 이전 이력으로 포함했다.
- cmdstanpy 로그는 노트북에서 억제했다.
- 06-21 Prophet과 랜덤포레스트 후보에서 현상금_경험치, 불꽃늑대_경험치, 스타포스_1+1강화, 스타포스_성공확률이 제외됨을 `assert`로 확인했다.

### 작업 3. 리포트와 HTML

- `outputs/report/final_report.md` §6에 Prophet 비교 하위 절을 추가했다.
- 공정 비교 `date_hit_rate` 표, 06-14 검증 비교표, 06-21 예보 비교표를 추가했다.
- 결론은 Prophet 우월이 아니라 두 방식 모두 단종 게이트가 필요하다는 비교 결과로 정리했다.
- `outputs/report/build_html.py`를 재실행해 `outputs/report/final_report.html`을 재생성했다.
- 기존 그림 7개는 모두 base64로 내장됐고 외부 PNG 링크는 남지 않았다.

### 작업 4. 의존성

- `requirements.txt`에 `prophet`을 추가했다.
- 현재 설치 확인 버전은 `prophet 1.3.0`이다.

## 검증 결과

`python -m pytest -q`

```text
...................................................                      [100%]
51 passed in 1.04s
```

`python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb --output 06_predict_phase17_check.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/06_predict.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 34375 bytes to notebooks\06_predict_phase17_check.ipynb
```

`python -m jupyter nbconvert --to notebook --execute notebooks/07_prophet.ipynb --output 07_prophet_phase17_check.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/07_prophet.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 33365 bytes to notebooks\07_prophet_phase17_check.ipynb
```

- 두 nbconvert 실행은 성공했다.
- Windows/ZMQ 런타임 경고만 있었고 실행 실패는 없었다.
- 검증용 `notebooks/*phase17*.ipynb`, `notebooks/*phase16*.ipynb`, `notebooks/*nbconvert*.ipynb` 산출물은 삭제했다.

`python outputs/report/build_html.py`

```text
작성: C:\Users\USER\Desktop\수업\데이터처리실습\final_project\sunday-maple\outputs\report\final_report.html
크기: 478.1 KB
내장 이미지 수: 7
남은 외부 png 링크: 0
```

### 수치 대조

- 분류기 백테스트 4행은 06_predict와 07_prophet 실행 출력에서 일치한다.
- 랜덤포레스트 `date_hit_rate`는 0.449275이고 리포트에는 0.4493으로 반올림했다.
- Prophet `date_hit_rate`는 0.420290이고 리포트에는 0.4203으로 반올림했다.
- 06-14 게이트 후 검증에서 랜덤포레스트와 Prophet은 모두 상위 5개 적중 수 1/2다.
- 06-14 몬스터파크_경험치는 랜덤포레스트 5위 24.0%, Prophet 4위 `yhat` 0.350이다.
- 06-14 선물_기타지급은 두 방법 모두 후보권 밖이다.
- 06-21 랜덤포레스트 상위 5개는 몬스터컬렉션 41.7%, 스타포스_비용할인 39.3%, 주문의흔적_비용할인 36.7%, 어빌리티_재설정할인 34.3%, 엘리트몬스터_증가 27.7%다.
- 06-21 Prophet 상위 5개는 몬스터파크_경험치 0.402, 주문의흔적_비용할인 0.330, 룬_경험치버프 0.318, 콤보킬_경험치 0.281, 스타포스_비용할인 0.157이다.
- 06-21 추론 후보에 현상금_경험치, 불꽃늑대_경험치, 스타포스_1+1강화, 스타포스_성공확률이 없음을 확인했다.
- `src/predict_dataset.py`, `src/prophet_cycle.py`의 코드 주석 0개, docstring 0개다.
- `notebooks/06_predict.ipynb`, `notebooks/07_prophet.ipynb`의 코드 주석 0개다.

## 데이터 상태

- `data/processed/tidy_rewards.csv`: 1160행, 14컬럼
- 전체 결측 수: 2608

| 컬럼 | 결측 수 |
|---|---:|
| reward_raw | 42 |
| reward_trailing | 1055 |
| reward_norm | 42 |
| category | 42 |
| reward_magnitude | 122 |
| event_context | 26 |
| time_limited | 1140 |
| is_discontinued | 42 |
| cycle_days | 97 |

- `data/interim/manual_obs_20260614.csv`: 2행, 3컬럼
- 보조 관측 파일 내용:

| date | reward_norm | source |
|---|---|---|
| 2026-06-14 | 몬스터파크_경험치 | user_official_20260616 |
| 2026-06-14 | 선물_기타지급 | user_official_20260616 |

- `data/interim/manual_obs_20260614.csv`는 `.gitignore`의 `data/interim/` 규칙에 걸려 `git status`에는 표시되지 않지만 파일은 생성되어 있다.
- `data/raw/`와 `data/processed/`는 수정하지 않았다.

### 산출물 경로

- Prophet 모듈: `src/prophet_cycle.py`
- Prophet 테스트: `tests/test_prophet_cycle.py`
- Prophet 노트북: `notebooks/07_prophet.ipynb`
- 분류기 노트북: `notebooks/06_predict.ipynb`
- 06-14 보조 관측: `data/interim/manual_obs_20260614.csv`
- 최종 리포트 Markdown: `outputs/report/final_report.md`
- 최종 리포트 HTML: `outputs/report/final_report.html`
- 의존성 파일: `requirements.txt`

## Claude 리뷰 요청

Critical:

- `build_weekly_series`와 Prophet 백테스트가 기준일 미만 이력만 사용해 누수를 만들지 않는지 확인해 달라.
- Phase 16의 게이트와 도메인 단종 목록을 중복 정의하지 않고 재사용한 것이 충분한지 검토해 달라.
- Prophet `date_hit_rate` 계산이 분류기와 공정하게 같은 정의를 쓰는지 확인해 달라.

Major:

- Prophet 백테스트에서 train 적합 후 test 전체 yhat을 예측하고, 날짜별 게이트는 각 test 날짜 미만 이력으로 적용한 해석이 packet 의도와 맞는지 봐 달라.
- 리포트 §6의 결론이 Prophet 우월로 과장되지 않고, 둘 다 게이트가 필요하다는 비교 결과로 읽히는지 검토해 달라.
- 06-21 예보 비교표에서 분류기 확률과 Prophet yhat의 단위 차이가 충분히 명시됐는지 확인해 달라.

Minor:

- `data/interim/manual_obs_20260614.csv`가 `.gitignore`에 걸리는 상태를 제출 방식에서 어떻게 처리할지 확인해 달라.
- Prophet 후보를 학습 구간 빈도 상위 20개로 제한한 런타임 선택이 발표 설명에 충분한지 봐 달라.
- Windows/ZMQ 런타임 경고가 최종 검증 로그에 남는 점을 허용해도 되는지 확인해 달라.
