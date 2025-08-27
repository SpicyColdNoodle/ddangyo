import os
from typing import Dict
from urllib.parse import quote


def run_app_button_agent(state: Dict) -> Dict:
    """앱 버튼/딥링크 연동(시뮬레이션) 에이전트.
    - 실제 앱 내 특정 화면을 여는 딥링크를 생성하여 안내.
    - 여기서는 기본 BASE + path + 쿼리를 구성.
    """
    user_input: str = state.get("user_input", "")
    base = os.getenv("APP_DEEPLINK_BASE", "myapp://action")
    path = "open"
    q = quote(user_input)
    deeplink = f"{base}/{path}?q={q}"
    state["response"] = (
        "앱에서 바로 진행할 수 있는 버튼을 생성했습니다.\n"
        f"- 딥링크: {deeplink}\n"
        "앱에서 링크를 열면 관련 작업 화면으로 이동합니다."
    )
    return state
