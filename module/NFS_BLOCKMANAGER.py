import logging
from typing import Literal, Iterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from module.contants_blockmanager import COLNAME_PER_KIT, KEYWORDS_PAIREDPROFILE, PAIR_TEXTEVIDENCE
import pandas as pd
import re
from collections import defaultdict

logger = logging.getLogger(__name__) 



class ProfileBlock(ABC):
    """블록 공통 인터페이스"""
    indexes: list
    type_block: str
    text_evidencenumber: str
    @abstractmethod
    def get_singles(self) -> Iterator['SingleProfileBlock']:
        ...


class SingleProfileBlock(ProfileBlock):
    """단일 블록"""
    def __init__(self, indexes: list, type_block: str,nickname: str, id_ref: str):
        self.indexes = indexes
        self.type_block = type_block
        self.nickname = nickname
        self.id_ref = id_ref
    
    def get_singles(self) -> Iterator['SingleProfileBlock']:
        yield self


class PairedProfileBlock(ProfileBlock):
    """순서 있는 두 SingleBlock의 쌍"""
    def __init__(self, first: SingleProfileBlock, second: SingleProfileBlock, type_block:str):
        self.first = first
        self.second = second
        type_block = type_block
    @property
    def indexes(self) -> list:
        return self.first.indexes
    
    @property
    def text_evidencenumber(self) -> str:
        return self.first.text_evidencenumber
    
    def get_singles(self) -> Iterator[SingleProfileBlock]:
        yield self.first
        yield self.second


# @dataclass
# class BlockProfile:
#     idx_first: str
#     nickname: str
#     text_table: str
#     text_phrase: str
#     id_ref: str


