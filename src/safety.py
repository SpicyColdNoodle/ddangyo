from __future__ import annotations

import re
from typing import Dict, Tuple


# 간단한 PII/욕설 감지 및 마스킹 유틸리티
# 규칙 기반 최소 구현: 실제 서비스에서는 전용 라이브러리/모델 사용 권장


_PHONE_RE = re.compile(r"(?:\+?82[-\s]?)?0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_RRN_RE = re.compile(r"\b\d{6}-\d{7}\b")  # 주민등록번호 패턴(예: 900101-1234567)
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")  # 단순 카드번호 패턴


_PROFANITIES = [
    # 한국어/영어 대표적 비속어(부분)
    "씨발",
    "씨빨",
    "병신",
    "지랄",
    "fuck",
    "shit",
    "bitch",
]


def _mask_match(text: str, regex: re.Pattern, label: str) -> Tuple[str, int]:
    count = 0
    def repl(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f"<{label}>"
    return regex.sub(repl, text), count


def _mask_pii(text: str) -> Tuple[str, Dict[str, int]]:
    stats: Dict[str, int] = {}
    masked, c = _mask_match(text, _EMAIL_RE, "EMAIL")
    if c:
        stats["email"] = c
    masked, c = _mask_match(masked, _PHONE_RE, "PHONE")
    if c:
        stats["phone"] = c
    masked, c = _mask_match(masked, _RRN_RE, "RRN")
    if c:
        stats["rrn"] = c
    masked, c = _mask_match(masked, _CARD_RE, "CARD")
    if c:
        stats["card"] = c
    return masked, stats


def _mask_profanity(text: str) -> Tuple[str, int]:
    count = 0
    masked = text
    # 단어 경계 무시 단순 포함 기준(소문자 비교)
    lowered = masked.lower()
    for bad in _PROFANITIES:
        idx = 0
        while True:
            pos = lowered.find(bad, idx)
            if pos == -1:
                break
            end = pos + len(bad)
            masked = masked[:pos] + "*" * len(bad) + masked[end:]
            lowered = masked.lower()
            idx = end
            count += 1
    return masked, count


def sanitize_user_input(user_input: str) -> Tuple[str, Dict[str, int]]:
    """사용자 입력에서 PII/욕설을 마스킹하고 간단 통계를 반환.

    반환값: (sanitized_text, stats)
    stats 예: {"email":1, "phone":2, "profanity":1}
    """
    masked, pii_stats = _mask_pii(user_input)
    masked, prof_count = _mask_profanity(masked)
    if prof_count:
        pii_stats["profanity"] = prof_count
    return masked, pii_stats


def moderate_or_block(user_input: str) -> Tuple[bool, str, Dict[str, int]]:
    """블록 여부, 표시 메시지(또는 정제 텍스트), 통계를 반환.

    - PII가 포함되면 마스킹만 하고 통과
    - 과도한 욕설(예: 3회 이상)일 경우 차단 메시지 반환
    """
    sanitized, stats = sanitize_user_input(user_input)
    profanity_count = stats.get("profanity", 0)
    if profanity_count >= 3:
        return True, "부적절한 표현이 다수 감지되어 요청이 차단되었습니다.", stats
    return False, sanitized, stats


