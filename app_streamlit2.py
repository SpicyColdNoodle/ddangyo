###프로젝트 폴더로 이동    cd C:\Users\shic\Downloads\AgentPoC
###가상환경 활성화   .\.venv\Scripts\Activate.ps1
###의존성 설치     pip install -r requirements.txt
### 앱 실행 streamlit run app_streamlit2.py



"""app_streamlit2

이 파일은 Streamlit으로 만든 모바일 친화형(412x915 가정) 챗 UI 예제입니다.

아래와 같은 부분이 손쉽게 조정 가능합니다(예시 포함):

- 헤더 스타일: 배경색, 둥근 정도, 패딩/마진
  예) 헤더 배경색 변경: `.app-header { background: #FB521C; }` → `#111827`
  예) 아래쪽 여백 늘리기: `.app-header { margin: -16px -16px 4px -16px; }`에서 세 번째 값(하단)을 12px로 변경

- 버튼 바(헤더 아래) 레이아웃과 간격: `.button-bar`, `.button-pill`
  예) 버튼 높이: `.button-pill { height: 36px; }` → `32px`
  예) 좌우 여유(패딩): `.button-pill { padding: 0 10px; }` → `0 12px`
  예) 버튼 간 간격: `.button-bar { gap: 8px; }` → `6px`
  예) 전체 가로 폭 한계: `.button-bar { max-width: 412px; }` → 원하는 모바일 기준폭

- 모바일 전용 미디어쿼리: `@media (max-width: 420px)` 아래에서 모바일일 때만 따로 수치 조정
  예) 작은 화면에서 높이만 더 줄이기: `.button-pill { height: 34px; }`

- 색상/테두리/글자색: `.button-pill`의 `background`, `border`, `color`
  예) 테두리 진하게: `border: 1px solid #D1D5DB;` → `#9CA3AF`

주의: CSS padding(패딩)은 음수값을 허용하지 않습니다. `padding: 0 -20px;` 같이 음수로
작성되면 브라우저가 무시할 수 있으니 0 이상의 값으로 설정하는 것을 권장합니다.
"""


import base64
import os
import re
import html as html_lib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from src.safety import moderate_or_block


def load_image_safe(path: Path) -> Optional[bytes]:
    """지정된 경로의 이미지를 안전하게 읽어 bytes로 반환합니다. 파일이 없거나 실패 시 None 반환.

    매개변수:
    - path: 읽을 이미지 파일 경로(Path)

    반환값:
    - 이미지 바이트 또는 None
    """
    try:
        if path.exists() and path.is_file():
            return path.read_bytes()
    except Exception:
        return None
    return None


def to_b64_data_uri(img_bytes: Optional[bytes], mime: str = "image/png") -> str:
    """이미지 바이트를 Base64 Data URI로 변환합니다. 이미지가 없으면 빈 문자열 반환.

    매개변수(초보자용 팁 포함):
    - img_bytes: 이미지 바이트. 파일을 못 읽었다면 None일 수 있습니다.
    - mime: MIME 타입 문자열. PNG는 "image/png", JPG는 "image/jpeg"를 사용하세요.

    예시:
    - PNG로 표시: `to_b64_data_uri(bytes, mime="image/png")`
    - JPG로 표시: `to_b64_data_uri(bytes, mime="image/jpeg")`
    """
    if not img_bytes:
        return ""
    encoded = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def init_graph() -> Any:
    """앱에서 사용하는 그래프(에이전트 파이프라인)를 세션에 1회 생성/캐싱합니다.

    내부적으로 `src.graph.build_graph()`를 호출합니다.
    """
    if "graph" not in st.session_state or st.session_state.get("graph") is None:
        from src.graph import build_graph

        st.session_state["graph"] = build_graph()
    return st.session_state["graph"]


def get_app_paths() -> Tuple[Path, Path, Path]:
    """로고/사용자 아바타/봇 아바타 파일 경로를 반환합니다.

    변경 팁:
    - 파일 이미지를 바꾸고 싶다면 `img` 폴더 내 파일명을 교체하거나 이 함수의 경로를 바꾸세요.
    - PNG/JPG 확장자에 맞춰 `to_b64_data_uri(..., mime=...)`의 mime도 함께 조정하세요.
    """
    root = Path(__file__).resolve().parent
    logo = root / "img" / "mainlogo.png"
    user_avatar = root / "img" / "solbear.png"
    bot_avatar = root / "img" / "bikemolly.jpg"
    return logo, user_avatar, bot_avatar


