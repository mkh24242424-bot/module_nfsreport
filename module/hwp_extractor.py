"""HWP 문서에서 정보 추출 모듈

win32com을 사용하여 HWP 감정서의 누름틀에서 정보를 추출합니다.
"""

import logging
import re
from typing import Any

import win32com.client as win32

from .constants_hwpformatter import NAME_FIELDTEXT
from .input_handler import DEFAULT_VALUES

logger = logging.getLogger(__name__)


class HWPExtractor:
    """HWP 문서에서 정보를 추출하는 클래스

    HWP 문서의 누름틀(ClickHere)에서 텍스트를 읽어옵니다.
    향후 다른 용도로 재사용 가능하도록 설계되었습니다.

    Attributes:
        hwp_path: HWP 파일 경로
        hwp_control: HWP COM 객체

    Examples:
        >>> extractor = HWPExtractor("path/to/document.hwp")
        >>> scas, date, number = extractor.extract_comparison_case_info()
        >>> extractor.close()
    """

    def __init__(self, hwp_path: str):
        """HWPExtractor 초기화

        Args:
            hwp_path: HWP 파일 경로

        Raises:
            Exception: HWP 파일 열기 실패 시
        """
        logger.info(f"HWPExtractor 초기화: {hwp_path}")
        self.hwp_path = hwp_path
        self.hwp_control: Any = None
        self._open_document()

    def _open_document(self) -> None:
        """HWP 문서 열기"""
        try:
            self.hwp_control = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
            self.hwp_control.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")
            # 백그라운드 모드로 열기 (화면에 표시하지 않음)
            self.hwp_control.XHwpWindows.Item(0).Visible = False
            self.hwp_control.Open(self.hwp_path)
            logger.debug(f"HWP 문서 열기 성공: {self.hwp_path}")
        except Exception as e:
            logger.error(f"HWP 문서 열기 실패: {e}")
            raise

    def get_field_text(self, field_name: str) -> str:
        """누름틀에서 텍스트 읽기

        Args:
            field_name: 누름틀 필드명 (NAME_FIELDTEXT의 값)

        Returns:
            필드의 텍스트 값 (빈 문자열 가능)
        """
        try:
            text = self.hwp_control.GetFieldText(field_name)
            logger.debug(f"필드 '{field_name}' 값: {text}")
            return text if text else ""
        except Exception as e:
            logger.warning(f"필드 '{field_name}' 읽기 실패: {e}")
            return ""

    def _format_date(self, date_str: str) -> str:
        """날짜 포맷 변환: (2025년 10월 27일) → 2025. 10. 27

        Args:
            date_str: HWP에서 추출한 날짜 문자열

        Returns:
            변환된 날짜 문자열
        """
        match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}. {int(month)}. {int(day)}"
        return date_str

    def _format_nfs_number(self, nfs_str: str) -> str:
        """국과수 접수번호 포맷 변환: 2025-C-7982호 → 2025-C-7982

        Args:
            nfs_str: HWP에서 추출한 국과수 접수번호

        Returns:
            마지막 '호' 제거된 문자열
        """
        if nfs_str.endswith("호"):
            return nfs_str[:-1]
        return nfs_str

    def extract_comparison_case_info(self) -> tuple[str, str, str]:
        """연관 건 정보 추출

        HWP 감정서의 누름틀에서 SCAS 접수번호, 접수날짜, 국과수 접수번호를 추출합니다.

        Returns:
            (scas_number, request_date, nfs_number)
            추출 실패 시 해당 항목은 기본값으로 대체
        """
        # SCAS 접수번호: 의뢰관서 + 문서번호 조합
        goansu = self.get_field_text(NAME_FIELDTEXT["의뢰관서"])
        munsuno = self.get_field_text(NAME_FIELDTEXT["문서번호"])

        if goansu and munsuno:
            scas_number = f"{goansu} {munsuno}"
        else:
            scas_number = DEFAULT_VALUES["scas_number"]
            logger.debug(f"SCAS 접수번호 추출 실패 → 기본값: {scas_number}")

        # 접수 날짜
        request_date = self.get_field_text(NAME_FIELDTEXT["접수일자"])
        if not request_date:
            request_date = DEFAULT_VALUES["request_date"]
            logger.debug(f"접수 날짜 추출 실패 → 기본값: {request_date}")
        else:
            request_date = self._format_date(request_date)

        # 국과수 접수번호
        nfs_number = self.get_field_text(NAME_FIELDTEXT["접수번호"])
        if not nfs_number:
            nfs_number = DEFAULT_VALUES["nfs_number"]
            logger.debug(f"국과수 접수번호 추출 실패 → 기본값: {nfs_number}")
        else:
            nfs_number = self._format_nfs_number(nfs_number)

        return scas_number, request_date, nfs_number

    def close(self) -> None:
        """HWP 문서 닫기 및 리소스 정리"""
        try:
            if self.hwp_control:
                self.hwp_control.Clear(1)  # 문서 닫기 (저장 안 함)
                self.hwp_control.Quit()
                self.hwp_control = None
                logger.debug("HWP 문서 닫기 완료")
        except Exception as e:
            logger.warning(f"HWP 문서 닫기 오류: {e}")

    def __enter__(self) -> "HWPExtractor":
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        self.close()
