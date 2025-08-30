"""
땡겨요 고객응대 챗봇 (Streamlit) - URL 버튼 버전

이 파일은 기존 app_streamlit2.py의 UX를 참고하여 외부 API와 연동하는 
모바일 친화형 챗봇 UI입니다.

주요 기능:
- 외부 API (http://34.64.207.124:8000/agent/) 연동
- 모바일 최적화 UI (412x915 가정)
- 실시간 채팅 인터페이스
- 세션 관리 및 사용자 ID 관리 (API에서 제공)
- 가드레일 결과 표시
- 인텐트 분류 결과 표시
- 감정 분석 결과 표시
- 최초 진입 시 인사 메시지 아래에 5개의 샘플 질문 제시
- 샘플 질문 클릭 시 해당 텍스트로 질문
- API 응답의 res.refUrl을 기반으로 답변 말풍선에 버튼 렌더링
- 복수의 URL에 대응하여 여러 버튼 생성

개발자: AI Assistant
버전: 1.0
최종 수정일: 2024년
"""

import base64
import json
import re
import html as html_lib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

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


def load_recommendations() -> List[Dict[str, Any]]:
    """추천 질문 목록을 JSON 파일에서 로드합니다."""
    try:
        recommendations_file = Path(__file__).resolve().parent / "recommendations.json"
        if recommendations_file.exists():
            with open(recommendations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("recommendations", [])
        else:
            st.warning("추천 질문 파일을 찾을 수 없습니다.")
            return []
    except Exception as e:
        st.error(f"추천 질문 로드 오류: {e}")
        return []


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
        api_response = response.json()
        
        # 모든 응답에 refUrl 필드 추가 (기본값: 빈 리스트)
        if "refUrl" not in api_response:
            api_response["refUrl"] = []
        
        # 테스트용: 특정 키워드 포함 시 가상의 refUrl 추가
        if "버튼테스트1234" in user_text:
            # URL 패턴 테스트를 위한 다양한 URL들
            test_urls = [
                "https://support.example.com/call",      # 1:1 고객문의
                "https://www.ddanggyeo.com/faq",         # 자주묻는 질문
                "https://help.ddanggyeo.com/guide",      # 이용가이드
                "https://www.ddanggyeo.com/order",       # 주문조회
                "https://app.ddanggyeo.com/download"     # 앱 다운로드
            ]
            
            # URL 유효성 검사
            valid_urls = []
            for url in test_urls:
                try:
                    parsed = urlparse(url)
                    if parsed.scheme and parsed.netloc:
                        valid_urls.append(url)
                    else:
                        st.warning(f"잘못된 URL 형식: {url}")
                except Exception as e:
                    st.warning(f"URL 파싱 오류: {url} - {e}")
            
            api_response["refUrl"] = valid_urls
            
            # 디버깅용 로그
            if valid_urls:
                st.info(f"테스트 URL 추가됨: {len(valid_urls)}개 - {valid_urls}")
        
        return api_response
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {e}")
        return {
            "user_id": user_id,
            "session_id": session_id,
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "guardrail_result": "FAIL",
            "intent": "ERROR",
            "sentiment": "NEUTRAL",
            "refUrl": []  # 오류 시 빈 URL 리스트
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
      .status-positive {{
        background: #d1fae5;
        color: #065f46;
      }}
      .status-negative {{
        background: #fee2e2;
        color: #991b1b;
      }}
      .status-neutral {{
        background: #f3f4f6;
        color: #4b5563;
      }}

      /* ===== 버튼 바 영역 ===== */
      .button-bar-wrapper {{
        margin: 8px -16px 24px -16px;
        padding: 0 30px;
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

       /* ===== 샘플 질문 영역 ===== */
       .sample-questions-container {{
         margin: 16px 0; /* [조정] 컨테이너 상하 여백 (px) */
         padding: 0;
         background: transparent;
         border: none;
         box-shadow: none;
       }}
       .sample-questions-grid {{
         display: flex;
         flex-direction: column;
         gap: 8px; /* [조정] 샘플 질문 간 간격 (px) - 더 가깝게 조절 가능 */
         margin: 0;
         padding: 0;
       }}
       /* Streamlit 버튼 스타일 오버라이드 */
       .sample-questions-grid button {{
         width: 100% !important;
         padding: 14px 16px !important; /* [조정] 버튼 내부 여백 (상하 좌우) */
         background: white !important;
         border: 1px solid #e2e8f0 !important;
         border-radius: 12px !important; /* [조정] 버튼 모서리 둥글기 (px) */
         color: #334155 !important;
         font-size: 14px !important; /* [조정] 버튼 텍스트 크기 (px) */
         font-weight: 500 !important;
         text-align: left !important;
         cursor: pointer !important;
         transition: all 0.2s ease !important;
         box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
         margin: 0 !important;
         line-height: 1.4 !important; /* [조정] 텍스트 줄 간격 */
       }}
       .sample-questions-grid button:hover {{
         border-color: #FF7A00 !important; /* [조정] 호버 시 테두리 색상 */
         background: #fff7ed !important; /* [조정] 호버 시 배경 색상 */
         transform: translateY(-2px) !important; /* [조정] 호버 시 위로 이동 거리 (px) */
         box-shadow: 0 6px 16px rgba(255, 122, 0, 0.2) !important; /* [조정] 호버 시 그림자 */
       }}
       .sample-questions-grid button:active {{
         transform: translateY(0) !important; /* [조정] 클릭 시 원래 위치로 */
         box-shadow: 0 2px 8px rgba(255, 122, 0, 0.15) !important; /* [조정] 클릭 시 그림자 */
       }}

       /* ===== URL 버튼 영역 ===== */
       .url-buttons-container {{
         margin-top: 12px;
         display: flex;
         flex-direction: column;
         gap: 8px;
       }}
       .url-button {{
         display: inline-block;
         padding: 12px 18px;
         background: #FF7A00;
         color: white !important;
         text-decoration: none !important;
         border-radius: 10px;
         font-size: 14px;
         font-weight: 600;
         text-align: center;
         transition: all 0.2s ease;
         box-shadow: 0 2px 6px rgba(255, 122, 0, 0.25);
         border: none;
         cursor: pointer;
         max-width: 100%;
         word-wrap: break-word;
         letter-spacing: 0.5px;
       }}
       .url-button:hover {{
         background: #e66a00;
         transform: translateY(-2px);
         box-shadow: 0 6px 12px rgba(255, 122, 0, 0.35);
         text-decoration: none !important;
         color: white !important;
       }}
       .url-button:active {{
         transform: translateY(0);
         box-shadow: 0 2px 4px rgba(255, 122, 0, 0.2);
         color: white !important;
       }}
       .url-button:link, .url-button:visited {{
         color: white !important;
         text-decoration: none !important;
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


def render_status_bar(user_id: str, session_id: str, guardrail_result: str = "", intent: str = "", sentiment: str = "") -> None:
    """상태 바를 렌더링합니다."""
    guardrail_class = "status-pass" if guardrail_result == "PASS" else "status-fail"
    intent_class = "status-qna" if intent == "QNA" else "status-aicc"
    
    # 감정 분석 클래스 결정
    if sentiment == "POSITIVE":
        sentiment_class = "status-positive"
    elif sentiment == "NEGATIVE":
        sentiment_class = "status-negative"
    else:
        sentiment_class = "status-neutral"
    
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
          {f'<div class="status-item"><span>감정:</span><span class="status-badge {sentiment_class}">{sentiment}</span></div>' if sentiment else ''}
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


def render_sample_questions() -> None:
    """샘플 질문 5개를 렌더링합니다."""
    recommendations = load_recommendations()
    
    if not recommendations:
        return
    
    # 샘플 질문 컨테이너 시작
    st.markdown("""
    <div class="sample-questions-container">
      <div class="sample-questions-grid">
    """, unsafe_allow_html=True)
    
    # 각 샘플 질문을 렌더링
    for rec in recommendations:
        if st.button(
            rec["question"], 
            key=f"sample_{rec['id']}", 
            help=f"클릭하면 '{rec['question']}' 질문이 입력됩니다"
        ):
            # 버튼 클릭 시 입력창에 질문 설정
            st.session_state["pending_question"] = rec["question"]
            st.rerun()
    
    # 샘플 질문 컨테이너 종료
    st.markdown("""
      </div>
    </div>
    """, unsafe_allow_html=True)


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


def get_button_text_from_url(url: str) -> str:
    """URL 패턴에 따라 버튼 텍스트를 결정합니다."""
    # URL 패턴별 버튼 텍스트 매핑 규칙
    url_patterns = {
        # 고객 지원 관련
        "support": "1:1 고객문의",
        "help": "도움말",
        "faq": "자주묻는 질문",
        "contact": "연락처",
        "call": "전화상담",
        
        # 서비스 관련
        "service": "서비스 안내",
        "guide": "이용가이드",
        "manual": "매뉴얼",
        "tutorial": "튜토리얼",
        
        # 주문/결제 관련
        "order": "주문조회",
        "payment": "결제관리",
        "billing": "청구서",
        "invoice": "영수증",
        
        # 계정 관련
        "account": "계정관리",
        "profile": "프로필",
        "settings": "설정",
        "preferences": "환경설정",
        
        # 앱 관련
        "app": "앱 다운로드",
        "download": "다운로드",
        "install": "설치",
        
        # 기타
        "terms": "이용약관",
        "privacy": "개인정보처리방침",
        "notice": "공지사항",
        "news": "뉴스",
        "blog": "블로그"
    }
    
    # URL을 소문자로 변환하여 패턴 매칭
    url_lower = url.lower()
    
    # 패턴 매칭 (가장 구체적인 패턴부터 검사)
    for pattern, button_text in url_patterns.items():
        if pattern in url_lower:
            return button_text  # 🔗 이모지 제거
    
    # 패턴이 매칭되지 않으면 도메인 기반 텍스트 생성
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme and parsed_url.netloc:
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain  # 🔗 이모지 제거
        else:
            return "링크"  # 🔗 이모지 제거
    except Exception:
        return "링크"  # 🔗 이모지 제거

def render_url_buttons(ref_urls: List[str]) -> str:
    """refUrl 리스트를 기반으로 URL 버튼들을 렌더링합니다."""
    if not ref_urls:
        return ""
    
    # URL 리스트 유효성 검사
    if not isinstance(ref_urls, list):
        st.error("refUrl이 리스트 형식이 아닙니다.")
        return ""
    
    buttons_html = '<div class="url-buttons-container">'
    
    for i, url in enumerate(ref_urls):
        # URL 문자열 유효성 검사
        if not isinstance(url, str) or not url.strip():
            st.warning(f"잘못된 URL 형식 (인덱스 {i}): {url}")
            continue
        
        url = url.strip()
        
        # URL 패턴에 따른 버튼 텍스트 생성
        button_text = get_button_text_from_url(url)
        
        # HTML 이스케이프 처리
        safe_url = html_lib.escape(url)
        safe_button_text = html_lib.escape(button_text)
        
        buttons_html += f'''
        <a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="url-button">
          {safe_button_text}
        </a>
        '''
    
    buttons_html += '</div>'
    return buttons_html


def render_messages(messages: List[Dict[str, str]], user_uri: str, bot_uri: str) -> None:
    """대화 메시지 목록을 렌더링합니다."""
    
    # 간격 조정 변수
    message_gap = 10  # [조정] 메시지 간 간격 (px)
    
    # 간단한 방식으로 메시지 렌더링
    for i, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        ref_urls = msg.get("refUrl", [])  # refUrl 필드 추가
        
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
            
            # URL 버튼들 렌더링
            url_buttons_html = render_url_buttons(ref_urls)
            
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; align-items: flex-start; gap: 8px; margin-bottom: {margin_bottom};">
                  <img src="{bot_uri}" alt="bot" style="width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0;" />
                  <div style="background-color: white; color: #111827; padding: 12px 16px; border-radius: 16px; max-width: 70%; word-wrap: break-word; border: 1px solid #e6e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    {content_html}
                    {url_buttons_html}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main() -> None:
    """앱의 진입점."""
    load_dotenv()
    st.set_page_config(
        page_title="땡겨요 고객문의 PoC - URL 버튼",
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
    if "last_sentiment" not in st.session_state:
        st.session_state["last_sentiment"] = ""
    if "is_loading" not in st.session_state:
        st.session_state["is_loading"] = False
    if "show_samples" not in st.session_state:
        st.session_state["show_samples"] = True  # 처음에만 샘플 질문 표시
    if "pending_question" not in st.session_state:
        st.session_state["pending_question"] = None

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
    
    # 처음 진입 시에만 샘플 질문 표시
    if st.session_state["show_samples"] and len(st.session_state["messages"]) == 1:
        render_sample_questions()
    
    # 로딩 중일 때 스켈레톤 표시
    if st.session_state["is_loading"]:
        render_loading_skeleton(bot_uri)
    
    # 상태 바를 메시지 영역 아래, 입력창 위에 표시
    render_status_bar(
        st.session_state["user_id"], 
        st.session_state["session_id"],
        st.session_state["last_guardrail"],
        st.session_state["last_intent"],
        st.session_state["last_sentiment"]
    )

    # 사용자 입력 처리
    user_text = st.chat_input("메시지를 입력하세요")
    
    # Handle pending question from sample buttons
    if st.session_state.get("pending_question"):
        user_text = st.session_state["pending_question"]
        st.session_state["pending_question"] = None  # Clear pending question
    
    if user_text:
        # 즉시 사용자 메시지 추가 및 화면 업데이트
        st.session_state["messages"].append({"role": "user", "content": user_text})
        st.session_state["is_loading"] = True
        
        # 샘플 질문 숨기기 (첫 번째 사용자 메시지 후)
        if st.session_state["show_samples"]:
            st.session_state["show_samples"] = False
        
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
            
            # 봇 응답 추가 (refUrl 포함)
            bot_reply = api_response.get("response", "죄송합니다. 응답을 받지 못했습니다.")
            ref_urls = api_response.get("refUrl", [])  # refUrl 필드 추가
            
            st.session_state["messages"].append({
                "role": "assistant", 
                "content": bot_reply,
                "refUrl": ref_urls  # refUrl을 메시지에 포함
            })
            
            # 상태 업데이트
            st.session_state["last_guardrail"] = api_response.get("guardrail_result", "")
            st.session_state["last_intent"] = api_response.get("intent", "")
            st.session_state["last_sentiment"] = api_response.get("sentiment", "NEUTRAL")
            
            # 로딩 상태 해제
            st.session_state["is_loading"] = False
            st.rerun()


if __name__ == "__main__":
    main()
