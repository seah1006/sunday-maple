import type { SiteData } from './types'

export async function loadSiteData(): Promise<SiteData> {
  const names = ['meta', 'forecast', 'backtest', 'history', 'rewards', 'live_record'] as const
  const results = await Promise.all(names.map(async name => {
    const response = await fetch(`${import.meta.env.BASE_URL}data/${name}.json`)
    if (!response.ok) throw new Error('데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.')
    return response.json()
  }))
  return Object.fromEntries(names.map((name, index) => [name, results[index]])) as unknown as SiteData
}
