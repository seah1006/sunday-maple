# Codex Work Packet — Phase 25 (포트폴리오 마감: README, 방법론·분석 페이지, Phase 24 보완)

> Phase 24 후속. 자동화와 배포 준비가 끝났다. 남은 것은 보안 보완 1건과 포트폴리오로 보여 줄 문서·페이지다.

## 작업 배경

### Phase 24 리뷰 결과 (Claude, 2026-10-25)

- **handoff 누락**: Codex 세션은 2026-10-24 23:01 KST에 "작업 1~4 구현·최종 검증 통과, 전후 수치표와 실행 로그를 인계에 정리 중"이라고 보고한 뒤 중단됐고, `docs/claude_handoff_phase24.md`는 만들어지지 않았다. 사용자 지시로 Codex를 다시 실행하지 않고 Claude가 산출물을 직접 검토했다. 아래가 그 기록이다.
- 판정: **통과**. Claude 재실행: pytest **93 passed**, 웹 lint 0/0, Vitest **13 passed**, build 성공. `data/raw`, `data/processed`, `data/observations`, `notebooks`, `src/normalize.py` 변경 없음.
- 작업 1: scope_v3 검증셋 12/12, 승인 백필 20/20 완전 일치(`docs/extraction_eval.md` v3 열, `data/interim/phase24_v3_eval.json`). v3를 기본 프롬프트로 사용.
- 작업 2: `src/weekly.py` `collect / approve / forecast / score`. 운영 경로는 `model_policy=weekly_full_history`이고, 단종 목록에서 `스타포스_1+1강화`를 뺐다(D1, D2). `--historical-model`로 6월 회귀 검증을 유지한다.
- 11-01 예보 전후(운영 재학습 반영). 스냅샷 `data/predictions/2026-11-01.json`, `generated_at` 2026-10-24 14:25 KST, 후보 RF 15 / Prophet 15.

| 순위 | 재학습 전 (2025 이전 학습) | 재학습 후 (10-25까지 전체) |
|---:|---|---|
| 1 | 스타포스_비용할인 60.3 | 룬_재등장감소 62.7 |
| 2 | 몬스터컬렉션 36.7 | 어빌리티_재설정할인 46.3 |
| 3 | 엘리트몬스터_증가 36.7 | 트레져헌터_경험치 26.0 |
| 4 | 어빌리티_재설정할인 35.3 | 미라클타임 21.7 |
| 5 | 룬_경험치버프 32.0 | 스타포스_파괴방지 21.7 |

- Prophet 1위는 그대로 몬스터파크_경험치 0.423이다.
- 스냅샷의 `model_version`은 695c614이고 `working_tree_dirty: true`다. Phase 24 코드가 커밋 전 상태였다는 뜻이다. 스냅샷은 불변이라 고치지 않고, 코드 기준 커밋은 Phase 24 커밋으로 README의 '실전 기록' 절에 밝힌다.
- 작업 3: `.github/workflows/weekly.yml`(월 10:00 KST, collect → 신규 행이 있으면 PR, 자동 머지 없음), `publish.yml`(main의 `official.csv` 변경 또는 수동 → forecast → score → 봇 커밋 → 웹 빌드 → Pages). 봇 커밋은 `official.csv`를 건드리지 않아 재귀 실행이 없다.
- 작업 4: `/track` 실전 기록 섹션(`live_record.json`, 현재 `[]`), scope 배지, Vite `base: '/sunday-maple/'`.
- 리뷰 지적:
  - Minor (보안): `weekly.yml`이 `VISION_API_KEY`를 job 수준 `env`로 넣어 `pip install` 등 모든 단계에 노출한다. **collect 단계의 `env`로만 좁힌다.**
  - Minor: `weekly_summary.md` 문구는 "이미지 대조 후 승인해 주세요"로 끝난다. PR 본문에 승인 명령 예시(`python -m src.weekly approve --notice-ids … --review-method image_checked`)를 덧붙인다.

### 배포 상태

- push, 저장소 공개 전환, Secrets(`VISION_API_KEY`), Pages 소스(GitHub Actions) 설정은 **상위 세션이 사용자 승인 후** 한다. 이 Phase에서 Codex는 하지 않는다.
- 공개 전 점검(Claude): 이력에 실제 비밀값 없음(테스트용 가짜 키만 있음). 커밋 작성자 이메일과 노트북 출력의 로컬 경로(`C:\Users\my\...`)는 공개된다. 원본 데이터 27.5MB(인벤 HTML, 공식 이미지 32장)도 공개된다.

