"""기존에 이미 발행된 글들에 이미지를 소급 추가하는 1회성 스크립트.
이미 이미지가 들어간 글(본문에 data:image가 있는 글)은 건너뛴다."""
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import insert_images_into_html, load_site_config, resolve_category
from generate_images import generate_images_for_article


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
    images_per_post = int(site.get("images_per_post", 4))
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    service = get_blogger_service()

    posts = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True).execute()
    items = posts.get("items", [])
    print(f"총 {len(items)}개 글 확인")

    for post in items:
        post_id = post["id"]
        title = post["title"]
        content = post["content"]
        labels = post.get("labels", [])
        category = resolve_category(labels, site)

        if "data:image" in content:
            print(f"[건너뜀] 이미 이미지가 있음: {title}")
            continue

        print(f"[처리 중] {title} (카테고리: {category})")
        images = generate_images_for_article(category, title, count=images_per_post)
        print(f"  -> {len(images)}장 생성")
        if not images:
            print("  -> 이미지 생성 실패, 건너뜀")
            continue

        new_content = insert_images_into_html(content, images)
        service.posts().update(
            blogId=blog_id,
            postId=post_id,
            body={"title": title, "labels": labels, "content": new_content},
        ).execute()
        print("  -> 업데이트 완료")
        time.sleep(3)

    print("\n모든 글 처리 완료.")


if __name__ == "__main__":
    main()
