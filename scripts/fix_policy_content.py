"""1회성 스크립트: 이미 발행된 글에서 애드센스/검색 정책 위반 소지가 있는 요소를 제거한다.

- "이 소식을 접한 누리꾼들은 ..." 형태의 가짜 반응 인용 문단을 전부 삭제한다
  (실제로 수집한 적 없는 반응을 사실처럼 인용하는 "사용자 기만 콘텐츠"에 해당).
- 유용한법률/유용한정보 카테고리 글에는, 아직 없다면 "개인 상황에 따라 다를 수
  있으니 공식 기관에서 확인하라"는 한 줄짜리 안내 문구를 마지막 면책 문구 앞에 추가한다.

generate_article.py의 SYSTEM_PROMPT는 이미 이 두 가지를 더 이상 만들어내지 않도록
수정되었으므로, 이 스크립트는 그 수정 이전에 발행된 과거 글들만 손보면 된다.
"""
import os
import re
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REACTION_RE = re.compile(r"<p>이 소식을 접한 누리꾼들은.*?반응을 보이고 있습니다\.</p>", re.DOTALL)

YMYL_LABELS = {"유용한법률", "유용한정보"}
YMYL_MARKER = "관할 기관"
YMYL_NOTICE = (
    '<p style="font-size:13px;color:#777;margin-top:16px;">※ 구체적인 자격 요건과 절차는 '
    "개인 상황에 따라 달라질 수 있으니, 신청 전 관할 기관(정부24, 고용센터, 국민연금공단 "
    "등) 공식 안내를 통해 다시 한번 확인하시기 바랍니다.</p>"
)
FINAL_DISCLAIMER_RE = re.compile(
    r'(<p style="font-size:12px;color:#999;margin-top:24px;">※ 본 콘텐츠는)'
)


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


def list_all_posts(service, blog_id):
    posts = []
    page_token = None
    while True:
        req = service.posts().list(
            blogId=blog_id, maxResults=500, fetchBodies=True, pageToken=page_token
        )
        resp = req.execute()
        posts.extend(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return posts


def fix_content(content, labels):
    changed = False

    new_content, n = REACTION_RE.subn("", content)
    if n:
        content = new_content
        changed = True

    if YMYL_LABELS.intersection(labels) and YMYL_MARKER not in content:
        if FINAL_DISCLAIMER_RE.search(content):
            content = FINAL_DISCLAIMER_RE.sub(YMYL_NOTICE + r"\1", content, count=1)
        else:
            content = content + YMYL_NOTICE
        changed = True

    return content, changed


def main():
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    service = get_blogger_service()

    posts = list_all_posts(service, blog_id)
    print(f"총 {len(posts)}개 글 확인", flush=True)

    updated = 0
    for post in posts:
        post_id = post["id"]
        title = post["title"]
        labels = post.get("labels", [])
        content = post["content"]

        new_content, changed = fix_content(content, labels)
        if not changed:
            continue

        service.posts().update(
            blogId=blog_id,
            postId=post_id,
            body={"title": title, "labels": labels, "content": new_content},
        ).execute()
        updated += 1
        print(f"[수정] {title}", flush=True)
        time.sleep(2)

    print(f"\n총 {len(posts)}개 중 {updated}개 글 수정 완료.", flush=True)


if __name__ == "__main__":
    main()
