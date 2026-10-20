"""기존에 base64로 삽입된 이미지를 외부 URL(Pollinations.ai) 참조로 교체하는 1회성 마이그레이션.

문제: 글마다 base64 이미지 4장이 본문에 직접 삽입되어 글 하나가 180~210KB까지 커졌고,
Blogger가 홈/검색 등 여러 글을 한 번에 보여주는 페이지에서 응답 크기 제한에 걸려
글이 1~2개만 보이고 나머지가 잘려나가는 문제가 있었다(2026-10-17 확인).

해결: 기존 base64 <img> 태그를 전부 제거하고, 같은 카테고리 프롬프트로 새로 생성한
Pollinations 외부 URL 이미지로 교체한다(본문 용량이 200KB -> 2~3KB 수준으로 줄어듦)."""
import os
import re
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import insert_images_into_html, load_site_config, resolve_category
from generate_images import generate_images_for_article

IMG_RE = re.compile(r'<img[^>]*src="data:image/[^"]*"[^>]*/?>', re.DOTALL)


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
    images_per_post = int(site.get("images_per_post", 4))
    service = get_blogger_service()

    posts = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True).execute()
    items = posts.get("items", [])
    print(f"총 {len(items)}개 글 확인\n")

    for post in items:
        content = post["content"]
        title = post["title"]
        labels = post.get("labels", [])
        category = resolve_category(labels, site)

        before_len = len(content)
        stripped = IMG_RE.sub("", content)
        has_base64 = "data:image" in content
        has_any_img = bool(re.search(r"<img", content))

        if has_any_img and not has_base64:
            print(f"[건너뜀] 이미 외부 URL 이미지로 마이그레이션됨: {title[:30]}")
            continue

        print(f"[처리 중] {title[:30]} (카테고리: {category}, 기존 길이: {before_len}자)")
        images = generate_images_for_article(category, title, count=images_per_post)
        print(f"  -> 새 이미지 {len(images)}장 생성 (외부 URL)")

        new_content = insert_images_into_html(stripped, images)
        print(f"  -> 새 길이: {len(new_content)}자")

        service.posts().update(
            blogId=blog_id,
            postId=post["id"],
            body={"title": title, "labels": labels, "content": new_content},
        ).execute()
        print("  -> 업데이트 완료\n")
        time.sleep(3)

    print("모든 글 처리 완료.")


if __name__ == "__main__":
    main()
