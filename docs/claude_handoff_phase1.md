## 작업 범위

Phase 1 Work Packet(`docs/codex_work_packet_phase1.md`)에 따라 인벤 메인 게시글 데이터 수집만 구현했다.

- `src/collect.py`: 인벤 게시글 원본 HTML 저장, 메타 저장, `종류별`/`날짜별` 원시 텍스트 추출
- `notebooks/01_collect.ipynb`: 수집 실행 및 산출물 검증 노트북
- `requirements.txt`: Phase 1 및 후속 단계 예정 의존성 목록

파싱·정규화·tidy 변환은 구현하지 않았다.

## 구현 요약

- `src/collect.py`
  - `fetch_inven_post(url, *, user_agent, timeout=10)`: `robots.txt` 확인 후 User-Agent를 명시해 1회 GET 요청, 상태코드 확인, 인코딩 보정.
  - `save_raw_html(resp, out_dir, slug)`: 원본 HTML과 메타 JSON 저장. 기존 HTML이 있으면 덮어쓰지 않고 메타를 재사용.
  - `extract_views(html)`: 저장 HTML에서 본문 컨테이너 `#powerbbsContent`를 사용.
  - 뷰 분리 방식: `종류별(가나다순)` 다음 줄부터 `[[B]]날짜별[[/B]]` 직전까지를 `by_type`, `[[B]]날짜별[[/B]]` 다음 줄부터 끝까지를 `by_date`로 분리.
  - 볼드 태그(`<b>`, `<strong>`, `font-weight: 700`)는 `[[B]]...[[/B]]`, 취소선 태그(`<s>`, `<strike>`, `<del>`)는 `[[S]]...[[/S]]`로 보존.
  - `collect_main(out_dir="data/raw")`: 원본 HTML이 이미 있으면 재요청하지 않고 로컬 파일을 사용. 텍스트 산출물도 기존 파일이 있으면 덮어쓰지 않음.

- `notebooks/01_collect.ipynb`
  - `nbformat`으로 생성.
  - `collect_main()` 호출, 4개 산출물 존재·글자 수·바이트 수 출력.
  - `view_by_type.txt`, `view_by_date.txt`의 앞 30줄 출력.
  - 날짜 패턴과 `[[B]]`/`[[S]]` 마커 개수 출력.

- `requirements.txt`
  - Work Packet 지정 목록 반영: `requests`, `beautifulsoup4`, `lxml`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `mlxtend`, `jupyter`, `pytest`.

## 검증 결과

- `python -c "import src.collect"`: 실행 완료, 출력 없음.
- `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_collect.ipynb`: 실행 완료.
- `python -m pytest -q`: `no tests ran in 0.03s`, 종료 코드 1.

robots 및 메타:

| 항목 | 값 |
|---|---:|
| `robots_allowed` | `True` |
| `status_code` | `200` |
| `encoding` | `utf-8` |
| `content_length` | `693602` |

산출물 크기:

| 파일 | 글자 수 | 바이트 수 |
|---|---:|---:|
| `data/raw/inven_20563.html` | 629378 | 698829 |
| `data/raw/inven_20563_meta.json` | 417 | 426 |
| `data/raw/view_by_type.txt` | 23476 | 31110 |
| `data/raw/view_by_date.txt` | 43800 | 82038 |

텍스트 검증:

| 파일 | 날짜 패턴 수 | `[[B]]` 수 | `[[S]]` 수 |
|---|---:|---:|---:|
| `data/raw/view_by_type.txt` | 1140 | 71 | 0 |
| `data/raw/view_by_date.txt` | 503 | 568 | 2 |

관찰:

- `#powerbbsContent` 내부는 HTML 텍스트로 구성되어 있었다.
- `종류별(가나다순)`과 `[[B]]날짜별[[/B]]` 헤더가 실제 저장 HTML에서 확인됐다.
- `view_by_type.txt`의 취소선 마커 수는 0이다.
- `view_by_date.txt`의 취소선 마커 수는 2이다.
- 두 뷰의 날짜 패턴 수는 서로 다르다.

## 데이터 상태

- 생성된 원본/원시 산출물:
  - `data/raw/inven_20563.html`
  - `data/raw/inven_20563_meta.json`
  - `data/raw/view_by_type.txt`
  - `data/raw/view_by_date.txt`
- 이번 Phase에서는 행 단위 데이터셋을 만들지 않았으므로 처리된 행 수와 결측 현황은 없음.
- `data/interim/`, `data/processed/` 산출물은 생성하지 않음.

## Claude 리뷰 요청

Critical:

- 없음.

Major:

- `view_by_type.txt`의 `[[S]]` 마커 수가 0인 상태 검토.
- `view_by_type.txt`와 `view_by_date.txt`의 날짜 패턴 수 불일치 검토.

Minor:

- `pytest`는 테스트가 없어 `no tests ran`으로 종료 코드 1을 반환함.
