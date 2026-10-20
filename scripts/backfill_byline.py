"""기존에 이미 발행된 글들의 기자 바이라인을 모두 교체하는 1회성 스크립트.
기자 이름/이메일이 겹치지 않도록 reporters 목록을 섞어서 글마다 다르게 배정한다."""
import os
import random
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import load_site_config, pick_reporter, set_byline


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

    posts = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True).execute()
    items = posts.get("items", [])
    print(f"총 {len(items)}개 글 확인", flush=True)

    reporters = site.get("reporters", [])
    shuffled = reporters[:]
    random.shuffle(shuffled)

    for i, post in enumerate(items):
        post_id = post["id"]
        title = post["title"]
        labels = post.get("labels", [])
        content = post["content"]

        reporter = shuffled[i % len(shuffled)] if shuffled else pick_reporter(site)
        new_content = set_byline(content, reporter, site)

        service.posts().update(
            blogId=blog_id,
            postId=post_id,
            body={"title": title, "labels": labels, "content": new_content},
        ).execute()
        print(f"[완료] {title} -> {reporter['name']} 기자 ({reporter['email']})", flush=True)
        time.sleep(2)

    print("\n모든 글 처리 완료.", flush=True)


if __name__ == "__main__":
    main()
