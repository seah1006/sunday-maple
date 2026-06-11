# Phase 9 Codex Handoff

## 작업 범위

- `src/viz.py` 신규 생성: 한글 폰트 설정과 그림 저장 유틸리티 추가.
- `notebooks/04_eda.ipynb` 신규 생성: `tidy_rewards.csv`만 로드해 4개 탐색 질문(Q1, Q8, Q2, Q3)을 집계·시각화.
- `notebooks/05_model.ipynb` 신규 생성: 등장 3회 이상 `reward_norm` 대상 최소 베이스라인 모델 평가.
- `outputs/figures/`에 발표용 그림 7개 저장.
- `data/raw/`, `data/processed/tidy_rewards.csv`, `src/parse.py`, `src/normalize.py`, `src/features.py`는 수정하지 않음.

## 구현 요약

### `src/viz.py`

- `set_korean_font()` 추가.
  - `matplotlib.pyplot.rcParams["font.family"] = "Malgun Gothic"`
  - `axes.unicode_minus = False`
  - 설정 실패 시 경고만 발생.
- `save_fig(fig, name, outdir="outputs/figures")` 추가.
  - 출력 디렉터리 생성.
  - `{name}.png`를 `dpi=150`, `bbox_inches="tight"`로 저장.
  - 저장 경로 문자열 반환.
- Claude 검토 포인트: Windows 전제의 간단한 구현이며, 과한 폰트 탐색·환경 방어 코드는 넣지 않았음.

### `notebooks/04_eda.ipynb`

- 첫 코드 셀에서 `set_korean_font()` 호출.
- `data/processed/tidy_rewards.csv`만 로드.
- 기본 분석 필터를 명시하고 적용: `reward_norm.notna() & ~is_future`.
- 분석 대상 행 수는 1118행.
- 모든 마크다운, 출력 라벨, 그래프 제목·축·범례를 한글로 작성.
- 2017년과 2026년은 부분 연도임을 출력과 그래프 주석에 표시.

그래프별 Claude 검토 포인트:

- `q1_category_share_by_year.png`: 연도별 카테고리 비중 100% 누적 막대. 부분 연도 주석 포함.
- `q8_rewards_per_session.png`: 연도별 보상 수 / 고유 회차 수 기반 회차당 보상 수 추이.
- `q2_cycle_by_norm.png`: `reward_norm`별 중앙 `cycle_days` 하위 10개와 상위 10개 비교.
- `q2_cycle_hist.png`: `cycle_days` 전체 분포와 중앙값 기준선.
- `q3_discontinued_by_category.png`: 카테고리별 단종·현행 보상 조합 수.
- `q3_last_seen_year.png`: 단종 보상 조합의 마지막 등장 연도 분포.
- 마지막 마크다운에 정규 보상 기준, 이벤트 연동 일회성 보상 제외 스코프를 명시.

### `notebooks/05_model.ipynb`

- 서두에 보조·최소 베이스라인임을 명시.
- 난수 시드 `RANDOM_SEED = 42` 고정.
- 등장일 3회 이상 `reward_norm`만 평가 대상으로 사용.
- 각 `reward_norm`의 마지막 `cycle_days`를 검증용 실제값으로 두고, 이전 `cycle_days` 중앙값으로 예측.
- 전역 `cycle_days` 중앙값 기준과 평균절대오차를 비교.
- `model_pred_vs_actual.png`: 예측값과 실제값 산점도 저장.
- 추가 피처, 복잡 모델, 튜닝은 넣지 않음.
- Claude 검토 포인트: 장기 휴면 보상과 운영 정책 변화는 설명하지 않는 최소 기준선임.

## 검증 결과

### Pytest

```text
.................................                                        [100%]
33 passed in 0.75s
```

### 노트북 재실행

