# Codex Work Packet — Phase 23 (공식 공지 수집 + 비전 LLM 보상 추출 + 백필)

> Phase 22 후속. 인벤 원글이 2026-06-07 이후 멈춰서, 메이플스토리 공식 썬데이 공지(이미지)를 수집하고 비전 LLM으로 보상 문구를 뽑아 관측 데이터로 쌓는다(사용자 결정 B, 2026-10-24). 추출 결과는 사람이 확인한 뒤 확정한다. Phase 22 리뷰 지적도 함께 처리한다.

## 작업 배경

### Phase 22 리뷰 결과 (Claude, 2026-10-24)

- 판정: **통과**. Python 61 passed, Vitest 11 passed, oxlint 0/0, build 성공(Claude 재실행 확인). 1280px·375px 화면을 Claude가 브라우저로 확인했고 가로 넘침은 없다.
- 지적 (이번 Phase 작업 0에서 처리):
  - **Major**: 적중 기록(`backtest.per_date`)은 게이트 없는 원시 RF 순위라 `스타포스_1+1강화`, `불꽃늑대_경험치` 같은 단종·휴면 보상이 예측으로 자주 나온다. 사이트가 실제로 쓰는 예보는 게이트 적용이므로 적중 기록도 **게이트 적용 기준**이 주 지표여야 한다.
  - Minor: 판정 불가 회차(실제 보상이 후보 20개 밖)는 실제 칸이 비어 보인다. 실제 보상 전체를 보여 주고 후보 밖임을 표시한다.
  - Minor: 2열 카드에서 한국어 단어가 끊긴다(`스타포스 비용할 / 인`). `word-break: keep-all` 등으로 처리.
  - Minor: 라우트 이동 시 스크롤이 맨 위로 가지 않는다.

### 공식 공지 조사 (Claude 확인, `docs/website_roadmap.md` §6)

- 목록: `https://maplestory.nexon.com/News/Event/Closed?searchKeyword=썬데이&page={n}`. 진행 중 회차는 목록 상단에 `/News/Event/{id}` 링크로 함께 나온다. 목록 항목 텍스트 예: `썬데이 메이플 2026.06.14 ~ 2026.06.14`, `스페셜 썬데이 메이플 …`, `수정 스페셜 썬데이 메이플 …`.
- 상세: `/News/Event/{id}`의 `.new_board_con` 안에 PNG 1장(`lwi.nexon.com/maplestory/...png`), alt 없음. 정정 안내가 있으면 같은 컨테이너에 텍스트로 붙는다(10-25: `룬 경험치 버프 … (전) 200% (후) 100%`). **정정 텍스트가 이미지보다 우선**한다.
- 이미지 구조: 상단 배너(날짜) → 혜택 블록마다 큰 제목 한 줄(예: `몬스터파크 클리어 경험치 추가 250%`) + 작은 설명. 추출 대상은 **큰 제목 줄**이다. `썬데이 메이플 선물 지급`처럼 표가 딸린 블록도 제목 한 줄로 본다.
- 검증셋 ID (인벤 정답 있음): 1300(03-22), 1302(03-29 스페셜), 1304(04-05), 1307(04-12), 1310(04-19), 1314(04-26 스페셜), 1315(05-03), 1317(05-10 스페셜), 1325(05-17), 1326(05-24), 1327(05-31 스페셜), 1329(06-07).
- 백필 ID: 1330(06-14), 1350(06-21), 1352, 1354, 1355, 1356, 1365, 1367, 1368, 1369, 1375, 1376, 1377, 1379, 1390, 1391, 1396, 1397, 1399, 1405(10-25). 날짜는 로드맵 §6.1 표.
- Claude가 06-14, 06-21, 10-25 이미지를 직접 봤다. 06-14는 `manual_obs_20260614.csv`와 일치(몬스터파크 경험치, 선물 지급). 06-21 실제: 트레저 헌터 경험치 3배, 룬 재등장·재사용 대기시간 감소, 룬 경험치 버프 +100%, 콤보킬 경험치 +300%, 몬스터파크 클리어 경험치 +250%, 사냥 솔 에르다 2배. 10-25: HEXA 스탯 강화 확률 20% 증가, 룬 기본 지속시간 50% 증가, 룬 경험치 버프 +100%, 콤보킬 경험치 +300%.

### 비전 모델

- 제공사·모델은 **사용자 승인 대기**다. 코드는 제공사 독립 인터페이스로 만들고, HTTP는 `requests`로 직접 호출한다(SDK 의존성 추가 금지).
- 키는 환경변수 `VISION_API_KEY`, 제공사는 `VISION_PROVIDER`(`gemini` | `anthropic` | `openai`), 모델은 `VISION_MODEL`. 로컬은 저장소 루트 `.env`(gitignore)에서 읽는 30줄 이내 로더를 직접 만든다(python-dotenv 금지).
- **키가 없으면 실호출 단계(작업 5, 6)는 건너뛰고** handoff에 남긴다. 나머지는 목(mock) 테스트로 완료한다.

