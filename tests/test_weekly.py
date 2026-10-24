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
