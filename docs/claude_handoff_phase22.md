# Phase 22 구현 인계

## 작업 범위

`docs/codex_work_packet_phase22.md` 작업 1~4: Phase21 Minor 2건, Vite + React + TS, 공통 데이터 계약·표시 헬퍼, 예측/적중/이력 화면, 테스트와 로컬 빌드·preview. 커밋·배포·수집·노트북 변경은 하지 않았다.

## 구현 요약

- 작업 1 완료: `src/site_data.py`의 appearances를 `group.date.nunique()`로 변경했다. per_date rf_hit을 nullable Int64로 변환한 뒤 JSON으로 내보내 정수 또는 null을 보장한다. `tests/test_site_data.py`에서 이력 고유 날짜 수와 등장 횟수 일치, 정수 타입을 검증한다. Prophet 포함 CLI로 5개 JSON 재생성했다.
- 작업 2 완료: create-vite react-ts로 web 생성. `scripts/sync-data.mjs`를 predev/prebuild에 연결했다. `types.ts`, `data.ts` 병렬 5 JSON fetch, `format.ts` 중앙 표시 헬퍼 추가. base `./`, BASE_URL fetch, HashRouter 사용.
- 작업 3 완료: `App.tsx` 공통 레이아웃·예측 화면, `Records.tsx` 적중 기록·이력 화면, `index.css` 반응형 CSS. 메인 상위5 카드/나머지/접이식 Prophet·제외 후보, 과거 데이터 기준일과 생성 시각, 보정 확률 아님 안내를 표시한다. 적중 방법별 막대와 최신순 회차 표·실제/예측 교집합 강조를 추가했다. 이력 원문·표시명 검색+카테고리 필터+50개 단위 더 보기와 보상 통계 모든 열 정렬을 구현했다. 표는 좁은 화면에서 컨테이너 내 가로 스크롤한다. 푸터 출처·비공식 문구 포함.
- 작업 4 완료: 실제 JSON 축약 고정 픽스처, 표시 헬퍼/화면/Prophet null/검색/필터/정렬/레이아웃/오류 안내 테스트. CLAUDE.md 개발 환경에 프론트 명령만 추가했다.
- 메시지 합의: **create-vite 9.3.1 기본 린터가 oxlint라 그대로 사용**. ESLint로 교체하거나 관련 의존성을 추가하지 않았다. 설치된 Node 24.22.1, npm 11.17.0 확인. 템플릿 기본 React 19.3.1, Vite 8.3.5와 사양의 router·Vitest·Testing Library·jsdom만 사용한다. package-lock.json 생성.
- 코드 주석·docstring을 추가하지 않았고 템플릿 tsconfig 주석도 제거했다. 데모 SVG와 App.css 삭제, README를 로컬 실행 안내로 대체했다.

## 검증 결과

- `py -m pytest -q -p no:cacheprovider`: **61 passed, 9 warnings in 18.64s** (기존59 + 신규2). 경고는 종전 pandas deprecation/로지스틱 수렴 경고다.
- `py -m src.site_data --out data/site`: Prophet 포함 종료 코드 0. 기존 예보/지표 변경 없음.
- `npm run lint`: oxlint **0 warnings, 0 errors**.
- `npm run test -- --run`: **2 files, 11 tests passed**, 2.31초.
- `npm run build`: tsc + Vite 성공. Vite 빌드 205ms. JS 268.90KB(gzip85.52KB), CSS 6.37KB(gzip2.12KB), HTML 0.63KB. 데이터 포함 `web/dist` **587226바이트**.
- preview: **http://127.0.0.1:4173/**, `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort` 실행 중(exec session1005). 검토를 위해 종료하지 않았다. 경로 `/#/track`, `/#/history`.
- preview `/`와 `/data/forecast.json` HTTP **200** 확인.
- `git check-ignore`로 web/node_modules/react/package.json, web/dist/index.html, web/public/data/meta.json 무시 확인.
- 수정 범위: .gitignore, CLAUDE.md 개발 환경, src/site_data.py, tests/test_site_data.py, data/site/{meta,backtest,rewards}.json, web/, 본 인계 문서만. raw/processed/notebooks 및 다른 src 모듈 불변.
- 서브에이전트 UI 조작 금지에 따라 브라우저·스크린샷은 수행하지 않았다. 상위 Claude에게 preview 주소를 보내 375px/1280px 시각 확인을 요청했다. CSS에는 600px/900px 브레이크포인트를 두었다.

## 데이터 상태

- data_through 2026-06-14, backtest_data_through 2026-06-07, target_date 2026-06-21 유지. history 460회차, rewards 48개, classifier 10개 유지.
- 등장 횟수 변경 전 상위5: 룬_경험치버프90, 콤보킬_경험치87, 몬스터파크_경험치84, 몬스터컬렉션78, 현상금_경험치77.
- 변경 후 상위5: 룬_경험치버프88, 콤보킬_경험치87, 몬스터파크_경험치83, 현상금_경험치77, 불꽃늑대_경험치74. 몬스터컬렉션은 고유 날짜 기준40회.
- hit 75회차는 정수0/1 또는 null. 판정 불가 행은 프론트에 '판정 불가'로 표시한다.
- 예보/이력 JSON 내용은 불변. meta 생성 시각과 집계 수정 JSON만 갱신됐다. 모델 데이터 재수집 없음.

## Claude 리뷰 요청

- **Critical**: 없음. 미해결 사양 질문 없음.
- **Major**: preview에서 실제 375px/1280px 시각 확인을 부탁드립니다. 서브에이전트는 UI 상호작용 없이 구현·테스트·HTTP 검증만 수행했습니다.
- **Minor**: 과거 백테스트임을 화면에 추가로 명시했습니다. 모델 점수는 JSON 3자리값을 100배해 소수1자리로 표시합니다. 최신 회차 수집·사전 예측 저장·배포는 후속 Phase 범위입니다.
