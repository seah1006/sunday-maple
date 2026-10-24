from pathlib import Path

import pandas as pd
from src.normalize import normalize_reward, categorize, extract_magnitude
from src.observations import load_manual_observations

COLUMNS = ['date', 'notice_id', 'title', 'is_special', 'reward_raw', 'scope', 'reward_norm', 'category', 'source_url', 'extracted_by', 'reviewed', 'review_method', 'note']


def store_extracted(notice, rewards, *, provider, model, out_dir='data/observations', known_rewards=None):
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    if known_rewards is None:
        known_rewards = set(pd.read_csv('data/processed/tidy_rewards.csv').reward_norm.dropna())
    rows, unmapped = [], []
    for item in rewards:
        raw = item['reward_raw']
        if raw.strip() == '샤이닝 스타포스 타임':
            continue
        norm = normalize_reward(raw)
        row = {'date': notice.start_date, 'notice_id': notice.id, 'title': notice.title, 'is_special': notice.is_special, 'reward_raw': raw, 'scope': item.get('scope', 'all'), 'reward_norm': norm, 'category': categorize(norm) if norm else None, 'source_url': notice.url, 'extracted_by': f'{provider}:{model}', 'reviewed': False, 'review_method': '', 'note': f"special_time_header: {item['special_time_header']} (scope={item.get('scope', 'all')})" if item.get('special_time_header') else ''}
        if norm is None or norm not in known_rewards:
            row['note'] = '미등록 보상: 사람 확인 필요'
            unmapped.append({**row, 'reward_magnitude': extract_magnitude(raw)})
        rows.append(row)
    path = root / 'official.csv'
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=COLUMNS)
    if notice.id in set(existing.notice_id):
        prior = existing.loc[existing.notice_id == notice.id]
        if prior.reviewed.astype(str).str.lower().eq('true').any():
            return prior.copy()
        existing = existing.loc[existing.notice_id != notice.id]
    pd.concat([existing, pd.DataFrame(rows)], ignore_index=True).to_csv(path, index=False, encoding='utf-8')
    if unmapped:
        path = root / 'unmapped.csv'
        old = pd.read_csv(path) if path.exists() else pd.DataFrame()
        pd.concat([old, pd.DataFrame(unmapped)], ignore_index=True).drop_duplicates(['notice_id', 'reward_raw']).to_csv(path, index=False, encoding='utf-8')
    return pd.DataFrame(rows)


def load_reviewed_observations(manual_path='data/interim/manual_obs_20260614.csv', official_path='data/observations/official.csv'):
    manual = load_manual_observations(manual_path)
    path = Path(official_path)
    if not path.exists():
        return manual
    official = pd.read_csv(path, parse_dates=['date'])
    official = official.loc[official.reviewed.astype(str).str.lower().eq('true')].copy()
    if official.empty:
        return manual
    if official.reward_norm.isna().any():
        raise ValueError('리뷰 완료 관측에 미등록 보상이 있음')
    if 'scope' not in official:
        official['scope'] = 'all'
    official['scope'] = official.scope.fillna('all')
    official['is_special'] = official.is_special.astype(str).str.lower().eq('true')
    manual = manual.loc[~manual.date.isin(official.date)]
    return pd.concat([manual, official], ignore_index=True, sort=False)
