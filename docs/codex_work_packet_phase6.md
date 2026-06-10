# Codex Work Packet — Phase 6 (is_discontinued 병합 + tidy 스키마 완성)

> 입력: Phase 5 handoff 리뷰(통과). Phase 5에서 cycle_days까지 추가됨. 본 Phase는 CLAUDE.md 목표 스키마의 마지막 미충족 컬럼 `is_discontinued`를 by_type에서 병합해 tidy 스키마를 완성한다. 이후 EDA(03_eda) 착수 가능.

## 작업 배경

`data/processed/tidy_rewards.csv`(Phase 5, 1160행 13컬럼)는 by_date spine 기반이라 단종 여부 정보가 없다. by_type(`parsed_by_type`)는 `is_discontinued`(원문 `(단종)`/`([[B]]단종)` 마커)를 (reward_raw)별로 보유하며, Phase 3에서 단종 고유 보상 71개로 확정됐다. decision-1(관측 단위 = reward_raw)에 따라 **is_discontinued는 raw 단위 보상 속성**으로 병합한다.

### Phase 5 리뷰에서 확정된 사실 (Claude 직접 재검증)
1. `pytest` 28 passed(재실행). raw 불변(`git status data/raw/` 무출력).
2. `cycle_days`를 **독립 재계산해 CSV 컬럼과 정확히 일치(불일치 0)** — 구현 정확. null 97 = 42(null norm) + 55(norm 첫 등장, 묶음 첫날 포함).
3. `(date, reward_raw)` 중복 0, `(date, reward_norm)` 117행(norm-묶음, decision-1 허용).
4. `cycle_days > 1500` 2건(버닝 2030, 엘리트몬스터_증가 1911)은 **단종-부활 장기휴면의 정확한 값**(직접 등장일 확인). 이상치 아님 → **별도 플래그 없이 원값 유지**(Phase 5 특이질문 종결).
5. `raw cycle missing computed 67건`은 by_type stated vs by_date raw-cycle 대조의 명칭변경·문자열차이 케이스. `raw cycle mismatch 0`(둘 다 존재 시 일치)이 핵심 신호 → 파싱 일관성 양호. norm 단위 cycle이 이 파편화를 회피하므로 **추가 조치 불필요**(출력-only 유지, Phase 5 특이질문 종결).
6. 교차검증 exact match rate 0.6637→0.7257(82/113) 개선(파워업 8행 편입 효과).

## 제약 조건

- `data/raw/` 불변. 기존 `python -m pytest -q` 전부 통과 유지. 기존 tidy 컬럼·행 수(1160) 보존 — **컬럼 추가만**.
- `src/parse.py`/`normalize.py`/`features.py` 공개 시그니처 유지(추가만).
- 노트북 02 커널 재시작 후 순차 재실행 성공 유지.
- decision-1·2 유지. norm-묶음 중복 제거 금지.
- **CLAUDE.md 파일 수정 금지**(governance) — 문서화는 data_dictionary.md.

---

## 작업 1 — is_discontinued raw 단위 병합

**수정 대상**: `notebooks/02_parse_clean.ipynb`(병합 셀 추가), `data/processed/tidy_rewards.csv`(컬럼 추가), 필요 시 `src/features.py`(순수 병합 헬퍼 + 테스트).

### 1-A. 병합 로직

- `parsed_by_type`에서 `(reward_raw → is_discontinued)` 매핑 생성. **주의**: by_type는 한 reward_raw가 단일 단종상태를 가짐(Phase 3 확인, 71개 True). 동일 reward_raw가 by_type에서 상충(True/False 혼재)하면 **에러로 출력**(예상 0건).
- tidy의 `reward_raw`(정제본) 기준 left-join으로 `is_discontinued` 부여.
- **키 정합 주의**: by_type와 by_date의 reward_raw 문자열이 정확히 일치해야 매칭됨. 불일치(명칭변경 변형 등)는 NaN으로 남음. 매칭 실패 행과 고유 reward_raw 목록을 **출력**.
- 매칭 안 된 reward 있는 행(`reward_raw` not null & `is_discontinued` NaN)은 기본값 정책 필요: **`False`로 채우되**(by_type에 단종표기 없으면 active로 간주), 채운 건수와 대상 reward_raw를 출력해 Claude가 검토.
- `no_event_week`/future 빈 행(`reward_raw` null)은 `is_discontinued` NaN 유지.

> 순수 함수로 분리 권장: `merge_is_discontinued(tidy, parsed_by_type) -> pd.Series`(tidy index 정렬). 그러면 `tests/test_features.py`에 단위 테스트 가능.

### 1-B. 검증 요구사항

- `tests/test_features.py`(또는 신규): 소형 픽스처로 ① 단종 reward_raw 행 True, ② 비단종 행 False, ③ reward_raw null 행 NaN, ④ by_type에 없는 raw → False(기본값) 동작 확인.
- 노트북 무결성 출력:
  - `is_discontinued` True/False/NaN 분포. True 고유 reward_raw 개수가 **71과 일치**하는지(by_type 단종 고유 수). 불일치 시 차이 reward_raw 출력.
  - by_type 매칭 실패(NaN→False로 채운) 행 수와 reward_raw 목록.
  - 동일 reward_raw 내 is_discontinued 혼재 0건 assert.

## 작업 2 — 스키마 완성 문서화

**수정 대상**: `data_dictionary.md`.

- `is_discontinued` 컬럼 정의 추가(raw 단위 보상 속성, by_type `(단종)` 기준, 스냅샷 시점 기준 은퇴 여부).
- CLAUDE.md 목표 스키마 대비 tidy 컬럼 매핑 표 갱신(완성 상태 명시). `time_limited`(하루종일/시간제) 등 기존 컬럼 포함 현황 정리.
- Phase 5 특이질문 2건 종결 기록: ① cycle_days>1500은 단종-부활 정상값(원값 유지), ② raw-cycle missing 67은 norm 단위 cycle로 회피, 출력-only 유지.

---

## 검증 기준

- `python -m pytest -q` 전부 통과(기존 + is_discontinued 병합 테스트).
- 노트북 02 커널 재시작 후 재실행 성공, 무결성 출력에서 단종 True 고유 reward_raw = 71 확인, 혼재 0.
- `tidy_rewards.csv`에 `is_discontinued` 컬럼 추가, 기존 컬럼·1160행 보존.
- `data_dictionary.md`에 is_discontinued + 스키마 완성 문서화.

## 작업 우선순위 요약

| 작업 | 대상 | 규모(예상) | 의존 |
|---|---|---|---|
| 1 | 02 병합 셀 + (헬퍼+테스트) | ~60줄 | parsed_by_type, tidy |
| 2 | data_dictionary.md | +20줄 | 작업1 |

## 이번 범위 제외 항목

- EDA(03_eda)·예측 모델(04) — tidy 스키마 완성 후 별도 Phase(설계 초안부터).
- norm 단위 is_discontinued 집계(일부 raw만 단종인 norm) — 필요 시 EDA에서 파생.
- cycle_days 이상치 플래그·raw-cycle 67건 — Phase 5에서 종결, 재론 안 함.
