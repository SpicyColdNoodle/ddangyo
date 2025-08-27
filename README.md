## 고객응대 멀티-에이전트 챗봇 (LangGraph 기반)

이 프로젝트는 사용자의 입력을 4가지 하위 에이전트(RAG, 전화연결, 앱버튼연동, Human상담사 필터링)로 라우팅하고, 필요 시 마지막에 화법(말투) 적용 에이전트를 거쳐 응답을 생성하는 콘솔 앱 예제입니다.

### 1) 사전 준비
- Windows PowerShell 환경 기준
- Python 3.10+ 권장

### 2) 가상환경 생성 및 활성화
```powershell
# 프로젝트 디렉토리로 이동
cd C:\Users\shic\Downloads\AgentPoC

# 가상환경 생성 (폴더명: .venv)
python -m venv .venv

# 가상환경 활성화
. .venv\Scripts\Activate.ps1

# 필요 패키지 설치
pip install -U pip
pip install -r requirements.txt
```

만약 실행 정책 문제로 활성화가 안 되면 아래를 참고하세요(관리자 PowerShell 권장):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3) 환경변수 설정(.env)
프로젝트 루트에 `.env` 파일을 만들고 필요한 값을 채우세요. 예시는 `.env.example` 참고.

### 4) 실행 방법
```powershell
# 콘솔 앱 실행
python main.py
```

실행 후 프롬프트에 사용자 문장을 입력하면, 분류기 → 라우팅 → 하위 에이전트 → (선택적) 화법 적용 → 최종 출력의 흐름으로 응답을 확인할 수 있습니다. 종료는 `exit` 또는 `quit` 입력.

### 5) 구조 개요
```
AgentPoC/
├─ data/
│  └─ kb/
│     ├─ faq_1.txt
│     └─ faq_2.txt
├─ src/
│  ├─ agents/
│  │  ├─ rag_agent.py
│  │  ├─ phone_agent.py
│  │  ├─ app_button_agent.py
│  │  └─ human_filter_agent.py
│  ├─ style_agent.py
│  ├─ router.py
│  └─ graph.py
├─ scripts/
│  └─ smoke_faq.py
├─ img/
│  └─ mainlogo.png  # 로고 파일(사용자 제공)
├─ .env.example
├─ requirements.txt
├─ README.md
├─ .streamlit/config.toml
├─ app_streamlit.py
└─ main.py
```

### 6) Streamlit 웹 UI 실행
```powershell
# 의존성 설치 후
streamlit run app_streamlit.py
```
- 로고 파일은 `img/mainlogo.png` 경로에 두시면 자동 적용됩니다. 없으면 기본 포인트 컬러로 동작합니다.
- 테마 기본값은 `.streamlit/config.toml`에서 조정 가능합니다.

### 7) 커스텀/개선 가이드
- 분류기(`src/router.py`) 키워드/룰 튜닝
- RAG(`src/agents/rag_agent.py`) 벡터DB·임베딩 전환
- 전화/앱버튼 실제 API 연동
- 화법(`src/style_agent.py`) 프리셋 강화
- 브랜딩: `BRAND_NAME`, `img/mainlogo.png`, `.streamlit/config.toml` 색상

### 8) 라이선스
MIT
