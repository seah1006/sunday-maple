# Codex Work Packet — Phase 10 (Phase 9 보강: Q3 집계 수정 + event_context 파싱 정정 + 문서 동기화)

> 입력: `docs/claude_handoff_phase9.md` 리뷰 + Claude의 전체 개선 계획 조사. Phase 9는 **보강 필요** 판정 — EDA Q3에 Critical 집계 버그 1건, 파싱에 Major 결함 1건이 발견됐다.

## 작업 배경

Phase 9 handoff를 Claude가 독립 재검증하며 직접 확인한 사실:

1. **Q3-2 집계 버그 (Critical)**: `04_eda.ipynb` Q3 코드 셀의
   ```python
   last_seen = (
       analysis[analysis['is_discontinued'] == True]
       .groupby(['reward_raw', 'reward_trailing'])['date']
       .max()
   ```
   에서 pandas `groupby`의 기본 `dropna=True` 때문에 `reward_trailing`이 결측(전체 1160행 중 1055행 결측)인 단종 보상이 전부 탈락한다. 단종 고유 `reward_raw` 71개 중 **15개만 집계**됐고, `q3_last_seen_year.png`(노트북 출력: 2017=3, 2018=6, 2019=4, 2022=2)는 발표에 사용 불가.
   Claude가 tidy에서 재계산한 실제 분포(고유 `reward_raw` 단위, 합계 71):
   | 연도 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
   |---|---|---|---|---|---|---|---|---|---|
   | 개수 | 11 | 21 | 9 | 5 | 2 | 10 | 4 | 8 | 1 |

2. **Q3-1 단위 혼동 (Major)**: 같은 셀의 `combo` drop_duplicates에 `date`가 포함되어 사실상 **등장 행 수**(단종 311행)를 세는데, 그래프 제목·y축 라벨은 "보상 조합 수"다. "무엇이 단종되었나"라는 질문에는 고유 보상 수(단종 고유 `reward_raw` 71 / 고유 norm 36)가 맞는 단위다.

3. **event_context 오염 (Major)**: `data/raw/view_by_date.txt` 1129행 원문은
   ```
   2024.04.01(월) (유니온 릴레이)
   ```
   인데, `src/parse.py` `_parse_date_header`가 context_text `(월) (유니온 릴레이)`에 `re.fullmatch(r"\((.*)\)", ...)`를 탐욕 매칭해 event_context가 **`월) (유니온 릴레이`**(괄호 불균형)로 저장됐다. tidy의 2024-04-01 4행이 영향. CLAUDE.md가 경고한 `(월)`/`(토)` 요일 표기 케이스다.
   - 원문 전수 검색 결과 날짜 헤더에 `(요일)`이 붙은 줄은 이 1건뿐이다. 파워업 위크의 `YYYY.MM.DD(요일) - 보상` 줄(897~903행)은 `INLINE_DAILY_RE`가 정상 처리한다.
   - `view_by_type.txt` 265행에도 `2024.04.01(월)`이 있다. `TYPE_DATE_RE`의 trailing 그룹으로 `(월)`이 들어갈 텐데, 단종 매칭·교차검증에 부작용이 없는지 확인이 필요하다(작업 3 검증 항목).

4. **표시 개선 (Minor, handoff 특이 질문에 대한 판정)**: `cycle_days` 최대 2030일(장기휴면 2건, Phase 5 결정으로 원값 유지)은 데이터로는 그대로 두되, **표시만** 개선한다. `q2_cycle_hist.png`는 장기 구간을 마지막 빈으로 합치고 주석, `model_pred_vs_actual.png`는 로그 축 또는 축 범위 주석으로 가독성을 확보한다.

## 제약 조건

- `data/raw/` 불변. tidy 스키마(14컬럼) 유지 — 컬럼 추가/삭제/이름 변경 없음.
- 기존 `python -m pytest -q` 33개 통과 유지(테스트는 추가만).
- `04_eda.ipynb`는 **Q3 코드 셀·해석 셀과 Q2 히스토그램 표시부만** 수정. Q1·Q8 셀 변경 금지.
- `05_model.ipynb`는 **산점도 표시부만** 수정. 모델 로직·지표 변경 금지.
- 그래프·출력 라벨 전부 한글 유지(발표자료 규칙).
- tidy 재생성 시 변경 diff가 event_context 4행을 벗어나면 멈추고 handoff에 보고.

---

## 작업 1 — `04_eda.ipynb` Q3-2 단종 마지막 등장 연도 집계 수정 (Critical)

**수정 대상**: `notebooks/04_eda.ipynb` Q3 코드 셀.

- **현재 코드**: 위 작업 배경 1의 발췌. `groupby(['reward_raw', 'reward_trailing'])`가 trailing 결측 행을 탈락시킴.
- **변경 후 목표**: 단종 보상 단위를 **고유 `reward_raw`**로 집계.
  ```python
  last_seen = (
      analysis[analysis['is_discontinued'] == True]
      .groupby('reward_raw')['date']
      .max()
      .dt.year
  )
  ```
  (대안: `groupby([...], dropna=False)` — 단, 단종 매칭 자체가 원문 문자열 기준이므로 raw 단위 권장. 혼재 사례인 "엘리트 몬스터 수 증가"는 `is_discontinued == True` 필터로 단종 행만 남아 자연 처리된다.)
- **검증 요구사항**: 출력 분포 합계 = 71, 작업 배경 1의 표와 일치. `q3_last_seen_year.png` 재생성.
- **기존 결과 영향**: 그림·출력만 교체. 해석 마크다운도 새 분포(2018 정리 피크, 2024에도 8개 단종 등)에 맞게 갱신.

