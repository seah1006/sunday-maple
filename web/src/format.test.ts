import { describe, expect, it } from 'vitest'
import { daysAgo, displayName, formatDate, formatGeneratedAt, formatScore } from './format'
describe('표시 헬퍼',()=>{
 it('표시명은 모든 밑줄을 공백으로 바꾼다',()=>expect(displayName('스타포스_비용_할인')).toBe('스타포스 비용 할인'))
 it('모델 점수를 한 자리로 표시한다',()=>expect(formatScore(0.667)).toBe('66.7'))
 it('날짜와 경과일을 표시한다',()=>{expect(formatDate('2026-06-14T00:00:00Z')).toBe('2026-06-14');expect(daysAgo('2026-06-14','2026-06-21')).toBe(7)})
 it('생성 시각은 한국 시간으로 표시한다',()=>expect(formatGeneratedAt('2026-06-14T00:00:00Z')).toContain('9:00'))
})
