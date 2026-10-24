import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect, it } from 'vitest'
import { AboutPage } from './About'
import { SiteLayout } from './App'
import fixture from './__fixtures__/site.json'
import type { SiteData } from './types'
const data=fixture as SiteData

it('방법론에 데이터 흐름과 평가 및 한계를 설명한다',()=>{
 render(<AboutPage data={data}/>)
 expect(screen.getByRole('heading',{name:'방법론'})).toBeInTheDocument()
 expect(screen.getByRole('list',{name:'데이터 처리 흐름'})).toBeInTheDocument()
 expect(screen.getByText('0.522')).toBeInTheDocument()
 expect(screen.getByText(/매주 전체 승인 관측으로 재학습/)).toBeInTheDocument()
 expect(screen.getByText(/선물류·일회성 보상/)).toBeInTheDocument()
})

it.each([['/about','방법론'],['/insights','분석 요약']])('라우트 %s가 메뉴와 연결된다',(route,title)=>{
 render(<MemoryRouter initialEntries={[route]}><SiteLayout data={data}/></MemoryRouter>)
 expect(screen.getByRole('heading',{name:title})).toBeInTheDocument()
 expect(screen.getByRole('link',{name:title})).toHaveAttribute('href',route)
})