class BlockProfileManager:
    """블록 프로필 관리 클래스

    증거물 정보를 프로필 유형별로 그룹화하고,
    각 유형에 맞는 ProfileBlock 객체를 생성합니다.

    주요 기능:
    - 프로필 유형별 코드 그룹화 (대조, 대조일치, 대표일치, ND, NC)
    - 멀티인덱스를 통한 빠른 데이터 조회
    - 증거물 텍스트 자동 생성 (표기번호, 체액 반응 포함)

    Attributes:
        kit: 키트 종류 ("STR" 또는 "YSTR")
        COL_NICKNAME: 키트별 대조 이름 컬럼명
        COL_REPORTED: 키트별 기재 여부 컬럼명
        COL_TEXT_EVIDENCE: 키트별 표기번호 컬럼명
        COL_CODE: 키트별 코드 컬럼명
        COL_TYPE: 키트별 프로필 유형 컬럼명
        codes_groupby_type: 프로필 유형별 코드 딕셔너리
        info_indexed: 멀티인덱스 DataFrame (코드, 유형)
        blocks: 유형별 생성된 블록 딕셔너리
        evidence_text_generator: 증거물 텍스트 생성기

    Examples:
        >>> info = df[df["기재_여부"] == "기재"]
        >>> manager = BlockProfileManager(info, kit="STR")
        >>> manager.generate_blocks()
        >>> len(manager.blocks['대조'])

    See Also:
        EvidenceTextGenerator: 증거물 텍스트 생성을 담당하는 헬퍼 클래스
        NFSReportWriter: 이 매니저를 사용하는 상위 감정서 작성 클래스
    """

    def __init__(self, info_written: pd.DataFrame, kit: str = "STR"):
        """블록 프로필 매니저 초기화

        기재된 증거물 정보를 기반으로 프로필 블록을 관리하는 매니저를 초기화합니다.
        증거물 유형별로 코드를 그룹화하고, 블록 생성을 위한 인덱싱을 수행합니다.

        Args:
            info_written: 기재된 증거물 정보 DataFrame (기재_여부 == "기재"로 필터링된 데이터)
            kit: 키트 종류. 기본값은 "STR"

        Raises:
            ValueError: kit이 "STR" 또는 "YSTR"이 아닌 경우

        Examples:
            >>> info_written = df[df["기재_여부"] == "기재"]
            >>> manager = BlockProfileManager(info_written=info_written, kit="STR")
            >>> manager.generate_blocks()
        """
        self.info_written = info_written
        logger.debug(f"BlockProfileManager 초기화 시작 (kit={kit}, 증거물 수={len(info_written)})")

        # 1. 입력 검증
        if kit not in COLNAME_PER_KIT:
            logger.error(f"잘못된 kit 값: {kit}. 'STR' 또는 'YSTR'이어야 합니다.")
            raise ValueError(
                f"kit은 'STR' 또는 'YSTR'이어야 합니다. 입력값: {kit}"
            )

        if len(info_written) == 0:
            logger.debug("빈 DataFrame으로 초기화됨 (기재된 증거물 없음)")

        # 2. 키트별 컬럼명 설정
        col_config = COLNAME_PER_KIT[kit]
        self.COL_NICKNAME = col_config["NICKNAME"]
        self.COL_REPORTED = col_config["REPORTED"]
        self.COL_TEXT_EVIDENCE = col_config["TEXT_EVIDENCE"]
        self.COL_CODE = col_config["CODE"]
        self.COL_TYPE = col_config["TYPE"]
        self.kit = kit

        # 3. 프로필 유형별 코드 그룹화
        self.codes_groupby_type = (
            info_written.groupby(self.COL_TYPE)[self.COL_CODE]
            .unique()
            .to_dict()
        )
        logger.debug(
            f"프로필 유형별 코드 그룹화 완료 (유형 수={len(self.codes_groupby_type)})"
        )

        # 4. 멀티인덱스 생성 (코드, 유형으로 빠른 조회)
        # reset_index()로 원본 인덱스를 'index' 컬럼으로 보존 (증거물 연속성 유지)
        # set_index()로 (코드, 유형) 멀티인덱스 설정
        self.info_indexed = (
            info_written.reset_index()
            .set_index([self.COL_CODE, self.COL_TYPE])
        )

        # 5. 블록 저장소 및 텍스트 생성기 초기화
        self.blocks:list[SingleProfileBlock] = []
        self.evidence_text_generator = EvidenceTextGenerator(info_written.copy())
        self.generate_blocks()
        logger.debug("BlockProfileManager 초기화 완료")
    
    @property
    def number_of_blocks(self) -> int:
        """생성된 블록의 총 개수 반환"""
        return len(self.blocks)

    def generate_blocks(self):
        """모든 블록 유형 생성

        프로필 유형별로 블록을 생성하여 self.blocks에 저장합니다.
        5가지 블록 유형을 생성:
        - 대조: 대조 프로필 블록
        - 대조일치: 대조 프로필과 일치하는 일반 프로필 블록
        - 대표일치: 대표 프로필과 일치하는 일반 프로필 블록
        - ND: No Data 블록
        - NC: No Conclusion 블록

        Examples:
            >>> manager = BlockProfileManager(info_written, kit="STR")
            >>> manager.generate_blocks()
            >>> len(manager.blocks['대조'])

        See Also:
            _generate_blocks_ref: 대조 블록 생성
            _generate_blocks_match: 일치 블록 생성
            _generate_blocks_noprofile: ND/NC 블록 생성
        """
        logger.debug("블록 생성 시작")

        # 1. 블록 저장소 초기화
        # self.blocks = {
        #     '대조': [],
        #     '대조일치': [],
        #     '대표일치': [],
        #     'ND': [],
        #     'NC': [] # 추후에 필요시 블록 종류 추가 가능, 예) LC = 정량 결과 농도 낮아 실험하지 않음, NX: 특정 이유로 실험하지 않음.
        # }

        self.blocks = []

        # 2. 각 유형별 블록 생성
        
        self.blocks.extend(self._generate_blocks_ref())
        logger.debug(f"대조 블록 생성 완료")

        self.blocks.extend(self._generate_blocks_match(type_profile='대조일치'))
        logger.debug(f"대조일치 블록 생성 완료")

        self.blocks.extend(self._generate_blocks_match(type_profile='대표일치'))
        logger.debug(f"대표일치 블록 생성 완료")

        self.blocks.extend(self._generate_blocks_noprofile(type_profile='ND'))
        logger.debug(f"ND 블록 생성 완료")

        self.blocks.extend(self._generate_blocks_noprofile(type_profile='NC'))
        logger.debug(f"NC 블록 생성 완료")

        total_blocks = self.number_of_blocks
        logger.debug(f"블록 생성 완료 (총 {total_blocks}개)")

    def _generate_block(
        self,
        info: pd.DataFrame,
        id_ref: str,
        type_block: str,
        nickname_ref: str = "",
    ) -> SingleProfileBlock:
        """단일 블록 프로필 생성

        증거물 정보 DataFrame으로부터 ProfileBlock 객체를 생성합니다.

        빈 DataFrame이 전달될 경우 빈 텍스트를 가진 블록을 생성합니다.
        (매치되는 일반 프로필이 없는 경우 발생 가능)

        Args:
            info: 증거물 정보 DataFrame. 필수 컬럼: 감정물번호, index (빈 DataFrame 허용)
            id_ref: 참조 ID (감정물번호 또는 특수 코드 like ND/NC)
            nickname_ref: 참조 닉네임. 기본값은 ""

        Returns:
            ProfileBlock: 생성된 블록 프로필 객체

        Examples:
            >>> info = pd.DataFrame({
            ...     "감정물번호": ["2025-C-1-1", "2025-C-1-2"],
            ...     "index": [0, 1]
            ... })
            >>> block = manager._generate_block(info, "2025-C-1-1", "피의자")
            >>> block.id_ref
            "2025-C-1-1"

            >>> # 빈 DataFrame도 허용
            >>> empty_info = pd.DataFrame({})
            >>> block = manager._generate_block(empty_info, "V1", "피해자")
            >>> block.text_table
            ""
        """
        logger.debug(f"블록 생성 시작 (id_ref={id_ref}, 증거물 수={len(info)})")

        # 1. 증거물 Index 추출
        evidence_idx = list(info['index'])
        logger.debug(f"증거물 index 추출 완료 (개수={len(evidence_idx)})")

        # 3. BlockProfile 객체 생성
        block = SingleProfileBlock(
            indexes=evidence_idx,
            nickname=nickname_ref,
            type_block=type_block,
            id_ref=id_ref,
        )

        logger.debug(f"블록 생성 완료 (idx_first={block.indexes[0]})")
        return block        

    def _generate_blocks_ref(self) -> list[SingleProfileBlock]:
        """대조 프로필 블록 생성

        '대조' 유형의 프로필에 대한 블록을 생성합니다.
        각 대조 코드별로 하나의 블록을 생성하며, 닉네임 정보를 포함합니다.

        Returns:
            list[BlockProfile]: 생성된 대조 블록 리스트. 대조 프로필이 없으면 빈 리스트

        Examples:
            >>> manager = BlockProfileManager(info_written, kit="STR")
            >>> blocks = manager._generate_blocks_ref()
            >>> len(blocks)
            2
            >>> blocks[0].nickname
            "피의자"

        See Also:
            _generate_block: 단일 블록 생성 헬퍼
        """
        type_profile = "대조"
        logger.debug(f"{type_profile} 블록 생성 시작")

        # 1. 대조 유형 존재 여부 확인
        if type_profile not in self.codes_groupby_type:
            logger.debug(f"{type_profile} 유형이 없음 (빈 리스트 반환)")
            return []

        # 2. 각 대조 코드별 블록 생성
        blocks = []
        codes = self.codes_groupby_type[type_profile]
        logger.debug(f"{type_profile} 코드 수: {len(codes)}")

        for code in codes:
            info_ref = self.info_indexed.loc[[(code, type_profile)], :]
            id_ref = info_ref.iloc[0]["감정물번호"]
            nickname_ref = info_ref.iloc[0][self.COL_NICKNAME]

            block = self._generate_block(
                info=info_ref,
                id_ref=id_ref,
                nickname_ref=nickname_ref,
                type_block=type_profile
            )
            blocks.append(block)
            logger.debug(f"대조 블록 생성 (code={code}, id_ref={id_ref}, nickname={nickname_ref})")

        logger.debug(f"{type_profile} 블록 생성 완료 (총 {len(blocks)}개)")
        return blocks
    
    def _generate_blocks_match(
        self,
        type_profile: Literal["대표일치", "대조일치"]
    ) -> list[SingleProfileBlock]:
        """일치 블록 생성 (대조일치 또는 대표일치)

        지정된 프로필 유형(대조/대표)과 일치하는 일반 프로필들의 블록을 생성합니다.

        처리 로직:
        - 대조일치: 대조 프로필과 일치하는 일반 프로필들만 포함
        - 대표일치: 대표 프로필 자체 + 일치하는 일반 프로필들 포함 (index 순으로 정렬)

        Args:
            type_profile: 프로필 유형. "대조" 또는 "대표"

        Returns:
            list[BlockProfile]: 생성된 일치 블록 리스트. 해당 유형이 없으면 빈 리스트

        Examples:
            >>> manager = BlockProfileManager(info_written, kit="STR")
            >>> blocks = manager._generate_blocks_match(type_profile="대조")
            >>> len(blocks)
            1
            >>> blocks[0].nickname
            "피의자"

        See Also:
            _generate_block: 단일 블록 생성 헬퍼
        """
        logger.debug(f"{type_profile}일치 블록 생성 시작")

        # 1. 프로필 유형 존재 여부 확인
        if type_profile not in self.codes_groupby_type:
            logger.debug(f"{type_profile} 유형이 없음 (빈 리스트 반환)")
            return []

        # 2. 각 코드별 일치 블록 생성
        blocks = []
        codes = self.codes_groupby_type[type_profile]
        logger.debug(f"{type_profile} 코드 수: {len(codes)}")

        for code in codes:
            # 2-1. 참조 프로필 정보 추출
            info_ref = self.info_indexed.loc[[(code, type_profile)], :]
            id_ref = info_ref.iloc[0]["감정물번호"]
            nickname_ref = info_ref.iloc[0][self.COL_NICKNAME]

            # 2-2. 일치하는 일반 프로필 찾기
            try:
                info_match = self.info_indexed.loc[[(code, "일반")], :]
                logger.debug(f"일치 정보 찾음 (code={code}, 행 수={len(info_match)})")
            except KeyError:
                # 일치하는 일반 프로필이 없는 경우 빈 DataFrame 사용
                info_match = pd.DataFrame({})
                logger.warning(f"매치되는 일반 프로필이 없습니다 (code={code})")

            # 2-3. 대표일치의 경우 대표 프로필 자체도 포함
            if type_profile == "대표일치":
                info_match = pd.concat([info_ref, info_match]).sort_values(by='index')
                logger.debug(f"대표 프로필 포함 (총 행 수={len(info_match)})")
            
            # 2-4. 블록 생성
            if len(info_match) == 0:
                logger.info(f"{type_profile}일치 프로필이 없어 블록 생성하지 않음 (code={code})")
                continue
            block = self._generate_block(
                info=info_match,
                id_ref=id_ref,
                nickname_ref=nickname_ref,
                type_block=type_profile
            )
            blocks.append(block)
            logger.debug(f"{type_profile}일치 블록 생성 (code={code}, id_ref={id_ref})")

        logger.debug(f"{type_profile}일치 블록 생성 완료 (총 {len(blocks)}개)")
        return blocks
    
    def _generate_blocks_noprofile(
        self,
        type_profile: Literal["ND", "NC"]
    ) -> list[SingleProfileBlock]:
        """프로필 없음 블록 생성 (ND 또는 NC)

        프로필이 없거나 결론을 내릴 수 없는 증거물들의 블록을 생성합니다.
        - ND (No Data): DNA가 검출되지 않은 증거물
        - NC (No Conclusion): 결론을 내릴 수 없는 증거물

        Args:
            type_profile: 프로필 유형. "ND" 또는 "NC"

        Returns:
            list[BlockProfile]: 생성된 블록 리스트.
                해당 유형이 없으면 빈 리스트, 있으면 1개 요소 리스트

        Examples:
            >>> manager = BlockProfileManager(info_written, kit="STR")
            >>> blocks = manager._generate_blocks_noprofile(type_profile="ND")
            >>> len(blocks)
            1
            >>> blocks[0].id_ref
            "ND"

        See Also:
            _generate_block: 단일 블록 생성 헬퍼
        """
        logger.debug(f"{type_profile} 블록 생성 시작")

        try:
            # ND/NC 유형의 일반 프로필 조회
            info = self.info_indexed.loc[[(type_profile, "일반")], :]

            # 블록 생성 (id_ref는 "ND" 또는 "NC")
            block = self._generate_block(info, id_ref=type_profile, type_block=type_profile)

            logger.debug(f"{type_profile} 블록 생성 완료 (증거물 수={len(info)})")
            return [block]

        except KeyError:
            # 해당 유형의 프로필이 없는 경우
            logger.info(f"{type_profile} 프로필이 분류 결과에 없습니다 (건너뜀)")
            return []
    
    def _generate_blocks_special(self, column, value) -> list[SingleProfileBlock]:
        """특수 블록 생성 (예: LC, NX)

        지정된 컬럼에서 특정 값을 가진 증거물들의 블록을 생성합니다.
        예: LC (Low Concentration), NX (Not eXamined) 등

        Args:
            column: 필터링할 컬럼명
            value: 필터링할 값

        Returns:
            list[BlockProfile]: 생성된 블록 리스트.
                해당 조건에 맞는 증거물이 없으면 빈 리스트

        Examples:
            >>> manager = BlockProfileManager(info_written, kit="STR")
            >>> blocks = manager._generate_blocks_special("특수_상태", "LC")
            >>> len(blocks)
        """
        logger.debug(f"특수 블록 생성 시작 (column={column}, value={value})")

        # 1. 특수 조건에 맞는 증거물 필터링
        info_special = self.info_indexed.reset_index()
        info_special = info_special[info_special[column] == value]

        if len(info_special) == 0:
            logger.info(f"특수 조건에 맞는 증거물이 없습니다 (column={column}, value={value})")
            return []

        # 2. 블록 생성
        block = self._generate_block(
            info=info_special,
            id_ref=value,
            type_block=value
        )

        logger.debug(f"특수 블록 생성 완료 (증거물 수={len(info_special)})")
        return [block]    
            
    def export_blocks(self, block_type:Literal['single', 'pair'], reaction=False) -> list[ProfileBlock]:
        """생성된 블록 리스트 반환

        Returns:
            list[ProfileBlock]: 생성된 모든 블록 리스트
        """
        # 단일 블록과 비단일블록 나누기
        blocks:list = []
        single_blocks:list[SingleProfileBlock] = []
        nonsingle_blocks:list[SingleProfileBlock] = []
        paired_blocks:list[PairedProfileBlock] = []
        if block_type == 'pair':
            condition = self.info_written[self.COL_TEXT_EVIDENCE].str.contains('|'.join(KEYWORDS_PAIREDPROFILE))
            idx_nonsingle_total = self.info_written[condition].index.to_list()
            for block in self.blocks:
                idxs_nonsingle = [idx for idx in block.indexes if idx in idx_nonsingle_total]
                idxs_single = [idx for idx in block.indexes if idx not in idx_nonsingle_total]
                for idx in idxs_nonsingle:
                    nonsingle_block = SingleProfileBlock(indexes=[idx], 
                                                         type_block=block.type_block, 
                                                         nickname=block.nickname, 
                                                         id_ref=block.id_ref)
                    nonsingle_blocks.append(nonsingle_block)
                profileblock_single = SingleProfileBlock(indexes=idxs_single,
                                                         type_block=block.type_block,
                                                         nickname=block.nickname,
                                                         id_ref=block.id_ref)
                single_blocks.append(profileblock_single)
            # PAIRED BLOCK 생성
            # 1. 따로 따로 생성
            list_type_paired = []
            for first_block in nonsingle_blocks:
                for keyword_first in PAIR_TEXTEVIDENCE.keys():
                     textevidence_first = str(self.info_written.loc[first_block.indexes, self.COL_TEXT_EVIDENCE])#iloc를 써야 할것 같은데?
                     textevidence = re.sub(r'\([^)]*\)', '', textevidence_first) #괄호 제거
                     if keyword_first in textevidence_first:
                         for second_block in nonsingle_blocks:
                             textevidence_second = str(self.info_written.loc[second_block.indexes, self.COL_TEXT_EVIDENCE])
                             text_expected = textevidence + PAIR_TEXTEVIDENCE[keyword_first]
                             if textevidence_second == text_expected:
                                 paired_block = PairedProfileBlock(first=first_block, second=second_block, type_block=keyword_first)
                                 paired_blocks.append(paired_block)
                                 list_type_paired.append(f"{first_block.type_block}:{second_block.type_block}") # 같은 페어를 합치기 위한 참조 리스트
            # 2. 합칠 수 있는 것은 합친다. type이 같으면.
            combined_paired_blocks = []
            indices_dict = defaultdict(list)
            for i, value in enumerate(list_type_paired):
                indices_dict[value].append(i)
            for idx_paired_blocks in indices_dict.values():
                indexes_first = []
                indexes_second = []
                for idx in idx_paired_blocks:
                    indexes_first.extend(paired_blocks[idx].first.indexes)
                    indexes_second.extend(paired_blocks[idx].second.indexes)
                paired_blocks[idx_paired_blocks[0]].first.indexes = indexes_first
                paired_blocks[idx_paired_blocks[0]].second.indexes = indexes_second
                combined_paired_blocks.append(paired_blocks[idx_paired_blocks[0]])
            blocks = single_blocks + combined_paired_blocks
        else:
            blocks = self.blocks
      
        # 텍스트 생성
        for block in blocks:
            block.text_evidencenumber = self.evidence_text_generator.create_text_evidence(indexes=block.indexes, kit=self.kit, reaction=reaction)

        # 정렬
        sorted_blocks = sorted(blocks, key=lambda b: b.indexes[0])

        return sorted_blocks

