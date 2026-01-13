"""
Report type phraser mappings for NFSReportWriter.

Each report type defines phraser functions for different block types
across STR and YSTR kits.
"""

from typing import Dict, Callable
import module.NFS_REPORTPHRASER as NFS_RP
from dataclasses import dataclass
from typing import Callable

from typing import Dict, List

# ==================== 키트별 유전자 마커 정의 ====================
# 키트마다 사용하는 좌위 마커를 감정서 표에 나열되는 순서대로 작성한 리스트.

# Type alias for phraser mapping
PhraserMapping = Dict[str, Dict[str, Callable]]


DEFAULT_LR: tuple[str, str] = ("0", "0")

REPORT_TYPE_PHRASERS: Dict[str, PhraserMapping] = {
    "DEFAULT": {
        "STR": {
            "상피세포층": NFS_RP.make_pharase_differential_extraction,
            "검출형": NFS_RP.make_pharase_presume,
            "대조": NFS_RP.make_phrase_none,
            "대조일치": NFS_RP.make_phrase_ref,
            "대표일치": NFS_RP.make_phrase_res,
            "ND": NFS_RP.make_phrase_nd,
            "NC": NFS_RP.make_phrase_nc,
        },
        "YSTR": {
            "대조": NFS_RP.make_phrase_none,
            "대조일치": NFS_RP.make_phrase_ref_y,
            "대표일치": NFS_RP.make_phrase_res_y,
            "ND": NFS_RP.make_phrase_nd_y,
            "NC": NFS_RP.make_phrase_nc_y,
        }
    },
    "DECEASED_ONLY":{
        "STR": {
            "상피세포층": NFS_RP.make_pharase_differential_extraction,
            "검출형": NFS_RP.make_pharase_presume,
           "대조": NFS_RP.make_phrase_deceased,
            "대조일치": NFS_RP.make_phrase_ref,
            "대표일치": NFS_RP.make_phrase_res,
            "ND": NFS_RP.make_phrase_nd,
            "NC": NFS_RP.make_phrase_nc,
        },
        "YSTR": {
            "대조": NFS_RP.make_phrase_none,
            "대조일치": NFS_RP.make_phrase_ref_y,
            "대표일치": NFS_RP.make_phrase_res_y,
            "ND": NFS_RP.make_phrase_nd_y,
            "NC": NFS_RP.make_phrase_nc_y,
        }
    }
    # Future report types can be added here
    # "suspect": {...},
    # "paternity": {...},
}

KEYWORD_IGNORE_EVIDENCE = ["소변", "슬라이드"]
KEYWORD_NONSTUFF = ['면봉', '소변', '혈액', '음모', '늑연골', '구강키트', '심낭혈', '꽁초', '손톱', '질액']

PHRASE_EXPERIMENT_METHOD = "STR 유전자형 분석법(NFS-QI-DAM-01:2025)."
PHRASE_EXPERIMENT_METHOD_YSTR = "1) STR 유전자형 분석법(NFS-QI-DAM-01:2025).\r\n2) Y-STR 유전자형 분석법(NFS-QI-DAM-03:2020)."

KEYWORD_SUSPECT = ["피의자", "피혐의자", "용의자", "관계자", "참고인"]

PHRASE_DBSEARCH_RESULT = {
    "결과없음-피의자": "{nickname}의 디엔에이형을 현재까지 수록된 \"디엔에이신원확인정보 데이터베이스\"에서 검색한 결과 일치 건 없음.\r\n",
    "결과없음-현장프로필": "{nickname}의 디엔에이형을 현재까지 수록된 \"디엔에이신원확인정보 데이터베이스\"에서 검색한 결과 일치 건(범죄 현장 등, 구속피의자 등 및 수형인 등) 없음.\r\n",
    "과거건일치-피의자": "{nickname}의 디엔에이형을 현재까지 수록된 \"디엔에이신원확인정보 데이터베이스\"에서 검색한 결과, 다음 [표]의 사건에서 확보된 디엔에이형과 일치함.\r\n",
    "과거건일치-현장프로필": "{nickname}의 디엔에이형을 현재까지 수록된 \"디엔에이신원확인정보 데이터베이스\"에서 검색한 결과, 다음 [표]의 사건에서 확보된 디엔에이형과 일치하고, 구속피의자 등 및 수형인 등과 일치 건 없음.\r\n",
    "수형인일치": "{nickname}의 디엔에이형을 현재까지 수록된 \"디엔에이신원확인정보 데이터베이스\"에서 검색한 결과, 다음 [표]의 수형인 등의 디엔에이형과 일치함.\r\n",
    "구속피의자일치" :"{nickname}의 디엔에이형을 현재까지 수록된 \"디엔에이신원확인정보 데이터베이스\"에서 검색한 결과, 구속피의자 식별코드 \"{code_arrestee}\"의 디엔에이형과 일치함.\r\n"
}

PHRASE_MATCH_PROB = "* 이와 같이 일치된 디엔에이형의 개인식별지수는 한국인 집단에서 {base} x 10{power}임.\r\n"

# 반환 처리용 데이터 클래스
@dataclass(frozen=True)
class ReturnStatus:
    """반환 상태 정의"""
    key: str                    # DataFrame 필터링 키
    single_phrase: str          # 단일 상태일 때 문구
    mixed_phrase: str           # 혼합 상태일 때 문구
    needs_evidence_num: bool    # 증거물 번호 필요 여부
    process_order: int          # 혼합 시 처리 순서 (낮을수록 먼저)