```text
jupyter nbconvert --to notebook --execute notebooks/04_eda.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/04_eda.ipynb to notebook
[NbConvertApp] Writing 213780 bytes to notebooks\04_eda.ipynb

jupyter nbconvert --to notebook --execute notebooks/05_model.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/05_model.ipynb to notebook
[NbConvertApp] Writing 52910 bytes to notebooks\05_model.ipynb
```

실행 중 Windows `zmq` 이벤트 루프 경고가 출력되었으나 노트북 실행은 성공함.

### 한글 라벨 점검

```text
notebooks\04_eda.ipynb issues= [] english_terms= []
notebooks\05_model.ipynb issues= [] english_terms= []
```

대표 그림(`q1_category_share_by_year.png`, `model_pred_vs_actual.png`)을 시각 확인했고 한글 깨짐은 보이지 않음.

### 생성된 그래프 목록

```text
outputs/figures/q1_category_share_by_year.png
outputs/figures/q8_rewards_per_session.png
outputs/figures/q2_cycle_by_norm.png
outputs/figures/q2_cycle_hist.png
outputs/figures/q3_discontinued_by_category.png
outputs/figures/q3_last_seen_year.png
outputs/figures/model_pred_vs_actual.png
```

### `04_eda.ipynb` 출력 원문

```text
전체 tidy 행 수: 1160
기본 분석 대상 행 수: 1118
분석 대상 날짜 범위: 2017-03-12 ~ 2026-06-07
부분 연도: 2017년은 3월 시작, 2026년은 6월까지의 공개분만 포함
```

```text
연도별 카테고리 비중(%):
category    강화    성장  사냥효율  수집기타
year
2017      25.4  22.5  38.0  14.1
2018      27.1  27.1  25.0  20.8
2019      39.5  17.3  22.2  21.0
2020      30.1  33.3  17.2  19.4
2021      34.0  28.3  17.0  20.8
2022      29.7  30.6  18.0  21.6
2023      31.3  32.8  19.4  16.4
2024      30.4  36.3  20.5  12.9
2025      35.5  32.2  20.8  11.5
2026      34.7  29.2  16.7  19.4
```

```text
연도별 회차당 보상 수:
      보상 수  고유 회차 수  회차당 보상 수
year
2017    71       36     1.972
2018    96       39     2.462
2019    81       44     1.841
2020    93       52     1.788
2021   106       52     2.038
2022   111       52     2.135
2023   134       57     2.351
2024   171       52     3.288
2025   183       52     3.519
2026    72       23     3.130
```

```text
자주 재등장하는 보상:
reward_norm
프리미엄PC방       7.0
몬스터파크_경험치    21.0
트레져헌터_경험치    24.5
룬_경험치버프      28.0
스타포스_파괴방지    28.0
솔에르다_사냥      28.0
불꽃늑대_경험치     28.0
룬_재등장감소      28.0
콤보킬_경험치      28.0
현상금_경험치      28.0
드물게 재등장하는 보상:
reward_norm
선물_기타지급       469.0
명예의훈장         392.0
데미지스킨_지급      210.0
우르스           210.0
잠재능력_재설정할인    189.0
솔에르다_접속지급     189.0
미라클타임         182.0
유니온프리셋_지급     178.5
헤어타임          175.0
코디타임          175.0
```

```text
cycle_days 요약:
count    1063.0
mean       65.2
std       109.7
min         4.0
25%        28.0
50%        42.0
75%        70.0
max      2030.0
```

```text
카테고리별 단종·현행 보상 조합 수:
단종 상태      단종   현행
category
강화          7  350
성장         93  244
사냥효율      157   77
수집기타       54  136
```

```text
단종 보상 마지막 등장 연도 분포:
마지막 등장 연도
2017    3
2018    6
2019    4
2022    2
```

### `05_model.ipynb` 출력 원문

```text
기본 분석 대상 행 수: 1118
난수 시드: 42
```

