import logging
from typing import Any
from dataclasses import dataclass
import re
from Modules.input_handler import get_comparison_case_input
logger = logging.getLogger(__name__)


@dataclass
class Properties_Phrase:
    gender: str
    likelihoodratio: tuple
    text_evidence: str
    nickname: str


def make_pharase_differential_extraction(text_evidence: str, phrase_nonsperm:str, phrase_sperm:str) -> str:
    reaction = re.search(r'\((.*?)\)', text_evidence)
    text_evidence = re.sub(r'\([^)]*\)', '', text_evidence)
    if reaction:
        phrase_pair = f"{text_evidence}은 {reaction.group(1)}이고,"
    else:
        phrase_pair = f"{text_evidence}은, " 
    # phrase_nonsperm = re.sub(r'\([^)]*\)', '', phrase_nonsperm)
    # phrase_nonsperm = re.sub(r'증\([^)]+\)호', '상피세포층', phrase_nonsperm)
    # phrase_sperm = re.sub(r'\([^)]*\)', '', phrase_sperm)
    # phrase_sperm = re.sub(r'증\([^)]+\)호', '정자층', phrase_sperm)
    phrase = f"{phrase_pair}\r\n @1) {phrase_nonsperm}\n @2) {phrase_sperm}"
    return phrase

def make_pharase_presume(text_evidence: str, phrase_detected:str, phrase_presumed:str) -> str:
    text_evidence = re.sub(r'\([^)]*\)', '', text_evidence)
    phrase_detected = phrase_detected.replace("됨.", "되고, ")
    phrase_presumed = phrase_presumed.replace("이 검출됨.", "을 추정할 수 있음.") 
    phrase = f"{text_evidence}에서 {phrase_detected}{phrase_presumed}"
    return phrase

def make_phrase_ref(info: Properties_Phrase) -> str:
    logger.debug(f"대조 문구 생성 시작 (nickname={info.nickname})")
    answer_victim = None
    # 피해자, 변사자, 관계자의 경우 식별 지수 표기 및 문장 단축.
    list_exception = ['피해자', '변사자', '참고인', '관계자']

    if any([(exception in info.nickname) for exception in list_exception]):
        # 터미널 모드: input() 사용
        logger.debug("터미널 모드: input() 사용")
        try:
            response = input(f"{info.text_evidence}의 '{info.nickname}' 일치에 대해 식별지수를 제외하시겠습니까? (y/n): ").strip().lower()
            exclude_index = (response in ['y', 'yes', '예'])
        except (EOFError, KeyboardInterrupt):
            logger.warning("입력 중단됨. 식별지수 포함")
            exclude_index = False
    else:
        exclude_index = False

    if exclude_index:
        phrase = f"{info.text_evidence}에서 {info.nickname}의 디엔에이형이 검출됨.\r\n"
    else:
        phrase = f"{info.text_evidence}에서 {info.nickname}의 디엔에이형과 일치하는 {info.gender} 디엔에이형이 검출됨.\r\n"
        phrase = phrase + f" * 이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서 {info.likelihoodratio[0]} x 10{info.likelihoodratio[1]}임.\r\n"
    logger.debug(f"대조 문구 생성 완료")
    return phrase

def make_phrase_res(info: Properties_Phrase) -> str:
    logger.debug(f"대표 문구 생성 (nickname={info.nickname})")
    phrase = f"{info.text_evidence}에서 {info.nickname} 디엔에이형이 검출됨.\r\n"
    return phrase

def make_phrase_nc(info: Properties_Phrase) -> str:
    logger.debug("NC 문구 생성")
    phrase = f"{info.text_evidence}에서 여러 사람의 디엔에이형이 혼합 검출되어 특정 디엔에이형을 결정할 수 없음.\r\n"
    return phrase

def make_phrase_nd(info: Properties_Phrase) -> str:
    logger.debug("ND 문구 생성: " + info.text_evidence)
    phrase = f"{info.text_evidence}에서 디엔에이형이 검출되지 않음.\r\n"
    return phrase

def make_phrase_ref_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 {info.nickname}의 Y-STR 디엔에이형과 일치하는 Y-STR 디엔에이형이 검출됨."
    return phrase

def make_phrase_res_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 {info.nickname} Y-STR 디엔에이형이 검출됨.\r\n"
    return phrase

def make_phrase_nd_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 Y-STR 디엔에이형이 검출되지 않음.\r\n"
    return phrase

