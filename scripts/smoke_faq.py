import sys
from pathlib import Path

# 프로젝트 루트 기준으로 실행 가정
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.graph import build_graph  # noqa: E402


CASES = [
    "배송 문의 있습니다",
    "교환/반품 기간 알려줘",
    "전화 연결 부탁",
    "앱에서 버튼으로 열어줘",
    "환불 문제로 분쟁이 있습니다",
]


def main() -> None:
    g = build_graph()
    print("=== FAQ Smoke Test ===")
    for text in CASES:
        result = g.invoke({"user_input": text})
        out = result.get("final_text") or result.get("response") or "(no response)"
        print(f"\n[INPUT] {text}\n[OUTPUT]\n{out}\n")
    print("=== Done ===")


if __name__ == "__main__":
    main()
