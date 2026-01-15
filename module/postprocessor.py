"""
Postprocessor module for NFSReport.

감정서 작성 후 특이 조건에 대한 후처리를 담당합니다.
두 가지 레벨의 후처리를 제공합니다:
1. TextPostprocessor: HWPFormatter 입력 전 텍스트 수정
2. HWPPostprocessor: HWP 파일 내 텍스트 스캔 및 형식 변경
"""

from typing import Optional
from module.constants_postprocessor import (
    TextReplaceRule,
    HWPFormatRule,
    TEXT_REPLACE_RULES,
    HWP_FORMAT_RULES,
)


class TextPostprocessor:
    """
    텍스트 레벨 후처리 클래스.

    HWPFormatter에 입력하기 전 텍스트를 조건에 따라 수정합니다.
    """

    def __init__(self, rules: Optional[list[TextReplaceRule]] = None):
        """
        TextPostprocessor 초기화.

        Args:
            rules: 적용할 규칙 목록. None이면 기본 규칙(TEXT_REPLACE_RULES) 사용.
        """
        self.rules: list[TextReplaceRule] = rules if rules is not None else list(TEXT_REPLACE_RULES)

    def add_rule(self, rule: TextReplaceRule) -> None:
        """
        규칙 추가.

        Args:
            rule: 추가할 텍스트 교체 규칙
        """
        self.rules.append(rule)

    def process(self, text: str) -> str:
        """
        텍스트 후처리 실행.

        등록된 모든 규칙을 순차적으로 적용합니다.

        Args:
            text: 후처리할 텍스트

        Returns:
            후처리된 텍스트
        """
        result = text
        for rule in self.rules:
            if rule.condition(result):
                result = rule.replacement(result)
        return result


class HWPPostprocessor:
    """
    HWP 레벨 후처리 클래스.

    HWP 파일 내 텍스트를 스캔하고 형식을 변경합니다.
    """

    def __init__(self, hwp_control, rules: Optional[list[HWPFormatRule]] = None):
        """
        HWPPostprocessor 초기화.

        Args:
            hwp_control: HWP COM 객체 (NFS_HWPFormatter.hwp_control)
            rules: 적용할 규칙 목록. None이면 기본 규칙(HWP_FORMAT_RULES) 사용.
        """
        self.hwp_control = hwp_control
        self.rules: list[HWPFormatRule] = rules if rules is not None else list(HWP_FORMAT_RULES)

    def add_rule(self, rule: HWPFormatRule) -> None:
        """
        규칙 추가.

        Args:
            rule: 추가할 HWP 형식 변경 규칙
        """
        self.rules.append(rule)

    def process(self) -> None:
        """
        HWP 후처리 실행.

        등록된 모든 규칙을 순차적으로 적용합니다.
        """
        for rule in self.rules:
            self._apply_rule(rule)

    def _apply_rule(self, rule: HWPFormatRule) -> None:
        """
        개별 규칙 적용.

        Args:
            rule: 적용할 HWP 형식 변경 규칙
        """
        if rule.format_type == "superscript":
            self._apply_superscript(rule.pattern, rule.options)
        # 추가 형식 타입은 여기에 구현

    def _apply_superscript(self, pattern: str, options: Optional[dict] = None) -> None:
        """
        패턴에 매칭되는 텍스트를 위첨자로 변경.

        Args:
            pattern: 찾을 텍스트 패턴 (정규식)
            options: 추가 옵션
        """
        # TODO: HWP 문서 스캔 및 위첨자 적용 로직 구현
        pass

    def scan_document(self, pattern: str) -> list[dict]:
        """
        HWP 문서에서 패턴에 매칭되는 텍스트 위치를 스캔.

        Args:
            pattern: 찾을 텍스트 패턴 (정규식)

        Returns:
            매칭된 텍스트 정보 목록 (위치, 텍스트 등)
        """
        # TODO: HWP 문서 스캔 로직 구현
        pass

