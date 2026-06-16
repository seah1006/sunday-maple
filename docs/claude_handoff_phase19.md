# Claude Handoff Phase 19

## 구현 요약

### 작업 1. Phase 18 export 정리

- `notebooks/06_predict.ipynb`에서 Phase 18의 `pres_*.csv` export 코드 셀을 제거했다.
- `notebooks/07_prophet.ipynb`에서 Phase 18의 `pres_*.csv` export 코드 셀을 제거했다.
- `data/interim/pres_*.csv` 6개를 삭제했다.
- `data/interim/manual_obs_20260614.csv`는 유지했다.

### 작업 2. `notebooks/08_presentation.ipynb` 전면 재작성

- 08을 로드 전용 노트북에서 강의식 자족형 단일 흐름으로 재작성했다.
- 흐름은 보관 원본 로드 → raw 파싱과 tidy 생성 → 인라인 시각화 → 분류기/Prophet 예측 → 결론이다.
- 재크롤링은 하지 않고 `data/raw/view_by_type.txt`, `data/raw/view_by_date.txt`, `data/raw/inven_20563_meta.json`만 읽는다.
- `src.parse`, `src.normalize`, `src.features`, `src.viz`, `src.predict_dataset`, `src.prophet_cycle` 함수를 재사용했다.
- `TODAY = 2026-06-10`, `SPLIT_CUTOFF = 2025-01-01`, `RANDOM_SEED = 42`로 고정했다.
- tidy는 메모리에서만 만들고 `data/processed/tidy_rewards.csv`를 저장하거나 덮어쓰지 않는다.
- 08은 전체 14셀, 코드 8셀이다.

## 검증 결과

`python -m pytest -q`

```text
...................................................                      [100%]
51 passed in 1.04s
```

`python -m jupyter nbconvert --to notebook --execute notebooks/06_predict.ipynb --output 06_predict_phase19_check2.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/06_predict.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 34490 bytes to notebooks\06_predict_phase19_check2.ipynb
```

`python -m jupyter nbconvert --to notebook --execute notebooks/07_prophet.ipynb --output 07_prophet_phase19_check2.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/07_prophet.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 33480 bytes to notebooks\07_prophet_phase19_check2.ipynb
```

`python -m jupyter nbconvert --to notebook --execute notebooks/08_presentation.ipynb --output 08_presentation_phase19_check.ipynb --output-dir notebooks`

```text
[NbConvertApp] Converting notebook notebooks/08_presentation.ipynb to notebook
C:\Users\USER\AppData\Roaming\Python\Python313\site-packages\zmq\_future.py:718: RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq. Registering an additional selector thread for add_reader support via tornado. Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
  self._get_loop()
[NbConvertApp] Writing 145646 bytes to notebooks\08_presentation_phase19_check.ipynb
```

- 06/07/08 nbconvert 실행은 모두 성공했다.
- Windows/ZMQ 런타임 경고만 있었고 실행 실패는 없었다.
- 검증용 `notebooks/*phase19*.ipynb` 산출물은 삭제했다.

### 08 실행 수치

- 전처리 결과: 전체 1160행, 분석 1118행, 컬럼 14개
- 고유 `reward_norm`: 48개
- 단종 고유 `reward_raw`: 71개
- `(date, reward_raw)` 중복: 0개
- 비일요일 행: 11개
- 백테스트 `date_hit_rate`: 간격규칙 0.347826, 사전확률 0.362319, 랜덤포레스트 0.449275, Prophet 0.420290
- 06-14 검증: 게이트 전 상위5 적중 0/2, 게이트 후 상위5 적중 1/2
- 06-14 몬스터파크_경험치: 게이트 전 9위 24.0%, 게이트 후 5위 24.0%
- 06-21 랜덤포레스트 1위: 몬스터컬렉션 41.7%
- 06-21 Prophet 1위: 몬스터파크_경험치 `yhat` 0.402
- 06-21 후보에서 현상금_경험치, 불꽃늑대_경험치, 스타포스_1+1강화, 스타포스_성공확률 부재 assert 통과

### 제약 확인

- `notebooks/08_presentation.ipynb`: 전체 14셀, 코드 8셀
- 06/07/08 코드 주석 0개
- 06/07에 `pres_` export 언급 0개
- `data/interim/pres_*.csv` 0개
- `data/interim/manual_obs_20260614.csv` 유지
- `data/raw/`, `data/processed/` 변경 없음

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

| date | reward_norm | source |
|---|---|---|
| 2026-06-14 | 몬스터파크_경험치 | user_official_20260616 |
| 2026-06-14 | 선물_기타지급 | user_official_20260616 |

### 산출물 경로

- 발표 노트북: `notebooks/08_presentation.ipynb`
- 분류기 노트북: `notebooks/06_predict.ipynb`
- Prophet 노트북: `notebooks/07_prophet.ipynb`
- 06-14 보조 관측: `data/interim/manual_obs_20260614.csv`
- Phase 19 handoff: `docs/claude_handoff_phase19.md`

## Claude 리뷰 요청

Critical:

- 08이 raw 보관본에서 시작해 tidy를 메모리에서 생성하고, `data/processed`에 쓰지 않는지 확인해 달라.
- 08의 전처리 수치 1160/1118/71/11이 02 결과와 같은지 검토해 달라.
- 08의 예측 수치가 06/07 및 리포트 §6과 일치하는지 확인해 달라.

Major:

- 08이 기존 `src` 함수 재사용 원칙을 지키고, 핵심 로직을 재구현하지 않았는지 봐 달라.
- 08의 강의식 흐름이 수집→전처리→시각화→예측 순서로 발표에 적합한지 검토해 달라.
- 06/07 export 셀 제거와 `pres_*.csv` 삭제가 Phase 18 정리 요구에 맞는지 확인해 달라.

Minor:

- 08의 시각화 4개가 발표 분량에 적절한지 봐 달라.
- 08 코드 셀 8개, 전체 14셀 구성이 강의식 발표용으로 충분히 간결한지 확인해 달라.
- Windows/ZMQ 런타임 경고가 검증 로그에 남는 점을 허용해도 되는지 확인해 달라.
