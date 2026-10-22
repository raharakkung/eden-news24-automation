"""매일 실행되는 메인 스크립트: 주제를 골라 기사를 생성하고 Blogger에 발행한다."""
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import (
    add_byline,
    insert_images_into_html,
    load_site_config,
    pick_next_topics,
    pick_reporter,
    save_category_cursor,
    save_used_topics,
)
from generate_article import generate_article
from generate_images import generate_images_for_article

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


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


def publish_post(service, blog_id, article, retries=3):
    """일시적인 네트워크/SSL 오류(예: SSLEOFError)에 대비해 짧게 재시도한다.
    2026-10-22 실제로 Blogger insert 호출 중 SSLEOFError가 발생해 재시도 없이
    스크립트 전체가 죽으면서 그날 발행분이 전부 유실된 적이 있어 추가함."""
    body = {
        "title": article["title"],
        "content": article["html"],
        "labels": article["labels"],
    }
    meta_description = article.get("meta_description")
    if meta_description:
        body["searchDescription"] = meta_description[:150]

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return (
                service.posts()
                .insert(blogId=blog_id, body=body, isDraft=False)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001 - 네트워크/SSL 등 다양한 예외를 포괄 재시도
            last_exc = exc
            print(f"  [발행 재시도 {attempt}/{retries}] {exc}")
            if attempt < retries:
                time.sleep(10 * attempt)
    raise last_exc


def main():
    site = load_site_config()
    count = int(os.environ.get("POSTS_PER_DAY", site.get("posts_per_day", 2)))

    picked, updated_used, next_cursor = pick_next_topics(count)
    if not picked:
        print("발행할 주제가 없습니다. config/topics.json을 확인하세요.")
        sys.exit(1)

    service = None if DRY_RUN else get_blogger_service()
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    results = []
    failed_keys = set()
    for item in picked:
        category, topic = item["category"], item["topic"]
        key = f"{category}::{topic}"
        try:
            print(f"[생성 중] ({category}) {topic}")
            article = generate_article(category, topic, model=site.get("model", "gemini-flash-lite-latest"))

            images_per_post = int(site.get("images_per_post", 4))
            if images_per_post > 0:
                print(f"  [이미지 생성 중] {images_per_post}장")
                images = generate_images_for_article(category, topic, count=images_per_post)
                print(f"  -> {len(images)}장 생성 완료")
                article["html"] = insert_images_into_html(article["html"], images)

            reporter = pick_reporter(site)
            article["html"] = add_byline(article["html"], reporter, site)
            print(f"  [담당 기자] {reporter['name']} 기자 ({reporter['email']})")

            if DRY_RUN:
                print(f"  -> (DRY RUN) 제목: {article['title']}")
            else:
                res = publish_post(service, blog_id, article)
                print(f"  -> 발행 완료: {res.get('url')}")
                time.sleep(5)  # Blogger API 호출 간 약간의 간격

            results.append({"category": category, "topic": topic, "title": article["title"]})
        except Exception as exc:  # noqa: BLE001 - 한 건 실패해도 나머지는 계속 진행
            print(f"  [실패, 건너뜀] ({category}) {topic} - {exc}")
            failed_keys.add(key)

    if not DRY_RUN:
        # 실패한 주제는 '사용함'으로 기록하지 않아 다음 실행에서 다시 시도된다.
        save_used_topics(sorted(updated_used - failed_keys))
        save_category_cursor(next_cursor)

    print(f"\n총 {len(results)}개 기사 발행 완료, {len(failed_keys)}개 실패.")
    for r in results:
        print(f" - [{r['category']}] {r['title']}")

    if failed_keys:
        sys.exit(1)


if __name__ == "__main__":
    main()
