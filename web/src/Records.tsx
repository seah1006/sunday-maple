import { useState } from 'react'
import { displayName } from './format'
import type { SiteData, Reward } from './types'

export function TrackPage({data}: {data: SiteData}) {
 return <section><div className="heading"><p className="eyebrow">예측을 기록으로 확인하기</p><h1>얼마나 맞혔을까요?</h1><p className="intro">실제 보상 수 k만큼 상위 k개를 뽑았을 때 하나라도 맞힌 회차 비율</p></div><p className="notice">{data.backtest.split_cutoff} 이후 회차, 학습은 그 이전 데이터만 사용<br />백테스트 데이터 기준 {data.meta.backtest_data_through} · 과거 데이터 재평가이며 사전 저장된 운영 예측 기록은 아닙니다.</p>
 <div className="panel metrics">{data.backtest.metrics.map(m => <div className={`metric ${['random_forest','prophet'].includes(m.method) ? 'highlight' : ''}`} key={m.method}><div><strong>{m.label}</strong><span>{m.date_hit_rate === null ? '판정 불가' : m.date_hit_rate.toFixed(3)}</span></div><div className="bar"><div style={{width: `${(m.date_hit_rate ?? 0)*100}%`}} /></div></div>)}</div><div className="section-title"><h2>회차별 적중 기록</h2><span>랜덤포레스트 · 최신순</span></div><div className="table-wrap"><table><thead><tr><th>날짜</th><th>실제 보상</th><th>예측 후보</th><th>적중</th></tr></thead><tbody>{[...data.backtest.per_date].sort((a,b)=>b.date.localeCompare(a.date)).map(r => <tr key={r.date}><td className="nowrap">{r.date}</td><td>{r.actual.map(n=><span className={`reward-line ${r.predicted.includes(n)?'matched':''}`} key={n}>{displayName(n)}</span>)}</td><td>{r.predicted.map(n=><span className={`reward-line ${r.actual.includes(n)?'matched':''}`} key={n}>{displayName(n)}</span>)}</td><td className={r.hit===1?'matched':'muted'}>{r.hit===null?'판정 불가':r.hit===1?'O':'X'}</td></tr>)}</tbody></table></div></section>
}

type SortKey = keyof Reward
export function HistoryPage({data}: {data: SiteData}) {
 const [query,setQuery]=useState('')
 const [category,setCategory]=useState('')
 const [limit,setLimit]=useState(50)
 const [sort,setSort]=useState<{key: SortKey; ascending: boolean}>({key:'appearances',ascending:false})
 const categories=[...new Set(data.rewards.map(r=>r.category))].sort()
 const filtered=data.history.filter(r=>r.rewards.some(i=>(!category||i.category===category)&&`${i.reward_raw??''} ${displayName(i.reward_norm)}`.toLowerCase().includes(query.toLowerCase())))
 const rewards=[...data.rewards].sort((a,b)=>{
  const l=a[sort.key],r=b[sort.key]
  const result=l===r?0:l===null?1:r===null?-1:typeof l==='number'&&typeof r==='number'?l-r:String(l).localeCompare(String(r),'ko')
  return sort.ascending?result:-result
 })
 const columns: [SortKey,string][]=[['reward_norm','보상'],['category','카테고리'],['appearances','등장 횟수'],['first_seen','첫 등장'],['last_seen','마지막 등장'],['median_cycle_days','주기 중앙값'],['is_discontinued','단종 여부']]
 return <section><div className="heading"><p className="eyebrow">쌓여 온 썬데이의 기록</p><h1>역대 이력</h1><p className="intro">보상과 이벤트를 검색하고, 돌아오는 주기를 살펴보세요.</p></div><div className="filters"><label>보상 검색<input type="search" value={query} placeholder="보상 이름으로 찾아보세요" onChange={e=>{setQuery(e.target.value);setLimit(50)}} /></label><label>카테고리<select value={category} onChange={e=>{setCategory(e.target.value);setLimit(50)}}><option value="">전체 카테고리</option>{categories.map(n=><option key={n}>{n}</option>)}</select></label></div><p role="status" className="muted">총 {filtered.length}개 회차 · {Math.min(limit,filtered.length)}개 표시</p>
 <div>{filtered.slice(0,limit).map(r=><article className="history-entry" key={r.date}><div><h2>{r.date}</h2><p className="muted">{r.event_context??'이벤트 맥락 정보 없음'}</p>{r.is_special&&<span className="badge special">스페셜 썬데이</span>}</div><ul>{r.rewards.map((i,index)=><li key={`${i.reward_norm}-${index}`}>{i.reward_raw??displayName(i.reward_norm)} <span className="badge">{i.category}</span></li>)}</ul></article>)}</div>
 {!filtered.length&&<p className="empty">일치하는 회차가 없습니다. 다른 검색어를 입력해 주세요.</p>}{filtered.length>limit&&<button className="more" onClick={()=>setLimit(limit+50)}>더 보기</button>}
 <div className="section-title"><h2>보상별 통계</h2><span>열 제목을 눌러 정렬</span></div><div className="table-wrap"><table><thead><tr>{columns.map(([key,label])=><th key={key} aria-sort={sort.key===key?sort.ascending?'ascending':'descending':'none'}><button onClick={()=>setSort({key,ascending:sort.key===key?!sort.ascending:true})}>{label}{sort.key===key?sort.ascending?' ↑':' ↓':''}</button></th>)}</tr></thead><tbody>{rewards.map(r=><tr key={r.reward_norm}><td>{displayName(r.reward_norm)}</td><td>{r.category}</td><td>{r.appearances}회</td><td className="nowrap">{r.first_seen}</td><td className="nowrap">{r.last_seen}</td><td>{r.median_cycle_days===null?'기록 없음':`${r.median_cycle_days}일`}</td><td>{r.is_discontinued?'단종':'아니요'}</td></tr>)}</tbody></table></div></section>
}
