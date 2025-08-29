"""
땡겨요 고객응대 챗봇 (Streamlit)

이 파일은 기존 app_streamlit2.py의 UX를 참고하여 외부 API와 연동하는 
모바일 친화형 챗봇 UI입니다.

주요 기능:
- 외부 API (http://34.64.207.124:8000/agent/) 연동
- 모바일 최적화 UI (412x915 가정)
- 실시간 채팅 인터페이스
- 세션 관리 및 사용자 ID 관리
- 가드레일 결과 표시
- 인텐트 분류 결과 표시
"""

import base64
import json
import os
import re
import html as html_lib
import uuid
from datetime import datetime
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


def generate_session_id() -> str:
    """고유한 세션 ID를 생성합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"


def generate_user_id() -> str:
    """고유한 사용자 ID를 생성합니다."""
    return f"user_{str(uuid.uuid4())[:8]}"


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


def render_global_css(logo_uri: str, user_uri: str, bot_uri: str) -> None:
    """앱 전역 CSS를 삽입합니다.
    
    주요 조정 포인트:
    - 전체 배경색: `background: #f5f6f8`
    - 헤더 스타일: `.app-header` 내 background, padding, margin, border-radius
    - 로고 크기: `.header-logo`의 width, max-width
    - 제목 스타일: `.header-title`의 color, font-size, font-weight
    - 상태 바: `.status-bar`의 background, padding, font-size
    - 버튼 바 레이아웃: `.button-bar`의 gap, max-width
    - 버튼 스타일: `.button-pill`의 height, padding, border, background, color
    - 말풍선 간격: `.chat-container`의 gap (현재 12px)
    - 말풍선 스타일: `.bubble-user`, `.bubble-bot`의 색상과 여백
    - 아바타 크기: `.avatar`의 width/height (현재 48px)
    - 입력창 위치: `[data-testid="stChatInput"]`의 bottom, left, right
    """
    css = f"""
    <style>
      /* ===== 전체 배경 및 레이아웃 ===== */
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background: #f5f6f8 !important;  /* [조정] 전체 배경색 */
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
        background: #FB521C;                    /* [조정] 헤더 배경색 */
        border-bottom-left-radius: 12px;        /* [조정] 헤더 하단 왼쪽 둥근 모서리 */
        border-bottom-right-radius: 12px;       /* [조정] 헤더 하단 오른쪽 둥근 모서리 */
        padding: 14px 12px 16px 12px;          /* [조정] 헤더 내부 여백 (위/우/아래/좌) */
        margin: -16px -16px 4px -16px;         /* [조정] 헤더 외부 여백 (위/우/아래/좌) */
      }}
      .app-header-inner {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;                              /* [조정] 헤더 내부 요소 간 간격 */
      }}
      .header-logo {{
        width: 200px;                          /* [조정] 로고 기본 폭 */
        max-width: 60vw;                       /* [조정] 로고 최대 폭 (뷰포트 대비) */
        height: auto;
        display: block;
      }}
      .header-title {{
        color: #FFFFFF;                        /* [조정] 헤더 제목 글자색 */
        font-weight: 700;                      /* [조정] 헤더 제목 글자 굵기 */
        font-size: 18px;                       /* [조정] 헤더 제목 글자 크기 */
        line-height: 1.2;                      /* [조정] 헤더 제목 줄 간격 */
        text-align: center;
      }}

      /* ===== 상태 바 영역 ===== */
      .status-bar {{
        position: fixed;                       /* [조정] 상태 바 고정 위치 */
        bottom: 0;                             /* [조정] 상태 바 최하단 위치 */
        left: 0;                               /* [조정] 상태 바 전체 너비 */
        right: 0;                              /* [조정] 상태 바 전체 너비 */
        background: #FFFFFF;                    /* [조정] 상태 바 배경색 */
        border-top: 1px solid #e6e8f0;         /* [조정] 상태 바 상단 테두리 */
        padding: 8px 16px;                     /* [조정] 상태 바 내부 여백 (위아래/좌우) */
        font-size: 12px;                       /* [조정] 상태 바 기본 글자 크기 */
        color: #6b7280;                        /* [조정] 상태 바 기본 글자색 */
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 1000;                         /* [조정] 상태 바 레이어 순서 */
        box-shadow: 0 -2px 8px rgba(0,0,0,0.1); /* [조정] 상태 바 그림자 (위쪽) */
        height: 50px;                          /* [조정] 상태 바 고정 높이 */
        overflow: hidden;                      /* [조정] 내용이 넘치면 숨김 */
      }}
      .status-item {{
        display: flex;
        align-items: center;
        gap: 4px;                              /* [조정] 상태 항목 내부 간격 */
        white-space: nowrap;                   /* [조정] 텍스트 줄바꿈 방지 */
        overflow: hidden;                      /* [조정] 넘치는 내용 숨김 */
        text-overflow: ellipsis;               /* [조정] 넘치는 텍스트 ... 표시 */
        max-width: 25%;                        /* [조정] 각 항목 최대 너비 */
      }}
      .status-badge {{
        padding: 2px 6px;                      /* [조정] 상태 배지 내부 여백 (위아래/좌우) */
        border-radius: 4px;                    /* [조정] 상태 배지 둥근 모서리 */
        font-size: 10px;                       /* [조정] 상태 배지 글자 크기 */
        font-weight: 600;                      /* [조정] 상태 배지 글자 굵기 */
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
        margin: 8px -16px 8px -16px;          /* [조정] 버튼 바 외부 여백 (위/우/아래/좌) */
        padding: 0 12px;                       /* [조정] 버튼 바 내부 여백 (좌우) */
      }}
      .button-bar {{
        display: flex;
        flex-direction: row;
        align-items: stretch;
        justify-content: center;
        gap: 8px;                              /* [조정] 버튼 간 간격 */
        width: 100%;
        max-width: 412px;                      /* [조정] 버튼 바 최대 폭 (모바일 기준) */
        margin: 0 auto;
      }}
      .button-pill {{
        flex: 1 1 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        height: 36px;                          /* [조정] 버튼 높이 */
        padding: 0 10px;                       /* [조정] 버튼 내부 여백 (좌우) */
        border-radius: 999px;                  /* [조정] 버튼 둥근 모서리 */
        border: 1px solid #D1D5DB;            /* [조정] 버튼 테두리 색상 */
        background: #FFFFFF;                   /* [조정] 버튼 배경색 */
        color: #111827;                        /* [조정] 버튼 글자색 */
        text-decoration: none !important;
        font-weight: 600;                      /* [조정] 버튼 글자 굵기 */
        font-size: 14px;                       /* [조정] 버튼 글자 크기 */
        box-shadow: 0 1px 2px rgba(0,0,0,0.06); /* [조정] 버튼 그림자 */
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
        background: #111827;                   /* [조정] 버튼 눌렀을 때 배경색 */
        color: #FFFFFF;                        /* [조정] 버튼 눌렀을 때 글자색 */
        border-color: #111827;                 /* [조정] 버튼 눌렀을 때 테두리색 */
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.12);
      }}
      @media (max-width: 420px) {{
        /* ===== 모바일 전용 조정 ===== */
        .button-pill {{
          font-size: 13px;                     /* [조정] 모바일 버튼 글자 크기 */
          height: 34px;                        /* [조정] 모바일 버튼 높이 */
          padding: 0 8px;                      /* [조정] 모바일 버튼 내부 여백 */
        }}
        .button-bar {{
          gap: 6px;                            /* [조정] 모바일 버튼 간 간격 */
          max-width: 100%;                     /* [조정] 모바일 버튼 바 최대 폭 */
        }}
        
        /* ===== 모바일 말풍선 조정 ===== */
        .chat-container {{
          gap: 12px;                           /* [조정] 모바일 말풍선 간격 */
        }}
        .bubble {{
          max-width: 85vw;                     /* [조정] 모바일 말풍선 최대 폭 */
          padding: 10px 12px;                  /* [조정] 모바일 말풍선 내부 여백 */
          font-size: 13px;                     /* [조정] 모바일 말풍선 글자 크기 */
        }}
        .avatar {{
          width: 40px;                         /* [조정] 모바일 아바타 크기 */
          height: 40px;                        /* [조정] 모바일 아바타 크기 */
          flex: 0 0 40px;                      /* [조정] 모바일 아바타 고정 크기 */
        }}
        .bubble-user {{
          margin-left: 40px;                   /* [조정] 모바일 사용자 말풍선 여백 */
        }}
        .bubble-bot {{
          margin-right: 40px;                  /* [조정] 모바일 봇 말풍선 여백 */
        }}
      }}

      /* ===== 채팅 영역 ===== */
      .msg-row {{ 
        display: flex; 
        gap: 8px;                              /* [조정] 메시지 행 내부 간격 */
        align-items: flex-start; 
        margin-bottom: 16px;                   /* [조정] 메시지 행 간 세로 간격 */
      }}
      .msg-row:last-child {{
        margin-bottom: 0;                      /* 마지막 메시지는 하단 여백 제거 */
      }}
      .msg-row.bot {{ justify-content: flex-start; }}
      .msg-row.user {{ justify-content: flex-end; }}
      .avatar {{
        width: 48px;                           /* [조정] 아바타 크기 */
        height: 48px;                          /* [조정] 아바타 크기 */
        border-radius: 50%;                    /* [조정] 아바타 둥근 모서리 */
        object-fit: cover; 
        flex: 0 0 48px;
      }}
      .bubble {{
        max-width: 78vw;                       /* [조정] 말풍선 최대 폭 (뷰포트 대비) */
        padding: 12px 16px;                    /* [조정] 말풍선 내부 여백 (위아래/좌우) */
        border-radius: 16px;                   /* [조정] 말풍선 둥근 모서리 */
        line-height: 1.5;                      /* [조정] 말풍선 줄 간격 */
        font-size: 14px;                       /* [조정] 말풍선 글자 크기 */
        word-wrap: break-word;
        white-space: pre-wrap;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); /* [조정] 말풍선 그림자 */
      }}
      .bubble-user {{
        background: #FF7A00;                   /* [조정] 사용자 말풍선 배경색 */
        color: #FFFFFF;                        /* [조정] 사용자 말풍선 글자색 */
        margin-left: 48px;                     /* [조정] 사용자 말풍선 왼쪽 여백 */
      }}
      .bubble-bot {{
        background: #FFFFFF;                   /* [조정] 봇 말풍선 배경색 */
        color: #111827;                        /* [조정] 봇 말풍선 글자색 */
        border: 1px solid #e6e8f0;            /* [조정] 봇 말풍선 테두리 */
        margin-right: 48px;                    /* [조정] 봇 말풍선 오른쪽 여백 */
      }}
      .bubble-bot .deeplink-btn {{
        display: inline-flex;
        align-items: center; 
        justify-content: center;
        height: 30px;                          /* [조정] 딥링크 버튼 높이 */
        padding: 0 10px;                       /* [조정] 딥링크 버튼 내부 여백 */
        margin-top: 6px;                       /* [조정] 딥링크 버튼 위 여백 */
        border: 1px solid #FF7A00;            /* [조정] 딥링크 버튼 테두리 */
        border-radius: 10px;                   /* [조정] 딥링크 버튼 둥근 모서리 */
        background: #FF7A00;                   /* [조정] 딥링크 버튼 배경색 */
        color: #FFFFFF;                        /* [조정] 딥링크 버튼 글자색 */
        font-weight: 500;                      /* [조정] 딥링크 버튼 글자 굵기 */
        font-size: 13px;                       /* [조정] 딥링크 버튼 글자 크기 */
        text-decoration: none !important; 
        white-space: nowrap;
      }}
      .bubble-bot .deeplink-btn:active {{
        filter: brightness(0.95);              /* [조정] 딥링크 버튼 눌렀을 때 밝기 */
      }}

      /* ===== 입력창 고정 ===== */
      [data-testid="stChatInput"] {{
        position: fixed; 
        bottom: 60px;                          /* [조정] 입력창 하단 여백 (상태 바 높이 50px + 여백 10px) */
        left: 16px;                            /* [조정] 입력창 왼쪽 여백 */
        right: 16px;                           /* [조정] 입력창 오른쪽 여백 */
        z-index: 1001;                         /* [조정] 입력창 레이어 순서 (상태 바보다 위) */
      }}
            
      /* ===== 메시지 영역 하단 여백 (입력창 겹침 방지) ===== */
      .block-container {{
        padding-bottom: 120px !important;      /* [조정] 메시지 영역 하단 여백 (입력창 높이 + 여유) */
      }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header(logo_uri: str) -> None:
    """상단 헤더(로고 + 타이틀)를 렌더링합니다.
    
    변경 팁:
    - 로고 크기/타이틀 크기: 전역 CSS의 `.header-logo`, `.header-title`를 조정하세요.
    - 헤더 배경색/둥근 모서리/여백: `.app-header`를 조정하세요.
    - 제목 텍스트: 아래 HTML의 "땡겨요 1:1 고객문의" 텍스트를 변경하세요.
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


def render_status_bar(user_id: str, session_id: str, guardrail_result: str = "", intent: str = "") -> None:
    """상태 바를 렌더링합니다.
    
    표시 정보:
    - 사용자 ID: 고유한 사용자 식별자
    - 세션 ID: 현재 대화 세션 (축약형으로 표시)
    - 가드레일 결과: PASS/FAIL (색상 구분)
    - 인텐트 분류: QNA/AICC (색상 구분)
    
    변경 팁:
    - 상태 바 스타일: 전역 CSS의 `.status-bar`, `.status-badge`를 조정하세요.
    - 색상 구분: `.status-pass`, `.status-fail`, `.status-qna`, `.status-aicc`를 조정하세요.
    """
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
    """앱의 진입점.
    
    주요 기능:
    - 환경 설정 및 페이지 구성
    - 세션 상태 초기화 (사용자 ID, 세션 ID, 메시지 히스토리)
    - 이미지 로드 및 UI 렌더링
    - 사용자 입력 처리 및 API 연동
    
    자주 바꾸는 설정:
    - 페이지 제목: `st.set_page_config(page_title=...)`
    - 페이지 아이콘: `page_icon` 경로 변경 가능
    - 초기 메시지: `st.session_state["messages"]`의 초기값 변경
    - 레이아웃: `layout="wide"` → 필요시 `"centered"`
    - API URL: `call_api` 함수 내 `api_url` 변경
    """
    load_dotenv()
    st.set_page_config(
        page_title="땡겨요 고객문의 PoC",
        page_icon=str((Path(__file__).resolve().parent / "img" / "mainlogo.png")),
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # 세션 상태 초기화
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = generate_user_id()
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = generate_session_id()
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "안녕하세요! 땡겨요 AI 에이전트입니다. 무엇을 도와드릴까요?"}
        ]
    if "last_guardrail" not in st.session_state:
        st.session_state["last_guardrail"] = ""
    if "last_intent" not in st.session_state:
        st.session_state["last_intent"] = ""

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
        # 사용자 메시지 추가
        st.session_state["messages"].append({"role": "user", "content": user_text})
        
        # API 호출
        api_response = call_api(
            user_text, 
            st.session_state["user_id"], 
            st.session_state["session_id"]
        )
        
        # 봇 응답 추가
        bot_reply = api_response.get("response", "죄송합니다. 응답을 받지 못했습니다.")
        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        
        # 상태 업데이트
        st.session_state["last_guardrail"] = api_response.get("guardrail_result", "")
        st.session_state["last_intent"] = api_response.get("intent", "")
        
        st.rerun()


if __name__ == "__main__":
    main()

