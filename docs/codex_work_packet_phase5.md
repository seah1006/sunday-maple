# Codex Work Packet — Phase 5 (cycle_days 피처 + 무결성/재현성 정리)

> 입력: `docs/phase5_design.md`(설계 초안) + Phase 4 handoff 리뷰. 사용자가 §1 결정 2건 확정. Phase 4 판정 = 통과.

## 작업 배경

Phase 4에서 `data/processed/tidy_rewards.csv`(정규화·카테고리·강도) 산출 완료. 리뷰에서 확정된 사실과 사용자 결정:

### 사용자 확정 결정
| # | 결정 | 선택 | 사양 반영 |
|---|---|---|---|
| 1 | 관측 단위 / norm 입도 | **raw=관측단위, norm=라벨** | 무결성 기준을 `(date, reward_raw)` 유일로 채택. `(date, reward_norm)` 중복 56쌍은 "같은 슬롯 동반 지급된 별개 보상"으로 정당 허용·문서화 |
| 2 | 미래 빈 블록 12행 | **유지 + 플래그** | processed에 유지(`is_future=True`로 구분). 변경 없음, 문서화만 |

### Claude 직접 검증 사실
1. `python -m pytest -q` → 24 passed(재실행 확인).
2. `(date, reward_raw)` 전역 **유일(중복 0)**. `(date, reward_norm)` 중복 56쌍은 **100% norm-묶음**(서로 다른 reward_raw가 같은 norm으로 통합). 최대 기여: 몬스터컬렉션 38일(등록확률+모몽), 돌발미션 7, 룬·버닝·우르스·솔에르다_접속 등.
3. `reward_norm` 결측 42 = no_event_week 30 + 미래 빈 블록 12. 정상 분해.
4. **`src/collect.py`는 이미 raw 불변 가드 보유**: `collect_main`/`save_raw_html`이 파일 존재 시 fetch·overwrite 생략(skip-if-exists). `data/raw/`는 git 커밋됨. → `collect_main('data/raw')` 재실행 후 `git status data/raw/` **변경 없음** 확인. **01은 idempotent하고 안전**. 코드 수정 불필요, 문서화만.
5. by_type는 `stated_cycle_days`(원문 `(+N일)`)를 (reward_raw, date)별로 보유 → cycle_days 교차검증 기준으로 사용 가능.

## 제약 조건

- `data/raw/` 불변. 기존 `python -m pytest -q` 전부 통과 유지. Phase 4 산출 스키마(`tidy_rewards.csv` 기존 컬럼) 유지 — **컬럼 추가만**.
- `src/parse.py`, `src/normalize.py` 공개 함수 시그니처 유지(필요 시 추가만).
- 노트북 02 커널 재시작 후 순차 재실행 성공 유지. `data/interim`는 재생성 전제.
- decision 1·2를 코드와 문서에 일관 반영. norm-묶음 중복을 **제거하지 말 것**(정당 허용).

---

## 작업 1 — `cycle_days` 피처 산출 (`src/features.py` 신규)

**수정 대상**: `src/features.py`(신규), `tests/test_features.py`(신규), `notebooks/02_parse_clean.ipynb`(통합), `data/processed/tidy_rewards.csv`(컬럼 추가).

### 1-A. 정의 (decision-1 정합)

`cycle_days` = **직전 동일 `reward_norm` 등장일로부터의 경과일**(보상 *타입* 재등장 주기). decision-1에 따라 norm은 분석 라벨이므로 cycle은 norm 단위로 산출하되, norm-묶음(같은 날 같은 norm 다건)은 **고유 (date, reward_norm)로 축약 후** 계산한다.

```python
def compute_cycle_days(tidy: pd.DataFrame) -> pd.Series:
    """reward_norm별 직전 등장일 대비 경과일. tidy 인덱스에 정렬된 Series 반환.
    - reward_norm이 null(no_event/future)인 행은 NaN.
    - 같은 (date, reward_norm) 다건은 동일 cycle_days(해당 norm의 직전 고유일 대비) 공유.
    - 각 norm의 첫 등장은 NaN.
    """
```
구현 가이드:
1. `d = tidy[tidy['reward_norm'].notna()]`의 고유 `(date, reward_norm)` 추출, `date` 오름차순.
2. `groupby('reward_norm')['date'].diff().dt.days` → 고유일 기준 cycle.
3. 원본 tidy에 `(date, reward_norm)` 기준 merge로 되붙임(묶음 행은 같은 값 공유). null norm 행은 NaN.
4. `date`는 datetime으로 변환해 일수 계산. 결과는 정수 또는 NaN(Int64 nullable 권장).

### 1-B. 교차검증 (parse 무결성, 저장 안 함 — 출력만)

raw 단위 cycle을 직접 계산해 by_type `stated_cycle_days`와 대조(파싱 신뢰도 확인):
- `parsed_by_type`(이미 02에서 생성)의 `(reward_raw, date, stated_cycle_days)`와, tidy에서 `reward_raw`별 `date.diff()`로 계산한 raw-cycle을 `(reward_raw, date)`로 조인.
- **불일치 건수와 사례를 출력**. 명칭변경 경계(예: 현상금 폴로와프리토→에스페시아)에서 raw가 바뀌어 NaN/불일치가 나는 것은 예상됨 — 그 외 불일치가 있으면 목록 출력(판정은 Claude).

### 1-C. 검증 요구사항 (tests/test_features.py)

