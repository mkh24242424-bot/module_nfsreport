"""
Postprocessor module for NFSReport.

감정서 작성 후 특이 조건에 대한 후처리를 담당합니다.
"""


class TextPostprocessor:
    """텍스트 레벨 후처리"""

    def process_evidence(self, text: str) -> str:
        """
        증거물명 텍스트 변환.

        변환 규칙:
        - "담배꽁초" → "담배꽁초()"
        """
        result = text
        result = result.replace("담배꽁초", "담배꽁초()")
        return result


class HWPPostprocessor:
    """HWP 레벨 후처리 - HWP 파일 내 텍스트 스캔 및 형식 변경"""

    def __init__(self, hwp_control):
        self.hwp_control = hwp_control

    def process(self) -> None:
        pass
