from typing import Dict, List, Tuple
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimpleRAG:
    """아주 간단한 TF-IDF 기반 RAG 구현.
    - 프로젝트의 data/kb/*.txt 를 로드하여 문서 코퍼스를 구성
    - 쿼리와 코퍼스의 코사인 유사도를 계산하여 Top-K를 반환
    """

    def __init__(self, kb_dir: str = "data/kb", top_k: int = 2):
        self.kb_dir = kb_dir
        self.top_k = top_k
        self.documents: List[str] = []
        self.doc_paths: List[Path] = []
        self.vectorizer = TfidfVectorizer()
        self.doc_matrix = None
        self._load_corpus()

    def _load_corpus(self) -> None:
        kb_path = Path(self.kb_dir)
        if not kb_path.exists():
            kb_path.mkdir(parents=True, exist_ok=True)
        for p in kb_path.glob("*.txt"):
            try:
                text = p.read_text(encoding="utf-8").strip()
            except UnicodeDecodeError:
                text = p.read_text(errors="ignore").strip()
            if text:
                self.documents.append(text)
                self.doc_paths.append(p)
        if self.documents:
            self.doc_matrix = self.vectorizer.fit_transform(self.documents)

    def retrieve(self, query: str) -> List[Tuple[str, float]]:
        if not self.documents:
            return []
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.doc_matrix).flatten()
        top_indices = sims.argsort()[::-1][: self.top_k]
        results: List[Tuple[str, float]] = []
        for idx in top_indices:
            results.append((self.documents[idx], float(sims[idx])))
        return results

    def answer(self, query: str) -> str:
        """Top-K 문서에서 간단 요약/결합 응답 생성(규칙 기반)."""
        hits = self.retrieve(query)
        if not hits:
            return "지식베이스에 관련 정보가 없습니다. 상담사 연결 또는 다른 요청을 시도해주세요."
        snippets = []
        for doc, score in hits:
            # 너무 길면 앞부분만 발췌
            snippet = doc[:300]
            snippets.append(f"- 관련도 {score:.2f}: {snippet}")
        joined = "\n".join(snippets)
        return f"다음 정보를 찾았습니다:\n{joined}\n\n질문에 대한 핵심 정보를 위에서 발췌했습니다. 추가 질문이 있다면 말씀해주세요."


def run_rag_agent(state: Dict) -> Dict:
    """RAG 에이전트 진입점. state['user_input']를 받아 답변 텍스트를 생성."""
    user_input: str = state.get("user_input", "")
    rag: SimpleRAG = state.setdefault("_rag_instance", SimpleRAG())
    response_text = rag.answer(user_input)
    state["response"] = response_text
    return state
