import logging
from typing import Any
from dataclasses import dataclass
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QApplication
import re

logger = logging.getLogger(__name__)


def has_qapplication() -> bool:
    """
    QApplication 인스턴스가 존재하는지 확인합니다.

    Returns:
        bool: QApplication 인스턴스가 존재하면 True, 아니면 False
    """
    return QApplication.instance() is not None


@dataclass
class Properties_Phrase:
    gender: str
    likelihoodratio: tuple
    text_evidence: str
    nickname: str

def input_comparison_case() -> tuple[str | Any, str | Any, Any] | tuple[str | Any, str | Any, str]:
    if has_qapplication():
        # GUI 모드: QInputDialog 사용
        logger.debug("GUI 모드: QInputDialog 사용")
        request_scas, ok = QInputDialog.getText(None, "SCAS 접수 번호 입력",
                                                "요청건의 SCAS 접수 번호 입력.(e.g. 대전서부경찰서 SCAS여성청소년과-1212")
        if not ok or not request_scas.strip():
            request_scas = "*** SCAS***-***호"
            logger.debug(f"SCAS 접수 번호: 빈 입력 또는 취소 → 기본값 사용: {request_scas}")

        request_date, ok = QInputDialog.getText(None, "SCAS 접수 날짜 입력", "연관 건의 접수 날짜를 입력하세요.(e.g. 2024. 1. 22)")
        if not ok or not request_date.strip():
            request_date = "2024. *. *."
            logger.debug(f"SCAS 접수 날짜: 빈 입력 또는 취소 → 기본값 사용: {request_date}")

        request_number, ok = QInputDialog.getText(None, "사건 접수 번호 입력", "국립과학수사연구원 접수 번호를 입력하세요.(e.g. 2023-C-334)")
        if not ok or not request_number.strip():
            request_number = "2024-C-****"
            logger.debug(f"사건 접수 번호: 빈 입력 또는 취소 → 기본값 사용: {request_number}")

        return request_scas, request_date, request_number
    else:
        # 터미널 모드: input() 사용
        logger.debug("터미널 모드: input() 사용")
        try:
            request_scas = input("요청건의 SCAS 접수 번호 입력 (e.g. 대전서부경찰서 SCAS여성청소년과-1212): ").strip()
            if not request_scas:
                request_scas = "*** SCAS***-***호"
                logger.debug(f"SCAS 접수 번호: 빈 입력 → 기본값 사용: {request_scas}")

            request_date = input("연관 건의 접수 날짜를 입력하세요 (e.g. 2024. 1. 22): ").strip()
            if not request_date:
                request_date = "2024. *. *."
                logger.debug(f"SCAS 접수 날짜: 빈 입력 → 기본값 사용: {request_date}")

            request_number = input("국립과학수사연구원 접수 번호를 입력하세요 (e.g. 2023-C-334): ").strip()
            if not request_number:
                request_number = "2024-C-****"
                logger.debug(f"사건 접수 번호: 빈 입력 → 기본값 사용: {request_number}")

            logger.info(f"입력 완료 - SCAS: {request_scas}, 날짜: {request_date}, 번호: {request_number}")
            return request_scas, request_date, request_number
        except (EOFError, KeyboardInterrupt):
            # Ctrl+C 또는 EOF 시 기본값 반환
            logger.warning("입력 중단됨. 모든 항목에 기본값 사용")
            return "*** SCAS***-***호", "2024. *. *.", "2024-C-****"


