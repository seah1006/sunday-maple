import json
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from src.official import Notice, parse_notice_list, parse_notice_detail, save_notice_raw
from src.official_observations import store_extracted, load_reviewed_observations
from src import vision

FIXTURES = Path('tests/fixtures/official')


def test_actual_official_fixtures():
    notices = parse_notice_list((FIXTURES / 'list.html').read_text(encoding='utf-8'))
    assert notices
    notice = next(n for n in notices if n.id == 1405)
    assert notice.start_date == '2026-10-25'
    detail = parse_notice_detail(notice, (FIXTURES / 'detail.html').read_text(encoding='utf-8'))
    assert len(detail.image_urls) == 1
    assert '(후) 100%' in detail.correction_text
    assert '이벤트 기간' not in detail.correction_text


def test_raw_is_immutable(tmp_path, monkeypatch):
    from src import official
    notice = Notice(1, '썬데이', '2026-06-14', '2026-06-14', False, 'https://example.com')
    detail = official.NoticeDetail(notice, ['https://example.com/a.png'], '')
    request = Mock(return_value=Mock(content=b'image'))
    monkeypatch.setattr(official, '_request', request)
    save_notice_raw(detail, tmp_path)
    save_notice_raw(detail, tmp_path)
    assert request.call_count == 1
    assert (tmp_path / '2026-06-14_1.png').read_bytes() == b'image'


def response(text, status=200):
    return Mock(status_code=status, ok=status==200, headers={'Retry-After':'0'}, json=lambda: {'candidates':[{'content':{'parts':[{'text':text}]}}], 'usageMetadata':{'promptTokenCount':10,'candidatesTokenCount':5}})


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(vision.time, 'sleep', lambda seconds: None)
    post = Mock(return_value=response('[{"reward_raw":"몬스터파크 클리어 경험치 추가 250%"}]'))
    monkeypatch.setattr(vision.requests, 'post', post)
    return post


def test_gemini_request_and_cache(api, tmp_path):
    options = {'api_key':'test-only', 'model':'gemini-3.5-flash-lite', 'cache_dir':tmp_path}
    rows = vision.cached_extract_rewards(1, b'image', '정정100%', **options)
    assert rows[0]['reward_raw'].startswith('몬스터파크')
    assert vision.cached_extract_rewards(1, b'image', '정정100%', **options) == rows
    assert api.call_count == 1
    body = api.call_args.kwargs['json']
    assert body['generationConfig']['responseMimeType'] == 'application/json'
    assert '정정100%' in body['contents'][0]['parts'][0]['text']
    assert body['contents'][0]['parts'][1]['inline_data']['data'] == 'aW1hZ2U='
    assert json.loads(next(tmp_path.glob('*.json')).read_text(encoding='utf-8'))['usage']['promptTokenCount'] == 10


def test_gemini_parse_retry(api):
    api.side_effect = [response('not json'), response('[]')]
    assert vision.extract_rewards(b'x', '', provider='gemini', model='test', api_key='test-only') == []
    assert api.call_count == 2


def test_gemini_429_retry(api):
    api.side_effect = [response('',429), response('[]')]
    assert vision.extract_rewards(b'x', '', provider='gemini', model='test', api_key='test-only') == []
    assert api.call_count == 2


def test_gemini_retry_limits(api):
    api.return_value = response('',429)
    with pytest.raises(RuntimeError):
        vision.extract_rewards(b'x','',provider='gemini',model='test',api_key='test-only')
    assert api.call_count == 4


def test_observations_review_priority_and_unmapped(tmp_path):
    notice = Notice(1,'스페셜 썬데이','2026-06-14','2026-06-14',True,'https://example.com')
    store_extracted(notice,[{'reward_raw':'정체불명 보상'}],provider='gemini',model='test',out_dir=tmp_path)
    assert (tmp_path/'unmapped.csv').exists()
    manual = tmp_path/'manual.csv'
    pd.DataFrame({'date':['2026-06-14'],'reward_norm':['수동']}).to_csv(manual,index=False)
    assert load_reviewed_observations(manual,tmp_path/'official.csv').iloc[0].reward_norm == '수동'
    official = pd.read_csv(tmp_path/'official.csv')
    official['reward_norm']='공식';official['reviewed']=True
    official.to_csv(tmp_path/'official.csv',index=False)
    merged=load_reviewed_observations(manual,tmp_path/'official.csv')
    assert len(merged)==1
    assert merged.iloc[0].reward_norm=='공식'
    assert merged.iloc[0].is_special


def test_empty_env_key_is_missing(tmp_path, monkeypatch):
    monkeypatch.delenv('VISION_API_KEY', raising=False)
    path = tmp_path / '.env'
    path.write_text('VISION_PROVIDER=gemini\nVISION_API_KEY=\n', encoding='utf-8')
    assert not vision.load_env(path)


