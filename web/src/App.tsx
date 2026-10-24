import { useEffect, useState } from 'react'
import { HashRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { loadSiteData } from './data'
import { displayName, formatGeneratedAt, formatScore } from './format'
import { HistoryPage, TrackPage } from './Records'
import type { SiteData } from './types'

export function ForecastPage({ data }: { data: SiteData }) {
 const f = data.forecast
 return <section><div className="heading"><p className="eyebrow">다음 회차 미리 보기</p><h1>{f.target_date}<br />썬데이 메이플 예측</h1><p className="intro">지난 기록에서 찾은 다음 썬데이의 후보들.<br />어떤 보상이 돌아올지 함께 살펴보세요.</p></div>
 <div className="section-title"><h2>주목할 후보 5</h2><span>랜덤포레스트 · 모델 점수순</span></div>
 <div className="cards">{f.classifier.slice(0,5).map(c => <article className={`card rank-${c.rank}`} key={c.reward_norm}><div className="card-top"><span className="rank">{String(c.rank).padStart(2,'0')}</span><span className="badge">{c.category}</span></div><h3>{displayName(c.reward_norm)}</h3><div className="score"><strong>{formatScore(c.score)}</strong><span>모델 점수</span></div><div className="bar"><div style={{width: `${c.score*100}%`}} /></div><p className="last">마지막 등장 {c.days_since_last}일 전<br />({c.last_seen})</p></article>)}</div>
 <aside className="notice"><strong>점수는 어떻게 읽나요?</strong><p>모델 점수는 보정된 확률이 아닙니다. 상위 후보는 검토 우선순위일 뿐 확정 예보가 아닙니다. 마지막 등장 경과일은 예측 대상 날짜 기준입니다.</p></aside>
 <section className="panel"><h2>함께 살펴볼 후보</h2><ul className="rows">{f.classifier.slice(5).map(c => <li key={c.reward_norm}><span className="muted">{c.rank}</span><strong>{displayName(c.reward_norm)}</strong><span className="badge">{c.category}</span><span>{formatScore(c.score)}</span></li>)}</ul></section>
 {f.prophet && <details className="panel"><summary>Prophet 모델과 비교하기</summary><p className="muted">yhat은 등장 확률이 아닌 주기 기반 모델의 예측값입니다.</p><ol>{f.prophet.slice(0,5).map(c => <li key={c.reward_norm}>{displayName(c.reward_norm)} <strong>{c.yhat.toFixed(3)}</strong></li>)}</ol></details>}
 <details className="panel"><summary>이번 예측에서 제외된 후보 · {f.excluded.length}개</summary><ul>{f.excluded.map(c => <li key={c.reward_norm}>{displayName(c.reward_norm)} <span className="muted">{c.reason === 'recency_gate' ? '180일 넘게 미등장' : '단종 처리'}</span></li>)}</ul></details></section>
}

export function SiteLayout({ data }: { data: SiteData }) {
 const location=useLocation()
 useEffect(()=>{window.scrollTo(0,0)},[location.pathname])
 return <><header><NavLink className="brand" to="/">썬데이 메이플 <span>예보</span></NavLink><nav aria-label="주 메뉴"><NavLink to="/" end>예측</NavLink><NavLink to="/track">적중 기록</NavLink><NavLink to="/history">역대 이력</NavLink></nav></header><main><div className="data-badge">데이터 기준 {data.meta.data_through}<span> · 생성 {formatGeneratedAt(data.meta.generated_at)}</span></div><Routes><Route path="/" element={<ForecastPage data={data} />} /><Route path="/track" element={<TrackPage data={data} />} /><Route path="/history" element={<HistoryPage data={data} />} /><Route path="*" element={<p>찾을 수 없는 페이지입니다. 위 메뉴로 이동해 주세요.</p>} /></Routes></main><footer><strong>썬데이 메이플 예보</strong><p>넥슨과 무관한 비공식 프로젝트</p><p>출처: <a href="https://www.inven.co.kr/board/maple/2304/20563" target="_blank" rel="noreferrer">인벤 역대 썬데이메이플 정리</a> · <a href="https://maplestory.nexon.com/News/Event" target="_blank" rel="noreferrer">메이플스토리 공식 공지</a></p></footer></>
}

export default function App() {
 const [data,setData] = useState<SiteData | null>(null)
 const [failed,setFailed] = useState(false)
 useEffect(() => { let active = true; loadSiteData().then(d => {if(active) setData(d)}).catch(() => {if(active) setFailed(true)}); return () => {active=false} },[])
 if(failed) return <main className="empty" role="alert">데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.</main>
 if(!data) return <main className="empty" role="status">썬데이 기록을 불러오는 중입니다.</main>
 return <HashRouter><SiteLayout data={data} /></HashRouter>
}
