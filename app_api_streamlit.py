"""
땡겨요 고객응대 챗봇 (Streamlit)

이 파일은 기존 app_streamlit2.py의 UX를 참고하여 외부 API와 연동하는 
모바일 친화형 챗봇 UI입니다.

주요 기능:
- 외부 API (http://34.64.207.124:8000/agent/) 연동
- 모바일 최적화 UI (412x915 가정)
- 실시간 채팅 인터페이스
- 세션 관리 및 사용자 ID 관리 (API에서 제공)
- 가드레일 결과 표시
- 인텐트 분류 결과 표시
"""

import base64
import json
import os
import re
import html as html_lib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
from dotenv import load_dotenv


def load_image_safe(path: Path) -> Optional[bytes]:
    """지정된 경로의 이미지를 안전하게 읽어 bytes로 반환합니다."""
    try:
        if path.exists() and path.is_file():
            return path.read_bytes()
    except Exception:
        return None
    return None


def to_b64_data_uri(img_bytes: Optional[bytes], mime: str = "image/png") -> str:
    """이미지 바이트를 Base64 Data URI로 변환합니다."""
    if not img_bytes:
        return ""
    encoded = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def get_app_paths() -> Tuple[Path, Path, Path]:
    """로고/사용자 아바타/봇 아바타 파일 경로를 반환합니다."""
    root = Path(__file__).resolve().parent
    logo = root / "img" / "mainlogo.png"
    user_avatar = root / "img" / "solbear.png"
    bot_avatar = root / "img" / "bikemolly.jpg"
    return logo, user_avatar, bot_avatar


def call_api(user_text: str, user_id: str, session_id: str) -> Dict[str, Any]:
    """외부 API를 호출하여 응답을 받습니다."""
    api_url = "http://34.64.207.124:8000/agent/"
    
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "human": user_text
    }
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {e}")
        return {
            "user_id": user_id,
            "session_id": session_id,
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "guardrail_result": "FAIL",
            "intent": "ERROR"
        }


