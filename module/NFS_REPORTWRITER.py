import logging
from typing import Dict, List, Literal, Callable
from . import NFS_REPORTINFORMATION as NFS_RI
from . import NFS_REPORTPHRASER as NFS_RP
from .constants_reportwriter import KEYWORD_IGNORE_EVIDENCE, KEYWORD_NONSTUFF, \
    PHRASE_EXPERIMENT_METHOD, PHRASE_EXPERIMENT_METHOD_YSTR, \
        KEYWORD_SUSPECT, PHRASE_DBSEARCH_RESULT, PHRASE_MATCH_PROB,\
        REPORT_TYPE_PHRASERS
from .NFS_BLOCKMANAGER import BlockProfileManager, BlockProfile
import re
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
        blocks_manager_ystr: BlockProfileManager,
        type_report: str = "default"
    ):
        """감정서 작성기를 초기화합니다.
        NFSReportWriter 인스턴스를 생성하고 감정서 작성에 필요한 
        기본 속성과 블록 매니저를 설정합니다.
            report_data (NFS_RI.NFSReportInformation): 감정서 작성에 필요한 데이터
            blocks_manager_str (BlockProfileManager): STR 형식의 블록 프로필 매니저
            blocks_manager_ystr (BlockProfileManager): YSTR 형식의 블록 프로필 매니저
            type_report (str): 감정서 유형 (기본값: "default")
        Attributes:
            report_data (NFS_RI.NFSReportInformation): 감정서 작성 데이터
            blocks_manager (dict): 블록 유형별 매니저를 저장하는 딕셔너리
                - "STR": STR 형식 블록 매니저
                - "YSTR": YSTR 형식 블록 매니저
            phrases_result (list[str]): 결과 문구를 저장하는 리스트
            type_report (str): 감정서 유형
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

        #4. 감정서 유형 설정
        self.type_report: str = type_report

        logger.debug("NFSReportWriter 초기화 완료")

    # ==================== Profile Content Generation ====================
    def _calculate_likelihood_ratio(self, id_ref: str, kit: Literal["STR", "YSTR"]) -> tuple[str, str]:
        """주어진 프로필 ID에 대한 우도비 계산

        Args:
            id_ref: 프로필 식별자
            kit: 키트 종류 ("STR" 또는 "YSTR")

        Returns:
            tuple[str, str]: 우도비를 나타내는 문자열 튜플 (예: ("1.2", "5") -> 1.2 x 10^5)
        """
        logger.debug(f"우도비 계산 시작 (kit={kit}, id_ref={id_ref})")

        # 1. 키트별 ProfileDataManager 선택
        if kit == "STR":
            profile_manager = self.report_data.pm_str
        else:  # YSTR
            profile_manager = self.report_data.pm_ystr

        # 2. 우도비 계산 (예외 처리)
        try:
            if profile_manager is not None:
                lr = profile_manager.calculate_likelihood_from_profile(id_ref)
                logger.debug(f"우도비 계산 완료 (lr={lr})")
                return lr
            else:
                logger.warning(
                    f"{kit} ProfileDataManager가 None입니다 "
                    f"(id_ref={id_ref}): 기본값 사용"
                )
                return ("0", "0")
        except Exception as e:
            logger.warning(
                f"우도비 계산 실패 (kit={kit}, id_ref={id_ref}): {e}. "
                f"기본값 사용"
            )
            return ("0", "0")
    
    def _extract_gender(self, id_ref: str, kit: Literal["STR", "YSTR"]) -> str:
        """주어진 프로필 ID에 대한 성별 추출

        Args:
            id_ref: 프로필 식별자
            kit: 키트 종류 ("STR" 또는 "YSTR")

        Returns:
            str: 성별 문자열 ("남성", "여성", 또는 "")
        """
        logger.debug(f"성별 추출 시작 (kit={kit}, id_ref={id_ref})")

        # 1. 키트별 ProfileDataManager 선택
        if kit == "STR":
            profile_manager = self.report_data.pm_str
        else:  # YSTR
            profile_manager = self.report_data.pm_ystr

        # 2. 성별 추출 (예외 처리)
        try:
            if profile_manager is not None:
                gender = profile_manager.extract_gender_from_profile(id_ref)
                logger.debug(f"성별 추출 완료 (gender={gender})")          
                return gender
            else:
                logger.warning(
                    f"{kit} ProfileDataManager가 None입니다 "
                    f"(id_ref={id_ref}): 기본값 사용"
                )
                return ""
        except Exception as e:
            logger.warning(
                f"성별 추출 실패 (kit={kit}, id_ref={id_ref}): {e}. "
                f"기본값 사용"
            )
            return ""   

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

        # 1. 성별 및 우도비 
        gender = self._extract_gender(block.id_ref, kit)
        lr = self._calculate_likelihood_ratio(block.id_ref, kit)
     
        # 2. Properties_Phrase 객체 생성
        properties = NFS_RP.Properties_Phrase(
            gender=gender,
            likelihoodratio=lr,
            text_evidence=block.text_phrase,
            nickname=block.nickname
        )

        # 3. Phraser 함수 호출
        phrase = phraser(properties)
        logger.debug(f"결과 문구 생성 완료 (길이={len(phrase)})")
        return phrase

    def _make_contents_experiment_result(
        self,
        phrasers: Dict[str, Dict[str, Callable]]
    ) -> list[str]:
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
        phrases_result = []

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
                    phrases_result.append(phrase)
                    logger.debug(
                        f"{kit} {block_type} 문구 생성 "
                        f"(id_ref={block.id_ref}, nickname={block.nickname})"
                    )

                if blocks:
                    logger.debug(
                        f"{kit} {block_type} 처리 완료 (블록 수={len(blocks)})"
                    )

            logger.debug(f"{kit} 블록 처리 완료")
        
        return phrases_result
    
    def make_contents_evidence(self) -> str:
        """증거물명 리스트를 감정서에 바로 쓸 수 있는 형태로 편집"""
        
        lines_evidence = self.report_data.evidenceinfo['감정물'].tolist()
        # 1. 파싱 및 필터링
        evidence = {}
        for line in lines_evidence:
            key = line.split(':')[0][1:-1]
            item = line.split('호:')[1]
            if not any(kw in item for kw in KEYWORD_IGNORE_EVIDENCE):
                evidence[key] = item
        
        # 2. 키 정규화 (M/F, a/b 등 접미사 제거)
        normalized = {}
        for key, item in evidence.items():
            if key.endswith(('M', 'F')) or key[-1].isalpha():
                normalized[key[:-1]] = item
            else:
                normalized[key] = item
        
        # 3. 현물 증거물에 실험 부위 작성란 추가
        has_sub_items = {k[:-1] for k in evidence if k[-1].isalpha()}
        
        for key, item in normalized.items():
            is_physical = not any(kw in item for kw in KEYWORD_NONSTUFF)
            if is_physical and key not in has_sub_items:
                normalized[key] = f'{item}\r\n        - '
        
        # 4. 키 정렬 (예: 1-1, 1-2, 2-1 순)
        num_pattern = re.compile(r'\d+')
        sorted_keys = sorted(
            normalized.keys(),
            key=lambda k: (
                int(num_pattern.findall(k)[0]),
                int(num_pattern.findall(k)[1]) if len(num_pattern.findall(k)) >= 2 else 0
            )
        )
        
        # 5. 출력 텍스트 생성
        lines_output = []
        for key in sorted_keys:
            if key[-1].isnumeric():
                lines_output.append(f'증{key}호: {normalized[key]}')
            else:
                lines_output.append(f'\t증{key}호:')
        
        return '\r\n'.join(lines_output)

    def make_contents_experiment_methods(self) -> str:
        """실험방법 리스트를 감정서에 바로 쓸 수 있는 형태로 편집"""
        if self.blocks_manager['YSTR'].number_of_blocks == 0:
            return PHRASE_EXPERIMENT_METHOD
        else:
            return PHRASE_EXPERIMENT_METHOD_YSTR

    def _make_contents_dbsearch_results(self) -> str:
        """DB 검색 결과를 감정서에 바로 쓸 수 있는 형태로 편집"""
        df_search = self.report_data.evidenceinfo[self.report_data.evidenceinfo["검색_결과"] != "검색 안함"]
        phrase_search = ""
        for idx, result in df_search.iterrows():
            nickname = result["대조_이름"]
            id = result["감정물번호"]
            is_suspect = any(keyword in nickname for keyword in KEYWORD_SUSPECT)
            if result["검색_결과"] == "결과 없음":
                if is_suspect:
                    phrase_search = PHRASE_DBSEARCH_RESULT['결과없음-피의자'].format(nickname=nickname)
                else:
                    phrase_search = PHRASE_DBSEARCH_RESULT['결과없음-현장프로필'].format(nickname=nickname)
            elif result["검색_결과"] == "과거건 일치": 
                if is_suspect:
                    phrase_search = PHRASE_DBSEARCH_RESULT['과거건일치-피의자'].format(nickname=nickname)
                    base, power = self._calculate_likelihood_ratio(id, kit="STR")
                    phrase_search += PHRASE_MATCH_PROB.format(base=base, power=power)
                else:
                    phrase_search = PHRASE_DBSEARCH_RESULT['과거건일치-현장프로필'].format(nickname=nickname)
            elif result["검색_결과"] == "수형인 일치":
                phrase_search = PHRASE_DBSEARCH_RESULT['수형인일치'].format(nickname=nickname)
            elif result["검색_결과"] == "구속피의자 일치":
                code_arrestee = result["comment"] # DB결과 정리시 comment 컬럼에 구속피의자 식별코드 저장
                phrase_search = PHRASE_DBSEARCH_RESULT['구속피의자일치'].format(nickname=nickname, code_arrestee=code_arrestee)
                base, power = self._calculate_likelihood_ratio(id, kit="STR")
                phrase_search += PHRASE_MATCH_PROB.format(base=base, power=power)
        return phrase_search
    
            # 우도비 계산
            # DB 저장, 보존 유무는 이 후에 따로 처리 고려.
            # 예외 처리 필요: 피의자 일치의 경우
                
    
        
        pass

    def make_contents_result(self) -> str:
        """감정 결과 문구를 감정서에 바로 쓸 수 있는 형태로 편집"""
        logger.info("감정 결과 문구 생성 시작")

        # 1. Phraser 매핑 로드
        if self.type_report not in REPORT_TYPE_PHRASERS:
            raise ValueError(f"유효하지 않은 감정서 유형: {self.type_report}")
        
        phrasers = REPORT_TYPE_PHRASERS[self.type_report]

        # 2. 감정 결과 문구 생성
        phrases_result = self._make_contents_experiment_result(phrasers)

        # 3. DB 검색 결과 추가
        phrase_dbsearch = self._make_contents_dbsearch_results()
        if phrase_dbsearch:
            phrases_result.append(phrase_dbsearch)

        # 4. 최종 문구 결합
        phrase_final = ""
        for idx, phrase in enumerate(phrases_result, start=1):
            phrase_final = phrase_final + f"{idx}) {phrase}\n"
        phrase_final = phrase_final + f"{idx+1}) "    

        logger.info("감정 결과 문구 생성 완료")
        return phrase_final
        



            
            