- `test_cycle_days_basic`: 소형 픽스처(한 norm이 3개 날짜) → 기대 경과일(첫 NaN, 이후 일수) 일치.
- `test_cycle_days_bundled_same_day`: 같은 (date, norm) 2건 입력 → 두 행이 같은 cycle_days, 직전 *고유일* 기준.
- `test_cycle_days_null_norm`: reward_norm NaN 행 → cycle_days NaN.
- `test_cycle_days_first_occurrence_nan`: 각 norm 첫 등장 NaN.

## 작업 2 — 무결성 기준 정리 + 문서화

**수정 대상**: `notebooks/02_parse_clean.ipynb`(무결성 셀 보강), `data_dictionary.md`.

### 2-A. 노트북 무결성 셀 (assert + 출력)

decision-1 반영:
- `assert tidy[tidy['reward_raw'].notna()].duplicated(['date','reward_raw']).sum() == 0` — **(date, reward_raw) 유일이 무결성 기준**.
- `(date, reward_norm)` 중복 건수는 **출력하되 제거하지 않음**. norm-묶음으로 정당함을 마크다운에 명시. 묶음 상위 norm(몬스터컬렉션 38 등) 표 출력.
- `reward_norm` 결측 = no_event_week + is_future 분해 출력(`assert 결측 == no_event_week_수 + future_empty_수`).
- `cycle_days` 음수 0건, 비현실적 대값(예 >1500일) 사례 출력(단종 후 부활 등 설명 가능 여부 확인용).

### 2-B. data_dictionary.md 갱신

- `cycle_days` 컬럼 정의 추가(norm 단위, 고유일 기준, 첫 등장 NaN).
- decision-1 기록: 관측 단위 = `reward_raw`, 무결성 키 = `(date, reward_raw)`. `(date, reward_norm)` 중복은 동반 지급으로 허용(예시 norm·근거 표).
- decision-2 기록: 미래 빈 블록 12행 유지, `is_future`로 구분, 분석 시 필터 권장.
- **CLAUDE.md의 무결성 항목 "동일 (date, reward_norm) 중복 없는가"는 raw 단위로 재해석됨**을 data_dictionary에 명시(주: CLAUDE.md 파일 자체는 수정하지 말 것 — governance 파일. data_dictionary에서 정정·근거 기록).

## 작업 3 — 01 재현성 문서화 (코드 변경 없음)

**수정 대상**: `notebooks/01_collect.ipynb`(마크다운 셀만).

- `collect_main`이 skip-if-exists로 idempotent하며 `data/raw/`가 커밋되어 있어 **01 재실행이 raw를 덮어쓰지 않음**을 마크다운으로 명시(검증: `git status data/raw/` 무변경).
- 재크롤이 필요한 경우 raw 파일을 의도적으로 비운 뒤 실행해야 함을 주석. **코드/원본 수정 금지.**

## 작업 4 — 교차검증 재확인 (파워업 위크 반영)

**수정 대상**: `notebooks/03_crossval.ipynb`(재실행 + 출력 확인).

- 파워업 위크 8행이 by_date에 편입된 후 by_type vs by_date 보상 등장 횟수 재집계.
- Phase 3 대비 by_type-only 불일치가 **감소**했는지(파워업 8건이 양쪽에 존재) 출력으로 확인. 변화 요약을 handoff에 기재.
- 코드 의도 변경 없이 재실행 결과만 보고.

---

## 검증 기준

- `python -m pytest -q` 전부 통과(기존 + `test_features.py`).
- 노트북 02 커널 재시작 후 재실행 성공, 2-A assert 통과((date,raw) 유일, 결측 분해, cycle 음수 0).
- `tidy_rewards.csv`에 `cycle_days` 컬럼 추가, 기존 컬럼·행 수 보존.
- 03_crossval 재실행, 파워업 반영 후 불일치 변화 리포트.
- `data_dictionary.md`에 cycle_days·decision-1·decision-2 문서화.

## 작업 우선순위 요약

| 작업 | 대상 | 규모(예상) | 의존 |
|---|---|---|---|
| 1 | `src/features.py` + `tests/test_features.py` + 02 통합 | 신규 ~120줄 | tidy_rewards |
| 2 | 02 무결성 셀 + `data_dictionary.md` | +40줄 | 작업1 |
| 3 | 01 마크다운 노트 | +5줄 | 없음 |
| 4 | 03_crossval 재실행 | 출력만 | 작업 무관 |

## Claude 방법론 결정 (리뷰 포인트)

- `cycle_days`를 **norm 단위·고유일 기준**으로 산출(raw 단위 아님). 근거: decision-1에서 norm=분석 라벨, "보상 타입 재등장 주기"가 분석 목표("등장 패턴")에 부합. 명칭변경으로 raw가 바뀌어도 norm은 연속되어 주기가 끊기지 않음. raw 단위 gap은 by_type와의 교차검증(1-B)에만 사용. **이 결정에 이견 있으면 리뷰에서 조정.**

## 이번 범위 제외 항목

- `is_discontinued` by_type→tidy 병합(키 정합 별도 필요) — Phase 6.
- EDA(03_eda)·예측 모델(04) — cycle_days 확정 후.
- norm-묶음 중복의 dedup — decision-1에서 허용으로 종결(재론 안 함).
- 계절성·빈도 등 추가 피처 — EDA 단계에서 필요 시.