def test_env_does_not_override_process(tmp_path, monkeypatch):
    monkeypatch.setenv('VISION_API_KEY', 'test-process-only')
    path = tmp_path / '.env'
    path.write_text('VISION_API_KEY=test-file-only\n', encoding='utf-8')
    assert vision.load_env(path)
    assert vision.os.environ['VISION_API_KEY'] == 'test-process-only'


@pytest.mark.parametrize('status', [403, 404])
def test_linked_image_robots_4xx_allowed(monkeypatch, status):
    from src import official
    url = 'https://images.example.com/notice.png'
    monkeypatch.setattr(official, '_responses', {})
    monkeypatch.setattr(official, '_robots', {})
    monkeypatch.setattr(official, '_linked_images', {url})
    monkeypatch.setattr(official, '_image_robots_status', {})
    monkeypatch.setattr(official, '_image_unavailable', set())
    monkeypatch.setattr(official.time, 'sleep', lambda seconds: None)
    robot = Mock(status_code=status)
    image = Mock(content=b'image')
    image.raise_for_status = Mock()
    get = Mock(side_effect=[robot, image])
    monkeypatch.setattr(official.requests, 'get', get)
    assert official._request(url, image=True).content == b'image'
    assert official._image_robots_status['https://images.example.com'] == status
    assert get.call_count == 2
    with pytest.raises(PermissionError):
        official._request('https://images.example.com/other.png', image=True)


def test_image_robots_5xx_denied(monkeypatch):
    from src import official
    url = 'https://images.example.com/notice.png'
    monkeypatch.setattr(official, '_responses', {})
    monkeypatch.setattr(official, '_robots', {})
    monkeypatch.setattr(official, '_linked_images', {url})
    monkeypatch.setattr(official.time, 'sleep', lambda seconds: None)
    robot = Mock(status_code=503)
    robot.raise_for_status.side_effect = RuntimeError('unreachable')
    get = Mock(return_value=robot)
    monkeypatch.setattr(official.requests, 'get', get)
    with pytest.raises(RuntimeError):
        official._request(url, image=True)
    assert get.call_count == 1


def test_static_image_allowlist():
    notice = Notice(1, '썬데이', '2026-06-14', '2026-06-14', False, 'https://maplestory.nexon.com/News/Event/1')
    detail = parse_notice_detail(notice, '<div class="new_board_con"><img src="https://lwi.nexon.com/a.png"><img src="https://lwi.nexon.com/b.jpg"><img src="https://lwi.nexon.com/c.gif"><img src="https://other.example.com/d.png"></div>')
    assert detail.image_urls == ['https://lwi.nexon.com/a.png', 'https://lwi.nexon.com/b.jpg']
    assert detail.skipped_image_uris_count == 2


def test_multi_image_single_request(api):
    vision.extract_rewards([b'png', b'\xff\xd8jpeg'], '', provider='gemini', model='test', api_key='test-only')
    parts = api.call_args.kwargs['json']['contents'][0]['parts']
    assert len(parts) == 3
    assert parts[2]['inline_data']['mime_type'] == 'image/jpeg'
    assert api.call_count == 1


@pytest.mark.parametrize('raw, norm', [
    ('룬 재 등장 및 재사용 대기시간 감소', '룬_재등장감소'),
    ('몬스터파크 클리어 경험치 추가 250%', '몬스터파크_경험치'),
    ('트레저 헌터 경험치 3배', '트레져헌터_경험치'),
    ('썬데이 메이플 선물 지급', '선물_기타지급'),
    ('어빌리티 재설정 명성치 비용 50% 할인', '어빌리티_재설정할인'),
    ('룬 기본 지속시간 50% 증가', '룬_지속시간증가'),
    ('룬 경험치 버프 지속시간 2배', '룬_경험치버프'),
    ('잠재능력, 에디셔널 잠재능력 재설정 시 등급이 승급될 확률 2배!', '미라클타임'),
])
def test_official_wording_aliases(raw, norm):
    from src.normalize import normalize_reward
    assert normalize_reward(raw) == norm


def test_scope_header_does_not_mark_whole_world_special(tmp_path):
    notice = Notice(10, '썬데이 메이플', '2026-06-14', '2026-06-14', False, 'https://example.com')
    rows = store_extracted(notice, [{'reward_raw':'스타포스 강화 비용 30% 할인','scope':'챌린저스 월드 전용','special_time_header':'샤이닝 스타포스 타임'}], provider='gemini', model='test', out_dir=tmp_path)
    assert not rows.iloc[0].is_special
    assert rows.iloc[0].scope == '챌린저스 월드 전용'
    assert 'special_time_header: 샤이닝 스타포스 타임' in rows.iloc[0].note
