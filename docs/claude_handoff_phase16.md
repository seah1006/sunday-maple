# Claude Handoff Phase 16

## 구현 요약

### 작업 1. 재증 게이트와 도메인 단종 목록

- `src/predict_dataset.py`에 `DEFAULT_RECENCY_GATE_DAYS = 180`과 `DOMAIN_DISCONTINUED = {"스타포스_1+1강화"}`를 추가했다.
- `gate_candidates`를 추가해 Phase 17에서도 같은 게이트를 재사용할 수 있게 했다.
- `build_inference_frame`에 `recency_gate_days`, `domain_discontinued` 인자를 추가했다.
- 기본 추론 경로는 기준일 미만 마지막 등장 후 180일을 초과한 후보와 도메인 단종 후보를 제외한다.
- `build_prediction_frame`은 변경하지 않아 백테스트 후보 universe와 Phase 14 비교표를 유지했다.
- `tests/test_predict_dataset.py`에 게이트 관련 테스트 4개를 추가했다.

### 작업 2. 06-14 검증과 06-21 예보

- `data/interim/manual_obs_20260614.csv`를 추가했다.
- 보조 관측 2행은 `2026-06-14,몬스터파크_경험치,user_official_20260616`과 `2026-06-14,선물_기타지급,user_official_20260616`이다.
- `notebooks/06_predict.ipynb`의 추론 구간을 06-14 게이트 전후 검증과 06-21 게이트 적용 예보로 교체했다.
- 모델, 피처, 하이퍼파라미터, 백테스트 분할은 변경하지 않았다.
- 06-21 추론 후보에서 현상금_경험치, 불꽃늑대_경험치, 스타포스_성공확률, 스타포스_1+1강화가 제외됨을 `assert`로 확인했다.

### 작업 3. 리포트와 HTML

- `outputs/report/final_report.md`의 §6을 Phase 16 결과 기준으로 재작성했다.
- 백테스트 4행 표는 Phase 14와 같은 수치를 유지했다.
- 06-14 검증표와 06-21 예보 상위 5개 표를 추가했다.
- `outputs/report/build_html.py`를 재실행해 `outputs/report/final_report.html`을 재생성했다.
- 기존 그림 7개는 모두 base64로 내장됐고 외부 PNG 링크는 남지 않았다.

## 검증 결과

`python -m pytest -q`

```text
................................................                         [100%]
48 passed in 1.05s
```

`python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb --output 06_predict_phase16_final.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/06_predict.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 34462 bytes to notebooks\06_predict_phase16_final.ipynb
```

- nbconvert 실행은 성공했다.
- Windows/ZMQ 런타임 경고만 있었고 실행 실패는 없었다.
- 검증용 `notebooks/06_predict_phase16_verify.ipynb`와 `notebooks/06_predict_phase16_final.ipynb`는 삭제했다.

`python outputs/report/build_html.py`

```text
작성: C:\Users\USER\Desktop\수업\데이터처리실습\final_project\sunday-maple\outputs\report\final_report.html
크기: 473.9 KB
내장 이미지 수: 7
남은 외부 png 링크: 0
```

### 수치 대조

- 백테스트 비교표는 06_predict 실행 출력과 일치한다.
- 랜덤포레스트 `date_hit_rate`는 0.449275이고 리포트에는 0.4493으로 반올림했다.
- 06-14 게이트 전 후보 수는 20, 상위 5개 적중 수는 0/2다.
- 06-14 게이트 후 후보 수는 10, 상위 5개 적중 수는 1/2다.
- 06-14 몬스터파크_경험치는 게이트 전 9위 24.0%, 게이트 후 5위 24.0%다.
- 06-14 선물_기타지급은 게이트 전후 모두 후보권 밖이다.
- 06-21 게이트 적용 상위 5개는 몬스터컬렉션 41.7%, 스타포스_비용할인 39.3%, 주문의흔적_비용할인 36.7%, 어빌리티_재설정할인 34.3%, 엘리트몬스터_증가 27.7%다.
- 06-21 추론 후보에 현상금_경험치, 불꽃늑대_경험치, 스타포스_성공확률, 스타포스_1+1강화가 없음을 확인했다.
- 코드 셀 주석 0개다.

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
- `data/raw/`와 `data/processed/`는 수정하지 않았다.

### 산출물 경로

- 게이트 구현: `src/predict_dataset.py`
- 게이트 테스트: `tests/test_predict_dataset.py`
- 06-14 보조 관측: `data/interim/manual_obs_20260614.csv`
- 예측 노트북: `notebooks/06_predict.ipynb`
- 최종 리포트 Markdown: `outputs/report/final_report.md`
- 최종 리포트 HTML: `outputs/report/final_report.html`

## Claude 리뷰 요청

Critical:

- `gate_candidates`가 기준일 미만 이력만 사용하고, target 당일·이후 등장을 누수로 보지 않는지 확인해 달라.
- `build_prediction_frame`을 변경하지 않아 백테스트 비교표가 Phase 14와 동일하게 유지되는 결정이 packet 의도와 맞는지 확인해 달라.

Major:

- 06-14 보조 관측을 `data/interim/manual_obs_20260614.csv`로 둔 방식과 source 값이 충분한지 검토해 달라.
- 06-14 검증 해석이 원시 모델 실패와 게이트 수정 효과를 과장 없이 설명하는지 확인해 달라.
- 06-21 예보에서 게이트 제외 대상 4개가 빠진 것이 리포트와 노트북에 충분히 드러나는지 봐 달라.

Minor:

- 리포트 §6 문장 톤이 발표용으로 자연스러운지 봐 달라.
- 노트북 한글 컬럼명이 PowerShell 텍스트 출력에서 깨져 보이지만 HTML/노트북 자체는 UTF-8인 상태를 허용해도 되는지 확인해 달라.
- `python -m jupyter` 검증에서 Windows/ZMQ 런타임 경고가 남는 점을 최종 제출상 문제로 볼지 확인해 달라.
