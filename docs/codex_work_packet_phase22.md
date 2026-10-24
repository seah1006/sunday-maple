# Codex Work Packet — Phase 22 (프론트엔드 골격: Vite + React + TS)

> Phase 21 후속. Phase 21이 만든 `data/site/*.json`을 읽는 정적 사이트를 `web/`에 만든다. 메인은 **다음 선데이 예측**이다. 이번 Phase는 로컬 실행과 빌드까지만 한다. 배포·Actions·신규 회차 수집은 하지 않는다.

## 작업 배경

### Phase 21 리뷰 결과 (Claude, 2026-10-24)

- 판정: **통과**. 59 passed(Claude 재실행 확인), `py -m src.site_data` Prophet 포함 22초.
- 메시지 합의 사항(사양 정정): 학습·백테스트는 raw tidy만, 수동 관측 결합 tidy는 예보·history·rewards에만 쓴다. `meta.backtest_data_through` 추가.
- 환경 차이: pandas 3.1.0 / scikit-learn 1.9.1에서는 원본 08 코드도 RF 개별 점수가 다르게 나온다(Claude가 원본 08 코드를 재실행해 확인). 06-21 RF 1위 몬스터컬렉션 66.7%. `date_hit_rate` 5개는 불변. `requirements.txt` 버전 고정.
- 리뷰 지적 (이번 Phase 작업 1에서 처리):
  - Minor 1: `rewards.json`의 `appearances`가 행 수로 세어진다. 날짜별로 같은 `reward_norm`이 2행 이상인 회차가 54개라 등장 횟수가 부풀려진다. **고유 날짜 수**로 바꾼다.
  - Minor 2: `backtest.json` `per_date[].hit`이 `0.0/1.0` 실수다. `0/1` 정수(또는 `null`)로 바꾼다.

### JSON 계약 (Phase 21 출력, Claude 확인)

- `meta.json`: `generated_at, data_through, backtest_data_through, target_date, sources[{name, url?, path?, fetched_at?}], split_cutoff, random_seed`
- `forecast.json`: `target_date, classifier[{rank, reward_norm, category, score(0~1), days_since_last, last_seen}], prophet[{reward_norm, yhat, rank}] | null, excluded[{reward_norm, reason: "recency_gate"|"domain_discontinued"}]`
- `backtest.json`: `split_cutoff, metrics[{method, label, accuracy?, f1?, roc_auc?, date_hit_rate}], per_date[{date, actual[], predicted[], hit}]` (75개 날짜)
- `history.json`: 날짜 내림차순 `[{date, event_context|null, is_special, rewards[{reward_raw|null, reward_norm, category}]}]` (460개, 259KB)
- `rewards.json`: `[{reward_norm, category, appearances, first_seen, last_seen, median_cycle_days|null, is_discontinued}]` (48개)
- 카테고리 값: 강화, 성장, 사냥효율, 수집기타, 스페셜 (실제 값은 JSON에서 확인 후 사용)

### 현재 데이터 상태와 표시 원칙

- 데이터는 2026-06-14까지라 예측 대상 06-21은 이미 지난 날짜다. 화면에 **데이터 기준일**(`data_through`)과 **생성 시각**을 항상 보여 준다. 수집 갱신은 Phase 23.
- `score`는 보정된 확률이 아니다. UI에서 "확률"이라고 쓰지 말고 "모델 점수"로 표기하고, 짧은 설명을 붙인다(리포트 §6 문구 참고: "상위 후보는 검토 우선순위일 뿐 확정 예보가 아니다").
- 보상 표시명은 이번 Phase에서 `reward_norm`의 `_`를 공백으로 바꾼 값으로 한다(`displayName()` 한 곳에서 처리해 나중에 사전으로 교체 가능하게).
- 사이트는 비공식 팬 프로젝트다. 푸터에 출처(인벤 원글 링크, 메이플스토리 공식 공지)와 "넥슨과 무관한 비공식 프로젝트" 문구를 넣는다.

### 환경

- 이 PC에는 Node.js가 없을 수 있다. 작업 시작 전에 `node -v`, `npm -v`로 확인하고, 없으면 **설치하지 말고 바로 Claude에게 메시지로 알린다**(설치는 사용자 승인 사항).
- Python은 `py` 런처. 셸은 PowerShell 7.

## 제약 조건

- 수정 범위: 새 디렉터리 `web/`, `src/site_data.py`(작업 1 한정), `tests/test_site_data.py`, `data/site/*.json`(재생성), `.gitignore`, `CLAUDE.md`의 '개발 환경' 절(프론트 명령 추가만).
- `data/raw`, `data/processed`, 노트북, 다른 `src` 모듈 수정 금지. Python 테스트 59개 통과 유지.
- 프론트 의존성은 최소: `react`, `react-dom`, `react-router-dom`, 개발용 `vite`, `typescript`, `@vitejs/plugin-react`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, Vite 템플릿 기본 ESLint 구성. **차트·UI 라이브러리·CSS 프레임워크 추가 금지**(막대는 CSS로). 추가가 꼭 필요하면 먼저 묻는다.
- 라우팅은 `HashRouter`(GitHub Pages 새로고침 404 회피). Vite `base`는 `"./"`로 두고 데이터는 `import.meta.env.BASE_URL + "data/..."`로 fetch한다.
- UI 문구 한글. 코드 식별자 영어. 코드 주석·docstring 금지(기존 규칙, TS도 동일).
- 모바일(375px)과 데스크톱(1280px) 모두 깨지지 않게.

## 작업 1 — Phase 21 Minor 2건 수정 (`src/site_data.py`)

