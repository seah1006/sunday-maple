export interface Meta {
  generated_at: string; data_through: string; backtest_data_through: string; target_date: string
  sources: { name: string; url?: string; path?: string; fetched_at?: string }[]
  split_cutoff: string; random_seed: number
}
export interface Candidate { rank: number; reward_norm: string; category: string; score: number; days_since_last: number; last_seen: string }
export interface Forecast { target_date: string; classifier: Candidate[]; prophet: { reward_norm: string; yhat: number; rank: number }[] | null; excluded: { reward_norm: string; reason: 'recency_gate' | 'domain_discontinued' }[] }
export interface Metric { method: string; label: string; accuracy?: number | null; f1?: number | null; roc_auc?: number | null; date_hit_rate: number | null }
export interface Backtest { split_cutoff: string; metrics: Metric[]; per_date: { date: string; actual: string[]; actual_all: string[]; outside_candidates: string[]; predicted: string[]; hit: number | null; gated_predicted: string[]; gated_hit: number | null }[] }
export interface HistoryEntry { date: string; event_context: string | null; is_special: boolean; rewards: { reward_raw: string | null; reward_norm: string; category: string; scope?: string }[] }
export interface Reward { reward_norm: string; category: string; appearances: number; first_seen: string; last_seen: string; median_cycle_days: number | null; is_discontinued: boolean }
export interface SiteData { meta: Meta; forecast: Forecast; backtest: Backtest; history: HistoryEntry[]; rewards: Reward[]; live_record?: LiveRecord[] }

export interface LiveModelScore { top5: string[]; top5_hits: number; k: number; k_hit: number | null; outside_candidates: string[] }
export interface LiveRecord { target_date: string; generated_at: string; actual: string[]; classifier: LiveModelScore; prophet: LiveModelScore | null }
