from typing import Dict, Literal, Tuple

INTENTS = Literal["rag", "phone", "app", "human"]

# 매우 단순한 키워드 기반 분류기. 실제로는 분류 모델/프롬프트 분류를 권장.
KEYWORDS = {
    "phone": ["전화", "통화", "상담 전화", "콜", "연락"],
    "app": ["버튼", "앱", "바로가기", "링크", "열기", "이동"],
    "human": ["상담사", "사람", "직원", "연결", "에스컬레이션"],
}


def classify_intent(user_input: str) -> INTENTS:
    lowered = user_input.lower()
    for intent, words in KEYWORDS.items():
        for w in words:
            if w.lower() in lowered:
                return intent  # type: ignore
    return "rag"  # 기본값


def need_style(user_input: str) -> bool:
    # 느낌표/반말/무응답 등을 고려해 일괄적으로 적용하도록 기본 True
    return True


def route(state: Dict) -> Dict:
    """그래프 첫 단계: 의도 분류 및 스타일 적용 여부 결정."""
    user_input = state.get("user_input", "")
    intent: INTENTS = classify_intent(user_input)
    state["intent"] = intent
    state["apply_style"] = need_style(user_input)
    return state