```text
등장 3회 이상 reward_norm 수: 34
평가 대상 reward_norm 수: 34
전역 cycle_days 중앙값: 42.0
모델 비교:
        모델  평균절대오차(일)  평가 보상 수
보상별 과거 중앙값      74.49       34
 전역 중앙값 기준      93.65       34
오차가 작은 예시:
reward_norm  예측값  실제값  전역 중앙값 예측  절대오차  전역 중앙값 절대오차  학습 간격 수
   경험치쿠폰_지급 63.0 56.0       42.0   7.0         14.0       18
    룬_경험치버프 28.0 35.0       42.0   7.0          7.0       86
    룬_재등장감소 28.0 35.0       42.0   7.0          7.0       21
  몬스터파크_경험치 21.0 14.0       42.0   7.0         28.0       80
   위대한소울_확률 63.0 70.0       42.0   7.0         28.0       51
 어빌리티_재설정할인 42.0 35.0       42.0   7.0          7.0       67
  스타포스_파괴방지 28.0 35.0       42.0   7.0          7.0       14
  스타포스_비용할인 42.0 35.0       42.0   7.0          7.0       71
    콤보킬_경험치 28.0 35.0       42.0   7.0          7.0       85
  흔적복구_비용할인 28.0 35.0       42.0   7.0          7.0        1
```

## 데이터 상태

- 원본 산출물 경로: `data/processed/tidy_rewards.csv`
- 전체 행 수: 1160
- 전체 컬럼 수: 14
- Phase 9 기본 분석 대상: 1118행
- 분석 대상 날짜 범위: 2017-03-12 ~ 2026-06-07
- 분석 대상 고유 `reward_norm`: 48개
- `cycle_days` 비결측: 1063행
- `cycle_days` 중앙값: 42.0일
- `cycle_days` 최댓값: 2030.0일
- `is_discontinued` 분포: False 807행, True 311행
- 모델 평가 대상: 등장 3회 이상 `reward_norm` 34개
- 보상별 과거 중앙값 평균절대오차: 74.49일
- 전역 중앙값 기준 평균절대오차: 93.65일

카테고리 분포:

```text
강화      357
사냥효율    234
성장      337
수집기타    190
```

연도별 분석 대상 행 수:

```text
2017     71
2018     96
2019     81
2020     93
2021    106
2022    111
2023    134
2024    171
2025    183
2026     72
```

## Claude 리뷰 요청

### Critical

- `04_eda.ipynb`, `05_model.ipynb`가 `tidy_rewards.csv`만 의존하고 재파싱을 하지 않는지 확인.
- 그래프와 출력 라벨이 발표자료 한글 규칙을 충분히 만족하는지 확인.
- `outputs/figures/` 루트 경로에 저장된 7개 그림이 발표용으로 사용 가능한지 확인.

### Major

- Q3의 "보상 조합 수" 집계 단위가 `reward_raw`, `reward_trailing`, `reward_norm`, `category`, `is_discontinued`, `date` 중복 제거 결과로 적절한지 검토.
- 2017년과 2026년 부분 연도 주석이 비중·회차당 평균 해석에 충분히 반영되었는지 검토.
- 최소 베이스라인 모델이 발표의 보조 기준선이라는 범위를 벗어나지 않는지 검토.

### Minor

- 그래프 색상과 범례 위치가 발표 슬라이드에서 읽기 쉬운지 확인.
- 출력 표에서 `reward_norm`, `cycle_days` 같은 코드 식별자 표기가 발표자료 언어 규칙과 충돌하지 않는지 확인.

### 특이 질문

- `cycle_days` 최댓값 2030일이 Q2 히스토그램과 모델 산점도의 축 범위를 넓히는 요인이다. Phase 5 결정에 따라 원값을 유지했으며, 별도 절단·로그 변환은 하지 않았다. 발표용 그림에서 이 처리가 그대로 적절한지 확인 요청.
- Phase 9 패킷 파일은 로컬 출력에서 인코딩이 깨져 보였으나, 사용자 프롬프트와 패킷 내 식별 가능한 요구사항을 기준으로 구현했다. 패킷 원문과 다른 세부 요구가 있었는지 확인 요청.
