# Codex Work Packet — Phase 24 (주간 자동화 + 예측 사전 저장 + 배포)

> Phase 23 후속. 매주 새 공지를 수집·추출하고, 사람 승인 후 예보를 갱신해 배포한다. **일요일 전에 예측을 저장**해서 사후 백테스트가 아닌 진짜 적중 기록을 쌓는다. ⚠ 표시 항목은 사용자 결정에 따라 확정한다(Claude가 결정 후 메시지로 알림).

## 작업 배경

### Phase 23 리뷰 결과 (Claude, 2026-10-24)

- 판정: **통과**. Python 85 passed, 웹 11 passed, lint·build 성공(Claude 재실행). API 키 접두가 추적 파일에 없음 확인.
- 공식 관측 78행·20공지 승인(`image_checked` 9, `pattern_approved` 11). `data_through` 2026-10-25, `target_date` 2026-11-01. 11-01 RF(게이트) 1위 스타포스_비용할인 60.3, Prophet 1위 몬스터파크_경험치 0.423.
- 백테스트: 게이트 RF `date_hit_rate` **0.522**(36/69), 기존 5개 지표 불변.
- 검증셋: scope_v2 12/12 완전 일치. **리뷰 예외(미라클 타임·선물은 제목 1행)를 반영한 scope_v3는 아직 실호출로 검증하지 않았다**. 작업 1에서 처리한다.
- 메시지 합의(Phase 23 중): robots RFC 9309 4xx 예외(공지 이미지 한정), 이미지 URI 허용 목록(https + lwi.nexon.com + PNG/JPG), `scope` 컬럼(월드 전용 블록 분리, 모델 입력은 `all`만), is_special은 제목 기준, 미라클 타임은 보상 1행이고 샤이닝·솔 에르다 타임은 꼬리표.
- 발견: 1355(07-12)에 `스타포스_1+1강화` 재등장 → `DOMAIN_DISCONTINUED` 가정이 깨짐.
- 저장소: `seah1006/sunday-maple`는 비인증 API 조회 404라 **비공개**로 보인다. 무료 계정의 GitHub Pages는 공개 저장소에서만 가능하다.

### 공지 게시 시점

- 10-25 회차 공지(1405)는 10-22(목)에 올라왔다. 그러니 "다음 일요일 예측"은 **월~수요일**에 공개돼야 의미가 있다.

## 사용자 결정 (2026-10-24 확정)

- D1 제거, D2 매주 재학습, D3 게이트 RF 메인: **추천안대로**.
- D4: **저장소 공개 + GitHub Pages**. Vite `base`는 `/sunday-maple/`, 배포는 `actions/upload-pages-artifact` + `actions/deploy-pages`. 공개 전환과 push는 상위 세션이 사용자 최종 확인 후 한다.
- D5: **Aside 루틴이 검토**. Actions는 PR만 열고 자동 머지하지 않는다. PR 본문에 공지 URL, 이미지 URL, 추출 행 표, 미등록 행을 넣어 루틴이 이미지와 대조할 수 있게 한다. 루틴은 검토 결과를 사용자에게 알리고, 머지는 사용자 승인 후에 한다. 수정이 필요하면 PR 브랜치에서 `official.csv`를 고치고 `reviewed=True`로 바꾼 뒤 머지한다. Actions가 여는 PR의 행은 `reviewed=False`로 두고, `py -m src.weekly approve --pr-rows` 같은 승인 전환 명령(지정 공지 ID의 행을 `reviewed=True`, `review_method` 기록)을 제공한다.

## 사용자 결정 항목 (기록용)

| # | 항목 | Claude 추천 |
|---|---|---|
| D1 | `DOMAIN_DISCONTINUED`에서 `스타포스_1+1강화` 제거 | 제거. 180일 게이트만으로 충분하다 |
| D2 | 운영 예보 모델 재학습 | 매주 그 시점까지의 전체 관측(인벤 raw + 승인된 공식)으로 다시 학습. 백테스트 지표는 기존 방식 그대로 고정 |
| D3 | 메인 모델 | 게이트 RF(0.522) 유지, Prophet은 비교 섹션 |
| D4 | 호스팅 | (a) 저장소 공개 + GitHub Pages, 또는 (b) 비공개 유지 + Cloudflare Pages/Netlify(무료, 정적 dist만 배포) |
| D5 | 승인 방식 | Actions가 추출 결과로 PR을 열고, 사용자(또는 Claude)가 이미지와 대조해 머지 |

## 제약 조건

- 배포 연결, 저장소 공개 전환, GitHub Secrets 등록, push는 **사용자 승인 후 사용자 또는 Claude가** 한다. Codex는 워크플로 파일과 스크립트만 만든다.
- 예측 스냅샷은 **한 번 쓰면 수정 금지**(raw와 같은 규칙). 일요일 이후에는 새 스냅샷을 만들 수 없다.
- Actions는 무료 한도 안에서 돈다(주 1~2회, 1회 5분 이내 목표). Gemini 호출은 주 1장.
- 기존 테스트 통과 유지. 새 의존성 금지(Actions 액션은 GitHub 공식 액션만).

