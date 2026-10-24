import { render, screen } from '@testing-library/react'
import { expect, it, vi, afterEach } from 'vitest'
import { InsightsPage } from './Insights'

afterEach(()=>vi.unstubAllEnvs())

it('분석 요약에 네 그림과 과거 기준일을 표시한다',()=>{
 vi.stubEnv('BASE_URL','/sunday-maple/')
 render(<InsightsPage/> )
 expect(screen.getByRole('heading',{name:'분석 요약'})).toBeInTheDocument()
 expect(screen.getByText('2026년 6월 인벤 데이터 기준')).toBeInTheDocument()
 expect(screen.getAllByRole('img')).toHaveLength(4)
 expect(screen.getByAltText('보상 재등장 간격의 분포를 나타낸 히스토그램')).toHaveAttribute('src', '/sunday-maple/figures/q2_cycle_hist.png')
 expect(screen.getByText(/평균은 65.2일/)).toBeInTheDocument()
})
