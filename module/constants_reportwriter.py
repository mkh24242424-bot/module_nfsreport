"""
Report type phraser mappings for NFSReportWriter.

Each report type defines phraser functions for different block types
across STR and YSTR kits.
"""

from typing import Dict, Callable
import module.NFS_REPORTPHRASER as NFS_RP

# Type alias for phraser mapping
PhraserMapping = Dict[str, Dict[str, Callable]]

REPORT_TYPE_PHRASERS: Dict[str, PhraserMapping] = {
    "default": {
        "STR": {
            "대조": NFS_RP.make_phrase_deceased,
            "대조일치": NFS_RP.make_phrase_ref,
            "대표일치": NFS_RP.make_phrase_res,
            "ND": NFS_RP.make_phrase_nd,
            "NC": NFS_RP.make_phrase_nc,
        },
        "YSTR": {
            "대조": NFS_RP.make_phrase_suspect_match_y,
            "대조일치": NFS_RP.make_phrase_ref_y,
            "대표일치": NFS_RP.make_phrase_res_y,
            "ND": NFS_RP.make_phrase_nd_y,
            "NC": NFS_RP.make_phrase_nc_y,
        }
    },
    "deceased_only":{
        "STR": {
            "대조": NFS_RP.make_phrase_deceased,
        },
        "YSTR": {}
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

# Valid report type names (for validation)
VALID_REPORT_TYPES = set(REPORT_TYPE_PHRASERS.keys())
