import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

import pandas as pd

from src.official import list_sunday_notices, fetch_notice, save_notice_raw
from src.official_observations import store_extracted, load_reviewed_observations
from src.site_data import export_site_data, _clean
from src.vision import load_env, cached_extract_rewards, PROMPT_VERSION


def collect(official_path='data/observations/official.csv'):
    path = Path(official_path)
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=['notice_id', 'reward_norm'])
    known_ids = set(existing.notice_id)
    notices = list_sunday_notices(oldest_id=int(max(known_ids)) if known_ids else 1300)
    new = [notice for notice in notices if notice.id not in known_ids]
    summary = ['# 공식 공지 추출 검토', '', f'신규 공지 {len(new)}개. 자동 머지하지 않습니다. 이미지 대조 후 승인해 주세요.', '']
    if new:
        load_env()
        if not os.environ.get('VISION_API_KEY'):
            raise ValueError('VISION_API_KEY가 필요합니다')
    for notice in new:
        detail = fetch_notice(notice)
        metas = save_notice_raw(detail)
        images = [meta.with_name(meta.name.replace('_meta.json', '.png')) for meta in metas]
        if not images:
            summary.append(f'공지 {notice.id}: 정지 이미지 없음. 수동 확인 필요. {notice.url}')
            continue
        rows = cached_extract_rewards(notice.id, [image.read_bytes() for image in images], detail.correction_text, provider=os.environ.get('VISION_PROVIDER', 'gemini'), model=os.environ.get('VISION_MODEL', 'gemini-3.5-flash-lite'), api_key=os.environ['VISION_API_KEY'])
        known = set(pd.read_csv('data/processed/tidy_rewards.csv').reward_norm.dropna()) | set(existing.reward_norm.dropna())
        saved = store_extracted(notice, rows, provider=os.environ.get('VISION_PROVIDER', 'gemini'), model=os.environ.get('VISION_MODEL', 'gemini-3.5-flash-lite'), out_dir=path.parent, known_rewards=known)
        summary += [f'## {notice.id} {notice.start_date} {notice.title}', '', f'공지: {notice.url}', f'프롬프트: {PROMPT_VERSION}', '']
        summary += [f'이미지: {url}' for url in detail.image_urls]
        summary += [f'원본: {image.as_posix()}' for image in images]
        summary += ['', '| 원문 | 정규화 | scope | 검토 |', '|---|---|---|---|']
        for row in saved.itertuples():
            summary.append(f'| {row.reward_raw.replace(chr(124), chr(47))} | {row.reward_norm or "미등록"} | {row.scope} | 미검토 |')
        unmapped = saved.loc[saved.reward_norm.isna()]
        summary += ['', '미등록: ' + (', '.join(unmapped.reward_raw) if len(unmapped) else '없음'), '정정문: ' + (detail.correction_text or '없음'), '']
    text = '\n'.join(summary) + '\n'
    output = Path('data/interim/weekly_summary.md')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding='utf-8')
    print(text)
    return len(new)


def approve(notice_ids, review_method, official_path='data/observations/official.csv'):
    if review_method not in {'image_checked', 'pattern_approved', 'user_approved'}:
        raise ValueError('유효한 review_method가 필요합니다')
    path = Path(official_path)
    frame = pd.read_csv(path)
    if set(notice_ids) - set(frame.notice_id):
        raise ValueError('CSV에 없는 공지 ID')
    selected = frame.notice_id.isin(notice_ids)
    if frame.loc[selected, 'reward_norm'].isna().any():
        raise ValueError('미등록 보상을 먼저 수정해야 합니다')
    frame['review_method'] = frame.get('review_method', pd.Series('', index=frame.index)).astype('string').fillna('')
    frame.loc[selected, 'reviewed'] = True
    frame.loc[selected, 'review_method'] = review_method
    frame.to_csv(path, index=False, encoding='utf-8')
    return int(selected.sum())


def save_prediction(payloads, out_dir='data/predictions', now=None, model_version=None):
    meta, forecast = payloads['meta'], payloads['forecast']
    target = pd.Timestamp(forecast['target_date']).normalize()
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    output = root / f'{target.date()}.json'
    if output.exists():
        return False
    current = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz='Asia/Seoul')
    current = current.tz_localize('Asia/Seoul') if current.tzinfo is None else current.tz_convert('Asia/Seoul')
    if current.date() >= target.date():
        raise ValueError('일요일 당일 또는 이후에는 예측을 새로 저장할 수 없습니다')
    version = model_version or subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip())
    snapshot = {'target_date': str(target.date()), 'generated_at': datetime.now(timezone.utc).isoformat() if now is None else current.isoformat(), 'model_version': version, 'working_tree_dirty': dirty, 'model_policy': meta.get('model_policy'), 'training_through': meta.get('training_through', meta['data_through']), 'classifier': forecast['classifier'], 'prophet': forecast['prophet']}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(_clean(snapshot), stream, ensure_ascii=False, indent=2, allow_nan=False)
    return True


def forecast(out='data/site', predictions='data/predictions', now=None):
    payloads = export_site_data(out=out)
    created = save_prediction(payloads, predictions, now=now)
    print(f'예측 저장: {"신규" if created else "기존 유지"} {payloads["forecast"]["target_date"]}')
    return created


def _score_model(rows, actual):
    names = [row['reward_norm'] for row in rows]
    k = len(actual & set(names))
    return {'top5': names[:5], 'top5_hits': len(actual & set(names[:5])), 'k': k, 'k_hit': int(bool(actual & set(names[:k]))) if k else None, 'outside_candidates': sorted(actual - set(names))}


def score(predictions='data/predictions', out='data/site/live_record.json', observations=None):
    frame = load_reviewed_observations() if observations is None else observations.copy()
    frame['date'] = pd.to_datetime(frame.date)
    frame = frame.loc[frame.get('scope', pd.Series('all', index=frame.index)).fillna('all').eq('all')]
    actual_by_date = {str(date.date()): set(group.reward_norm.dropna()) for date, group in frame.groupby('date')}
    records = []
    for path in sorted(Path(predictions).glob('*.json'), reverse=True):
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        actual = actual_by_date.get(snapshot['target_date'])
        if actual is None:
            continue
        records.append({'target_date': snapshot['target_date'], 'generated_at': snapshot['generated_at'], 'actual': sorted(actual), 'classifier': _score_model(snapshot['classifier'], actual), 'prophet': _score_model(snapshot['prophet'], actual) if snapshot['prophet'] is not None else None})
    output = Path(out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'실전 채점 {len(records)}회차')
    return records


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('collect')
    commands.add_parser('forecast')
    commands.add_parser('score')
    approval = commands.add_parser('approve')
    approval.add_argument('--pr-rows', type=int, nargs='+', required=True)
    approval.add_argument('--review-method', required=True)
    args = parser.parse_args(argv)
    if args.command == 'approve':
        print(f'승인 {approve(args.pr_rows, args.review_method)}행')
    else:
        {'collect': collect, 'forecast': forecast, 'score': score}[args.command]()


if __name__ == '__main__':
    main()
