"""최초 1회 실행: 애드센스 승인에 필요한 소개/개인정보처리방침/문의 페이지를 생성한다."""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import load_site_config


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

    for key in ("about_page", "privacy_page", "contact_page"):
        page = site[key]
        body = {"title": page["title"], "content": page["html"]}
        res = service.pages().insert(blogId=blog_id, body=body, isDraft=False).execute()
        print(f"생성됨: {page['title']} -> {res.get('url')}")

    print("\n완료. Blogger 관리 화면의 '페이지' 메뉴에서 내비게이션 바에 노출할지 확인하세요.")


if __name__ == "__main__":
    main()
