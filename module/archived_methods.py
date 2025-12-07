"""보관된 메서드 (Archived Methods)

이 파일은 더 이상 사용되지 않지만 향후 참조를 위해 보관된 코드를 포함합니다.

⚠️ 주의: 이 파일의 코드는 현재 프로젝트에서 사용되지 않습니다.
         새로운 기능 구현 시 참조 목적으로만 사용하세요.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


# ==============================================================================
# NFSProfileDataManager.export_to_str() 및 헬퍼 메서드들
# ==============================================================================
# 원래 위치: module/NFS_PROFILEDATAMANAGER.py
# 제거 일자: 2025-11-27
# 제거 이유: 코드베이스 전체에서 호출되지 않음 (Dead Code)
# 관련 이슈: LikelihoodCalculator 클래스 분리 작업 중 발견
#
# 기능: 감정물번호의 프로필을 문자열 딕셔너리로 변환
#       - NC/ND 처리
#       - 미세변이 처리
#       - 혼합 프로필 처리
#       - 특이사항 리스트 반환
#
# 향후 참조: 프로필 문자열 변환 기능 추가 시 이 로직 참조 가능
# ==============================================================================

def archived_check_mixture(
    series_profile: pd.Series,
    list_marker: list,
    y23: bool,
    TA_THRESHOLD: int = 2
) -> bool:
    """현재 작업중인 프로필이 혼합 프로필인지 검사

    원래 위치: NFSProfileDataManager._check_mixture()

    Args:
        series_profile: 프로필 데이터 시리즈
        list_marker: 검사할 마커 리스트
        y23: Y-STR 마커 사용 여부
        TA_THRESHOLD: 혼합 판단 임계값 (기본값: 2)

    Returns:
        bool: 혼합 프로필 여부
    """
    limit_allele = 1 if y23 else 2
    cnt_ta = 0
    for marker in list_marker:
        alleles = series_profile[marker]
        cnt_ta = cnt_ta + 1 if len(alleles) > limit_allele else cnt_ta
    return cnt_ta > TA_THRESHOLD


def archived_check_special_case(locus: str, allele: str, DICT_MARKERS: dict) -> bool:
    """비정형 좌위값 중 허용되는 특수 케이스인지 여부를 체크

    원래 위치: NFSProfileDataManager._check_special_case()

    Microvariant 중 허용되는 특수한 경우들을 검사합니다.

    Args:
        locus: 좌위 (예: TH01, D2S441)
        allele: 좌위값 (예: 9.3, 17.3)
        DICT_MARKERS: 마커 딕셔너리

    Returns:
        bool: 특수 케이스 여부
    """
    # Y-STR 마커는 모두 허용
    if locus in DICT_MARKERS["Y23"]:
        return True

    # 소수점이 없으면 특수 케이스 아님
    if "." not in allele:
        return False

    decimal_place = allele.split(".")[1]

    # .2는 모두 허용
    if decimal_place == "2":
        return True

    # 좌위별 특수 케이스
    if locus == "TH01" and allele == "9.3":
        return True
    elif locus == "D2S441" and allele == "9.1":
        return True
    elif locus == "D1S1656" and allele in ("17.3", "18.3"):
        return True
    elif locus in ("Penta E", "Penta D") and decimal_place in ("2", "3"):
        return True

    return False


def archived_transform_set_to_list(set_input: set) -> list:
    """Allele 값 집합을 정렬된 리스트로 변환

    원래 위치: NFSProfileDataManager._transform_set_to_list()

    숫자형 allele는 숫자로 정렬하고, 문자형 allele는 문자로 정렬합니다.

    Args:
        set_input: Allele 값 집합

    Returns:
        정렬된 allele 리스트
    """
    def is_number(string: str) -> bool:
        try:
            float(string)
            return True
        except (ValueError, OverflowError):
            return False

    # 숫자형과 문자형 분리
    num_input = list(filter(is_number, set_input))
    num_input.sort(key=float)
    str_input = list(filter(lambda x: not is_number(x), set_input))
    str_input.sort()

    # 문자형이 있으면 문자형 우선, 없으면 숫자형 반환
    if str_input:
        return str_input
    else:
        return [str(s) for s in num_input]


def archived_handle_nc_nd_profiles(
    code_evidence: str,
    list_marker: list
) -> Optional[Tuple[Dict[str, str], List[str]]]:
    """NC/ND 프로필 처리

    원래 위치: NFSProfileDataManager._handle_nc_nd_profiles()

    Args:
        code_evidence: 증거물 코드 ("NC" 또는 "ND")
        list_marker: 마커 리스트

    Returns:
        tuple: (프로필 딕셔너리, 특이사항 리스트) 또는 None (NC/ND가 아닌 경우)
    """
    if code_evidence == "ND":
        string_profile = {locus: "ND" for locus in list_marker}
        str_etc = ["ND : 디엔에이형이 검출되지 않음."]
        return string_profile, str_etc
    elif code_evidence == "NC":
        string_profile = {locus: "NC" for locus in list_marker}
        str_etc = ["NC : 디엔에이형을 결정할 수 없음."]
        return string_profile, str_etc
    return None


def archived_export_to_str(
    df_profile: pd.DataFrame,
    code_evidence: str,
    list_marker: list,
    y23: bool = True,
    DICT_MARKERS: dict = None,
    TA_THRESHOLD: int = 2,
    export_df_in_set_func = None
) -> Tuple[Dict[str, str], List[str]]:
    """감정물번호의 프로필을 문자열로 구성된 프로필 딕셔너리 형태로 반환하고, 프로필 내 특이사항을 리스트로 정리해 반환한다.

    원래 위치: NFSProfileDataManager.export_to_str()

    ⚠️ 주의: 이 메서드는 더 이상 사용되지 않습니다.
             향후 유사한 기능이 필요할 경우 참조 목적으로만 사용하세요.

    기능:
    - NC/ND 프로필 처리
    - 미세변이(Microvariant) 감지 및 표기
    - 혼합 프로필 감지 및 표기
    - 특수 케이스 처리 (TH01 9.3, D2S441 9.1 등)

    Args:
        df_profile: 프로필 DataFrame
        code_evidence: 감정물 유형. e.g. 대조, 대표, NC, ND
        list_marker: 사용할 좌위 마커 리스트
        y23: Y-STR 마커 사용 여부
        DICT_MARKERS: 마커 딕셔너리
        TA_THRESHOLD: 혼합 판단 임계값
        export_df_in_set_func: export_df_in_set() 함수 (NFSProfileDataManager의 메서드)

    Returns:
        tuple: (dict, list) = (문자열로 구성된 프로필 딕셔너리, 프로필내 특이사항 리스트)

    Examples:
        >>> # NC 프로필
        >>> profile, notes = archived_export_to_str(df, "NC", markers)
        >>> profile
        {"D3S1358": "NC", "vWA": "NC", ...}
        >>> notes
        ["NC : 디엔에이형을 결정할 수 없음."]

        >>> # 미세변이 포함 프로필
        >>> profile, notes = archived_export_to_str(df, "2025-C-6697-1", markers)
        >>> profile
        {"D3S1358": "15-16*", "vWA": "14-17", ...}
        >>> notes
        ["* : 미세변이 (검출값 : 15.3)"]

        >>> # 혼합 프로필
        >>> profile, notes = archived_export_to_str(df, "2025-C-6697-2", markers)
        >>> profile
        {"D3S1358": "15/16/17", "vWA": "14/17/18", ...}
        >>> notes
        ["/ : 혼합 디엔에이형."]
    """
    # 1. NC/ND 프로필 처리
    nc_nd_result = archived_handle_nc_nd_profiles(code_evidence, list_marker)
    if nc_nd_result:
        return nc_nd_result

    # 2. 변수 초기화
    string_profile = {}
    flag_NC = False
    flag_ND = False
    cnt_microvariant = 0
    str_etc = []
    str_etc_microvariant = []
    temp_profile = {}

    # 3. 대조, 대표 프로필 처리
    if export_df_in_set_func is None:
        raise ValueError("export_df_in_set_func를 제공해야 합니다")

    df_profile_set = export_df_in_set_func()
    series_profile = df_profile_set[df_profile_set["감정물번호"] == code_evidence].iloc[0]

    for locus in list_marker:
        alleles = archived_transform_set_to_list(set(series_profile[locus]))
        temp_alleles = []
        if len(alleles) == 0:
            temp_alleles.append("NC")
            flag_NC = True
        elif alleles[0] == "ND":
            temp_alleles.append("ND")
            flag_ND = True
        elif alleles[0] == "NC":
            temp_alleles.append("NC")
            flag_NC = True
        else:
            for allele in alleles:
                if allele.find("OL") != -1:
                    continue
                modified_allele = allele
                if allele.find(".") != -1:
                    if not archived_check_special_case(locus, allele, DICT_MARKERS):
                        cnt_microvariant = cnt_microvariant + 1
                        decimal_place = allele.split(".")[1]
                        if decimal_place == "1":
                            modified_allele = str(int(float(allele)))
                        else:
                            modified_allele = str(int(float(allele) + 1))
                        modified_allele = modified_allele + "*" * cnt_microvariant
                        str_etc_microvariant.append(
                            "*" * cnt_microvariant
                            + " : 미세변이 (검출값 : {0})".format(allele)
                        )
                temp_alleles.append(modified_allele)
        temp_profile[locus] = temp_alleles

    if archived_check_mixture(series_profile, list_marker, y23, TA_THRESHOLD):
        str_etc.append("/ : 혼합 디엔에이형.")
        for locus, alleles in temp_profile.items():
            string_profile[locus] = "/".join([str(element) for element in alleles])
    else:
        for locus, alleles in temp_profile.items():
            if not y23 and len(alleles) == 1 and alleles[0] != "NC":
                alleles = alleles * 2
            string_profile[locus] = "-".join([str(element) for element in alleles])
            # 특수 케이스
            if locus == "AMEL":
                string_profile[locus] = string_profile[locus].replace("-", "")
            if locus == "DYS385":
                string_profile[locus] = string_profile[locus].replace("-", ", ")

    str_etc = str_etc + str_etc_microvariant
    if flag_ND:
        str_etc.append("ND : 디엔에이형이 검출되지 않음.")
    if flag_NC:
        str_etc.append("NC : 디엔에이형을 결정할 수 없음.")

    return string_profile, str_etc


# ==============================================================================
# 사용 예제 (참고용)
# ==============================================================================
"""
# NFSProfileDataManager와 함께 사용하는 경우:

from module.archived_methods import archived_export_to_str
from module.NFS_PROFILEDATAMANAGER import NFSProfileDataManager

pm = NFSProfileDataManager(kit="STR")
pm.df_profile = pd.read_csv("profile_data.csv")

# 마커 리스트 준비
from module.constants_strprofile import DICT_MARKERS, TA_THRESHOLD
list_marker = DICT_MARKERS["STR"][:-3]  # STR-20

# 프로필 문자열 변환
profile_dict, notes = archived_export_to_str(
    df_profile=pm.df_profile,
    code_evidence="2025-C-6697-1",
    list_marker=list_marker,
    y23=False,
    DICT_MARKERS=DICT_MARKERS,
    TA_THRESHOLD=TA_THRESHOLD,
    export_df_in_set_func=pm.export_df_in_set
)

print("프로필:", profile_dict)
print("특이사항:", notes)
"""
