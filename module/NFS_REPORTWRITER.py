import logging
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Callable
from . import NFS_REPORTINFORMATION as NFS_RI
from . import NFS_REPORTPHRASER as NFS_RP
from .constants_reportwriter import KEYWORD_IGNORE_EVIDENCE, KEYWORD_NONSTUFF, \
    PHRASE_EXPERIMENT_METHOD, PHRASE_EXPERIMENT_METHOD_YSTR, \
        KEYWORD_SUSPECT, PHRASE_DBSEARCH_RESULT, PHRASE_MATCH_PROB,\
        REPORT_TYPE_PHRASERS, DEFAULT_LR, RETURN_STATUSES, ETC_CONDITIONS, PHRASE_EMPTY, \
        KEYWORDS_NOPROFILE, MICROVARIANT_ALLOWED_DECIMALS, \
        MICROVARIANT_SPECIAL_ALLELES, MICROVARIANT_SPECIAL_DECIMALS, LIMIT_ALLELE_BY_KIT
from .constants_strprofile import DICT_MARKERS, TA_THRESHOLD
from .NFS_BLOCKMANAGER import BlockProfileManager, SingleProfileBlock, PairedProfileBlock
import re
logger = logging.getLogger(__name__)


@dataclass
class ProfileMeta:
    """프로필 처리 중 수집되는 메타데이터

    Attributes:
        is_mixture: 혼합 프로필 여부
        has_nc: NC 값 포함 여부
        has_nd: ND 값 포함 여부
        microvariant_notes: 미세변이 특이사항 리스트
    """
    is_mixture: bool = False
    has_nc: bool = False
    has_nd: bool = False
    microvariant_notes: list[str] = field(default_factory=list)


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
    _SUPPORTED_KITS = ("STR", "YSTR")

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
                return DEFAULT_LR
        except Exception as e:
            logger.warning(
                f"우도비 계산 실패 (kit={kit}, id_ref={id_ref}): {e}. "
                f"기본값 사용"
            )
            return DEFAULT_LR
    
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

    def _extract_profile_data(self, id_ref, kit:Literal["STR", "STR20", "YSTR"]) -> dict[str,str]:
        if kit in ["STR20", "STR"]:
            profile_manager = self.report_data.pm_str
        else:  # YSTR
            profile_manager = self.report_data.pm_ystr
        flag_STR_20 = True if kit=='STR20' else False
        try:
            if profile_manager is not None:
                if id_ref in KEYWORDS_NOPROFILE:
                    noprofile = {}
                    for marker in DICT_MARKERS[kit]:
                        noprofile[marker]=id_ref
                    return noprofile
                else:
                    return profile_manager.generate_STRProfile(samplename=id_ref, STR_20=flag_STR_20).export_to_str() 
            else:
                logger.warning(
                    f"{kit} ProfileDataManager가 None입니다 "
                )
                return {}
        except Exception as e:
            logger.warning(
                f"프로필 추출 실패 (kit={kit}, id_ref={id_ref}): {e}. "
                f"빈 값 반환"
            )
            return {}   
        return []
    
    
    def _get_processed_evidence_num(self, df_subset) -> str:
        """증거물번호 전처리"""
        list_id = df_subset['감정물번호'].tolist()
        text_num = self.blocks_manager['STR'].evidence_text_generator.create_text_evidence(indexes=list_id, kit="STR")
        text_num = re.sub(r"\(상피세포층\)|\(정자층\)|[a-zA-Z]", "", text_num)
        text_num = " 및 ".join(dict.fromkeys(text_num.split(" 및 ")))
        text_num = ", ".join(dict.fromkeys(text_num.split(", ")))
        return text_num

    def _make_contents_from_block(
        self,
        block: SingleProfileBlock,
        phraser: Callable,
        kit: Literal["STR", "YSTR"] = "STR"
    ) -> str:
        """블록 프로필로부터 감정 결과 문구 생성

        ProfileBlock과 phraser 함수를 사용하여 감정서 결과 문구를 생성합니다.
        성별과 우도비(likelihood ratio)를 추출하여 Properties_Phrase 객체를 만들고,
        phraser 함수에 전달합니다.

        Args:
            block: 블록 프로필 객체
            phraser: 문구 생성 함수 (Properties_Phrase -> str)
            kit: 키트 종류. 기본값은 "STR"

        Returns:
            str: 생성된 감정 결과 문구

        Examples:
            >>> block = ProfileBlock(...)
            >>> phrase = writer._make_contents_from_block(block, make_phrase_ref, "STR")

        See Also:
            NFS_REPORTPHRASER.make_phrase_ref: 대조 문구 생성
            NFS_REPORTPHRASER.make_phrase_res: 대표 문구 생성
        """
        logger.debug(f"결과 문구 생성 시작 (kit={kit}, id_ref={block.id_ref})")

        # 1. 성별 및 우도비 
        gender = self._extract_gender(block.id_ref, kit)
        lr = self._calculate_likelihood_ratio(block.id_ref, kit)
        logger.debug(f"블록의 text {block.text_evidencenumber}")
        # 2. Properties_Phrase 객체 생성
        properties = NFS_RP.Properties_Phrase(
            gender=gender,
            likelihoodratio=lr,
            text_evidence=block.text_evidencenumber,
            nickname=block.nickname
        )

        # 3. Phraser 함수 호출
        phrase = phraser(properties)
        logger.debug(f"결과 문구 생성 완료 (길이={len(phrase)})")
        return phrase

    def _make_contents_from_paired_block(
        self,
        block: PairedProfileBlock,
        phrasers: Dict[str, Callable],
        kit: Literal["STR", "YSTR"] = "STR"
    ) -> str:
        """페어 블록 프로필로부터 감정 결과 문구 생성

        PairedProfileBlock(상피세포층/정자층 쌍)을 받아 두 개의 SingleProfileBlock에 대한
        결과 문구를 각각 생성하고, 이를 합쳐 최종 문구를 반환합니다.

        Args:
            block: 페어 블록 프로필 객체 (first, second SingleProfileBlock 포함)
            phrasers: 블록 타입별 phraser 함수 딕셔너리
            kit: 키트 종류. 기본값은 "STR"

        Returns:
            str: 생성된 감정 결과 문구

        See Also:
            _make_contents_from_block: 단일 블록 문구 생성
        """
        logger.debug(f"결과 문구 생성 시작 (kit={kit}, type={block.type_block})")
        text_evidence = block.text_evidencenumber.replace(f"({block.type_block})", "") #타입 텍스트 지우기
        phraser = phrasers[block.type_block]
        first_phrase = self._make_contents_from_block(block.first, phraser=phrasers[block.first.type_block], kit=kit)
        second_phrase = self._make_contents_from_block(block.second, phraser=phrasers[block.second.type_block], kit=kit)
        phrase = phraser(text_evidence, first_phrase, second_phrase)
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
            >>> RW._make_contents_experiment_result(REPORT_TYPE_PHRASERS["suspect"])
        """
        logger.debug(f"_make_contents_experiment_result 시작 (phraser 타입 수={len(phrasers)})")
        phrases_result = []

        # 1. STR 및 YSTR 키트 처리
        for kit in self._SUPPORTED_KITS:
            logger.debug(f"{kit} 블록 처리 시작")
            block_manager = self.blocks_manager[kit]
            kit_phrasers = phrasers[kit]
            blocks_exported = block_manager.export_blocks(block_type='pair', reaction=True)
            # 2. 각 블록 유형별 처리
            for block_type in kit_phrasers:
                blocks = [block for block in blocks_exported if block.type_block==block_type]
                if len(blocks)==0:
                    continue
                phraser = kit_phrasers[block_type]

                for block in blocks:
                    if isinstance(block, PairedProfileBlock):
                        phrase = self._make_contents_from_paired_block(block, kit_phrasers, kit=kit)
                    else: #SingleProfileBlock
                        phrase = self._make_contents_from_block(
                            block, # type: ignore
                            phraser=phraser,
                            kit=kit
                        )
                    phrases_result.append(phrase)
                    logger.debug(
                        f"{kit} {block_type} 문구 생성 "
                    )

                if blocks:
                    logger.debug(
                        f"{kit} {block_type} 처리 완료 (블록 수={len(blocks)})"
                    )

            logger.debug(f"{kit} 블록 처리 완료")
        
        return phrases_result

    def _make_contents_dbsearch_results(self) -> str:
        """DB 검색 결과를 감정서에 바로 쓸 수 있는 형태로 편집"""
        df_search = self.report_data.evidenceinfo[
            self.report_data.evidenceinfo["검색_결과"] != "검색 안함"
        ]
        
        phrases = []  # 버그 수정: 덮어쓰기 -> 리스트 수집
        
        for _, result in df_search.iterrows():
            nickname = result["대조_이름"]
            evidence_id = result["감정물번호"]
            search_result = result["검색_결과"]
            is_suspect = any(keyword in nickname for keyword in KEYWORD_SUSPECT)
            
            if search_result == "결과 없음":
                key = "결과없음-피의자" if is_suspect else "결과없음-현장프로필"
                phrases.append(PHRASE_DBSEARCH_RESULT[key].format(nickname=nickname))
                
            elif search_result == "과거건 일치":
                key = "과거건일치-피의자" if is_suspect else "과거건일치-현장프로필"
                phrase = PHRASE_DBSEARCH_RESULT[key].format(nickname=nickname)
                if is_suspect:
                    base, power = self._calculate_likelihood_ratio(evidence_id, kit="STR")
                    phrase += PHRASE_MATCH_PROB.format(base=base, power=power)
                phrases.append(phrase)
                
            elif search_result == "수형인 일치":
                phrases.append(PHRASE_DBSEARCH_RESULT["수형인일치"].format(nickname=nickname))
                
            elif search_result == "구속피의자 일치":
                code_arrestee = result["comment"]
                phrase = PHRASE_DBSEARCH_RESULT["구속피의자일치"].format(
                    nickname=nickname, code_arrestee=code_arrestee
                )
                base, power = self._calculate_likelihood_ratio(evidence_id, kit="STR")
                phrase += PHRASE_MATCH_PROB.format(base=base, power=power)
                phrases.append(phrase)
        
        return "\n".join(phrases)  # 또는 기존 반환 형식에 맞게
    
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
        numbered_phrases = []
        for idx, phrase in enumerate(phrases_result, start=1):
            numbered_phrase = f"{idx}) {phrase}"
            numbered_phrase = numbered_phrase.replace("@", f"{idx}-") #상피세포층, Y-STR 결과에서 -로 문단 구분 시 서브 번호 붙여주기.
            numbered_phrases.append(numbered_phrase) 
        next_number = len(phrases_result) + 1
        phrase_final = "\n".join(numbered_phrases) + f"\n{next_number}) "  

        logger.info("감정 결과 문구 생성 완료")
        return phrase_final

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
        
        # 2. 키 정규화 (M/F, a/b 등 접미사 철;)
        normalized = {}
        for key, item in evidence.items():
            if key.endswith(('M', 'F')):
                normalized[key[:-1]] = item
            elif key[-1].isalpha():
                if key[-1]=='a':
                    normalized[key[:-1]] = item
                    normalized[key] = item
                else:
                    normalized[key] = item
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

    def _make_contents_return(self) -> str:
        """반환 문구 정리"""
        phrase_return = []
        df_written = self.report_data.evidenceinfo[self.report_data.evidenceinfo["기재_여부"] == "기재"]
        total_count = len(df_written)
        
        # 상태별 DataFrame 생성
        status_dfs = {
            status.key: df_written[df_written["반환_여부"] == status.key]
            for status in RETURN_STATUSES
        }
        
        # 단일 상태 체크
        for status in RETURN_STATUSES:
            if len(status_dfs[status.key]) == total_count:
                return status.single_phrase
        
        # 혼합 상태 처리 (process_order 순으로 정렬)
        parts = []
        sorted_statuses = sorted(RETURN_STATUSES, key=lambda x: x.process_order)
        
        for status in sorted_statuses:
            df_subset = status_dfs[status.key]
            if not df_subset.empty:
                if status.needs_evidence_num:
                    linked_num = self._get_processed_evidence_num(df_subset)
                    parts.append(status.mixed_phrase.format(linked_num))
                else:
                    parts.append(status.mixed_phrase)
        
        phrase_return = ", ".join(parts) + ".\r\n"
        return phrase_return

    def _make_contents_etc(self, text: str) -> list[str]:
        """비고 문구 정리"""
        phrases_etc = []
        for cond in ETC_CONDITIONS:
            if cond.condition(text):
                phrases_etc.append(cond.phrase)
        return phrases_etc

    def _make_contents_empty_evidence(self) -> str:
        """감정물 없음 문구 생성"""
        df_empty = self.report_data.evidenceinfo[self.report_data.evidenceinfo["기재_여부"] == "내용물 없음"]
        if not df_empty.empty:
            text_num = self._get_processed_evidence_num(df_empty)
            phrase_empty = PHRASE_EMPTY.format(text_num=text_num)
            return phrase_empty
        return ""
    
    def make_contents_remarks(self, phrase_result) -> str:
        """비고 문구를 감정서에 바로 쓸 수 있는 형태로 편집"""
        logger.info("비고 문구 생성 시작")
        
        # 1. 비고 문구 수집
        phrases_etc = []
        
        # 1-1. 기타 조건 문구
        phrases_etc.extend(self._make_contents_etc(phrase_result))
        
        # 1-2. 내용물 없음 문구
        phrase_empty = self._make_contents_empty_evidence()
        if phrase_empty:
            phrases_etc.append(phrase_empty)
        
        # 1-3. 반환 문구
        phrase_return = self._make_contents_return()
        phrases_etc.append(phrase_return)

        # 2. 최종 비고 문구 결합
        phrase_final = ""
        if len(phrases_etc) == 1:
            phrase_final = phrases_etc[0]
        else:
            numbered_phrases = [
                f"{idx}) {phrase}" 
                for idx, phrase in enumerate(phrases_etc, start=1)
            ]
            phrase_final = "\n".join(numbered_phrases) 
        return phrase_final
            
    def make_contents_profile_blocks(
        self,
        kit: Literal["STR", "STR20", "YSTR"] = "STR"
    ) -> tuple[list[list[str]], str]:
        """프로필 데이터를 처리하고 직렬화하여 반환합니다.

        블록 매니저에서 블록을 가져와서:
        1. 프로필 데이터 추출
        2. 특수 케이스 처리 (미세변이, AMEL, 혼합 등)
        3. 직렬화
        4. notes 문자열 생성

        Args:
            kit: 키트 종류 ("STR", "STR20", "YSTR")

        Returns:
            tuple[list[list[str]], str]: (직렬화된 블록 리스트, 특이사항 문자열)
        """
        logger.info(f"표에 넣을 프로필 데이터 생성 시작, kit={kit}")

        markers = DICT_MARKERS[kit]
        block_manager = self.blocks_manager["STR"] if kit in ["STR", "STR20"] else self.blocks_manager[kit]
        blocks = block_manager.export_blocks(block_type='pair', reaction=False)

        serialized_blocks = []
        all_metas: list[ProfileMeta] = []
        microvariant_map: dict[str, int] = {}

        for block in blocks:
            data = []

            if isinstance(block, PairedProfileBlock):
                # 페어 블록 처리
                dict_profile1 = self._extract_profile_data(id_ref=block.first.id_ref, kit=kit)
                dict_profile2 = self._extract_profile_data(id_ref=block.second.id_ref, kit=kit)

                # 첫번째 프로필 처리
                processed1, meta1, microvariant_map = self._process_profile(
                    dict_profile1, kit, microvariant_map
                )
                all_metas.append(meta1)

                # 두번째 프로필 처리
                processed2, meta2, microvariant_map = self._process_profile(
                    dict_profile2, kit, microvariant_map
                )
                all_metas.append(meta2)

                # 직렬화
                text_evidence = block.text_evidencenumber.replace(f"({block.type_block})", "")
                data.append(text_evidence)
                data.append(block.first.text_evidencenumber)
                data.extend(self._serialize_profile(processed1, markers))
                data.append(block.second.text_evidencenumber)
                data.extend(self._serialize_profile(processed2, markers))
            else:
                # 단일 블록 처리
                dict_profile = self._extract_profile_data(id_ref=block.id_ref, kit=kit) # type: ignore

                # 프로필 처리
                processed, meta, microvariant_map = self._process_profile(
                    dict_profile, kit, microvariant_map
                )
                all_metas.append(meta)

                # 직렬화
                evidence_text = (
                    block.text_evidencenumber
                    if block.nickname == ""  # type: ignore
                    else f"{block.text_evidencenumber}\r\n{block.nickname}" # type: ignore
                )
                data.append(evidence_text)
                data.extend(self._serialize_profile(processed, markers))

            logger.debug(f"개별 데이터: {data}")
            serialized_blocks.append(data)

        # notes 문자열 생성
        notes_string = self._build_notes_string(all_metas)

        logger.debug(f"최종 데이터: {serialized_blocks}")
        logger.debug(f"특이사항: {notes_string}")

        return serialized_blocks, notes_string

    def _is_special_case_allele(self, marker: str, allele: str, kit: Literal["STR", "STR20", "YSTR"]) -> bool:
        """비정형 좌위값 중 허용되는 특수 케이스인지 여부를 체크합니다.

        특수 케이스 상수는 constants_reportwriter.py에서 정의됩니다:
        - MICROVARIANT_ALLOWED_DECIMALS: 모든 좌위에서 허용되는 소수점
        - MICROVARIANT_SPECIAL_ALLELES: 좌위별 허용되는 특수 allele 값
        - MICROVARIANT_SPECIAL_DECIMALS: 좌위별 허용되는 소수점 자릿수

        Args:
            marker: 좌위명
            allele: 좌위값 (소수점 포함 문자열)
            kit: 키트 종류

        Returns:
            bool: 특수 케이스 여부 (True면 미세변이 처리 불필요)
        """
        # Y-STR 마커는 모두 특수 케이스로 처리
        if kit == "YSTR":
            return True

        if "." not in allele:
            return True

        decimal_place = allele.split(".")[1]

        # 일반적으로 허용되는 소수점 자릿수 체크
        if decimal_place in MICROVARIANT_ALLOWED_DECIMALS:
            return True

        # 좌위별 특수 allele 값 체크
        if marker in MICROVARIANT_SPECIAL_ALLELES:
            if allele in MICROVARIANT_SPECIAL_ALLELES[marker]:
                return True

        # 좌위별 특수 소수점 자릿수 체크
        if marker in MICROVARIANT_SPECIAL_DECIMALS:
            if decimal_place in MICROVARIANT_SPECIAL_DECIMALS[marker]:
                return True

        return False

    def _process_allele_value(
        self,
        marker: str,
        value: str,
        kit: Literal["STR", "STR20", "YSTR"],
        microvariant_map: dict[str, int]
    ) -> tuple[str, dict[str, int], list[str]]:
        """단일 마커 값을 처리하고 미세변이를 수정합니다.

        Args:
            marker: 좌위명
            value: 마커 값 (예: "15-16", "12/13/14", "NC")
            kit: 키트 종류
            microvariant_map: 미세변이 값 -> 별 개수 매핑 (같은 값은 같은 별 개수)

        Returns:
            tuple[str, dict[str, int], list[str]]: (수정된 값, 갱신된 미세변이 맵, 특이사항 리스트)
        """
        # NC/ND는 그대로 반환
        if value in KEYWORDS_NOPROFILE:
            return value, microvariant_map, []

        # AMEL은 혼합 여부에 따라 후처리되므로 그대로 반환
        if marker == "AMEL":
            return value, microvariant_map, []

        # 구분자 설정
        if "-" in value:
            separator = "-"
        else:
            # 단일 값
            separator = None

        if separator:
            alleles = value.split(separator)
        else:
            alleles = [value]

        processed_alleles = []
        etc_notes = []

        for allele in alleles:
            # OL(Off-ladder) 값은 건너뜀
            if "OL" in allele:
                continue

            modified_allele = allele

            # 소수점이 있는 경우 미세변이 체크
            if "." in allele:
                if not self._is_special_case_allele(marker, allele, kit):
                    # 같은 미세변이 값이 이미 있으면 기존 별 개수 사용
                    if allele in microvariant_map:
                        star_count = microvariant_map[allele]
                    else:
                        # 새로운 미세변이 → 새 별 개수 할당
                        star_count = len(microvariant_map) + 1
                        microvariant_map[allele] = star_count
                        etc_notes.append(
                            f"{'*' * star_count} : 미세변이 (검출값 : {allele})"
                        )

                    decimal_place = allele.split(".")[1]

                    # .1은 내림, 그 외는 올림
                    if decimal_place == "1":
                        modified_allele = str(int(float(allele)))
                    else:
                        modified_allele = str(int(float(allele) + 1))

                    # * 표시 추가
                    modified_allele = modified_allele + "*" * star_count

            processed_alleles.append(modified_allele)

        # 값 재조합
        if separator and processed_alleles:
            result_value = separator.join(processed_alleles)
        elif processed_alleles:
            result_value = processed_alleles[0]
        else:
            result_value = value

        return result_value, microvariant_map, etc_notes

    def _process_amel_value(self, value: str, is_mixture: bool) -> str:
        """AMEL 값을 혼합 여부에 따라 처리합니다.

        비혼합:
            - "X-Y" → "XY"
            - "X-X" → "XX"
            - "X" → "XX"

        혼합:
            - "X-Y" → "X/Y"
            - "X-X" → "X"
            - "X" → "X"

        Args:
            value: AMEL 마커 값
            is_mixture: 해당 프로필의 혼합 여부

        Returns:
            str: 처리된 AMEL 값
        """
        if value in KEYWORDS_NOPROFILE:
            return value

        if is_mixture:
            # 혼합: homozygous는 단일 표현, heterozygous는 "/" 구분
            if value in ("X-X", "X"):
                return "X"
            elif value == "X-Y":
                return "X/Y"
            else:
                # 기타 경우 (예: X-X-Y 등)
                return value.replace("-", "/")
        else:
            # 비혼합: "-" 제거하여 붙임
            if value == "X":
                return "XX"
            else:
                return value.replace("-", "")

    def _is_triallelic(self, value: str, kit: Literal["STR", "STR20", "YSTR"]) -> bool:
        """마커 값이 tri-allelic(정상 allele 개수 초과)인지 체크합니다.

        Args:
            value: 마커 값 (예: "15-16", "12-13-14")
            kit: 키트 종류

        Returns:
            bool: tri-allelic 여부
        """
        # NC/ND는 tri-allelic 아님
        if value in KEYWORDS_NOPROFILE:
            return False

        limit_allele = LIMIT_ALLELE_BY_KIT[kit]
        allele_count = len(value.split("-"))
        return allele_count > limit_allele

    def _process_profile(
        self,
        profile: dict[str, str],
        kit: Literal["STR", "STR20", "YSTR"],
        microvariant_map: dict[str, int] | None = None
    ) -> tuple[dict[str, str], ProfileMeta, dict[str, int]]:
        """dict 형태의 프로필에서 특수 케이스를 처리합니다.

        처리 항목:
        - 혼합 프로필 판단 (tri-allelic 좌위 카운트)
        - 미세변이 처리 (정수화 + * 표시)
        - NC/ND 플래그 수집
        - AMEL 포맷팅

        Args:
            profile: {marker: value} 형태의 프로필 딕셔너리
            kit: 키트 종류
            microvariant_map: 미세변이 값 -> 별 개수 매핑 (같은 값은 같은 별 개수)

        Returns:
            tuple[dict[str, str], ProfileMeta, dict[str, int]]:
                - 처리된 프로필 딕셔너리
                - 메타데이터 (is_mixture, has_nc, has_nd, microvariant_notes)
                - 갱신된 미세변이 맵
        """
        if microvariant_map is None:
            microvariant_map = {}

        markers = DICT_MARKERS[kit]
        processed_profile = {}
        meta = ProfileMeta()
        triallelic_count = 0

        # 1단계: 각 마커별 처리 (미세변이, NC/ND 체크, tri-allelic 카운트)
        for marker in markers:
            value = profile.get(marker, "")

            # NC/ND 플래그 체크
            if value == "NC":
                meta.has_nc = True
            elif value == "ND":
                meta.has_nd = True

            # tri-allelic 체크
            if self._is_triallelic(value, kit):
                triallelic_count += 1

            # 미세변이 처리 (AMEL 제외)
            if marker == "AMEL" or value in KEYWORDS_NOPROFILE:
                processed_profile[marker] = value
            else:
                processed_value, microvariant_map, notes = self._process_allele_value(
                    marker, value, kit, microvariant_map
                )
                processed_profile[marker] = processed_value
                meta.microvariant_notes.extend(notes)

        # 2단계: 혼합 여부 판단
        meta.is_mixture = triallelic_count > TA_THRESHOLD

        # 3단계: AMEL 및 혼합 구분자 처리
        for marker in markers:
            value = processed_profile[marker]
            if marker == "AMEL":
                processed_profile[marker] = self._process_amel_value(value, meta.is_mixture)
            elif meta.is_mixture and value not in KEYWORDS_NOPROFILE:
                processed_profile[marker] = value.replace("-", "/")

        return processed_profile, meta, microvariant_map

    def _serialize_profile(
        self,
        profile: dict[str, str],
        markers: list[str]
    ) -> list[str]:
        """처리된 프로필 딕셔너리를 마커 순서대로 리스트로 변환합니다.

        Args:
            profile: {marker: value} 형태의 처리된 프로필
            markers: 마커 순서 리스트

        Returns:
            list[str]: 마커 순서대로 정렬된 값 리스트
        """
        return [profile.get(marker, "") for marker in markers]

    def _build_notes_string(self, metas: list[ProfileMeta]) -> str:
        """프로필 메타데이터들을 모아서 특이사항 문자열을 생성합니다.

        Args:
            metas: ProfileMeta 리스트

        Returns:
            str: 단락으로 구분된 특이사항 문자열
        """
        notes = []

        # 혼합 프로필 여부
        has_mixture = any(m.is_mixture for m in metas)
        if has_mixture:
            notes.append("/ : 혼합 디엔에이형.")

        # 미세변이 노트 수집 (순서 유지)
        for meta in metas:
            notes.extend(meta.microvariant_notes)

        # NC/ND 플래그
        has_nd = any(m.has_nd for m in metas)
        has_nc = any(m.has_nc for m in metas)

        if has_nd:
            notes.append("ND : 디엔에이형이 검출되지 않음.")
        if has_nc:
            notes.append("NC : 디엔에이형을 결정할 수 없음.")

        return "\r\n".join(notes) if notes else ""
