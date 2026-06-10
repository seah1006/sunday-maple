# Work Packet — Phase 1: 데이터 수집

## 작업 배경

선데이메이플 분석 프로젝트의 첫 단계. 인벤 게시글에서 9년치(2017~현재) 선데이메이플 이력을 수집해 `data/raw/`에 원본을 저장한다. 이 단계는 **수집만** 담당하며, tidy 변환·파싱은 Phase 2 범위다.

### 조사 결과 (Claude 직접 확인, Work Packet 입력)

**메인 소스** — 인벤 "역대 썬데이메이플 정리(종류별, 날짜별)"
- URL: `https://www.inven.co.kr/board/maple/2304/20563`
- 최신 갱신: 2026-05-28. 2017년 첫 회차부터 현재까지 한 페이지에 정리됨.
- **본문은 순수 HTML 텍스트** (이미지·표 아님). 정적 페이지이므로 `requests` + `BeautifulSoup`로 충분. **Selenium/JS 렌더링 불필요.**
- 한 게시글에 **"종류별" 뷰와 "날짜별" 뷰가 모두** 들어 있음 (같은 데이터의 두 표현 → Phase 3 교차검증 자료).

**원문 표기 규칙 (확인된 실제 패턴)**
- 날짜: `2024.07.21`, 연속 표기 `2024.07.21 (+84일)2024.10.13`
- 주기: `(+84일)`, `(+91일)`, `(+77일)` — `(+N일)` 형식
- 대형 이벤트: `**<메이플 모멘트리>**` 처럼 `**볼드**` + `<...>`
- 소형 맥락: `(사냥 가속! 슈퍼 헤이스트!)` 처럼 `(...)`
- 단종: `**(단종)**경험치 2배`
- 스페셜/시간제: `(샤이닝 스타포스 타임)`, `2022.02.06 (샤이닝 스타포스 타임)`
- 취소선(strikethrough) 사용됨 → HTML 태그(`<s>`, `<strike>`, `del`)로 들어올 수 있으니 **텍스트 추출 시 태그 정보를 보존**해야 Phase 2 파싱이 가능.

**보조 소스 (이번 범위 제외, 향후 교차검증용으로 URL만 기록)**
- 추가·단종 정리(2021.05.02~2025.06.15): `https://www.inven.co.kr/board/maple/2304/44585`
- 최근 1년 분석: `https://www.inven.co.kr/board/maple/2304/45734`

---

## 제약 조건

- **원본 불변**: `data/raw/`에 저장한 파일은 이후 절대 덮어쓰지 않는다. 재수집은 스크립트 재실행으로만.
- **인코딩**: 저장·로드 모두 UTF-8 명시 (`encoding="utf-8"`). 인벤 페이지 응답 인코딩 확인 후 디코딩(`response.encoding` 또는 `apparent_encoding`).
- **크롤링 예절**: User-Agent 명시(일반 브라우저 UA), 요청 1회성(메인 1건). `robots.txt` 확인하고 차단 시 보고. 반복 요청 금지 — 한 번 받은 HTML은 `data/raw/`에 저장해 재요청 없이 재사용.
- **HTML 보존**: 원본 HTML 전체를 그대로 저장한다(파싱 전). 텍스트 추출은 별도 산출물로.
- **서식 정보 보존**: `**볼드**`(대형 이벤트)와 취소선(단종/과거)은 Phase 2 파싱의 핵심 신호다. 텍스트로 평탄화할 때 이 정보를 잃지 않도록 마커로 변환하거나 별도 컬럼/태그로 남긴다. (구현 전략 참고)
- **이 단계에서 파싱·정규화·tidy 변환을 하지 않는다.** 날짜·주기·카테고리 분리는 Phase 2.

---

## 작업 1 — `src/collect.py` (크롤러)

인벤 게시글을 수집해 원본 HTML과 "종류별"/"날짜별" 두 뷰의 원시 텍스트를 `data/raw/`에 저장하는 함수형 모듈.

**요구 함수 (제안 시그니처, 구현 재량 허용)**
```python
def fetch_inven_post(url: str, *, user_agent: str, timeout: int = 10) -> requests.Response
    # GET 요청, 상태코드 검증, 인코딩 보정. robots.txt 위반/차단 시 예외.

def save_raw_html(resp: requests.Response, out_dir: str, slug: str) -> dict
    # 원본 HTML → data/raw/{slug}.html, 메타 → data/raw/{slug}_meta.json
    # 메타: url, fetched_at(ISO8601), status_code, content_length, encoding
    # 반환: 메타 dict

def extract_views(html: str) -> dict[str, str]
    # 게시글 본문(div)에서 "종류별" 뷰와 "날짜별" 뷰 텍스트를 분리 추출.
    # 반환: {"by_type": "...", "by_date": "..."}
    # 본문 컨테이너 선택자는 실제 HTML 확인 후 결정(인벤 게시글 본문은 통상 #powerbbsContent 계열).
    # 볼드/취소선은 마커로 변환해 보존: 예) **볼드** -> [[B]]텍스트[[/B]], 취소선 -> [[S]]텍스트[[/S]]
    #   (Phase 2 파서가 이 마커로 is_major_event / 단종·과거 여부를 복원한다)

def collect_main(out_dir: str = "data/raw") -> None
    # 위 함수들을 엮어 메인 소스 1건 수집 → 4개 산출물 저장. 멱등(이미 있으면 건너뛰거나 경고).
```