def render_global_css(logo_uri: str, user_uri: str, bot_uri: str) -> None:
    """앱 전역 CSS를 삽입합니다.

    주요 조정 포인트 요약(초보자용):
    - 배경색: `background: #f5f6f8` 값을 원하는 색상코드로 변경
    - 헤더 스타일: `.app-header` 내 background, padding, margin, border-radius
    - 버튼 바 레이아웃: `.button-bar`의 `gap`, `max-width`
    - 버튼 스타일: `.button-pill`의 `height`, `padding`, `border`, `background`, `color`
    - 모바일 전용 수치: `@media (max-width: 420px)` 아래 값들
    - 채팅 말풍선 스타일: `.bubble-user`, `.bubble-bot`
    - 입력창 고정: `[data-testid="stChatInput"]` 위치
    """
    css = f"""
    <style>
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background: #f5f6f8 !important;
      }}
      html, body {{ margin: 0 !important; padding: 0 !important; }}
      [data-testid="stAppViewContainer"] > .main {{ padding-top: 0 !important; }}
      .block-container {{ padding-top: 0 !important; }}
      /* Hide Streamlit chrome */
      div[data-testid='stToolbar'], header[data-testid='stHeader'], div[data-testid='stDecoration'], #MainMenu {{
        display: none !important;
      }}

      .app-header {{
        position: sticky;
        top: 0;
        z-index: 1000;
        background: #FB521C;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        padding: 14px 12px 16px 12px;
        margin: -16px -16px 4px -16px; /* [조정] 헤더 상하좌우 여백. 4개의 값은 위/우/아래/좌 순서 */
      }}
      .app-header-inner {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }}
      .header-logo {{
        width: 200px;         /* [조정] 로고의 기본 폭(px) */
        max-width: 60vw;      /* [조정] 뷰포트 대비 최대 폭 비율 */
        height: auto;
        display: block;
      }}
      .header-title {{
        color: #FFFFFF;
        font-weight: 700;
        font-size: 18px;      /* [조정] 제목 텍스트 크기 */
        line-height: 1.2;
        text-align: center;
      }}

      /* Button bar under header */
      .button-bar-wrapper {{
        margin: 8px -16px 8px -16px;  /* [조정] 바깥여백: 위/우/아래/좌 */
        padding: 0 12px;              /* [조정] 양옆 안쪽여백 */
      }}
      .button-bar {{
        display: flex;
        flex-direction: row;
        align-items: stretch;
        justify-content: center;
        gap: 8px;                     /* [조정] 버튼 간 간격 */
        width: 100%;
        max-width: 412px;             /* [조정] 목표 모바일 가로폭 (예: 390, 414 등) */
        margin: 0 auto;
      }}
      .button-pill {{
        flex: 1 1 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        height: 36px;                 /* [조정] 버튼 높이(px) */
        padding: 0 10px;              /* [조정] 버튼 좌우 여유(px) */
        border-radius: 999px;
        border: 1px solid #D1D5DB;    /* [조정] 테두리 색상 */
        background: #FFFFFF;          /* [조정] 기본 배경색 */
        color: #111827;               /* [조정] 기본 글자색 */
        text-decoration: none !important;
        font-weight: 600;
        font-size: 14px;              /* [조정] 텍스트 크기 */
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        transition: background 0.15s ease, box-shadow 0.15s ease;
        white-space: nowrap;
        -webkit-tap-highlight-color: transparent;
        user-select: none;
      }}
      .button-pill:link, .button-pill:visited, .button-pill:hover, .button-pill:focus {{
        text-decoration: none !important;
        color: inherit;
        outline: none;
      }}
      .button-pill:active {{
        background: #111827;          /* [조정] 눌렀을 때 배경색 (반전 효과) */
        color: #FFFFFF;               /* [조정] 눌렀을 때 글자색 */
        border-color: #111827;        /* [조정] 눌렀을 때 테두리색 */
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.12);
      }}
      @media (max-width: 420px) {{
        /* 모바일 장치(가로 420px 이하) 전용 조정 영역 */
        .button-pill {{
          font-size: 13px;   /* [조정] 모바일 시 글자 크기 */
          height: 34px;      /* [조정] 모바일 시 높이 */
          padding: 0 -20px;  /* [주의] 음수 패딩은 권장하지 않습니다. 0 이상으로 설정하세요. */
        }}
        .button-bar {{
          gap: 6px;          /* [조정] 모바일 시 버튼 간 간격 */
          max-width: 100%;   /* [조정] 모바일 시 가로폭 제한 해제 */
        }}
      }}

      

      /* Chat area */
      .chat-container {{
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding-bottom: 30px; /* space for input */
        margin-top: 0;
      }}
      .msg-row {{ display: flex; gap: 8px; align-items: flex-start; }}
      .msg-row.bot {{ justify-content: flex-start; }}
      .msg-row.user {{ justify-content: flex-end; }}
      .avatar {{
        width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex: 0 0 48px;
      }}
      .bubble {{
        max-width: 78vw;
        padding: 10px 12px;
        border-radius: 14px;
        line-height: 1.45;
        font-size: 14px;
        word-wrap: break-word;
        white-space: pre-wrap;
      }}
      .bubble-user {{
        background: #FF7A00; color: #FFFFFF;
        margin-left: 48px; /* pad opposite side */
      }}
      .bubble-bot {{
        background: #FFFFFF; color: #111827; border: 1px solid #e6e8f0;
        margin-right: 48px; /* pad opposite side */
      }}
      .bubble-bot .deeplink-btn {{
        display: inline-flex;
        align-items: center; justify-content: center;
        height: 30px; padding: 0 10px; margin-top: 6px;
        border: 1px solid #FF7A00; border-radius: 10px;
        background: #FF7A00; color: #FFFFFF; font-weight: 500; font-size: 13px;
        text-decoration: none !important; white-space: nowrap;
      }}
      .bubble-bot .deeplink-btn:active {{
        filter: brightness(0.95);
      }}

      /* Make Streamlit chat input stick to bottom */
      [data-testid="stChatInput"] {{
        position: fixed; bottom: 8px; left: 16px; right: 16px; z-index: 1000;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header(logo_uri: str) -> None:
    """상단 헤더(로고 + 타이틀)를 렌더링합니다.

    변경 팁:
    - 로고 크기/타이틀 크기: 전역 CSS의 `.header-logo`, `.header-title`를 조정하세요.
    - 헤더 배경색/둥근 모서리/여백: `.app-header`를 조정하세요.
    """
    st.markdown(
        f"""
        <div class="app-header">
          <div class="app-header-inner">
            <img src="{logo_uri}" alt="logo" class="header-logo" />
            <div class="header-title">땡겨요 1:1 고객문의</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header_buttons() -> None:
    """헤더 아래에 가로 정렬된 3개의 버튼을 렌더링합니다(모바일 최적화).

    변경 팁:
    - 버튼 텍스트 변경: 아래 HTML의 텍스트를 바꾸면 됩니다.
    - 버튼 동작 추가: 현재는 `onclick="return false;"`로 클릭을 막고 있습니다.
      페이지 이동을 원하면 `href="#"` 대신 URL을 넣거나, Streamlit과 상호작용하려면
      `st.session_state`를 갱신하는 콜백 방식을 고려하세요.
    - 버튼 스타일(두께/여백/색상 등)은 `render_global_css` 내 `.button-pill`을 수정하세요.
    """
    st.markdown(
        """
        <div class="button-bar-wrapper">
          <div class="button-bar">
            <a class="button-pill" href="#" onclick="return false;">자주묻는 질문</a>
            <a class="button-pill" href="#" onclick="return false;">상담원 연결</a>
            <a class="button-pill" href="#" onclick="return false;">주문조회</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _convert_links_to_buttons(text: str) -> str:
    """텍스트 내 URL을 탐지해 버튼(anchor) HTML로 치환합니다.

    동작:
    - 일반 텍스트는 HTML 이스케이프 처리하여 안전하게 표시
    - URL은 `<a class="deeplink-btn" href="...">앱으로 이동</a>` 버튼으로 변환

    초보자 팁:
    - 버튼 문구를 바꾸려면 아래 `button_label` 값을 변경하세요.
    - 새 창 없이 동일 창을 쓰려면 `target` 속성을 제거하세요.
    """
    if not text:
        return ""

    button_label = "앱으로 이동"

    # 1) 전체를 escape 해서 안전하게 만든 후, URL만 버튼으로 대체
    escaped = html_lib.escape(text)

    # 2) URL 정규식 (http/https 및 커스텀 스킴 모두 포괄)
    url_pattern = re.compile(r"(https?://[^\s]+|[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+)")

    def repl(match: re.Match) -> str:
        url = match.group(0)
        safe_url = html_lib.escape(url)
        return (
            f'<a class="deeplink-btn" href="{safe_url}" target="_blank" rel="noopener noreferrer">{button_label}</a>'
        )

    converted = url_pattern.sub(repl, escaped)
    return converted

 


def call_graph(user_text: str) -> str:
    """그래프(에이전트 파이프라인)에 사용자 입력을 전달하고 응답 텍스트를 반환합니다.

    매개변수:
    - user_text: 사용자가 입력한 문장

    반환값:
    - 문자열 형태의 응답. 내부 딕셔너리 키(`final_text`, `response`)를 우선 추출하며,
      실패하면 문자열로 변환하여 반환합니다.
    """
    graph = init_graph()
    try:
        # 입력 안전 필터링
        blocked, safe_text, stats = moderate_or_block(user_text)
        if blocked:
            return "부적절한 표현이 감지되어 요청이 차단되었습니다."

        result: Dict[str, Any] = graph.invoke({"user_input": safe_text, "_safety_stats": stats})
        if isinstance(result, dict):
            if "final_text" in result and isinstance(result["final_text"], str):
                return result["final_text"].strip()
            if "response" in result and isinstance(result["response"], str):
                return result["response"].strip()
        return str(result)
    except Exception as exc:  # fallback safe
        return f"오류가 발생했습니다: {exc}"


def render_messages(messages: List[Dict[str, str]], user_uri: str, bot_uri: str) -> None:
    """대화 메시지 목록을 렌더링합니다.

    매개변수:
    - messages: `{ "role": "user"|"assistant", "content": str }`의 리스트
    - user_uri: 사용자 아바타 이미지 Data URI
    - bot_uri:  봇 아바타 이미지 Data URI

    UI 조정 팁:
    - 말풍선 최대 폭: `.bubble { max-width: 78vw; }`
    - 말풍선 색상: `.bubble-user`, `.bubble-bot`
    - 아바타 크기: `.avatar { width/height }`
    """
    st.markdown("<div class=\"chat-container\">", unsafe_allow_html=True)
    for msg in messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            st.markdown(
                f"""
                <div class="msg-row user">
                  <div class="bubble bubble-user">{content}</div>
                  <img class="avatar" src="{user_uri}" alt="me" />
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # 봇 응답 내 URL을 버튼으로 치환하여 표시
            content_html = _convert_links_to_buttons(content)
            st.markdown(
                f"""
                <div class="msg-row bot">
                  <img class="avatar" src="{bot_uri}" alt="bot" />
                  <div class="bubble bubble-bot">{content_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    """앱의 진입점. 환경 설정, 에셋 로딩, CSS/헤더/버튼/메시지 렌더링을 수행합니다.

    자주 바꾸는 설정:
    - 페이지 제목: `st.set_page_config(page_title=...)`
    - 페이지 아이콘: `page_icon` 경로 변경 가능
    - 초기 메시지: `st.session_state["messages"]`의 초기값 변경
    - 레이아웃: `layout="wide"` → 필요시 `"centered"`
    """
    load_dotenv()
    st.set_page_config(
        page_title="땡겨요 고객문의 에이전트",
        page_icon=str((Path(__file__).resolve().parent / "img" / "mainlogo.png")),
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    logo_path, user_path, bot_path = get_app_paths()
    logo_uri = to_b64_data_uri(load_image_safe(logo_path), mime="image/png")
    user_uri = to_b64_data_uri(load_image_safe(user_path), mime="image/png")
    bot_uri = to_b64_data_uri(load_image_safe(bot_path), mime="image/jpeg")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}
        ]

    render_global_css(logo_uri, user_uri, bot_uri)
    render_header(logo_uri)
    render_header_buttons()

    render_messages(st.session_state["messages"], user_uri, bot_uri)

    user_text = st.chat_input("메시지를 입력하세요")
    if user_text:
        st.session_state["messages"].append({"role": "user", "content": user_text})
        bot_reply = call_graph(user_text)
        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        st.rerun()


if __name__ == "__main__":
    main()


