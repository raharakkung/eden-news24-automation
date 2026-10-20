"""기존에 생성된 소개/개인정보처리방침/문의 페이지를 config/site.json 최신 내용으로
덮어쓰는 유틸리티. 제목으로 기존 페이지를 찾아 update한다(새로 만들지 않음)."""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import load_site_config

OLD_TITLES = {
    "about_page": {"검색뉴스 소개", "라하뉴스 소개"},
    "privacy_page": {"개인정보처리방침"},
    "contact_page": {"문의하기"},
}


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

    pages = service.pages().list(blogId=blog_id).execute().get("items", [])

    for key in ("about_page", "privacy_page", "contact_page"):
        page_cfg = site[key]
        match = next((p for p in pages if p["title"] in OLD_TITLES[key]), None)
        if not match:
            print(f"[건너뜀] {key}: 기존 페이지를 찾지 못함")
            continue
        service.pages().update(
            blogId=blog_id,
            pageId=match["id"],
            body={"title": page_cfg["title"], "content": page_cfg["html"]},
        ).execute()
        print(f"[완료] {match['title']} -> {page_cfg['title']}")


if __name__ == "__main__":
    main()
