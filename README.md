# 이든뉴스 (EDEN NEWS) — 자동 바이럴 트렌드 블로그

이슈·연예·스포츠·라이프·유용한정보·유용한법률·동물뉴스 등 다양한 분야의 "지금 화제가
되는" 트렌드를 다루는 블로그입니다. **Google Gemini API 무료 티어**가 기사를 생성하고
Blogger API로 자동 발행합니다. GitHub Actions가 매일 지정된 수(기본 20개)만큼 글을
올립니다. 이미지는 **Pollinations.ai**(무료, 가입/카드 불필요)로 기사당 4장씩 생성됩니다.

이 프로젝트는 `google-blog`(라하뉴스) 자동화 파이프라인을 복제해 만들었으며, 완전히
독립된 GitHub 계정·저장소·Google 계정·Blogger 블로그(eden-news24.blogspot.com)를
사용합니다. 두 프로젝트는 서로 영향을 주지 않습니다.

## ⚠️ 콘텐츠 안전 규칙 (반드시 숙지)

`scripts/generate_article.py`의 프롬프트에는 **실존 인물(연예인/운동선수/공인)의
이름이나 그 사람이 실제로 한 것처럼 보이는 발언·사건을 절대 지어내지 않는다**는
규칙이 명시돼 있습니다. "연예"/"스포츠"/"이슈" 카테고리도 업계 트렌드·일반 현상
수준으로만 다루도록 설계했습니다. 이 규칙을 임의로 제거하지 마세요 — 실존 인물에
대한 허위 사실은 명예훼손 소지가 있습니다.

## 구성

- `config/site.json` — 사이트 기본 정보, 카테고리(7개), 담당 기자 배정, 소개/개인정보처리방침/문의 페이지 내용
- `config/topics.json` — 카테고리별 주제(검색 키워드) 뱅크
- `data/used_topics.json`, `data/category_cursor.json` — 발행 진행 상태(자동 갱신됨)
- `scripts/generate_article.py` — Gemini API(무료)로 기사 1건 생성 (바이럴 트렌드 톤 + 실존 인물 금지 규칙)
- `scripts/generate_images.py` — Pollinations.ai(무료)로 기사당 이미지 생성
- `scripts/publish_to_blogger.py` — 매일 실행되는 메인 스크립트 (주제 선택 → 기사/이미지 생성 → 바이라인 추가 → 발행)
- `scripts/get_refresh_token.py` — 최초 1회, 로컬에서 Google OAuth 인증
- `scripts/create_static_pages.py` — 최초 1회, 필수 페이지(소개/개인정보처리방침/문의) 생성
- `.github/workflows/daily-publish.yml` — 매일 자동 실행 워크플로 (기본 `POSTS_PER_DAY=20`)
- `SETUP.md` — 처음부터 끝까지 따라 하는 설정 가이드 (여기부터 시작하세요)

## 시작하기

`SETUP.md`를 순서대로 따라 하세요.

## 로컬 테스트 (발행 없이 생성만 확인)

```bash
pip install -r requirements.txt
set GEMINI_API_KEY=AIzaSyxxxx
set DRY_RUN=true
python scripts/publish_to_blogger.py
```

## 발행량 조정

기본값은 하루 20개입니다(Gemini 무료 한도 1일 1,000회 중 2%만 사용, 매우 여유 있음).
안정적으로 며칠 돌아가는 것을 Actions 탭에서 확인한 뒤, 다음 두 곳의 숫자를 함께
올리면 발행량을 늘릴 수 있습니다:

- `.github/workflows/daily-publish.yml`의 `POSTS_PER_DAY`
- (선택) `config/site.json`의 `posts_per_day` — 로컬 실행 시 기본값으로 쓰임
