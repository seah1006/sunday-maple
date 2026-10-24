import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi, afterEach } from 'vitest'
import App, { ForecastPage, SiteLayout } from './App'
import { TrackPage, HistoryPage } from './Records'
import fixture from './__fixtures__/site.json'
import type { SiteData } from './types'
const data=fixture as SiteData
afterEach(()=>vi.restoreAllMocks())
describe('화면',()=>{
 it('예측 메인에 후보와 점수를 표시한다',()=>{render(<ForecastPage data={data}/>);expect(screen.getByRole('heading',{name:'몬스터컬렉션'})).toBeInTheDocument();expect(screen.getByText('66.7')).toBeInTheDocument();expect(screen.getByText(/보정된 확률이 아닙니다/)).toBeInTheDocument()})
 it('Prophet이 없으면 비교를 숨긴다',()=>{render(<ForecastPage data={{...data,forecast:{...data.forecast,prophet:null}}}/>);expect(screen.queryByText('Prophet 모델과 비교하기')).not.toBeInTheDocument()})
 it('적중 기록에 방법별 지표와 회차 표를 표시한다',()=>{render(<TrackPage data={data}/>);expect(screen.getByText('0.449')).toBeInTheDocument();expect(screen.getByRole('table')).toBeInTheDocument()})
 it('검색과 카테고리 필터로 결과가 바뀐다',()=>{render(<HistoryPage data={data}/>);expect(screen.getByRole('status')).toHaveTextContent('총 3개 회차');fireEvent.change(screen.getByRole('searchbox'),{target:{value:'몬스터파크 경험치'}});expect(screen.getByRole('status')).toHaveTextContent('총 1개 회차');fireEvent.change(screen.getByRole('combobox'),{target:{value:'강화'}});expect(screen.getByRole('status')).toHaveTextContent('총 0개 회차')})
 it('통계 열 정렬 방향을 바꾼다',()=>{render(<HistoryPage data={data}/>);const table=screen.getByRole('table');fireEvent.click(within(table).getByRole('button',{name:/등장 횟수/}));expect(within(table).getByRole('columnheader',{name:/등장 횟수/})).toHaveAttribute('aria-sort','ascending')})
 it('HashRouter 안에서 사용할 공통 레이아웃을 표시한다',()=>{render(<MemoryRouter><SiteLayout data={data}/></MemoryRouter>);expect(screen.getByText(/데이터 기준 2026-06-14/)).toBeInTheDocument();expect(screen.getByText('넥슨과 무관한 비공식 프로젝트')).toBeInTheDocument()})
 it('데이터 실패시 한글 안내를 표시한다',async()=>{vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('network')));render(<App/>);expect(await screen.findByRole('alert')).toHaveTextContent('데이터를 불러오지 못했어요');vi.unstubAllGlobals()})
})
