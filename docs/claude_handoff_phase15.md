# Claude Handoff Phase 15

## 구현 요약

### 작업 1. `outputs/report/final_report.md`

- 새 `## 6. 다음 회차 예측` 절을 추가했다.
- 기존 `## 6. 한계와 스코프`는 `## 7. 한계와 스코프`로, 기존 `## 7. 결론`은 `## 8. 결론`로 번호를 재배치했다.
- 시간순 백테스트 4행 비교표를 추가했다.
- 2026-06-14 다음 회차 랜덤포레스트 추론 상위 5개 후보표를 추가했다.
- 랜덤포레스트를 최종 추론 표에 사용한 이유를 `date_hit_rate` 최고값 기준으로 명시했다.
- 예측 신호를 단순 빈도가 아니라 주기 위상으로 해석해야 한다는 프레임을 보정했다.
- 05_model의 주기 MAE 74.49와 전역 기준 93.65를 함께 명시했다.

### 작업 2. `notebooks/06_predict.ipynb`

- 코드 셀은 변경하지 않았다.
- 모델 학습과 시간순 백테스트 마크다운에 랜덤포레스트 선택 사유를 추가했다.
- 다음 회차 추론 마크다운에서 `상장 보장` 표현을 `등장 보장`으로 보정했다.
- 결론 프레임 마크다운에서 예측 신호가 빈도가 아니라 주기 위상이라는 설명을 추가했다.

### 작업 3. `outputs/report/final_report.html`

- `outputs/report/build_html.py`를 재실행해 HTML을 재생성했다.
- 새 `## 6. 다음 회차 예측` 절이 HTML에 반영됐다.
- 기존 그림 7개는 모두 base64로 내장됐고 외부 PNG 링크는 남지 않았다.
- 선택 예측 그림은 추가하지 않았다. 기존 그림 7개 유지 요구를 우선했다.

## 검증 결과

`python -m pytest -q`

```text
............................................                             [100%]
44 passed in 1.49s
```

`jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb`

```text
jupyter : The term 'jupyter' is not recognized as the name of a cmdlet, function, script file, or
 operable program. Check the spelling of the name, or if a path was included, verify that the pat
h is correct and try again.
At line:2 char:1
+ jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb
+ ~~~~~~~
    + CategoryInfo          : ObjectNotFound: (jupyter:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```

같은 검증을 현재 Python 환경의 모듈 실행 방식으로 수행했다.

`python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb`

```text
[NbConvertApp] Converting notebook notebooks/06_predict.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 25787 bytes to notebooks\06_predict.nbconvert.ipynb
```

- nbconvert 실행은 성공했다.
- Windows/ZMQ 런타임 경고만 있었고 실행 실패는 없었다.
- 검증용 `notebooks/06_predict.nbconvert.ipynb`와 `notebooks/06_predict_verify.ipynb`는 삭제했다.

`python outputs/report/build_html.py`

```text
작성: C:\Users\USER\Desktop\수업\데이터처리실습\final_project\sunday-maple\outputs\report\final_report.html
크기: 473.0 KB
내장 이미지 수: 7
남은 외부 png 링크: 0
```

### 수치 대조

- 리포트 백테스트 4행은 06_predict 실행 출력과 일치한다.
- 로지스틱 `roc_auc`는 노트북 출력 0.748498을 리포트에서 0.7485로 반올림했다.
- 랜덤포레스트 `roc_auc`는 노트북 출력 0.734951을 리포트에서 0.7350으로 반올림했다.
- 다음 회차 상위 5개 후보와 확률은 06_predict 실행 출력과 일치한다.
- 05_model 출력의 보상별 과거 중앙값 기준 MAE 74.49, 전역 중앙값 기준 93.65와 리포트 수치가 일치한다.
- HTML에 `다음 회차 예측` 절이 포함됨을 확인했다.
- 코드 셀 변경 없음, 신규 코드 주석과 docstring 0개다.

## 데이터 상태

- `data/processed/tidy_rewards.csv`: 1160행, 14컬럼
- 분석 대상 eligible 데이터: 1118행, 14컬럼
- 날짜 범위: 2017-03-12 ~ 2026-08-30
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

### 산출물 경로

- 최종 리포트 Markdown: `outputs/report/final_report.md`
- 최종 리포트 HTML: `outputs/report/final_report.html`
- 예측 노트북: `notebooks/06_predict.ipynb`
- 기존 그림 경로: `outputs/figures/`
- 원천 데이터 `data/raw/`와 처리 데이터 `data/processed/`는 수정하지 않았다.

## Claude 리뷰 요청

Critical:

- `outputs/report/final_report.md`의 새 §6이 Phase 14 출력 수치를 과장 없이 반영했는지 확인해 달라.
- 랜덤포레스트를 추론 표에 사용한 사유가 `date_hit_rate` 기준이라는 점이 충분히 명확한지 확인해 달라.

Major:

- 예측 신호를 빈도가 아니라 주기 위상으로 해석한 문장이 발표 프레임과 맞는지 검토해 달라.
- `고신뢰`가 실제 등장 보장이 아니라 상위 5개 절단선이라는 점이 충분히 드러나는지 확인해 달라.
- 기존 §6, §7을 §7, §8로 민 번호 재배치가 본문 흐름상 자연스러운지 봐 달라.

Minor:

- 노트북 마크다운 보정 문장이 발표 자료 톤과 맞는지 봐 달라.
- 리포트의 `등장 확률` 표현과 노트북 출력 컬럼명 `상장확률` 사이의 표현 차이를 허용해도 되는지 확인해 달라.
- `jupyter` 명령이 PATH에 없어 `python -m jupyter`로 검증한 점을 최종 제출 환경에서 문제로 볼지 확인해 달라.