- `rewards[].appearances` = 해당 `reward_norm`이 등장한 **고유 날짜 수**.
- `backtest.per_date[].hit` = `1`/`0` 정수, 판정 불가는 `null`.
- 테스트: `tests/test_site_data.py`에 `appearances`가 `history.json`에서 센 고유 날짜 수와 같은지, `hit`이 `{0, 1, None}` 중 하나인지 추가.
- `py -m src.site_data --out data/site`로 재생성하고 변경 전후 `appearances` 상위 5개를 handoff에 기록.

## 작업 2 — `web/` 스캐폴드와 데이터 연결

- `npm create vite@latest web -- --template react-ts`로 생성 후 불필요한 데모 자산 제거.
- `web/scripts/sync-data.mjs`: `../data/site/*.json`을 `web/public/data/`로 복사. `package.json`의 `predev`, `prebuild`에 연결. `web/public/data/`는 `.gitignore`에 추가(원본은 `data/site/` 하나만 추적).
- `web/src/types.ts`: 위 JSON 계약의 TS 타입.
- `web/src/data.ts`: `loadSiteData()` 한 함수로 5개 JSON을 병렬 fetch. 실패 시 화면에 한글 오류 메시지.
- `web/src/format.ts`: `displayName(rewardNorm)`, `formatScore(score)`(예: `66.7`), `formatDate()`, `daysAgo()` 등 표시 헬퍼.

## 작업 3 — 화면 3개 + 공통 레이아웃

1. **레이아웃**: 헤더(사이트 이름 "썬데이 메이플 예보", 메뉴: 예측 / 적중 기록 / 역대 이력), 기준일 배지(`데이터 기준 2026-06-14 · 생성 …`), 푸터(출처·비공식 문구).
2. **예측 `/`** (메인)
   - 제목: `{target_date} 썬데이 메이플 예측`.
   - 상위 5개 카드: 순위, 표시명, 카테고리 배지, 모델 점수 막대(CSS width %), "마지막 등장 N일 전 (YYYY-MM-DD)".
   - 나머지 후보 목록(6위~).
   - Prophet 비교: 접을 수 있는 섹션, 상위 5개와 `yhat`. `prophet`이 `null`이면 섹션 숨김.
   - 제외 후보: 접을 수 있는 섹션, 사유 한글화(`recency_gate` → "180일 넘게 미등장", `domain_discontinued` → "단종 처리").
   - 점수 설명 한 문단(보정 확률 아님).
3. **적중 기록 `/track`**
   - 방법별 `date_hit_rate` 비교(막대, 랜덤포레스트·Prophet 강조). 정의 한 줄: "실제 보상 수 k만큼 상위 k개를 뽑았을 때 하나라도 맞힌 회차 비율".
   - 회차별 표: 날짜, 실제, 예측, O/X. 최신순. 맞힌 보상은 강조.
   - 범위 안내: "2025-01-01 이후 회차, 학습은 그 이전 데이터만 사용".
4. **역대 이력 `/history`**
   - 날짜별 목록(최신순). 각 회차에 이벤트 맥락, 스페셜 여부, 보상 목록(`reward_raw`가 있으면 원문, 없으면 표시명).
   - 검색창(원문·표시명 부분 일치)과 카테고리 필터. 460회차라 한 번에 50개씩 "더 보기".
   - 보상별 통계 표(`rewards.json`): 표시명, 카테고리, 등장 횟수, 첫/마지막 등장, 주기 중앙값, 단종 여부. 열 클릭 정렬.

## 작업 4 — 테스트와 검증

- Vitest + Testing Library: `format.ts` 단위 테스트, 각 화면이 고정 픽스처 JSON(`web/src/__fixtures__/`, 실제 JSON에서 축약)으로 핵심 텍스트를 렌더하는지(예: 메인에 `몬스터컬렉션`과 `66.7`, 적중 기록에 `0.449`, 이력 검색 후 결과 수 변화).
- 명령: `npm run lint`, `npm run test -- --run`, `npm run build`가 모두 성공.
- `npm run preview` 또는 `npm run dev`로 띄운 주소와 포트를 handoff에 적는다(Claude가 브라우저로 화면을 확인한다). 서버는 확인 후 종료해도 된다.
- `CLAUDE.md` '개발 환경'에 `cd web && npm install && npm run dev` 등 프론트 명령을 추가.

## 검증 기준

1. `py -m pytest -q -p no:cacheprovider` 전체 통과(59 + 신규).
2. `py -m src.site_data --out data/site` 성공, Minor 2건 반영 확인.
3. `web/`에서 `npm run lint`, `npm run test -- --run`, `npm run build` 성공. `web/dist/` 크기 기록.
4. `git status`로 수정 범위 밖 변경 없음 확인. `web/node_modules`, `web/dist`, `web/public/data`가 무시되는지 확인.

## 작업 우선순위 요약

| 작업 | 대상 | 예상 규모 | 의존 |
|---|---|---|---|
| 1 | `src/site_data.py` Minor 2건 + 테스트 | 약 10줄 + 테스트 10줄 | - |
| 2 | Vite 스캐폴드, sync-data, types, data, format | 약 150줄 | Node 확인 |
| 3 | 레이아웃 + 화면 3개 + CSS | 약 400~500줄 | 2 |
| 4 | Vitest 테스트, lint/build, CLAUDE.md | 약 150줄 | 3 |

## 이번 범위 제외 항목

- 신규 회차 수집(공식 공지 + 비전 LLM 추출), 백필 — Phase 23.
- GitHub Actions, GitHub Pages 배포, `base` 경로 최종 확정 — Phase 24(배포는 사용자 승인).
- 분석(EDA) 페이지, 방법론 페이지, README — Phase 25.
- 보상 표시명 사전, 다크 모드, 차트 라이브러리.
- `final_report` 수치 갱신(환경 차이) — Phase 25에서 방법론 페이지와 함께.
