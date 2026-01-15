"""
Postprocessor module for NFSReport.

감정서 작성 후 특이 조건에 대한 후처리를 담당합니다.
"""


class TextPostprocessor:
    """텍스트 레벨 후처리 - HWPFormatter 입력 전 텍스트 수정"""

    def process(self, text: str) -> str:
        return text


class HWPPostprocessor:
    """HWP 레벨 후처리 - HWP 파일 내 텍스트 스캔 및 형식 변경"""

    def __init__(self, hwp_control):
        self.hwp_control = hwp_control

    def process(self) -> None:
        pass