## 작업 2 — `04_eda.ipynb` Q3-1 집계 단위·라벨 정정 (Major)

**수정 대상**: 같은 Q3 코드 셀의 첫 번째 차트.

- **현재 코드**: `combo = analysis[[..., 'date']].drop_duplicates()` 후 category×단종상태 count → 행 수(단종 311)인데 라벨은 "보상 조합 수".
- **변경 후 목표**: 카테고리별 **고유 보상 수(`reward_raw` 기준)**의 단종/현행 비교 막대로 변경. 제목·y축 "고유 보상 수". 등장 행 수(311/807)는 print 표로만 참고 병기. 혼재 raw("엘리트 몬스터 수 증가")는 양쪽에 1씩 카운트됨을 해석 마크다운에 한 줄 주석.
- **검증 요구사항**: 단종 고유 합 71, 그림 `q3_discontinued_by_category.png` 재생성.

## 작업 3 — `src/parse.py` 날짜 헤더 `(요일)` 처리 수정 (Major)

**수정 대상**: `src/parse.py` `_parse_date_header`, `tests/test_parse.py`, `notebooks/02_parse_clean.ipynb` 재실행.

- **현재 코드**: `DATE_HEADER_RE.match` 후 context_text에 선행 `(월)`이 남아 `re.fullmatch(r"\((.*)\)")` 탐욕 매칭으로 오염.
- **변경 후 목표**: context 해석 전에 선행 요일 토큰 제거.
  ```python
  context_text = re.sub(r"^\([월화수목금토일]\)\s*", "", context_text)
  ```
- **검증 요구사항**:
  - `tests/test_parse.py`에 케이스 추가: 입력 `2024.04.01(월) (유니온 릴레이)` → date 2024-04-01, event_context `유니온 릴레이`, is_major_event False. 기존 헤더 케이스 회귀 통과.
  - `02_parse_clean.ipynb` 재실행으로 tidy 재생성. **변경 전후 diff 출력**: 행 수 1160 유지, 변경은 2024-04-01 4행의 event_context뿐이어야 함.
  - by_type 265행 `2024.04.01(월)`의 trailing 처리 결과를 출력해 단종 매칭(71개)·교차검증 수치에 변동이 없음을 확인.
  - 이후 `03_crossval` → `04_eda` → `05_model` 순차 재실행 성공.
- **기존 결과 영향**: event_context 4행 정정 외 없음(예상). cycle_days·단종·카테고리 불변.

## 작업 4 — 그림 표시 개선 (Minor)

**수정 대상**: `04_eda.ipynb` Q2 히스토그램 셀, `05_model.ipynb` 산점도 셀.

- `q2_cycle_hist.png`: 장기 구간(예: 365일 초과)을 마지막 빈으로 합치거나 x축 상한 + "최대 2030일, 장기휴면 2건은 원값 유지(Phase 5 결정)" 한글 주석.
- `model_pred_vs_actual.png`: 로그 축 적용 또는 축 범위 조정 + 동일 취지 주석. 데이터·지표(MAE) 변경 금지.
- **검증 요구사항**: 두 그림 재생성, 한글 깨짐 없음, MAE 수치 기존과 동일.

## 작업 5 — `data_dictionary.md` 동기화 (Minor)

- 1장 산출물 개요 표에 `03_crossval.ipynb`(교차검증), `04_eda.ipynb`·`05_model.ipynb`(분석·모델, `outputs/figures/` 생성) 행 추가.
- 5장 무결성 기준에 비일요일 11행 예외 명시: 파워업 위크 인라인 7행(2023-01-12~18) + 2024-04-01(월) 4행(원문이 월요일 진행으로 기록).
- 8장 의사결정 로그에 2건 추가: Q3 집계 단위(고유 `reward_raw`) 확정, `(요일)` 헤더 파싱 정정.

## 검증 기준

- `python -m pytest -q` 전체 통과(기존 33 + 신규 파싱 케이스).
- `02 → 03 → 04 → 05` 노트북 커널 재시작 후 순차 재실행 성공.
- tidy 재생성 diff: 1160행 유지, event_context 4행 외 변경 없음.
- Q3 두 그림의 단종 합계 71, 작업 배경 1의 분포와 일치.
- 모든 그림·라벨 한글.

## 작업 우선순위 요약

| 작업 | 대상 | 심각도 | 규모 | 의존 |
|---|---|---|---|---|
| 1 | 04_eda Q3-2 집계 | Critical | ~10줄 | 없음 |
| 2 | 04_eda Q3-1 단위 | Major | ~15줄 | 작업 1과 같은 셀 |
| 3 | parse.py + 테스트 + tidy 재생성 | Major | ~20줄 | 없음(재실행은 1·2 이후) |
| 4 | 그림 표시 2종 | Minor | ~10줄 | 없음 |
| 5 | data_dictionary 동기화 | Minor | 문서 ~20줄 | 1~3 확정 후 |

## 이번 범위 제외 항목

- 최종 리포트(`outputs/report/`) 작성 — Phase 10 통과 후 Phase 11에서 진행.
- 추가 EDA 질문(Q4~Q6) — 발표 분량 판단 후 필요 시.
- 모델 고도화·피처 추가 — 보조 목표 범위 밖(CLAUDE.md).
- `time_limited` 분석 — 비결측 20/1160으로 분석 부적합(Phase 9에서 확정).
- 단종 표기의 시점 해석(2024~2025 마지막 등장 9건) — 데이터 수정 아닌 발표 해석 문제로, 사용자 결정 대기.
