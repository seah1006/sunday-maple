# Codex Work Packet — Phase 9 (EDA + 최소 베이스라인 모델)

> 입력: `docs/phase8_eda_design.md` + 사용자 결정. 데이터 파이프라인·신뢰성 검증 완료(Phase 1~8). 본 Phase는 발표용 EDA(혼합 스토리)와 보조 최소 베이스라인 모델을 구현한다. **발표자료** — CLAUDE.md "발표자료 언어(한글)" 규칙: 노트북 마크다운·출력 라벨·그래프 제목/축/범례 전부 한글.

## 작업 배경

### 사용자 결정
| 항목 | 선택 |
|---|---|
| 발표 스토리 | **혼합**(운영 변화 + 보상 패턴) |
| 보조 모델 | **최소 베이스라인 1개만 포함** |

### Claude 직접 확인한 데이터 사실 (`tidy_rewards.csv`, 1160행)
- 분석대상(reward_norm 있음 & `is_future==False`) = **1118행**. EDA·모델은 이 필터를 기본으로.
- **`time_limited`는 비결측 20/1160뿐 → 시계열 분석 부적합.** 설계 Q7(시간제→하루종일)을 **Q8(회차당 평균 보상 수 추이)**로 교체(운영 변화 스토리 유지). 근거를 노트북에 명시.
- 연도별 보상 수: 2017=71 … 2024=171, 2025=183, 2026=72. **2017·2026은 부분 연도**(2017은 3월 시작, 2026은 6월까지 + 미래 제외) → 절대수 대신 **비중·회차당 평균**으로 정규화하고 부분 연도를 주석.
- 연도별 고유 회차 수: 2017=36 … 2022~2025=52~57, 2026=23.
- 카테고리×연도 추이 뚜렷(강화 18→65, 사냥효율 16→59 증가; 수집기타 ~20 평탄). → Q1 유효.
- cycle_days 비결측 1063, 평균주기 산출 가능 norm 41개 → Q2 유효.
- is_discontinued True 311 / False 807 → Q3 유효.

### EDA 4종 (혼합: 운영 2 + 패턴 2)
| ID | 질문(1문장) | 컬럼 |
|---|---|---|
| Q1 | 보상 **카테고리 구성**이 9년간 어떻게 변했나? | year, category |
| Q8 | **회차당 보상 수**가 어떻게 변했나? (운영 강화 추세) | year, date, reward_raw |
| Q2 | 어떤 보상이 **자주/드물게 재등장**하나? | reward_norm, cycle_days |
| Q3 | **무엇이 단종되고 무엇이 살아남았나?** | is_discontinued, category, date |

## 제약 조건

- `data/raw/` 불변, `tidy_rewards.csv` 재생성·수정 없음(읽기만). `src/parse.py`/`normalize.py`/`features.py` 변경 없음.
- 기존 `python -m pytest -q` 통과 유지.
- 새 노트북은 `tidy_rewards.csv`만 로드(재파싱 금지). 분석 기본 필터 `reward_norm.notna() & ~is_future` 명시.
- 그래프·텍스트 전부 한글(한글 폰트 깨짐 금지). 난수 사용 시 시드 고정.
- 오버엔지니어링 금지(CLAUDE.md): 모델은 보조·최소. 화려함보다 질문에 답하는 그래프.

---

## 작업 1 — `src/viz.py` (한글 폰트 + 헬퍼)

**수정 대상**: `src/viz.py`(신규), `tests/test_viz.py`(경량, 선택).

```python
def set_korean_font() -> None:
    # Windows: Malgun Gothic, axes.unicode_minus=False
def save_fig(fig, name: str, outdir="outputs/figures") -> str:
    # outdir 생성 후 {name}.png 저장(dpi 적정), 경로 반환
```
- `set_korean_font`은 `plt.rcParams['font.family']='Malgun Gothic'`, `axes.unicode_minus=False`.
- 폰트 부재 환경 대비 try/except로 경고만(테스트 환경 깨지지 않게). 과한 방어는 금지 — Windows 전제.

