from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from src.collect import DEFAULT_USER_AGENT

BASE_URL = 'https://maplestory.nexon.com'
_responses = {}
_robots = {}
_last_request = 0.0
_linked_images = set()
_image_robots_status = {}
_image_unavailable = set()


@dataclass
class Notice:
    id: int
    title: str
    start_date: str
    end_date: str
    is_special: bool
    url: str


@dataclass
class NoticeDetail:
    notice: Notice
    image_urls: list[str]
    correction_text: str
    skipped_image_uris_count: int = 0


def _request(url, *, image=False):
    global _last_request
    parsed_url = urlsplit(url)
    if parsed_url.scheme != "https" or parsed_url.username or parsed_url.password:
        raise PermissionError("허용되지 않은 요청 URI")
    if url in _responses:
        return _responses[url]
    if image and url not in _linked_images:
        raise PermissionError("허용된 공식 공지에 연결되지 않은 이미지")
    origin = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
    if origin not in _robots:
        time.sleep(max(0, 1 - (time.monotonic() - _last_request)))
        _last_request = time.monotonic()
        response = requests.get(origin + '/robots.txt', headers={'User-Agent': DEFAULT_USER_AGENT}, timeout=30)
        if image:
            _image_robots_status[origin] = response.status_code
        if image and 400 <= response.status_code < 500:
            _image_unavailable.add(origin)
            robot = RobotFileParser()
            robot.parse([])
        else:
            response.raise_for_status()
            robot = RobotFileParser()
            robot.parse(response.text.splitlines())
        _robots[origin] = robot
    if origin in _image_unavailable and not image:
        raise PermissionError("이미지 외 경로에 robots 예외 적용 불가")
    if not _robots[origin].can_fetch(DEFAULT_USER_AGENT, url):
        raise PermissionError('robots.txt 수집 제한')
    time.sleep(max(0, 1 - (time.monotonic() - _last_request)))
    _last_request = time.monotonic()
    response = requests.get(url, headers={'User-Agent': DEFAULT_USER_AGENT}, timeout=30)
    response.raise_for_status()
    _responses[url] = response
    return response


def parse_notice_list(html):
    soup = BeautifulSoup(html, 'lxml')
    notices = {}
    for anchor in soup.select('a[href]'):
        match = re.search(r'/News/Event/(?:Closed/)?(\d+)', anchor['href'])
        title = anchor.get_text(' ', strip=True)
        if not match or '썬데이' not in title:
            continue
        container = anchor.find_parent('dl') or anchor.parent
        period = re.search(r'(\d{4}\.\d{2}\.\d{2})[^~]*~\s*(\d{4}\.\d{2}\.\d{2})', container.get_text(' ', strip=True))
        if period:
            notice_id = int(match[1])
            notices[notice_id] = Notice(notice_id, title, period[1].replace('.', '-'), period[2].replace('.', '-'), '스페셜' in title, f'{BASE_URL}/News/Event/{notice_id}')
    return list(notices.values())


def list_sunday_notices(max_pages=10, oldest_id=1300):
    notices = {}
    for page in range(1, max_pages + 1):
        url = f'{BASE_URL}/News/Event/Closed?searchKeyword=%EC%8D%AC%EB%8D%B0%EC%9D%B4&page={page}'
        batch = parse_notice_list(_request(url).content)
        for notice in batch:
            if notice.id >= oldest_id:
                notices[notice.id] = notice
        if not batch or any(notice.id < oldest_id for notice in batch):
            break
    return sorted(notices.values(), key=lambda n: n.start_date, reverse=True)


def parse_notice_detail(notice, html):
    body = BeautifulSoup(html, 'lxml').select_one('.new_board_con')
    if body is None:
        raise ValueError('공식 공지 본문을 찾을 수 없음')
    linked = [urljoin(notice.url, image['src']) for image in body.select('img[src]')]
    images = list(dict.fromkeys(url for url in linked if urlsplit(url).scheme == 'https' and urlsplit(url).hostname == 'lwi.nexon.com' and not urlsplit(url).username and not urlsplit(url).password and urlsplit(url).path.lower().endswith(('.png', '.jpg', '.jpeg'))))
    skipped = sum(1 for url in linked if url not in images)
    for element in body.select('.b_srch, style, script'):
        element.decompose()
    return NoticeDetail(notice, images, body.get_text(' ', strip=True), skipped)


def fetch_notice(notice):
    if urlsplit(notice.url).hostname != 'maplestory.nexon.com':
        raise PermissionError('공식 공지 호스트가 아님')
    detail = parse_notice_detail(notice, _request(notice.url).content)
    _linked_images.update(detail.image_urls)
    return detail


def save_notice_raw(detail, out_dir='data/raw/official'):
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for index, image_url in enumerate(detail.image_urls):
        suffix = '' if index == 0 else f'_{index + 1}'
        stem = f'{detail.notice.start_date}_{detail.notice.id}{suffix}'
        image = root / f'{stem}.png'
        meta_path = root / f'{stem}_meta.json'
        if image.exists():
            if not meta_path.exists():
                raise FileExistsError('이미지의 원본 메타가 없음')
            results.append(meta_path)
            continue
        try:
            content = _request(image_url, image=True).content
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else None
            if status not in (403, 404):
                raise
            failure = {**asdict(detail.notice), 'image_url': image_url, 'download_status': status, 'skipped_image_uris_count': detail.skipped_image_uris_count, 'used_image_count': 0}
            if not meta_path.exists():
                meta_path.write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding='utf-8')
            continue
        meta = {**asdict(detail.notice), 'period': [detail.notice.start_date, detail.notice.end_date], 'image_url': image_url, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'correction_text': detail.correction_text, 'sha256': hashlib.sha256(content).hexdigest(), 'skipped_image_uris_count': detail.skipped_image_uris_count, 'used_image_count': len(detail.image_urls)}
        origin = '{0.scheme}://{0.netloc}'.format(urlsplit(image_url))
        meta['image_robots_status'] = _image_robots_status.get(origin)
        meta['image_robots_policy'] = 'rfc9309_4xx_unavailable' if origin in _image_unavailable else 'robots_allowed'
        with image.open('xb') as stream:
            stream.write(content)
        with meta_path.open('x', encoding='utf-8') as stream:
            json.dump(meta, stream, ensure_ascii=False, indent=2)
        results.append(meta_path)
    return results
