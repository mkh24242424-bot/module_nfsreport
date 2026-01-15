"""
Postprocessor module constants.

특이 조건에 대한 후처리에 사용되는 상수들을 정의합니다.
"""

from dataclasses import dataclass
from typing import Callable, Optional


# ==================== 텍스트 후처리 규칙 정의 ====================

@dataclass
class TextReplaceRule:
    """
    텍스트 교체 규칙.

    Attributes:
        name: 규칙 이름 (디버깅/로깅용)
        condition: 조건 함수 - 텍스트를 받아 규칙 적용 여부를 반환
        replacement: 교체 함수 - 텍스트를 받아 수정된 텍스트를 반환
    """
    name: str
    condition: Callable[[str], bool]
    replacement: Callable[[str], str]


# ==================== HWP 후처리 규칙 정의 ====================

@dataclass
class HWPFormatRule:
    """
    HWP 형식 변경 규칙.

    Attributes:
        name: 규칙 이름 (디버깅/로깅용)
        pattern: 찾을 텍스트 패턴 (정규식)
        format_type: 적용할 형식 타입 (예: "superscript", "bold", "underline")
        options: 추가 옵션 (형식별 세부 설정)
    """
    name: str
    pattern: str
    format_type: str
    options: Optional[dict] = None


# ==================== 개별 텍스트 후처리 규칙 ====================
# 각 규칙을 개별 변수로 정의하여 추가/수정/제거가 용이하도록 함

# 예시 규칙 (주석 처리)
# TEXT_RULE_EXAMPLE = TextReplaceRule(
#     name="example_rule",
#     condition=lambda text: "특정문구" in text,
#     replacement=lambda text: text.replace("특정문구", "대체문구"),
# )


# ==================== 개별 HWP 후처리 규칙 ====================
# 각 규칙을 개별 변수로 정의하여 추가/수정/제거가 용이하도록 함

# 예시 규칙 (주석 처리)
# HWP_RULE_SUPERSCRIPT_NUMBERS = HWPFormatRule(
#     name="superscript_numbers",
#     pattern=r"\d+",
#     format_type="superscript",
# )


# ==================== 텍스트 후처리 규칙 목록 ====================
# 활성화할 규칙만 리스트에 추가

TEXT_REPLACE_RULES: list[TextReplaceRule] = [
    # TEXT_RULE_EXAMPLE,
]


# ==================== HWP 후처리 규칙 목록 ====================
# 활성화할 규칙만 리스트에 추가

HWP_FORMAT_RULES: list[HWPFormatRule] = [
    # HWP_RULE_SUPERSCRIPT_NUMBERS,
]

