import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

# LangGraph 그래프 로딩
from src.graph import build_graph
from src.safety import moderate_or_block


def get_project_root() -> Path:
    return Path(__file__).resolve().parent


def load_image_safe(path: Path) -> Image.Image | None:
    try:
        return Image.open(path)
    except Exception:
        return None


def get_asset_path(relative: str) -> Path:
    return get_project_root() / relative


def init_app_state() -> None:
    if "graph" not in st.session_state:
        st.session_state.graph = build_graph()
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_header(logo_path: Path) -> None:
    # 중앙 정렬 + 모바일 적정 크기 + 상단 영역 축소
    import base64
    img_tag = ""
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            img_tag = f"<img alt='logo' src='data:image/{logo_path.suffix[1:]};base64,{b64}' style=\"display:block;margin:0 auto;max-width:70%;width:200px;height:auto;\"/>"
    except Exception:
        if (logo_img := load_image_safe(logo_path)) is not None:
            # 폴백: st.image (중앙 래퍼로 감쌈)
            st.markdown("<div class='header-wrap'><div class='header-logo'>", unsafe_allow_html=True)
            st.image(logo_img, width=200)
            st.markdown("</div><div class='header-title'>땡겨요 1:1 고객문의</div></div>", unsafe_allow_html=True)
            st.markdown("<div class='header-sep'></div>", unsafe_allow_html=True)
            return

    st.markdown("<div class='header-wrap'>" +
                "<div class='header-logo'>" + img_tag + "</div>" +
                "<div class='header-title'>땡겨요 1:1 고객문의</div>" +
                "</div>", unsafe_allow_html=True)
    # 헤더와 채팅 영역 구분 장식 제거 (요청 반영)


def render_messages(user_avatar: Path, bot_avatar: Path) -> None:
    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")

        is_user = role == "user"
        if is_user:
            _render_bubble_with_avatar(content, user_avatar, align="right")
        else:
            _render_bubble_with_avatar(content, bot_avatar, align="left")


