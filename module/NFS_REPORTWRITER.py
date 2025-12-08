import logging
from typing import Dict, List, Literal, Callable
from . import NFS_REPORTINFORMATION as NFS_RI
from . import NFS_REPORTPHRASER as NFS_RP
from .constants_reportwriter import REPORT_TYPE_PHRASERS, VALID_REPORT_TYPES
from .NFS_BLOCKMANAGER import BlockProfileManager, BlockProfile

logger = logging.getLogger(__name__) 

class NFSReportWriter:
    """NFS 감정서 작성 클래스

    NFSReportInformation 데이터를 기반으로 HWP control을 사용하여
    법의학 DNA 감정서를 작성합니다. STR과 Y-STR 두 키트 유형을
    모두 처리하며, 각 프로필 유형별로 적절한 문구를 생성합니다.

    Attributes:
        report_data: 감정서 작성에 필요한 모든 데이터
        blocks_manager: 키트별 블록 프로필 매니저 (STR, YSTR)
        phrases_result: 생성된 감정 결과 문구 리스트

    Examples:
        >>> info = NFSReportInformation(id_case="2025-C-6845")
        >>> writer = NFSReportWriter(info, ["/path/pic1.jpg"])
        >>> writer.make_contents_default()
    """

    def __init__(
        self,
        report_data: NFS_RI.NFSReportInformation,
        blocks_manager_str: BlockProfileManager,
        blocks_manager_ystr: BlockProfileManager
    ):
        """감정서 작성기를 초기화합니다.
        NFSReportWriter 인스턴스를 생성하고 감정서 작성에 필요한 
        기본 속성과 블록 매니저를 설정합니다.
            report_data (NFS_RI.NFSReportInformation): 감정서 작성에 필요한 데이터
            blocks_manager_str (BlockProfileManager): STR 형식의 블록 프로필 매니저
            blocks_manager_ystr (BlockProfileManager): YSTR 형식의 블록 프로필 매니저
        Attributes:
            report_data (NFS_RI.NFSReportInformation): 감정서 작성 데이터
            blocks_manager (dict): 블록 유형별 매니저를 저장하는 딕셔너리
                - "STR": STR 형식 블록 매니저
                - "YSTR": YSTR 형식 블록 매니저
            phrases_result (list[str]): 결과 문구를 저장하는 리스트
            >>> str_manager = BlockProfileManager()
            >>> ystr_manager = BlockProfileManager()
            >>> writer = NFSReportWriter(
            ...     report_data=info,
            ...     blocks_manager_str=str_manager,
            ...     blocks_manager_ystr=ystr_manager
            ... )
        """

        logger.info(f"NFSReportWriter 초기화 시작 ")

        # 1. 기본 속성 설정
        self.report_data: NFS_RI.NFSReportInformation = report_data

        # 2. 블록 매니저 딕셔너리 설정
        self.blocks_manager = {
            "STR": blocks_manager_str,
            "YSTR": blocks_manager_ystr
        }

        # 3. 결과 문구 저장소 초기화
        self.phrases_result: list[str] = []

        logger.debug("NFSReportWriter 초기화 완료")


    # ==================== Profile Content Generation ====================
    def _make_contents_from_block(
        self,
        block: BlockProfile,
        phraser: Callable,
        kit: Literal["STR", "YSTR"] = "STR"
    ) -> str:
        """블록 프로필로부터 감정 결과 문구 생성

        BlockProfile과 phraser 함수를 사용하여 감정서 결과 문구를 생성합니다.
        성별과 우도비(likelihood ratio)를 추출하여 Properties_Phrase 객체를 만들고,
        phraser 함수에 전달합니다.

        Args:
            block: 블록 프로필 객체
            phraser: 문구 생성 함수 (Properties_Phrase -> str)
            kit: 키트 종류. 기본값은 "STR"

        Returns:
            str: 생성된 감정 결과 문구

        Examples:
            >>> block = BlockProfile(...)
            >>> phrase = writer._make_contents_from_block(block, make_phrase_ref, "STR")

        See Also:
            NFS_REPORTPHRASER.make_phrase_ref: 대조 문구 생성
            NFS_REPORTPHRASER.make_phrase_res: 대표 문구 생성
        """
        logger.debug(f"결과 문구 생성 시작 (kit={kit}, id_ref={block.id_ref})")

        # 1. 키트별 ProfileDataManager 선택
        if kit == "STR":
            profile_manager = self.report_data.pm_str
        else:  # YSTR
            profile_manager = self.report_data.pm_ystr

        # 2. 성별 및 우도비 추출 (예외 처리)
        try:
            if profile_manager is not None:
                gender = profile_manager.extract_gender_from_profile(block.id_ref)
                lr = profile_manager.calculate_likelihood_from_profile(block.id_ref)
                logger.debug(f"프로필 정보 추출 완료 (gender={gender}, lr={lr})")
            else:
                gender = ""
                lr = ("0", "0")
                logger.warning(
                    f"{kit} ProfileDataManager가 None입니다 "
                    f"(id_ref={block.id_ref}): 기본값 사용"
                )
        except Exception as e:
            logger.warning(
                f"프로필 정보 추출 실패 (kit={kit}, id_ref={block.id_ref}): {e}. "
                f"기본값 사용"
            )
            gender = ""
            lr = ("0", "0")

        # 3. Properties_Phrase 객체 생성
        properties = NFS_RP.Properties_Phrase(
            gender=gender,
            likelihoodratio=lr,
            text_evidence=block.text_phrase,
            nickname=block.nickname
        )

        # 4. Phraser 함수 호출
        phrase = phraser(properties)
        logger.debug(f"결과 문구 생성 완료 (길이={len(phrase)})")
        return phrase

    def make_contents_result(
        self,
        phrasers: Dict[str, Dict[str, Callable]]
    ) -> None:
        """외부에서 제공된 phraser 매핑으로 감정 결과 문구 생성

        블록 유형별로 지정된 phraser 함수를 사용하여 모든 블록의
        감정 결과 문구를 생성합니다.

        Args:
            phrasers: Phraser 매핑 딕셔너리
                구조: {kit: {block_type: phraser_function}}
                예: {"STR": {"대조": make_phrase_deceased, ...}, "YSTR": {...}}

        Raises:
            ValueError: phrasers가 올바른 구조가 아닐 경우
            KeyError: 필요한 kit 또는 block_type이 누락된 경우

        Examples:
            >>> from module.constants_reportwriter import REPORT_TYPE_PHRASERS
            >>> RW = NFSReportWriter(info, [])
            >>> RW.make_contents_result(REPORT_TYPE_PHRASERS["suspect"])
        """
        logger.debug(f"make_contents_result 시작 (phraser 타입 수={len(phrasers)})")

        # 1. 검증: 필수 kit이 모두 있는지 확인
        required_kits = ("STR", "YSTR")
        for kit in required_kits:
            if kit not in phrasers:
                raise ValueError(f"phrasers에 '{kit}' kit이 누락되었습니다.")

        # 2. STR 및 YSTR 키트 처리
        for kit in required_kits:
            logger.debug(f"{kit} 블록 처리 시작")
            block_manager = self.blocks_manager[kit]
            kit_phrasers = phrasers[kit]

            # 3. 각 블록 유형별 처리
            for block_type in kit_phrasers:
                # 블록이 존재하지 않으면 스킵
                if block_type not in block_manager.blocks:
                    logger.warning(f"{kit}의 '{block_type}' 블록 타입이 존재하지 않습니다.")
                    continue

                blocks = block_manager.blocks[block_type]
                phraser = kit_phrasers[block_type]

                for block in blocks:
                    phrase = self._make_contents_from_block(
                        block,
                        phraser=phraser,
                        kit=kit
                    )
                    self.phrases_result.append(phrase)
                    logger.debug(
                        f"{kit} {block_type} 문구 생성 "
                        f"(id_ref={block.id_ref}, nickname={block.nickname})"
                    )

                if blocks:
                    logger.debug(
                        f"{kit} {block_type} 처리 완료 (블록 수={len(blocks)})"
                    )

            logger.debug(f"{kit} 블록 처리 완료")

        logger.info(f"make_contents_result 완료 (총 문구 수={len(self.phrases_result)})")

        



            
            

