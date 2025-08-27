import os
from rich.console import Console
from dotenv import load_dotenv

# LangGraph 그래프 로딩
from src.graph import build_graph
from src.safety import moderate_or_block


def main():
    """콘솔 인터랙티브 루프. 사용자의 문장을 받아 그래프 실행 후 결과 출력."""
    load_dotenv()
    console = Console()

    graph = build_graph()
    console.print("[bold green]고객응대 멀티-에이전트 챗봇 시작[/bold green]")
    console.print("종료하려면 'exit' 또는 'quit'을 입력하세요.\n")

    while True:
        user_input = input("사용자> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            console.print("[bold]종료합니다.[/bold]")
            break

        # 안전 필터링 적용
        blocked, safe_input, stats = moderate_or_block(user_input)
        if blocked:
            console.print("[bold red]요청이 차단되었습니다:[/bold red] 부적절한 표현이 감지되었습니다.")
            continue

        # 그래프 실행: 상태는 dict로 주고받음
        state = {"user_input": safe_input, "_safety_stats": stats}
        result = graph.invoke(state)
        final_text = result.get("final_text") or result.get("response") or "(응답이 없습니다)"
        console.print(f"\n[bold cyan]봇>[/bold cyan] {final_text}\n")


if __name__ == "__main__":
    main()
