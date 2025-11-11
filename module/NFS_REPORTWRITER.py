
from typing import Dict, List, Literal, Callable

from dataclasses import dataclass
import pandas as pd
from . import NFS_REPORTINFORMATION as NFS_RI

@dataclass
class Properties_Phrase:
    gender: str
    likelihoodratio: tuple
    text_evidence: str
    nickname: str

@dataclass
class Block_Profile:
    idx_first: str
    nickname: str
    text_evidence: str
    id_evidence: str

class NFSReportWriter():
    """NFSReportInformation 인스턴스의 데이터를 토대로 HWP control을 사용하여 감정서를 작성하는 클래스"""
    def __init__(self, report_data:NFS_RI.NFSReportInformation, paths_picture:list):
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

        self.switch_kit:dict = {
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
        evidenceinfo_str = self.report_data.evidenceinfo[self.report_data.evidenceinfo["기재_여부"] == "기재"].copy()
        self.code_categorized = categorize_code(df=evidenceinfo_str)
        
        # MultiIndex 설정 (기존 groupby 대체)
        self.categorized_info = evidenceinfo_str.reset_index() # 숫자 인덱스를 보존. index 칼럼으로.
        self.categorized_info = evidenceinfo_str.set_index(["코드", "프로필_유형"])
        
        # Y-STR 데이터 처리
        evidenceinfo_ystr = self.report_data.evidenceinfo[self.report_data.evidenceinfo["Y_기재_여부"] == "기재"].copy()
        self.code_categorized_ystr = categorize_code(evidenceinfo_ystr, column_prefix="Y_")
        
        # MultiIndex 설정 (기존 groupby 대체)
        self.categorized_info_ystr = evidenceinfo_ystr.reset_index() # 숫자 인덱스를 보존
        self.categorized_info_ystr = evidenceinfo_ystr.set_index(["Y_코드", "Y_프로필_유형"])
        self.categorized_info_ystr.sort_index(inplace=True)  # 조회 성능 향상을 위한 정렬

    def _create_text_evidence(self, list_id: list, kit:Literal["STR", "YSTR"]= "STR", reaction=False) -> str:
        """
        각 증거물의 감정물번호를 감정서 본문에 넣을 형식(표기번호)으로 변환하여 반환하는 함수. 감정물번 호가 연속될 경우 ~로 묶어서 반환함. 
        체액 반응 여부가 해당 증거물에 존재할 경우 이를 고려해서 반응 여부를 삽입.
        
        Parameters
        ----------
        list_id: 작업할 표기번호들의 증거물번호 리스트
        kit: 사용 키트 종류. "STR" or "YSTR"
        reaction: 체액반응 실험결과 포함 여부

        Returns
        -------
        연속된 표기번호가 ~으로 묶여진 문자열.
        예시 : list_samplenames: ["증1호", "증2호", "증3호"], reaction=False -> ["증1호~증3호"]
        """
        kit_data = self.switch_kit[kit]
        df_target = self.report_data.evidenceinfo
        df_target = df_target[df_target[kit_data["colname_text_evidence"]] != "미기재", :].copy()
        df_target['표기번호'] = df_target[kit_data["colname_text_evidence"]] 

        # 다음 감정물번호를 나타내는 칼럼 생성
        df_target["감정물번호_다음"] = df_target["감정물번호"].shift(-1)
        # 해당 증거물명의 데이터만 추출
        df_target = df_target.loc[df_target["감정물번호"].isin(list_id)]
        df_target = df_target.reset_index(drop=True)
        # 반응실험결과 칼럼 생성
        equivalent_reaction = (
            ""  # 반응실험 결과가 모두 같을 때 모두 ~반응 양성 하나로 적어주기 위한 변수
        )

        if reaction:
            df_target.loc[:, "반응실험결과"] = (
                df_target["타액_반응"].apply(
                    lambda x: "타액반응 " + x if x != "실험 안함" else ""
                )
                + ","
                + df_target["정액_반응"].apply(
                    lambda x: "정액반응 " + x if x != "실험 안함" else ""
                )
                + ","
                + df_target["혈흔_반응"].apply(
                    lambda x: "혈흔반응 " + x if x != "실험 안함" else ""
                )
            )
            list_reaction = df_target["반응실험결과"].tolist()
            final = []
            for i in list_reaction:
                each = i.split(",")
                process = [x for x in each if x != ""]
                print("process:", process)
                if len(process) == 0:
                    final.append("")
                else:
                    final.append("(" + ", ".join(process) + ")")
            df_target["반응실험결과"] = final
            if (
                1 < len(df_target) == df_target["반응실험결과"].value_counts().iloc[0]
            ):  # 모두 반응실험 결과가 같으면
                equivalent_reaction = df_target.loc[
                    df_target.index[-1], "반응실험결과"
                ].replace("(", "(모두 ")
                df_target.loc[:, "반응실험결과"] = ""
            df_target["표기번호"] = df_target["표기번호"] + df_target["반응실험결과"]

        # 표기번호에 괄호가 있는지 여부 칼럼 생성
        df_target["괄호여부"] = df_target["표기번호"].str.contains(
            r"\(.*\)", regex=True
        )
        # 필요한 데이터만 정리
        df_target = df_target[["감정물번호", "감정물번호_다음", "표기번호", "괄호여부"]]
        # 데이터가 하나일 때
        if len(df_target) == 1:
            linked_num = df_target.iloc[0]["표기번호"]
        elif len(df_target) == 2:
            linked_num = (
                df_target.iloc[0]["표기번호"] + " 및 " + df_target.iloc[1]["표기번호"]
            )
        else:
            stack = []
            chains = []
            stack.append(df_target.iloc[0]["표기번호"])
            next_samplename = df_target.iloc[0]["감정물번호_다음"]
            prev_parentheses = df_target.iloc[0]["괄호여부"]
            for index, row in df_target.iloc[1:].iterrows():
                if (
                    next_samplename == row["감정물번호"]
                    and not row["괄호여부"]
                    and not prev_parentheses
                ):
                    stack.append(row["표기번호"])
                else:
                    chains.append(stack)
                    stack = [row["표기번호"]]
                next_samplename = row["감정물번호_다음"]
                prev_parentheses = row["괄호여부"]
            chains.append(stack)
            list_text_chain = []
            for chain in chains:
                if len(chain) < 3:
                    text_chain = ", ".join(chain)
                else:
                    text_chain = chain[0] + "~" + chain[-1]
                list_text_chain.append(text_chain)
            linked_num = ", ".join(list_text_chain)
        return linked_num + equivalent_reaction

    def make_contents_with_profile(self, phraser: Callable, type_profile:Literal["대표", "대조"], kit:Literal["STR", "YSTR"]="STR") -> None:
        """
            감정서에 들어갈 프로필이 존재하는 증거물(대표, 대조, 일치)에 대한 결과 문구를 작성
        """
        var_kit = self.switch_kit[kit]
        # 대조
        if type_profile in var_kit["code_categorized"].keys():
            for code in var_kit["code_categorized"][type_profile]:
                info_ref = var_kit['info_indexed'].loc[(code, type_profile)]
                try: #예외처리를 이렇게 써도 되나?
                    info_match = var_kit['info_indexed'].loc[(code, "일반")]
                except KeyError as e:
                    print(f"{e}: 매치되는 그룹바이가 없습니다. 빈 데이터프레임을 반환합니다.")
                    info_match = pd.DataFrame({})
                id_ref = info_ref.iloc[0]["감정물번호"] # 대조 데이터가 하나라고 가정
                nickname_ref = info_ref.iloc[0][var_kit["colname_nickname"]]
                if type_profile=="대조": # 대조시료의 비교 문구의 경우 프로필 블록을 별개로 생성한다.
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
                elif type_profile=="대표": # 대표시료의 비교 문구의 경우 대표프로필과 일치프로필을 합쳐서 처리한다.
                    info_match = pd.concat([info_ref, info_match]).sort_values(by='index')
                
                # 문장 생성시 필요한 정보를 정리
                if kit=="STR":
                    gender=self.report_data.pm_str.extract_gender_from_profile(id_ref) if self.report_data.pm_str is not None else ""
                    lr = self.report_data.pm_str.calculate_likelihood_from_profile(id_ref) if self.report_data.pm_str is not None else ("0","0")
                properties = Properties_Phrase(
                    gender=gender,
                    likelihoodratio=lr,
                    text_evidence=self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit, reaction=True),
                    nickname=nickname_ref) #본문에 들어갈 text_evidence에는 반응여부 넣는다:reaction=True
                # 문장생성
                try:
                    self.phrases_result.append(phraser(properties))
                except TypeError as e: #TypeError로 모두 잡을 수 있을까?
                    print(f"{e}: 감정서 문구 탬플릿 오류입니다.")
                # 일치 프로필 블록 생성
                linked_text_match = self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit).replace(" 및 ", ", ")
                block_match = Block_Profile(
                    idx_first=info_match.iloc[0]["index"],
                    nickname="",
                    text_evidence=linked_text_match,
                    id_evidence=id_ref
                )
                var_kit["profile_blocks"].append(block_match)
    
    def make_contents_without_profile(self, phraser: Callable, type_profile:Literal["ND", "ND"], kit:Literal["STR", "YSTR"]="STR") -> None:
        """
        감정서에 들어갈 프로필이 존재하지 않는 증거물(NC, ND)에 대한 결과 문구를 작성
        """
        var_kit = self.switch_kit[kit]
        if type_profile in var_kit["code_categorized"].keys():
            info_match = var_kit['info_indexed'].loc[(type_profile, "일반")]            
            properties = Properties_Phrase(
                    gender="",
                    likelihoodratio=("",""),
                    text_evidence=self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit, reaction=True),
                    nickname=type_profile) #본문에 들어갈 text_evidence에는 반응여부 넣는다:reaction=True
            try:
                self.phrases_result.append(phraser(properties))
            except TypeError as e: #TypeError로 모두 잡을 수 있을까?
                print(f"{e}: 감정서 문구 탬플릿 오류입니다.")
            # 프로필 블록 생성
            linked_text_match = self._create_text_evidence(list_id=list(info_match['감정물번호']), kit=kit).replace(" 및 ", ", ")
            block_match = Block_Profile(
                idx_first=info_match.iloc[0]["index"],
                nickname="",
                text_evidence=linked_text_match,
                id_evidence=type_profile
            )
            var_kit["profile_blocks"].append(block_match)


