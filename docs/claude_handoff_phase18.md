# Claude Handoff Phase 18

## 구현 요약

### 작업 1. 06/07 결과표 export

- `notebooks/06_predict.ipynb` 끝에 `## 발표용 표 저장` 마크다운 셀과 export 코드 셀 1개를 추가했다.
- 06 노트북은 이미 계산된 `comparison_results`, `verification_0614`, `actual_rank_0614`, `forecast_0621_top5`만 CSV로 저장한다.
- `notebooks/07_prophet.ipynb` 끝에 `## 발표용 표 저장` 마크다운 셀과 export 코드 셀 1개를 추가했다.
- 07 노트북은 이미 계산된 `method_comparison`, `comparison_0621`만 CSV로 저장한다.
- 모델, 피처, 분할, 기존 계산 셀은 변경하지 않았다.

### 작업 2. 발표용 노트북

- `notebooks/08_presentation.ipynb`를 새로 추가했다.
- 전체 14셀, 코드 6셀로 구성했다.
- 08은 `data/processed/tidy_rewards.csv`, `outputs/figures/*.png`, `data/interim/pres_*.csv`만 로드한다.
- 모델 적합, Prophet 적합, 예측 재계산은 넣지 않았다.
- 표시 그림은 핵심 4개로 제한했다.
- 발표 흐름은 데이터와 파이프라인, 신뢰성, EDA, 예측 방법, 06-14 검증, 06-21 예보, 결론 순서로 구성했다.

### 생성 CSV

- `data/interim/pres_backtest_full.csv`
- `data/interim/pres_0614_gate.csv`
- `data/interim/pres_0614_actual.csv`
- `data/interim/pres_0621_rf.csv`
- `data/interim/pres_method_compare.csv`
- `data/interim/pres_0621_compare.csv`

## 검증 결과

`python -m pytest -q`

```text
...................................................                      [100%]
51 passed in 1.00s
```

`python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb --output 06_predict_phase18_check.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/06_predict.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 35347 bytes to notebooks\06_predict_phase18_check.ipynb
```

`python -m jupyter nbconvert --to notebook --execute notebooks/07_prophet.ipynb --output 07_prophet_phase18_check.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/07_prophet.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 34133 bytes to notebooks\07_prophet_phase18_check.ipynb
```

`python -m jupyter nbconvert --to notebook --execute notebooks/08_presentation.ipynb --output 08_presentation_phase18_check.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/08_presentation.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 276407 bytes to notebooks\08_presentation_phase18_check.ipynb
```

- 06/07/08 nbconvert 실행은 모두 성공했다.
- Windows/ZMQ 런타임 경고만 있었고 실행 실패는 없었다.
- 검증용 `notebooks/*phase18*.ipynb` 산출물은 삭제했다.

### CSV 생성 확인

```text
Name                    Length
----                    ------
pres_0614_actual.csv       248
pres_0614_gate.csv          76
pres_0621_compare.csv      410
pres_0621_rf.csv           200
pres_backtest_full.csv     344
pres_method_compare.csv    158
```

### 08 표 수치 확인

- 헤드라인: 전체행 1160, 분석행 1118, 회차수 459, 날짜 범위 2017-03-12 ~ 2026-06-07, 고유보상 48
- `pres_method_compare.csv`: 간격규칙 0.347826, 사전확률 0.362319, 랜덤포레스트 0.449275, Prophet 0.420290
- `pres_0614_gate.csv`: 게이트 전 상위5 적중 0/2 후보수 20, 게이트 후 상위5 적중 1/2 후보수 10
- `pres_0614_actual.csv`: 몬스터파크_경험치 게이트 전 9위 24.0%, 게이트 후 5위 24.0%, 선물_기타지급 후보권 밖
- `pres_0621_compare.csv`: 06-21 RF/Prophet 비교표가 07 노트북 출력과 일치

### 제약 확인

- `notebooks/08_presentation.ipynb`: 전체 14셀, 코드 6셀
- 06/07/08 코드 셀 주석 0개
- 08 마크다운 한글 손상 없음
- `data/raw/`, `data/processed/` 변경 없음
- `final_report.md`, `build_html.py`, `requirements.txt`, `src/`, `tests/`는 Phase 18에서 수정하지 않았다.

## 데이터 상태

- `data/processed/tidy_rewards.csv`: 1160행, 14컬럼
- 분석 대상 행: 1118행
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
- `data/interim/pres_*.csv`: 6개 생성
- `data/interim/`는 `.gitignore` 대상이라 생성 CSV는 `git status`에 표시되지 않는다.

### 산출물 경로

- 분류기 노트북: `notebooks/06_predict.ipynb`
- Prophet 노트북: `notebooks/07_prophet.ipynb`
- 발표 노트북: `notebooks/08_presentation.ipynb`
- 발표용 CSV: `data/interim/pres_*.csv`
- Phase 18 handoff: `docs/claude_handoff_phase18.md`

## Claude 리뷰 요청

Critical:

- 06/07에 추가된 셀이 기존 변수 저장만 수행하고, 모델·피처·분할·기존 출력에 영향을 주지 않는지 확인해 달라.
- 08이 모델 또는 Prophet을 재적합하지 않고 산출물 로드 전용으로 유지되는지 확인해 달라.

Major:

- 08의 발표 흐름이 리포트 내러티브와 맞고 새 해석을 만들지 않았는지 검토해 달라.
- `pres_*.csv` 6개가 발표에 필요한 표를 빠짐없이 담는지 확인해 달라.
- 08에서 핵심 그림 4개만 표시한 구성이 발표 분량에 적절한지 봐 달라.

Minor:

- 08 코드 셀 6개, 전체 14셀 구성이 발표 속도와 가독성에 맞는지 봐 달라.
- `data/interim/`가 `.gitignore` 대상이라 `pres_*.csv`가 status에 보이지 않는 점을 제출 방식에서 어떻게 처리할지 확인해 달라.
- Windows/ZMQ 런타임 경고가 검증 로그에 남는 점을 허용해도 되는지 확인해 달라.
