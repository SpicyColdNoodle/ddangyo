from typing import Dict


def apply_style(state: Dict) -> Dict:
    """최종 응답에 공손하고 명확한 한국어 화법을 적용(간단 규칙 기반)."""
    text = state.get("response") or ""
    if not text:
        state["final_text"] = "죄송합니다. 현재 드릴 수 있는 답변이 없습니다."
        return state

    styled = (
        "안녕하세요. 문의 주셔서 감사합니다.\n"
        f"{text}\n\n"
        "추가로 도움이 필요하시면 언제든지 말씀해 주세요."
    )
    state["final_text"] = styled
    return state
