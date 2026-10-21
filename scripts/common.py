"""공용 유틸리티: 설정 파일 로딩, 사용한 주제 상태 관리."""
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_CONFIG_PATH = os.path.join(ROOT, "config", "site.json")
TOPICS_PATH = os.path.join(ROOT, "config", "topics.json")
USED_TOPICS_PATH = os.path.join(ROOT, "data", "used_topics.json")
CATEGORY_CURSOR_PATH = os.path.join(ROOT, "data", "category_cursor.json")


def load_site_config():
    with open(SITE_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_topics():
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_used_topics():
    if not os.path.exists(USED_TOPICS_PATH):
        return []
    with open(USED_TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_used_topics(used):
    os.makedirs(os.path.dirname(USED_TOPICS_PATH), exist_ok=True)
    with open(USED_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def load_category_cursor():
    """다음 실행에서 어느 카테고리부터 이어갈지 기억하는 커서(인덱스)를 읽는다."""
    if not os.path.exists(CATEGORY_CURSOR_PATH):
        return 0
    with open(CATEGORY_CURSOR_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("next_index", 0)


def save_category_cursor(next_index):
    os.makedirs(os.path.dirname(CATEGORY_CURSOR_PATH), exist_ok=True)
    with open(CATEGORY_CURSOR_PATH, "w", encoding="utf-8") as f:
        json.dump({"next_index": next_index}, f, ensure_ascii=False, indent=2)


def pick_next_topics(count):
    """카테고리를 순서대로 하나씩 순환하며 주제를 count개 고른다.

    실행할 때마다 카테고리 인덱스를 0부터 다시 시작하지 않고, 지난 실행이
    멈춘 지점(category_cursor.json)부터 이어간다. 예: 카테고리가 8개이고
    하루 2개씩 발행하면 1일차 생활정보+IT/디지털, 2일차 건강+금융/정부지원,
    3일차 법률/행정+자동차, 4일차 쇼핑/생활꿀팁+교육/취업, 5일차부터 다시 처음.

    한 카테고리의 주제를 모두 썼다면 그 카테고리의 사용 기록만 초기화해서
    다시 돈다(다른 카테고리의 사용 기록은 유지).
    """
    topics_by_category = load_topics()
    used = set(load_used_topics())
    categories = list(topics_by_category.keys())
    cursor = load_category_cursor() % len(categories)

    picked = []
    for i in range(count):
        category = categories[(cursor + i) % len(categories)]

        candidates = [t for t in topics_by_category[category] if f"{category}::{t}" not in used]
        if not candidates:
            # 이 카테고리의 주제를 모두 사용함: 이 카테고리만 사용 기록 초기화
            used = {u for u in used if not u.startswith(f"{category}::")}
            candidates = topics_by_category[category]

        topic = candidates[0]
        picked.append({"category": category, "topic": topic})
        used.add(f"{category}::{topic}")

    next_cursor = (cursor + count) % len(categories)
    return picked, used, next_cursor


def resolve_category(labels, site):
    """Blogger API는 라벨 순서를 알파벳순 등으로 재배열해서 돌려주므로,
    labels[0]이 아니라 known 카테고리 중 하나가 포함돼 있는지로 찾는다."""
    known = site.get("categories", [])
    for label in labels or []:
        if label in known:
            return label
    return known[0] if known else "생활정보"


def _image_tag(image_url, alt):
    """image_url: 외부 이미지 URL(예: Pollinations.ai). base64로 본문에 직접 삽입하면
    글 용량이 커져 Blogger의 다중 게시물 페이지(홈/검색)에서 응답 크기 제한에 걸려
    글이 잘려나가는 문제가 있어(2026-10-17 확인), 반드시 외부 URL 참조 방식을 사용한다.
    alt 텍스트는 "{키워드} / 사진=출처" 형태라고 가정하고, 그대로 이미지 아래 작은
    캡션으로도 노출한다(국내 뉴스 매체의 사진 캡션 관행을 따름)."""
    safe_alt = alt.replace('"', "'")
    return (
        f'<img src="{image_url}" alt="{safe_alt}" '
        'style="max-width:100%;height:auto;border-radius:8px;margin:16px 0 4px 0;" loading="lazy"/>'
        f'<p style="font-size:12px;color:#888;margin:0 0 16px 0;">{safe_alt}</p>'
    )


H2_OPEN_RE = re.compile(r"<h2\b[^>]*>")
P_CLOSE_RE = re.compile(r"</p>")


def insert_images_into_html(html, images):
    """images: [(image_url, alt_text), ...]. <h2> 소제목(속성이 붙어 있어도 매치)
    앞마다 이미지를 하나씩 배치한다. 소제목 수보다 이미지가 많으면, 남는 이미지는
    본문 뒷부분(마지막 소제목 이후)의 </p> 문단 경계에 고르게 분산 배치해서 한곳에
    몰리지 않게 한다. 이미지가 없으면 원본 html을 그대로 반환한다."""
    if not images:
        return html

    images = list(images)
    h2_starts = [m.start() for m in H2_OPEN_RE.finditer(html)]

    anchors = h2_starts[: len(images)]

    need = len(images) - len(anchors)
    if need > 0:
        search_from = h2_starts[0] if h2_starts else 0
        p_ends = [m.end() for m in P_CLOSE_RE.finditer(html) if m.end() > search_from]
        if p_ends:
            step = max(1, len(p_ends) // (need + 1))
            idx = step - 1
            while len(anchors) < len(images) and idx < len(p_ends):
                pos = p_ends[idx]
                if pos not in anchors:
                    anchors.append(pos)
                idx += step
            # 그래도 자리가 부족하면 남은 문단 경계를 끝에서부터 채운다
            for pos in reversed(p_ends):
                if len(anchors) >= len(images):
                    break
                if pos not in anchors:
                    anchors.append(pos)

    pairs = list(zip(sorted(set(anchors)), images))

    result = html
    for pos, (url, alt) in sorted(pairs, key=lambda item: -item[0]):
        result = result[:pos] + _image_tag(url, alt) + "\n" + result[pos:]

    if len(pairs) < len(images):
        remaining_imgs = images[len(pairs):]
        result += "".join(_image_tag(url, alt) for url, alt in remaining_imgs)

    return result


BYLINE_MARKER = 'class="kn-byline"'
BYLINE_BLOCK_RE = re.compile(r'<p[^>]*class="kn-byline"[^>]*>.*?</p>\s*', re.DOTALL)


def pick_reporter(site):
    """기사마다 담당 기자를 무작위로 배정한다(카테고리 고정 아님)."""
    reporters = site.get("reporters", [])
    if not reporters:
        return {"name": "편집팀", "email": ""}
    return random.choice(reporters)


def build_byline_html(reporter, site):
    """신문 기사처럼 [매체명] 기자명 기자 | 이메일 형태의 바이라인을 만든다."""
    site_name = site.get("site_name", "라하뉴스")
    name = reporter.get("name", "편집팀")
    email = reporter.get("email", "")
    email_part = f' | <a href="mailto:{email}">{email}</a>' if email else ""
    return (
        f'<p {BYLINE_MARKER} style="color:#666;font-size:14px;margin:0 0 20px 0;">'
        f"[{site_name}] {name} 기자{email_part}</p>"
    )


def has_byline(html):
    return BYLINE_MARKER in html


def strip_byline(html):
    return BYLINE_BLOCK_RE.sub("", html, count=1)


def add_byline(html, reporter, site):
    """이미 바이라인이 있으면 그대로 두고, 없으면 맨 앞에 추가한다(새 글 발행용)."""
    if has_byline(html):
        return html
    return build_byline_html(reporter, site) + "\n" + html


def set_byline(html, reporter, site):
    """기존 바이라인이 있으면 제거하고 새 기자 정보로 교체한다(기존 글 수정용)."""
    html = strip_byline(html)
    return build_byline_html(reporter, site) + "\n" + html
