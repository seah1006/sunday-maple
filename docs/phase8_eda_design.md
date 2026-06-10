# Phase 8 설계 초안 — EDA (탐색적 분석·시각화)

> Phase 7까지 데이터 파이프라인 완성(`tidy_rewards.csv`, 14컬럼, 1160행). 이 문서는 발표자료용 EDA의 **분석 질문 후보**를 제시한다. 사용자가 중심 질문을 고르면 `docs/codex_work_packet_phase8.md`로 확정한다. 발표자료이므로 시각화·설명은 한글(CLAUDE.md 규칙), 새 노트북은 `04_eda.ipynb`(03_crossval 다음).

> 원칙(CLAUDE.md): 화려함보다 "질문에 답하는" 그래프. 각 그래프는 한 문장 질문에 대응. matplotlib 한글 폰트(Malgun Gothic)는 `src/viz.py` 헬퍼로.

## 분석 질문 후보 (각 1~2개 그래프로 답)

| # | 질문 | 사용 컬럼 | 그래프(안) |
|---|---|---|---|
| Q1 | 보상 **카테고리 구성**이 9년간 어떻게 변했나? (운영 방향 변화) | date(연도), category | 연도별 카테고리 비중 stacked area/bar |
| Q2 | 어떤 보상이 **자주/드물게** 재등장하나? (재등장 주기) | reward_norm, cycle_days | norm별 평균 cycle_days 막대(상·하위), cycle 분포 히스토그램 |
| Q3 | **무엇이 단종되고 무엇이 살아남았나?** | is_discontinued, reward_norm, date | 단종 vs 현행 보상 수, 단종 보상의 마지막 등장 시점 분포 |
| Q4 | **스페셜 썬데이**(is_special)는 얼마나 자주, 어떤 보상과? | is_special, date, reward_norm | 연도별 스페셜 횟수, 스페셜 동반 보상 top |
| Q5 | 보상 **강도 인플레이션**? (2배→3배→5배 상향 추세) | reward_magnitude, date, reward_norm | 대표 보상(현상금/불꽃늑대 등)의 배수 시계열 |
| Q6 | **대형 이벤트**(is_major_event) 기간엔 보상이 다른가? | is_major_event, category | 대형/비대형 보상 카테고리·건수 비교 |
| Q7 | **시간제→하루종일** 등 운영 방식 변화 시점? | time_limited, date | 시간제/하루종일 표기 추이 |
| Q8 | 한 회차에 보상 **몇 개**가 풀리나? 시기별 변화? | date, reward_raw 수 | 회차당 보상 수 시계열 |

## 보조(선택) — 04_model

CLAUDE.md상 모델은 보조 목표·오버엔지니어링 금지. 후보:
- "다음 썬데이에 특정 보상 카테고리가 등장할까" 베이스라인 분류(빈도/주기 기반) vs 단순 비교.
- 또는 cycle_days 기반 "다음 등장 시점" 단순 추정.
→ EDA 확정 후, 원하면 최소 베이스라인만.

## 열린 결정 (사용자)

1. **중심 질문 선택**: 위 Q1~Q8 중 발표에서 다룰 것(권장 3~5개). 전부는 과함.
2. **보조 모델 포함 여부**: 04_model 최소 베이스라인을 넣을지, EDA로 마무리할지.
3. **발표 스토리 톤**: (a) 운영 변화사(시간축 중심) / (b) 보상 종류별 패턴(주기·단종 중심) / (c) 둘 혼합.

## 범위/제약
- 새 노트북 `04_eda.ipynb`. tidy_rewards.csv 로드해서만 분석(재파싱 안 함). 분석 시 `is_future==False` 필터(미래 빈 블록 제외), no_event_week 처리 명시.
- `src/viz.py` 신규: 한글 폰트 설정 + 공통 그래프 헬퍼.
- 그래프는 `outputs/figures/`에 저장.
