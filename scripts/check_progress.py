"""마이그레이션 진행 상황을 빠르게 확인하는 진단 스크립트."""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


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
    items.sort(key=lambda p: p["published"], reverse=True)
    for p in items:
        has_b64 = "data:image" in p["content"]
        print(f"{p['title'][:30]:30s} len={len(p['content']):>7d} base64={has_b64}")


if __name__ == "__main__":
    main()
