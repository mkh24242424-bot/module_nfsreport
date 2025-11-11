from . import NFS_PROFILEDATAMANAGER as NFS_PM
import pandas as pd

class NFSReportInformation():
    """국립과학수사연구원 유전자과 감정서에 필요한 한 사건의 정보를 모아서 정리하는 데이터클래스"""
    def __init__(self, id_case:str = "noname", type_case:str = "default"):
        self.id_case = id_case
        self.type_case = type_case
        self.caseinfo:dict = {}
        self.evidenceinfo:pd.DataFrame = pd.DataFrame()
        self.pm_str = None
        self.pm_ystr = None

    def extract_caseinfo_from_df(self, df_caseinfo:pd.DataFrame):
        """사건정보 데이터프레임에서 사건번호에 해당하는 사건정보 중 감정서에 필요한 데이터 추출해서 딕셔너리화"""

        list_required_columns = ['의뢰관서', '문서번호', '접수일자', '시행일자']
        try:
            self.caseinfo = df_caseinfo.loc[df_caseinfo['접수번호']==self.id_case, list_required_columns].iloc[0].to_dict() 
        except KeyError as e:
            print(f"{e} : {self.id_case}의 사건 정보가 데이터프레임에 존재하지 않습니다.")
            
    def extract_evidenceinfo_from_df(self, df_evidenceinfo:pd.DataFrame):
        list_required_columns = ['접수번호', '감정물번호', '감정물', '분류', '대조_이름', 'Y_대조_이름', '프로필_유형', 
                                 'Y_프로필_유형', '코드', 'Y_코드', '표기번호', 'Y_표기번호', '기재_여부', 'Y_기재_여부',
                                   '타액_반응', '정액_반응', '혈흔_반응', '검색_결과', '반환_여부']
        try:
            self.evidenceinfo = df_evidenceinfo.loc[df_evidenceinfo['접수번호']==self.id_case, list_required_columns]
        except KeyError as e:
            print(f"{e} : {self.id_case}의 사건 정보가 데이터프레임에 존재하지 않습니다.")
    
    def load_str_profiledatamanager(self, pdm: NFS_PM.NFSProfileDataManager):
        self.pm_str = pdm.filter_by_codecase(code_case = self.id_case)
    
    def load_ystr_profiledatamanager(self, pdm: NFS_PM.NFSProfileDataManager):
        self.pm_ystr = pdm.filter_by_codecase(code_case = self.id_case)