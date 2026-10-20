"""최초 1회, 내 PC에서 직접 실행하는 스크립트.

Google Cloud Console에서 다운로드한 client_secret.json을 이용해
브라우저로 로그인/동의 절차를 거친 뒤, GitHub Actions에 등록할
refresh_token을 콘솔에 출력한다.

사용법:
    python scripts/get_refresh_token.py client_secret.json
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/blogger"]


def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/get_refresh_token.py <client_secret.json 경로>")
        sys.exit(1)

    client_secret_path = sys.argv[1]
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n브라우저 인증이 완료되었습니다. 아래 값을 GitHub Secrets에 등록하세요.\n")
    print(f"GOOGLE_CLIENT_ID     = {creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET = {creds.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN = {creds.refresh_token}")

    if not creds.refresh_token:
        print(
            "\n[경고] refresh_token이 발급되지 않았습니다. "
            "Google 계정 설정 > 보안 > 타사 액세스 권한이 있는 앱에서 "
            "기존 연결을 삭제한 뒤 이 스크립트를 다시 실행해 보세요."
        )


if __name__ == "__main__":
    main()
