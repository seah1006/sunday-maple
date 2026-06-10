# Codex Work Packet — Phase 7 (is_discontinued 정확성 수정 + 노트북 전면 한글화)

> 입력: Phase 6 handoff 리뷰. Phase 6는 **단종 11개 오표기 결함**으로 보강 필요(통과 보류). 추가로 발표자료용 노트북 한글화 지시. **CLAUDE.md "발표자료 언어(한글)" 규칙 신설됨** — 이후 모든 노트북 비코드 텍스트는 한글.

## 작업 배경

### 작업 1 배경 — is_discontinued 오표기 (Phase 6 Critical 확정)

Phase 6에서 `is_discontinued`를 by_type → tidy로 **exact reward_raw**로 병합했으나, tidy 단종 True 고유 raw가 71이 아닌 60이었다. Claude 직접 재검증 결과:

- 차이 11개는 **전부 tidy에 trailing-제거된 문자열로 존재**하며 **현재 `is_discontinued=False`로 잘못 표기**됨(by_type 전용 0개). → 정확성 결함.
- 원인: `parse_by_type._parse_type_header`는 헤더 끝 괄호를 reward_raw에 **유지**(`돌발미션 일일 클리어 가능 횟수 2배(3회→6회)`)하지만, `parse_by_date`는 `_split_trailing`으로 끝 괄호를 `reward_trailing`으로 **분리**(`돌발미션 일일 클리어 가능 횟수 2배` + `(3회→6회)`). 두 뷰의 reward_raw 문자열이 달라 exact 병합이 실패.
- 영향 11종: 돌발미션 횟수 2/3/5배, 룬 경험치 버프 지속시간 2배, 보스파티 결성 버프 효과 증가, 엘리트 마일리지 꾸러미 4배, 강력한/영원한 환생의 불꽃 5개…지급, 사냥 엘리트 몬스터 수 증가(1마리→2마리), 월드 통합 파티퀘스트 입장 2배, 파티 포인트 5배.
- Codex가 임의 alias 보정을 거부하고 Critical로 보고한 것은 **올바른 처신**.

**중요 추가 발견(Claude)**: `사냥 시 소환되는 엘리트 몬스터 수 증가`는 by_date에서 단일 reward_raw(body)로 합쳐지지만 `reward_trailing`이 `(1마리→2마리)`(단종)와 `(1마리→3마리)`(현행, active)로 갈린다. 즉 **이 보상은 같은 reward_raw 안에서 단종/비단종이 혼재**한다. 따라서 is_discontinued는 reward_raw 단위가 아니라 **(reward_raw + reward_trailing) = 원문 전체 문자열 단위**로 판정해야 하며, Phase 6 packet의 "동일 reward_raw 혼재 0" 가정은 **이 한 건에서 성립하지 않음**(정상).

### 작업 2 배경 — 발표자료 한글화

노트북 마크다운이 영어로 작성됨(01·02·03), 02에는 깨진 한글 셀(`## ?? ??`) 1개 존재. `print`/`display` 출력 라벨도 영어. 발표자료이므로 비코드 텍스트 전부 한글화. (CLAUDE.md 신설 규칙 적용.)

## 제약 조건

- `data/raw/` 불변. 기존 `python -m pytest -q` 전부 통과 유지. tidy 기존 컬럼·1160행 보존(작업1은 기존 `is_discontinued` 값 정정, 컬럼 추가 아님).
- `src/parse.py`/`normalize.py` 공개 시그니처 유지. `features.py`는 `merge_is_discontinued` 수정 허용(시그니처 유지).
- 데이터 값(`reward_raw` 등 원문 문자열)·코드 로직·식별자 변경 금지(작업2는 텍스트만).
- 노트북 02 커널 재시작 후 순차 재실행 성공 유지.

---

## 작업 1 — is_discontinued 이중 키(원문 전체 문자열) 병합으로 수정

**수정 대상**: `src/features.py`(`merge_is_discontinued`), `tests/test_features.py`, `notebooks/02_parse_clean.ipynb`(무결성 출력), `data/processed/tidy_rewards.csv`(값 정정).

### 1-A. 수정 로직

`merge_is_discontinued(tidy, parsed_by_type)`를 다음 규칙으로 정정:

1. `DISC = set(parsed_by_type.loc[parsed_by_type.is_discontinued, 'reward_raw'].unique())` (단종 by_type 원문, 71개).
2. tidy 각 행에 대해, **두 형태 중 하나라도 DISC에 있으면 True**:
   - `reward_raw` (trailing 분리된 body)
   - `reward_raw + (reward_trailing or '')` (원문 전체 재구성 — by_date split이 body와 trailing 사이 공백을 만들지 않으므로 단순 결합이 by_type 원문과 일치)
3. `reward_raw`가 null(no_event/future)인 행은 `pd.NA`.
4. 그 외(어느 형태도 DISC에 없음)는 `False`.

> 이 규칙이 세 경계 사례를 모두 해소함(테스트로 고정):
> - `데미지 스킨 선택 지급`: by_type가 body 형태(끝 괄호 없음) → **body 매칭**으로 True. (by_date trailing은 `(샤방샤방/…)` 변형이라 전체결합은 불일치하지만 body로 잡힘.)
> - `돌발미션 일일 클리어 가능 횟수 2배`: by_type가 `…2배(3회→6회)` → **전체결합 매칭**으로 True.
> - `사냥 시 소환되는 엘리트 몬스터 수 증가` + `(1마리→2마리)` → 전체결합이 DISC에 있어 True; 같은 body + `(1마리→3마리)`는 DISC에 없어(active) False. **같은 reward_raw가 행별로 갈림(정상)**.