RETURN_STATUSES = [
        ReturnStatus(
            key="반환",
            single_phrase="감정물은 반환함.\r\n",
            mixed_phrase="{} 감정물은 반환하고",
            needs_evidence_num=True,
            process_order=1,
        ),
        ReturnStatus(
            key="독성",
            single_phrase="감정물은 대전과학수사연구소 독성화학과로 반환하였음.\r\n",
            mixed_phrase="{} 감정물은 대전과학수사연구소 독성화학과로 반환했고",
            needs_evidence_num=True,
            process_order=2,
        ),
        ReturnStatus(
            key="폐기",
            single_phrase="감정물은 감정서 발송일로부터 14일 이내에 `반환` 요구가 없을시 폐기처분하겠음.\r\n",
            mixed_phrase="{} 감정물은 감정서 발송일로부터 14일 이내에 `반환` 요구가 없을시 폐기처분하고",
            needs_evidence_num=True,
            process_order=3,
        ),
        ReturnStatus(
            key="전량 소모",
            single_phrase="감정물은 전량 소모하였음.\r\n",
            mixed_phrase="나머지 감정물은 전량 소모하였음",
            needs_evidence_num=False,
            process_order=99,  # 항상 마지막
        ),
    ]

# 결과 내용에 따른 비고 문구 생성용 데이터클래스
@dataclass
class EtcCondition:
    key: str
    phrase: str
    condition: Callable[[str], bool]


ETC_CONDITIONS: list[EtcCondition] = [
    EtcCondition(
        key="수형인일치",
        phrase="수형인 등과 일치건에 대한 검색결과는 대검찰청에서 별도 회보함.\r\n",
        condition=lambda text: "수형인 등과 일치 건 있음" in text
    ),
    EtcCondition(
        key="DB저장",
        phrase=(
            "「디엔에이신원확인정보의 이용 및 보호에 관한 법률」에 따라, "
            "본 건에서 확보된 디엔에이형을 \"디엔에이신원확인정보 데이터베이스\"에 수록하여 관리하겠음.\r\n"
        ),
        condition=lambda text: "일치 건(범죄 현장 등, 구속피의자 등 및 수형인 등)" in text \
                                or "다음 [표]의 사건에서 확보된 디엔에이형과 일치하고, 구속피의자 등 및 수형인 등과 일치 건 없음." in text 
    ),
    EtcCondition(
        key="DB삭제",
        phrase=(
            "「디엔에이신원확인정보의 이용 및 보호에 관한 법률」에 따라, "
            "신원이 확인된 본 건 관련 범죄현장 증거물의 디엔에이형은 데이터베이스에서 삭제하겠음.\r\n"
        ),
        condition=lambda text: "수형인 등과 일치 건 있음" in text \
                                or "구속피의자 식별코드" in text \
                                or "다음 [표]의 사건에서 확보된 디엔에이형과 일치함." in text
    ),
    EtcCondition(
        key="개인식별지수",
        phrase=(
            "개인식별지수란 감정물의 디엔에이가 동일인으로부터 유래되어서 "
            "디엔에이형이 일치할 확률 대 다른 사람으로부터 유래되었으나 우연히 디엔에이형이 일치할 확률의 비임.\r\n"
        ),
        condition=lambda text: "개인식별지수" in text
    ),
    EtcCondition(
        key="YSTR일치",
        phrase="Y-STR 디엔에이형이 일치할 경우, 동일부계 남성이 배제되지 않음.\r\n",
        condition=lambda text: "Y-STR 디엔에이형과 일치함" in text
    ),
]

PHRASE_EMPTY = "{text_num}은 내용물 없음\r\n"

KEYWORDS_NOPROFILE = ["NC", "ND"]

# ==================== 혼합 프로필 판단 상수 ====================
# 키트별 정상 allele 개수 (이 값 초과 시 tri-allelic으로 판단)
# STR: diploid이므로 2개까지 정상, Y-STR: haploid이므로 1개까지 정상
LIMIT_ALLELE_BY_KIT: dict[str, int] = {
    "STR": 2,
    "STR20": 2,
    "YSTR": 1,
}

# ==================== 미세변이(Microvariant) 특수케이스 정의 ====================
# 소수점이 있지만 미세변이 처리를 하지 않는 특수 케이스들

# 일반적으로 허용되는 소수점 자릿수 (모든 좌위에 적용)
MICROVARIANT_ALLOWED_DECIMALS: set[str] = {"2"}

# 좌위별 허용되는 특수 allele 값 {좌위명: {허용값들}}
MICROVARIANT_SPECIAL_ALLELES: dict[str, set[str]] = {
    "TH01": {"9.3"},
    "D2S441": {"9.1"},
    "D1S1656": {"17.3", "18.3"},
}

# 좌위별 허용되는 소수점 자릿수 {좌위명: {허용 소수점들}}
MICROVARIANT_SPECIAL_DECIMALS: dict[str, set[str]] = {
    "Penta E": {"2", "3"},
    "Penta D": {"2", "3"},
}

# Valid report type names (for validation)
VALID_REPORT_TYPES = set(REPORT_TYPE_PHRASERS.keys())