class EvidenceTextGenerator:
    """증거물 ID를 감정서 형식 텍스트로 변환

    증거물 정보 DataFrame을 받아 감정물번호를 감정서에 사용되는
    형식으로 변환합니다. 연속된 증거물은 "~"로 묶고,
    체액 반응 정보를 괄호로 추가할 수 있습니다.

    주요 기능:
    - 연속 증거물 감지 및 범위 표현 (예: "증1호~증3호")
    - 2개 증거물은 "및"로 연결 (예: "증1호 및 증3호")
    - 체액 반응 정보 포맷팅 (예: "증1호(타액반응 양성)")
    - 동일 반응 감지 및 통합 표시

    Attributes:
        evidenceinfo: 증거물 정보를 담은 pandas DataFrame

    Class Constants:
        REACTION_TYPES: 체액 반응 유형 매핑 (컬럼명 -> 표시명)
        MIN_CHAIN_LENGTH: 범위 표현("~")을 사용할 최소 연속 개수 (기본값: 3)

    Examples:
        >>> gen = EvidenceTextGenerator(evidenceinfo_df)
        >>> gen.create_text_evidence(["2025-C-1-1", "2025-C-1-2", "2025-C-1-3"])
        "증1호~증3호"

        >>> gen.create_text_evidence(["2025-C-1-1", "2025-C-1-5"])
        "증1호 및 증5호"

        >>> gen.create_text_evidence(["2025-C-1-1"], reaction=True)
        "증1호(타액반응 양성)"

    See Also:
        NFSReportWriter: 이 클래스를 사용하는 상위 보고서 작성 클래스
    """

    # ==================== 클래스 상수 ====================
    REACTION_TYPES = {
        "타액_반응": "타액반응",
        "정액_반응": "정액반응",
        "혈흔_반응": "혈흔반응"
    }
    MIN_CHAIN_LENGTH = 3

    # ==================== 초기화 ====================

    def __init__(self, evidenceinfo: pd.DataFrame):
        """증거물 텍스트 생성기 초기화

        증거물 정보 DataFrame을 받아 증거물 번호를 감정서 형식으로
        변환하는 생성기를 초기화합니다.

        Args:
            evidenceinfo: 증거물 정보 DataFrame.
                필수 컬럼: 감정물번호, 표기번호/Y_표기번호, 타액_반응, 정액_반응, 혈흔_반응

        Examples:
            >>> gen = EvidenceTextGenerator(evidenceinfo_df)
            >>> text = gen.create_text_evidence(["2025-C-1-1", "2025-C-1-2"])
        """
        logger.debug(f"EvidenceTextGenerator 초기화 (증거물 수={len(evidenceinfo)})")
        self.evidenceinfo = evidenceinfo
        logger.debug("EvidenceTextGenerator 초기화 완료")

    # ==================== Public Interface ====================

    def create_text_evidence(self, indexes: list, kit: str = "STR", reaction: bool = False) -> str:
        """증거물 ID를 감정서 형식 텍스트로 변환

        증거물 ID 리스트를 받아 감정서에 사용되는 형식으로 변환합니다.
        연속된 증거물은 "~"로 묶고, 체액 반응 정보를 괄호로 추가할 수 있습니다.

        처리 파이프라인:
        1. 증거물 df의 index로 DataFrame 필터링 (_filter_evidence_by_idx)
        2. 특수 케이스 처리 (0개, 1개, 2개 증거물)
        3. 체액 반응 정보 추가 (reaction=True인 경우, _add_reaction_info)
        4. 연속된 증거물 그룹화 (_group_consecutive_evidence)
        5. 최종 텍스트 포맷팅 (_format_evidence_text)

        Args:
            list_id: 증거물 ID 리스트 (감정물번호)
            kit: 키트 종류. 기본값은 "STR"
            reaction: 체액 반응 정보 포함 여부. 기본값은 False

        Returns:
            str: 포맷팅된 증거물 텍스트

        Examples:
            >>> gen = EvidenceTextGenerator(evidenceinfo_df)
            >>> gen.create_text_evidence(["2025-C-1-1", "2025-C-1-2", "2025-C-1-3"])
            "증1호~증3호"

            >>> gen.create_text_evidence(["2025-C-1-1", "2025-C-1-5"])
            "증1호 및 증5호"

            >>> gen.create_text_evidence(["2025-C-1-1"], reaction=True)
            "증1호(타액반응 양성)"

        See Also:
            _filter_evidence_by_ids: 증거물 ID 필터링
            _add_reaction_info: 체액 반응 정보 추가
            _group_consecutive_evidence: 연속 증거물 그룹화
            _format_evidence_text: 최종 텍스트 포맷팅
        """
        logger.debug(f"증거물 텍스트 생성 시작 (kit={kit}, 증거물 수={len(indexes)}, reaction={reaction})")

        # 1. 데이터 필터링
        filtered_df = self._filter_evidence_by_index(indexes, kit)

        # 2. 체액 반응 값 생성
        if reaction:
            filtered_df = self._add_reaction_info(filtered_df)
        

        # 2. 특수 케이스 처리
        evidence_count = len(filtered_df)

        if evidence_count == 0:
            logger.debug("빈 데이터프레임 (결과: 빈 문자열)")
            return ""

        if evidence_count == 1:
            logger.debug("단일 증거물 처리")
            result = filtered_df.iloc[0]["표기번호"]
            logger.debug(f"증거물 텍스트 생성 완료: {result}")
            return result

        if evidence_count == 2:
            logger.debug("2개 증거물 처리 ('및'로 연결)")
            result = f"{filtered_df.iloc[0]['표기번호']} 및 {filtered_df.iloc[1]['표기번호']}"
            logger.debug(f"증거물 텍스트 생성 완료: {result}")
            return result

        # 3. 3개 이상 증거물 처리
        logger.debug(f"3개 이상 증거물 처리 (총 {evidence_count}개)")
        evidence_chains = self._group_consecutive_evidence(filtered_df) # 연속 번호 그룹화
        result = self._format_evidence_text(evidence_chains)
        logger.debug(f"증거물 텍스트 생성 완료: {result}")
        return result

    # ==================== 데이터 전처리 ====================

    def _filter_evidence_by_index(self, indexes: list, kit: str) -> pd.DataFrame:
        """감정물번호 리스트로 증거물 데이터 필터링 및 전처리

        미기재 증거물을 제외하고, 지정된 감정물번호만 필터링합니다.
        연속성 판단을 위해 다음 감정물번호 정보를 추가합니다.

        Args:
            list_id: 필터링할 감정물번호 리스트
            kit: 키트 종류. "STR" 또는 "YSTR"

        Returns:
            필터링 및 전처리된 DataFrame. 컬럼: 표기번호, 감정물번호_다음

        Raises:
            KeyError: kit이 "STR" 또는 "YSTR"이 아닌 경우

        Examples:
            >>> gen = EvidenceTextGenerator(evidenceinfo_df)
            >>> filtered = gen._filter_evidence_by_ids(["2025-C-1-1"], "STR")
            >>> len(filtered)
            1
        """
        logger.debug(f"증거물 필터링 시작 (kit={kit}, 입력 IDX 수={len(indexes)})")

        # 키트별 컬럼명 결정
        if kit not in COLNAME_PER_KIT:
            logger.error(f"잘못된 kit 값: {kit}. 'STR' 또는 'YSTR'이어야 합니다.")
            raise KeyError(f"kit은 'STR' 또는 'YSTR'이어야 합니다. 입력값: {kit}")

        col_text_evidence = COLNAME_PER_KIT[kit]["TEXT_EVIDENCE"]

        df = self.evidenceinfo

        # 1단계: 미기재 제외
        original_size = len(df)
        df = df[df[col_text_evidence] != "미기재"].copy()
        logger.debug(f"미기재 제외 (전: {original_size}, 후: {len(df)})")

        # 2단계: 표기번호 컬럼 추가
        df['표기번호'] = df[col_text_evidence]

        # 3단계: 다음 감정물번호 추가 (list_id 필터링 전에 계산)
        # 이렇게 해야 원본 데이터셋에서의 실제 연속성을 정확히 판단할 수 있음
        df["감정물번호_다음"] = df["감정물번호"].shift(-1)

        # 4단계: 지정된 index만 필터링
        df = df.loc[indexes]
        logger.debug(f"ID 필터링 후 데이터 크기: {len(df)}")

        return df.reset_index(drop=True)

    # ==================== 체액 반응 처리 ====================

    def _add_reaction_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """체액 반응 정보를 DataFrame에 추가

        타액, 정액, 혈흔 반응 정보를 포맷팅하여 표기번호에 추가합니다.
        모든 증거물의 반응이 동일한 경우 동일 반응 문자열을 반환합니다.

        Args:
            df: 증거물 DataFrame. 필수 컬럼: 타액_반응, 정액_반응, 혈흔_반응, 표기번호

        Returns:
            반응 정보가 추가된 DataFrame

        Examples:
            >>> gen = EvidenceTextGenerator(evidenceinfo_df)
            >>> df = pd.DataFrame({
            ...     "표기번호": ["증1호"],
            ...     "타액_반응": ["양성"],
            ...     "정액_반응": ["실험 안함"],
            ...     "혈흔_반응": ["음성"]
            ... })
            >>> df_result, equiv = gen._add_reaction_info(df)
            >>> df_result["표기번호"].iloc[0]
            "증1호(타액반응 양성, 혈흔반응 음성)"
        """
        logger.debug(f"체액 반응 정보 처리 시작 (데이터 수={len(df)})")

        def format_row_reactions(row):
            """한 행의 모든 반응을 포맷팅"""
            reactions = []
            for reaction_col, reaction_name in self.REACTION_TYPES.items():
                value = row[reaction_col]
                if value != "실험 안함":
                    reactions.append(f"{reaction_name} {value}")

            if reactions:
                return f"({', '.join(reactions)})"
            return ""

        # 각 행에 대해 반응 포맷팅
        df["반응실험결과"] = df.apply(format_row_reactions, axis=1)

        # 모든 반응이 동일한지 확인 (2개 이상일 때만)
        if len(df) > 1:
            unique_reactions = df["반응실험결과"].unique()
            if len(unique_reactions) == 1 and unique_reactions[0] != "":
                # 모두 같은 반응이면 마지막만 "(모두 ...)" 형태로 남기고 나머지는 빈 문자열
                equivalent_reaction = unique_reactions[0].replace("(", "(모두 ")
                df["반응실험결과"] = ""
                df.at[df.index[-1], "반응실험결과"] = equivalent_reaction
                logger.debug(f"동일 반응 감지: {equivalent_reaction}")

        # 표기번호에 반응 추가
        df["표기번호"] = df["표기번호"] + df["반응실험결과"]
        logger.debug("체액 반응 정보 처리 완료")

        return df

    # ==================== 증거물 그룹화 및 포맷팅 ====================

    def _group_consecutive_evidence(self, df: pd.DataFrame) -> list[list[str]]:
        """연속된 증거물 번호를 그룹화

        감정물번호가 연속되고 괄호(반응 정보)가 없는 증거물들을
        하나의 그룹으로 묶습니다. 연속성은 '감정물번호_다음' 컬럼으로 판단합니다.

        Args:
            df: 증거물 DataFrame. 필수 컬럼: 표기번호, 감정물번호, 감정물번호_다음

        Returns:
            그룹화된 표기번호 리스트의 리스트

        Examples:
            >>> gen = EvidenceTextGenerator(evidenceinfo_df)
            >>> df = pd.DataFrame({
            ...     "표기번호": ["증1호", "증2호", "증3호", "증5호"],
            ...     "감정물번호": ["2025-C-1-1", "2025-C-1-2", "2025-C-1-3", "2025-C-1-5"],
            ...     "감정물번호_다음": ["2025-C-1-2", "2025-C-1-3", "2025-C-1-5", None]
            ... })
            >>> gen._group_consecutive_evidence(df)
            [["증1호", "증2호", "증3호"], ["증5호"]]
        """
        logger.debug(f"연속 번호 그룹화 시작 (데이터 수={len(df)})")
        if len(df) == 0:
            return []

        # 괄호 여부 확인 (반응 정보가 있으면 연속으로 묶지 않음)
        df["괄호여부"] = df["표기번호"].str.contains(r"\(.*\)", regex=True)

        chains = []
        current_chain = [df.iloc[0]["표기번호"]]

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # 연속 조건: 감정물번호가 연속이고, 괄호가 없음
            is_consecutive = (
                prev_row["감정물번호_다음"] == row["감정물번호"]
                and not row["괄호여부"]
                and not prev_row["괄호여부"]
            )

            if is_consecutive:
                current_chain.append(row["표기번호"])
            else:
                chains.append(current_chain)
                current_chain = [row["표기번호"]]

        chains.append(current_chain)
        logger.debug(f"연속 번호 그룹화 완료 (그룹 수={len(chains)}, 그룹별 크기={[len(c) for c in chains]})")
        return chains

    def _format_evidence_text(self, chains: list[list[str]], equivalent_reaction: str = "") -> str:
        """그룹화된 증거물을 문자열로 포맷팅

        그룹화된 표기번호 리스트를 감정서 형식으로 포맷팅합니다.
        3개 이상 연속된 경우 "증1호~증3호" 형식으로 표현합니다.

        Args:
            chains: 그룹화된 표기번호 리스트
            equivalent_reaction: 동일 반응 문자열. 기본값 ""

        Returns:
            포맷팅된 증거물 문자열

        Examples:
            >>> gen = EvidenceTextGenerator(evidenceinfo_df)
            >>> chains = [["증1호", "증2호", "증3호"], ["증5호"]]
            >>> gen._format_evidence_text(chains)
            "증1호~증3호, 증5호"
            >>> chains = [["증1호", "증2호"]]
            >>> gen._format_evidence_text(chains)
            "증1호, 증2호"
        """
        logger.debug(f"증거물 텍스트 포맷팅 시작 (그룹 수={len(chains)})")
        formatted_chains = []

        for idx, chain in enumerate(chains, 1):
            if len(chain) >= self.MIN_CHAIN_LENGTH:
                # 3개 이상: "증1호~증5호"
                formatted = f"{chain[0]}~{chain[-1]}"
                logger.debug(f"그룹 {idx} 포맷팅 (범위): {formatted}")
                formatted_chains.append(formatted)
            else:
                # 1-2개: "증1호, 증2호"
                formatted = ", ".join(chain)
                logger.debug(f"그룹 {idx} 포맷팅 (개별): {formatted}")
                formatted_chains.append(formatted)

        result = ", ".join(formatted_chains)
        final_result = result + equivalent_reaction
        logger.debug(f"증거물 텍스트 포맷팅 완료: {final_result[:100] if len(final_result) <= 100 else final_result[:100] + '...'}")
        return final_result