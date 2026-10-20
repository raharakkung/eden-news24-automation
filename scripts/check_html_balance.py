"""각 글의 content HTML에 태그 불균형(닫히지 않은 태그 등)이 있는지 점검하는 진단 스크립트.
홈/검색/라벨 등 여러 글을 한번에 보여주는 뷰에서 1개 글만 렌더링되고 멈추는 버그의
원인이 특정 글의 깨진 HTML(스니펫 생성 스크립트가 처리하다 죽는 것)인지 확인하기 위함."""
import os
import re
from html.parser import HTMLParser

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

VOID_TAGS = {"br", "img", "hr", "input", "meta", "link", "area", "base", "col", "embed", "source", "track", "wbr"}


class BalanceChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(f"닫는 태그만 있고 여는 태그 없음: </{tag}>")
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            idx = len(self.stack) - 1 - self.stack[::-1].index(tag)
            unclosed = self.stack[idx + 1:]
            self.errors.append(f"</{tag}> 닫기 전에 안 닫힌 태그들: {unclosed}")
            self.stack = self.stack[:idx]
        else:
            self.errors.append(f"짝 없는 닫는 태그: </{tag}>")

    def error(self, message):
        self.errors.append(f"parser error: {message}")


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

    for i, post in enumerate(items):
        content = post["content"]
        checker = BalanceChecker()
        checker.feed(content)
        base64_matches = re.findall(r'data:image/[a-zA-Z]+;base64,([A-Za-z0-9+/=]+)', content)
        print(f"[{i}] {post['title'][:30]!r} published={post['published']}")
        print(f"    길이: {len(content)}자, base64 이미지 수: {len(base64_matches)}, 남은 스택: {checker.stack}")
        if checker.errors:
            for e in checker.errors[:5]:
                print(f"    문제: {e}")
        else:
            print("    태그 균형: 정상")
        # 이상한 제어문자/널바이트 확인
        bad_chars = [c for c in content if ord(c) < 32 and c not in "\t\n\r"]
        if bad_chars:
            print(f"    제어문자 발견: {[hex(ord(c)) for c in bad_chars[:10]]}")
        print()


if __name__ == "__main__":
    main()
