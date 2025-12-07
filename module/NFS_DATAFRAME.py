import logging
import os
import pandas as pd
from openpyxl import load_workbook
import re

logger = logging.getLogger(__name__)


def xls_to_dataframe(filepath: str, header: bool = True) -> pd.DataFrame:
    """엑셀 파일을 DataFrame으로 변환

    Args:
        filepath: 엑셀 파일 경로
        header: 헤더 행 존재 여부. 기본값은 True

    Returns:
        pd.DataFrame: 엑셀 파일 내용을 담은 DataFrame (모든 컬럼은 object 타입)

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 엑셀 파일 읽기에 실패했을 때

    Examples:
        >>> df = xls_to_dataframe('data/profiles.xlsx')
        >>> df = xls_to_dataframe('data/raw_data.xlsx', header=False)
    """
    logger.debug(f"엑셀 파일 읽기 시작 (filepath={filepath}, header={header})")

    # 1. 파일 존재 여부 검증
    if not os.path.exists(filepath):
        logger.error(f"파일이 존재하지 않습니다: {filepath}")
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {filepath}")

    # 2. 엑셀 파일 읽기
    try:
        header_value = 0 if header else None
        df = pd.read_excel(filepath, dtype='object', header=header_value)
    except Exception as e:
        logger.error(f"엑셀 파일 읽기 실패: {filepath} - {e}")
        raise ValueError(f"엑셀 파일 읽기 실패: {filepath}") from e

    logger.info(f"엑셀 파일 읽기 완료 (rows={len(df)}, cols={len(df.columns)})")
    return df


def sort_by_serial_number(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """일련번호 형식의 키로 DataFrame 자연 정렬

    일련번호 형식(예: "2023-D-1234-5")을 숫자 부분별로 파싱하여
    자연스러운 순서로 정렬합니다.

    정렬 기준: (연도, 분류번호, 일련번호, 서브번호)
    예: 2023-D-1234-2 < 2023-D-1234-10 < 2023-D-1235-1

    Args:
        df: 정렬할 DataFrame
        key_column: 일련번호가 저장된 컬럼명

    Returns:
        pd.DataFrame: 자연 정렬된 DataFrame (인덱스 재설정됨)

    Raises:
        KeyError: key_column이 DataFrame에 존재하지 않을 때
        ValueError: 일련번호 형식이 올바르지 않을 때

    Examples:
        >>> df = pd.DataFrame({'코드': ['2023-D-1234-10', '2023-D-1234-2']})
        >>> sorted_df = sort_by_serial_number(df, '코드')
        >>> list(sorted_df['코드'])
        ['2023-D-1234-2', '2023-D-1234-10']
    """
    logger.debug(f"데이터프레임 정렬 시작 (rows={len(df)}, key_column={key_column})")

    # 1. 컬럼 존재 여부 검증
    if key_column not in df.columns:
        logger.error(f"컬럼 '{key_column}'이 DataFrame에 존재하지 않습니다")
        raise KeyError(f"컬럼 '{key_column}'이 DataFrame에 존재하지 않습니다")

    # 2. 일련번호 파싱 및 정렬 키 생성
    digit_pattern = re.compile(r'\d+')

    def parse_serial_number(serial: str) -> tuple:
        """일련번호 문자열을 정렬 가능한 튜플로 변환"""
        digits = digit_pattern.findall(serial)

        if len(digits) < 3:
            logger.error(f"일련번호 형식 오류: '{serial}' (최소 3개 숫자 필요)")
            raise ValueError(f"일련번호 형식 오류: '{serial}'")

        # (연도, 분류번호, 일련번호, 서브번호)
        # 서브번호가 없으면 0으로 처리
        return (
            int(digits[0]),
            int(digits[1]),
            int(digits[2]),
            int(digits[3]) if len(digits) > 3 else 0
        )

    # 3. 정렬 순서 계산
    serial_numbers = list(df[key_column])
    sorted_serials = sorted(serial_numbers, key=parse_serial_number)
    serial_to_rank = {serial: rank for rank, serial in enumerate(sorted_serials)}

    # 4. DataFrame 정렬
    df_with_rank = df.copy()
    df_with_rank['_RANK'] = df[key_column].map(serial_to_rank)
    df_sorted = df_with_rank.sort_values('_RANK').drop('_RANK', axis=1)

    # 5. 인덱스 재설정
    df_sorted = df_sorted.reset_index(drop=True)

    logger.debug(f"데이터프레임 정렬 완료 (rows={len(df_sorted)})")
    return df_sorted

