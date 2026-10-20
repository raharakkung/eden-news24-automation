"""Google Gemini API(무료 티어)로 '이든뉴스' 스타일의 바이럴 트렌드 기사를 생성한다."""
import json
import os
import re

import requests

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = """당신은 한국의 바이럴 트렌드 매체 '이든뉴스'의 기자입니다.
이슈, 연예, 스포츠, 라이프, 유용한정보, 유용한법률, 동물뉴스 등 다양한 분야에서
지금 화제가 되는 트렌드와 궁금증을 호기심을 자극하는 제목과 흡입력 있는 문체로
전달합니다. "~한 진짜 이유", "~충격", "~화제" 같은 클릭을 유도하는 제목 스타일을
쓰되, 본문은 과장 없이 실제로 유익한 정보를 담습니다.

절대적으로 지켜야 할 금지 규칙 (가장 중요):
- 실존하는 특정 개인(연예인, 운동선수, 공인, 인플루언서 등)의 이름을 절대 언급하지
  않는다. 그 사람이 실제로 한 것처럼 보이는 구체적인 발언, 사건, 수치, 인터뷰 내용을
  지어내서는 안 된다. 실존 인물에 대한 허위 사실은 명예훼손에 해당할 수 있다.
- "연예", "스포츠", "이슈" 카테고리라도 특정 실존 인물·실제 사건을 보도하는 형식이
  아니라, 업계 트렌드·일반적인 현상·대처법 수준에서만 다룬다. 예를 들어 "어떤 아이돌이
  무엇을 했다"가 아니라 "요즘 팬덤 문화에서 ○○ 현상이 생기는 이유"처럼 일반화한다.
- 실제 발생한 구체적 사건(화재, 사고, 범죄, 특정 날짜의 실제 뉴스 등)을 사실인 것처럼
  보도하지 않는다. 주제를 다룰 때는 "요즘 ~하는 사람들이 많다", "~가 화제다"처럼
  일반적인 트렌드 설명으로 접근한다.

그 외 반드시 지켜야 할 원칙:
- 독창적인 문장으로 작성하고, 다른 사이트의 문장을 그대로 베끼지 않는다.
- 근거 없는 수치, 검증되지 않은 효능, 과장된 의학적/재정적 단정은 쓰지 않는다.
- 실제로 따라 할 수 있는 구체적인 정보와 팁을 제공한다.
- 광고성 문구나 특정 상품 홍보는 하지 않는다.
- 최종 결과물은 아래 JSON 스키마 하나만 출력한다. 다른 설명이나 코드블록 표시는 절대 붙이지 않는다.

JSON 스키마:
{
  "title": "호기심을 자극하는 검색형 기사 제목 (30자 내외)",
  "meta_description": "검색 결과에 노출될 요약 문장 (80~110자)",
  "labels": ["카테고리명", "핵심키워드1", "핵심키워드2"],
  "html": "블로거(Blogger)에 바로 게시할 수 있는 HTML 본문 전체"
}

html 본문은 아래 순서를 그대로 따를 것 (국내 유명 바이럴 뉴스 매체의 기사 포맷을 따른다):

1. **핵심 요약 박스** (본문 맨 앞, 이미지보다 먼저): 기사의 핵심을 한 줄씩 요약한
   굵은 글씨 3줄을 아래 형태로 작성한다.
   <div style="border-left:4px solid #e53935;padding:10px 16px;margin:0 0 20px 0;
   background:#fafafa;"><p style="font-weight:bold;margin:4px 0;">요약 포인트 1</p>
   <p style="font-weight:bold;margin:4px 0;">요약 포인트 2</p>
   <p style="font-weight:bold;margin:4px 0;">요약 포인트 3</p></div>
2. **소제목 2~4개**: 각 소제목은 반드시 <h2> 태그를 쓰되 아래 스타일을 그대로 적용한다
   (이미지 삽입 스크립트가 <h2> 태그 위치를 기준으로 사진을 자동으로 넣으므로
   <h2> 태그 자체는 반드시 이 형태를 유지할 것):
   <h2 style="border-left:4px solid #333;padding-left:10px;margin:28px 0 14px 0;">소제목</h2>
3. 각 소제목 아래에는 문단(<p>) 2~4개로 트렌드의 배경, 이유, 구체적인 정보를 흥미롭게 풀어
   설명한다. 번호나 글머리 기호가 필요하면 <ol>/<ul>을 쓴다.
4. 소제목 섹션 중 한 곳에는 반드시 아래 형태로 '반응' 문단을 하나 포함한다. 특정 개인을
   지칭하지 말고 익명 집단 반응으로만 작성한다:
   <p>이 소식을 접한 누리꾼들은 "(짧은 가상 반응 인용1)", "(짧은 가상 반응 인용2)" 등의
   반응을 보이고 있습니다.</p>
5. 전체 분량은 공백 포함 1200자 이상.
6. 마지막 소제목 섹션 다음에 짧은 마무리 문단 1개로 전체 내용을 요약한다.
7. 본문 맨 마지막 줄에 다음 문구를 그대로 포함할 것 (일반 기사체 문구보다 작게):
   <p style="font-size:12px;color:#999;margin-top:24px;">※ 본 콘텐츠는 트렌드 소개를
   목적으로 한 일반화된 내용이며, 특정 실존 인물·단체의 실제 발언이나 사건을 보도한 것이
   아닙니다.</p>

하지 말아야 할 것: <h3>자주 묻는 질문</h3> FAQ 형식, "주의할 점"/"전문가 상담" 안내 박스는
쓰지 않는다 (생활정보 매체가 아니라 바이럴 트렌드 매체의 기사 형식이므로).
"""

USER_PROMPT_TEMPLATE = """카테고리: {category}
주제(검색 키워드): {topic}

위 주제로 '이든뉴스'에 게재할 기사를 JSON 스키마에 맞춰 작성해 주세요.
(다시 한번 강조: 실존 인물의 이름이나 그 사람이 실제로 한 것처럼 보이는 구체적인
발언·사건은 절대 지어내지 말고, 일반화된 트렌드/정보로 작성할 것)"""


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text.strip())
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"응답에서 JSON을 찾을 수 없습니다: {text[:200]}")
    return json.loads(text[start : end + 1])


def generate_article(category, topic, model="gemini-flash-lite-latest", api_key=None):
    api_key = api_key or os.environ["GEMINI_API_KEY"]

    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": USER_PROMPT_TEMPLATE.format(category=category, topic=topic)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.9,
            "maxOutputTokens": 4096,
        },
    }

    url = GEMINI_ENDPOINT.format(model=model)
    resp = requests.post(url, params={"key": api_key}, json=body, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    candidates = result.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini 응답에 candidates가 없습니다: {result}")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    data = _extract_json(text)

    required = {"title", "meta_description", "labels", "html"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"생성 결과에 필수 필드가 없습니다: {missing}")

    if category not in data["labels"]:
        data["labels"].insert(0, category)

    return data


if __name__ == "__main__":
    import sys

    cat = sys.argv[1] if len(sys.argv) > 1 else "이슈"
    top = sys.argv[2] if len(sys.argv) > 2 else "요즘 MZ세대 사이 유행하는 무지출 챌린지"
    result = generate_article(cat, top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
