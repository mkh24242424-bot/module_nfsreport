import logging
from typing import Dict, Set, Optional, Union

logger = logging.getLogger(__name__)

class STRProfile:
    """
    법의학 실험에서 생성된 STR(Short Tandem Repeat) 데이터를 저장하고 가공하는 클래스

    STR 프로파일은 여러 유전자 좌위(locus)에서의 대립유전자(allele) 정보를 포함하며,
    DNA 감식, 친자확인, 개인식별 등에 사용됩니다.

    Attributes:
        id (str): 프로파일의 고유 식별자 (예: "Sample001", "Evidence_A")
        profile (Dict[str, Set[str]]): 좌위명을 키로, 해당 좌위의 대립유전자 집합을 값으로 하는 딕셔너리
                                     예: {"D3S1358": {"15", "16"}, "vWA": {"14", "17"}}

    Private Attributes:
        __TA_THRESHOLD (int): 혼합 프로파일 판정시 허용할 최대 Triallelic 좌위 수

    Examples:
        >>> # 단일 기여자 프로파일 생성
        >>> profile1 = STRProfile(
        ...     id="Sample001",
        ...     profile={
        ...         "D3S1358": {"15", "16"},
        ...         "vWA": {"14", "17"},
        ...         "FGA": {"21", "24"}
        ...     }
        ... )

        >>> # 다른 프로파일과 매치 확인
        >>> profile2 = STRProfile(id="Sample002", profile={"D3S1358": {"15", "16"}})
        >>> profile1.check_match(profile2)  # True (공통 좌위에서 일치)

        >>> # 혼합 프로파일 생성
        >>> mixed = profile1.union_profiles(profile2)
        >>> print(mixed.id)  # "Sample001 + Sample002"
    """

    def __init__(self, id: str = "", profile: Optional[Dict[str, Set[str]]] = None) -> None:
        """
        STRProfile 인스턴스를 초기화합니다.

        Args:
            id: 프로파일의 고유 식별자
            profile: 좌위-대립유전자 딕셔너리. None인 경우 빈 딕셔너리로 초기화

        Note:
            mutable default argument 문제를 방지하기 위해 profile=None을 사용합니다.
        """
        self.id = id
        self.profile = profile if profile is not None else {}
        self.__TA_THRESHOLD = 0
        logger.debug(f"STRProfile 생성 (id={id}, 좌위 수={len(self.profile)})")

    def __find_common_loci(self, target_profile: Dict[str, Set[str]],
                           query_profile: Dict[str, Set[str]]) -> Set[str]:
        """
        두 STR 프로파일에 공통으로 포함된 좌위명을 찾습니다.

        Args:
            target_profile: 대상 프로파일의 좌위-대립유전자 딕셔너리
            query_profile: 비교할 프로파일의 좌위-대립유전자 딕셔너리

        Returns:
            두 프로파일에 공통으로 존재하는 좌위명들의 집합

        Examples:
            >>> profile1 = {"D3S1358": {"15"}, "vWA": {"14"}}
            >>> profile2 = {"D3S1358": {"16"}, "FGA": {"21"}}
            >>> self._STRProfile__find_common_loci(profile1, profile2)
            {'D3S1358'}
        """
        loci_target = set(target_profile.keys())
        loci_query = set(query_profile.keys())
        return loci_target.intersection(loci_query)

    def check_match(self, query: 'STRProfile') -> bool:
        """
        입력받은 프로파일과의 완전 일치 여부를 확인합니다.

        공통 좌위에서 대립유전자가 정확히 일치하는 경우에만 True를 반환합니다.
        단일 기여자 프로파일 간의 비교에 주로 사용됩니다.

        Args:
            query: 비교할 STRProfile 인스턴스

        Returns:
            모든 공통 좌위에서 대립유전자가 일치하면 True, 그렇지 않으면 False

        Raises:
            TypeError: query가 STRProfile 인스턴스가 아닌 경우

        Examples:
            >>> profile1 = STRProfile("A", {"D3S1358": {"15", "16"}})
            >>> profile2 = STRProfile("B", {"D3S1358": {"15", "16"}})
            >>> profile1.check_match(profile2)
            True

            >>> profile3 = STRProfile("C", {"D3S1358": {"15", "17"}})
            >>> profile1.check_match(profile3)
            False
        """
        if not isinstance(query, STRProfile):
            logger.error(f"TypeError: query must be an STRProfile instance (got {type(query)})")
            raise TypeError("query must be an STRProfile instance")

        logger.debug(f"일치 확인 (self.id={self.id}, query.id={query.id})")
        for locus in self.__find_common_loci(self.profile, query.profile):
            if self.profile[locus] != query.profile[locus]:
                logger.debug(f"일치 확인 결과: False (불일치 좌위={locus})")
                return False
        logger.debug("일치 확인 결과: True")
        return True

    def check_inclusion(self, query: 'STRProfile') -> bool:
        """
        입력받은 프로파일이 현재 프로파일에 포함되는지 확인합니다.

        혼합 프로파일 분석에서 단일 기여자가 혼합물에 포함되어 있는지
        판단할 때 사용됩니다.

        Args:
            query: 포함 여부를 확인할 STRProfile 인스턴스

        Returns:
            query의 모든 대립유전자가 현재 프로파일에 포함되면 True

        Examples:
            >>> mixed = STRProfile("Mixed", {"D3S1358": {"15", "16", "17"}})
            >>> single = STRProfile("Single", {"D3S1358": {"15", "16"}})
            >>> mixed.check_inclusion(single)
            True
        """
        if not isinstance(query, STRProfile):
            logger.error(f"TypeError: query must be an STRProfile instance (got {type(query)})")
            raise TypeError("query must be an STRProfile instance")

        logger.debug(f"포함 확인 (self.id={self.id}, query.id={query.id})")
        for locus in self.__find_common_loci(self.profile, query.profile):
            alleles_target = self.profile[locus]
            alleles_query = query.profile[locus]
            if not alleles_query.issubset(alleles_target):
                logger.debug(f"포함 확인 결과: False (불포함 좌위={locus})")
                return False
        logger.debug("포함 확인 결과: True")
        return True

    def union_profiles(self, query: 'STRProfile') -> 'STRProfile':
        """
        현재 프로파일과 입력된 프로파일의 합집합으로 혼합 프로파일을 생성합니다.

        Args:
            query: 합칠 STRProfile 인스턴스

        Returns:
            두 프로파일의 대립유전자 합집합을 가진 새로운 STRProfile

        Examples:
            >>> profile1 = STRProfile("A", {"D3S1358": {"15", "16"}})
            >>> profile2 = STRProfile("B", {"D3S1358": {"17", "18"}})
            >>> mixed = profile1.union_profiles(profile2)
            >>> mixed.profile["D3S1358"]
            {'15', '16', '17', '18'}
        """
        if not isinstance(query, STRProfile):
            raise TypeError("query must be an STRProfile instance")

        union_profile = STRProfile()
        union_profile.id = f"{self.id} + {query.id}"

        for locus in self.__find_common_loci(self.profile, query.profile):
            alleles_target = self.profile[locus]
            alleles_query = query.profile[locus]
            union_profile.profile[locus] = alleles_target.union(alleles_query)

        return union_profile

    def export_to_str(self) -> Dict[str, str]:
        """
        프로파일 데이터를 문자열 형태로 변환하여 내보냅니다.

        각 좌위의 대립유전자 집합을 하이픈(-)으로 연결된 문자열로 변환합니다.
        숫자 대립유전자는 수치 순으로, 문자 대립유전자는 알파벳 순으로 정렬됩니다.

        Returns:
            좌위명을 키로, 하이픈으로 연결된 대립유전자 문자열을 값으로 하는 딕셔너리

        Examples:
            >>> profile = STRProfile("Test", {"D3S1358": {"16", "15"}, "AMEL": {"X", "Y"}})
            >>> profile.export_to_str()
            {'D3S1358': '15-16', 'AMEL': 'X-Y'}
        """

        def _sort_alleles(allele_set: set) -> list:
            """
            대립유전자 집합을 적절한 순서로 정렬합니다.

            Args:
                allele_set: 정렬할 대립유전자 집합

            Returns:
                정렬된 대립유전자 리스트 (숫자는 수치순, 문자는 알파벳순)
            """

            def _is_numeric(s: str) -> bool:
                """문자열이 숫자인지 확인합니다."""
                try:
                    float(s)
                    return True
                except ValueError:
                    return False

            numeric_alleles = [a for a in allele_set if _is_numeric(a)]
            string_alleles = [a for a in allele_set if not _is_numeric(a)]

            # 숫자 대립유전자는 수치순으로 정렬
            numeric_alleles.sort(key=float)
            # 문자 대립유전자는 알파벳순으로 정렬
            string_alleles.sort()

            # 숫자가 있으면 숫자를 우선, 없으면 문자만 반환
            if numeric_alleles:
                return [str(a) for a in numeric_alleles] + string_alleles
            return string_alleles

        result = {}
        for locus, alleles in self.profile.items():
            sorted_alleles = _sort_alleles(alleles)
            result[locus] = '-'.join(sorted_alleles)

        return result

    def __str__(self) -> str:
        """STRProfile의 문자열 표현을 반환합니다."""
        return f"STRProfile(id='{self.id}', loci_count={len(self.profile)})"

    def __repr__(self) -> str:
        """STRProfile의 개발자용 문자열 표현을 반환합니다."""
        return f"STRProfile(id='{self.id}', profile={self.profile})"
 