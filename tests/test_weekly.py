import json

import pandas as pd
import pytest

from src.weekly import save_prediction, score, approve, collect


def payload():
    return {'meta': {'data_through': '2026-10-25', 'model_policy': 'weekly_full_history'}, 'forecast': {'target_date': '2026-11-01', 'classifier': [{'reward_norm': 'A'}, {'reward_norm': 'B'}], 'prophet': [{'reward_norm': 'B'}, {'reward_norm': 'A'}]}}


def test_prediction_immutable(tmp_path):
    assert save_prediction(payload(), tmp_path, now='2026-10-24', model_version='test')
    path = tmp_path / '2026-11-01.json'
    before = path.read_bytes()
    assert not save_prediction(payload(), tmp_path, now='2026-11-02', model_version='different')
    assert path.read_bytes() == before


@pytest.mark.parametrize('now', ['2026-11-01', '2026-11-02'])
def test_prediction_cannot_be_created_on_or_after_sunday(tmp_path, now):
    with pytest.raises(ValueError):
        save_prediction(payload(), tmp_path, now=now, model_version='test')
    assert not list(tmp_path.glob('*.json'))


def test_live_score_candidate_k_and_scope(tmp_path):
    save_prediction(payload(), tmp_path, now='2026-10-24', model_version='test')
    obs = pd.DataFrame({'date': ['2026-11-01'] * 4, 'reward_norm': ['A', 'outside', 'B', 'A'], 'scope': ['all', 'all', '전용', 'all']})
    result = score(tmp_path, tmp_path/'live.json', observations=obs)[0]
    assert result['classifier']['k'] == 1
    assert result['classifier']['k_hit'] == 1
    assert result['classifier']['top5_hits'] == 1
    assert result['classifier']['outside_candidates'] == ['outside']
    assert result['prophet']['k_hit'] == 0


def test_live_score_zero_candidates_is_null(tmp_path):
    save_prediction(payload(), tmp_path, now='2026-10-24', model_version='test')
    obs = pd.DataFrame({'date':['2026-11-01'], 'reward_norm':['outside']})
    result = score(tmp_path, tmp_path/'live.json', observations=obs)[0]
    assert result['classifier']['k_hit'] is None


def test_approve_only_requested_notices(tmp_path):
    path = tmp_path/'official.csv'
    pd.DataFrame({'notice_id':[1,2], 'reward_norm':['A','B'], 'reviewed':[False,False], 'review_method':['','']}).to_csv(path,index=False)
    assert approve([1], 'image_checked', path) == 1
    frame = pd.read_csv(path)
    assert frame.reviewed.tolist() == [True,False]
    assert frame.iloc[0].review_method == 'image_checked'


def test_collect_no_new_does_not_call_vision(tmp_path, monkeypatch):
    from src import weekly
    path = tmp_path/'official.csv'
    pd.DataFrame({'notice_id':[1], 'reward_norm':['A']}).to_csv(path,index=False)
    monkeypatch.setattr(weekly, 'list_sunday_notices', lambda **kwargs: [])
    monkeypatch.setattr(weekly, 'load_env', lambda: pytest.fail('새 공지 없을 때 키를 요구하면 안 됨'))
    assert collect(path) == 0


def test_review_summary_includes_notice_image_and_approval_command():
    from pathlib import Path
    from types import SimpleNamespace
    from src.weekly import notice_review_summary
    notice = SimpleNamespace(id=1405, start_date='2026-10-25', title='썬데이 메이플', url='https://maplestory.nexon.com/News/Event/1405')
    detail = SimpleNamespace(image_urls=['https://lwi.nexon.com/notice.png'], correction_text='200% → 100%')
    rows = pd.DataFrame({'reward_raw':['룬 경험치'], 'reward_norm':['룬_경험치버프'], 'scope':['all']})
    text = '\n'.join(notice_review_summary(notice, detail, [Path('raw.png')], rows))
    assert '1405' in text
    assert '[1](https://lwi.nexon.com/notice.png)' in text
    assert 'python -m src.weekly approve --notice-ids 1405 --review-method image_checked' in text
    assert '자동 머지하지 않습니다' in text


@pytest.mark.parametrize('flag', ['--notice-ids', '--pr-rows'])
def test_approve_notice_ids_alias(monkeypatch, flag):
    from src import weekly
    calls = []
    monkeypatch.setattr(weekly, 'approve', lambda ids, method: calls.append((ids, method)) or 2)
    weekly.main(['approve', flag, '1405', '1406', '--review-method', 'image_checked'])
    assert calls == [([1405,1406], 'image_checked')]


def test_vision_secret_is_scoped_to_collect_step():
    from pathlib import Path
    text = Path('.github/workflows/weekly.yml').read_text(encoding='utf-8')
    assert '    env:\n' not in text.replace('        env:\n', '')
    collect_step = text.split('      - run: python -m src.weekly collect')[1].split('      - name:')[0]
    assert 'VISION_API_KEY: ${{ secrets.VISION_API_KEY }}' in collect_step
    assert text.count('VISION_API_KEY:') == 1
