# Claude Handoff — Phase 8

## 작업 범위

- 문서와 노트북 마크다운만 수정.
- 코드 로직, 테스트 파일, tidy 데이터, `data/raw/`는 수정하지 않음.
- 공식 넥슨 이미지 파일은 저장소에 추가하지 않고 URL만 기록.
- 추가 텍스트는 CLAUDE.md의 발표자료 언어 규칙에 맞춰 한글로 작성.

## 구현 요약

### `data_dictionary.md`

추가 내용:
- 데이터 출처와 신뢰성 검증 섹션 추가.
- 원본이 인벤 단일 게시글 기반 2차 자료이며, 단일 작성자가 약 9년간 누적 정리한 자료임을 명시.
- 공식 공지는 보상 목록이 이미지로 게시되어 자동 텍스트 대조가 어렵고, 수동 스팟체크 방식으로 검증했음을 문서화.
- 공식 공지 스팟체크 3회차 결과표 추가:
  - 2026-04-19: 공식 3개, tidy 3/3 일치.
  - 2025-07-27: 공식 4개, tidy 4/4 일치.
  - 2023-05-21: 공식 5개 중 상시 보상 3/3 일치, 이벤트 연동 보상 2개 미수록.
- 스코프 한계 문서화:
  - 인벤 원본은 정규 썬데이 보상 중심 자료.
  - 이벤트 연동 일회성 보상은 제외될 수 있음.
  - 회차당 공식 전체 보상 수 집계에는 이벤트 기간 과소계상 가능성이 있음.
- 보조 신뢰성 근거로 by_type↔by_date 내부 교차검증 일치율 0.726 기록.

### `notebooks/03_crossval.ipynb`

추가 내용:
- 노트북 끝에 `외부(공식 공지) 스팟체크 검증` 마크다운 셀 추가.
- 공식 페이지 URL과 3회차 스팟체크 결과표 추가.
- 발표용 요약 문장 추가:
  - 정규 보상은 공식 공지와 일치.
  - 분석 범위는 정규 썬데이 보상 등장 패턴이며 이벤트 연동 일회성 보상은 범위 밖.

코드 셀은 변경하지 않았다.

## 검증 결과

### pytest

```text
python -m pytest -q
.................................                                        [100%]
33 passed in 0.78s
```

### 03 노트북 재실행

```text
jupyter nbconvert --to notebook --execute notebooks/03_crossval.ipynb --inplace --ExecutePreprocessor.timeout=300 --ExecutePreprocessor.kernel_name=python3
[NbConvertApp] Converting notebook notebooks/03_crossval.ipynb to notebook
[NbConvertApp] Writing 27953 bytes to notebooks\03_crossval.ipynb
```

재실행 후 기존 코드 출력은 동일한 수치로 유지됐다.

```text
parsed_by_type 행 수: 1140
parsed_by_date 행 수: 1160
tidy_prenorm 행 수: 1160
주기 검증 대상 행 수: 1041
주기 불일치 행 수: 0
고유 reward_raw 전체 수: 113
등장 횟수 일치 보상 수: 82
등장 횟수 불일치 보상 수: 31
등장 횟수 일치율: 0.7256637168141593
reward_inventory 행 수: 113
reward_inventory 단종 보상 수: 71
reward_inventory 바이트: 9603
parsed_by_type 단종 고유 보상 수: 71
no_event_week 행 수: 30
no_event_week 중 미래 행 수: 0
미래 빈 블록 수: 12
센티넬 없는 과거 빈 블록 수: 0
최소 날짜: 2017-03-12
최대 날짜: 2026-08-30
고유 날짜 수: 501
```

### 변경 범위 확인

```text
git status --short
 M data_dictionary.md
 M notebooks/03_crossval.ipynb
```

이미지 파일 추가 없음. `data/raw/` 변경 없음.

## 추가한 문서 내용 요약

- 공식 공지 스팟체크 결과 정규 썬데이 보상은 tidy와 일치했다.
- 2023-05-21 공식 공지의 이벤트 연동 보상 2개는 인벤 원본에 없으므로, 원본의 스코프는 정규 보상 중심으로 해석한다.
- 본 프로젝트 분석 범위는 정규 보상 등장 패턴이다.
- 이벤트 기간의 공식 전체 보상 수를 회차별로 집계하면 과소계상 가능성이 있다.
- 내부 교차검증 일치율 0.726은 보조 신뢰성 근거로 기록했다.

## Claude 리뷰 요청

### Critical

- 없음.

### Major

- 공식 공지 스팟체크는 3회차 수동 검증이다. 더 넓은 공식 대조가 필요하면 별도 Phase에서 회차를 늘려야 한다.

### Minor

- 03 노트북 실행 시 기존 Windows/ZMQ 경고와 notebook cell id 경고가 출력됐지만 실행은 완료됐다.
