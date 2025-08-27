from typing import Dict

SENSITIVE_KEYWORDS = ["환불", "결제 오류", "계정 잠김", "개인정보", "법적", "분쟁"]


def run_human_filter_agent(state: Dict) -> Dict:
    """Human 상담사 전달을 위한 필터링/요약 에이전트(간단 규칙 기반).
    - 민감 키워드 탐지 시 에스컬레이션 권고 문구와 요약 제공.
    - 실제로는 PII 마스킹, 요약/태깅, 우선순위 산정 등을 수행.
    """
    user_input: str = state.get("user_input", "")
    lowered = user_input.lower()

    flagged = any(kw.lower() in lowered for kw in SENSITIVE_KEYWORDS)
    if flagged:
        state["response"] = (
            "민감/복잡 이슈로 판단되어 상담사 연결이 권장됩니다.\n"
            f"- 고객 메시지 요약: '{user_input[:120]}' ...\n"
            "- 처리 가이드: 고객 본인확인, 결제/환불 정책 확인, 필요한 경우 추가 증빙 요청"
        )
    else:
        state["response"] = (
            "상담사 검토 대상은 아니지만, 필요 시 연결 가능합니다.\n"
            f"- 고객 메시지 요약: '{user_input[:120]}' ..."
        )
    return state
