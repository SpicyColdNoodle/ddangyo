from typing import Dict
from langgraph.graph import StateGraph, END

from src.router import route
from src.agents.rag_agent import run_rag_agent
from src.agents.phone_agent import run_phone_agent
from src.agents.app_button_agent import run_app_button_agent
from src.agents.human_filter_agent import run_human_filter_agent
from src.style_agent import apply_style


def build_graph():
    """LangGraph 상태 그래프 구성.
    노드:
      - route: 의도 분류 및 스타일 여부 결정
      - rag/phone/app/human: 각 모듈 실행
      - style(optional): 화법 적용
    """
    graph = StateGraph(dict)

    # 노드 등록
    graph.add_node("route", route)
    graph.add_node("rag", run_rag_agent)
    graph.add_node("phone", run_phone_agent)
    graph.add_node("app", run_app_button_agent)
    graph.add_node("human", run_human_filter_agent)
    graph.add_node("style", apply_style)

    # 시작 노드
    graph.set_entry_point("route")

    # 분기: route -> intent 별 노드
    def decide_after_route(state: Dict) -> str:
        intent = state.get("intent")
        if intent == "phone":
            return "phone"
        if intent == "app":
            return "app"
        if intent == "human":
            return "human"
        return "rag"

    graph.add_conditional_edges("route", decide_after_route)

    # 각 에이전트 이후: 스타일 적용 여부에 따라 style 또는 END
    def maybe_style(state: Dict) -> str:
        return "style" if state.get("apply_style") else END

    for node in ("rag", "phone", "app", "human"):
        graph.add_conditional_edges(node, maybe_style)

    # style 이후 종료
    graph.add_edge("style", END)

    return graph.compile()