def render_loading_skeleton(bot_uri: str) -> None:
    """답변 대기 중 로딩 스켈레톤을 렌더링합니다."""
    st.markdown(
        f"""
        <div style="display: flex; justify-content: flex-start; align-items: flex-start; gap: 8px; margin-top: 20px; margin-bottom: 10px;">
          <img src="{bot_uri}" alt="bot" style="width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0;" />
          <div style="background-color: white; border: 1px solid #e6e8f0; border-radius: 16px; padding: 12px 16px; min-width: 200px; max-width: 70%;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span style="color: #6b7280; font-size: 14px;">답변을 생성하고 있습니다...</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_global_css(logo_uri: str, user_uri: str, bot_uri: str) -> None:
    """앱 전역 CSS를 삽입합니다."""
    css = f"""
    <style>
      /* ===== 전체 배경 및 레이아웃 ===== */
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

      /* ===== 헤더 영역 ===== */
      .app-header {{
        position: sticky;
        top: 0;
        z-index: 1000;
        background: #FB521C;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        padding: 14px 12px 16px 12px;
        margin: -16px -16px 4px -16px;
      }}
      .app-header-inner {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }}
      .header-logo {{
        width: 200px;
        max-width: 60vw;
        height: auto;
        display: block;
      }}
      .header-title {{
        color: #FFFFFF;
        font-weight: 700;
        font-size: 18px;
        line-height: 1.2;
        text-align: center;
      }}

      /* ===== 상태 바 영역 ===== */
      .status-bar {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #FFFFFF;
        border-top: 1px solid #e6e8f0;
        padding: 8px 16px;
        font-size: 12px;
        color: #6b7280;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 1000;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
        height: 50px;
        overflow: hidden;
      }}
      .status-item {{
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 25%;
      }}
      .status-badge {{
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
      }}
      .status-pass {{
        background: #dcfce7;
        color: #166534;
      }}
      .status-fail {{
        background: #fef2f2;
        color: #dc2626;
      }}
      .status-qna {{
        background: #dbeafe;
        color: #1e40af;
      }}
      .status-aicc {{
        background: #fef3c7;
        color: #d97706;
      }}

      /* ===== 버튼 바 영역 ===== */
      .button-bar-wrapper {{
        margin: 8px -16px 8px -16px;
        padding: 0 12px;
      }}
      .button-bar {{
        display: flex;
        flex-direction: row;
        align-items: stretch;
        justify-content: center;
        gap: 8px;
        width: 100%;
        max-width: 412px;
        margin: 0 auto;
      }}
      .button-pill {{
        flex: 1 1 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        height: 36px;
        padding: 0 10px;
        border-radius: 999px;
        border: 1px solid #D1D5DB;
        background: #FFFFFF;
        color: #111827;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 14px;
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
        background: #111827;
        color: #FFFFFF;
        border-color: #111827;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.12);
      }}

      /* ===== 로딩 애니메이션 ===== */
      .loading-dots {{
        display: flex;
        gap: 4px;
        align-items: center;
      }}
      .loading-dots span {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #d1d5db;
        animation: loading-bounce 1.4s ease-in-out infinite both;
      }}
      .loading-dots span:nth-child(1) {{
        animation-delay: -0.32s;
      }}
      .loading-dots span:nth-child(2) {{
        animation-delay: -0.16s;
      }}
      @keyframes loading-bounce {{
        0%, 80%, 100% {{
          transform: scale(0);
          opacity: 0.5;
        }}
        40% {{
          transform: scale(1);
          opacity: 1;
        }}
      }}

      /* ===== 입력창 고정 ===== */
      [data-testid="stChatInput"] {{
        position: fixed; 
        bottom: 60px;
        left: 16px;
        right: 16px;
        z-index: 1001;
      }}
      
      /* ===== 메시지 영역 하단 여백 (입력창 겹침 방지) ===== */
      .block-container {{
        padding-bottom: 120px !important;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header(logo_uri: str) -> None:
    """상단 헤더(로고 + 타이틀)를 렌더링합니다."""
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


def render_status_bar(user_id: str, session_id: str, guardrail_result: str = "", intent: str = "") -> None:
    """상태 바를 렌더링합니다."""
    guardrail_class = "status-pass" if guardrail_result == "PASS" else "status-fail"
    intent_class = "status-qna" if intent == "QNA" else "status-aicc"
    
    st.markdown(
        f"""
        <div class="status-bar">
          <div class="status-item">
            <span>사용자:</span>
            <span>{user_id}</span>
          </div>
          <div class="status-item">
            <span>세션:</span>
            <span>{session_id[:20]}...</span>
          </div>
          {f'<div class="status-item"><span>가드레일:</span><span class="status-badge {guardrail_class}">{guardrail_result}</span></div>' if guardrail_result else ''}
          {f'<div class="status-item"><span>인텐트:</span><span class="status-badge {intent_class}">{intent}</span></div>' if intent else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header_buttons() -> None:
    """헤더 아래에 가로 정렬된 3개의 버튼을 렌더링합니다."""
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
    """텍스트 내 URL을 탐지해 버튼(anchor) HTML로 치환합니다."""
    if not text:
        return ""

    button_label = "앱으로 이동"
    
    # 전체 텍스트를 먼저 이스케이프
    escaped = html_lib.escape(text)
    
    # URL 패턴 (http/https 및 커스텀 스킴)
    url_pattern = re.compile(r"(https?://[^\s]+|[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+)")

    def repl(match: re.Match) -> str:
        url = match.group(0)
        # URL은 이미 이스케이프된 상태이므로 그대로 사용
        return (
            f'<a class="deeplink-btn" href="{url}" target="_blank" rel="noopener noreferrer">{button_label}</a>'
        )

    converted = url_pattern.sub(repl, escaped)
    return converted


def render_messages(messages: List[Dict[str, str]], user_uri: str, bot_uri: str) -> None:
    """대화 메시지 목록을 렌더링합니다."""
    
    # 간격 조정 변수
    message_gap = 10  # [조정] 메시지 간 간격 (px)
    
    # 간단한 방식으로 메시지 렌더링
    for i, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        
        # 마지막 메시지인지 확인
        is_last = (i == len(messages) - 1)
        margin_bottom = "0px" if is_last else f"{message_gap}px"
        
        if role == "user":
            # 사용자 메시지 - 직접 스타일 적용
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; align-items: flex-start; gap: 8px; margin-bottom: {margin_bottom};">
                  <div style="background-color: #FF7A00; color: white; padding: 12px 16px; border-radius: 16px; max-width: 70%; word-wrap: break-word; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">{html_lib.escape(content)}</div>
                  <img src="{user_uri}" alt="me" style="width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0;" />
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # 봇 메시지 - 직접 스타일 적용
            content_html = _convert_links_to_buttons(content)
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; align-items: flex-start; gap: 8px; margin-bottom: {margin_bottom};">
                  <img src="{bot_uri}" alt="bot" style="width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0;" />
                  <div style="background-color: white; color: #111827; padding: 12px 16px; border-radius: 16px; max-width: 70%; word-wrap: break-word; border: 1px solid #e6e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">{content_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main() -> None:
    """앱의 진입점."""
    load_dotenv()
    st.set_page_config(
        page_title="땡겨요 고객문의 PoC",
        page_icon=str((Path(__file__).resolve().parent / "img" / "mainlogo.png")),
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # 세션 상태 초기화
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = ""  # API에서 받을 예정
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = ""  # API에서 받을 예정
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "안녕하세요! 땡겨요 AI 에이전트입니다. 무엇을 도와드릴까요?"}
        ]
    if "last_guardrail" not in st.session_state:
        st.session_state["last_guardrail"] = ""
    if "last_intent" not in st.session_state:
        st.session_state["last_intent"] = ""
    if "is_loading" not in st.session_state:
        st.session_state["is_loading"] = False

    # 이미지 로드
    logo_path, user_path, bot_path = get_app_paths()
    logo_uri = to_b64_data_uri(load_image_safe(logo_path), mime="image/png")
    user_uri = to_b64_data_uri(load_image_safe(user_path), mime="image/png")
    bot_uri = to_b64_data_uri(load_image_safe(bot_path), mime="image/jpeg")

    # UI 렌더링
    render_global_css(logo_uri, user_uri, bot_uri)
    render_header(logo_uri)
    render_header_buttons()
    render_messages(st.session_state["messages"], user_uri, bot_uri)
    
    # 로딩 중일 때 스켈레톤 표시
    if st.session_state["is_loading"]:
        render_loading_skeleton(bot_uri)
    
    # 상태 바를 메시지 영역 아래, 입력창 위에 표시
    render_status_bar(
        st.session_state["user_id"], 
        st.session_state["session_id"],
        st.session_state["last_guardrail"],
        st.session_state["last_intent"]
    )

    # 사용자 입력 처리
    user_text = st.chat_input("메시지를 입력하세요")
    if user_text:
        # 즉시 사용자 메시지 추가 및 화면 업데이트
        st.session_state["messages"].append({"role": "user", "content": user_text})
        st.session_state["is_loading"] = True
        st.rerun()
    
    # 로딩 상태에서 API 호출 처리
    if st.session_state["is_loading"] and len(st.session_state["messages"]) > 0:
        # 마지막 메시지가 사용자 메시지인지 확인
        last_message = st.session_state["messages"][-1]
        if last_message["role"] == "user":
            # API 호출
            api_response = call_api(
                last_message["content"], 
                st.session_state["user_id"], 
                st.session_state["session_id"]
            )
            
            # API 응답에서 user_id와 session_id 업데이트
            if api_response.get("user_id"):
                st.session_state["user_id"] = api_response["user_id"]
            if api_response.get("session_id"):
                st.session_state["session_id"] = api_response["session_id"]
            
            # 봇 응답 추가
            bot_reply = api_response.get("response", "죄송합니다. 응답을 받지 못했습니다.")
            st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
            
            # 상태 업데이트
            st.session_state["last_guardrail"] = api_response.get("guardrail_result", "")
            st.session_state["last_intent"] = api_response.get("intent", "")
            
            # 로딩 상태 해제
            st.session_state["is_loading"] = False
            st.rerun()


if __name__ == "__main__":
    main()