## 제약 조건

- `data/raw/` 기존 파일 수정 금지. 새 원본은 `data/raw/official/`에 **한 번만 쓰고 덮어쓰지 않는다**(기존 `save_raw_html`와 같은 규칙).
- 공식 사이트 요청: `robots.txt` 확인(`src.collect`와 같은 방식), 요청 간 1초 이상, 기존 UA 사용, 한 실행에서 이미 받은 파일은 다시 받지 않는다.
- 학습·백테스트 기준(raw 인벤 tidy)과 기존 지표 5개(0.3478/0.3623/0.3913/0.4493/0.4203)는 그대로 둔다. 게이트 적용 지표는 **새 방법으로 추가**한다.
- 정규화 사전(`src/normalize.py`)에 규칙을 추가할 때는 **기존 매핑 결과가 바뀌지 않아야** 한다(기존 테스트 + tidy 1160행 `reward_norm` 불변 확인). 새 규칙은 handoff에 표로 남기고 Claude가 리뷰한다.
- LLM 추출 결과는 바로 확정하지 않는다. `reviewed` 컬럼이 True인 행만 사이트 데이터에 들어간다. 이번 Phase에서 리뷰는 Claude가 이미지를 보고 한다(작업 6 이후 메시지로 요청).
- 새 의존성 금지. 코드 주석·docstring 금지. API 키는 커밋·로그·handoff에 절대 남기지 않는다.

## 작업 0 — Phase 22 리뷰 반영

- `src/forecast.py` `backtest()`: `random_forest_gated` 방법 추가. 각 test 날짜마다 `gate_candidates(eligible, candidates, date)`로 걸러진 후보만 RF 점수로 순위를 매기고, 08의 `date_hit` 정의(k = 후보 안 실제 보상 수, 상위 k 중 하나라도 맞으면 1)를 그대로 쓴다. `per_date`에 `gated_predicted`, `gated_hit` 추가. 라벨 `랜덤포레스트(게이트)`.
- `backtest.per_date[]`에 `actual_all`(그 날짜 실제 보상 전체 `reward_norm`)과 `outside_candidates`(후보 20개 밖 실제 보상) 추가.
- 프론트 `/track`: 게이트 적용 RF를 주 지표·기본 표로, 원시 RF는 "참고: 게이트 없는 원시 모델" 토글로. 실제 칸은 `actual_all`을 보여 주고 후보 밖 보상은 흐리게 + "후보 밖" 표시.
- CSS `word-break: keep-all`(카드 제목·목록), 라우트 변경 시 `window.scrollTo(0, 0)`.
- 테스트: 게이트 백테스트가 단종 4종을 예측에 넣지 않는지, 기존 5개 지표 불변, 프론트 track 화면 픽스처 갱신.
- handoff에 `random_forest_gated` `date_hit_rate` 값을 기록한다(새 값이라 기준 없음, Claude 리뷰).

## 작업 1 — `src/official.py` (공식 공지 탐색·원본 저장)

- `list_sunday_notices(max_pages=…) -> list[Notice]`: 목록 페이지를 넘기며 `id, title, start_date, end_date, is_special(제목에 '스페셜'), url`을 모은다. 날짜는 목록 텍스트 `YYYY.MM.DD ~ YYYY.MM.DD`에서 파싱. 이미 알고 있는 가장 오래된 ID보다 오래되면 멈춘다(인자).
- `fetch_notice(notice) -> NoticeDetail`: 상세 페이지에서 이미지 URL 목록과 `.new_board_con` 텍스트(정정 문구)를 얻는다.
- `save_notice_raw(detail, out_dir="data/raw/official")`: `{date}_{id}.png`, `{date}_{id}_meta.json`(url, image_url, title, period, fetched_at, correction_text, sha256). 이미 있으면 건너뛴다.
- 테스트: 저장해 둔 목록·상세 HTML 픽스처(작게 잘라 `tests/fixtures/official/`)로 파싱 검증. 네트워크 호출 없음.

## 작업 2 — `src/vision.py` (제공사 독립 추출)

- `extract_rewards(image_bytes, correction_text, *, provider, model, api_key) -> list[dict]`. 반환 `[{ "reward_raw": "몬스터파크 클리어 경험치 추가 250%" }]`.
- 프롬프트(한국어): "썬데이 메이플 공지 이미지에서 혜택 블록의 큰 제목 줄만, 이미지에 적힌 그대로 JSON 배열로. 설명·주의사항·계산표·버튼 문구 제외. 정정 텍스트가 주어지면 그 수치를 우선." 응답은 JSON만 받도록 지정하고 파싱 실패 시 1회 재시도.
- 제공사별 어댑터 3개(gemini/anthropic/openai)는 각 REST 형식으로 `requests.post`. 이미지는 base64.
- 캐시: `data/interim/vision_cache/{id}_{model}.json`(gitignore 대상 `data/interim/*` 안이라 자동 무시). 같은 이미지·모델은 다시 호출하지 않는다.
- 호출마다 입력/출력 토큰 수(응답에 있으면)를 캐시에 기록.
- 테스트: `requests.post`를 목으로 바꿔 세 어댑터의 요청 형식과 응답 파싱, 재시도, 캐시 적중 검증.