def make_phrase_nc_y(info: Properties_Phrase) -> str:
    phrase = f"남성 특이적인 Y-STR 디엔에이형 추가 분석 결과, {info.text_evidence}에서 " \
             f"여러 사람의 Y-STR 디엔에이형이 혼합 검출되어 특정 디엔에이형을 결정할 수 없음.\r\n"
    return phrase

def make_phrase_deceased(info: Properties_Phrase) -> str:
    phrase = f"{info.text_evidence}에서 {info.gender}({info.nickname}) 디엔에이형이 검출됨.\r\n"
    return phrase

def make_phrase_deceased_expanded(info: Properties_Phrase) -> str:
    phrase = f"{info.text_evidence}에서 {info.gender}({info.nickname}) 디엔에이형이 검출됨.\r\n"
    return phrase

def make_phrase_suspect_match(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = get_comparison_case_input()
    phrase =f"{info.nickname}의 디엔에이형은 관련 건 {request_scas}({request_date})호, " \
              f"국립과학수사연구원 접수번호 {request_number}호의 ~에서 검출된 {info.gender} 디엔에이형과 일치함.\r\n"
    phrase = phrase + f" * 이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서 {info.likelihoodratio[0]} x 10{info.likelihoodratio[1]}임.\r\n"
    return phrase

def make_phrase_suspect_match_y(info: Properties_Phrase) -> str:
    phrase = f"{info.nickname}의 Y-STR 디엔에이형은 위 연관 건에서 검출된 Y-STR 디엔에이형과 일치함.\r\n"
    return phrase

def make_phrase_suspect_nomatch(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = get_comparison_case_input()
    phrase = f"{info.nickname}의 디엔에이형은 관련 건 {request_scas}({request_date})호, " \
             f"국립과학수사연구원 접수번호 {request_number}호의 ~에서 검출된 {info.gender} 디엔에이형과 일치하지 않음.\r\n"
    return phrase

def make_phrase_suspect_nomatch_y(info: Properties_Phrase) -> str:
    phrase = f"{info.nickname}의 Y-STR 디엔에이형은 위 연관 건에서 검출된 Y-STR 디엔에이형과 일치하지 않음.\r\n"
    return phrase

def make_phrase_suspect_nocomparable(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = get_comparison_case_input()
    phrase = f"{info.nickname}의 디엔에이형은 관련 건 {request_scas}({request_date})호, " \
             f"국립과학수사연구원 접수번호 {request_number}호의 ~에서 " \
             f"{info.gender} 디엔에이형이 검출되지 않았으므로 대조할 수 없음.\r\n"
    return phrase

def make_phrase_suspect_nocomparable_y(info: Properties_Phrase) -> str:
    phrase = f"{info.nickname}의 Y-STR 디엔에이형은 위 연관 건에서 " \
             f"Y-STR 디엔에이형이 검출되지 않았으므로 대조할 수 없음.\r\n"
    return phrase

def make_phrase_paternity_match(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = get_comparison_case_input()
    phrase = f"{info.nickname}의 디엔에이형은 관련 건 {request_scas}({request_date})호, " \
             f"국립과학수사연구원 접수번호 {request_number}호에서 검출된 ***의 디엔에이형과 대조 비교시, " \
             f"친자관계임이 인정됨.\r\n * 이와 같이 친자관계가 성립될 확률은 23 STR 디엔에이형에서 99.9999%임.\r\n"
    return phrase

def make_phrase_paternity_nomatch(info: Properties_Phrase) -> str:
    request_scas, request_date, request_number = get_comparison_case_input()
    phrase = f"{info.nickname}의 디엔에이형은 관련 건 {request_scas}({request_date})호, " \
             f"국립과학수사연구원 접수번호 {request_number}호에서 검출된 ***의 디엔에이형과 대조 비교시, " \
             f"친자관계임이 인정되지 않음.\r\n"
    return phrase

def make_phrase_simple_c(info: Properties_Phrase) -> str:
    phrase = f"{info.text_evidence}에서 {info.gender}의 디엔에이형이 검출되고, " \
             f"현재까지 수록된 “디엔에이신원확인정보 데이터베이스”에서 검색한 결과 " \
             f"일치 건(범죄 현장 등, 구속피의자 등 및 수형인 등) 없음.\r\n"
    return phrase

def make_phrase_none(info: Properties_Phrase) -> str:
    return ""
