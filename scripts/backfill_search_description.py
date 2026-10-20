"""기존에 발행된 글에 검색 설명(searchDescription, meta description)이 비어있는
경우 본문에서 자연스러운 요약 문장을 추출해 채워 넣는 1회성 스크립트.

Gemini 등 외부 API를 호출하지 않고 본문의 첫 문단 텍스트만 사용한다
(repair_missing_titles.py와 같은 방식)."""
import os
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BYLINE_RE = re.compile(r'<p[^>]*class="kn-byline"[^>]*>.*?</p>\s*', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
MAX_LEN = 150


def strip_tags(html):
    return TAG_RE.sub("", html).strip()


def guess_description(content):
    content_no_byline = BYLINE_RE.sub("", content, count=1)
    p_match = re.search(r"<p[^>]*>(.*?)</p>", content_no_byline, re.DOTALL)
    if not p_match:
        return None
    text = strip_tags(p_match.group(1)).strip()
    if not text:
        return None
    if len(text) <= MAX_LEN:
        return text
    return text[:MAX_LEN].rsplit(" ", 1)[0] + "..."


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
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    service = get_blogger_service()

    posts = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True).execute()
    items = posts.get("items", [])
    print(f"총 {len(items)}개 글 확인\n")

    for post in items:
        existing = (post.get("searchDescription") or "").strip()
        if existing:
            print(f"[건너뜀] 이미 검색 설명 있음: {post['title'][:30]}")
            continue

        desc = guess_description(post["content"])
        if not desc:
            print(f"[실패] 설명 추출 불가: {post['title'][:30]}")
            continue

        service.posts().update(
            blogId=blog_id,
            postId=post["id"],
            body={
                "title": post["title"],
                "labels": post.get("labels", []),
                "content": post["content"],
                "searchDescription": desc,
            },
        ).execute()
        print(f"[완료] {post['title'][:30]}\n  -> {desc}")

    print("\n모든 글 처리 완료.")


if __name__ == "__main__":
    main()
