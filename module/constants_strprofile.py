"""STR/YSTR 프로필 분석에 사용되는 상수 정의

이 모듈은 국립과학수사연구원(NFS) DNA 감정서 생성 시스템에서 사용되는
STR 및 Y-STR 프로필 분석 관련 상수들을 정의합니다.

Constants:
    DICT_MARKERS: 키트별 유전자 마커 리스트 (STR, YSTR, STR20)
    PROB_NOMATCH: Allele frequency 테이블에 없는 좌위의 기본 빈도값
    TA_THRESHOLD: 혼합 프로필 판단 시 허용되는 최대 tri-allelic 좌위 개수
    STR_24_ADDITIONAL_MARKERS: STR-24가 STR-20 대비 추가된 마커 수
"""

from typing import Dict, List

# ==================== 키트별 유전자 마커 정의 ====================
# 키트마다 사용하는 좌위 마커를 감정서 표에 나열되는 순서대로 작성한 리스트.

DICT_MARKERS: Dict[str, List[str]] = {
    "STR": [
        "AMEL",
        "D3S1358",
        "vWA",
        "D16S539",
        "CSF1PO",
        "TPOX",
        "D8S1179",
        "D21S11",
        "D18S51",
        "D2S441",
        "D19S433",
        "TH01",
        "FGA",
        "D22S1045",
        "D5S818",
        "D13S317",
        "D7S820",
        "D10S1248",
        "D1S1656",
        "D12S391",
        "D2S1338",
        "Penta E",
        "Penta D",
        "SE33",
    ],
    "YSTR": [
        "DYS576",
        "DYS389 I",
        "DYS448",
        "DYS389 II",
        "DYS19",
        "DYS391",
        "DYS481",
        "DYS533",
        "DYS438",
        "DYS437",
        "DYS570",
        "DYS635",
        "DYS390",
        "DYS439",
        "DYS392",
        "DYS393",
        "DYS458",
        "DYS385",
        "DYS456",
        "Y GATA H4",
    ],
    "STR20": [
        "AMEL",
        "D3S1358",
        "vWA",
        "D16S539",
        "CSF1PO",
        "TPOX",
        "D8S1179",
        "D21S11",
        "D18S51",
        "D2S441",
        "D19S433",
        "TH01",
        "FGA",
        "D22S1045",
        "D5S818",
        "D13S317",
        "D7S820",
        "D10S1248",
        "D1S1656",
        "D12S391",
        "D2S1338",
    ],
}

# ==================== 확률 및 임계값 상수 ====================

# Allele frequency 테이블에 존재하지 않는 좌위의 기본 빈도값
PROB_NOMATCH: float = 0.0003

# 혼합 프로필 판단 시 허용되는 최대 tri-allelic 좌위 개수
TA_THRESHOLD: int = 2

# STR-24가 STR-20 대비 추가된 마커 수 (D2S441, D10S1248, D22S1045)
STR_24_ADDITIONAL_MARKERS: int = 3

# ==================== 파일 경로 상수 ====================

# Allele frequency 데이터 파일명 (module 디렉토리 기준)
ALLELE_FREQUENCY_FILENAME: str = "allele_frequency.csv"
