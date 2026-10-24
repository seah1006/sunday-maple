import base64
import hashlib
import json
import os
from pathlib import Path
import time

import requests

PROMPT = '썬데이 메이플 공지 이미지에서 혜택 블록의 큰 제목 줄만, 이미지에 적힌 그대로 JSON 배열로 반환하세요. 각 항목은 reward_raw 문자열 필드 하나입니다. 설명·주의사항·계산표·버튼 문구는 제외하세요. 정정 텍스트가 주어지면 그 수치를 우선하세요. JSON만 반환하세요.'
PROMPT_VERSION = 'scope_v3'
PROMPT += ' 각 항목에 scope를 추가하세요. 값은 all 또는 혜택 블록에 붙은 전용 라벨 그대로(예: 챌린저스 월드 전용)입니다. ○○ 전용 라벨이 붙은 블록 안의 모든 혜택은 그 라벨을 scope로 쓰세요. 샤이닝 스타포스 타임 같은 스페셜 타임 헤더는 보상 항목이 아니며, 그 아래 실제 혜택 3개만 추출하세요.'
PROMPT += ' 혜택이 속한 블록에 ○○ 타임 헤더가 있으면 각 혜택의 special_time_header에 그 제목을 그대로 넣고, 없으면 null로 쓰세요. 헤더 자체를 reward_raw로 별도 생성하지 마세요.'
PROMPT += ' 예외: 미라클 타임은 인벤 관례상 보상 제목이므로 reward_raw 미라클 타임 한 항목만 추출하고 승급2배 세부 항목들은 별도 보상으로 추출하지 마세요. 선물 지급 블록도 구성품이 아닌 썬데이 메이플 선물 지급 제목 한 항목만 추출하세요.'
_last_call = 0.0


def load_env(path='.env'):
    source = Path(path)
    if source.exists():
        for line in source.read_text(encoding='utf-8-sig').splitlines():
            text = line.strip()
            if not text or text.startswith('#') or '=' not in text:
                continue
            key, value = text.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('\"').strip("'"))
    return bool(os.environ.get('VISION_API_KEY'))


def _gemini(image_bytes, correction_text, model, api_key):
    global _last_call
    images = image_bytes if isinstance(image_bytes, list) else [image_bytes]
    parts = [{'text': PROMPT + '\n이미지는 본문 순서입니다. 모든 이미지의 혜택 제목을 합치세요.\n정정 텍스트: ' + correction_text}]
    parts.extend({'inline_data': {'mime_type': 'image/jpeg' if image.startswith(b'\xff\xd8') else 'image/png', 'data': base64.b64encode(image).decode('ascii')}} for image in images)
    payload = {'contents': [{'parts': parts}], 'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0}}
    parse_failures = 0
    rate_failures = 0
    while True:
        time.sleep(max(0, 5 - (time.monotonic() - _last_call)))
        _last_call = time.monotonic()
        response = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', headers={'x-goog-api-key': api_key}, json=payload, timeout=90)
        if response.status_code == 429 and rate_failures < 3:
            rate_failures += 1
            try:
                delay = float(response.headers.get('Retry-After', 30))
            except ValueError:
                delay = 30
            time.sleep(delay)
            continue
        if not response.ok:
            raise RuntimeError(f'비전 요청 실패: HTTP {response.status_code}')
        body = response.json()
        try:
            text = ''.join(part.get('text', '') for part in body['candidates'][0]['content']['parts'])
            rows = json.loads(text)
            if not isinstance(rows, list) or not all(isinstance(row, dict) and isinstance(row.get('reward_raw'), str) and row['reward_raw'].strip() for row in rows):
                raise ValueError('응답 배열 형식 오류')
            for row in rows:
                row.setdefault('scope', 'all')
                if not isinstance(row['scope'], str) or not row['scope'].strip():
                    raise ValueError('scope 형식 오류')
            return rows, body.get('usageMetadata', {})
        except (ValueError, KeyError, IndexError, TypeError):
            if parse_failures:
                raise ValueError('비전 JSON 응답 파싱 실패') from None
            parse_failures += 1


_ADAPTERS = {'gemini': _gemini}


def extract_rewards(image_bytes, correction_text, *, provider, model, api_key):
    if provider not in _ADAPTERS:
        raise ValueError('지원하지 않는 비전 제공사')
    return _ADAPTERS[provider](image_bytes, correction_text, model, api_key)[0]


def cached_extract_rewards(notice_id, image_bytes, correction_text='', *, provider='gemini', model='gemini-3.5-flash-lite', api_key, cache_dir='data/interim/vision_cache'):
    if provider not in _ADAPTERS:
        raise ValueError('지원하지 않는 비전 제공사')
    root = Path(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f'{notice_id}_{model}_{PROMPT_VERSION}.json'
    images = image_bytes if isinstance(image_bytes, list) else [image_bytes]
    digest = hashlib.sha256(json.dumps([hashlib.sha256(image).hexdigest() for image in images]).encode()).hexdigest()
    if path.exists():
        cached = json.loads(path.read_text(encoding='utf-8'))
        if cached['sha256'] == digest and cached.get('correction_text') == correction_text and cached.get('provider') == provider:
            return cached['rewards']
    rows, usage = _ADAPTERS[provider](image_bytes, correction_text, model, api_key)
    path.write_text(json.dumps({'provider': provider, 'model': model, 'prompt_version': PROMPT_VERSION, 'sha256': digest, 'correction_text': correction_text, 'rewards': rows, 'usage': usage, 'used_image_count': len(images)}, ensure_ascii=False, indent=2), encoding='utf-8')
    return rows
