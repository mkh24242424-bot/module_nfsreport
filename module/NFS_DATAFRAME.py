import logging
import pandas as pd
from openpyxl import load_workbook
import re

logger = logging.getLogger(__name__)


def xls_to_dataframe(path: str, header: bool = True) -> pd.DataFrame:
    """
    엑셀 파일을 Dataframe 객체로 전환해서 반환

    Parameters:
        path(str): openpyxl 라이브러리로 작업할 NFIS 파일의 경로
        header(bool): 헤더의 존재 여부

    Returns:
        DataFrame: NFIS 파일의 내용을 DataFrame으로 변환한 객체
    """
    logger.debug(f"엑셀 파일 읽기 시작 (path={path})")
    if header:
        df = pd.read_excel(path, dtype='object', header=0)
    else:
        df = pd.read_excel(path, dtype='object', header=None)
    logger.info(f"엑셀 파일 읽기 완료 (rows={len(df)}, cols={len(df.columns)})")
    return df


def sort_by_serial_number(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """
    입력받은 데이터프레임을 serial number 형식(e.g 2023-D-1232-1a)의 key를 기준으로 natural sort한다.

    Parameters:
        df(pd.DataFrame): 정렬할 데이터프레임
        key_column:
        digit: 자릿수
    """
    logger.debug(f"데이터프레임 정렬 시작 (rows={len(df)}, key_column={key_column})")
    df.sort_values(key_column, inplace=True)
    list_serial = list(df[key_column])
    p = re.compile(r'\d+')
    sorted_serial = sorted(list_serial, key=lambda x: (
        int(p.findall(x)[0]), int(p.findall(x)[1]), int(p.findall(x)[2]), int(p.findall(x)[3])) if len(
        p.findall(x)) > 3 else (int(p.findall(x)[0]), int(p.findall(x)[1]), int(p.findall(x)[2]), 0))
    # 2019-D-1234-5 => 2019, 1234, 5
    df_sorted = df.sort_values(key_column)
    rank = {k: v for v, k in enumerate(sorted_serial)}
    df_sorted['RANK'] = df[key_column].apply(lambda x: rank[x])
    df_sorted = df_sorted.sort_values('RANK')
    df_sorted = df_sorted.drop('RANK', axis=1).reset_index(drop=True)
    logger.debug(f"데이터프레임 정렬 완료 (rows={len(df_sorted)})")
    return df_sorted


def link_num_evidence(df: pd.DataFrame, reaction: bool = False, y23: bool = False) -> str:
    """
    증거물 번호를 연결하여 보고서 형식의 문자열로 반환

    연속된 증거물 번호는 ~로 묶어 표현하며, 체액 반응 정보를 포함할 수 있습니다.

    Parameters:
        df: 증거물 정보가 담긴 DataFrame
        reaction: 체액 반응 정보 포함 여부
        y23: Y-STR 마커 사용 여부

    Returns:
        연결된 증거물 번호 문자열 (예: "증1호~증3호, 증5호")
    """
    # 기재 해야하는 체액반응이 있을 경우 serial에 체액 반응을 추가해서 표기번호 리스트로 만듬.
    df_target = df.copy()
    reaction = reaction and not y23
    if reaction:
        df_target['반응'] = df_target['타액_반응'].apply(lambda x: '타액반응 ' + x if x != "실험 안함" else "") + ',' \
                          + df_target['정액_반응'].apply(lambda x: '정액반응 ' + x if x != "실험 안함" else "") + ',' \
                          + df_target['혈흔_반응'].apply(lambda x: '혈흔반응 ' + x if x != "실험 안함" else "")
        list_reaction = df_target['반응'].tolist()
        final = []
        for i in list_reaction:
            each = i.split(',')
            process = [x for x in each if x != ""]
            if len(process) == 0:
                final.append("")
            else:
                final.append("(" + ', '.join(process) + ")")
        df_target['반응'] = final
        df_target['표기번호+반응'] = df_target['표기번호'] + df_target['반응']
        list_serial = list(df_target['표기번호+반응'])
        list_reaction = list(df_target["반응"])
    else:
        list_serial = list(df_target['표기번호']) if y23 == False else list(df_target['Y_표기번호'])  # 수정 사항

    # 연속되는 번호 처리.
    list_idx = list(df_target.index)
    stack_serial = []
    stack_idx = []
    list_result = []
    if len(list_serial) == 1:
        list_result.append('{0}'.format(list_serial[0]))
    elif len(list_serial) == 2:
        list_result.append('{0} 및 {1}'.format(list_serial[0], list_serial[1]))
    else:
        stack_serial.append(list_serial[0])
        stack_idx.append(list_idx[0])
        for idx, target in enumerate(list_serial[1:]):
            # 증거물 번호가 연속되는 것이라고 처리하는 조건1
            cond_continue1 = ((stack_idx[-1] + 1) == list_idx[(idx + 1)])
            if reaction == False:
                cond_continue2 = True
            else:
                # 증거물 번호가 연속되는 것이라고 처리하는 조건2 - 다음 증거물의 체액 반응 여부가 없다면
                cond_continue2 = (list_reaction[idx] == '') and (list_reaction[idx + 1] == '')
            if cond_continue1 and cond_continue2:  # 번호가 이어지거나 다음 증거물의 체액 반응 여부가 없다면
                stack_idx.append(list_idx[(idx + 1)])
                stack_serial.append(target)
            else:
                if len(stack_serial) == 1:
                    list_result.append('{0}'.format(stack_serial[0]))
                    stack_serial.clear()
                    stack_idx.clear()
                    stack_serial.append(target)
                    stack_idx.append(list_idx[(idx + 1)])
                elif len(stack_serial) == 2:
                    list_result.append('{0}'.format(stack_serial[0]))
                    list_result.append('{0}'.format(stack_serial[1]))
                    stack_serial.clear()
                    stack_idx.clear()
                    stack_serial.append(target)
                    stack_idx.append(list_idx[(idx + 1)])
                else:
                    list_result.append('{0}~{1}'.format(stack_serial[0], stack_serial[-1]))
                    stack_serial.clear()
                    stack_idx.clear()
                    stack_serial.append(target)
                    stack_idx.append(list_idx[(idx + 1)])
        # 남은 stack_serial의 처리
        if len(stack_serial) != 0:
            if len(stack_serial) == 1:
                list_result.append('{0}'.format(stack_serial[0]))
                stack_idx.clear()
                stack_serial.clear()
            elif len(stack_serial) == 2:
                list_result.append('{0}'.format(stack_serial[0]))
                list_result.append('{0}'.format(stack_serial[1]))
                stack_idx.clear()
                stack_serial.clear()
            else:
                list_result.append('{0}~{1}'.format(stack_serial[0], stack_serial[-1]))
                stack_idx.clear()
                stack_serial.clear()
    return ', '.join(list_result)