### 1-B. 검증 요구사항 (tests/test_features.py)

기존 테스트 유지 + 추가:
- `test_disc_body_form_match`: by_type가 body 형태(데미지 스킨류) → True.
- `test_disc_fullstring_match`: by_type가 끝괄호 포함(돌발미션 2배(3회→6회)) → tidy body+trailing로 True.
- `test_disc_same_raw_split_by_trailing`: 같은 reward_raw, trailing `(1마리→2마리)`=True / `(1마리→3마리)`=False (혼재 허용).
- `test_disc_null_and_active`: reward_raw null → NA; DISC에 없는 active raw → False.

### 1-C. 노트북 무결성 출력 (정정)

- `is_discontinued=True` 고유 **(reward_raw, reward_trailing) 조합** 수가 **71과 일치**하는지 확인(reward_raw 단위 아님). 불일치 시 차이 출력.
- "동일 reward_raw 혼재" 검사는 **제거 또는 완화**: 혼재가 발생하는 reward_raw 목록을 출력하고, `사냥 시 소환되는 엘리트 몬스터 수 증가` 1건만 정상 혼재임을 마크다운으로 설명. 그 외 혼재가 있으면 경고.
- True/False/NA 분포 출력.

### 1-D. data_dictionary.md 정정

- `is_discontinued` 정의를 **"원문 전체 문자열(reward_raw + reward_trailing) 단위 보상 속성"**으로 수정. 엘리트 몬스터 수 증가가 같은 reward_raw 안에서 단종/현행으로 갈리는 예외를 근거와 함께 명시. Phase 6의 raw-단위 서술을 정정.

---

## 작업 2 — 노트북 비코드 텍스트 전면 한글화 (발표자료)

**수정 대상**: `notebooks/01_collect.ipynb`, `notebooks/02_parse_clean.ipynb`, `notebooks/03_crossval.ipynb`.

CLAUDE.md "발표자료 언어(한글)" 규칙대로:

1. **모든 마크다운 셀을 한글로** 작성/번역. 영어로 된 기존 마크다운(예: 01 "Phase 1 raw collection", "Reproducibility notes"; 02 "Phase 6 parse, normalize…", "Phase 6 schema decisions"; 03 "Cross-validation A/B", "Reward inventory" 등) 전부 한글로.
2. **깨진 한글 셀 복구**: `02_parse_clean.ipynb`의 `## ?? ??`로 시작하는 마크다운 셀(저장 결과 요약)을 올바른 한글로 재작성. 의미는 해당 셀 직전 코드(중간 산출물 저장·검증)에 맞춰 복원.
3. **`print`/`display` 출력 라벨 문자열을 한글로**: 화면에 보이는 라벨/메시지(예: `'total rows:'`, `'cycle_days non-null rows:'`, `'category counts:'`, `'powerup week rows:'`, `'date min:'` 등)를 한글로(예: `'전체 행 수:'`, `'cycle_days 비결측 행:'`). **f-string의 변수·표현식, 컬럼명, 함수·변수 식별자, 로직은 그대로 둔다.** 컬럼명이 한글인 출력(`category` 분포 등 데이터 값)은 변경 불필요.
4. **데이터 값·코드 식별자 불변**: `reward_raw` 원문, norm 문자열, 변수/함수명은 절대 변경 금지.

### 검증 요구사항

- 세 노트북 커널 재시작 후 순차 재실행 성공(01은 idempotent, raw 불변 확인).
- 재실행 후에도 작업1 무결성 assert·수치가 동일(텍스트 변경이 로직에 영향 없음).
- 마크다운 셀에 영문 문장이 남아있지 않음(고유명사·코드 토큰 제외). 깨진 `?` 문자열 0.

---

## 검증 기준

- `python -m pytest -q` 전부 통과(기존 + 작업1 추가 테스트). 단종 True 조합 수 71 확인.
- 노트북 01·02·03 커널 재시작 후 재실행 성공. 02 무결성 출력에서 is_discontinued 정정 반영(11종이 True로).
- `tidy_rewards.csv`의 `is_discontinued`가 11종에 대해 True로 정정, 행 수·기타 컬럼 보존.
- 노트북 비코드 텍스트 전부 한글, 깨진 셀 복구.
- `data_dictionary.md` is_discontinued 정의 정정.

## 작업 우선순위 요약

| 작업 | 대상 | 규모(예상) | 의존 |
|---|---|---|---|
| 1 | features.py + test + 02 무결성 + data_dictionary | ~50줄 | parsed_by_type, tidy |
| 2 | 01·02·03 노트북 텍스트 한글화 | 텍스트 다수 | 작업1(02 재실행) |

## 이번 범위 제외 항목

- EDA(03_eda)·예측 모델(04) — tidy 스키마·정합 확정 후 별도 Phase.
- norm 단위 is_discontinued 집계 — 필요 시 EDA에서 파생.
- 출력 라벨 한글화 시 데이터 값/식별자 변경 — 금지.
