const figures = [
  {
    file: 'q1_category_share_by_year.png',
    title: '보상 구성은 강화·성장 쪽으로 이동',
    alt: '2017년부터 2026년까지 연도별 보상 카테고리 비중',
    conclusion: '2017년에는 사냥효율 비중이 38.0%로 가장 컸고, 이후 강화와 성장 쪽으로 무게가 옮겨 갔습니다. 2017년과 2026년은 일부 기간만 집계한 해입니다.',
  },
  {
    file: 'q2_cycle_hist.png',
    title: '재등장 주기의 중심은 42일',
    alt: '보상 재등장 간격의 분포를 나타낸 히스토그램',
    conclusion: '주기 중앙값은 42일, 평균은 65.2일입니다. 수백 일씩 나오지 않는 보상도 있어, 평균 주기 하나만으로 다음 등장을 설명하기는 어렵습니다.',
  },
  {
    file: 'q3_discontinued_by_category.png',
    title: '성장·사냥효율·수집기타에서 보상 정리가 집중',
    alt: '카테고리별 현행 보상과 단종 표기 보상의 고유 원문 수 비교',
    conclusion: '강화보다 성장·사냥효율·수집기타에서 단종 표기 보상의 비중이 컸습니다. 여기서 단종은 원문 작성자의 당시 표기이며, 현재도 영구 단종이라는 뜻은 아닙니다.',
  },
  {
    file: 'q8_rewards_per_session.png',
    title: '한 회차에 담기는 보상 수는 증가',
    alt: '연도별 썬데이 메이플 한 회차당 평균 보상 수',
    conclusion: '회차당 보상 수는 2017년 1.972개에서 2025년 3.519개로 늘었습니다. 단일 혜택보다 여러 보상을 묶어 제시하는 방향으로 바뀌었습니다.',
  },
]

export function InsightsPage() {
  return <section className="editorial">
    <div className="heading"><p className="eyebrow">기록에서 읽는 변화</p><h1>분석 요약</h1><p className="intro">어떤 보상이 늘고, 얼마나 자주 돌아왔을까요?</p></div>
    <aside className="notice"><strong>2026년 6월 인벤 데이터 기준</strong><p>그림은 2017-03-12~2026-06-07의 분석 대상 1,118행으로 만든 기존 EDA 결과입니다. 이후 공식 공지 백필과 현재 운영 예보를 반영해 다시 그린 자료가 아닙니다.</p></aside>
    <div className="insight-list">{figures.map(figure => <article className="panel insight-card" key={figure.file}>
      <h2>{figure.title}</h2><figure><img src={`${import.meta.env.BASE_URL}figures/${figure.file}`} alt={figure.alt} loading="lazy" /><figcaption>{figure.conclusion}</figcaption></figure>
    </article>)}</div>
    <p className="muted">근거: 저장소의 outputs/report/final_report.md 탐색적 분석 Q1·Q2·Q3·Q8. 과거 분석과 최신 운영 예보의 기준일을 구분해 읽어 주세요.</p>
  </section>
}
