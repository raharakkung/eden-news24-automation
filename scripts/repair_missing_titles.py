"""title/labels가 비어버린 글(배포 스크립트의 posts().update() 버그로 인한 손상)을
기존 본문(content)만 가지고 복구하는 1회성 스크립트.

복구 방법 (Gemini 등 외부 API 호출 없이, 본문 안의 정보만 사용):
- 제목: 본문의 첫 <h2> 소제목 텍스트를 사용 (없으면 첫 문단 일부)
- 카테고리: 본문 텍스트에 등장하는 카테고리별 연관 키워드 빈도로 추정
"""
import os
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import load_site_config

CATEGORY_KEYWORDS = {
    "IT/디지털": ["스마트폰", "휴대폰", "와이파이", "컴퓨터", "노트북", "앱", "App", "메신저", "카카오톡",
                  "데이터", "인터넷", "와이파이", "충전", "usb", "pc", "핸드폰", "갤럭시", "아이폰", "계정"],
    "건강": ["건강", "병원", "증상", "통증", "다이어트", "수면", "운동", "영양", "질환", "병원비",
             "스트레스", "면역", "두통", "혈압", "검진"],
    "금융/정부지원": ["지원금", "대출", "세금", "환급", "보험료", "연금", "적금", "신용", "카드",
                      "정부지원", "복지", "수당", "국민연금", "건강보험", "연말정산"],
    "법률/행정": ["법률", "계약", "소송", "주민센터", "서류", "등본", "신고", "과태료", "변호사",
                  "소비자", "분쟁", "행정", "민원"],
    "자동차": ["자동차", "차량", "주행", "타이어", "엔진", "자동차보험", "운전", "주차", "세차", "연비"],
    "쇼핑/생활꿀팁": ["쇼핑", "할인", "꿀팁", "구매", "배송", "반품", "교환", "특가", "쿠폰"],
    "교육/취업": ["교육", "취업", "이력서", "면접", "자격증", "학자금", "공부", "대학", "입시", "채용"],
    "생활정보": ["생활", "청소", "빨래", "세탁", "곰팡이", "냄새", "수납", "정리", "관리비", "분리수거"],
}

BYLINE_RE = re.compile(r'<p[^>]*class="kn-byline"[^>]*>.*?</p>\s*', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(html):
    return TAG_RE.sub("", html).strip()


def guess_title(content_no_byline):
    h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", content_no_byline, re.DOTALL)
    if h2_match:
        title = strip_tags(h2_match.group(1)).strip()
        if title:
            return title

    p_match = re.search(r"<p[^>]*>(.*?)</p>", content_no_byline, re.DOTALL)
    if p_match:
        text = strip_tags(p_match.group(1)).strip()
        if text:
            return text[:40]

    return "생활 정보 안내"


def guess_category(plain_text):
    best_cat, best_score = None, 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(plain_text.count(kw) for kw in keywords)
        if score > best_score:
            best_cat, best_score = cat, score
    return best_cat or "생활정보"


def get_blogger_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    return build("blogger", "v3", credentials=creds)


def main():
    site = load_site_config()
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    service = get_blogger_service()

    all_items = []
    req = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True)
    while req is not None:
        resp = req.execute()
        all_items.extend(resp.get("items", []))
        req = service.posts().list_next(req, resp)

    print(f"총 {len(all_items)}개 글 확인\n")

    fixed = 0
    for post in all_items:
        title = (post.get("title") or "").strip()
        if title:
            continue

        content = post["content"]
        content_no_byline = BYLINE_RE.sub("", content, count=1)
        plain_text = strip_tags(content_no_byline)

        new_title = guess_title(content_no_byline)
        category = guess_category(plain_text)
        new_labels = [category]

        print(f"[복구] id={post['id']} url={post.get('url')}")
        print(f"  -> 제목: {new_title}")
        print(f"  -> 카테고리: {category}")

        service.posts().update(
            blogId=blog_id,
            postId=post["id"],
            body={"title": new_title, "labels": new_labels, "content": content},
        ).execute()
        fixed += 1

    print(f"\n총 {fixed}개 글 복구 완료.")


if __name__ == "__main__":
    main()
