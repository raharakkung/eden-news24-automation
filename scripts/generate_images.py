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
# 실존 인물 초상권/명예훼손 리스크를 피하기 위해 모든 프롬프트에 "no real celebrity,
# generic anonymous person, no identifiable face"를 포함해 특정인을 닮은 얼굴이
# 생성되지 않도록 한다.
CATEGORY_PROMPTS = {
    "이슈": [
        "trendy Korean cafe with young people chatting, lifestyle photography, no identifiable face, no text",
        "smartphone showing a blurred social media app, trending topic concept, no text, no logos",
        "crowded Seoul street with shopping bags, lifestyle photography, no identifiable face, no text",
        "close-up of a trendy product on a minimal background, editorial photography, no text, no logos",
        "person scrolling on a phone at a cafe table, generic anonymous person, no identifiable face, no text",
    ],
    "연예": [
        "concert stage with colorful lights, no identifiable face, no real celebrity, no text, no logos",
        "fans holding lightsticks at a concert, silhouettes only, no identifiable face, no text",
        "modern TV studio set with bright lights, no identifiable face, no text, no logos",
        "vinyl records and headphones on a table, music lifestyle photography, no text",
        "theater or cinema seats in dim lighting, no identifiable face, no text",
    ],
    "스포츠": [
        "empty modern stadium with bright lights, sports photography, no identifiable face, no text",
        "running shoes and a track field, sports lifestyle photography, no identifiable face, no text",
        "soccer ball on a green pitch, bright daylight, no identifiable face, no text, no logos",
        "gym equipment in a bright modern fitness center, no identifiable face, no text, no logos",
        "person stretching before a run outdoors, generic anonymous person, no identifiable face, no text",
    ],
    "라이프": [
        "cozy Korean apartment living room, tidy and organized, bright daylight, no text",
        "hands using a cleaning spray in a kitchen, lifestyle photo, no identifiable face, no text",
        "home cafe setup with coffee and pastries, bright natural light, no text, no logos",
        "neatly organized closet with folded clothes, clean lifestyle photography, no text",
        "cozy bedroom with soft morning light, peaceful lifestyle concept, no text",
    ],
    "유용한정보": [
        "modern government office building exterior, bright daylight, no text",
        "calculator and documents on a desk, finance concept, clean editorial photography, no text",
        "stack of paperwork and a pen on a wooden desk, bright natural light, no text",
        "piggy bank and coins on a table, savings concept, clean minimal style, no text",
        "hands holding a smartphone with a blurred banking app, no identifiable face, no text",
    ],
    "유용한법률": [
        "stack of official documents and a pen on a desk, clean editorial style, no text",
        "modern courthouse building exterior, bright daylight, no text",
        "hands signing a document, close-up, warm natural light, no identifiable face, no text",
        "folder of paperwork on an office desk, clean minimal style, no text",
        "gavel and law books on a wooden desk, soft lighting, no text",
    ],
    "동물뉴스": [
        "cute fluffy dog sitting in a bright living room, pet photography, no text, no logos",
        "curious cat looking out a window, soft natural light, pet photography, no text",
        "dog and owner walking in a park, generic anonymous person, no identifiable face, no text",
        "cozy pet bed with a sleeping cat, warm lighting, no text, no logos",
        "veterinary clinic exterior or pet supplies on a table, clean editorial style, no text",
    ],
}

DEFAULT_PROMPTS = CATEGORY_PROMPTS["라이프"]


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
        alt = f"{topic} / 사진=이든뉴스 자료사진"
        results.append((url, alt))
        time.sleep(1)  # 무료 서비스에 대한 매너 딜레이
    return results


if __name__ == "__main__":
    imgs = generate_images_for_article("생활정보", "변기 막힘 뚫는 법", count=2)
    print(f"생성된 이미지 수: {len(imgs)}")
    for url, alt in imgs:
        print(alt, "|", url)