## 작업 1 — scope_v3 검증

- 검증셋 12개를 scope_v3로 다시 추출해 `docs/extraction_eval.md`에 v3 열을 추가한다. 백필 20개도 v3로 추출해 승인된 `official.csv`와 비교한 일치율을 기록한다(CSV는 바꾸지 않는다).
- 12/12와 백필 일치율이 모두 유지되면 v3를 기본 프롬프트로 둔다. 하나라도 떨어지면 차이를 보고하고 v2를 유지한다.

## 작업 2 — 주간 파이프라인 CLI

- `py -m src.weekly collect`: 공지 목록에서 `official.csv`에 없는 새 회차를 찾아 원본을 저장하고 추출한다. 결과는 `reviewed=False` 행으로 추가하고, 변경 요약 Markdown(공지 링크, 이미지 경로, 추출 행, 미등록 행)을 stdout과 `data/interim/weekly_summary.md`에 쓴다.
- `py -m src.weekly forecast`: `site_data`를 재생성하고, `target_date`가 아직 미래면 `data/predictions/{target_date}.json` 스냅샷을 만든다. 내용은 생성 시각, 모델 버전(git SHA), 학습 데이터 기준일, RF·Prophet 상위 10이고, 이미 있으면 건너뛴다.
- `py -m src.weekly score`: 스냅샷이 있고 그 날짜의 승인된 관측이 생긴 회차를 채점해 `data/site/live_record.json`을 만든다. 상위 5 적중 수, 실제 보상, k-적중을 담는다.
- D1·D2는 결정에 따라 `forecast.py`의 운영 경로에만 반영한다(백테스트 경로 불변).

## 작업 3 — GitHub Actions

- `.github/workflows/weekly.yml`: 월요일 10:00 KST(`cron: "0 1 * * 1"`) + 수동 실행. `collect` 후 새 행이 있으면 `peter-evans/...` 같은 서드파티 대신 `gh pr create`로 PR을 연다(`GITHUB_TOKEN`). PR 본문은 `weekly_summary.md`.
- `.github/workflows/publish.yml`: main에 `data/observations/official.csv`가 머지되면 `forecast` → `score` → 웹 빌드 → 배포(D4에 따라 Pages 액션 또는 호스팅 쪽 빌드 훅). 스냅샷과 `data/site` 변경은 봇 커밋으로 남긴다.
- 시크릿 이름: `VISION_API_KEY`. 모델은 워크플로 env `VISION_MODEL=gemini-3.5-flash-lite`.
- 로컬 검증: `act`는 쓰지 않는다. 워크플로 YAML은 문법 검사(가능하면 `actionlint` 없이 파이썬 yaml 로드 수준)와 각 단계를 로컬 명령으로 재현한 결과를 handoff에 남긴다.

## 작업 4 — 프론트 반영

- `/track` 맨 위에 **실전 기록**(`live_record.json`) 섹션: "일요일 전에 저장한 예측" 표(대상일, 저장 시각, 상위 5, 실제, 적중 수). 기록이 없으면 "첫 실전 기록은 11-01 회차 이후 표시" 안내.
- 이력 화면에 `scope`가 `all`이 아닌 항목은 배지로 표시한다(예: `챌린저스 월드 전용`).
- Vite `base`: `/sunday-maple/`(D4 결정). 로컬 dev에서도 동작하도록 데이터 fetch는 계속 `import.meta.env.BASE_URL` 기준.

## 검증 기준

1. pytest, 웹 lint/test/build 통과.
2. `weekly collect`(새 회차가 없으면 0건으로 정상 종료), `weekly forecast`(11-01 스냅샷 생성, 재실행 시 건너뜀), `weekly score`(아직 채점 대상 없음) 로컬 실행 로그.
3. 스냅샷 불변 테스트, 일요일 이후 스냅샷 생성 거부 테스트.
4. v3 평가표.

## 작업 우선순위 요약

| 작업 | 대상 | 예상 규모 | 의존 |
|---|---|---|---|
| 1 | scope_v3 검증 | 실행 + 문서 | 키 |
| 2 | `src/weekly.py` collect/forecast/score + 테스트 | 약 200줄 | D1, D2 |
| 3 | 워크플로 2개 | 약 120줄 YAML | D4, D5 |
| 4 | 실전 기록 화면, scope 배지, base | 약 120줄 | 2 |

## 이번 범위 제외 항목

- 실제 배포 연결과 push, Secrets 등록 — 사용자 승인 후 상위 세션이 처리.
- README, 분석·방법론 페이지, `final_report` 수치 갱신, 보상 표시명 사전 — Phase 25.
