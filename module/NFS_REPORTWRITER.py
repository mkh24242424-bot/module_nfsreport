import logging
from typing import Dict, List, Literal, Callable

from dataclasses import dataclass
import pandas as pd
from . import NFS_REPORTINFORMATION as NFS_RI
from .NFS_REPORTPHRASER import Properties_Phrase
from .exceptions import DataFrameOperationError, TemplateError

logger = logging.getLogger(__name__)


@dataclass
class Block_Profile:
    idx_first: str
    nickname: str
    text_evidence: str
    id_evidence: str

class NFSReportWriter():
    """NFSReportInformation 인스턴스의 데이터를 토대로 HWP control을 사용하여 감정서를 작성하는 클래스"""
    def __init__(self, report_data:NFS_RI.NFSReportInformation, paths_picture:list):
        logger.info(f"NFSReportWriter 초기화 (id_case={report_data.id_case}, 사진 수={len(paths_picture)})")
        self.report_data:NFS_RI.NFSReportInformation = report_data
        self.paths_picture:list = paths_picture

        self.code_categorized:Dict[str, List[str]] = {}
        self.categorized_info:pd.DataFrame = pd.DataFrame({})
        self.profile_blocks_ref:list = []
        self.profile_blocks = []

        self.code_categorized_ystr:Dict[str, List[str]]  = {}
        self.categorized_info_ystr:pd.DataFrame = pd.DataFrame({})
        self.profile_blocks_ref_ystr:list = []
        self.profile_blocks_ystr:list = []

        self.phrases_result:list = []
        logger.debug("NFSReportWriter 초기화 완료")

    @property
    def switch_kit(self) -> dict:
        """키트별 변수 매핑을 동적으로 반환하는 property.

        재할당 문제 해결: self.code_categorized 등이 재할당되어도
        항상 최신 값을 참조하도록 property로 구현.

        Returns:
            STR/YSTR 키트별 변수 매핑 딕셔너리
        """
        return {
            "STR": {
                "code_categorized": self.code_categorized,
                "profilemanager": self.report_data.pm_str,
                "info_indexed" : self.categorized_info,
                "profile_blocks_ref" : self.profile_blocks_ref,
                "profile_blocks" : self.profile_blocks,
                "colname_nickname" : "대조_이름",
                "colname_reported" : "기재_여부",
                "colname_text_evidence" : "표기번호"
            },
            "YSTR": {
                "code_categorized": self.code_categorized_ystr,
                "profilemanager": self.report_data.pm_ystr,
                "info_indexed" : self.categorized_info_ystr,
                "profile_blocks_ref" : self.profile_blocks_ref_ystr,
                "profile_blocks" : self.profile_blocks_ystr,
                "colname_nickname" : "Y_대조_이름",
                "colname_reported" : "Y_기재_여부",
                "colname_text_evidence" : "Y_표기번호"
            }
        }

    def categorize_profiles(self) -> None:
        """ReportData.df_evidences를 유형별로 분류하여 정리.

        - code_categorized: 코드-프로필_유형을 키-밸류로 정리하여 딕셔너리화
        - df_str_indexed: ReportData.df_evidences를 MultiIndex로 설정하여 빠른 조회 가능
        """
        logger.info("프로필 분류 시작")

        def categorize_code(df: pd.DataFrame, column_prefix: str = "") -> Dict[str, List[str]]:
            """코드를 프로필 유형에 따라 분류.
            
            Args:
                df: 유형별 분류할 리포트 데이터프레임
                column_prefix: 컬럼명 접두사 (Y-STR의 경우 'Y_')
                
            Returns:
                프로필 유형별로 그룹화된 코드 딕셔너리 e.g {V: ['2025-C-3123-1'], S: ['2025-3123-2']}
            """

            code_col = f"{column_prefix}코드"
            profile_col = f"{column_prefix}프로필_유형"

            return df.groupby(profile_col)[code_col].unique().to_dict()
    
        # STR 데이터 처리
        logger.debug("STR 프로필 분류 중")
        evidenceinfo_str = self.report_data.evidenceinfo[self.report_data.evidenceinfo["기재_여부"] == "기재"].copy()
        self.code_categorized = categorize_code(df=evidenceinfo_str)

        # MultiIndex 설정 (기존 groupby 대체)
        # reset_index()로 원본 인덱스를 "index" 컬럼으로 보존한 뒤 MultiIndex 설정
        self.categorized_info = evidenceinfo_str.reset_index().set_index(["코드", "프로필_유형"])
        logger.info(f"STR 프로필 분류 완료 (유형별: {dict((k, len(v)) for k, v in self.code_categorized.items())})")

        # Y-STR 데이터 처리
        logger.debug("YSTR 프로필 분류 중")
        evidenceinfo_ystr = self.report_data.evidenceinfo[self.report_data.evidenceinfo["Y_기재_여부"] == "기재"].copy()
        self.code_categorized_ystr = categorize_code(evidenceinfo_ystr, column_prefix="Y_")

        # MultiIndex 설정 (기존 groupby 대체)
        # reset_index()로 원본 인덱스를 "index" 컬럼으로 보존한 뒤 MultiIndex 설정
        self.categorized_info_ystr = evidenceinfo_ystr.reset_index().set_index(["Y_코드", "Y_프로필_유형"])
        self.categorized_info_ystr.sort_index(inplace=True)  # 조회 성능 향상을 위한 정렬
        logger.info(f"YSTR 프로필 분류 완료 (유형별: {dict((k, len(v)) for k, v in self.code_categorized_ystr.items())})")

    # ==================== Evidence Text Generation ====================
    # 증거물 번호를 감정서 형식으로 변환하는 메서드들

    # 상수 정의
    REACTION_TYPES = {
        "타액_반응": "타액반응",
        "정액_반응": "정액반응",
        "혈흔_반응": "혈흔반응"
    }
    MIN_CHAIN_LENGTH = 3  # ~로 묶을 최소 연속 개수

    def _filter_evidence_by_ids(self, list_id: list, kit: str) -> pd.DataFrame:
        """
        감정물번호 리스트로 증거물 데이터 필터링

        Args:
            list_id: 필터링할 감정물번호 리스트
            kit: 키트 종류 ("STR" or "YSTR")

        Returns:
            필터링 및 전처리된 DataFrame
        """
        logger.debug(f"증거물 필터링 시작 (kit={kit}, 입력 ID 수={len(list_id)})")
        kit_data = self.switch_kit[kit]
        df = self.report_data.evidenceinfo

        # 1단계: 미기재 제외
        original_size = len(df)
        df = df[df[kit_data["colname_text_evidence"]] != "미기재"].copy()
        logger.debug(f"미기재 제외 (전: {original_size}, 후: {len(df)})")

        # 2단계: 표기번호 컬럼 추가
        df['표기번호'] = df[kit_data["colname_text_evidence"]]

        # 3단계: 다음 감정물번호 추가 (list_id 필터링 전에 계산)
        # 이렇게 해야 원본 데이터셋에서의 실제 연속성을 정확히 판단할 수 있음
        # 예: [1,2,3,4,5]에서 4가 미기재면 -> [1,2,3,5]가 되고, 3의 next는 5가 됨
        # 하지만 list_id=[1,2,3,5,6]으로 필터하기 전에 계산하면 3의 next는 4가 됨
        # 그래서 3->5는 연속이 아님을 감지할 수 있음
        df["감정물번호_다음"] = df["감정물번호"].shift(-1)

        # 4단계: 지정된 감정물번호만 필터링
        df = df[df["감정물번호"].isin(list_id)]
        logger.debug(f"ID 필터링 후 데이터 크기: {len(df)}")

        return df.reset_index(drop=True)

    def _format_single_reaction(self, reaction_type: str, value: str) -> str:
        """
        단일 체액 반응 결과를 포맷팅

        Args:
            reaction_type: 반응 유형 ("타액_반응", "정액_반응", "혈흔_반응")
            value: 반응 결과 값

        Returns:
            포맷팅된 반응 문자열 (예: "타액반응 양성") 또는 빈 문자열
        """
        if value == "실험 안함":
            return ""
        return f"{self.REACTION_TYPES[reaction_type]} {value}"

    def _format_reaction_parentheses(self, reaction_text: str) -> str:
        """
        반응 결과를 괄호로 감싸기

        Args:
            reaction_text: 쉼표로 구분된 반응 문자열

        Returns:
            괄호로 감싼 문자열 (예: "(타액반응 양성, 혈흔반응 음성)")
        """
        parts = [x for x in reaction_text.split(",") if x]
        if not parts:
            return ""
        return f"({', '.join(parts)})"

    def _check_equivalent_reaction(self, df: pd.DataFrame) -> str:
        """
        모든 증거물의 반응이 동일한지 확인

        Args:
            df: 반응실험결과 컬럼이 있는 DataFrame

        Returns:
            모두 동일하면 "(모두 ...)" 형식의 문자열, 아니면 빈 문자열
        """
        if len(df) <= 1:
            return ""

        value_counts = df["반응실험결과"].value_counts()
        if len(value_counts) == 1 and value_counts.iloc[0] == len(df):
            # 모두 같은 반응
            return df.iloc[-1]["반응실험결과"].replace("(", "(모두 ")
        return ""

    def _add_reaction_info(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        """
        체액 반응 정보를 DataFrame에 추가

        Args:
            df: 증거물 DataFrame

        Returns:
            (반응 정보가 추가된 DataFrame, 동일 반응 문자열)
        """
        logger.debug(f"체액 반응 정보 처리 시작 (데이터 수={len(df)})")
        # 각 반응 유형 처리
        reactions = []
        for col in ["타액_반응", "정액_반응", "혈흔_반응"]:
            reactions.append(df[col].apply(lambda x: self._format_single_reaction(col, x)))

        # 반응 결과 결합
        combined = reactions[0] + "," + reactions[1] + "," + reactions[2]

        # 빈 문자열 제거 및 괄호 추가
        df["반응실험결과"] = combined.apply(self._format_reaction_parentheses)

        # 모두 같은 반응이면 한 번만 표시
        equivalent_reaction = self._check_equivalent_reaction(df)
        if equivalent_reaction:
            logger.debug(f"동일 반응 감지: {equivalent_reaction}")
            df["반응실험결과"] = ""

        # 표기번호에 반응 추가
        df["표기번호"] = df["표기번호"] + df["반응실험결과"]
        logger.debug("체액 반응 정보 처리 완료")

        return df, equivalent_reaction

    def _group_consecutive_evidence(self, df: pd.DataFrame) -> list[list[str]]:
        """
        연속된 증거물 번호를 그룹화

        Args:
            df: 증거물 DataFrame

        Returns:
            그룹화된 표기번호 리스트 (예: [["증1호", "증2호", "증3호"], ["증5호"]])
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
        """
        그룹화된 증거물을 문자열로 포맷팅

        Args:
            chains: 그룹화된 표기번호 리스트
            equivalent_reaction: 동일 반응 문자열

        Returns:
            포맷팅된 증거물 문자열 (예: "증1호~증3호, 증5호")
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

    def _create_text_evidence(self, list_id: list, kit: str = "STR", reaction: bool = False) -> str:
        """
        증거물 번호를 감정서 형식으로 변환

        연속된 감정물번호는 ~로 묶어 표현하며, 체액 반응 정보를 포함할 수 있습니다.
        기존 123줄 메서드를 6개의 작은 헬퍼 메서드로 분리하여 리팩토링했습니다.

        개선사항:
        - 단일 책임 원칙 적용
        - 복잡도 감소 (13+ → 5)
        - 테스트 가능한 작은 단위로 분리
        - 명확한 메서드명으로 의도 전달

        Args:
            list_id: 증거물 번호 리스트
            kit: 키트 종류 ("STR" or "YSTR")
            reaction: 체액 반응 포함 여부

        Returns:
            포맷팅된 증거물 문자열 (예: "증1호~증3호")

        Examples:
            >>> writer._create_text_evidence(["2023-D-1-1", "2023-D-1-2", "2023-D-1-3"])
            "증1호~증3호"

            >>> writer._create_text_evidence(["2023-D-1-1"], reaction=True)
            "증1호(타액반응 양성)"
        """
        logger.debug(f"증거물 텍스트 생성 시작 (kit={kit}, 증거물 수={len(list_id)}, reaction={reaction})")

        # 1. 데이터 필터링
        df = self._filter_evidence_by_ids(list_id, kit)

        # 2. 특수 케이스 처리
        if len(df) == 0:
            logger.debug("빈 데이터프레임 (결과: 빈 문자열)")
            return ""
        if len(df) == 1:
            # 단일 증거물
            logger.debug("단일 증거물 처리")
            if reaction:
                df, equiv = self._add_reaction_info(df)
                result = df.iloc[0]["표기번호"] + equiv
                logger.debug(f"증거물 텍스트 생성 완료: {result}")
                return result
            result = df.iloc[0]["표기번호"]
            logger.debug(f"증거물 텍스트 생성 완료: {result}")
            return result
        if len(df) == 2:
            # 두 개 증거물: "및"로 연결
            logger.debug("2개 증거물 처리 ('및'로 연결)")
            if reaction:
                df, equiv = self._add_reaction_info(df)
            result = f"{df.iloc[0]['표기번호']} 및 {df.iloc[1]['표기번호']}"
            logger.debug(f"증거물 텍스트 생성 완료: {result}")
            return result

        # 3. 체액 반응 처리
        logger.debug(f"3개 이상 증거물 처리 (총 {len(df)}개)")
        equivalent_reaction = ""
        if reaction:
            df, equivalent_reaction = self._add_reaction_info(df)

        # 4. 연속 번호 그룹화
        chains = self._group_consecutive_evidence(df)

        # 5. 최종 문자열 생성
        result = self._format_evidence_text(chains, equivalent_reaction)
        logger.debug(f"증거물 텍스트 생성 완료: {result}")
        return result

    # ==================== Profile Content Generation ====================

    def make_contents_with_profile(self, phraser: Callable, type_profile:Literal["대표", "대조"], kit:Literal["STR", "YSTR"]="STR") -> None:
        """
            감정서에 들어갈 프로필이 존재하는 증거물(대표, 대조, 일치)에 대한 결과 문구를 작성
        """
        logger.info(f"프로필 문구 생성 시작 (type_profile={type_profile}, kit={kit})")
        var_kit = self.switch_kit[kit]
        # 대조
        if type_profile in var_kit["code_categorized"].keys():
            logger.info(f"{type_profile} 프로필 {len(var_kit['code_categorized'][type_profile])}개 발견")
            for idx, code in enumerate(var_kit["code_categorized"][type_profile], 1):
                logger.info(f"[{idx}/{len(var_kit['code_categorized'][type_profile])}] 프로필 처리 중 (code={code}, type={type_profile})")
                info_ref = var_kit['info_indexed'].loc[[(code, type_profile)], :]
                logger.debug(f"참조 정보 행 수: {len(info_ref) if isinstance(info_ref, pd.DataFrame) else 1}")
                try:
                    info_match = var_kit['info_indexed'].loc[[(code, "일반")], :]
                    logger.debug(f"일치 정보 행 수: {len(info_match) if isinstance(info_match, pd.DataFrame) else 1}")
                except KeyError as e:
                    logger.warning(f"매치되는 일반 프로필이 없습니다 (code={code}): 빈 데이터프레임 사용")
                    info_match = pd.DataFrame({})
                id_ref = info_ref.iloc[0]["감정물번호"] # 대조 데이터가 하나라고 가정
                nickname_ref =str(info_ref.iloc[0][var_kit["colname_nickname"]])
                logger.info(f"참조 프로필 정보 (id={id_ref}, nickname={nickname_ref})")
                if type_profile=="대조": # 대조시료의 비교 문구의 경우 프로필 블록을 별개로 생성한다.
                    logger.debug("대조 프로필 블록 생성 시작")
                    linked_text_ref = self._create_text_evidence(
                        list_id=[id_ref], kit=kit
                    )
                    block_ref = Block_Profile(
                        idx_first=info_ref.iloc[0]["index"],
                        nickname=nickname_ref,
                        text_evidence=linked_text_ref,
                        id_evidence=id_ref
                    )
                    var_kit["profile_blocks_ref"].append(block_ref)
                    logger.debug(f"대조 프로필 블록 생성 완료 (text={linked_text_ref})")
                elif type_profile=="대표": # 대표시료의 비교 문구의 경우 대표프로필과 일치프로필을 합쳐서 처리한다.
                    logger.debug("대표 프로필과 일치 프로필 병합 시작")
                    info_match = pd.concat([info_ref, info_match]).sort_values(by='index')
                    logger.debug(f"병합 후 총 행 수: {len(info_match)}")
                
                # 문장 생성시 필요한 정보를 정리
                if kit=="STR":
                    logger.debug("성별 및 개인식별지수 추출 시작")
                    gender=self.report_data.pm_str.extract_gender_from_profile(id_ref) if self.report_data.pm_str is not None else ""
                    lr = self.report_data.pm_str.calculate_likelihood_from_profile(id_ref) if self.report_data.pm_str is not None else ("0","0")
                    logger.debug(f"성별: {gender}, 개인식별지수: {lr[0]}x10^{lr[1]}")
                else:
                    gender = ""
                    lr = ("0", "0")
                logger.debug(f"증거물 텍스트 생성 시작 (증거물 수={len(info_match)})")
                if len(info_match):
                    text_evidence = self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit, reaction=True)
                    properties = Properties_Phrase(
                        gender=gender,
                        likelihoodratio=lr,
                        text_evidence=text_evidence,
                        nickname=nickname_ref) #본문에 들어갈 text_evidence에는 반응여부 넣는다:reaction=True
                    logger.debug(f"Properties 생성 완료 (nickname={nickname_ref}, evidence={text_evidence[:30]}...)")
                    # 문장생성
                    try:
                        logger.debug("감정서 문구 생성 중 (phraser 호출)")
                        phrase = phraser(properties)
                        self.phrases_result.append(phrase)
                        logger.info(f"문구 생성 완료 ({len(phrase)}자): {phrase[:80] if len(phrase) <= 80 else phrase[:80] + '...'}")
                    except TypeError as e:
                        logger.error(f"감정서 문구 템플릿 오류 (phraser={phraser.__name__}): {e}")
                        raise TemplateError(phraser.__name__, e) from e
                    # 일치 프로필 블록 생성
                    logger.debug("일치 프로필 블록 생성 시작")
                    linked_text_match = self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit).replace(" 및 ", ", ")
                    block_match = Block_Profile(
                        idx_first=info_match.iloc[0]["index"],
                        nickname="",
                        text_evidence=linked_text_match,
                        id_evidence=id_ref
                    )
                    var_kit["profile_blocks"].append(block_match)
                    logger.debug(f"일치 프로필 블록 생성 완료 (text={linked_text_match})")
        else:
            logger.info(f"{type_profile} 프로필이 분류 결과에 없습니다 (건너뜀)")
        logger.info(f"프로필 문구 생성 완료 (type_profile={type_profile}, kit={kit}, 생성된 문구={len(self.phrases_result)}, 생성된 블록 수={len(var_kit['profile_blocks'])})")
    
    def make_contents_without_profile(self, phraser: Callable, type_profile:Literal["ND", "NC"], kit:Literal["STR", "YSTR"]="STR") -> None:
        """
        감정서에 들어갈 프로필이 존재하지 않는 증거물(NC, ND)에 대한 결과 문구를 작성
        """
        logger.info(f"프로필 없는 문구 생성 시작 (type_profile={type_profile}, kit={kit})")
        var_kit = self.switch_kit[kit]
        try:
            info_match = var_kit['info_indexed'].loc[[(type_profile, "일반")], :]
            evidence_count = len(info_match) if isinstance(info_match, pd.DataFrame) else 1
            logger.info(f"{type_profile} 프로필 {evidence_count}개 발견")
            logger.debug(f"처리할 증거물 ID: {list(info_match['감정물번호'])}")

            logger.debug("증거물 텍스트 생성 중 (반응 포함)")
            text_evidence = self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit, reaction=True)
            properties = Properties_Phrase(
                    gender="",
                    likelihoodratio=("",""),
                    text_evidence=text_evidence,
                    nickname=type_profile) #본문에 들어갈 text_evidence에는 반응여부 넣는다:reaction=True
            logger.debug(f"Properties 생성 완료 (type={type_profile}, evidence={text_evidence[:50]}...)")

            try:
                logger.debug("감정서 문구 생성 중 (phraser 호출)")
                phrase = phraser(properties)
                self.phrases_result.append(phrase)
                logger.info(f"문구 생성 완료 ({len(phrase)}자): {phrase[:80] if len(phrase) <= 80 else phrase[:80] + '...'}")
            except TypeError as e:
                logger.error(f"감정서 문구 템플릿 오류 (phraser={phraser.__name__}): {e}")
                raise TemplateError(phraser.__name__, e) from e

            # 프로필 블록 생성
            logger.debug("프로필 블록 생성 시작")

            linked_text_match = self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit).replace(" 및 ", ", ")
            block_match = Block_Profile(
                idx_first=info_match.iloc[0]["index"],
                nickname="",
                text_evidence=linked_text_match,
                id_evidence=type_profile
            )
            var_kit["profile_blocks"].append(block_match)
            logger.debug(f"프로필 블록 생성 완료 (text={linked_text_match})")
        except KeyError as e:
            logger.info(f"{e}: {type_profile} 프로필이 분류 결과에 없습니다 (건너뜀)")
        logger.info(f"프로필 없는 문구 생성 완료 (type_profile={type_profile}, kit={kit}, 생성된 문구={len(self.phrases_result)}, 생성된 블록 수={len(var_kit['profile_blocks'])})")