def _render_bubble_with_avatar(text: str, avatar_path: Path, align: str = "left") -> None:
    # 큰 아바타 + 말풍선 (좌측 위/우측 위 정렬)
    bubble_class = "bubble-user" if align == "right" else "bubble-bot"
    
    # 이미지를 base64로 인코딩하여 안정적으로 표시
    import base64
    try:
        with open(avatar_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
            img_src = f"data:image/{avatar_path.suffix[1:]};base64,{img_data}"
    except Exception:
        img_src = str(avatar_path)
    
    if align == "right":
        # 사용자: 우측 위 정렬
        st.markdown(
            f"""
            <div style="display:flex; align-items:flex-start; justify-content:flex-end; gap:10px; margin:6px 0; width:100%; padding-left:50px;">
                <div class="{bubble_class}">{text}</div>
                <img src="{img_src}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;flex-shrink:0;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # 챗봇: 좌측 위 정렬
        st.markdown(
            f"""
            <div style="display:flex; align-items:flex-start; justify-content:flex-start; gap:10px; margin:6px 0; width:100%; padding-right:50px;">
                <img src="{img_src}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;flex-shrink:0;" />
                <div class="{bubble_class}">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def invoke_agent(user_text: str) -> str:
    # 안전 필터링
    blocked, safe_text, stats = moderate_or_block(user_text)
    if blocked:
        return "부적절한 표현이 감지되어 요청이 차단되었습니다."

    state = {"user_input": safe_text, "_safety_stats": stats}
    result = st.session_state.graph.invoke(state)
    return (
        result.get("final_text")
        or result.get("response")
        or "(응답이 없습니다)"
    )


def main() -> None:
    load_dotenv()

    st.set_page_config(
        page_title="땡겨요 고객문의 에이전트",
        page_icon=str(get_asset_path("img/mainlogo.png")),
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # 가벼운 모바일 최적화 스타일
    ORANGE = "#FF7A00"  # 로고 주황 톤(예시)
    HEADER = "#FB521C"  # R:251, G:82, B:28
    st.markdown(
        f"""
        <style>
        /* 본문 여백 제거(최상단), 채팅 폭 제한 */
        .block-container {{ padding-top: 0; padding-bottom: 6rem; max-width: 720px; }}
        footer {{ visibility: hidden; }}
        /* 전역 배경: 아주 연한 회색 */
        html, body, [data-testid="stAppViewContainer"] {{ background: #f5f6f8 !important; }}
        /* 툴바/헤더/데코레이션 완전 제거 */
        div[data-testid='stToolbar']{{ display:none !important; height:0 !important; visibility:hidden !important; }}
        header[data-testid='stHeader']{{ display:none !important; height:0 !important; visibility:hidden !important; }}
        div[data-testid='stDecoration']{{ display:none !important; height:0 !important; visibility:hidden !important; }}
        #MainMenu {{ display:none !important; }}

        /* 헤더 영역 - 최상단까지 확장, 로고 잘림 방지 */
        .header-wrap {{
            display: flex; flex-direction: column; align-items: center;
            background: {HEADER};
            /* 상단/좌우 여백 없이 화면 가득 */
            width: 100vw;
            margin: 0 0 6px 0;
            margin-left: calc(50% - 50vw);
            margin-right: calc(50% - 50vw);
            padding: 10px 12px 8px 12px;
            /* 하단 모서리 라운드 */
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }}
        .header-logo {{ display:flex; justify-content:center; align-items:center; width: 100%; }}
        .header-title {{ text-align:center; margin-top:2px; font-weight:800; font-size:18px; color:#ffffff; }}

        /* FAQ 3x3 그리드 (모바일 412x915 최적화) */
        .faq-grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; padding: 0 8px; margin: 4px 0 6px 0; }}
        .faq-item {{ background:#ffffff; color:#222; border:1px solid #d9dbe3; border-radius:10px; padding:10px 6px; font-size:12px; text-align:center; }}

        /* 말풍선 스타일 - 폰트 소형화 */
        .bubble-bot {{
            background: #ffffff;
            border: 1px solid #e6e8f0;
            border-radius: 14px;
            padding: 10px 12px;
            max-width: 78vw; /* 화면 기준 최대폭 조정 */
            line-height: 1.45;
            font-size: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .bubble-user {{
            background: {ORANGE};
            color: #ffffff;
            border-radius: 14px;
            padding: 10px 12px;
            max-width: 78vw; /* 화면 기준 최대폭 조정 */
            line-height: 1.45;
            font-size: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_app_state()

    logo_path = get_asset_path("img/mainlogo.png")
    user_avatar = get_asset_path("img/solbear.png")
    bot_avatar = get_asset_path("img/bikemolly.jpg")

    render_header(logo_path)
    # 헤더와 채팅 사이 퀵 액션 버튼 3개 (가로 고정)
    st.markdown("<div id='qa-row'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1], gap="small")
    with c1:
        b1 = st.button("자주묻는 질문", key="qa_btn_left", use_container_width=True)
    with c2:
        b2 = st.button("나의 문의내역", key="qa_btn_mid", use_container_width=True)
    with c3:
        b3 = st.button("기업구매문의", key="qa_btn_right", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 버튼 클릭 시 토스트: 클릭한 버튼의 텍스트를 표시
    if b1:
        st.toast("자주묻는 질문", icon="✅")
    if b2:
        st.toast("나의 문의내역", icon="✅")
    if b3:
        st.toast("기업구매문의", icon="✅")

    render_messages(user_avatar, bot_avatar)

    if prompt := st.chat_input("메시지를 입력하세요…"):
        # 사용자 메시지 추가 및 렌더
        st.session_state.messages.append({"role": "user", "content": prompt})
        _render_bubble_with_avatar(prompt, user_avatar, align="right")

        # 에이전트 호출 및 봇 메시지 추가/렌더
        with st.spinner("생각 중…"):
            bot_reply = invoke_agent(prompt)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        _render_bubble_with_avatar(bot_reply, bot_avatar, align="left")


if __name__ == "__main__":
    main()