## 제약 조건

- 데이터·모델·예측 스냅샷 변경 금지. `data/site/*.json`은 재생성하지 않는다(문서와 프론트만 바꾼다).
- 새 의존성 금지(차트 라이브러리 포함). 코드 주석 금지. 사용자에게 보이는 글은 한글.
- 사실은 저장소 안의 문서·데이터에서만 가져온다. 수치는 `data/site/*.json`, `docs/extraction_eval.md`, `outputs/report/final_report.md`를 출처로 한다.

## 작업 1 — Phase 24 보완

- `weekly.yml`: `VISION_*` env를 collect 단계로 이동.
- `weekly_summary.md` 생성부: 신규 공지가 있으면 승인 명령 예시와 공지별 이미지 링크를 PR 본문에 넣는다.
- 테스트: 요약 생성 함수가 공지 ID와 승인 명령을 포함하는지.

## 작업 2 — `README.md` (저장소 루트, 한글)

구성(각 절은 짧게, 표 위주):
1. 한 줄 소개 + 사이트 링크 자리(`https://seah1006.github.io/sunday-maple/`, 배포 전이라 '배포 예정' 표기)
2. 무엇을 하나: 다음 썬데이 예측, 적중 기록, 역대 이력
3. 데이터 파이프라인: 인벤 9년 이력(2017~2026-06-07) + 공식 공지 이미지 → Gemini 비전 추출 → 사람 검토 → tidy → 예측 → JSON → React. Mermaid 다이어그램 1개
4. 숫자로 보는 결과: tidy 1160행, 보상 48종(+신규 1), 백테스트 `date_hit_rate`(간격규칙 0.348, 사전확률 0.362, 로지스틱 0.391, RF 0.449, RF 게이트 0.522, Prophet 0.420), 추출 검증 12/12
5. 설계 판단 5개: raw 불변, 시간 분할 백테스트(누수 방지), 재증 게이트, 월드 전용 scope 분리, 자동 머지 없는 사람 검토
6. 실전 기록: 첫 스냅샷 2026-11-01(위 dirty 사실 명시)
7. 로컬 실행(`py -m pip install -r requirements.txt`, `py -m src.site_data`, `cd web && npm ci && npm run dev`)
8. 출처·고지(인벤 원글, 메이플스토리 공식 공지, 넥슨과 무관한 비공식 프로젝트)
9. 개발 방식: Claude(계획·리뷰) + Codex(구현), `docs/` Work Packet/handoff 이력

## 작업 3 — 방법론 페이지 `/about`

- 메뉴에 "방법론" 추가. 내용은 README 3~5절을 화면용으로 줄인 것(다이어그램은 CSS 박스 흐름으로, 라이브러리 없이).
- 점수 읽는 법, 게이트 설명, 백테스트와 실전 기록의 차이, 한계(선물류·스페셜 편성은 예측 밖).

## 작업 4 — 분석 요약 페이지 `/insights`

- `outputs/figures/` 그림 4장(q1 카테고리 비중, q2 주기 분포, q3 단종, q8 회차당 보상 수)을 `web/public/figures/`로 복사해 쓴다(sync 스크립트에 추가). 각 그림 아래에 리포트의 결론 한두 문장.
- 그림은 2026-06 인벤 데이터 기준이라는 안내를 붙인다.

## 검증 기준

1. pytest, 웹 lint/test/build 통과. `/about`, `/insights` 렌더 테스트 추가.
2. README의 수치가 JSON·문서 값과 일치하는지 표로 대조해 handoff에 남긴다.
3. **handoff를 먼저 뼈대로 만들어 두고** 작업마다 갱신한다(Phase 24처럼 세션이 끊겨도 기록이 남게).

## 작업 우선순위 요약

| 작업 | 대상 | 예상 규모 | 의존 |
|---|---|---|---|
| 1 | weekly.yml env 범위, PR 본문 | 약 20줄 + 테스트 | - |
| 2 | README.md | 문서 | - |
| 3 | /about | 약 120줄 | 2 |
| 4 | /insights + 그림 동기화 | 약 100줄 | - |

## 이번 범위 제외 항목

- 실제 배포, 저장소 공개, Secrets 등록, Aside 주간 검토 루틴 생성 — 상위 세션이 사용자 승인 후 처리.
- `final_report.md` 수치 갱신, 보상 표시명 사전, 다크 모드.