def make_phrase_ref(info: Properties_Phrase) -> str:
    logger.debug(f"대조 문구 생성 시작 (nickname={info.nickname})")
    answer_victim = None
    # 피해자, 변사자, 관계자의 경우 식별 지수 표기 및 문장 단축.
    list_exception = ['피해자', '변사자', '참고인', '관계자']

    if any([(exception in info.nickname) for exception in list_exception]):
        if has_qapplication():
            # GUI 모드: QMessageBox 사용
            logger.debug("GUI 모드: QMessageBox 사용")
            answer_victim = QMessageBox.question(None, '', "식별지수를 제외하시겠습니까?",
                                                 QMessageBox.Yes | QMessageBox.No)
            exclude_index = (answer_victim == QMessageBox.Yes)
        else:
            # 터미널 모드: input() 사용
            logger.debug("터미널 모드: input() 사용")
            try:
                response = input(f"'{info.nickname}'에 대해 식별지수를 제외하시겠습니까? (y/n): ").strip().lower()
                exclude_index = (response in ['y', 'yes', '예'])
            except (EOFError, KeyboardInterrupt):
                logger.warning("입력 중단됨. 식별지수 포함")
                exclude_index = False
    else:
        exclude_index = False

    if exclude_index:
        phrase = f"{info.text_evidence}에서 {info.nickname}의 디엔에이형이 검출됨.\r\n"
    else:
        phrase = f"{info.text_evidence}에서 {info.gender} 디엔에이형이 검출되고, 이는 {info.nickname}의 디엔에이형과 일치함.\r\n"
        phrase = phrase + f"* 이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서 {info.likelihoodratio[0]} x 10{info.likelihoodratio[1]}임.\r\n"
    logger.debug(f"대조 문구 생성 완료")
    return phrase


def make_phrase_res(info: Properties_Phrase) -> str:
    logger.debug(f"대표 문구 생성 (nickname={info.nickname})")
    phrase = f"{info.text_evidence}에서 {info.nickname}의 디엔에이형이 검출됨.\r\n"
    return phrase


def make_phrase_nc(info: Properties_Phrase) -> str:
    logger.debug("NC 문구 생성")
    phrase = f"{info.text_evidence}에서 디엔에이형을 특정할 수 없음.\r\n"
    return phrase


def make_phrase_nd(info: Properties_Phrase) -> str:
    logger.debug("ND 문구 생성")
    phrase = f"{info.text_evidence}에서 디엔에이형이 검출되지 않음.\r\n"
    return phrase


def make_phrase_ref_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서  Y-STR 디엔에이형이 검출되고, {info.nickname}의 Y-STR 디엔에이형과 일치함."
    return phrase


def make_phrase_res_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 {info.nickname}의 Y-STR 디엔에이형이 검출됨.\r\n"
    return phrase


def make_phrase_nd_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 Y-STR 디엔에이형이 검출되지 않음.\r\n"
    return phrase


def make_phrase_nc_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 " \
             f"Y-STR 디엔에이형을 특정할 수 없음.\r\n"
    return phrase


def make_phrase_deceased(info: Properties_Phrase) -> str:
    phrase = f"{info.text_evidence}에서 {info.gender}({info.nickname}) 디엔에이형이 검출됨.\r\n"
    return phrase


def make_phrase_deceased_expanded(info: Properties_Phrase) -> str:
    phrase = f"{info.text_evidence}에서 {info.gender}({info.nickname}) 디엔에이형이 검출됨.\r\n"
    return phrase


