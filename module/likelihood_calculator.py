"""개인식별지수(Likelihood Ratio) 계산 모듈

이 모듈은 STR 프로필의 allele frequency를 기반으로
개인식별지수를 계산하는 LikelihoodCalculator 클래스를 제공합니다.

Classes:
    LikelihoodCalculator: 개인식별지수 계산 클래스
"""

import logging
import pandas as pd
import os
from typing import Optional
from .constants_strprofile import PROB_NOMATCH, ALLELE_FREQUENCY_FILENAME
from . import NFS_STRPROFILE as NFS_SP

logger = logging.getLogger(__name__)


class LikelihoodCalculator:
    """개인식별지수(Likelihood Ratio) 계산 클래스

    STR 프로필의 allele frequency를 기반으로 개인식별지수를 계산합니다.

    Attributes:
        df_allele_frequency (pd.DataFrame): Allele frequency 데이터
            - Loci: 마커명 (e.g., "D3S1358")
            - Allele: Allele 값 (e.g., 15.0)
            - Frequency: 해당 allele의 빈도

    Examples:
        >>> calculator = LikelihoodCalculator()
        >>> profile = STRProfile(id="S001", profile={"D3S1358": {"15", "16"}})
        >>> lr = calculator.calculate(profile)
        >>> print(f"{lr[0]} x 10^{lr[1]}")
        4.0 x 10^10
    """

    def __init__(self, df_allele_frequency: Optional[pd.DataFrame] = None):
        """LikelihoodCalculator 초기화

        Args:
            df_allele_frequency: Allele frequency DataFrame.
                                 None이면 기본 파일에서 로드 (테스트 시 mock 주입 가능)
        """
        logger.debug("LikelihoodCalculator 초기화 시작")

        if df_allele_frequency is not None:
            # 주입된 데이터 사용 (테스트용)
            self.df_allele_frequency = df_allele_frequency
            logger.debug("Allele frequency 주입됨 (테스트 모드)")
        else:
            # 기본 파일에서 로드
            module_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(module_dir, ALLELE_FREQUENCY_FILENAME)
            logger.debug(f"Allele frequency 로딩 중: {csv_path}")
            self.df_allele_frequency = pd.read_csv(csv_path)
            logger.info(f"Allele frequency 로딩 완료 (rows={len(self.df_allele_frequency)})")

        logger.debug("LikelihoodCalculator 초기화 완료")

    def calculate(self, str_profile: NFS_SP.STRProfile) -> tuple[str, str]:
        """STRProfile로부터 개인식별지수 계산

        프로필에 포함된 모든 마커를 사용하여 계산합니다.
        (호출자가 generate_STRProfile(STR_20=True)로 마커 제약 적용)

        Args:
            str_profile: 계산할 STR 프로필 (STRProfile 객체)

        Returns:
            tuple: (계수, 지수) e.g., ("4.0", "10") = 4.0 x 10^10

        Examples:
            >>> profile = STRProfile(id="S001", profile={"D3S1358": {"15", "16"}})
            >>> calculator = LikelihoodCalculator()
            >>> lr = calculator.calculate(profile)
            >>> print(f"{lr[0]} x 10^{lr[1]}")
            4.0 x 10^10
        """
        logger.debug(f"개인식별지수 계산 시작 (id={str_profile.id})")

        # 1. 프로필의 모든 마커 사용 (제약은 상위에서 적용됨)
        list_marker = list(str_profile.profile.keys())
        logger.debug(f"계산 대상 마커 수: {len(list_marker)}")

        # 2. 확률 계산
        prob_match = 1.0

        for marker in list_marker:
            alleles = str_profile.profile[marker]

            if len(alleles) == 0:
                continue

            frequencies = []
            for allele in alleles:
                try:
                    float_allele = float(allele)
                    freq = self._get_allele_frequency(marker, float_allele)
                    frequencies.append(freq)
                except ValueError:
                    # 비숫자 allele 건너뛰기 (AMEL의 "X", "Y" 등)
                    logger.debug(f"비숫자 allele 무시 (marker={marker}, allele={allele})")
                    continue

            if len(frequencies) == 0:
                continue
            elif len(frequencies) == 1:
                # Homozygous (동형접합): 단일 allele
                prob_match = prob_match / (frequencies[0] ** 2)
            else:
                # Heterozygous (이형접합): 두 allele (첫 2개만 사용)
                prob_match = prob_match / (2 * frequencies[0] * frequencies[1])

        # 3. 포맷팅
        result = self._format_likelihood_ratio(prob_match)
        logger.info(f"개인식별지수 계산 완료 (id={str_profile.id}, LR={result[0]}x10^{result[1]})")
        return result

    def _get_allele_frequency(self, marker: str, allele: float) -> float:
        """Allele frequency 테이블에서 빈도값 조회

        Args:
            marker: 마커명 (e.g., "D3S1358")
            allele: Allele 값 (e.g., 15.0)

        Returns:
            해당 allele의 frequency (테이블에 없으면 PROB_NOMATCH)
        """
        cond1 = self.df_allele_frequency["Loci"] == marker
        cond2 = self.df_allele_frequency["Allele"] == allele
        df_frequency = self.df_allele_frequency[cond1 & cond2]

        if df_frequency.shape[0] > 0:
            return df_frequency.iloc[0]["Frequency"]
        else:
            logger.debug(f"Allele frequency 테이블에 없음 (marker={marker}, allele={allele}), PROB_NOMATCH={PROB_NOMATCH} 사용")
            return PROB_NOMATCH

    @staticmethod
    def _format_likelihood_ratio(prob_match: float) -> tuple:
        """확률값을 감정서 형식으로 변환

        Args:
            prob_match: 계산된 확률값 (e.g., 40800000000.0)

        Returns:
            tuple: (계수, 지수) e.g., ("4.0", "10") for 4.0 x 10^10

        Examples:
            >>> LikelihoodCalculator._format_likelihood_ratio(40800000000.0)
            ('4.0', '10')
        """
        text_prob = "{0:.2e}".format(prob_match)  # '4.08e+10'
        text_prob = text_prob[:3] + text_prob[4:]  # '4.0e+10' (버림)
        return tuple(text_prob.split("e+"))
