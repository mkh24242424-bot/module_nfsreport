"""연관 건 정보 입력 모듈

tkinter 다이얼로그를 사용하여 연관 건 정보를 입력받거나
HWP 감정서에서 추출하는 기능을 제공합니다.
"""

import logging
import sys
from typing import Literal

import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

# Windows 고해상도 디스플레이 DPI 설정
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # 폴백: System DPI Aware
        except Exception:
            pass

logger = logging.getLogger(__name__)

# 기본값 정의
DEFAULT_VALUES = {
    "scas_number": "*** SCAS***-***호",
    "request_date": "2024. *. *.",
    "nfs_number": "2024-C-****",
}


def _init_tk_root() -> tk.Tk:
    """숨겨진 tkinter 루트 윈도우 생성"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root


def select_input_mode() -> Literal["manual", "hwp"]:
    """입력 방식 선택 다이얼로그

    Returns:
        "hwp": HWP 감정서에서 추출
        "manual": 직접 입력
    """
    root = _init_tk_root()
    try:
        result = messagebox.askyesno(
            "입력 방식 선택",
            "HWP 감정서에서 추출하시겠습니까?\n\n예: HWP에서 추출\n아니오: 직접 입력",
            parent=root
        )
        return "hwp" if result else "manual"
    except Exception as e:
        logger.warning(f"입력 방식 선택 오류, 직접 입력 모드로 진행: {e}")
        return "manual"
    finally:
        root.destroy()


def _get_input_with_default(prompt: str, title: str, default_key: str, parent: tk.Tk) -> str:
    """입력값이 없거나 오류 시 기본값 반환"""
    try:
        # 다이얼로그가 항상 최상위에 표시되도록 포커스 강제 활성화
        parent.lift()
        parent.focus_force()
        parent.update()

        value = simpledialog.askstring(title, prompt, parent=parent)
        if not value or not value.strip():
            logger.debug(f"{title}: 빈 입력 → 기본값 사용: {DEFAULT_VALUES[default_key]}")
            return DEFAULT_VALUES[default_key]
        return value.strip()
    except Exception as e:
        logger.warning(f"{title} 입력 오류 → 기본값 사용: {e}")
        return DEFAULT_VALUES[default_key]


def collect_manual_input() -> tuple[str, str, str]:
    """직접 입력으로 연관 건 정보 수집

    Returns:
        (scas_number, request_date, nfs_number)
    """
    root = _init_tk_root()
    try:
        scas_number = _get_input_with_default(
            "요청건의 SCAS 접수 번호 입력\n(e.g. 대전서부경찰서 SCAS여성청소년과-1212)",
            "SCAS 접수 번호",
            "scas_number",
            root
        )

        request_date = _get_input_with_default(
            "연관 건의 접수 날짜를 입력하세요\n(e.g. 2024. 1. 22)",
            "접수 날짜",
            "request_date",
            root
        )

        nfs_number = _get_input_with_default(
            "국립과학수사연구원 접수 번호를 입력하세요\n(e.g. 2023-C-334)",
            "국과수 접수 번호",
            "nfs_number",
            root
        )

        logger.info(f"직접 입력 완료 - SCAS: {scas_number}, 날짜: {request_date}, 번호: {nfs_number}")
        return scas_number, request_date, nfs_number
    finally:
        root.destroy()


def collect_hwp_path() -> str | None:
    """HWP 파일 경로 선택 다이얼로그

    Returns:
        선택된 파일 경로 또는 None (취소 시)
    """
    root = _init_tk_root()
    try:
        hwp_path = filedialog.askopenfilename(
            title="HWP 감정서 선택",
            filetypes=[("HWP files", "*.hwp"), ("All files", "*.*")],
            parent=root
        )
        if not hwp_path:
            logger.debug("HWP 파일 선택 취소")
            return None
        return hwp_path
    except Exception as e:
        logger.warning(f"HWP 파일 선택 오류: {e}")
        return None
    finally:
        root.destroy()


def get_comparison_case_input() -> tuple[str, str, str]:
    """연관 건 정보 입력 (직접 입력 또는 HWP 추출)

    1. 입력 방식 선택 (HWP 추출 / 직접 입력)
    2. 선택에 따라 정보 수집
    3. 오류 발생 시 기본값 반환

    Returns:
        (scas_number, request_date, nfs_number)
    """
    mode = select_input_mode()

    if mode == "manual":
        return collect_manual_input()

    # HWP 추출 모드
    hwp_path = collect_hwp_path()
    if not hwp_path:
        logger.info("HWP 파일 미선택, 직접 입력 모드로 전환")
        return collect_manual_input()

    try:
        from .hwp_extractor import HWPExtractor

        extractor = HWPExtractor(hwp_path)
        try:
            result = extractor.extract_comparison_case_info()
            logger.info(f"HWP 추출 완료 - SCAS: {result[0]}, 날짜: {result[1]}, 번호: {result[2]}")
            return result
        finally:
            extractor.close()
    except Exception as e:
        logger.error(f"HWP 추출 실패, 기본값 사용: {e}")
        return (
            DEFAULT_VALUES["scas_number"],
            DEFAULT_VALUES["request_date"],
            DEFAULT_VALUES["nfs_number"]
        )
