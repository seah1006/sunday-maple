import type { SiteData } from './types'

const pipeline = [
  ['기록 수집', '인벤 이력과 공식 공지 이미지'],
  ['이미지 추출', 'Gemini가 혜택 제목과 scope 추출'],
  ['사람 검토', '이미지 대조 · 미등록 수정 · PR 승인'],
  ['관측 정리', '원문 보존 · 보상 정규화 · scope 분리'],
  ['다음 회차 예보', '전체 관측 재학습 · 재등장 게이트'],
  ['사이트 제공', 'JSON → React · 실전 스냅샷 보존'],
]

export function AboutPage({ data }: { data: SiteData }) {
  return <section className="editorial">
    <div className="heading"><p className="eyebrow">예측이 만들어지는 과정</p><h1>방법론</h1><p className="intro">점수의 의미와 평가 기준, 그리고 모델이 모르는 것들.</p></div>
    <section className="panel"><h2>기록에서 예보까지</h2><p>인벤의 2017-03-12~2026-06-07 이력에 공식 공지의 승인된 보상을 연결합니다. 원래 tidy는 1,160행이며 분석 대상은 1,118행입니다.</p>
      <ol className="pipeline-flow" aria-label="데이터 처리 흐름">{pipeline.map(([title, description], index) => <li key={title}><strong>{String(index + 1).padStart(2, '0')}</strong><b>{title}</b><span>{description}</span></li>)}</ol>
      <p>원본과 당시 예측은 덮어쓰지 않습니다. 이미지 추출 결과는 자동 확정하지 않고, PR 검토와 사용자 승인 후에만 운영 관측에 넣습니다. 월드 전용 혜택은 이력에 scope 배지로 표시하고 모델에는 <code>scope=all</code>만 사용합니다.</p>
    </section>
    <section className="panel"><h2>모델 점수는 확률이 아닙니다</h2><p>랜덤포레스트는 경과일, 과거 등장 횟수·비율, 최근 주기, 계절 정보로 후보를 정렬합니다. 화면의 모델 점수는 보정된 확률이 아닙니다. 상위 후보는 검토 우선순위일 뿐 확정 예보가 아닙니다.</p><p>Prophet은 보상별 주간 등장 기록에서 연간 변화와 28일 주기 신호를 봅니다. 비교 섹션의 yhat도 확률이 아닌 상대적인 예측 점수입니다.</p></section>
    <section className="panel"><h2>왜 재등장 게이트가 필요한가요?</h2><p>오래 나오지 않은 보상을 경과일만으로 유력하게 보는 문제를 줄이기 위해, 예측 대상 날짜 미만의 마지막 등장 후 180일을 넘긴 후보를 거릅니다.</p><p>단종 표기는 영구적인 사실이 아닙니다. 재등장이 확인된 스타포스 1+1 강화는 운영 경로에서 영구 제외하지 않습니다. 과거 백테스트의 게이트는 지표 비교를 위해 그대로 유지합니다.</p></section>
    <section className="panel"><h2>과거 백테스트와 실전 기록</h2><p>백테스트는 {data.backtest.split_cutoff} 이전 데이터로 학습하고 이후 회차를 평가한 기록입니다. 미래 관측을 학습에 섞지 않도록 시간순으로 나눴습니다. 아래 수치는 고정된 과거 평가이며, 매주 전체 승인 관측으로 재학습하는 운영 예보의 실전 성적은 아닙니다.</p>
      <div className="table-wrap"><table aria-label="방법별 백테스트"><thead><tr><th>방법</th><th>회차 적중률</th></tr></thead><tbody>{data.backtest.metrics.map(metric => <tr key={metric.method}><td>{metric.label}</td><td>{metric.date_hit_rate === null ? '판정 불가' : metric.date_hit_rate.toFixed(3)}</td></tr>)}</tbody></table></div>
      <p>회차 적중률(date_hit_rate)은 후보 안의 실제 보상 수 k만큼 상위 k개를 골랐을 때 하나라도 맞힌 회차의 비율입니다.</p>
      <p>실전 기록은 일요일 전에 저장한 전체 후보 순위를 실제 보상과 대조합니다. 대상일 당일부터 새 스냅샷을 만들지 않고 기존 파일도 덮어쓰지 않습니다. 주 지표는 상위 5개 적중 수입니다. k는 실제 보상과 저장된 후보의 교집합 크기이며, k=0이면 k-적중은 판정 불가입니다. 후보 밖 보상도 함께 공개합니다.</p>
    </section>
    <aside className="notice"><strong>해석할 때의 한계</strong><ul><li>선물류·일회성 보상과 스페셜 편성 같은 운영 판단은 과거 주기만으로 설명하기 어렵습니다.</li><li>이미지 추출은 오인식할 수 있습니다. 검증셋 12/12 일치는 이후 모든 공지의 정확성을 보장하지 않습니다.</li><li>인벤은 2차 자료이며 공식 공지와 기록 범위가 다를 수 있습니다. 월드 전용 혜택을 분리한 이유입니다.</li></ul></aside>
    <p className="muted">근거: 저장소 README, data/site/backtest.json, docs/extraction_eval.md, outputs/report/final_report.md. 넥슨과 무관한 비공식 프로젝트입니다.</p>
  </section>
}