**산출물 (data/raw/)**
- `inven_20563.html` — 원본 HTML 전체
- `inven_20563_meta.json` — 수집 메타데이터
- `view_by_type.txt` — "종류별" 뷰 텍스트 (볼드/취소선 마커 보존)
- `view_by_date.txt` — "날짜별" 뷰 텍스트 (볼드/취소선 마커 보존)

**구현 전략 및 대안**
- 본문 컨테이너·뷰 구분 selector는 **저장한 HTML을 직접 열어 확인 후** 확정한다(추측 금지). "종류별"/"날짜별"이 헤더 텍스트·구분선으로 나뉘어 있으면 그 경계로 split.
- 두 뷰 구분이 selector로 깔끔히 안 되면, 전체 본문 텍스트를 하나(`view_full.txt`)로 저장하고 경계 후보(헤더 위치)를 메타에 기록 → Phase 2에서 분리. 이 경우 handoff에 사유 명시.
- 마커 변환은 `BeautifulSoup`에서 `<b>/<strong>` → `[[B]]...[[/B]]`, `<s>/<strike>/<del>` → `[[S]]...[[/S]]`로 치환 후 `get_text()`.

---

## 작업 2 — `notebooks/01_collect.ipynb`

`src/collect.py`를 호출해 수집을 실행하고, 결과를 사람이 검증하는 노트북.

**셀 구성**
1. (마크다운) 목적·소스 URL·수집 정책 설명
2. import + 경로 설정
3. `collect_main()` 실행 → 산출물 저장
4. 검증 출력:
   - 저장된 4개 파일 존재 확인 + 각 글자 수
   - `view_by_type.txt` / `view_by_date.txt` 앞 30줄 `print` (육안 확인)
   - 텍스트 내 날짜 패턴 `\d{4}\.\d{2}\.\d{2}` 개수 카운트 (두 뷰 각각) → 대략적 회차 수 확인 (예상: 수백 건)
5. (마크다운) 관찰 메모: 두 뷰의 날짜 개수 일치 여부, 이상 징후

> 노트북은 커널 재시작 후 위→아래 순차 실행으로 동일 결과가 나와야 한다. 단, 이미 `data/raw/`에 파일이 있으면 재요청 없이 로컬 파일을 읽도록(멱등) 구성한다.

---

## 작업 3 — `requirements.txt`

이번 단계 의존성 + 후속 단계 예정 의존성을 함께 기록(버전 핀은 메이저만 권장).
```
requests
beautifulsoup4
lxml
pandas
numpy
matplotlib
seaborn
scikit-learn
mlxtend
jupyter
pytest
```

---

## 검증 기준

- `python -c "import src.collect"` import 성공 (구문/의존성 오류 없음).
- `notebooks/01_collect.ipynb` 커널 재시작 후 전체 셀 실행 성공.
- `data/raw/`에 4개 산출물 생성 확인.
- `view_by_type.txt`·`view_by_date.txt`에서 날짜 패턴(`\d{4}\.\d{2}\.\d{2}`)이 각각 **100건 이상** 검출 (9년치이므로 정상이면 수백 건). 미달 시 본문 추출 실패로 보고 → handoff에 원인 분석.
- 메타 JSON에 `status_code == 200`.
- 볼드/취소선 마커(`[[B]]`/`[[S]]`)가 텍스트에 실제로 존재하는지 카운트 출력(0이면 서식 보존 실패 가능성 보고).

---

## 작업 우선순위 요약

| 순위 | 작업 | 산출물 | 예상 규모 |
|---|---|---|---|
| 1 | `src/collect.py` | 크롤러 함수 4개 | ~120줄 |
| 2 | `notebooks/01_collect.ipynb` | 실행·검증 노트북 | ~6셀 |
| 3 | `requirements.txt` | 의존성 목록 | ~12줄 |

---

## 이번 범위 제외 항목

- **텍스트 파싱·정규식 분리** (날짜/주기/맥락/단종) → Phase 2.
- **보상명 정규화·카테고리 매핑** → Phase 2~3.
- **보조 소스(44585, 45734) 수집** → 교차검증 필요 시점에 별도 packet.
- **공식 넥슨 공지 교차검증 수집** → 후속 phase.
- **tidy CSV 생성** → Phase 2.

---

## Codex 보고 요청 (claude_handoff_phase1.md)

- 본문 컨테이너 selector와 두 뷰 분리 방식(성공/실패 여부, 실패 시 대안 적용 내역).
- 검증 출력 실제 수치: 두 뷰의 날짜 개수, 마커 개수, 파일 글자 수.
- 두 뷰의 날짜 개수가 불일치하면 그 사실(판정은 Claude가 함).
- robots.txt 확인 결과.