## 작업 3 — 정규화 연결과 미등록 보상

- 추출된 `reward_raw`에 기존 `normalize_reward`, `categorize`, `extract_magnitude`를 그대로 적용한다.
- 매핑 실패(`None`) 또는 의심(기존 사전에 없는 새 `reward_norm`)은 `data/observations/unmapped.csv`에 남긴다.
- 공식 문구와 인벤 문구가 달라서 생기는 실패는 작업 5 검증셋으로 찾아, `normalize.py`에 **추가 규칙**으로 흡수한다(기존 결과 불변 조건). 진짜 새 보상은 새 `reward_norm`을 만들지 말고 목록만 보고한다(Claude가 이름·카테고리 결정).

## 작업 4 — 관측 저장소와 사이트 연결

- `data/observations/official.csv`: `date, notice_id, title, is_special, reward_raw, reward_norm, category, source_url, extracted_by(provider:model), reviewed(bool), note`.
- `src/site_data.py`: 관측 입력을 `manual_obs_20260614.csv` + `official.csv`(`reviewed=True`만)로 확장. 같은 날짜가 둘 다 있으면 official 우선. `meta.sources`에 공식 공지 추가. `history`의 `reward_raw`는 공식 문구, `is_special`은 공지 제목 기준.
- 학습·백테스트는 여전히 raw 인벤 tidy만(Phase 21 합의).

## 작업 5 — 추출 정확도 검증 (키 있을 때)

- 검증셋 12개 공지를 수집·추출하고, 인벤 tidy의 같은 날짜 `reward_norm` 집합과 비교한다.
- 지표: 회차별 정밀도·재현율, 전체 완전 일치 회차 수. 표로 handoff와 `docs/extraction_eval.md`에 남긴다.
- 불일치는 원인을 분류한다: (a) 추출 오류 (b) 정규화 규칙 부족 (c) 인벤·공식 표기 차이(예: 인벤이 이벤트 연동 보상을 뺌). (b)만 작업 3 규칙으로 고친다.

## 작업 6 — 백필 (키 있을 때)

- 06-14 ~ 10-25 20개 공지를 수집·추출해 `official.csv`에 `reviewed=False`로 넣는다.
- 끝나면 **message_agent로 Claude에게 리뷰를 요청**한다. Claude가 이미지와 대조해 행별로 승인·수정 내용을 보내면 반영하고 `reviewed=True`로 바꾼다.
- 그다음 `py -m src.site_data --out data/site` 재생성. 예상: `data_through` 2026-10-25, `target_date` 2026-11-01.

## 검증 기준

1. `py -m pytest -q -p no:cacheprovider` 전체 통과. 기존 지표 5개, tidy 1160/1118, 기존 `reward_norm` 매핑 불변.
2. 웹 `npm run lint`, `npm run test -- --run`, `npm run build` 통과.
3. 키가 있으면: 검증셋 지표표, 백필 20개 행 수, 호출 수와 토큰 합계(비용 추정), 재생성된 `meta`/`forecast` 핵심 값.
4. `git status`: `data/raw/` 기존 파일 불변, `.env` 무시됨, API 키 문자열이 어떤 추적 파일에도 없음(`git grep`으로 키 앞 6자 검색).

## 작업 우선순위 요약

| 작업 | 대상 | 예상 규모 | 의존 |
|---|---|---|---|
| 0 | 게이트 백테스트 + track 화면 + CSS 2건 | 약 80줄 + 테스트 | - |
| 1 | `src/official.py` + 픽스처 테스트 | 약 120줄 | - |
| 2 | `src/vision.py` + `.env` 로더 + 목 테스트 | 약 150줄 | - |
| 3 | 정규화 연결, unmapped 보고 | 약 40줄 (+규칙) | 2 |
| 4 | `official.csv` 스키마 + site_data 확장 | 약 60줄 | 3 |
| 5 | 검증셋 12개 평가 | 실행 + 문서 | 키, 1~3 |
| 6 | 백필 20개 + Claude 리뷰 루프 + 재생성 | 실행 | 키, 1~4 |

## 이번 범위 제외 항목

- GitHub Actions 주간 자동화, 예측 사전 저장, 배포 — Phase 24.
- 모델 재학습 정책(최신 데이터로 다시 학습) — Phase 24 전 결정.
- 보상 표시명 사전, 분석·방법론 페이지, README — Phase 25.
- NEXON Open API 연동(목록 페이지로 충분, 키 추가 부담) — 필요해지면 재검토.