## 작업 2 — `notebooks/04_eda.ipynb` (EDA 4종)

각 분석 = **질문 1문장 마크다운 셀 → 코드 셀(집계+그래프) → 해석 1~2문장 마크다운**. 그래프는 `viz.save_fig`로 `outputs/figures/`에 저장. 첫 셀에서 tidy 로드 + 기본 필터 + `set_korean_font()`.

- **Q1 카테고리 구성 변화**: 연도×category 건수 → 연도별 **비중**(100% 누적 막대 또는 누적 영역). 부분 연도(2017·2026) 주석. 저장 `q1_category_share_by_year.png`. 해석: 강화·사냥효율 비중 증가 등.
- **Q8 회차당 보상 수**: 연도별 `보상수/고유회차수` 평균 선그래프(또는 막대). 부분 연도 주석. 저장 `q8_rewards_per_session.png`. 해석: 2017 ~2.0 → 2025 ~3.5 증가.
- **Q2 재등장 주기**: cycle_days 비결측 기준 ① norm별 **중앙 cycle_days** 막대(자주=하위, 드묾=상위 각 10개), ② cycle_days 전체 분포 히스토그램. 저장 `q2_cycle_by_norm.png`, `q2_cycle_hist.png`. 해석: 주력 보상(스타포스·룬 등) 짧은 주기 vs 희귀 보상.
- **Q3 단종/생존**: ① category별 단종 vs 현행 보상 **고유 reward_norm/조합 수** 비교 막대, ② 단종 보상의 **마지막 등장 연도** 분포(언제 사라졌나) 히스토그램/막대. 저장 `q3_discontinued_by_category.png`, `q3_last_seen_year.png`. 해석: 어떤 종류가 정리됐나.
- 마지막 셀: 본 EDA가 **정규 보상 기준**(이벤트 연동 제외 스코프, data_dictionary 7장)임을 한 줄 주석.

## 작업 3 — `notebooks/05_model.ipynb` (최소 베이스라인, 보조)

목표: "각 보상(norm)의 **다음 등장 간격**을 과거 주기로 예측" 베이스라인. **보조·최소**임을 서두에 명시.

- 대상: cycle_days 산출 가능 norm(등장 3회 이상). 시드 고정.
- 방법: 각 norm의 등장일 시간순 정렬 → **마지막 간격을 holdout**, 그 이전 cycle_days **중앙값**으로 예측. 평가 지표 **MAE(일)**.
- 비교(naive): 전역 cycle_days 중앙값으로 동일 예측 → MAE 대조.
- 산출: norm별/전체 MAE 표 1개 + 예측 vs 실제 산점도 1개(`outputs/figures/model_pred_vs_actual.png`). 결과 1~2문장 해석(베이스라인 한계 포함).
- **확장 금지**: 추가 피처·복잡 모델·튜닝 없음. 한 베이스라인 + naive 대조로 종료.

## 검증 기준

- `python -m pytest -q` 통과 유지(+viz 테스트 시 통과).
- `04_eda.ipynb`·`05_model.ipynb` 커널 재시작 후 순차 재실행 성공(`tidy_rewards.csv`만 의존).
- `outputs/figures/`에 그래프 저장(한글 깨짐 없음), 각 그래프가 대응 질문 1문장과 연결.
- 노트북 비코드 텍스트·그래프 라벨 전부 한글.

## 작업 우선순위 요약
| 작업 | 대상 | 규모 | 의존 |
|---|---|---|---|
| 1 | `src/viz.py`(+테스트) | ~40줄 | 없음 |
| 2 | `04_eda.ipynb` 4종 | ~120줄 | 작업1, tidy |
| 3 | `05_model.ipynb` 베이스라인 | ~50줄 | 작업1, tidy |

## 이번 범위 제외 / 다음
- 복잡 예측 모델·하이퍼파라미터 튜닝·추가 피처 — 제외(보조 목표).
- 최종 리포트(`outputs/report/`) 작성 — EDA 결과 확정 후 별도 Phase.
- 추가 EDA 질문(Q4~Q6) — 발표 분량 보고 필요 시 후속.
