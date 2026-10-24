# Phase 25 구현 인계 (완료)

## 작업 범위

`docs/codex_work_packet_phase25.md` 기준. 실행 순서: 작업1 → 작업2 README → 작업4 insights → 작업3 about. push·원격설정·데이터재생성·커밋 금지. 사이트는 https://seah1006.github.io/sunday-maple/ 에서 운영 중.

## 구현 요약

- 작업1 완료: weekly.yml의 VISION_*를 collect 단계 env로 제한. notice_review_summary에서 공지·이미지 Markdown 링크와 승인 명령/자동머지 금지 안내 생성. --pr-rows 유지 + Claude 승인으로 --notice-ids 별칭 추가. 데이터 처리·승인 자체는 실행하지 않음.
- 작업2 완료: 루트 README 신규작성. 라이브사이트 링크, Mermaid 파이프라인1개, 결과수치·5개설계판단·실전기록dirty/코드기준8f47363·로컬명령·출처·협업방식 명시.
- 작업4 완료: /insights와 메뉴 추가. q1연도별카테고리/q2주기히스토그램/q3단종카테고리/q8회차보상수 기존PNG4장 동기화. final_report의 결론만 요약하고 2026-06 인벤 기준/당시단종표기 한계 명시. public/figures 복사본은gitignore,원본PNG불변.
- 작업3 완료: /about와 방법론 메뉴 추가. CSS박스6단계흐름, 점수≠보정확률,180일게이트,운영/고정백테스트/실전기록 구분,후보밖·선물·스페셜·이미지추출 한계 설명. 지표는현재backtestJSON을props로표시.

## 검증 결과

- 작업1: `py -m pytest tests/test_weekly.py -q -p no:cacheprovider` → 11 passed in 3.27s. 요약 ID·이미지·승인명령, 양쪽 CLI 옵션, 비밀변수 단계범위 테스트 추가.
- 작업2: 저장소 데이터/스냅샷과 README 수치 대조 스크립트 통과. 아래 표 참고.
- 작업4: 웹14 tests passed, build 성공, 그림4개 복사본SHA256이원본과일치. 원본재생성 없음. 최초URL테스트는Vitest기본BASE_URL이/라1개실패했고, 배포경로를stubEnv로명시해 재검증통과.
- 작업3: 방법론·신규2라우트 렌더테스트 추가. 웹 lint/test/build 통과.
- 최종 Python 전체: `py -m pytest -q -p no:cacheprovider` → **97 passed, 11 warnings in 44.05s**. 기존93개 유지 + 작업1신규4개. 기존 pandas deprecation/로지스틱 수렴 경고만 남음.
- 최종 웹: lint **0 warnings/0 errors**, Vitest **17 passed**(2.54s), build 성공(192ms). 신규 insights1개/about·라우트3개 추가.
- workflow YAML 로드 및 collect 단계만 VISION_* env를 가지는지 확인. pip/install/cache/PR 단계로 키가 전달되지 않음.
- 그림4개 outputs→public→dist SHA256 일치. dist총839369바이트, JS279.27KB(gzip89.91KB), CSS7.67KB(gzip2.41KB).
- Git diff로 data/raw·processed·observations·predictions·site·notebooks·outputs/figures·final_report 불변 확인. public/figures 복사본 gitignore 확인.
- 실제 collect/forecast/score/site_data CLI, 비전 API, push/원격설정/커밋은 실행하지 않음. pytest의 출력은 임시 디렉터리로만 생성하며 실제 site·관측·스냅샷은 그대로 유지.
- 서브세션 UI 조작 금지로 브라우저/스크린샷 검증은 수행하지 않음. 메뉴5개는 좁은 화면에서 flex-wrap하도록 처리했고 두 신규라우트는 렌더테스트로 검증.

| README 항목 | 확인 값 | 근거 |
|---|---|---|
| tidy/컬럼/분석 | 1160/14/1118 | data/processed/tidy_rewards.csv |
| 보상 | 기존48+신규1=49 | processed.reward_norm.nunique 및 data/site/rewards.json |
| 간격/사전/로지스틱 | 0.348/0.362/0.391 | data/site/backtest.json |
| RF/게이트RF/Prophet | 0.449/0.522/0.420 | data/site/backtest.json |
| v3 검증/백필 | 12/12,20/20 | docs/extraction_eval.md |
| 스냅샷 대상/생성 | 2026-11-01/2026-10-24 14:25KST | data/predictions/2026-11-01.json |
| 스냅샷SHA/dirty/실제코드기준 | 695c614/true/8f47363 | 스냅샷 및 Phase25 packet/git log |

## 데이터 상태

데이터·원본·예측 스냅샷 재생성하지 않음. 시작 git 상태는 본 handoff만 미추적.

- `data/site` 기준일2026-10-25/대상2026-11-01은 변경하지 않았다.
- 새 그림 생성 없이 기존PNG4장을 빌드 정적자산으로만 복사했다. 정본은 outputs/figures에 하나만 유지한다.
- 변경파일: .github/workflows/weekly.yml, .gitignore, src/weekly.py, tests/test_weekly.py, 루트README, 본handoff, web/scripts/sync-data.mjs, App.tsx/index.css, About/Insights 컴포넌트·테스트.
- 루트README의 사이트링크는 기존라이브URL이다. 이번 about/insights 코드는 로컬변경만 완료했으며 배포하지 않았다.

## Claude 리뷰 요청

- **Critical**: 없음. 지시순서 작업1→2→4→3 모두완료, 미해결질문/남은구현 없음.
- **Major**: 내일 첫주간실행 전 env범위 축소와 --notice-ids 승인안내를 우선리뷰·커밋·push해 주세요. Codex는 원격작업을 하지 않았습니다. 사용자/Claude 소유 절차입니다.
- **Minor**: 1280px/375px에서 신규정보페이지와5개메뉴 시각확인을 부탁드립니다. 원본그림은6월분석용이라 최신운영예보와 다르다는 안내를 붙였습니다. 원래리포트의 환경별예보수치는 수정하지 않고 README에서역사기록임을명시했습니다.

작업별로 본 인계파일을 갱신했으며 최종상태까지 기록했습니다.
