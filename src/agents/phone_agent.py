import os
from typing import Dict


def run_phone_agent(state: Dict) -> Dict:
    """전화 연결(시뮬레이션) 에이전트.
    - 실제로는 CTI/콜센터 API 와 연동하여 콜 큐 투입, 콜백 예약 등을 수행.
    - 여기서는 안내 문구와 가상의 티켓ID를 반환.
    """
    user_input: str = state.get("user_input", "")
    api_base = os.getenv("TELEPHONY_API_BASE", "(설정되지 않음)")
    fake_ticket_id = f"TICKET-{abs(hash(user_input)) % 10_000:04d}"
    response = (
        "전화 상담 요청을 접수했습니다. 곧 상담사가 연락드립니다.\n"
        f"- 연동 API: {api_base}\n- 접수번호: {fake_ticket_id}"
    )
    state["response"] = response
    return state