def make_phrase_suspect_match(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = input_comparison_case()
    phrase = (f"{info.nickname}의 디엔에이형은 연관 건인 '{request_scas}({request_date}, "
              f"국립과학수사연구원 접수번호 {request_number})호'에서 검출된 {info.gender} 디엔에이형과 일치함.\r\n")
    phrase = phrase + f"* 이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서 {info.likelihoodratio[0]} x 10{info.likelihoodratio[1]}임.\r\n"
    return phrase


def make_phrase_suspect_match_y(info: Properties_Phrase) -> str:
    phrase = f"{info.nickname}의 Y-STR 디엔에이형은 위 연관 건에서 검출된 Y-STR 디엔에이형과 일치함.\r\n"
    return phrase


def make_phrase_suspect_nomatch(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = input_comparison_case()
    phrase = f"{info.nickname}의 디엔에이형은 연관 건인 '{request_scas}({request_date}, " \
             f"국립과학수사연구원 접수번호 {request_number})호'에서 검출된 {info.gender} 디엔에이형과 일치하지 않음.\r\n"
    return phrase


def make_phrase_suspect_nomatch_y(info: Properties_Phrase) -> str:
    phrase = f"{info.nickname}의 Y-STR 디엔에이형은 위 연관 건에서 검출된 Y-STR 디엔에이형과 일치하지 않음.\r\n"
    return phrase


def make_phrase_suspect_nocomparable(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = input_comparison_case()
    phrase = f"{info.nickname}의 디엔에이형은 연관 건인 “{request_scas}({request_date}, " \
             f"국립과학수사연구원 접수번호 {request_number})호”에서 " \
             f"{info.gender} 디엔에이형이 검출되지 않았으므로 대조할 수 없음.\r\n"
    return phrase


def make_phrase_suspect_nocomparable_y(info: Properties_Phrase) -> str:
    phrase = f"{info.nickname}의 Y-STR 디엔에이형은 위 연관 건에서 " \
             f"Y-STR 디엔에이형이 검출되지 않았으므로 대조할 수 없음.\r\n"
    return phrase


def make_phrase_paternity_match(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = input_comparison_case()
    phrase = f"{info.nickname}의 디엔에이형을 연관 건인 '{request_scas}({request_date}, " \
                 f"국립과학수사연구원 접수번호 {request_number})호'에서 검출된 ***의 디엔에이형과 대조 비교시, " \
                 f"친자관계임이 인정됨.\r\n* 이와 같이 친자관계가 성립될 확률은 23 STR 디엔에이형에서 99.9999%임.\r\n"
    return phrase


def make_phrase_paternity_nomatch(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = input_comparison_case()
    phrase = f"{info.nickname}의 디엔에이형을 연관 건인 '{request_scas}({request_date}), " \
             f"국립과학수사연구원 접수번호 {request_number})호'에서 검출된 ***의 디엔에이형과 대조 비교시, " \
             f"친자관계임이 인정되지 않음.\r\n"
    return phrase


def make_phrase_simple_c(info: Properties_Phrase) -> str:
    phrase = f"{info.text_evidence}에서 {info.gender}의 디엔에이형이 검출되고, " \
             f"현재까지 수록된 “디엔에이신원확인정보 데이터베이스”에서 검색한 결과 " \
             f"일치 건(범죄 현장 등, 구속피의자 등 및 수형인 등) 없음.\r\n"
    return phrase


def edit_evidence(lines_evidence: list) -> str:
    """증거물명 리스트를 감정서에 바로 쓸 수 있는 형태로 편집하는 함수"""
    dict_evidence = {}
    keywords_omit = ["소변", "슬라이드"]
    for line in lines_evidence:
        key = line.split(':')[0][1:-1]
        item = line.split('호:')[1]
        if not any(keyword_omit in item for keyword_omit in keywords_omit):
            dict_evidence[key] = item

    temp_dict = dict_evidence.copy()
    for key in dict_evidence.keys():
        item = dict_evidence[key]
        # M, F 중복 처리
        if 'F' in key:
            key_new = key[:-1]  # M, F 문자열 제거
            key_m = key[:-1] + 'M'
            temp_dict[key_new] = item
            del temp_dict[key]
            del temp_dict[key_m]
        # a, b로 나눠진 샘플 처리
    dict_evidence = temp_dict.copy()
    for key in dict_evidence.keys():
        item = dict_evidence[key]
        if key[-1].isalpha():
            new_key = key[:-1]
            temp_dict[new_key] = item
    print(temp_dict)
        # 현물 감정물에 실험 부위 작성란 추가
    dict_evidence = temp_dict.copy()
    for key in dict_evidence.keys():
        item = dict_evidence[key]
        keyword_neg = ['면봉', '소변', '혈액', '음모', '늑연골', '구강키트', '심낭혈', '꽁초', '손톱', '질액'] #현물이 아닌 키워드
        flag = True
        for keyword in keyword_neg:
            if keyword in item:
                flag = False
        key_add = key + 'a'
        if flag and key_add not in dict_evidence.keys() and not key[-1].isalpha():
            temp_dict[key] = f'{item}\r\n        - '
    dict_evidence = temp_dict
    # 키를 정렬한 순서대로 텍스트 생성
    keys = list(dict_evidence.keys())
    keys.sort()
    p = re.compile(r'\d+')
    keys_sorted = sorted(keys, key=lambda x: (int(p.findall(x)[0]), int(p.findall(x)[1]))
    if len(p.findall(x)) == 2
    else (int(p.findall(x)[0]), 0)
                         )
    list_text = []
    for key in keys_sorted:
        if key[-1].isnumeric():
            list_text.append(f'증{key}호: {dict_evidence[key]}')
        else:
            list_text.append(f'\t증{key}호:')
    text_evidence_edited = '\r\n'.join(list_text)
    return text_evidence_edited

