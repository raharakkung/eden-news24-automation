"""Pollinations.ai(완전 무료, API 키 불필요)로 기사용 이미지를 생성한다.

이미지는 base64로 본문에 직접 삽입하지 않고, Pollinations의 외부 URL을 그대로
<img src=""/>로 참조한다. base64 삽입은 글 하나당 본문 용량이 180~200KB까지 커져
Blogger가 홈/검색 등 여러 글을 한 번에 보여주는 페이지에서 응답 크기 제한에 걸려
글이 1~2개만 보이고 잘려나가는 문제를 일으켰다(2026-10-17 확인)."""
import random
import time
import urllib.parse

import requests

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"

# 카테고리별 범용 이미지 프롬프트(영문). 특정 글의 정확한 내용 대신
# 카테고리 분위기에 맞는 편집 사진 스타일 이미지를 생성한다.
CATEGORY_PROMPTS = {
    "생활정보": [
        "clean bright modern home interior, cleaning supplies, lifestyle photography, no text, no people",
        "close-up of household cleaning tools, soft natural light, editorial photography style, no text",
        "cozy Korean apartment living room, tidy and organized, bright daylight, no text",
        "hands using a cleaning spray in a kitchen, lifestyle photo, no faces, no text",
        "fresh clean bathroom with white tiles, bright natural light, no text",
    ],
    "IT/디지털": [
        "modern smartphone on a wooden desk, soft lighting, tech lifestyle photography, no text",
        "laptop computer on a desk in a cozy home office, no text, no logos",
        "close-up of hands typing on a laptop keyboard, warm lighting, no text",
        "wifi router and tech gadgets on a desk, clean minimal style, no text",
        "modern desk setup with monitor and smartphone, tech lifestyle, no faces, no text",
    ],
    "건강": [
        "person stretching in a bright living room, healthy lifestyle photography, no face, no text",
        "bowl of healthy fresh food on a wooden table, bright natural light, no text",
        "cozy bedroom with soft morning light, peaceful sleep concept, no text",
        "glass of water and vitamins on a table, clean minimal health concept, no text",
        "yoga mat and stretching scene in a bright room, wellness lifestyle, no face, no text",
    ],
    "금융/정부지원": [
        "modern government office building exterior, bright daylight, no text",
        "calculator and documents on a desk, finance concept, clean editorial photography, no text",
        "stack of paperwork and a pen on a wooden desk, bright natural light, no text",
        "piggy bank and coins on a table, savings concept, clean minimal style, no text",
        "hands holding a smartphone with a blurred banking app, finance lifestyle, no text",
    ],
    "법률/행정": [
        "stack of official documents and a pen on a desk, clean editorial style, no text",
        "modern courthouse building exterior, bright daylight, no text",
        "hands signing a document, close-up, warm natural light, no faces, no text",
        "folder of paperwork on an office desk, clean minimal style, no text",
        "gavel and law books on a wooden desk, soft lighting, no text",
    ],
    "자동차": [
        "modern car dashboard interior, clean photography, no text, no logos",
        "close-up of a car tire and wheel, bright daylight, editorial photography, no text",
        "car engine bay, clean detailed photography, no text, no logos",
        "hands holding car keys next to a parked car, bright daylight, no faces, no text",
        "car parked in a clean modern garage, soft lighting, no text, no logos",
    ],
    "쇼핑/생활꿀팁": [
        "cardboard delivery boxes stacked at a front door, bright daylight, no text, no logos",
        "hands holding a smartphone with a blurred shopping app, lifestyle photo, no text",
        "neatly wrapped packages on a table, clean lifestyle photography, no text, no logos",
        "credit card and shopping bags on a table, clean minimal style, no text, no logos",
        "cozy living room with a delivery package on the floor, bright natural light, no text",
    ],
    "교육/취업": [
        "laptop and notebook on a desk, study concept, bright natural light, no text",
        "resume papers and a pen on a wooden desk, clean editorial photography, no text",
        "modern office meeting room, bright daylight, no people, no text",
        "stack of books and a coffee cup on a desk, study lifestyle photography, no text",
        "hands writing notes in a notebook, warm natural light, no face, no text",
    ],
}

DEFAULT_PROMPTS = CATEGORY_PROMPTS["생활정보"]


def _build_url(prompt, seed):
    url = POLLINATIONS_BASE + urllib.parse.quote(prompt)
    return url + f"?nologo=true&seed={seed}&width=800"


def _verify_one(url, retries=5):
    """URL이 실제로 이미지를 서빙하는지 한 번 확인한다(생성은 이미 이 요청에서 캐시됨)."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image"):
                return True
            print(f"    (시도 {attempt + 1}/{retries}) 상태 코드 {resp.status_code}, 재시도...")
        except requests.RequestException as exc:
            print(f"    (시도 {attempt + 1}/{retries}) 네트워크 오류: {exc}, 재시도...")
        time.sleep(8 * (attempt + 1))
    return False


def generate_images_for_article(category, topic, count=4):
    """(image_url, alt_text) 튜플 리스트를 반환한다. 생성 실패한 이미지는 건너뛴다."""
    prompts = CATEGORY_PROMPTS.get(category, DEFAULT_PROMPTS)
    chosen = random.sample(prompts, k=min(count, len(prompts)))
    while len(chosen) < count:
        chosen.append(random.choice(prompts))

    results = []
    for i, prompt in enumerate(chosen):
        seed = random.randint(1, 1_000_000)
        url = _build_url(prompt, seed)
        if not _verify_one(url):
            print(f"  [이미지 {i+1}] 생성 실패, 건너뜀")
            continue
        alt = f"{topic} 관련 이미지 {i + 1}"
        results.append((url, alt))
        time.sleep(1)  # 무료 서비스에 대한 매너 딜레이
    return results


if __name__ == "__main__":
    imgs = generate_images_for_article("생활정보", "변기 막힘 뚫는 법", count=2)
    print(f"생성된 이미지 수: {len(imgs)}")
    for url, alt in imgs:
        print(alt, "|", url)
