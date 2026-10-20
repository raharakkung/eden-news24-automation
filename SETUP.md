# 이든뉴스 자동화 설정 가이드

이 문서를 순서대로 따라 하면 **eden-news24.blogspot.com**에 매일 자동으로 글이
올라오도록 설정됩니다. `google-blog`(라하뉴스) 자동화와 완전히 독립적으로 동작하며,
**새 GitHub 계정 + 새 Google 계정**을 사용합니다.

로그인·비밀번호 입력·OAuth 동의 화면 클릭처럼 자격 증명이 필요한 단계는
**반드시 본인이 직접 브라우저에서 진행**해야 합니다(Claude가 대신 할 수 없음).
그 외 로컬 파일 작성/스크립트 실행은 Claude에게 요청하면 됩니다.

---

## STEP 0. 블로그 확인 (이미 생성되어 있음)

`https://eden-news24.blogspot.com/` 블로그는 이미 만들어져 있습니다("EDEN NEWS").
이 블로그가 어떤 Google 계정 소유인지 먼저 확인하세요 — **STEP 2~5의 Google Cloud
프로젝트, OAuth 클라이언트, Gemini API 키는 반드시 이 블로그를 소유한 Google 계정으로
진행해야 합니다.**

## STEP 1. GitHub 계정 전환 및 저장소 생성

1. 사용하려는 새 GitHub 계정으로 브라우저에 로그인
2. 새 저장소 생성 (예: `eden-news24-automation`)
   - **Public 권장** — Public 저장소는 GitHub Actions 실행 시간이 무제한 무료입니다.
     Private로 하면 월 2,000분 무료 한도를 하루 20건 발행 기준으로 초과할 수 있습니다.
     시크릿 값은 저장소가 Public이어도 암호화되어 노출되지 않습니다.
3. 아직 `git remote push`는 하지 마세요 — STEP 6에서 진행합니다.

## STEP 2. Google Cloud에서 Blogger API 사용 설정

1. https://console.cloud.google.com 접속 → **eden-news24 블로그를 소유한 Google 계정**으로 로그인
2. 상단 "프로젝트 선택" → "새 프로젝트" → 이름: `eden-news24-automation` → 만들기
3. 좌측 메뉴 → "API 및 서비스" → "라이브러리" → `Blogger API` 검색 → **사용 설정**
4. 좌측 메뉴 → "API 및 서비스" → "OAuth 동의 화면"
   - User Type: **외부(External)** 선택 → 만들기
   - 앱 이름: `이든뉴스 자동화`, 사용자 지원 이메일: 본인 이메일
   - 범위(Scopes) 단계는 기본값으로 넘어가도 됩니다
   - "테스트 사용자" 단계에서 본인 구글 이메일 주소를 추가
   - 저장 후 완료 (게시 상태는 "테스트" 그대로 두어도 자동화에는 문제 없습니다)
5. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
   - "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
   - 애플리케이션 유형: **데스크톱 앱**, 이름: `eden-news-desktop`
   - 만들기 후 뜨는 창에서 **JSON 다운로드** → 파일명을 `client_secret.json`으로 저장
   - 이 파일은 이 프로젝트 폴더 바로 아래 두되, 절대 GitHub에 올리지 마세요
     (`.gitignore`에 이미 등록되어 있습니다)

## STEP 3. 내 PC에서 1회 로그인하여 refresh token 받기

```bash
pip install -r requirements.txt
python scripts/get_refresh_token.py client_secret.json
```

자동으로 열리는 브라우저에서 STEP 2의 Google 계정으로 로그인·동의하세요
("앱이 확인되지 않았습니다" 경고가 뜨면 "고급" → "이동" 클릭, 본인이 만든 앱이라 안전).
터미널에 출력되는 `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN`을
메모해 두세요.

## STEP 4. Blog ID 확인하기

https://www.blogger.com 에서 eden-news24 블로그 관리 화면 접속 → 주소창 URL의
숫자 부분(`https://www.blogger.com/blog/posts/<이 숫자>`)이 `BLOGGER_BLOG_ID`입니다.

## STEP 5. Google Gemini API 키 발급 (무료)

1. https://aistudio.google.com/apikey 접속 (STEP 2와 동일한 Google 계정)
2. **"Create API key"** → 방금 만든 `eden-news24-automation` 프로젝트 선택
3. 생성된 키를 복사해 두세요 (`GEMINI_API_KEY`) — 신용카드 등록 불필요, 완전 무료 티어

## STEP 6. 로컬 저장소를 새 GitHub 저장소로 push

```bash
cd vibecoding-projects/eden-news24-blog
git init
git add .
git commit -m "init: 이든뉴스 자동화 프로젝트"
git branch -M main
git remote add origin https://github.com/<새-계정>/eden-news24-automation.git
git push -u origin main
```

`git push` 시 뜨는 인증 창에서 STEP 1의 새 GitHub 계정으로 로그인하세요.

## STEP 7. GitHub 저장소에 Secrets 등록

저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | STEP 5에서 받은 키 |
| `GOOGLE_CLIENT_ID` | STEP 3에서 받은 값 |
| `GOOGLE_CLIENT_SECRET` | STEP 3에서 받은 값 |
| `GOOGLE_REFRESH_TOKEN` | STEP 3에서 받은 값 |
| `BLOGGER_BLOG_ID` | STEP 4에서 확인한 숫자 |

## STEP 8. 필수 페이지 자동 생성 (소개/개인정보처리방침/문의)

애드센스 승인에는 이 페이지들이 꼭 필요합니다. 로컬에서 1회만 실행하세요.

```bash
set GEMINI_API_KEY=...
set GOOGLE_CLIENT_ID=...
set GOOGLE_CLIENT_SECRET=...
set GOOGLE_REFRESH_TOKEN=...
set BLOGGER_BLOG_ID=...
python scripts/create_static_pages.py
```

## STEP 9. 자동화 테스트 실행

1. GitHub 저장소 → **Actions** 탭 → "Daily Publish to Blogger" 워크플로 선택
2. **Run workflow** 버튼으로 수동 실행
3. 실행 시간을 확인하세요 (기본 20건 기준 약 1.5~3시간 예상). 완료 후 블로그에 글
   20개가 올라오는지 확인
4. 문제가 있다면 Actions 실행 로그에서 에러 메시지를 확인 (Secrets 오타가 가장 흔한 원인)

## STEP 10. 운영 및 발행량 확장

- 이후로는 매일 한국시간 오전 9시(`cron: "0 0 * * *"`, UTC 기준)에 자동으로
  20개 글이 발행됩니다.
- 며칠간 Actions 탭에서 실행 시간·실패율이 안정적인지 모니터링한 뒤, 늘리고 싶다면
  `.github/workflows/daily-publish.yml`의 `POSTS_PER_DAY` 값만 올리세요(Gemini 무료
  한도는 1일 1,000회라 여유가 많습니다. 다만 Pollinations.ai 이미지 생성과 GitHub
  Actions 실행 시간이 실질적인 제약이니 30 → 50처럼 점진적으로 늘리는 것을 권장합니다).
- 주제가 바닥나면 `config/topics.json`에 새 항목을 추가해 주세요.
- 검색엔진 노출 설정(Google Search Console, 네이버 서치어드바이저, 다음 웹마스터도구
  등록)은 `google-blog/SETUP.md`의 **STEP 11**을 참고해 동일한 방식으로 진행하면 됩니다
  (주소만 eden-news24로 바꿔서).
